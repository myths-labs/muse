#!/usr/bin/env python3
"""Load the optional `.muse/orchestration.json` shared by the multi-lane tools.

There are no author-machine defaults. Lookup order: an explicit path (``--config``),
``MUSE_ORCHESTRATION_CONFIG``, then the nearest ``.muse/orchestration.json`` above the
working directory. Relative paths resolve against the project that holds ``.muse/``;
``~`` and ``${VAR}`` are expanded. The vault root falls back to ``OBSIDIAN_VAULT`` in
``.muse/paths.md``. Without a config every tool gets an empty configuration and must
report what it could not check instead of guessing.

Sibling scripts load this file with ``importlib`` because ``python3 -I`` does not put
the script directory on ``sys.path``::

    spec = importlib.util.spec_from_file_location('orchestration_config', os.path.join(HERE, 'orchestration_config.py'))
    oc = importlib.util.module_from_spec(spec); spec.loader.exec_module(oc)
"""
from __future__ import annotations
import glob
import json
import os
from pathlib import Path
import re
import sys

CONFIG_NAME = '.muse/orchestration.json'
ENV_NAME = 'MUSE_ORCHESTRATION_CONFIG'
VAR = re.compile(r'\$\{([A-Za-z_][A-Za-z0-9_]*)\}')
PATHS_LINE = re.compile(r'^\s*([A-Z_][A-Z0-9_]*)\s*:\s*(\S.*?)\s*$')


class ConfigError(ValueError):
    pass


def _expand(value):
    def repl(match):
        name = match.group(1)
        if name not in os.environ:
            raise ConfigError('UNSET_VARIABLE: ' + name)
        return os.environ[name]
    return os.path.expanduser(VAR.sub(repl, value))


def find(explicit=None, start=None):
    """Return the config path in use, or None when the project has none."""
    chosen = explicit or os.environ.get(ENV_NAME)
    if chosen:
        path = Path(_expand(str(chosen)))
        if not path.is_file():
            raise ConfigError('CONFIG_NOT_FOUND: ' + str(path))
        return path.resolve()
    anchor = Path(start or os.getcwd()).resolve()
    for root in (anchor, *anchor.parents):
        candidate = root / CONFIG_NAME
        if candidate.is_file():
            return candidate
    return None


def _paths_md(root):
    """Read KEY: value pairs from .muse/paths.md (commented lines are ignored)."""
    result = {}
    path = root / '.muse' / 'paths.md'
    if not path.is_file():
        return result
    for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
        match = PATHS_LINE.match(line)
        if match:
            result[match.group(1)] = match.group(2)
    return result


class Config:
    def __init__(self, data, path=None):
        if not isinstance(data, dict):
            raise ConfigError('CONFIG_NOT_OBJECT')
        if data and data.get('schema_version') != 1:
            raise ConfigError('UNSUPPORTED_SCHEMA')
        self.data = data
        self.path = path
        # .muse/orchestration.json -> project root two levels up
        self.root = path.parent.parent if path else Path(os.getcwd()).resolve()

    def get(self, dotted, default=None):
        value = self.data
        for part in dotted.split('.'):
            if not isinstance(value, dict) or part not in value:
                return default
            value = value[part]
        return value

    def path_of(self, value):
        """Resolve one configured path; None stays None."""
        if value in (None, ''):
            return None
        path = Path(_expand(str(value)))
        return path if path.is_absolute() else (self.root / path)

    def paths(self, dotted):
        return [self.path_of(v) for v in (self.get(dotted) or []) if v]

    def globbed(self, dotted):
        """Expand configured glob patterns; results are sorted and de-duplicated."""
        seen, out = set(), []
        for pattern in self.paths(dotted):
            for hit in sorted(glob.glob(str(pattern), recursive=True)):
                real = os.path.realpath(hit)
                if real not in seen and os.path.isfile(hit):
                    seen.add(real)
                    out.append(Path(hit))
        return out

    def vault_root(self):
        configured = self.get('vault.root')
        if configured:
            return self.path_of(configured)
        fallback = _paths_md(self.root).get('OBSIDIAN_VAULT')
        return self.path_of(fallback) if fallback else None

    def lanes(self):
        """Orchestrator first, then user-defined lanes, each as a dict with an id."""
        out = []
        orchestrator = self.get('orchestrator')
        if isinstance(orchestrator, dict):
            out.append(dict(orchestrator, id=orchestrator.get('id', 'orchestrator')))
        for lane in self.get('lanes') or []:
            if isinstance(lane, dict) and lane.get('id'):
                out.append(lane)
        return out


def load(explicit=None, start=None):
    path = find(explicit, start)
    if path is None:
        return Config({}, None)
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
        raise ConfigError('CONFIG_UNREADABLE: ' + str(error))
    return Config(data, path)


if __name__ == '__main__':
    explicit = sys.argv[sys.argv.index('--config') + 1] if '--config' in sys.argv[:-1] else None
    try:
        config = load(explicit)
    except ConfigError as error:
        print(json.dumps({'status': 'FAIL', 'error': str(error)}))
        raise SystemExit(2)
    print(json.dumps({'status': 'PASS' if config.path else 'UNCONFIGURED',
                      'config': str(config.path) if config.path else None,
                      'root': str(config.root),
                      'lanes': [lane['id'] for lane in config.lanes()],
                      'vault': str(config.vault_root()) if config.vault_root() else None}, ensure_ascii=False))
