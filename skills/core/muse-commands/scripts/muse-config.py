#!/usr/bin/env python3
"""Resolve explicitly configured project roots without author-machine defaults."""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import sys


def unique(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError('DUPLICATE_CONFIG_KEY')
        result[key] = value
    return result


def load(config_path=None):
    explicit = str(config_path) if config_path is not None else os.environ.get('MUSE_CONFIG')
    config = Path(explicit).expanduser() if explicit else None
    if config is None and os.environ.get('DYA_ROOT'):
        roots = {'dya': Path(os.environ['DYA_ROOT']).expanduser().resolve()}
        for name, key in [('prometheus', 'PROMETHEUS_ROOT'), ('muse', 'MUSE_OSS_ROOT')]:
            if os.environ.get(key):
                roots[name] = Path(os.environ[key]).expanduser().resolve()
        return 'dya', roots
    if config is None:
        anchor = Path.cwd()
        for flag in ('--workspace', '--cwd'):
            if flag in sys.argv and sys.argv.index(flag) + 1 < len(sys.argv):
                anchor = Path(sys.argv[sys.argv.index(flag) + 1]).resolve()
                break
        for root in (anchor, *anchor.parents):
            candidate = root / '.muse/config.json'
            if candidate.exists() or candidate.is_symlink():
                config = candidate
                break
    if config is not None:
        if config.is_symlink() or not config.is_file() or config.stat().st_size > 65536:
            raise ValueError('INVALID_MUSE_CONFIG_FILE')
        data = json.loads(config.read_text(), object_pairs_hook=unique)
        if not isinstance(data, dict) or set(data) != {'schema_version', 'role_home', 'projects'}:
            raise ValueError('INVALID_MUSE_CONFIG')
        if type(data['schema_version']) is not int or data['schema_version'] != 1:
            raise ValueError('UNKNOWN_MUSE_CONFIG_VERSION')
        if not isinstance(data['projects'], dict) or not data['projects']:
            raise ValueError('INVALID_MUSE_PROJECTS')
        roots = {}
        for name, path in data['projects'].items():
            if not re.fullmatch(r'[a-z][a-z0-9_-]{0,31}', name) or not isinstance(path, str) or not path.strip():
                raise ValueError('INVALID_MUSE_PROJECT')
            roots[name] = (config.resolve().parent.parent / Path(path).expanduser()).resolve()
        center = data['role_home']
        if not isinstance(center, str) or center not in roots:
            raise ValueError('INVALID_MUSE_ROLE_HOME')
        if len(set(roots.values())) != len(roots):
            raise ValueError('AMBIGUOUS_MUSE_PROJECT_ROOTS')
        return center, roots
    # An explicitly configured legacy installation retains its stored identities.
    if os.environ.get('DYA_ROOT'):
        roots = {'dya': Path(os.environ['DYA_ROOT']).expanduser().resolve()}
        for name, key in [('prometheus', 'PROMETHEUS_ROOT'), ('muse', 'MUSE_OSS_ROOT')]:
            if os.environ.get(key):
                roots[name] = Path(os.environ[key]).expanduser().resolve()
        return 'dya', roots
    raise ValueError('MUSE_CONFIG_NOT_FOUND: install MUSE in this project or set MUSE_CONFIG')


if __name__ == '__main__':
    try:
        center, roots = load()
        print(json.dumps({'role_home': center, 'projects': {k: str(v) for k, v in roots.items()}}))
    except (ValueError, OSError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
