#!/usr/bin/env python3
"""Read native session identity; capture only Claude's SessionStart identity."""
from __future__ import annotations
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import stat
import sys


def valid_id(value):
    return isinstance(value,str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}',value)


def identity():
    platform=os.environ.get('MUSE_RUNTIME_PLATFORM')
    session=os.environ.get('MUSE_RUNTIME_SESSION_ID')
    if platform or session or os.environ.get('MUSE_RUNTIME_WORKSPACE'):
        workspace=os.environ.get('MUSE_RUNTIME_WORKSPACE','')
        if platform!='claude' or not valid_id(session) or not Path(workspace).is_absolute():
            raise ValueError('RUNTIME_IDENTITY_INVALID')
        return dict(platform='claude',session_id=session,workspace=str(Path(workspace).resolve()),source='claude_sessionstart_environment')
    session=os.environ.get('CODEX_THREAD_ID')
    if not valid_id(session):
        raise ValueError('RUNTIME_IDENTITY_UNAVAILABLE')
    return dict(platform='codex',session_id=session,workspace=None,source='codex_native_environment')


def require_workspace(current, workspace):
    native = current.get('workspace')
    if not native or native == workspace: return
    spec = importlib.util.spec_from_file_location('runtime_config', Path(__file__).with_name('muse-config.py'))
    config = importlib.util.module_from_spec(spec); spec.loader.exec_module(config)
    roots = list(config.load()[1].values())
    def owner(path):
        matches = [root for root in roots if path == root or root in path.parents]
        return max(matches, key=lambda root:len(root.parts)) if matches else None
    start,target = Path(native).resolve(),Path(workspace).resolve()
    if owner(start) is None or owner(start) != owner(target) or start not in target.parents:
        raise ValueError('RUNTIME_WORKSPACE_MISMATCH')


def require_writer(checkpoint):
    current=identity()
    if any(current[key]!=checkpoint[key] for key in ('platform','session_id')):
        raise ValueError('WRITER_MISMATCH: explicit claim is required')
    require_workspace(current, checkpoint['workspace'])
    return current


def capture():
    raw=sys.stdin.buffer.read(65537)
    if len(raw)>65536: raise ValueError('HOOK_INPUT_TOO_LARGE')
    event=json.loads(raw)
    if event.get('hook_event_name')!='SessionStart' or not valid_id(event.get('session_id')):
        raise ValueError('HOOK_IDENTITY_INVALID')
    cwd=event.get('cwd')
    if not isinstance(cwd,str) or not Path(cwd).is_absolute(): raise ValueError('HOOK_WORKSPACE_INVALID')
    envfile=os.environ.get('CLAUDE_ENV_FILE','')
    if not Path(envfile).is_absolute(): raise ValueError('CLAUDE_ENV_FILE_UNAVAILABLE')
    values=dict(MUSE_RUNTIME_PLATFORM='claude',MUSE_RUNTIME_SESSION_ID=event['session_id'],MUSE_RUNTIME_WORKSPACE=str(Path(cwd).resolve()))
    data=''.join('export '+key+'='+shlex.quote(value)+'\n' for key,value in values.items()).encode()
    fd=os.open(envfile,os.O_APPEND|os.O_WRONLY|os.O_CREAT|os.O_NOFOLLOW|os.O_NONBLOCK,0o600)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode): raise ValueError('UNSAFE_ENV_FILE')
        fcntl.flock(fd,fcntl.LOCK_EX)
        written=os.write(fd,data)
        if written!=len(data): raise OSError('SHORT_WRITE')
        os.fsync(fd)
    finally:
        os.close(fd)


if __name__=='__main__':
    try:
        if sys.argv[1:] == ['identity']: print(json.dumps(identity(),sort_keys=True))
        elif sys.argv[1:] == ['capture-claude-session']: capture()
        else: raise ValueError('UNKNOWN_RUNTIME_COMMAND')
    except (ValueError,OSError,TypeError,AttributeError) as exc:
        print('ERROR: '+(str(exc) if isinstance(exc,ValueError) else type(exc).__name__),file=sys.stderr)
        raise SystemExit(2)
