#!/usr/bin/env python3
"""Behaviour of the orchestration recall, vault and wall-recovery tools, in disposable directories only.

Every run gets a temporary HOME, a temporary working directory and no MUSE_ORCHESTRATION_CONFIG, so
nothing under the real ~/.claude is read.
"""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / 'skills' / 'core' / 'muse-orchestration' / 'scripts'
FAKE_SECRET = 'FAKE_TOOL_RESULT_VALUE_9d8c7b6a'


class OrchestrationTools(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='muse orchestration tools ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.home = self.root / 'home'
        self.work = self.root / 'work'
        self.project = self.root / 'project'
        for folder in (self.home, self.work, self.project / '.muse'):
            folder.mkdir(parents=True)
        self.env = dict(os.environ, HOME=str(self.home), PYTHONDONTWRITEBYTECODE='1')
        self.env.pop('MUSE_ORCHESTRATION_CONFIG', None)

    # helpers
    def run_tool(self, name, *args):
        return subprocess.run([sys.executable, '-I', str(SCRIPTS / name)] + [str(a) for a in args],
                              cwd=str(self.work), env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              encoding='utf-8', errors='replace', timeout=60)

    def write(self, path, text, age_hours=0.0):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        if age_hours:
            stamp = time.time() - age_hours * 3600
            os.utime(str(path), (stamp, stamp))
        return path

    def config(self, **data):
        data = dict(schema_version=1, **data)
        return self.write(self.project / '.muse' / 'orchestration.json', json.dumps(data, ensure_ascii=False))

    @staticmethod
    def hit_lines(stdout):
        return [line for line in stdout.splitlines() if re.match(r'^\S.*:\d+  ', line)]

    # recall
    def test_recall_hits_memory_checkpoints_and_extra_files(self):
        projects = self.root / 'projects'
        self.write(projects / 'proj-a' / 'memory' / 'note.md', 'intro\nWe picked ExampleVendor for meshes.\n')
        self.write(projects / 'proj-b' / 'memory' / 'deep' / 'more.md', 'examplevendor quote came back\n')
        self.write(projects / 'proj-b' / 'other' / 'not-memory.md', 'ExampleVendor outside memory\n')
        self.write(self.project / 'docs' / 'lanes' / 'build' / 'OPEN_THREADS.md', 'line\nline\nEXAMPLEVENDOR retry\n')
        self.write(self.project / 'docs' / 'facts' / 'FACTS.md', 'ExampleVendor price list\n')
        cfg = self.config(memory={'projects_root': str(projects)},
                          checkpoints={'files': ['docs/lanes/gone/OPEN_THREADS.md'], 'globs': ['docs/lanes/**/OPEN_THREADS*.md']},
                          extra_search_globs=['docs/facts/*.md'])
        result = self.run_tool('recall.py', '--config', cfg, 'ExampleVendor')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        out = result.stdout
        self.assertIn('scope: 2 memory dirs (2 .md files)', out)
        self.assertIn('== memory ==', out)
        self.assertIn('== checkpoints ==', out)
        self.assertIn('== extra ==', out)
        self.assertIn('note.md:2  We picked ExampleVendor for meshes.', out)
        self.assertIn('OPEN_THREADS.md:3  EXAMPLEVENDOR retry', out)
        self.assertNotIn('not-memory.md', out)
        self.assertIn('WARNING: missing: ' + str(self.project / 'docs' / 'lanes' / 'gone' / 'OPEN_THREADS.md'), out)
        self.assertIn('hint: keywords are all one script', out)
        self.assertEqual(out.strip().splitlines()[-1], 'total hits: 4 lines in 4 files (shown 4)')

    def test_recall_zero_hits_and_mixed_scripts(self):
        projects = self.root / 'projects'
        self.write(projects / 'proj-a' / 'memory' / 'note.md', 'nothing relevant here\n')
        cfg = self.config(memory={'projects_root': str(projects)})
        result = self.run_tool('recall.py', '--config', cfg, 'examplevendor', '示例供应商')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn('hint:', result.stdout)
        self.assertEqual(self.hit_lines(result.stdout), [])
        self.assertEqual(result.stdout.strip().splitlines()[-1], 'total hits: 0 lines in 0 files (shown 0)')

    def test_recall_caps_per_file_and_total(self):
        projects = self.root / 'projects'
        for n in range(12):
            body = ''.join('needle row %d\n' % i for i in range(9))
            self.write(projects / ('proj-%02d' % n) / 'memory' / 'n.md', body)
        cfg = self.config(memory={'projects_root': str(projects)})
        result = self.run_tool('recall.py', '--config', cfg, 'needle')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        out = result.stdout
        self.assertEqual(len(self.hit_lines(out)), 80)
        self.assertIn('(9 matching lines, showing first 8)', out)
        self.assertIn('over the 80-line limit, not shown: memory 2 files 18 lines', out)
        self.assertEqual(out.strip().splitlines()[-1], 'total hits: 108 lines in 12 files (shown 80)')

    def test_recall_skips_unmounted_removable_root_with_warning(self):
        projects = self.root / 'projects'
        self.write(projects / 'proj-a' / 'memory' / 'note.md', 'ExampleVendor on the main disk\n')
        drive = self.root / 'drive-stub'
        self.write(drive / 'lanes' / 'OPEN_THREADS.md', 'ExampleVendor only on the drive\n')
        self.assertFalse(os.path.ismount(str(drive)))
        cfg = self.config(memory={'projects_root': str(projects)}, removable_roots=[str(drive)],
                          checkpoints={'files': [str(drive / 'lanes' / 'OPEN_THREADS.md')],
                                       'globs': [str(drive / '**' / '*.md')]})
        result = self.run_tool('recall.py', '--config', cfg, 'examplevendor')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        out = result.stdout
        self.assertIn('WARNING: removable root %s is not mounted' % drive, out)
        self.assertIn('"Not found" does not mean "not there"', out)
        self.assertIn('removable roots: 0 mounted, 1 not mounted', out)
        self.assertNotIn('only on the drive', out)
        self.assertNotIn('WARNING: missing', out)
        self.assertEqual(out.strip().splitlines()[-1], 'total hits: 1 lines in 1 files (shown 1)')

    def test_recall_without_config_searches_default_projects_root(self):
        self.write(self.home / '.claude' / 'projects' / 'p' / 'memory' / 'a.md', 'ExampleVendor in the default root\n')
        result = self.run_tool('recall.py', 'examplevendor')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('a.md:1  ExampleVendor in the default root', result.stdout)
        self.assertEqual(self.run_tool('recall.py').returncode, 2)

    # vault coverage
    def coverage_fixture(self, id_patterns=('rel_[A-Za-z0-9]{6,}',)):
        self.write(self.project / 'docs' / 'OPEN_THREADS.md', '\n'.join([
            '# checkpoint',
            'Owner said 「ship the blue version first」 at noon',
            'Owner: “keep the old price for now” and rel_AbC123xyz went out',
            'later Owner wrote 『rollback only after review』',
            'Someone else said 「not an owner quote at all」',
            'Owner 「ok」 is too short to count',
        ]) + '\n')
        self.write(self.project / 'vault' / 'daily' / '2026-01-01.md', 'ship the  blue\nversion first\nrel_AbC123xyz\n')
        self.write(self.project / 'vault' / 'decisions' / 'pricing.md', 'keep the old price for now\n')
        self.write(self.project / 'vault' / 'daily' / 'nested' / 'deep.md', 'rollback only after review\n')
        return self.config(owner={'name': 'Owner'},
                           vault={'root': 'vault', 'coverage_source': 'docs/OPEN_THREADS.md',
                                  'coverage_skip': 'docs/skip.tsv', 'id_patterns': list(id_patterns)})

    def test_coverage_green_when_every_item_is_in_the_vault(self):
        cfg = self.coverage_fixture()
        result = self.run_tool('vault_coverage_check.py', '--config', cfg, '--from', 1, '--to', 3)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('source OPEN_THREADS.md lines 1-3: 3 items, 0 missing', result.stdout)
        self.assertEqual(result.stdout.strip().splitlines()[-1], 'RESULT: GREEN')

    def test_coverage_without_id_patterns_checks_quotes_only(self):
        cfg = self.coverage_fixture(id_patterns=())
        result = self.run_tool('vault_coverage_check.py', '--config', cfg, '--from', 1, '--to', 3)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('lines 1-3: 2 items, 0 missing', result.stdout)

    def test_coverage_red_lists_missing_items_with_source_line(self):
        cfg = self.coverage_fixture()
        result = self.run_tool('vault_coverage_check.py', '--config', cfg, '--from', 1)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        out = result.stdout
        self.assertIn('lines 1-7: 4 items, 1 missing', out)
        self.assertIn('MISSING OPEN_THREADS.md:4 quote "rollback only after review"', out)
        self.assertNotIn('not an owner quote', out)
        self.assertEqual(out.strip().splitlines()[-1], 'RESULT: RED')

    def test_coverage_skip_table_excludes_an_item(self):
        cfg = self.coverage_fixture()
        self.write(self.project / 'docs' / 'skip.tsv',
                   '# key\tsource line\treason\nrollback only after review\t4\tcovered elsewhere\n')
        result = self.run_tool('vault_coverage_check.py', '--config', cfg, '--from', 1)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('lines 1-7: 3 items, 0 missing', result.stdout)
        self.assertEqual(result.stdout.strip().splitlines()[-1], 'RESULT: GREEN')

    def test_coverage_cli_overrides_and_owner_flag(self):
        self.coverage_fixture()
        result = self.run_tool('vault_coverage_check.py', '--from', 2, '--to', 2, '--owner', 'Owner',
                               '--vault', self.project / 'vault', '--source', self.project / 'docs' / 'OPEN_THREADS.md')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('lines 2-2: 1 items, 0 missing', result.stdout)

    def test_coverage_unconfigured_exits_2(self):
        result = self.run_tool('vault_coverage_check.py', '--from', 1)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn('UNCONFIGURED', result.stdout)
        self.assertIn('vault.root', result.stdout)
        self.assertIn('owner.name', result.stdout)
        self.assertEqual(self.run_tool('vault_coverage_check.py').returncode, 2)

    # vault freshness
    def test_freshness_fresh_vault_exits_0(self):
        self.write(self.project / 'vault' / 'daily' / 'today.md', 'note\n', age_hours=1)
        self.write(self.project / 'vault' / '.obsidian' / 'cache.md', 'newer but in a dot directory\n')
        cfg = self.config(vault={'root': 'vault'})
        result = self.run_tool('vault_freshness.py', '--config', cfg)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('newest file: ' + os.path.join('daily', 'today.md'), result.stdout)
        self.assertNotIn('STALE', result.stdout)

    def test_freshness_stale_vault_exits_1_and_respects_configured_hours(self):
        self.write(self.project / 'vault' / 'daily' / 'old.md', 'note\n', age_hours=48)
        cfg = self.config(vault={'root': 'vault'})
        result = self.run_tool('vault_freshness.py', '--config', cfg)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('STALE: vault not written for more than 24 hours', result.stdout)
        cfg = self.config(vault={'root': 'vault', 'freshness_hours': 72})
        self.assertEqual(self.run_tool('vault_freshness.py', '--config', cfg).returncode, 0)
        self.assertEqual(self.run_tool('vault_freshness.py', '--config', cfg, '--max-hours', 12).returncode, 1)

    def test_freshness_without_vault_exits_2(self):
        result = self.run_tool('vault_freshness.py')
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn('UNCONFIGURED', result.stdout)
        result = self.run_tool('vault_freshness.py', '--vault', self.root / 'no-such-vault')
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)

    # wall recovery
    def transcript(self, path, rows, age_hours=0.0):
        return self.write(path, ''.join(json.dumps(r) + '\n' for r in rows), age_hours)

    def wall_fixture(self):
        projects = self.root / 'projects'
        session = '0f0e0d0c-1111-2222-3333-444455556666'
        folder = projects / 'proj-x'
        notice = ('<task-notification>\n<task-id>aaa111</task-id>\n<status>completed</status>\n'
                  '<result>' + FAKE_SECRET + '</result>\n</task-notification>')
        self.transcript(folder / (session + '.jsonl'), [
            {'type': 'user', 'timestamp': '2026-01-31T01:00:00.000Z', 'message': {'role': 'user', 'content': 'start'}},
            {'type': 'user', 'timestamp': '2026-01-31T01:05:00.000Z',
             'message': {'role': 'user', 'content': [{'type': 'tool_result', 'content': FAKE_SECRET}]}},
            {'type': 'user', 'timestamp': '2026-01-31T01:10:00.000Z', 'message': {'role': 'user', 'content': notice}},
        ])
        subs = folder / session / 'subagents'
        self.transcript(subs / 'agent-aaa111.jsonl', [
            {'type': 'assistant', 'timestamp': '2026-01-31T01:09:00.000Z',
             'message': {'content': [{'type': 'text', 'text': 'All release notes drafted.'}]}},
        ])
        self.write(subs / 'agent-aaa111.meta.json', json.dumps({'description': 'Draft release notes', 'model': 'model-a'}))
        self.transcript(subs / 'agent-bbb222.jsonl', [
            {'type': 'assistant', 'timestamp': '2026-01-31T01:20:00.000Z',
             'message': {'content': [{'type': 'text', 'text': 'Halfway through the\nmigration notes.'},
                                     {'type': 'tool_use', 'name': 'Bash', 'input': {'command': 'echo ' + FAKE_SECRET}}]}},
            {'type': 'user', 'timestamp': '2026-01-31T01:21:00.000Z',
             'message': {'content': [{'type': 'tool_result', 'content': FAKE_SECRET}]}},
            {'type': 'assistant', 'timestamp': '2026-01-31T01:22:00.000Z',
             'message': {'content': [{'type': 'text', 'text': "You've hit your usage limit"}]}},
        ])
        self.write(subs / 'agent-bbb222.meta.json', json.dumps({'description': 'Port migration notes', 'model': 'model-b'}))
        self.transcript(subs / 'agent-ccc333.jsonl', [
            {'type': 'assistant', 'timestamp': '2026-01-30T01:00:00.000Z',
             'message': {'content': [{'type': 'text', 'text': 'Old work from yesterday.'}]}},
        ], age_hours=5)
        return projects, session

    def test_wall_recover_lists_unfinished_sub_agents_without_tool_results(self):
        projects, session = self.wall_fixture()
        cfg = self.config(memory={'projects_root': str(projects)})
        since = datetime.fromtimestamp(time.time() - 3600).strftime('%Y-%m-%dT%H:%M')
        result = self.run_tool('wall_recover.py', session, '--config', cfg, '--since', since)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        out = result.stdout
        self.assertIn('sub-agents active since %s: 2, not completed: 1' % since, out)
        self.assertIn('- [UNFINISHED] bbb222 Port migration notes (model-b, last ', out)
        self.assertIn('1 tool calls)', out)
        self.assertIn('    last words: Halfway through the migration notes.', out)
        self.assertIn('- [completed] aaa111 Draft release notes (model-a', out)
        self.assertLess(out.index('[UNFINISHED]'), out.index('[completed]'))
        self.assertNotIn('All release notes drafted', out)
        self.assertNotIn('ccc333', out)
        self.assertNotIn('hit your', out)
        self.assertNotIn(FAKE_SECRET, out + result.stderr)

    def test_wall_recover_without_since_and_bad_input(self):
        projects, session = self.wall_fixture()
        result = self.run_tool('wall_recover.py', session, '--projects-root', projects)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('sub-agents active since start: 3, not completed: 2', result.stdout)
        self.assertNotIn(FAKE_SECRET, result.stdout + result.stderr)
        missing = self.run_tool('wall_recover.py', 'no-such-session', '--projects-root', projects)
        self.assertEqual(missing.returncode, 2)
        self.assertIn('no transcript for session no-such-session', missing.stdout)
        self.assertEqual(self.run_tool('wall_recover.py', '../*', '--projects-root', projects).returncode, 2)
        self.assertEqual(self.run_tool('wall_recover.py', session, '--projects-root', projects,
                                       '--since', 'yesterday').returncode, 2)


if __name__ == '__main__':
    unittest.main()
