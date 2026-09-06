#!/usr/bin/env python3
"""Portable command routing for the shared MUSE workflow and state helpers."""
from __future__ import annotations
import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

HERE = Path(__file__).resolve().parent
COMMANDS = ('resume', 'save', 'bye', 'sync', 'ctx', 'distill', 'settings', 'model',
            'role', 'start', 'sprint', 'retro', 'launch', 'release', 'migrate-to-myths-labs')
STATE = ('new-handoff-id', 'write-checkpoint', 'read-checkpoint', 'verify-handoff')
DAILY = ('enable-daily', 'disable-daily', 'resume-workflow', 'bye-workflow', 'prepare-resume',
         'save-daily', 'claim-lane', 'adopt-lane', 'initialize-lane', 'source-update', 'source-status')


def workspace(args):
    for flag in ('--workspace', '--cwd'):
        if flag in args:
            return args[args.index(flag) + 1]
    if args[0] in ('parse', 'parse-resume', 'checkpoint-path', 'resolve') and len(args) > 2:
        return args[2]
    if args[0] in ('doctor', 'smoke') and len(args) > 1:
        return args[1]
    if '--input' in args:
        path = Path(args[args.index('--input') + 1])
        if path.is_symlink() or path.stat().st_size > 256 * 1024:
            raise ValueError('INVALID_INPUT_FILE')
        data = json.loads(path.read_text())
        if isinstance(data, dict) and isinstance(data.get('workspace'), str):
            return data['workspace']
    return os.getcwd()


def main(args):
    if not args:
        raise ValueError('Usage: muse-doctor.sh doctor|parse-resume|prepare-resume|save-daily|...')
    cwd = Path(workspace(args)).resolve()
    if not os.environ.get('MUSE_CONFIG') and not os.environ.get('DYA_ROOT'):
        for root in (cwd, *cwd.parents):
            p = root / '.muse/config.json'
            if p.exists() or p.is_symlink():
                os.environ['MUSE_CONFIG'] = str(p)
                break
    spec = importlib.util.spec_from_file_location('cli_config', HERE/'muse-config.py')
    config = importlib.util.module_from_spec(spec); spec.loader.exec_module(config)
    center, roots = config.load()
    workflows = roots[center] / '.agent/workflows'

    def resolve(command):
        name = command.lstrip('/')
        if name not in COMMANDS:
            raise ValueError('UNSUPPORTED_COMMAND: ' + name)
        p = workflows / (name + '.md')
        if not p.is_file():
            raise ValueError('WORKFLOW_MISSING: ' + name)
        return str(p)

    name = args[0]
    if name in ('resolve', 'parse'):
        tokens = shlex.split(args[1])
        if not tokens: raise ValueError('EMPTY_COMMAND')
        route = resolve(tokens[0])
        if name == 'resolve': print(route)
        else: print('COMMAND\t'+tokens[0].lstrip('/')+'\nARGUMENTS\t'+' '.join(shlex.quote(t) for t in tokens[1:])+'\nWORKFLOW\t'+route)
        return 0
    if name == 'list':
        for command in COMMANDS: print('/'+command+'\t'+resolve(command))
        return 0
    if name in ('doctor', 'smoke'):
        missing = [str(workflows/(c+'.md')) for c in COMMANDS if not (workflows/(c+'.md')).is_file()]
        missing += [str(HERE/f) for f in ['muse-session-state.py', 'muse-daily.py', 'muse-onboarding.py', 'muse-runtime.py', 'muse-sources.py', 'muse-source-hook.py', 'muse-closeout.py'] if not (HERE/f).is_file()]
        print(json.dumps({'status': 'FAIL' if missing else 'PASS', 'role_home': center,
                          'missing': missing, 'scope': 'Installation files and configuration only; not user-flow QA'}))
        return 1 if missing else 0
    if name in ('parse-resume', 'checkpoint-path'):
        rest = [name, args[1], '--cwd', str(cwd)]; script = 'muse-session-state.py'
    elif name in STATE: rest = args; script = 'muse-session-state.py'
    elif name in DAILY: rest = args; script = 'muse-daily.py'
    elif name in ('save-delta', 'recover'): rest = args; script = 'muse-incremental.py'
    elif name in ('verify-closeout', 'check-closeout'): rest = args; script = 'muse-closeout.py'
    elif name == 'runtime-identity': rest = ['identity']; script = 'muse-runtime.py'
    else: raise ValueError('UNSUPPORTED_COMMAND: ' + name)
    return subprocess.call([sys.executable, str(HERE/script), *rest])


if __name__ == '__main__':
    try: raise SystemExit(main(sys.argv[1:]))
    except (ValueError, OSError, IndexError, KeyError, TypeError) as exc:
        print('MUSE_ERROR: '+str(exc), file=sys.stderr)
        raise SystemExit(2)
