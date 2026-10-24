#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""recall.py - search ALL memory before anyone says "it is not in my records".

Why: an agent session loads only the memory index of its own working directory, the index is
size-capped and gets compressed, and many decisions live only in lane checkpoint files. Asked
"do we also use ExampleVendor?", a session answered "it never appeared in my records" while the
answer sat in another project's memory directory. This tool searches all of them in one go.

Usage:
    python3 -I recall.py [--config PATH] [--projects-root DIR] <keyword> [<keyword> ...]
    e.g. python3 -I recall.py examplevendor "example vendor"

Keywords are OR-ed (any hit) and case-insensitive. Give synonyms in every language your notes use.

Searched (nothing per-directory is hard-coded):
    <memory.projects_root>/*/memory/**/*.md   every project's memory dir (default ~/.claude/projects)
    checkpoints.files + checkpoints.globs     lane checkpoint files; a named file that is missing is reported
    extra_search_globs                        any other files worth searching (fact banks, ...)
A path under a `removable_roots` entry is searched only while that root is a real mount point (an
unplugged drive can leave an empty stub directory behind, so the bare path is not enough). Otherwise
it is skipped with a warning: "not found" then does not mean "not there".

Output: grouped by file, "path:line  first 200 chars", at most 8 lines per file and 80 lines in
total; the last line is the total hit count. Standard library only, no network, read-only.
Exit 0 after any search (also with 0 hits), 2 on a usage or configuration error.
"""
import argparse
import glob
import importlib.util
import os
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PROJECTS_ROOT = os.path.join('~', '.claude', 'projects')

PER_FILE = 8
TOTAL = 80
WIDTH = 200


def load_config_module():
    spec = importlib.util.spec_from_file_location('orchestration_config', os.path.join(HERE, 'orchestration_config.py'))
    oc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oc)
    return oc


def norm(path):
    return os.path.normpath(os.path.abspath(str(path)))


def removable_roots(config):
    """[(root, mounted)] for every configured removable root."""
    out = []
    for path in config.paths('removable_roots'):
        root = norm(path)
        try:
            mounted = os.path.ismount(root)
        except OSError:
            mounted = False
        out.append((root, mounted))
    return out


def offline_root(path, roots):
    """The unmounted removable root that holds `path`, else None."""
    p = norm(path)
    for root, mounted in roots:
        if not mounted and (p == root or p.startswith(root.rstrip(os.sep) + os.sep)):
            return root
    return None


class Sources:
    def __init__(self, roots):
        self.roots = roots
        self.skipped = {}  # unmounted root -> configured entries not (fully) searched
        self.missing = []  # named files that do not exist
        self.seen = set()

    def gate(self, path, entry):
        root = offline_root(path, self.roots)
        if root:
            entries = self.skipped.setdefault(root, [])
            if str(entry) not in entries:
                entries.append(str(entry))
            return False
        return True

    def add(self, out, path, entry):
        if not os.path.isfile(path) or not self.gate(path, entry):
            return
        real = os.path.realpath(path)
        if real not in self.seen:
            self.seen.add(real)
            out.append(str(path))

    def named(self, paths):
        out = []
        for path in paths:
            if not self.gate(path, path):
                continue
            if not os.path.isfile(str(path)):
                self.missing.append(str(path))
                continue
            self.add(out, str(path), path)
        return out

    def globbed(self, patterns):
        out = []
        for pattern in patterns:
            if not self.gate(pattern, pattern):
                continue
            for hit in sorted(glob.glob(str(pattern), recursive=True)):
                self.add(out, hit, pattern)
        return out


def search_file(path, needles):
    hits = []
    try:
        with open(path, encoding='utf-8', errors='replace') as f:
            for no, line in enumerate(f, 1):
                low = line.casefold()
                if any(n in low for n in needles):
                    hits.append((no, ' '.join(line.split())[:WIDTH]))
    except OSError as e:
        return None, str(e)
    return hits, None


def scripts_of(text):
    """Unicode script names (first word of the character name: LATIN, CJK, CYRILLIC, ...) of the letters."""
    out = set()
    for ch in text:
        if ch.isalpha():
            try:
                out.add(unicodedata.name(ch).split(' ')[0])
            except ValueError:
                continue
    return out


def main(argv):
    ap = argparse.ArgumentParser(description='Search every memory directory, checkpoint and extra file at once.')
    ap.add_argument('--config', default=None, help='orchestration.json (default: MUSE_ORCHESTRATION_CONFIG or nearest .muse/)')
    ap.add_argument('--projects-root', default=None, help='overrides memory.projects_root')
    ap.add_argument('keywords', nargs='*')
    args = ap.parse_intermixed_args(argv)
    keywords = [k.strip() for k in args.keywords if k.strip()]
    if not keywords:
        print(__doc__)
        return 2

    oc = load_config_module()
    try:
        config = oc.load(args.config)
        roots = removable_roots(config)
        if args.projects_root:
            projects_root = norm(os.path.expanduser(args.projects_root))
        else:
            projects_root = norm(config.path_of(config.get('memory.projects_root') or DEFAULT_PROJECTS_ROOT))
        sources = Sources(roots)
        memory = []
        if sources.gate(projects_root, projects_root):
            memory = sources.globbed([os.path.join(projects_root, '*', 'memory', '**', '*.md')])
        checkpoints = sources.named(config.paths('checkpoints.files'))
        checkpoints += sources.globbed(config.paths('checkpoints.globs'))
        extra = sources.globbed(config.paths('extra_search_globs'))
    except oc.ConfigError as error:
        print('CONFIG_ERROR: %s' % error)
        return 2
    groups = [('memory', memory), ('checkpoints', checkpoints), ('extra', extra)]
    needles = [k.casefold() for k in keywords]

    memory_dirs = {os.path.relpath(p, projects_root).split(os.sep)[0] for p in memory}
    print('recall - keywords: %s (any hit, case-insensitive)' % ' | '.join(keywords))
    scope = 'scope: %d memory dirs (%d .md files) under %s · %d checkpoint files · %d extra files' % (
        len(memory_dirs), len(memory), projects_root, len(checkpoints), len(extra))
    if roots:
        mounted = sum(1 for _, m in roots if m)
        scope += ' · removable roots: %d mounted, %d not mounted' % (mounted, len(roots) - mounted)
    print(scope)
    if not os.path.isdir(projects_root) and not offline_root(projects_root, roots):
        print('WARNING: memory root not found: %s (set memory.projects_root or --projects-root)' % projects_root)
    for root, entries in sources.skipped.items():
        print('WARNING: removable root %s is not mounted; skipped: %s. "Not found" does not mean '
              '"not there"; search again once it is mounted.' % (root, ', '.join(entries)))
    for p in sources.missing:
        print('WARNING: missing: %s' % p)
    found_scripts = set()
    for k in keywords:
        found_scripts |= scripts_of(k)
    if len(found_scripts) == 1:
        print('hint: keywords are all one script; add synonyms in other languages '
              '(e.g. a name in its original script and in Latin letters).')

    total_lines, total_files, shown = 0, 0, 0
    hidden = {}  # category -> [files, lines] not displayed
    errors = []
    for category, paths in groups:
        printed_header = False
        for path in paths:
            hits, err = search_file(path, needles)
            if err:
                errors.append('%s (%s)' % (path, err))
                continue
            if not hits:
                continue
            total_lines += len(hits)
            total_files += 1
            room = min(PER_FILE, TOTAL - shown)
            if room <= 0:
                h = hidden.setdefault(category, [0, 0])
                h[0] += 1
                h[1] += len(hits)
                continue
            if not printed_header:
                print('\n== %s ==' % category)
                printed_header = True
            more = len(hits) - room
            print('# %s (%d matching lines%s)' % (path, len(hits), ', showing first %d' % room if more > 0 else ''))
            for no, text in hits[:room]:
                print('%s:%d  %s' % (path, no, text))
            shown += min(room, len(hits))
    if hidden:
        print('\n... over the %d-line limit, not shown: %s. Use a more specific keyword.' % (
            TOTAL, '; '.join('%s %d files %d lines' % (c, v[0], v[1]) for c, v in hidden.items())))
    for e in errors:
        print('WARNING: could not read %s' % e)
    print('\ntotal hits: %d lines in %d files (shown %d)' % (total_lines, total_files, shown))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
