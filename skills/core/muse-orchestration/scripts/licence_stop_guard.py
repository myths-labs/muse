#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stop hook (opt-in policy): a licence is one line of fact, not by itself a reason to skip evaluating a project.

Why: asked to survey open-source projects, model weights, datasets or papers, agents tend to read a
restrictive licence (non-commercial, research-only, OpenRAIL, training-data terms) as a reason to stop,
skip or exclude, so an option is dropped before anyone has evaluated it. This hook encodes ONE PROJECT
POLICY, stated in DEFAULT_REASON: record the licence in one line, keep evaluating side by side with your
own inputs where the licence permits evaluation, and raise licence limits for human review before any
production use. It is not legal advice and it does not judge what a licence allows.

Opt-in: install it only if your project adopts this policy. To state your own policy, set the
MUSE_LICENCE_GUARD_REASON environment variable for the hook process, or edit DEFAULT_REASON.

Behaviour:
  - stop_hook_active is true                    -> let the stop through (never loops)
  - an assistant sentence of the latest turn (everything after the last user prompt) holds a licence word AND a
    stop word, outside code, block quotes and quoted 「…」『…』“…”"…" spans, and the same sentence does not restate
    the rule ("不是停手理由", "照测", "并排", "not a reason", ...) or follow it (the licence goes to human review,
    or the licence itself forbids evaluation)
                                                -> {"decision": "block", "reason": ...}
  - anything else                               -> let the stop through, print nothing
FAIL-OPEN: any error, a missing or unreadable transcript, a parse failure, a turn longer than TAIL_CAP bytes, or the
internal DEADLINE (2.5 s, where the platform has SIGALRM) lets the stop through silently. The settings entry also
carries timeout 3; Claude Code ignores a failing Stop hook, so a broken guard never traps a session.

Usage (settings.json hooks.Stop; --install writes exactly this line):
    <absolute path of the installing python> -I <absolute path of this file>
Self-test (builds fake transcripts in a temp dir, runs this file as the hook would, block cases first, then an
install round trip on a throw-away settings file):
    python3 -I licence_stop_guard.py --selftest
Install / uninstall. The default target is .claude/settings.json under the current directory (run it from the
project root); --settings PATH picks another file, for example ~/.claude/settings.json for every project of this
user. The file is backed up into .muse-hook-backups/ next to it first (--backup-dir DIR to change), only this entry
is appended or removed, the result is re-parsed, and the backup is restored by itself if anything else changed.
A missing settings file is created on --install.
    python3 -I licence_stop_guard.py --install   [--settings PATH] [--backup-dir DIR]
    python3 -I licence_stop_guard.py --uninstall [--settings PATH] [--backup-dir DIR]
Python 3.7+ compatible. Standard library only.
"""
import json
import os
import re
import shlex
import signal
import sys

MARKER = "licence_stop_guard.py"
BACKUP_DIRNAME = ".muse-hook-backups"
HOOK_TIMEOUT = 3          # seconds, written into settings.json
DEADLINE = 2.5            # seconds, internal; on expiry the stop goes through
TAIL_CAP = 24 * 1024 * 1024
CHUNK = 1024 * 1024
REASON_ENV = "MUSE_LICENCE_GUARD_REASON"
MATCHED = "\nMatched sentence: "


def _python():
    """The interpreter running this file, as an absolute path (falls back to a PATH lookup)."""
    return os.path.abspath(sys.executable) if sys.executable else "python3"


HOOK_CMD = " ".join(shlex.quote(p) for p in (_python(), "-I", os.path.abspath(__file__)))

DEFAULT_REASON = ("A licence is one line of fact, not by itself a reason to skip evaluating an open-source project, "
                  "model or paper. Record the licence in one line, keep evaluating side by side with your own inputs "
                  "where the licence permits evaluation, and raise licence limits for human review before any "
                  "production use.")
REWORD = ("If the sentence only records the licence line or restates this rule, reword it without the "
          "stop wording.")

# ASCII words must stand alone: "licence_stop_guard.py" or "SubagentStop" is not a licence word or a stop word.
_L = r"(?<![A-Za-z0-9_])"
_R = r"(?![A-Za-z0-9_])"

LICENCE = re.compile("|".join([
    r"非商用", r"非商业", r"不能商用", r"不可商用", r"不得商用", r"禁止商用", r"禁商用",
    r"仅限研究", r"研究用途", r"商用许可", r"许可证", r"许可", r"授权",
    _L + r"licen[cs](?:e(?:s|d)?|ing)" + _R,
    _L + r"non[- ]?commercial" + _R,
    _L + r"CC[- ]?BY[- ]?NC" + _R,
    _L + r"OpenRAIL",
    _L + r"research[- ]only" + _R,
]), re.I)

STOP = re.compile("|".join([
    r"停下", r"停手", r"就停", r"已停", r"略过", r"跳过", r"放弃", r"不测", r"不研究", r"不采用", r"不考虑",
    r"排除", r"弃用", r"挡住", r"卡在许可",
    _L + r"(?:skip|drop|stop)(?:s|ped|ping)?" + _R,
    _L + r"exclude[sd]?" + _R, _L + r"excluding" + _R,
    _L + r"block(?:s|ed|ing)?" + _R,
    _L + r"rul(?:e|ed|ing)[ \t]+(?:(?:it|them|this|that|these|those|him|her)[ \t]+)?out" + _R,
    _L + r"can['’]?t use" + _R, _L + r"cannot use" + _R, _L + r"not usable" + _R,
]), re.I)

# A sentence that restates the rule or does what the rule says is not a hit.
EXEMPT = re.compile("|".join([
    r"不是停手理由", r"不作停手理由", r"不作为.{0,6}理由", r"不挡", r"照样", r"照测", r"并排", r"只记一行",
    r"not a reason", r"regardless", r"still test",
    # other ways to say "X is not a reason" ("绝不当作不测、跳过或停手的理由", "不要把许可当作停手理由"); the gap may not
    # cross a comma or full stop, so "不是技术问题，……所以放弃，理由充分" stays a hit
    r"不(?:要|能|得|应|该|会|可)?(?:把[^，,；。！？;!?\n]{0,20})?(?:作为|当作|当成|算作|算|是|作)[^，,；。！？;!?\n]{0,14}理由",
    # negated in front: "没有因为许可略过任何东西", "不会因为非商用就停"
    r"(?:没有|没|并未|从未|绝不会|绝不|不会|不要|不能|不得|不应)因(?:为)?",
    # what the policy asks for: licence limits raised for human review
    _L + r"(?:human|manual|legal) review" + _R, r"人工(?:审核|复核|审查|确认|判断)", r"法务(?:审核|复核|审查|确认)",
    # the policy's own limit: the licence itself does not permit evaluation
    _L + r"(?:not|n['’]t) (?:permit|allow)s? (?:any )?(?:evaluation|evaluating|testing|benchmarking)" + _R,
    _L + r"(?:forbids|prohibits|bans|disallows) (?:any )?(?:evaluation|evaluating|testing|benchmarking)" + _R,
    _L + r"(?:evaluation|testing|benchmarking) (?:is|are) not (?:permitted|allowed)" + _R,
    r"(?:禁止|不允许|不许|不得|不准)(?:任何)?(?:评估|评测|测试|试用|实测)",
]), re.I)

# Long hyphenated slugs are file names (notes such as notes-research-noncommercial-dont-skip-learn-and-build), not prose.
SLUG = re.compile(r"(?<![A-Za-z0-9_-])[a-z0-9]+(?:-[a-z0-9]+){5,}(?![A-Za-z0-9_-])")

# Talking about this very hook is not a stop word: "Stop hook", "Stop 钩子".
HOOK_WORDS = re.compile(_L + r"stop[ \t-]?hooks?" + _R + "|" + _L + r"stop[ \t]*钩子", re.I)

# Sentence ends: 。！？； newline . ; ! ?   ("4.0" inside a version / number is not a sentence end)
SENTENCE = re.compile(r"[。！？；;!?\n\r]|\.(?!\d)|(?<!\d)\.")

QUOTED = [
    re.compile(r"```.*?```", re.S),          # fenced code
    re.compile(r"`[^`\n]*`"),                # inline code
    re.compile(r"「[^」\n]*」"), re.compile(r"『[^』\n]*』"),
    re.compile(r"“[^”\n]*”"), re.compile(r"\"[^\"\n]*\""),
]
ENTRY = re.compile(rb'"type"\s*:\s*"(?:user|assistant)"')


class Deadline(Exception):
    pass


def reason_text():
    """The policy sentence shown to the model: MUSE_LICENCE_GUARD_REASON when set, else DEFAULT_REASON."""
    return os.environ.get(REASON_ENV, "").strip() or DEFAULT_REASON


def strip_quoted(text):
    text = "\n".join(l for l in text.splitlines() if not l.lstrip().startswith(">"))
    for pat in QUOTED:
        text = pat.sub(" ", text)
    return text


def licence_stop_claim(text):
    """The first sentence that holds a licence word and a stop word (and no rule restatement), or None."""
    clean = SLUG.sub(" ", HOOK_WORDS.sub(" ", strip_quoted(text or "")))
    for sentence in SENTENCE.split(clean):
        if LICENCE.search(sentence) and STOP.search(sentence) and not EXEMPT.search(sentence):
            flat = " ".join(sentence.split()).lstrip("-*•·#0123456789. ")
            return flat[:80] + ("…" if len(flat) > 80 else "")
    return None


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


def assistant_texts(turn):
    """Every assistant text block of one turn, oldest first (each block is judged on its own)."""
    out = []
    for e in turn:
        content = (e.get("message") or {}).get("content")
        if e.get("type") != "assistant" or not isinstance(content, list):
            continue
        for b in content:
            if isinstance(b, dict) and b.get("type") == "text" and isinstance(b.get("text"), str):
                out.append(b["text"])
    return out


def block(sentence):
    return {"decision": "block", "reason": "%s\n%s%s\"%s\"" % (reason_text(), REWORD, MATCHED, sentence)}


def decide(data):
    """The block decision dict, or None to let the stop through."""
    if data.get("stop_hook_active"):
        return None
    msg = data.get("last_assistant_message")
    if isinstance(msg, str):
        hit = licence_stop_claim(msg)
        if hit:
            return block(hit)                # the final answer itself: no need to read the transcript
    path = data.get("transcript_path")
    if not path or not os.path.isfile(path):
        return None
    turn = read_turn(path)
    if turn is None:
        return None
    for text in assistant_texts(turn):
        hit = licence_stop_claim(text)
        if hit:
            return block(hit)
    return None


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
    sid = "00000000-0000-4000-8000-0000000000bb"
    rows, parent = [], None

    def add(row):
        nonlocal parent
        row.update({"uuid": str(uuid.uuid4()), "parentUuid": parent, "sessionId": sid,
                    "isSidechain": False, "timestamp": "2026-10-24T06:00:00.000Z", "version": "2.1.x",
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
            else:                                   # ("bash", command)
                tid = "toolu_" + uuid.uuid4().hex[:20]
                assistant({"type": "tool_use", "id": tid, "name": "Bash", "caller": {"type": "direct"},
                           "input": {"command": value, "description": "Read the paper"}})
                add({"type": "user", "toolUseResult": {"stdout": "ok", "stderr": "", "interrupted": False,
                                                       "isImage": False, "noOutputExpected": False},
                     "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": tid,
                                                              "content": [{"type": "text", "text": "ok"}],
                                                              "is_error": False}]}})
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
                      "Stop": [{"hooks": [{"type": "command", "command": "/x/negative_claim_guard.py", "timeout": 3}]},
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
    d = tempfile.mkdtemp(prefix="lsg-selftest-")
    q = "帮我看下 ExampleModel、OtherModel、SampleLib 这几个开源项目能不能用"
    clean = "已读完论文与代码，下一步用我们自己的输入并排实测。"
    c_env = {"LC_ALL": "C", "LANG": "C", "PATH": "/usr/bin:/bin"}
    missing = os.path.join(d, "missing.jsonl")

    def t(name, steps, **kw):
        return _fixture(d, name, q, steps, **kw)

    # (id, label, transcript path or None for non-JSON stdin, extra stdin fields, env, expect_block); block cases first
    cases = [
        ("B1", "Chinese: non-commercial licence, so skipped", t("B1", [("text", "ExampleModel 是非商用许可，所以略过。")]),
         {}, None, True),
        ("B2", "English: non-commercial, so we drop it",
         t("B2", [("text", "ExampleNet trained on SampleSet, non-commercial, so we drop it.")]), {}, None, True),
        ("B3", "list item without a full stop: stop and report on non-commercial",
         t("B3", [("text", "好的，我这样安排：\n- 任何一处是非商用就停下报我")]), {}, None, True),
        ("B4", "blocked by an OpenRAIL licence, not tested", t("B4", [("text", "SampleLib 被 OpenRAIL 许可挡住，不测了。")]),
         {}, None, True),
        ("B5", "English: research-only ... ruled it out",
         t("B5", [("text", "The weights are research-only, so we ruled it out.")]), {}, None, True),
        ("B6", "hit only in last_assistant_message (Claude Code sends it); transcript clean",
         t("B6", [("text", clean)]), {"last_assistant_message": "OtherModel 的许可是非商用，我们先放弃。"}, None, True),
        ("B7", "hit in an earlier text of this turn, final text clean",
         t("B7", [("text", "OtherModel 许可证写着非商用，先跳过。"), ("bash", "ls"), ("text", clean)]), {}, None, True),
        ("B8", "an isMeta insert (skill load) after the hit does not cut the turn",
         t("B8", [("text", "SampleLib 是 OpenRAIL 许可，先不测。"), ("meta", "Base directory for this skill: x"),
                  ("text", clean)]), {}, None, True),
        ("B9", "started under the C locale (stdin/stdout do not depend on it)",
         t("B9", [("text", "ExampleModel 是非商用许可，所以略过。")]), {}, c_env, True),
        ("B10", "hit only in last_assistant_message, transcript missing", missing,
         {"last_assistant_message": "Licence is CC BY-NC, excluded."}, None, True),
        ("B11", "a comma between 不是 and 理由: not a restatement of the rule",
         t("B11", [("text", "不是技术问题，SampleLib 是 OpenRAIL 许可，所以放弃，理由充分。")]), {}, None, True),
        ("B12", "the licence named as the reason not to test: exactly what is blocked",
         t("B12", [("text", "ExampleModel 的非商用许可是不测的理由。")]), {}, None, True),
        ("B13", "因为非商用，所以略过: affirmative, blocked",
         t("B13", [("text", "因为非商用，所以略过 OtherModel。")]), {}, None, True),
        ("P1", "licence recorded in one line, then a side-by-side test",
         t("P1", [("text", "许可：CC BY-NC 4.0（一行事实）。下一步并排实测。")]), {}, None, False),
        ("P2", "restates the rule: not a reason to stop, test anyway", t("P2", [("text", "许可不是停手理由，照测。")]),
         {}, None, False),
        ("P3", "inside quotes (「」『』“”\"\")",
         t("P3", [("text", "上次的计划写了「非商用就停」，这是错的。\n另一处『许可挡住就略过』也不对。\n"
                           "那句“license blocked, skip”，还有\"non-commercial so drop\"。")]), {}, None, False),
        ("P4", "inside a code block and inline code",
         t("P4", [("text", "命令：\n```\necho 'non-commercial -> skip'\n```\n行内 `license: skip` 也不算。")]), {}, None, False),
        ("P5", "stop_hook_active=true (never loops)",
         t("P5", [("text", "ExampleModel 是非商用许可，所以略过。")]), {"stop_hook_active": True}, None, False),
        ("P6", "a stop word with no licence word", t("P6", [("text", "测试跑完就停。")]), {}, None, False),
        ("P7", "hit only in the previous turn, this turn clean",
         t("P7", [("text", clean)], prior=(q, [("text", "SampleLib 是非商用许可，所以略过。")])), {}, None, False),
        ("P8", "a > block-quote line", t("P8", [("text", "> 许可：非商用，略过\n以上是旧写法。")]), {}, None, False),
        ("P9", "English restatement: not a reason ... still test",
         t("P9", [("text", "The license is non-commercial, but that is not a reason to skip it; we still test it.")]),
         {}, None, False),
        ("P10", "follows the rule: OpenRAIL in one line, side-by-side test anyway",
         t("P10", [("text", "SampleLib 许可 OpenRAIL，只记一行，照样并排实测。")]), {}, None, False),
        ("P11", "talks about this hook itself (file name, Stop hook)",
         t("P11", [("text", "licence_stop_guard.py 已装好；这个 Stop 钩子会检查许可。")]), {}, None, False),
        ("P12", "the full stop after version 4.0 still ends the sentence",
         t("P12", [("text", "Model card license: CC BY-NC 4.0. Tests pass; we stop the dev server now.")]), {}, None, False),
        ("P15", "restates the rule: never a reason to skip or stop",
         t("P15", [("text", "许可只在报告里记一行事实，绝不当作不测、跳过或停手的理由。")]), {}, None, False),
        ("P16", "restates the rule: do not treat the licence as a reason to give up",
         t("P16", [("text", "不要把 OpenRAIL 许可当作放弃的理由。")]), {}, None, False),
        ("P17", "a long hyphenated file name holding noncommercial and skip",
         t("P17", [("text", "笔记里已有同一条（notes-research-noncommercial-dont-skip-learn-and-build），不用另写。")]),
         {}, None, False),
        ("P18", "negated in front: nothing was skipped because of a licence",
         t("P18", [("text", "这次的界面规范只用了两套字体，没有因为许可略过任何东西。")]), {}, None, False),
        ("P19", "the policy's own step: licence limits go to human review",
         t("P19", [("text", "The research-only licence goes to human review before production use, so we skip shipping it for now.")]),
         {}, None, False),
        ("P20", "the licence itself forbids evaluation (Chinese), raised for review",
         t("P20", [("text", "许可证明确禁止任何评估，所以不测，已交人工审核。")]), {}, None, False),
        ("P21", "the licence itself does not permit evaluation (English)",
         t("P21", [("text", "The licence does not permit evaluation, so we skip it.")]), {}, None, False),
        ("P13", "transcript missing and no last_assistant_message (fail open)", missing, {}, None, False),
        ("P14", "stdin is not JSON (fail open)", None, None, None, False),
    ]
    failures, blocks, passes = 0, 0, 0
    for cid, label, path, extra, env, expect_block in cases:
        if path is None:
            stdin = b"not json {"
        else:
            payload = {"session_id": "00000000-0000-4000-8000-0000000000bb", "transcript_path": path,
                       "cwd": d, "permission_mode": "default", "hook_event_name": "Stop", "stop_hook_active": False}
            payload.update(extra)
            stdin = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        rc, out, err = _run_hook(stdin, env)
        try:
            parsed = json.loads(out) if out else None
        except ValueError:
            parsed = None
        blocked = bool(parsed) and parsed.get("decision") == "block" and MATCHED in parsed.get("reason", "")
        ok = blocked == expect_block and rc == 0 and not err and (bool(out) == expect_block)
        failures += not ok
        blocks += bool(expect_block)
        passes += not expect_block
        print("%s %-4s %s -> %s (exit %d%s)" % ("PASS" if ok else "FAIL", cid, label, "block" if blocked else "pass", rc,
                                               ", stderr not empty" if err else ""))
        if parsed and cid in ("B1", "B2", "B3", "B4", "B10", "B11", "B12"):
            print("        matched: %s" % parsed["reason"].split(MATCHED, 1)[-1])
    total = len(cases)
    inst_dir = os.path.join(d, "inst")
    os.makedirs(inst_dir)
    inst = _selftest_install(inst_dir)
    for cid, label, ok in inst:
        failures += not ok
        print("%s %-4s %s" % ("PASS" if ok else "FAIL", cid, label))
    total += len(inst)
    print("hook decisions: %d must block, %d must pass; install round trip: %d" % (blocks, passes, len(inst)))
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
