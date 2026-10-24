#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stop hook: no "it is not in my records" answer without a full recall.py search first.

Why: an agent's memory is usually spread over several places (per-directory memory folders, size-capped
index files, checkpoint and session logs). An answer such as "there is no record of X" or "we don't seem
to use X", given after looking at only one of them, is a guess presented as a fact. recall.py, shipped
next to this file, searches all of them; this hook makes that search mandatory before a negative memory
claim. Not found where you looked is not the same as absent.

Behaviour:
  - stop_hook_active is true                    -> let the stop through (never loops)
  - the last assistant text of the turn makes a negative memory claim (记录里没有 / 没出现过 / 不像是在用 /
    not in my memory / no record of ...), outside code, block quotes and quoted 「…」『…』“…”"…" spans,
    and no shell tool call in this turn (everything after the last user prompt) ran a script named
    recall.py without an error result
                                                -> {"decision": "block", "reason": ...}
  - anything else                               -> let the stop through, print nothing
FAIL-OPEN: any error, a missing or unreadable transcript, a parse failure, a turn longer than TAIL_CAP
bytes, or the internal DEADLINE (2.5 s, where the platform has SIGALRM) lets the stop through silently.
The settings entry also carries timeout 3; Claude Code ignores a failing Stop hook, so a broken guard
never traps a session.

Usage (settings.json hooks.Stop; --install writes exactly this line):
    <absolute path of the installing python> -I <absolute path of this file>
Self-test (builds fake transcripts in a temp dir, runs this file as the hook would, then an install
round trip on a throw-away settings file):
    python3 -I negative_claim_guard.py --selftest
Install / uninstall. The default target is .claude/settings.json under the current directory (run it
from the project root); --settings PATH picks another file, for example ~/.claude/settings.json for every
project of this user. The file is backed up into .muse-hook-backups/ next to it first (--backup-dir DIR
to change), only this entry is appended or removed, the result is re-parsed, and the backup is restored
by itself if anything else changed. A missing settings file is created on --install.
    python3 -I negative_claim_guard.py --install   [--settings PATH] [--backup-dir DIR]
    python3 -I negative_claim_guard.py --uninstall [--settings PATH] [--backup-dir DIR]
Python 3.7+ compatible. Standard library only.
"""
import json
import os
import re
import shlex
import signal
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RECALL = os.path.join(HERE, "recall.py")
MARKER = "negative_claim_guard.py"
BACKUP_DIRNAME = ".muse-hook-backups"
HOOK_TIMEOUT = 3          # seconds, written into settings.json
DEADLINE = 2.5            # seconds, internal; on expiry the stop goes through
TAIL_CAP = 24 * 1024 * 1024
CHUNK = 1024 * 1024
REASON_PREFIX = "Negative memory claim without a full search"


def _python():
    """The interpreter running this file, as an absolute path (falls back to a PATH lookup)."""
    return os.path.abspath(sys.executable) if sys.executable else "python3"


HOOK_CMD = " ".join(shlex.quote(p) for p in (_python(), "-I", os.path.abspath(__file__)))

NEGATIVE = re.compile("|".join([
    # core phrasings
    r"记录里没有", r"记忆里没有", r"没有记录", r"没出现过", r"没有出现过", r"不像是?在用", r"没有这方面的记录",
    r"not in (?:my )?memory", r"no records? of",
    # same claims, other wording
    r"(?:记录|记忆|笔记)(?:里|中)(?:也|并|都|还|完全|根本)?(?:没有|没|无|找不到|查不到|没找到)",
    r"没有(?:任何|相关|这方面的?)记录", r"从未出现过", r"不在(?:我的)?(?:记录|记忆)(?:里|中)",
    r"(?:我们|我)?(?:从)?没(?:有)?用过",
    r"not in (?:my )?(?:memories|records?|notes)", r"nothing in (?:my )?(?:memory|records?|notes)",
    r"(?:don't|do not|doesn't|does not|can't|cannot) (?:have|see|find) (?:any )?(?:records?|memory|mention) of",
]), re.I)

QUOTED = [
    re.compile(r"```.*?```", re.S),          # fenced code
    re.compile(r"`[^`\n]*`"),                # inline code
    re.compile(r"「[^」\n]*」"), re.compile(r"『[^』\n]*』"),
    re.compile(r"“[^”\n]*”"), re.compile(r"\"[^\"\n]*\""),
]
ENTRY = re.compile(rb'"type"\s*:\s*"(?:user|assistant)"')
SEGMENT = re.compile(r"\|\||&&|[;|&\n]|\$\(|`")
PYTHON = re.compile(r"^(?:python(?:\d+(?:\.\d+)*)?|pypy3?)$")
LAUNCHERS = {"time", "env", "nice", "nohup", "command", "timeout", "caffeinate", "bash", "sh", "zsh", "uv", "run"}


class Deadline(Exception):
    pass


def strip_quoted(text):
    text = "\n".join(l for l in text.splitlines() if not l.lstrip().startswith(">"))
    for pat in QUOTED:
        text = pat.sub(" ", text)
    return text


def negative_claim(text):
    """The sentence holding a negative memory claim, or None."""
    clean = strip_quoted(text or "")
    m = NEGATIVE.search(clean)
    if not m:
        return None
    cuts = "。！？!?\n"
    start = max([clean.rfind(c, 0, m.start()) for c in cuts] + [-1]) + 1
    ends = [i for i in (clean.find(c, m.end()) for c in cuts) if i != -1]
    end = min(ends) if ends else len(clean)
    sentence = " ".join(clean[start:end].split()).lstrip("-*•·#0123456789. ")
    return sentence[:80] + ("…" if len(sentence) > 80 else "")


def _words(segment):
    """Shell words of one command segment; quoted paths with spaces stay one word."""
    try:
        words = shlex.split(segment)
    except ValueError:                       # unbalanced quotes: plain split, as before
        words = segment.split()
    return [w.strip("'\"()") for w in words]


def runs_recall(command):
    """True when a shell command line actually runs recall.py (not cat/sed/grep of it)."""
    for seg in SEGMENT.split(command or ""):
        words = _words(seg)
        idx = next((i for i, w in enumerate(words) if os.path.basename(w) == "recall.py"), None)
        if idx is None:
            continue
        ok = True
        for w in words[:idx]:
            base = os.path.basename(w)
            if not (PYTHON.match(base) or base in LAUNCHERS or w.startswith("-")
                    or "=" in w or re.match(r"^\d+[smh]?$", w)):
                ok = False
                break
        if ok:
            return True
    return False


def tail_lines(path):
    """Yield raw transcript lines from the end backwards; yields None once the file start is reached."""
    with open(path, "rb") as f:
        f.seek(0, 2)
        pos = f.tell()
        buf = b""
        read = 0
        while pos > 0:
            if read >= TAIL_CAP:
                return                       # cap hit: the caller fails open
            step = min(CHUNK, pos)
            pos -= step
            f.seek(pos)
            buf = f.read(step) + buf
            read += step
            parts = buf.split(b"\n")
            buf = parts[0]
            for raw in reversed(parts[1:]):
                yield raw
        yield buf
        yield None


def opens_turn(e):
    """A user entry that starts a turn: not a tool result, not a mid-turn meta insert (skill body, image note)."""
    if e.get("type") != "user" or e.get("isSidechain"):
        return False
    content = (e.get("message") or {}).get("content")
    if isinstance(content, list):
        if not any(isinstance(b, dict) and b.get("type") != "tool_result" for b in content):
            return False
    elif not isinstance(content, str):
        return False
    if e.get("isMeta") and not e.get("promptSource"):
        return False
    return True


def read_turn(path):
    """Entries of the current turn, oldest first, or None when the turn start was not reached."""
    turn = []
    for raw in tail_lines(path):
        if raw is None:
            return list(reversed(turn))      # whole file is one turn
        if not ENTRY.search(raw):
            continue
        try:
            e = json.loads(raw.decode("utf-8", "replace"))
        except ValueError:
            continue
        if not isinstance(e, dict) or e.get("type") not in ("user", "assistant") or e.get("isSidechain"):
            continue
        if opens_turn(e):
            return list(reversed(turn))
        turn.append(e)
    return None


def analyse(turn):
    """(last assistant text run, ran_recall) for the entries of one turn."""
    uses, failed = {}, set()
    parts, reset = [], False
    for e in turn:
        content = (e.get("message") or {}).get("content")
        if not isinstance(content, list):
            continue
        for b in content:
            if not isinstance(b, dict):
                continue
            t = b.get("type")
            if e.get("type") == "assistant" and t == "text":
                if reset:
                    parts, reset = [], False
                parts.append(b.get("text") or "")
            elif e.get("type") == "assistant" and t == "tool_use":
                reset = True
                cmd = (b.get("input") or {}).get("command") if isinstance(b.get("input"), dict) else None
                if isinstance(cmd, str) and runs_recall(cmd):
                    uses[b.get("id")] = cmd
            elif t == "tool_result":
                reset = True
                if b.get("is_error"):
                    failed.add(b.get("tool_use_id"))
    ran = any(i not in failed for i in uses)
    return "\n".join(parts), ran


def block(claim):
    cmd = "%s -I %s <term> <synonym>" % (shlex.quote(_python()), shlex.quote(RECALL))
    return {"decision": "block", "reason": (
        "%s: \"%s\". Before saying something is not in your records, run %s with the subject plus a "
        "synonym in each language your notes use (for example 数据库 database), read the hits, then answer from "
        "them. Not found where you looked is not the same as not there; if the full search also finds "
        "nothing, say what you searched instead of concluding that it does not exist." % (REASON_PREFIX, claim, cmd))}


def decide(data):
    """The block decision dict, or None to let the stop through."""
    if data.get("stop_hook_active"):
        return None
    text = data.get("last_assistant_message")
    if isinstance(text, str) and text.strip() and not negative_claim(text):
        return None                          # fast path: nothing to check
    path = data.get("transcript_path")
    if not path or not os.path.isfile(path):
        return None
    turn = read_turn(path)
    if turn is None:
        return None
    last_text, ran = analyse(turn)
    if not (isinstance(text, str) and text.strip()):
        text = last_text
    claim = negative_claim(text)
    if not claim or ran:
        return None
    return block(claim)


def _alarm(signum, frame):
    raise Deadline()


def hook():
    timed = hasattr(signal, "SIGALRM")       # no SIGALRM (Windows): the settings timeout still applies
    try:
        if timed:
            signal.signal(signal.SIGALRM, _alarm)
            signal.setitimer(signal.ITIMER_REAL, DEADLINE)
        # bytes in, ASCII-escaped JSON out: independent of the locale the hook is started under
        data = json.loads(sys.stdin.buffer.read().decode("utf-8", "replace") or "{}")
        out = decide(data) if isinstance(data, dict) else None
        if timed:
            signal.setitimer(signal.ITIMER_REAL, 0)
        if out:
            sys.stdout.write(json.dumps(out) + "\n")
            sys.stdout.flush()
    except BaseException:                    # fail open, including Deadline and KeyboardInterrupt
        pass
    return 0


# ---------------------------------------------------------------- install / uninstall

def _arg(argv, flag, default):
    if flag not in argv:
        return default
    i = argv.index(flag)
    if i + 1 >= len(argv):
        raise SystemExit("%s needs a value" % flag)
    return os.path.abspath(os.path.expanduser(argv[i + 1]))


def _is_ours(group):
    return MARKER in json.dumps(group)


def _indent_of(text):
    """Indentation the settings file already uses (2 spaces when it has none)."""
    m = re.search(r'^([ \t]+)"', text or "", re.M)
    return m.group(1) if m else 2


def _write_json(path, data, like_text):
    """Write data in the file's own indentation and trailing-newline style, validate, then replace."""
    import stat
    tmp = path + ".tmp-" + MARKER
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=_indent_of(like_text))
            if like_text is None or like_text.endswith("\n"):
                f.write("\n")
        if os.path.exists(path):
            os.chmod(tmp, stat.S_IMODE(os.stat(path).st_mode))     # keep the file mode
        with open(tmp, encoding="utf-8") as f:
            json.load(f)                     # validate before replacing
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def _backup(path, backup_dir):
    """Copy the settings file into backup_dir under a new name; never overwrite an earlier backup."""
    import shutil
    import time
    if not os.path.isdir(backup_dir):
        os.makedirs(backup_dir)
        with open(os.path.join(backup_dir, ".gitignore"), "w", encoding="utf-8") as f:
            f.write("# settings backups written by MUSE hook installers; keep them out of git\n*\n")
    stem = os.path.join(backup_dir, "%s.%s.%s" % (os.path.basename(path), MARKER[:-3], time.strftime("%Y%m%d_%H%M%S")))
    backup, n = stem + ".json", 1
    while os.path.exists(backup):
        backup, n = "%s_%d.json" % (stem, n), n + 1
    shutil.copy2(path, backup)
    return backup


def _stop_list(d):
    hooks = d.get("hooks") if isinstance(d, dict) else None
    return (hooks or {}).get("Stop", []) if isinstance(hooks, (dict, type(None))) else None


def install(argv, remove=False):
    import shutil
    given = _arg(argv, "--settings", os.path.join(os.getcwd(), ".claude", "settings.json"))
    path = os.path.realpath(given)           # a symlinked settings file is updated in place
    backup_dir = _arg(argv, "--backup-dir", os.path.join(os.path.dirname(given), BACKUP_DIRNAME))
    existed = os.path.isfile(path)
    if existed:
        with open(path, encoding="utf-8") as f:
            text = f.read()
        try:
            data = json.loads(text)
        except ValueError as exc:
            print("Not valid JSON, nothing changed: %s (%s)" % (path, exc))
            return 1
    elif os.path.exists(path):
        print("Not a file, nothing changed: %s" % path)
        return 1
    elif remove:
        print("No settings file, nothing to remove: %s" % path)
        return 0
    else:
        text, data = None, {}
    stop = _stop_list(data)
    if not isinstance(data, dict) or not isinstance(stop, list):
        print("Unexpected settings shape (hooks.Stop must be a list), nothing changed: %s" % path)
        return 1
    present = [g for g in stop if _is_ours(g)]
    if not remove and present:
        print("Already installed, nothing appended: %s" % path)
        return 0
    if remove and not present:
        print("No %s entry found, nothing changed: %s" % (MARKER, path))
        return 0
    orig = json.loads(text) if existed else {}
    backup = _backup(path, backup_dir) if existed else None
    if data.get("hooks") is None:
        data["hooks"] = {}
    hooks = data["hooks"]
    if remove:
        hooks["Stop"] = [g for g in stop if not _is_ours(g)]
    else:
        hooks.setdefault("Stop", stop).append({"hooks": [{"type": "command", "command": HOOK_CMD,
                                                          "timeout": HOOK_TIMEOUT}]})
        if not existed:
            os.makedirs(os.path.dirname(path), exist_ok=True)
    _write_json(path, data, text)
    with open(path, encoding="utf-8") as f:
        after = json.load(f)
    after_stop = after["hooks"]["Stop"]
    others_same = [g for g in _stop_list(orig) if not _is_ours(g)] == [g for g in after_stop if not _is_ours(g)]
    rest_same = ({k: v for k, v in orig.items() if k != "hooks"} == {k: v for k, v in after.items() if k != "hooks"}
                 and {k: v for k, v in (orig.get("hooks") or {}).items() if k != "Stop"}
                 == {k: v for k, v in after["hooks"].items() if k != "Stop"})
    if remove:
        ours_ok = not any(_is_ours(g) for g in after_stop)
    else:
        ours_ok = (sum(1 for g in after_stop if _is_ours(g)) == 1 and _is_ours(after_stop[-1])
                   and after_stop[-1]["hooks"][0]["command"] == HOOK_CMD)
    print("%s: %s" % ("Removed" if remove else ("Appended" if existed else "Created"), path))
    print("Backup: %s" % (backup or "none (there was no settings file)"))
    print("JSON re-parsed; other Stop hooks unchanged: %s; other settings unchanged: %s; this entry correct: %s"
          % (others_same, rest_same, ours_ok))
    if not (others_same and rest_same and ours_ok):
        if backup:
            shutil.copy2(backup, path)
        else:
            os.remove(path)
        print("Check failed, rolled back: %s" % path)
        return 1
    if backup:
        print("Roll back with: cp -p %s %s" % (shlex.quote(backup), shlex.quote(path)))
    return 0


# ---------------------------------------------------------------- self-test

def _fixture(dirpath, name, prompt, steps, prior=None):
    """Write a transcript shaped like a real Claude Code one (2026-10 field names)."""
    import uuid
    sid = "00000000-0000-4000-8000-0000000000aa"
    rows, parent = [], None

    def add(row):
        nonlocal parent
        row.update({"uuid": str(uuid.uuid4()), "parentUuid": parent, "sessionId": sid,
                    "isSidechain": False, "timestamp": "2026-10-22T04:40:00.000Z", "version": "2.1.x",
                    "cwd": dirpath, "userType": "external", "entrypoint": "cli"})
        parent = row["uuid"]
        rows.append(row)

    def assistant(block_):
        add({"type": "assistant", "message": {"id": "msg_x", "type": "message", "role": "assistant",
                                               "model": "example-model", "content": [block_],
                                               "stop_reason": None, "usage": {}}})

    def user_prompt(text):
        add({"type": "user", "promptSource": "sdk", "turnOrigin": "human", "permissionMode": "default",
             "message": {"role": "user", "content": text}})

    for turn_prompt, turn_steps in ([(prior[0], prior[1])] if prior else []) + [(prompt, steps)]:
        rows.append({"type": "last-prompt", "leafUuid": parent, "sessionId": sid})
        user_prompt(turn_prompt)
        rows.append({"type": "attachment", "attachment": {"type": "skill_listing"}, "sessionId": sid})
        assistant({"type": "thinking", "thinking": "", "signature": "sig"})
        for kind, value in turn_steps:
            if kind == "text":
                assistant({"type": "text", "text": value})
            elif kind == "meta":
                add({"type": "user", "isMeta": True, "message": {"role": "user", "content": [{"type": "text", "text": value}]}})
            else:                                   # ("bash", (command, is_error))
                cmd, err = value
                tid = "toolu_" + uuid.uuid4().hex[:20]
                assistant({"type": "tool_use", "id": tid, "name": "Bash", "caller": {"type": "direct"},
                           "input": {"command": cmd, "description": "Search all memory"}})
                add({"type": "user", "toolUseResult": {"stdout": "total hits: 92", "stderr": "", "interrupted": False,
                                                       "isImage": False, "noOutputExpected": False},
                     "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": tid,
                                                              "content": [{"type": "text", "text": "ok"}],
                                                              "is_error": err}]}})
        # noise that must be ignored: request blobs carry user/assistant roles but are not turn entries
        rows.append({"type": "api-request-blob", "hash": "h", "sessionId": sid,
                     "message": {"role": "user", "content": [{"type": "text", "text": "blob"}]}})
    p = os.path.join(dirpath, name + ".jsonl")
    with open(p, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return p


def _run_hook(stdin_bytes, env=None):
    import subprocess
    r = subprocess.run([sys.executable, "-I", os.path.abspath(__file__)], input=stdin_bytes,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10, env=env)
    return r.returncode, r.stdout.decode("utf-8").strip(), r.stderr


def _selftest_install(tmp):
    """Install / re-install / uninstall on a throw-away settings file: only our entry may move."""
    import subprocess
    settings = os.path.join(tmp, "settings.json")
    backups = os.path.join(tmp, BACKUP_DIRNAME)
    orig = {"permissions": {"allow": ["Bash(ls:*)"]},
            "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "pre"}]}],
                      "Stop": [{"hooks": [{"type": "command", "command": "/x/licence_stop_guard.py", "timeout": 3}]},
                               {"hooks": [{"type": "command", "command": "/x/other-hook.py", "timeout": 20}]}]}}
    orig_text = json.dumps(orig, ensure_ascii=False, indent=2) + "\n"
    with open(settings, "w", encoding="utf-8") as f:
        f.write(orig_text)

    def run(flag):
        r = subprocess.run([sys.executable, "-I", os.path.abspath(__file__), flag, "--settings", settings],
                           cwd=tmp, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        return r.returncode, r.stdout.decode("utf-8")

    def load():
        with open(settings, encoding="utf-8") as f:
            return f.read()

    def n_backups():
        return len([n for n in os.listdir(backups) if n.endswith(".json")]) if os.path.isdir(backups) else 0

    results = []
    rc, out = run("--install")
    d = json.loads(load())
    ours = [g for g in d["hooks"]["Stop"] if _is_ours(g)]
    cmd = shlex.split(ours[0]["hooks"][0]["command"]) if len(ours) == 1 else []
    results.append(("I1", "--install appends this entry; other Stop hooks and settings unchanged; backup beside it",
                    rc == 0 and len(ours) == 1 and cmd[1:] == ["-I", os.path.abspath(__file__)]
                    and os.path.isabs(cmd[0]) and ours[0]["hooks"][0]["timeout"] == HOOK_TIMEOUT
                    and d["hooks"]["Stop"][:2] == orig["hooks"]["Stop"] and d["hooks"]["PreToolUse"] == orig["hooks"]["PreToolUse"]
                    and d["permissions"] == orig["permissions"] and n_backups() == 1))
    before = load()
    rc, out = run("--install")
    results.append(("I2", "a second --install appends nothing and writes no backup",
                    rc == 0 and "Already installed" in out and load() == before and n_backups() == 1))
    rc, out = run("--uninstall")
    results.append(("I3", "--uninstall removes only this entry: the file is byte-identical to the original",
                    rc == 0 and load() == orig_text and n_backups() == 2))
    return results


def selftest():
    import shutil
    import tempfile
    d = tempfile.mkdtemp(prefix="ncg-selftest-")
    q = "我们只用 ExampleModel 还是也用 OtherModel？"
    wrong = "OtherModel 我的记录里没有出现过，不像是在用，但还没核实。"
    recall_cmd = "python3 -I %s OtherModel 其它模型 2>&1 | tail -40" % shlex.quote(RECALL)
    spaced_cmd = "cd /tmp && python3 -I '/opt/my tools/recall.py' OtherModel 其它模型 | tail -40"
    c_env = {"LC_ALL": "C", "LANG": "C", "PATH": "/usr/bin:/bin"}
    missing = os.path.join(d, "missing.jsonl")

    def t(name, steps, **kw):
        return _fixture(d, name, q, steps, **kw)

    # (id, label, transcript path or None for non-JSON stdin, extra stdin fields, env, expect_block)
    cases = [
        ("A", "negative claim, no recall.py this turn", t("A", [("text", wrong)]), {}, None, True),
        ("A2", "same as A, stdin carries last_assistant_message (Claude Code sends it)",
         t("A2", [("text", wrong)]), {"last_assistant_message": wrong}, None, True),
        ("A3", "English claim: no record of ... in my notes",
         t("A3", [("text", "I have no record of OtherModel in my notes, so we probably do not use it.")]), {}, None, True),
        ("B", "same text, recall.py ran in this turn", t("B", [("bash", (recall_cmd, False)), ("text", wrong)]),
         {}, None, False),
        ("B2", "recall.py at a quoted path with spaces ran in this turn",
         t("B2", [("bash", (spaced_cmd, False)), ("text", wrong)]), {}, None, False),
        ("C", "same as A, stop_hook_active=true", t("C", [("text", wrong)]), {"stop_hook_active": True}, None, False),
        ("D", "ordinary text", t("D", [("text", "ExampleModel 是主链路；OtherModel 在三次评估里做过对比。")]), {}, None, False),
        ("F", "recall.py ran only in the previous turn", _fixture(d, "F", "再确认一下", [("text", wrong)],
                                                                 prior=(q, [("bash", (recall_cmd, False)), ("text", "查到了。")])),
         {}, None, True),
        ("G", "this turn only cat-ed recall.py, and one recall.py run returned an error",
         t("G", [("bash", ("cat %s" % shlex.quote(RECALL), False)), ("bash", (recall_cmd, True)), ("text", wrong)]),
         {}, None, True),
        ("H", "a skill load (isMeta insert) after recall.py is not a new turn",
         t("H", [("bash", (recall_cmd, False)), ("meta", "Base directory for this skill: x"), ("text", wrong)]),
         {}, None, False),
        ("I", "negative wording only inside quotes (「」 / > quote / code)",
         t("I", [("text", "上次的回答写了「OtherModel 我的记录里没有出现过」——这是错的。\n> 记录里没有\n`no record of`")]),
         {}, None, False),
        ("J", "transcript missing (fail open)", missing, {}, None, False),
        ("K", "stdin is not JSON (fail open)", None, None, None, False),
        ("L", "started under the C locale (stdin/stdout do not depend on it)", t("L", [("text", wrong)]), {}, c_env, True),
    ]
    failures = 0
    for cid, label, path, extra, env, expect_block in cases:
        if path is None:
            stdin = b"not json {"
        else:
            payload = {"session_id": "00000000-0000-4000-8000-0000000000aa", "transcript_path": path,
                       "cwd": d, "permission_mode": "default", "hook_event_name": "Stop", "stop_hook_active": False}
            payload.update(extra)
            stdin = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        rc, out, err = _run_hook(stdin, env)
        try:
            parsed = json.loads(out) if out else None
        except ValueError:
            parsed = None
        blocked = bool(parsed) and parsed.get("decision") == "block" and parsed.get("reason", "").startswith(REASON_PREFIX)
        ok = blocked == expect_block and rc == 0 and not err and (bool(out) == expect_block)
        failures += not ok
        print("%s %-3s %s -> %s (exit %d%s)" % ("PASS" if ok else "FAIL", cid, label, "block" if blocked else "pass",
                                               rc, ", stderr not empty" if err else ""))
        if parsed and cid in ("A", "A3"):
            print("        reason: %s" % parsed["reason"])
    total = len(cases)
    inst_dir = os.path.join(d, "inst")
    os.makedirs(inst_dir)
    inst = _selftest_install(inst_dir)
    for cid, label, ok in inst:
        failures += not ok
        print("%s %-3s %s" % ("PASS" if ok else "FAIL", cid, label))
    total += len(inst)
    print("%d/%d passed" % (total - failures, total))
    if failures:
        print("fixtures kept in: %s" % d)
    else:
        shutil.rmtree(d, ignore_errors=True)
    return 1 if failures else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    if "--install" in sys.argv:
        sys.exit(install(sys.argv))
    if "--uninstall" in sys.argv:
        sys.exit(install(sys.argv, remove=True))
    sys.exit(hook())
