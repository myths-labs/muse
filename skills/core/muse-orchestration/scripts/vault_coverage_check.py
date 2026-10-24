#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check that the Obsidian vault did not miss anything from a checkpoint file.

Why: a vault can silently stop being written for days when no flow writes it. A freshness check
(vault_freshness.py) only says "something was written"; this says "every owner quote and every
tracked id in these source lines is in the vault".

What it checks, for source lines [--from, --to] of the checkpoint file (vault.coverage_source):
  - every owner quote: a quoted span 「…」, 『…』 or “…” (4 or more chars) that starts within
    40 chars after the owner's name (owner.name or --owner; case-sensitive)
  - every id matching one of vault.id_patterns (regular expressions, e.g. deploy ids); with no
    patterns only quotes are checked
Each item must appear somewhere in the vault's vault.coverage_dirs (default daily/ and decisions/,
top-level *.md only), compared after whitespace removal on the item's first 10 chars.

Items judged not to be owner words or not worth a vault entry go in the skip table
(vault.coverage_skip or --skip; TSV: key<TAB>source line<TAB>reason; key = the first 10 chars after
whitespace removal; lines starting with # are comments); they are not counted as missing.

Usage:  python3 -I vault_coverage_check.py --from N [--to M] [--vault PATH] [--source PATH]
                                           [--skip PATH] [--owner NAME] [--config PATH]
Exit 0 = nothing missing (RESULT: GREEN), 1 = something missing (RESULT: RED, each listed with its
source line), 2 = bad input or UNCONFIGURED (no vault, source or owner name: nothing is guessed).
Read-only. Python 3.7+, standard library only.
"""
import argparse
import importlib.util
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KEY_LEN = 10
GAP = 40
MIN_QUOTE = 4
QUOTE_PAIRS = (('「', '」'), ('『', '』'), ('“', '”'))
DEFAULT_DIRS = ['daily', 'decisions']


def load_config_module():
    spec = importlib.util.spec_from_file_location('orchestration_config', os.path.join(HERE, 'orchestration_config.py'))
    oc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oc)
    return oc


def quote_regex(owner):
    marks = re.escape(''.join(o + c for o, c in QUOTE_PAIRS))
    spans = '|'.join('%s([^%s\\n]{%d,})%s' % (re.escape(o), re.escape(c), MIN_QUOTE, re.escape(c))
                     for o, c in QUOTE_PAIRS)
    return re.compile('%s[^%s\\n]{0,%d}(?:%s)' % (re.escape(owner), marks, GAP, spans))


def squash(text):
    return re.sub(r'\s+', '', text)


def vault_text(vault, dirs):
    parts = []
    for sub in dirs:
        root = os.path.join(vault, sub)
        if not os.path.isdir(root):
            continue
        for name in sorted(os.listdir(root)):
            if name.endswith('.md'):
                with open(os.path.join(root, name), encoding='utf-8', errors='replace') as fh:
                    parts.append(fh.read())
    return squash('\n'.join(parts))


def finish(code, *lines):
    for line in lines:
        print(line)
    return code


def main():
    ap = argparse.ArgumentParser(description='Obsidian vault coverage check')
    ap.add_argument('--from', dest='start', type=int, required=True)
    ap.add_argument('--to', dest='end', type=int, default=0)
    ap.add_argument('--vault', default=None, help='overrides vault.root')
    ap.add_argument('--source', default=None, help='overrides vault.coverage_source')
    ap.add_argument('--skip', default=None, help='overrides vault.coverage_skip')
    ap.add_argument('--owner', default=None, help='overrides owner.name')
    ap.add_argument('--config', default=None)
    args = ap.parse_args()

    oc = load_config_module()
    try:
        config = oc.load(args.config)
        cli = lambda value: os.path.abspath(os.path.expanduser(value)) if value else None
        source = cli(args.source) or config.path_of(config.get('vault.coverage_source'))
        vault = cli(args.vault) or config.vault_root()
        skip_path = cli(args.skip) or config.path_of(config.get('vault.coverage_skip'))
    except oc.ConfigError as error:
        return finish(2, 'CONFIG_ERROR: %s' % error, 'RESULT: UNCONFIGURED')
    owner = args.owner or config.get('owner.name')
    patterns = config.get('vault.id_patterns') or []
    dirs = config.get('vault.coverage_dirs') or DEFAULT_DIRS

    unset = [name for name, value in (('vault.root (or --vault)', vault),
                                      ('vault.coverage_source (or --source)', source),
                                      ('owner.name (or --owner)', owner)) if not value]
    if unset:
        return finish(2, 'UNCONFIGURED: set %s' % ', '.join(unset), 'RESULT: UNCONFIGURED')
    if not oc.is_note_file(source):
        # Matches are printed, so the source must be a plain note, never .env* or key material.
        return finish(2, 'bad source: %s is not a plain note (.md/.markdown/.txt/.tsv)' % source,
                      'RESULT: UNCONFIGURED')
    if not isinstance(owner, str) or not isinstance(patterns, list) or not all(isinstance(p, str) for p in patterns) \
            or not isinstance(dirs, list) or not all(isinstance(d, str) for d in dirs):
        return finish(2, 'bad config: owner.name must be a string, vault.id_patterns and vault.coverage_dirs '
                         'lists of strings', 'RESULT: UNCONFIGURED')
    try:
        ids = [re.compile(p) for p in patterns]
    except re.error as error:
        return finish(2, 'bad vault.id_patterns entry: %s' % error, 'RESULT: UNCONFIGURED')
    source, vault = str(source), str(vault)
    if not os.path.isfile(source):
        return finish(2, 'source not found: %s' % source)
    if not os.path.isdir(vault):
        return finish(2, 'vault not found: %s' % vault)

    with open(source, encoding='utf-8', errors='replace') as fh:
        lines = fh.read().split('\n')
    end = args.end or len(lines)
    if args.start < 1 or args.start > end or end > len(lines):
        return finish(2, 'bad range %d-%d (file has %d lines)' % (args.start, end, len(lines)))
    haystack = vault_text(vault, dirs)
    skip = set()
    if skip_path and os.path.isfile(str(skip_path)):
        with open(str(skip_path), encoding='utf-8', errors='replace') as fh:
            for row in fh:
                if row.strip() and not row.startswith('#'):
                    skip.add(squash(row.split('\t')[0])[:KEY_LEN])

    quotes = quote_regex(owner)
    missing, total = [], 0
    for no in range(args.start, end + 1):
        line = lines[no - 1]
        items = [('quote', next(g for g in m.groups() if g is not None)) for m in quotes.finditer(line)]
        for pattern in ids:
            items += [('id', m.group(0)) for m in pattern.finditer(line) if m.group(0)]
        seen = set()
        for kind, item in items:
            key = squash(item)[:KEY_LEN]
            if not key or key in seen or key in skip:
                continue
            seen.add(key)
            total += 1
            if key not in haystack:
                missing.append((no, kind, item[:60]))

    name = os.path.basename(source)
    print('source %s lines %d-%d: %d items, %d missing' % (name, args.start, end, total, len(missing)))
    for no, kind, item in missing:
        print('  MISSING %s:%d %s "%s"' % (name, no, kind, item))
    print('RESULT: %s' % ('GREEN' if not missing else 'RED'))
    return 0 if not missing else 1


if __name__ == '__main__':
    sys.exit(main())
