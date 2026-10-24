#!/usr/bin/env python3
"""Recover what an orchestrating session was doing when the account hit its usage wall.

Read-only. For one parent session transcript it lists every sub-agent whose transcript was
written after --since, whether the parent ever got that sub-agent's completion notice, and the
sub-agent's last words, so a new session can re-dispatch only unfinished work.

Usage:
  python3 -I wall_recover.py <parent-session-id> [--since 2026-01-31T09:20] [--chars 300]
                             [--projects-root DIR] [--config PATH]

Transcript layout read (Claude Code; projects root from --projects-root, else
memory.projects_root, else ~/.claude/projects):
  <root>/<project>/<session-id>.jsonl                               parent session
  <root>/<project>/<session-id>/subagents/agent-<id>.jsonl          one per sub-agent
  <root>/<project>/<session-id>/subagents/agent-<id>.meta.json      description, model
  completion notice in the parent: <task-id><id></task-id> ... <status>...</status> ... </task-notification>
--since and the printed times use this machine's local time zone; transcripts store UTC.

Prints no tool results and no tool inputs (they can hold secrets); only sub-agent descriptions,
model names, tool-call counts and assistant text.
Exit 0 after listing, 2 on bad input (unknown session, bad --since, missing projects root).
"""
import argparse
import glob
import importlib.util
import json
import os
import re
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PROJECTS_ROOT = os.path.join('~', '.claude', 'projects')
SESSION_ID = re.compile(r'^[A-Za-z0-9_-]+$')
# The wall itself writes "You've hit your ... limit"; the words before it are the real last words.
WALL_TEXT = re.compile(r'hit your .{0,20}limit')


def load_config_module():
    spec = importlib.util.spec_from_file_location('orchestration_config', os.path.join(HERE, 'orchestration_config.py'))
    oc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oc)
    return oc


def records(path):
    """Yield each JSON object line of a transcript; unreadable lines are skipped."""
    with open(path, 'rb') as f:
        for line in f:
            try:
                o = json.loads(line)
            except ValueError:
                continue
            if isinstance(o, dict):
                yield o


def message_text(o):
    msg = o.get('message')
    c = msg.get('content') if isinstance(msg, dict) else None
    if isinstance(c, str):
        return c
    return ' '.join(x.get('text', '') for x in (c or []) if isinstance(x, dict) and isinstance(x.get('text'), str))


def notices(parent_path):
    """task-id -> (status, utc ts) from the parent's <task-notification> turns."""
    out = {}
    with open(parent_path, 'rb') as f:
        for line in f:
            if b'task-notification' not in line:
                continue
            try:
                o = json.loads(line)
            except ValueError:
                continue
            if not isinstance(o, dict):
                continue
            text = message_text(o)
            for m in re.finditer(r'<task-id>(\w+)</task-id>(.*?)</task-notification>', text, re.S):
                st = re.search(r'<status>(\w+)</status>', m.group(2))
                out[m.group(1)] = (st.group(1) if st else 'notified', o.get('timestamp', ''))
    return out


def last_words(path, chars):
    last_ts, last_text, tools = '', '', 0
    for o in records(path):
        last_ts = o.get('timestamp') or last_ts
        if o.get('type') != 'assistant':
            continue
        msg = o.get('message')
        content = msg.get('content') if isinstance(msg, dict) else None
        for x in content if isinstance(content, list) else []:
            if not isinstance(x, dict):
                continue
            if x.get('type') == 'text' and isinstance(x.get('text'), str) and x['text'].strip():
                if not WALL_TEXT.search(x['text']):
                    last_text = x['text'].strip()
            elif x.get('type') == 'tool_use':
                tools += 1
    return last_ts, last_text.replace('\n', ' ')[:chars], tools


def to_local(ts):
    if not ts:
        return '?'
    try:
        return datetime.fromisoformat(ts.replace('Z', '+00:00')).astimezone().strftime('%H:%M')
    except (ValueError, TypeError):
        return '?'


def read_meta(path):
    try:
        with open(path, encoding='utf-8') as f:
            meta = json.load(f)
    except (OSError, ValueError):
        return {}
    return meta if isinstance(meta, dict) else {}


def main():
    ap = argparse.ArgumentParser(description='List the sub-agents a session left unfinished at a usage wall.')
    ap.add_argument('session')
    ap.add_argument('--since', default=None, help='local time, e.g. 2026-01-31T09:20')
    ap.add_argument('--chars', type=int, default=300)
    ap.add_argument('--projects-root', default=None, help='overrides memory.projects_root')
    ap.add_argument('--config', default=None)
    a = ap.parse_args()

    if not SESSION_ID.match(a.session):
        print('bad session id: %r' % a.session)
        return 2
    oc = load_config_module()
    try:
        config = oc.load(a.config)
        if a.projects_root:
            root = os.path.abspath(os.path.expanduser(a.projects_root))
        else:
            root = str(config.path_of(config.get('memory.projects_root') or DEFAULT_PROJECTS_ROOT))
    except oc.ConfigError as error:
        print('CONFIG_ERROR: %s' % error)
        return 2
    if not os.path.isdir(root):
        print('projects root not found: %s (set memory.projects_root or --projects-root)' % root)
        return 2
    since = None
    if a.since:
        try:
            # A naive time is local time; an explicit offset is respected.
            since = datetime.fromisoformat(a.since).timestamp()
        except ValueError:
            print('bad --since %r (use local time like 2026-01-31T09:20)' % a.since)
            return 2

    hits = sorted(glob.glob(os.path.join(glob.escape(root), '*', a.session + '.jsonl')))
    if not hits:
        print('no transcript for session %s under %s' % (a.session, root))
        return 2
    parent = hits[0]
    sub_dir = os.path.join(os.path.dirname(parent), a.session, 'subagents')
    done = notices(parent)

    rows = []
    for path in glob.glob(os.path.join(glob.escape(sub_dir), 'agent-*.jsonl')):
        if since and os.path.getmtime(path) < since:
            continue
        aid = os.path.basename(path)[len('agent-'):-len('.jsonl')]
        meta = read_meta(path[:-len('.jsonl')] + '.meta.json')
        ts, text, tools = last_words(path, a.chars)
        status = done.get(aid, ('UNFINISHED', ''))[0]
        rows.append((status != 'completed', ts, aid, meta, status, text, tools))

    rows.sort(key=lambda r: (not r[0], r[1]))
    unfinished = sum(1 for r in rows if r[0])
    print('parent:', parent)
    if len(hits) > 1:
        print('note: %d transcripts share this session id; using the first' % len(hits))
    print('sub-agents active since %s: %d, not completed: %d' % (a.since or 'start', len(rows), unfinished))
    for _, ts, aid, meta, status, text, tools in rows:
        print('- [%s] %s %s (%s, last %s, %d tool calls)' % (
            status, aid[:9], meta.get('description', '?'), meta.get('model', '?'), to_local(ts), tools))
        if status != 'completed' and text:
            print('    last words:', text)
    return 0


if __name__ == '__main__':
    sys.exit(main())
