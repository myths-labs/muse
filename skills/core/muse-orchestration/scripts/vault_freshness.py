#!/usr/bin/env python3
"""Report how fresh the Obsidian vault is.

Prints the newest .md file's mtime and its age in hours (dot directories such as .obsidian are
skipped). Exits 1 and prints "STALE: vault not written for more than N hours" when the newest
note is older than the threshold (or the vault has no .md file at all), else 0.

The vault comes from --vault, else vault.root, else OBSIDIAN_VAULT in .muse/paths.md; the
threshold from --max-hours, else vault.freshness_hours, else 24. Without a vault the result is
UNCONFIGURED (exit 2): no path is guessed.

Usage:  python3 -I vault_freshness.py [--vault PATH] [--max-hours N] [--config PATH]
Exit 0 = fresh, 1 = stale or empty, 2 = UNCONFIGURED or the vault directory does not exist.
Standard library only, read-only (never writes to the vault).
"""
import argparse
import importlib.util
import os
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MAX_HOURS = 24.0


def load_config_module():
    spec = importlib.util.spec_from_file_location('orchestration_config', os.path.join(HERE, 'orchestration_config.py'))
    oc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oc)
    return oc


def newest_markdown(root):
    """Return (mtime, path) of the newest .md under root, skipping dot dirs."""
    best = (0.0, None)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        for name in filenames:
            if not name.endswith('.md'):
                continue
            path = os.path.join(dirpath, name)
            try:
                mtime = os.stat(path).st_mtime
            except OSError:
                continue
            if mtime > best[0]:
                best = (mtime, path)
    return best


def main():
    ap = argparse.ArgumentParser(description='Obsidian vault freshness check')
    ap.add_argument('--vault', default=None, help='overrides vault.root')
    ap.add_argument('--max-hours', type=float, default=None, help='overrides vault.freshness_hours (default 24)')
    ap.add_argument('--config', default=None)
    args = ap.parse_args()

    oc = load_config_module()
    try:
        config = oc.load(args.config)
        vault = os.path.abspath(os.path.expanduser(args.vault)) if args.vault else config.vault_root()
    except oc.ConfigError as error:
        print('CONFIG_ERROR: %s' % error)
        return 2
    if not vault:
        print('UNCONFIGURED: set vault.root in orchestration.json, OBSIDIAN_VAULT in .muse/paths.md, or pass --vault')
        return 2
    max_hours = args.max_hours
    if max_hours is None:
        max_hours = config.get('vault.freshness_hours')
    if max_hours is None:
        max_hours = DEFAULT_MAX_HOURS
    try:
        max_hours = float(max_hours)
    except (TypeError, ValueError):
        print('bad vault.freshness_hours: %r' % (max_hours,))
        return 2
    vault = str(vault)
    if not os.path.isdir(vault):
        print('vault directory does not exist: %s' % vault)
        return 2

    mtime, path = newest_markdown(vault)
    if path is None:
        print('no .md file in the vault: %s' % vault)
        return 1

    age_h = (time.time() - mtime) / 3600.0
    stamp = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
    print('newest file: %s' % os.path.relpath(path, vault))
    print('modified: %s (local time)' % stamp)
    print('age: %.1f hours' % age_h)
    if age_h > max_hours:
        print('STALE: vault not written for more than %g hours' % max_hours)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
