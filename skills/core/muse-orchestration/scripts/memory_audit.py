#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""memory_audit.py - audit and cross-link Claude Code auto-memory directories.

Why: Claude Code keeps one auto-memory directory per project
(<projects_root>/<project-dir>/memory/ = MEMORY.md + topic files). A session loads only its
own MEMORY.md, and only the first part of it, so a decision recorded in one project's memory
is invisible to sessions started in another project. This tool checks that the directories
stay consistent and visible to each other and, with --sync, writes a generated cross-dir
block into every MEMORY.md plus one cross-dir index file.

Loaded-part limits (memory.index_max_lines / memory.index_max_chars)
    The 200-line limit comes from the Claude Code memory documentation. The 25,000-character
    limit (counted in UTF-16 code units, i.e. JavaScript string length) was observed in one
    client build and is not documented. Check your own client version and set both keys to
    match it.

Modes
    python3 -I memory_audit.py            read-only audit. Last line: RESULT: GREEN|RED (...)
    python3 -I memory_audit.py --sync     write/refresh the cross-dir block in every MEMORY.md and
                                          regenerate the cross-dir index (needs a config file)
    python3 -I memory_audit.py --unsync   remove the cross-dir block from every MEMORY.md
                                          (exact byte-for-byte rollback of what --sync inserted)
    options: --config PATH, --projects-root DIR (alias --root), --json, --all,
             --days N (checkpoint window, default 7), --today YYYY-MM-DD / --now "YYYY-MM-DD HH:MM"

Configuration: `.muse/orchestration.json`, loaded by orchestration_config.py (see its docstring
for the lookup order). Without a config file the tool still audits what it can discover on
its own (every <projects_root>/*/memory directory, default projects root ~/.claude/projects)
and reports every other check as UNCONFIGURED; it never guesses paths. --sync refuses to run
without a config file; --unsync does not need one.

Checks (FAIL -> RED; WARN, SKIP and UNCONFIGURED do not change the result)
     1 dirs     every memory dir has MEMORY.md; the hub and labelled dirs exist;
                no memory dir appeared since the last --sync
     2 index    every index link resolves; every topic file is indexed (MEMORY.md plus one hop
                through linked index-*.md sub-indexes); index within the loaded-part limits
     3 block    every MEMORY.md carries a fresh cross-dir block inside its loaded part (>= 2 dirs)
     4 xindex   the cross-dir index exists and is fresh (>= 2 dirs)
     5 hub      decision / watch-term memory files of other dirs are named in the hub's loaded
                index (memory.hub; SKIP when null)
     6 terms    every watch term found in any memory file appears in every dir's loaded index
     7 backlog  owner decision lines and watch-term comparison lines in checkpoint files of the
                last N days have a memory (owner.*, checkpoints.*; SKIP without owner)
     8 vault    the notes vault was written within vault.freshness_hours while checkpoint files
                changed within vault.active_hours
     9 daily    memory/<today>.md exists in some checkout (git worktree) of every
                memory.daily_projects entry (yesterday's file also counts before 02:00)
    10 recall   the recall tool exists (memory.recall, default recall.py next to this script)
    11 keys     key-pattern scan of every memory dir, the cross-dir index and
                memory.scan_extra_paths; reports file:line and pattern name, never the value

Standard library only, Python 3.7+, no network. Never opens .env* files.
"""
from __future__ import print_function

import sys

sys.dont_write_bytecode = True  # loading the sibling config module must not leave __pycache__ behind

import argparse  # noqa: E402
import datetime  # noqa: E402
import fnmatch  # noqa: E402
import glob  # noqa: E402
import importlib.util  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import stat  # noqa: E402
import subprocess  # noqa: E402
import time  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SELF = os.path.abspath(__file__)


def _load_config_module():
    # python3 -I does not put the script directory on sys.path, so load the sibling by path.
    spec = importlib.util.spec_from_file_location("orchestration_config", os.path.join(HERE, "orchestration_config.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


OC = _load_config_module()
ConfigError = OC.ConfigError

PASS, WARN, FAIL, SKIP, UNCONF = "PASS", "WARN", "FAIL", "SKIP", "UNCONFIGURED"

DEFAULT_PROJECTS_ROOT = "~/.claude/projects"
DEFAULT_MAX_LINES = 200      # Claude Code memory docs: first 200 lines of MEMORY.md are loaded
DEFAULT_MAX_CHARS = 25000    # observed in one client build, not documented; configure per version
NEAR_LINES_RATIO = 0.95      # WARN once an index passes 95% of the line limit ...
NEAR_CHARS_RATIO = 0.94      # ... or 94% of the character limit
DEFAULT_BLOCK_MAX_AGE_H = 36
DEFAULT_CROSS_INDEX = ".muse/memory-cross-index.md"
DEFAULT_VAULT_FRESH_H = 24
DEFAULT_VAULT_ACTIVE_H = 6
HUB_BLOCK_CAP, OTHER_BLOCK_CAP = 10, 4   # decision files listed in the hub's / other dirs' block
TERMS_PER_LINE = 8
BEGIN = "<!-- CROSS-DIR:BEGIN"
END = "<!-- CROSS-DIR:END -->"

DEFAULT_DECISION_FILE_PATTERN = r"decision|provider|vendor|sota|comparison|evaluat|benchmark|pricing|payout|refund"
DEFAULT_DECISION_WORDS = ["decided", "approved", "chose", "go with", "定", "拍板", "裁定", "选定", "按建议", "批准", "同意"]
DEFAULT_SKIP_PATTERN = r"巡检|哨兵|早报|晚报|patrol|sentinel|morning report|evening report|daily report"

# (name, regex) - reported as file:line + name only, never the value
BUILTIN_KEY_PATTERNS = [
    # real OpenAI / Anthropic style keys are 40+ chars after "sk-"; >= 32 skips short test samples
    # and words such as task-identity (the lookbehind keeps "task-" from matching).
    ("sk-", r"(?<![A-Za-z0-9])sk-(?:proj-|ant-[a-z0-9]{2,6}-)?[A-Za-z0-9_-]{32,}"),
    ("AIzaSy", r"AIzaSy[A-Za-z0-9_-]{20,}"),
    ("AQ.", r"(?<![A-Za-z0-9.])AQ\.[A-Za-z0-9_-]{20,}"),
    ("xai-", r"(?<![A-Za-z0-9])xai-[A-Za-z0-9]{20,}"),
    ("gsk_", r"(?<![A-Za-z0-9])gsk_[A-Za-z0-9]{20,}"),
    ("sk_test_", r"sk_test_[A-Za-z0-9]{10,}"),
    ("pk_test_", r"pk_test_[A-Za-z0-9]{10,}"),
    ("sk_live_", r"(?<![A-Za-z0-9])[sr]k_live_[A-Za-z0-9]{10,}"),
    ("eyJhbG", r"eyJhbG[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    ("ghp_", r"(?<![A-Za-z0-9])(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{22,})"),
    ("AKIA", r"(?<![A-Z0-9])AKIA[0-9A-Z]{16}(?![A-Z0-9])"),
    ("xox", r"(?<![A-Za-z0-9])xox[abprs]-[A-Za-z0-9-]{10,}"),
    ("private-key", r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE" + r" KEY-----"),
]


def _key_selftest_samples():
    """Synthetic positives built at run time so this file carries no key-shaped literal."""
    return {"sk-": "sk-" + "Ab3x" * 12, "AIzaSy": "AIzaSy" + "Q9z-" * 8, "AQ.": " AQ." + "Ab3_" * 8,
            "xai-": "xai-" + "Ab3x" * 8, "gsk_": "gsk_" + "Ab3x" * 8, "sk_test_": "sk_test_" + "Ab3x" * 4,
            "pk_test_": "pk_test_" + "Ab3x" * 4, "sk_live_": "rk_live_" + "Ab3x" * 4,
            "eyJhbG": "eyJhbG" + "ciOiJIUzI1" + "." + "eyJzdWIiOiIx", "ghp_": "ghp_" + "Ab3x" * 9,
            "AKIA": "AKIA" + "QX7T" * 4, "xox": "xoxb-" + "1234-" * 3 + "Ab3x" * 3,
            "private-key": "-----BEGIN " + "RSA PRIVATE" + " KEY-----"}


KEY_SELFTEST_NEGATIVES = ("2d-task-identity", "desk-lamp-14-showcase-kinds-x", "risk-assessment-2026")
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+\.md)\)")
SECRET_RE = re.compile(r"(sk-[A-Za-z0-9_-]{6,}|AIzaSy[\w-]{6,}|\bAQ\.[\w-]{6,}|xai-[\w-]{6,}|gsk_[\w-]{6,}|"
                       r"sk_test_[\w-]{4,}|pk_test_[\w-]{4,}|eyJhbG[\w.-]{6,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}|"
                       r"\+?\d[\d\s-]{9,}\d)")

# checkpoint decision lines
SEC_RE = re.compile(r"^#+.*?(?:(20\d\d)-(\d\d)-(\d\d)|(?<![\d.])(\d{1,2})/(\d{1,2})(?![\d/]))")
TIME_RE = re.compile(r"^\s*[-*]?\s*\**\s*(\d{1,2}):(\d)")
CMP_RE = re.compile(r"评估|对比|横评|SOTA|\bvs\.?\b|优于|胜出|更像|更好|排名|排 |compar|benchmark|evaluat|"
                    r"better than|worse than|outperform|\bbeats?\b|\branked\b|ranking", re.I)
P2V_GENERIC = (r"定|拍板|决定|按建议|同意|批|改为|取代|必须|不准|不要|不用|以后|一律|只用|换成|"
               r"(?i:(?<![A-Za-z])(?:must|never|always|only|instead|from now on|do not|don't|stop|switch to)(?![A-Za-z]))")
QUOTE_RES = [re.compile(r"「([^」]{6,})」"), re.compile(r"“([^”]{6,})”"), re.compile(r"\"([^\"\n]{6,})\"")]
DECISION_CAT = r"(?i:decision)|决定|拍板"
WATCH_CAT = r"provider|vendor|供应商|sota"
MONEY_CAT = (r"pric|定价|积分|points|payout|提现|\bfee\b|抽成|佣金|refund|退款|payment|支付|\bcost|成本|budget|预算|"
             r"\$\d|¥\d|€\d|余额|balance|billing|invoice|\btax|税|revenue|commission|cash|融资|fundrais|valuation|估值")
STOPW = set("which there their these those about after before would could should where while still being other every "
            "never always first second third today night later again since until under above below without within "
            "between because through during maybe".split())
CJK_RE = re.compile(r"[\u3400-\u9fff\uf900-\ufaff]")


# ---------------------------------------------------------------- helpers
def u16len(s):
    """Length in UTF-16 code units (what a JavaScript string length reports)."""
    return len(s.encode("utf-16-le")) // 2


def read_text(path, strict=False):
    # newline="" keeps \r\n as-is so --sync / --unsync can round-trip a file byte for byte
    with open(path, encoding="utf-8", errors="strict" if strict else "replace", newline="") as fh:
        return fh.read()


def tilde(path):
    if not path:
        return path
    home = os.path.expanduser("~")
    path = str(path)
    if home and home != "/" and (path == home or path.startswith(home.rstrip(os.sep) + os.sep)):
        return "~" + path[len(home.rstrip(os.sep)):]
    return path


def plural(n, word):
    return "%d %s%s" % (n, word, "" if n == 1 else "s")


def short(s, n):
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def front(text):
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    d = {}
    if m:
        for line in m.group(1).splitlines():
            mm = re.match(r"^(\w+):\s*(.*)$", line)
            if mm:
                d[mm.group(1)] = mm.group(2).strip().strip('"')
    return d


def atomic_write(path, text, expect_mtime=None):
    """Write through a temp file + os.replace; refuse (False) when the file changed since expect_mtime."""
    if expect_mtime is not None and os.path.getmtime(path) != expect_mtime:
        return False
    tmp = path + ".tmp-memaudit-%d" % os.getpid()
    try:
        with open(tmp, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        if os.path.exists(path):
            try:
                os.chmod(tmp, stat.S_IMODE(os.stat(path).st_mode))
            except OSError:
                pass
        if expect_mtime is not None and os.path.getmtime(path) != expect_mtime:
            return False
        os.replace(tmp, path)
        tmp = None
        return True
    finally:
        if tmp and os.path.exists(tmp):
            os.remove(tmp)


# ---------------------------------------------------------------- configuration
def _cfg_type(value, kinds, key):
    """Return value when it is None or of the wanted type(s); bool never passes for a number."""
    kinds = kinds if isinstance(kinds, tuple) else (kinds,)
    if value is None:
        return None
    if (isinstance(value, bool) and bool not in kinds) or not isinstance(value, kinds):
        raise ConfigError("CONFIG_INVALID: %s has the wrong type" % key)
    return value


def _cfg_number(value, default, key, integer=False):
    _cfg_type(value, int if integer else (int, float), key)
    if value is None:
        return default
    if value <= 0:
        raise ConfigError("CONFIG_INVALID: %s must be positive" % key)
    return value


def _cfg_regex(pattern, key, flags=0):
    try:
        return re.compile(pattern, flags)
    except re.error as error:
        raise ConfigError("CONFIG_INVALID: %s: %s" % (key, error))


def _cfg_named_patterns(value, key, flags):
    out = []
    for i, item in enumerate(_cfg_type(value, list, key) or []):
        where = "%s[%d]" % (key, i)
        if not isinstance(item, dict) or not isinstance(item.get("name"), str) or not item.get("name") \
                or not isinstance(item.get("pattern"), str) or not item.get("pattern"):
            raise ConfigError("CONFIG_INVALID: %s needs a non-empty name and pattern" % where)
        compare = _cfg_type(item.get("compare", True), bool, where + ".compare")
        out.append((item["name"], _cfg_regex(item["pattern"], where + ".pattern", flags), item["pattern"], compare))
    return out


def _word_rx(word, strict):
    parts = [re.escape(p) for p in word.split()]
    if not parts:
        return None
    body = r"\s+".join(parts)
    if all(ord(c) < 128 for c in word):
        return r"(?i:(?<![A-Za-z0-9_])%s(?![A-Za-z0-9_]))" % body
    if strict and len(word.strip()) == 1 and CJK_RE.match(word.strip()):
        # a single CJK character such as 定 counts only when punctuation, space or 了 follows,
        # so compounds that merely contain it do not read as decisions
        return body + r"(?=[：:（(，,「」了\s。.;；]|$)"
    return body


def _name_rx(name):
    body = r"\s+".join(re.escape(p) for p in name.split())
    pre = r"(?<![A-Za-z0-9_])" if re.match(r"[A-Za-z0-9_]", name) else ""
    post = r"(?![A-Za-z0-9_])" if re.search(r"[A-Za-z0-9_]$", name) else ""
    return pre + body + post


def owner_regexes(name, words):
    """-> dict of compiled regexes for 'the owner decided' lines, built from owner.name + owner.decision_words."""
    n = _name_rx(name)
    loose = "|".join(x for x in (_word_rx(w, False) for w in words) if x)
    strict = "|".join(x for x in (_word_rx(w, True) for w in words) if x)
    date = r"(?:[(（]?\d{1,2}[:/]\d{1,2}[)）]?\S{0,3}\s*)?"
    filler = r"(?:(?i:has|had|have)\s+|已经?|[:：]\s*)?"
    decided = r"✅\s*%s\s*\S{0,6}?(?:%s)|%s\s*%s%s(?:%s)" % (n, loose, n, date, filler, strict)
    pending = (r"(?:等|待|请|问|需|要)\s*{n}|{n}\s*(?:待定|未定)|"
               r"(?i:waiting\s+(?:for|on)|awaiting|ask(?:ing)?|pending|needs?)\s+{n}|"
               r"{n}\s+(?i:to\s+decide|undecided|has\s+not\s+decided|hasn't\s+decided|will\s+decide)").format(n=n)
    quote = r"%s[^「“\"\n]{0,24}(?:原话|(?i:verbatim|said|wrote)|「|“|\")" % n
    return {"decided": re.compile(decided), "pending": re.compile(pending), "quote": re.compile(quote),
            "quote_verb": re.compile(P2V_GENERIC + ("|" + loose if loose else "")), "decided_src": decided}


class Settings(object):
    """Everything the audit needs, read once from the config (or from defaults when there is none)."""

    def __init__(self, config, args):
        get = config.get
        self.config = config
        self.configured = config.path is not None
        self.config_path = str(config.path) if config.path else None
        _cfg_type(get("memory"), dict, "memory")
        if args.projects_root:
            self.projects_root = os.path.abspath(os.path.expanduser(args.projects_root))
        elif _cfg_type(get("memory.projects_root"), str, "memory.projects_root"):
            self.projects_root = os.path.abspath(str(config.path_of(get("memory.projects_root"))))
        else:
            self.projects_root = os.path.abspath(os.path.expanduser(DEFAULT_PROJECTS_ROOT))
        labels = _cfg_type(get("memory.labels"), dict, "memory.labels") or {}
        for k, v in labels.items():
            if not isinstance(v, str) or not v:
                raise ConfigError("CONFIG_INVALID: memory.labels[%s] must be a non-empty string" % k)
        self.labels = dict(labels)
        self.ignore = [str(p) for p in (_cfg_type(get("memory.ignore"), list, "memory.ignore") or [])]
        hub = _cfg_type(get("memory.hub"), str, "memory.hub") or None
        if hub and hub not in self.labels:
            reverse = [k for k, v in self.labels.items() if v == hub]
            hub = reverse[0] if len(reverse) == 1 else hub
        self.hub = hub
        self.max_lines = _cfg_number(get("memory.index_max_lines"), DEFAULT_MAX_LINES, "memory.index_max_lines", True)
        self.max_chars = _cfg_number(get("memory.index_max_chars"), DEFAULT_MAX_CHARS, "memory.index_max_chars", True)
        self.near_lines = int(self.max_lines * NEAR_LINES_RATIO)
        self.near_chars = int(self.max_chars * NEAR_CHARS_RATIO)
        self.block_max_age_h = _cfg_number(get("memory.block_max_age_hours"), DEFAULT_BLOCK_MAX_AGE_H,
                                           "memory.block_max_age_hours")
        self.terms = _cfg_named_patterns(get("memory.watch_terms"), "memory.watch_terms", re.I)
        dfp = _cfg_type(get("memory.decision_file_pattern"), str, "memory.decision_file_pattern") \
            or DEFAULT_DECISION_FILE_PATTERN
        self.decision_file_re = _cfg_regex("|".join([dfp] + ["(?:%s)" % src for _, _, src, _ in self.terms]),
                                           "memory.decision_file_pattern", re.I)
        xi = _cfg_type(get("memory.cross_index"), str, "memory.cross_index") or DEFAULT_CROSS_INDEX
        self.cross_index = str(config.path_of(xi)) if self.configured else None
        recall = _cfg_type(get("memory.recall"), str, "memory.recall")
        self.recall = str(config.path_of(recall)) if recall else os.path.join(HERE, "recall.py")
        extra = _cfg_type(get("memory.scan_extra_paths"), list, "memory.scan_extra_paths")
        self.scan_extra = [str(p) for p in config.paths("memory.scan_extra_paths")] if extra else []
        self.key_patterns = [(n, re.compile(p)) for n, p in BUILTIN_KEY_PATTERNS] + \
            [(n, rx) for n, rx, _, _ in _cfg_named_patterns(get("memory.extra_key_patterns"),
                                                             "memory.extra_key_patterns", 0)]
        self.daily = []
        for i, item in enumerate(_cfg_type(get("memory.daily_projects"), list, "memory.daily_projects") or []):
            if not isinstance(item, dict) or not isinstance(item.get("root"), str) or not item.get("root"):
                raise ConfigError("CONFIG_INVALID: memory.daily_projects[%d] needs a root" % i)
            self.daily.append((str(item.get("name") or item["root"]), str(config.path_of(item["root"]))))
        for key in ("checkpoints.files", "checkpoints.globs"):
            _cfg_type(get(key), list, key)
        self.checkpoints_configured = bool(get("checkpoints.files") or get("checkpoints.globs"))
        self._checkpoint_files = None
        skip = _cfg_type(get("checkpoints.skip_pattern"), str, "checkpoints.skip_pattern") or DEFAULT_SKIP_PATTERN
        self.skip_re = _cfg_regex(skip, "checkpoints.skip_pattern", re.I)
        _cfg_type(get("owner"), dict, "owner")
        self.owner = _cfg_type(get("owner.name"), str, "owner.name") or None
        words = _cfg_type(get("owner.decision_words"), list, "owner.decision_words") or DEFAULT_DECISION_WORDS
        if any(not isinstance(w, str) for w in words):
            raise ConfigError("CONFIG_INVALID: owner.decision_words must be strings")
        self.owner_rx = owner_regexes(self.owner, words) if self.owner else None
        self.vault = str(config.vault_root()) if self.configured and config.vault_root() else None
        self.vault_fresh_h = _cfg_number(get("vault.freshness_hours"), DEFAULT_VAULT_FRESH_H, "vault.freshness_hours")
        self.vault_active_h = _cfg_number(get("vault.active_hours"), DEFAULT_VAULT_ACTIVE_H, "vault.active_hours")
        self.money_re = re.compile(MONEY_CAT, re.I)
        self.watch_cat_re = re.compile("|".join([WATCH_CAT] + ["(?:%s)" % src for _, _, src, _ in self.terms]), re.I)
        self.decision_cat_re = re.compile(DECISION_CAT + ("|" + self.owner_rx["decided_src"] if self.owner_rx else ""))

    def ignored(self, name):
        return any(fnmatch.fnmatchcase(name, pat) for pat in self.ignore)

    def checkpoint_files(self):
        if self._checkpoint_files is None:
            seen, out = set(), []
            listed = [p for p in self.config.paths("checkpoints.files") if p.is_file()]
            for f in listed + self.config.globbed("checkpoints.globs"):
                real = os.path.realpath(str(f))
                if real not in seen:
                    seen.add(real)
                    out.append(str(f))
            self._checkpoint_files = out
        return self._checkpoint_files

    def mask(self, s):
        for _, rx in self.key_patterns:
            s = rx.sub("[masked]", s)
        return SECRET_RE.sub("[masked]", s)


# ---------------------------------------------------------------- memory dirs
def loaded_part(S, index_text):
    """Approximate what the client loads: trimmed text, first max_lines lines, then first max_chars."""
    t = index_text.strip()
    lines = t.split("\n")
    over_lines = len(lines) > S.max_lines
    t2 = "\n".join(lines[: S.max_lines])
    over_chars = u16len(t2) > S.max_chars
    if over_chars:
        acc, keep = 0, []
        for ln in t2.split("\n"):
            acc += u16len(ln) + 1
            if acc > S.max_chars:
                break
            keep.append(ln)
        t2 = "\n".join(keep)
    return t2, over_lines, over_chars


def find_block(text):
    """-> (begin, end) of the generated block or None; ValueError when BEGIN has no END."""
    b = text.find(BEGIN)
    if b < 0:
        return None
    e = text.find(END, b)
    if e < 0:
        raise ValueError("unterminated cross-dir block")
    return b, e + len(END)


def split_block(text):
    """-> (block text or None, block time or None, unterminated flag)"""
    try:
        span = find_block(text or "")
    except ValueError:
        return None, None, True
    if span is None:
        return None, None, False
    block = text[span[0]:span[1]]
    m = re.search(r"(\d{4}-\d\d-\d\d \d\d:\d\d)", block[:200])
    bt = datetime.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M") if m else None
    return block, bt, False


def insert_block(text, block):
    """Replace the block in place, or insert it after the first '# ' heading line (else at the top).

    A fresh insert adds exactly "\\n" + block + "\\n" after the heading line, or block + "\\n" at the
    top, so remove_block() can take back exactly those characters."""
    span = find_block(text)
    if span:
        return text[: span[0]] + block + text[span[1]:]
    start = 1 if text.startswith("\ufeff") else 0
    if text.startswith("# ", start) and "\n" in text[start:]:
        cut = text.index("\n", start) + 1
        return text[:cut] + "\n" + block + "\n" + text[cut:]
    return text[:start] + block + "\n" + text[start:]


def remove_block(text):
    span = find_block(text)
    if span is None:
        return text
    b, e = span
    if e < len(text) and text[e] == "\n":
        e += 1
    if b >= 2 and text[b - 2:b] == "\n\n":
        b -= 1
    return text[:b] + text[e:]


def discover(S):
    """-> (dirs: name -> info, order: [names])"""
    names = []
    root = S.projects_root
    if os.path.isdir(root):
        for entry in sorted(os.listdir(root)):
            mdir = os.path.join(root, entry, "memory")
            if not os.path.isdir(mdir) or S.ignored(entry):
                continue
            try:
                has_md = any(f.endswith(".md") for f in os.listdir(mdir))
            except OSError:
                has_md = True  # unreadable: keep it so check 1 reports it
            if has_md or entry in S.labels or entry == S.hub:
                names.append(entry)
    for entry in list(S.labels) + ([S.hub] if S.hub else []):
        if entry not in names and not S.ignored(entry):
            names.append(entry)
    dirs = dict((n, load_dir(S, n)) for n in names)
    order = sorted(names, key=lambda n: (0 if n == S.hub else 1, dirs[n]["label"].lower(), n))
    return dirs, order


def load_dir(S, name):
    mdir = os.path.join(S.projects_root, name, "memory")
    info = {"name": name, "label": S.labels.get(name, name), "dir": mdir, "ok": os.path.isdir(mdir),
            "index_path": os.path.join(mdir, "MEMORY.md"), "index": None, "files": {}, "hooks": {}, "error": None}
    if not info["ok"]:
        return info
    try:
        entries = sorted(os.listdir(mdir))
    except OSError as error:
        info["ok"], info["error"] = False, str(error)
        return info
    if os.path.isfile(info["index_path"]):
        try:
            info["index"] = read_text(info["index_path"])
        except (IOError, OSError) as error:
            info["error"] = str(error)
    for bn in entries:
        path = os.path.join(mdir, bn)
        if bn == "MEMORY.md" or not bn.endswith(".md") or not os.path.isfile(path):
            continue
        try:
            text = read_text(path)
        except (IOError, OSError):
            continue
        info["files"][bn] = {"path": path, "text": text, "desc": front(text).get("description", ""),
                             "mtime": os.path.getmtime(path)}
    for line in (info["index"] or "").split("\n"):
        m = LINK_RE.search(line)
        if m:
            info["hooks"].setdefault(os.path.basename(m.group(2)), line.split("—", 1)[1].strip() if "—" in line else "")
    return info


def file_hook(S, info, bn):
    h = info["hooks"].get(bn) or info["files"][bn]["desc"]
    h = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", h)
    return S.mask(short(h, 120))


def newest(info):
    ts = [r["mtime"] for r in info.get("files", {}).values()]
    return max(ts) if ts else None


def usable(info):
    return info["ok"] and info.get("index") is not None


def decision_files(S, dirs, order, exclude=None):
    out = []
    for name in order:
        info = dirs[name]
        if name == exclude or not info["ok"]:
            continue
        for bn, r in info["files"].items():
            if S.decision_file_re.search(bn):
                out.append((name, bn, r["mtime"]))
    return out


def term_map(S, dirs, order):
    m = {}
    for tname, rx, _, _ in S.terms:
        hits = []
        for name in order:
            info = dirs[name]
            if not info["ok"]:
                continue
            for bn, r in info["files"].items():
                if rx.search(r["text"]):
                    score = (1 if S.decision_file_re.search(bn) or rx.search(bn) else 0, r["mtime"])
                    hits.append((score, name, bn))
        if hits:
            hits.sort(reverse=True)
            m[tname] = hits
    return m


# ---------------------------------------------------------------- block + cross index
def sync_command(S):
    return "python3 -I %s%s --sync" % (SELF, " --config %s" % S.config_path if S.config_path else "")


def recall_command(S):
    return "python3 -I %s%s <term> ..." % (S.recall, " --config %s" % S.config_path if S.config_path else "")


def build_block(S, dirs, order, name, now):
    lab = lambda n: dirs[n]["label"]  # noqa: E731
    lines = [BEGIN + " memory_audit.py --sync %s · generated, do not edit (the next --sync overwrites it); "
             "this dir's own index continues below -->" % now.strftime("%Y-%m-%d %H:%M")]
    parts = []
    for n in order:
        info = dirs[n]
        if not info["ok"]:
            parts.append("%s=missing" % lab(n))
            continue
        nt = newest(info)
        tag = "shared hub" if n == S.hub else "last write %s" % (time.strftime("%m-%d", time.localtime(nt)) if nt else "-")
        parts.append("%s=`%s` (%s, %s)" % (lab(n), tilde(info["dir"]), plural(len(info["files"]), "file"), tag))
    lines.append("- **Cross-dir memory (this dir = %s)**: Claude Code keeps one auto-memory dir per project and each "
                 "session loads only the first %d lines / %d characters of its own MEMORY.md. %d dirs: %s"
                 % (lab(name), S.max_lines, S.max_chars, len(order), " · ".join(parts)))
    search = []
    if os.path.isfile(S.recall):
        search.append("`%s` searches every memory dir and checkpoint" % recall_command(S))
    search.append("full cross-dir index `%s`" % tilde(S.cross_index))
    if S.hub and S.hub in dirs:
        tail = "Write new shared decisions into %s, add a line to its MEMORY.md, then run `%s`." % (lab(S.hub), sync_command(S))
    else:
        tail = "After writing memories, run `%s`." % sync_command(S)
    lines.append("- **Before answering about past decisions, check every dir**: %s. %s" % ("; ".join(search), tail))
    if S.hub and name != S.hub and S.hub in dirs and dirs[S.hub]["ok"]:
        lines.append("- **%s is the shared hub**: read `%s` before starting." % (lab(S.hub), tilde(dirs[S.hub]["index_path"])))
    dec = decision_files(S, dirs, order, exclude=name)
    dec.sort(key=lambda x: (0 if x[0] == S.hub else 1, -x[2]))
    cap = HUB_BLOCK_CAP if name == S.hub else OTHER_BLOCK_CAP
    for n, bn, _ in dec[:cap]:
        info = dirs[n]
        full = file_hook(S, info, bn)
        hk = short(full, 85)
        lost = [t for t, rx, _, _ in S.terms if rx.search(full) and not rx.search(hk)]
        if lost:
            hk += " (mentions %s)" % "/".join(lost)
        lines.append("- [%s:%s](%s) — %s" % (lab(n), bn[:-3], info["files"][bn]["path"], hk))
    if len(dec) > cap:
        lines.append("- %d more decision memories in other dirs: see the cross-dir index." % (len(dec) - cap))
    tm = term_map(S, dirs, order)
    chunk, chunks = [], []
    for tname, _, _, _ in S.terms:
        if tname not in tm:
            continue
        hits = tm[tname]
        more = "+%d" % (len(hits) - 1) if len(hits) > 1 else ""
        chunk.append("%s→%s:%s%s" % (tname, lab(hits[0][1]), hits[0][2][:-3], more))
        if len(chunk) == TERMS_PER_LINE:
            chunks.append(chunk)
            chunk = []
    if chunk:
        chunks.append(chunk)
    for i, c in enumerate(chunks):
        lines.append("- **Watch terms → memory%s**: %s" % ("" if i == 0 else " (cont.)", "｜".join(c)))
    lines.append(END)
    return "\n".join(lines)


def build_cross_index(S, dirs, order, now):
    out = ["# Cross-dir memory index (generated)", "",
           "> Generated by `%s` at %s. Do not edit. Claude Code keeps one auto-memory dir per project and each "
           "session loads only its own MEMORY.md; this file lists every memory in every dir so any session can "
           "find it in one hop.%s Emails, phone numbers and key-shaped strings in descriptions are masked."
           % (sync_command(S), now.strftime("%Y-%m-%d %H:%M"),
              (" Keyword search: `%s`." % recall_command(S)) if os.path.isfile(S.recall) else ""), ""]
    cats = [("Owner decisions", S.decision_cat_re), ("Watch terms / providers", S.watch_cat_re),
            ("Money / pricing", S.money_re)]
    for name in order:
        info = dirs[name]
        out.append("## %s — `%s`" % (info["label"], tilde(info["dir"])))
        out.append("")
        if not info["ok"]:
            out.extend(["(dir missing or unreadable)", ""])
            continue
        nt = newest(info)
        out.append("%s%s; last write %s." % (plural(len(info["files"]), "file"), " (shared hub)" if name == S.hub else "",
                                                   time.strftime("%Y-%m-%d %H:%M", time.localtime(nt)) if nt else "-"))
        out.append("")
        groups = dict((c, []) for c, _ in cats)
        groups["Other"] = []
        for bn, r in sorted(info["files"].items(), key=lambda kv: -kv[1]["mtime"]):
            probe = bn + " " + r["desc"] + " " + info["hooks"].get(bn, "")
            g = "Other"
            for c, rx in cats:
                if rx.search(probe):
                    g = c
                    break
            groups[g].append("- [%s](%s) — %s · %s" % (bn[:-3], r["path"], file_hook(S, info, bn),
                                                      time.strftime("%m-%d", time.localtime(r["mtime"]))))
        for c in [c for c, _ in cats] + ["Other"]:
            if groups[c]:
                out.append("### %s (%d)" % (c, len(groups[c])))
                out.extend(groups[c])
                out.append("")
    return "\n".join(out) + "\n"


def do_sync(S, dirs, order, now, unsync=False):
    results = []
    for name in order:
        info = dirs[name]
        lab = info["label"]
        path = info["index_path"]
        if not info["ok"] or not os.path.isfile(path):
            results.append((lab, "skipped: dir or MEMORY.md missing"))
            continue
        for _attempt in range(3):
            mt = os.path.getmtime(path)
            try:
                cur = read_text(path, strict=True)
            except UnicodeDecodeError:
                results.append((lab, "not written: MEMORY.md is not valid UTF-8"))
                break
            try:
                if unsync:
                    if find_block(cur) is None:
                        results.append((lab, "no block"))
                        break
                    new = remove_block(cur)
                else:
                    new = insert_block(cur, build_block(S, dirs, order, name, now))
            except ValueError:
                results.append((lab, "not written: block start marker without end marker; fix MEMORY.md by hand"))
                break
            if not unsync:
                _, ol, oc = loaded_part(S, new)
                if ol or oc:
                    results.append((lab, "not written: the block would push the index past the limit (%d lines / %d "
                                         "chars); shorten this dir's index first"
                                    % (len(new.strip().split("\n")), u16len(new.strip()))))
                    break
            if new == cur:
                results.append((lab, "unchanged"))
                break
            if atomic_write(path, new, expect_mtime=mt):
                results.append((lab, "block removed" if unsync else "block written (%d lines / %d chars)"
                                % (len(new.strip().split("\n")), u16len(new.strip()))))
                break
            time.sleep(0.5)
        else:
            results.append((lab, "not written: another session kept changing the file (3 attempts); rerun later"))
    if not unsync:
        xi = S.cross_index
        parent = os.path.dirname(xi)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        expect = os.path.getmtime(xi) if os.path.exists(xi) else None
        ok = atomic_write(xi, build_cross_index(S, dirs, order, now), expect_mtime=expect)
        results.append(("XINDEX", ("wrote %s" if ok else "not written: %s changed during the write") % tilde(xi)))
    return results


# ---------------------------------------------------------------- checkpoint backlog
def strong_tokens(line):
    """Distinctive tokens (dates, ids, numbers, english words) used for a weak 'probably has a memory' match."""
    t = set()
    t.update(re.findall(r"(?<![\d/])\d{1,2}/\d{1,2}(?![\d/])", line))
    t.update(x.lower() for x in re.findall(r"\b[A-Z]{1,4}-\d{1,4}\b|#\d{2,4}\b|\b[A-Z]\d{1,3}\b", line))
    t.update(re.findall(r"[$¥€]\s?\d[\d.,]*|\d+(?:\.\d+)?%", line))
    t.update(w.lower() for w in re.findall(r"[A-Za-z][A-Za-z0-9]{4,}", line) if w.lower() not in STOPW)
    t.update(re.findall(r"[\u4e00-\u9fff]{4,}", line))
    return set(re.sub(r"\s+", "", x) for x in t)


def scan_backlog(S, dirs, order, today, days):
    start = today - datetime.timedelta(days=days - 1)
    rx = S.owner_rx
    mem_all = {}
    for name in order:
        if dirs[name]["ok"]:
            for bn, r in dirs[name]["files"].items():
                mem_all[(name, bn)] = re.sub(r"\s+", "", r["text"])
    mem_low = dict((k, v.lower()) for k, v in mem_all.items())
    hub_ok = bool(S.hub and S.hub in dirs and usable(dirs[S.hub]))
    hub_loaded = loaded_part(S, dirs[S.hub]["index"])[0] if hub_ok else ""
    items = []
    for path in S.checkpoint_files():
        cur = None
        try:
            fh = open(path, encoding="utf-8", errors="replace")
        except (IOError, OSError):
            continue
        with fh:
            for i, line in enumerate(fh):
                m = SEC_RE.match(line)
                if m:
                    try:
                        if m.group(1):
                            cur = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                        else:
                            cur = datetime.date(today.year, int(m.group(4)), int(m.group(5)))
                    except ValueError:
                        pass
                    continue
                if cur is None or cur < start or cur > today or S.skip_re.search(line[:24]):
                    continue
                terms = [n for n, trx, _, _ in S.terms if trx.search(line)]
                compare_terms = [n for n, trx, _, cmp_ok in S.terms if cmp_ok and trx.search(line)]
                if rx["decided"].search(line) and not rx["pending"].search(line):
                    pri = "P1-owner-decision"
                elif compare_terms and CMP_RE.search(line):
                    pri = "P1-term-comparison"
                elif rx["quote"].search(line) and rx["quote_verb"].search(line):
                    pri = "P2-owner-quote"
                else:
                    continue
                probes = [re.sub(r"\s+", "", q)[:12] for qrx in QUOTE_RES for q in qrx.findall(line)][:3]
                anchors = []
                tmatch = TIME_RE.match(line)
                if tmatch:
                    h, m1 = tmatch.group(1), tmatch.group(2)
                    anchors = ["%d/%d%s:%s" % (cur.month, cur.day, h, m1), "%d/%02d%s:%s" % (cur.month, cur.day, h, m1),
                               "%s%s:%s" % (cur.isoformat(), h, m1)]
                hits = [k for k, t in mem_all.items() if any(p in t for p in probes) or any(a in t for a in anchors)]
                weak = []
                if not hits:
                    toks = strong_tokens(line)
                    if len(toks) >= 3:
                        for k, tl in mem_low.items():
                            n = sum(1 for x in toks if x in tl)
                            if n >= 3 and n >= 0.4 * len(toks):
                                weak.append(k)
                hub_vis = any(k[0] == S.hub or k[1][:-3] in hub_loaded for k in hits + weak) if hub_ok else None
                items.append({"pri": pri, "file": path, "line": i + 1, "date": cur.isoformat(), "covered": bool(hits),
                              "weak": bool(weak), "weak_files": ["%s:%s" % (dirs[k[0]]["label"], k[1]) for k in weak[:2]],
                              "terms": terms, "hub_visible": hub_vis, "text": S.mask(short(line, 110))})
    return items


# ---------------------------------------------------------------- other checks
def last_write_under(root):
    best = 0.0
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if not d.startswith(".")]
        for f in fn:
            if f.startswith("."):
                continue
            try:
                best = max(best, os.path.getmtime(os.path.join(dp, f)))
            except OSError:
                pass
    return best or None


def project_checkouts(root):
    """The configured checkout plus the same sub-path in every `git worktree list` checkout of its repo."""
    outs = [root]
    env = dict((k, v) for k, v in os.environ.items()
               if k not in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE"))
    try:
        top = subprocess.run(["git", "-C", root, "rev-parse", "--show-toplevel"], stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL, universal_newlines=True, timeout=20, env=env)
        if top.returncode != 0 or not top.stdout.strip():
            return outs
        top = top.stdout.strip()
        rel = os.path.relpath(os.path.realpath(root), os.path.realpath(top))
        if rel.startswith(".."):
            return outs
        r = subprocess.run(["git", "-C", top, "worktree", "list", "--porcelain"], stdout=subprocess.PIPE,
                           stderr=subprocess.DEVNULL, universal_newlines=True, timeout=20, env=env)
        for line in r.stdout.splitlines():
            if line.startswith("worktree "):
                p = line[len("worktree "):].strip()
                p = os.path.normpath(os.path.join(p, rel)) if rel != "." else p
                if p not in outs and os.path.realpath(p) != os.path.realpath(root):
                    outs.append(p)
    except (OSError, ValueError, subprocess.SubprocessError):
        pass
    return outs


def key_scan(S, paths):
    """-> list of 'file:line pattern-name' (values are never returned)."""
    out = []
    seen = set()
    for root in paths:
        if not root or not os.path.exists(root):
            continue
        if os.path.isfile(root):
            files = [root]
        else:
            files = []
            for dp, _dn, fn in os.walk(root):
                files.extend(os.path.join(dp, f) for f in sorted(fn))
        for f in files:
            real = os.path.realpath(f)
            if real in seen:
                continue
            seen.add(real)
            if os.path.basename(f).startswith(".env") or not re.search(r"\.(md|txt|json|tsv|pre)$", f):
                continue
            try:
                with open(f, encoding="utf-8", errors="replace") as fh:
                    for i, line in enumerate(fh):
                        for n, rx in S.key_patterns:
                            if rx.search(line):
                                out.append("%s:%d %s" % (tilde(f), i + 1, n))
            except (IOError, OSError):
                pass
    return out


# ---------------------------------------------------------------- audit
def audit(S, dirs, order, now, days, show_all):
    res = []
    today = now.date()
    add = lambda n, st, name, summary, det=(): res.append(  # noqa: E731
        {"id": n, "status": st, "check": name, "summary": summary, "details": list(det)})
    usable_dirs = [n for n in order if usable(dirs[n])]
    hub_info = dirs.get(S.hub) if S.hub else None

    # 1 dirs
    fails, warns = [], []
    if not os.path.isdir(S.projects_root):
        fails.append("projects root not found: %s" % tilde(S.projects_root))
    for n in order:
        info = dirs[n]
        if not info["ok"]:
            msg = "%s: memory dir missing or unreadable: %s%s" % (info["label"], tilde(info["dir"]),
                                                                  " (%s)" % info["error"] if info["error"] else "")
            (fails if n == S.hub else warns).append(msg + (" (memory.hub)" if n == S.hub else " (memory.labels)"))
        elif info["index"] is None:
            fails.append("%s: memory dir has no MEMORY.md, so no session loads it: %s" % (info["label"], tilde(info["dir"])))
    labels_seen = {}
    for n in order:
        labels_seen.setdefault(dirs[n]["label"], []).append(n)
    for lb, names in sorted(labels_seen.items()):
        if len(names) > 1:
            fails.append("label %s is used by %d dirs (%s); give each dir its own label" % (lb, len(names), ", ".join(names)))
    blocks = [(split_block(dirs[n]["index"])[:2], n) for n in usable_dirs]
    ref = None
    if hub_info and usable(hub_info) and split_block(hub_info["index"])[0]:
        ref = (split_block(hub_info["index"])[0], hub_info["label"])
    else:
        dated = sorted(((bt or datetime.datetime.min), blk, dirs[n]["label"]) for (blk, bt), n in blocks if blk)
        if dated:
            ref = (dated[-1][1], dated[-1][2])
    if ref:
        for n in order:
            if dirs[n]["ok"] and ("/%s/memory`" % n) not in ref[0]:
                fails.append("%s appeared after the last --sync (not listed in %s's block): its sessions cannot see "
                             "the other dirs and theirs cannot see it; run --sync" % (dirs[n]["label"], ref[1]))
    st = FAIL if fails else (WARN if warns else (WARN if not order else PASS))
    add(1, st, "memory dirs", "%d memory dirs under %s%s" % (len(order), tilde(S.projects_root),
                                                              "" if order else " (nothing to audit)"), fails + warns)

    # 2 index integrity + limits
    det, warn = [], []
    for n in usable_dirs:
        info = dirs[n]
        idx = info["index"]
        local = set()
        here = os.path.abspath(info["dir"])

        def resolve(target):
            target = os.path.expanduser(target)
            return target if os.path.isabs(target) else os.path.join(info["dir"], target)
        for m in LINK_RE.finditer(idx):
            p = resolve(m.group(2))
            if not os.path.exists(p):
                det.append("%s: index links a missing file: %s" % (info["label"], m.group(2)))
            if os.path.dirname(os.path.abspath(p)) == here:
                local.add(os.path.basename(p))
        # files linked from index-*.md sub-indexes (themselves linked from MEMORY.md) count as indexed; one hop
        for sub in sorted(b for b in local if b.startswith("index-") and b.endswith(".md")):
            try:
                sub_text = read_text(os.path.join(info["dir"], sub))
            except (IOError, OSError):
                continue
            for m in LINK_RE.finditer(sub_text):
                p = resolve(m.group(2))
                if not os.path.exists(p):
                    det.append("%s: sub-index %s links a missing file: %s" % (info["label"], sub, m.group(2)))
                elif os.path.dirname(os.path.abspath(p)) == here:
                    local.add(os.path.basename(p))
        for o in sorted(set(info["files"]) - local):
            det.append("%s: topic file not in the index: %s" % (info["label"], o))
        t = idx.strip()
        nl, nc = len(t.split("\n")), u16len(t)
        if nl > S.max_lines or nc > S.max_chars:
            det.append("%s: index is %d lines / %d chars, over the %d-line / %d-char loaded part; sessions do not see "
                       "the rest" % (info["label"], nl, nc, S.max_lines, S.max_chars))
        elif nl > S.near_lines or nc > S.near_chars:
            warn.append("%s: index is %d lines / %d chars, close to the %d / %d limit"
                        % (info["label"], nl, nc, S.max_lines, S.max_chars))
    add(2, FAIL if det else (WARN if warn else PASS), "index links + size limits",
        "%d problems, %d close to the limit" % (len(det), len(warn)), det + warn)

    # 3 block present + fresh + fits
    if len(order) < 2:
        add(3, SKIP, "cross-dir block", "only %s; nothing to cross-link" % plural(len(order), "memory dir"))
    else:
        det, warn = [], []
        for n in usable_dirs:
            info = dirs[n]
            block, bt, unterminated = split_block(info["index"])
            if unterminated:
                det.append("%s: MEMORY.md has a block start marker without the end marker; fix it by hand" % info["label"])
                continue
            if block is None:
                det.append("%s: MEMORY.md has no cross-dir block (its sessions cannot see the other dirs); run --sync"
                           % info["label"])
                continue
            if END not in loaded_part(S, info["index"])[0]:
                det.append("%s: the cross-dir block is outside the loaded part of MEMORY.md" % info["label"])
            if bt is None or (now - bt).total_seconds() > S.block_max_age_h * 3600:
                det.append("%s: the cross-dir block is older than %s h (written %s); run --sync"
                           % (info["label"], S.block_max_age_h, bt))
            else:
                newer = [dirs[m]["label"] for m in order if dirs[m]["ok"] and newest(dirs[m])
                         and newest(dirs[m]) > time.mktime(bt.timetuple()) + 60]
                if newer:
                    warn.append("%s: %s got new memories after the block was written; run --sync"
                                % (info["label"], "/".join(newer)))
        add(3, FAIL if det else (WARN if warn else PASS), "cross-dir block",
            "%d missing or stale" % len(det), det + sorted(set(warn)))

    # 4 cross index
    if not S.configured:
        add(4, UNCONF, "cross-dir index", "no config file; the cross-dir index location is unknown")
    elif len(order) < 2:
        add(4, SKIP, "cross-dir index", "only %s; nothing to cross-link" % plural(len(order), "memory dir"))
    else:
        det = []
        if not os.path.exists(S.cross_index):
            det.append("missing %s; run --sync" % tilde(S.cross_index))
        elif now.timestamp() - os.path.getmtime(S.cross_index) > S.block_max_age_h * 3600:
            det.append("%s is older than %s h; run --sync" % (tilde(S.cross_index), S.block_max_age_h))
        add(4, FAIL if det else PASS, "cross-dir index", "missing or stale" if det else "present and fresh", det)

    # 5 hub sees other dirs' decision / watch-term files
    name5 = "hub sees other dirs' decisions"
    if not S.configured:
        add(5, UNCONF, name5, "no config file; memory.hub unknown")
    elif not S.hub:
        add(5, SKIP, name5, "memory.hub is null; no dir is the shared hub")
    elif not hub_info or not usable(hub_info):
        add(5, FAIL, name5, "hub %s has no readable MEMORY.md" % S.hub, ["memory.hub = %s" % S.hub])
    else:
        det = []
        hub_loaded = loaded_part(S, hub_info["index"])[0]
        for n, bn, _ in sorted(decision_files(S, dirs, order, exclude=S.hub)):
            if bn[:-3] not in hub_loaded:
                det.append("%s's loaded index does not name %s:%s — %s"
                           % (hub_info["label"], dirs[n]["label"], bn, file_hook(S, dirs[n], bn)[:70]))
        add(5, FAIL if det else PASS, name5, "%d not visible" % len(det), det)

    # 6 watch terms visible in every dir's loaded index
    name6 = "watch terms visible in every index"
    if not S.configured:
        add(6, UNCONF, name6, "no config file; memory.watch_terms unknown")
    elif not S.terms:
        add(6, SKIP, name6, "memory.watch_terms is empty")
    else:
        det = []
        tm = term_map(S, dirs, order)
        for n in usable_dirs:
            loaded = loaded_part(S, dirs[n]["index"])[0]
            miss = ["%s(%s)" % (t, ",".join("%s:%s" % (dirs[m]["label"], bn[:-3]) for _, m, bn in tm[t][:2]))
                    for t, rx, _, _ in S.terms if t in tm and not rx.search(loaded)]
            if miss:
                det.append("%s: loaded index lacks %d watch terms: %s" % (dirs[n]["label"], len(miss), "; ".join(miss)))
        add(6, FAIL if det else PASS, name6, "%d dirs missing terms" % len(det), det)

    # 7 checkpoint backlog
    name7 = "checkpoint decisions have a memory"
    items = []
    if not S.configured:
        add(7, UNCONF, name7, "no config file; owner and checkpoints unknown")
    elif not S.owner:
        add(7, SKIP, name7, "owner.name is not set")
    elif not S.checkpoints_configured:
        add(7, SKIP, name7, "checkpoints.files / checkpoints.globs are not set")
    elif not S.checkpoint_files():
        add(7, WARN, name7, "checkpoints.files / checkpoints.globs matched no file")
    else:
        items = scan_backlog(S, dirs, order, today, days)
        p1 = [x for x in items if x["pri"].startswith("P1")]
        p1_weak = [x for x in p1 if not x["covered"] and x["weak"]]
        p1_unc = [x for x in p1 if not x["covered"] and not x["weak"]]
        p1_hidden = [x for x in p1 if x["covered"] and x["hub_visible"] is False]
        p1_old = [x for x in p1_unc if x["date"] < today.isoformat()]
        p2_unc = [x for x in items if x["pri"].startswith("P2") and not x["covered"] and not x["weak"]]
        det = []
        lim = None if show_all else 25
        for x in sorted(p1_unc, key=lambda y: (y["date"], y["line"]), reverse=True)[:lim]:
            det.append("not in memory %s %s %s:%d  %s" % (x["pri"], x["date"], os.path.basename(x["file"]), x["line"], x["text"]))
        for x in p1_hidden[:lim]:
            det.append("has a memory the hub cannot see %s %s:%d  %s"
                       % (x["date"], os.path.basename(x["file"]), x["line"], x["text"][:70]))
        summary = ("last %d days: %d decision lines in %d files (P1 %d: not in memory %d, of which before today %d; "
                   "weak match only %d; hidden from hub %s); P2 owner quotes not in memory %d"
                   % (days, len(items), len(S.checkpoint_files()), len(p1), len(p1_unc), len(p1_old), len(p1_weak),
                      len(p1_hidden) if S.hub else "n/a (memory.hub is null)", len(p2_unc)))
        add(7, FAIL if (p1_old or p1_hidden) else (WARN if (p1_unc or p2_unc) else PASS), name7, summary, det)

    # 8 vault
    name8 = "vault written recently"
    if not S.configured:
        add(8, UNCONF, name8, "no config file; vault.root unknown")
    elif not S.vault:
        add(8, SKIP, name8, "vault.root is not set (nor OBSIDIAN_VAULT in .muse/paths.md)")
    elif not os.path.isdir(S.vault):
        add(8, WARN, name8, "vault %s not found" % tilde(S.vault))
    else:
        lw = last_write_under(S.vault)
        active = [f for f in (S.checkpoint_files() if S.checkpoints_configured else [])
                  if now.timestamp() - os.path.getmtime(f) < S.vault_active_h * 3600]
        if lw is None:
            add(8, WARN, name8, "vault %s holds no files" % tilde(S.vault))
        else:
            age_h = (now.timestamp() - lw) / 3600
            failing = age_h > S.vault_fresh_h and bool(active)
            add(8, FAIL if failing else PASS, name8,
                "last write %s (%.0f h ago); checkpoint files changed in the last %s h: %d"
                % (time.strftime("%Y-%m-%d %H:%M", time.localtime(lw)), age_h, S.vault_active_h, len(active)),
                ["vault older than %s h while checkpoints are active: %s" % (S.vault_fresh_h, ", ".join(
                    os.path.basename(f) for f in active[:5]))] if failing else [])

    # 9 daily memory file
    name9 = "daily memory file memory/<today>.md"
    if not S.configured:
        add(9, UNCONF, name9, "no config file; memory.daily_projects unknown")
    elif not S.daily:
        add(9, SKIP, name9, "memory.daily_projects is empty")
    else:
        det, okp = [], []
        names = [today.isoformat() + ".md"]
        if now.hour < 2:
            names.append((today - datetime.timedelta(days=1)).isoformat() + ".md")
        for proj, root in S.daily:
            cos = [c for c in project_checkouts(root) if os.path.isdir(c)]
            found = [c for c in cos for n in names if os.path.exists(os.path.join(c, "memory", n))]
            if found:
                okp.append("%s: %s" % (proj, tilde(found[0])))
                continue
            latest = []
            for c in cos:
                md = os.path.join(c, "memory")
                ds = sorted(f for f in os.listdir(md) if re.match(r"^\d{4}-\d\d-\d\d\.md$", f)) if os.path.isdir(md) else []
                if ds:
                    latest.append(ds[-1][:-3])
            det.append("%s: no memory/%s in %d checkouts (newest daily file: %s)"
                       % (proj, names[0], len(cos), max(latest) if latest else "none"))
        add(9, FAIL if det else PASS, name9, "found: %s" % ("; ".join(okp) or "none"), det)

    # 10 recall
    add(10, PASS if os.path.isfile(S.recall) else WARN, "recall tool",
        tilde(S.recall) if os.path.isfile(S.recall) else "missing %s (memory.recall)" % tilde(S.recall))

    # 11 key-pattern scan (values never printed)
    roots = sorted(set(glob.glob(os.path.join(S.projects_root, "*", "memory")) + [dirs[n]["dir"] for n in order]))
    hits = key_scan(S, roots + ([S.cross_index] if S.cross_index else []) + S.scan_extra)
    samples = _key_selftest_samples()
    bad = [n for n, rx in S.key_patterns if n in samples and not rx.search(samples[n])]
    bad += ["false positive:" + w for w in KEY_SELFTEST_NEGATIVES if any(rx.search(w) for _, rx in S.key_patterns)]
    if bad:
        hits.append("scanner self-test failed: %s" % ",".join(bad))
    add(11, FAIL if hits else PASS, "key-pattern scan (memory dirs + cross-dir index + extra paths)",
        "%d hits (file:line and pattern name only)" % len(hits), hits)
    return res, items


def main(argv):
    ap = argparse.ArgumentParser(description="Audit / cross-link Claude Code auto-memory directories")
    ap.add_argument("--config", help="path to orchestration.json (default: lookup in orchestration_config.py)")
    ap.add_argument("--projects-root", "--root", dest="projects_root",
                    help="dir holding <project>/memory dirs (default: memory.projects_root or ~/.claude/projects)")
    ap.add_argument("--sync", action="store_true", help="write the cross-dir block + cross-dir index")
    ap.add_argument("--unsync", action="store_true", help="remove the cross-dir block from every MEMORY.md")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--all", action="store_true", help="list every detail")
    ap.add_argument("--days", type=int, default=7, help="checkpoint window in days (default 7)")
    ap.add_argument("--today", help="YYYY-MM-DD (tests)")
    ap.add_argument("--now", help='"YYYY-MM-DD HH:MM" (tests)')
    a = ap.parse_args(argv)
    try:  # a non-UTF-8 terminal must not crash on the non-ASCII separators in the report
        if (sys.stdout.encoding or "").lower().replace("-", "") != "utf8":
            sys.stdout.reconfigure(errors="backslashreplace")
    except (AttributeError, ValueError):
        pass
    if a.sync and a.unsync:
        ap.error("--sync and --unsync are mutually exclusive")
    if a.days < 1:
        ap.error("--days must be at least 1")
    try:
        if a.now:
            now = datetime.datetime.strptime(a.now, "%Y-%m-%d %H:%M")
        elif a.today:
            now = datetime.datetime.strptime(a.today + " 12:00", "%Y-%m-%d %H:%M")
        else:
            now = datetime.datetime.now()
    except ValueError:
        ap.error("--now must be 'YYYY-MM-DD HH:MM' and --today 'YYYY-MM-DD'")
    try:
        S = Settings(OC.load(a.config), a)
        if a.sync and not S.configured:
            print("memory_audit: UNCONFIGURED: --sync needs .muse/orchestration.json (or --config / %s); "
                  "nothing was written" % OC.ENV_NAME)
            return 2
        dirs, order = discover(S)
        if a.sync or a.unsync:
            for label, msg in do_sync(S, dirs, order, now, unsync=a.unsync):
                print("%-8s %s" % (label, msg))
            dirs, order = discover(S)
        res, _items = audit(S, dirs, order, now, a.days, a.all)
    except ConfigError as error:
        print("memory_audit: config error: %s" % error)
        print("RESULT: RED (config error)")
        return 2
    counts = dict((s, sum(1 for r in res if r["status"] == s)) for s in (FAIL, WARN, SKIP, UNCONF))
    result = "RED" if counts[FAIL] else "GREEN"
    tail = "fail=%d warn=%d skip=%d unconfigured=%d" % (counts[FAIL], counts[WARN], counts[SKIP], counts[UNCONF])
    if a.json:
        print(json.dumps({"checks": res, "result": result, "counts": counts, "config": S.config_path,
                          "projects_root": S.projects_root}, ensure_ascii=False, indent=1))
    else:
        print("memory_audit %s · projects root %s · config %s"
              % (now.strftime("%Y-%m-%d %H:%M"), tilde(S.projects_root), tilde(S.config_path) or "none (UNCONFIGURED)"))
        for r in res:
            print("[%s] %d %s — %s" % (r["status"], r["id"], r["check"], r["summary"]))
            for x in r["details"][: (None if a.all else 30)]:
                print("    · " + x)
            if not a.all and len(r["details"]) > 30:
                print("    · ... %d more (use --all)" % (len(r["details"]) - 30))
        print("RESULT: %s (%s)" % (result, tail))
    return 1 if counts[FAIL] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
