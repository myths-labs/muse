#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""recall.py - search ALL memory before anyone says "it is not in my records".

Why: an agent session loads only the memory index of its own working directory, the index is
size-capped and gets compressed, and many decisions live only in lane checkpoint files. Asked
"do we also use ExampleVendor?", a session answered "it never appeared in my records" while the
answer sat in another project's memory directory. This tool searches all of them in one go.

Usage:
    python3 -I recall.py [--config PATH] [--projects-root DIR] [--why NAME] <keyword> [<keyword> ...]
    e.g. python3 -I recall.py examplevendor "example vendor"

Keywords are OR-ed (any hit) and case-insensitive. Give synonyms in every language your notes use.

Searched (nothing per-directory is hard-coded):
    <memory.projects_root>/*/memory/**/*.md   every project's memory dir (default ~/.claude/projects)
    checkpoints.files + checkpoints.globs     lane checkpoint files; a named file that is missing is reported
    extra_search_globs                        any other files worth searching (fact banks, ...)
Only plain notes are read (.md, .markdown, .txt, .tsv; never .env* files or credential folders such
as .ssh or .aws), because a project's config may come from an untrusted checkout.
A path under a `removable_roots` entry is searched only while that root is a real mount point (an
unplugged drive can leave an empty stub directory behind, so the bare path is not enough). Otherwise
it is skipped with a warning: "not found" then does not mean "not there".

Order inside the memory section: memories that still hold first, then superseded ones, then pointer files
(MEMORY.md and index-*.md, which only point at other memories); path order inside each class. A memory is
superseded when its frontmatter has one line `superseded_by: <newer-memory-name>` (also `[[name]]`, `name.md`,
`proj:name`, or several names separated by commas). Its heading then reads "superseded by: <name>" (with a note
if no memory has that name); it is shown later, never dropped, and if the line limit cuts it the closing notice
names it. Keys are read line by line, so notes whose frontmatter is not strict YAML work too.
--why NAME  after the normal output, explain why files whose path contains NAME are (not) near the top: how many
            keywords hit, the rule that put other files first, whether the line limit hid it, whether its successor matched.

Output: grouped by file, "path:line  first 200 chars", at most 8 lines per file and 80 lines in
total; the last line is the total hit count. Standard library only, no network, read-only.
Exit 0 after any search (also with 0 hits), 2 on a usage or configuration error.
"""
import argparse
import glob
import importlib.util
import os
import re
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
    def __init__(self, roots, is_note):
        self.roots = roots
        self.is_note = is_note  # only plain notes are printed; never .env*, keys or credential dirs
        self.skipped = {}  # unmounted root -> configured entries not (fully) searched
        self.missing = []  # named files that do not exist
        self.refused = []  # configured files that are not plain notes
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
        if not self.is_note(path):
            self.refused.append(str(path))
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


SUPERSEDED_RE = re.compile(r'^superseded_by:[ \t]*(.*?)[ \t]*$')
PROJECT_PREFIX_RE = re.compile(r'^[A-Za-z0-9_.-]{1,24}:')


def is_pointer_file(path):
    """MEMORY.md and index-*.md only point at other memories; they are listed after the content files."""
    name = os.path.basename(path)
    return name == 'MEMORY.md' or name.startswith('index-')


def superseded_by(path):
    """Names from a top-level `superseded_by:` line in the frontmatter, [] if there is none."""
    try:
        with open(path, encoding='utf-8-sig', errors='replace') as f:
            if f.readline().strip() != '---':
                return []
            for i, line in enumerate(f):
                if line.strip() == '---' or i > 60:
                    return []
                m = SUPERSEDED_RE.match(line)
                if m:
                    names = []
                    for part in re.split(r'[,;]', m.group(1)):
                        name = part.strip().strip('"\'').replace('[[', '').replace(']]', '').strip()
                        name = PROJECT_PREFIX_RE.sub('', name)
                        name = name[:-3] if name.endswith('.md') else name
                        if name:
                            names.append(name)
                    return names
    except OSError:
        pass
    return []


def superseded_mark(names, known):
    return ', superseded by: ' + ', '.join(n if n in known else n + ' (no memory has this name)' for n in names)


def matched_needles(path, needles):
    found = set()
    try:
        with open(path, encoding='utf-8', errors='replace') as f:
            for line in f:
                low = line.casefold()
                found.update(n for n in needles if n in low)
    except OSError:
        pass
    return found


def print_why(term, keywords, needles, groups, per_file, order, status, sup, name_paths):
    """--why NAME: explain the position of files whose path contains NAME."""
    low = term.casefold()
    print('\n== why: %s ==' % term)
    cands = [(c, p) for c, ps in groups for p in ps if low in p.casefold()]
    if not cands:
        print('No searched file has a path containing "%s". The path may be outside the searched set (memory dirs, '
              'checkpoints, extra globs), a removable root may be unmounted, or the name is misspelled.' % term)
        return
    if len(cands) > 5:
        print('%d files have a path containing "%s"; explaining the first 5. Use a longer name to narrow it.' % (len(cands), term))
    for category, path in cands[:5]:
        print('\nfile: %s (%s)' % (path, category))
        n = per_file.get(path)
        if n is None:
            print('- could not be read (see the WARNING above).')
            continue
        got = matched_needles(path, needles)
        hit = [k for k, nd in zip(keywords, needles) if nd in got]
        miss = [k for k, nd in zip(keywords, needles) if nd not in got]
        if not n:
            print('- 0 matching lines: none of %s occurs in this file (case-insensitive substring). It is not in '
                  'the results.' % ', '.join(keywords))
            print('- To bring it up: open the file, see which words it really uses, then change or add keywords.')
            continue
        print('- %d/%d keywords hit (%s%s), %d matching lines.' % (
            len(hit), len(keywords), ', '.join(hit), '; missed: ' + ', '.join(miss) if miss else '', n))
        ordered = order.get(category, [])
        rank = ordered.index(path) + 1
        if category == 'memory':
            cls = lambda q: (is_pointer_file(q), q in sup)
            ahead = ordered[:rank - 1]
            behind_class = [q for q in ahead if cls(q) < cls(path)]
            print('- rank %d of %d matching memory files. Order: current memories, then superseded ones, then pointer '
                  'files (MEMORY.md, index-*); path order inside each class.' % (rank, len(ordered)))
            why = []
            if is_pointer_file(path):
                why.append('it is a pointer file, listed after %d content files' % len(behind_class))
            elif path in sup:
                why.append('it is superseded (-> %s), listed after %d current files' % (', '.join(sup[path]), len(behind_class)))
            same = len(ahead) - len(behind_class)
            if same:
                why.append('%d files of the same class come first by path order' % same)
            print('- %d files before it: %s.' % (rank - 1, '; '.join(why) if why else 'none, it is first'))
            for succ in sup.get(path, []):
                sp = name_paths.get(succ)
                if not sp:
                    print('- successor "%s": no memory has this name (check the superseded_by line for a typo).' % succ)
                else:
                    sh = per_file.get(sp[0], 0)
                    print('- successor "%s": %s.' % (succ, 'matches %d lines, rank %d' % (sh, ordered.index(sp[0]) + 1)
                                                    if sh and sp[0] in ordered else 'does not match these keywords; open it directly'))
        else:
            print('- rank %d of %d in "%s" (listed in path order).' % (rank, len(ordered), category))
        if status.get(path) == 'hidden':
            first = min(i for i, q in enumerate(ordered) if status.get(q) == 'hidden') + 1
            print('- NOT shown: the %d-line limit was used up by the files before it (cut starts at rank %d). '
                  'Use a more specific keyword.' % (TOTAL, first))
        else:
            print('- shown.')


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
    ap.add_argument('--why', default=None, metavar='NAME', help='explain why files whose path contains NAME are (not) near the top')
    ap.add_argument('keywords', nargs='*')
    args = ap.parse_intermixed_args(argv)
    keywords = [k.strip() for k in args.keywords if k.strip()]
    if args.why is not None and not args.why.strip():
        print('--why needs part of a file name (e.g. --why preview-deployments)')
        return 2
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
        sources = Sources(roots, oc.is_note_file)
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
    if sources.refused:
        print('WARNING: skipped %d configured file(s) that are not plain notes (.md/.markdown/.txt/.tsv, '
              'no .env* or credential folders), e.g. %s' % (len(sources.refused), sources.refused[0]))
    found_scripts = set()
    for k in keywords:
        found_scripts |= scripts_of(k)
    if len(found_scripts) == 1:
        print('hint: keywords are all one script; add synonyms in other languages '
              '(e.g. a name in its original script and in Latin letters).')

    total_lines, total_files, shown = 0, 0, 0
    hidden = {}  # category -> [files, lines] not displayed
    errors = []
    per_file, order, status, sup = {}, {}, {}, {}  # for --why and for superseded_by
    name_paths = {}
    for p in memory:
        name_paths.setdefault(os.path.basename(p)[:-3], []).append(p)
    for category, paths in groups:
        results = []
        for path in paths:
            hits, err = search_file(path, needles)
            if err:
                errors.append('%s (%s)' % (path, err))
                continue
            per_file[path] = len(hits)
            if hits:
                results.append((path, hits))
        if category == 'memory':
            for path, _ in results:
                names = superseded_by(path)
                if names:
                    sup[path] = names
            # current memories, then superseded ones, then pointer files; sort is stable, so path order is kept
            results.sort(key=lambda r: (is_pointer_file(r[0]), r[0] in sup))
        order[category] = [r[0] for r in results]
        printed_header = False
        for path, hits in results:
            total_lines += len(hits)
            total_files += 1
            room = min(PER_FILE, TOTAL - shown)
            if room <= 0:
                status[path] = 'hidden'
                h = hidden.setdefault(category, [0, 0])
                h[0] += 1
                h[1] += len(hits)
                continue
            status[path] = 'shown'
            if not printed_header:
                print('\n== %s ==' % category)
                printed_header = True
            more = len(hits) - room
            print('# %s (%d matching lines%s%s)' % (path, len(hits), ', showing first %d' % room if more > 0 else '',
                                                  superseded_mark(sup[path], name_paths) if path in sup else ''))
            for no, text in hits[:room]:
                print('%s:%d  %s' % (path, no, text))
            shown += min(room, len(hits))
    if hidden:
        print('\n... over the %d-line limit, not shown: %s. Use a more specific keyword.' % (
            TOTAL, '; '.join('%s %d files %d lines' % (c, v[0], v[1]) for c, v in hidden.items())))
        cut = [q for q in order.get('memory', []) if status.get(q) == 'hidden' and q in sup]
        if cut:  # a superseded memory pushed behind the limit must not vanish silently
            print('Superseded memories pushed past the limit, not shown: %s.' % '; '.join(
                '%s -> %s' % (os.path.basename(q)[:-3], ', '.join(sup[q])) for q in cut))
    for e in errors:
        print('WARNING: could not read %s' % e)
    print('\ntotal hits: %d lines in %d files (shown %d)' % (total_lines, total_files, shown))
    if args.why:
        print_why(args.why.strip(), keywords, needles, groups, per_file, order, status, sup, name_paths)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
