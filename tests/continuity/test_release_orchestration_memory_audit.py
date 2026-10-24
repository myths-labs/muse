#!/usr/bin/env python3
"""Synthetic regressions for skills/core/muse-orchestration/scripts/memory_audit.py.

Every test builds fake memory dirs, a fake project and a fake HOME inside a temporary
directory and runs the tool as a subprocess with ``python -I``. Nothing reads or writes
the real ~/.claude, and no key-shaped literal appears in this file (samples are built at
run time).
"""
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / 'skills/core/muse-orchestration/scripts/memory_audit.py'
HUB = '-path-to-alpha'
APP = '-path-to-beta'
GAMMA = '-path-to-gamma'
DELTA = '-path-to-delta'


class MemoryAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='muse-memory-audit-'))
        self.addCleanup(shutil.rmtree, str(self.tmp), True)
        self.home = self.tmp / 'home'
        self.projects = self.home / '.claude' / 'projects'
        self.project = self.tmp / 'project'
        self.elsewhere = self.tmp / 'elsewhere'
        for folder in (self.projects, self.project / '.muse', self.elsewhere):
            folder.mkdir(parents=True)
        # a clock two minutes ahead keeps every fixture file older than the block the tool writes
        stamp = datetime.datetime.now() + datetime.timedelta(minutes=2)
        self.now = stamp.strftime('%Y-%m-%d %H:%M')
        self.today = stamp.date()
        self.config_path = self.project / '.muse' / 'orchestration.json'

    # ------------------------------------------------------------ fixture
    def write(self, path, content):
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_bytes(content.encode('utf-8'))
        return path

    def memory(self, name):
        return self.projects / name / 'memory'

    def write_config(self, hub=HUB, owner=True):
        config = {
            'schema_version': 1,
            'owner': {'name': 'Owner', 'decision_words': ['decided', 'approved', 'go with', '定', '按建议', '同意']},
            'memory': {
                'projects_root': str(self.projects),
                'hub': hub,
                'labels': {HUB: 'ALPHA', APP: 'BETA'},
                'watch_terms': [{'name': 'ExampleVendor', 'pattern': 'examplevendor'}],
                'index_max_lines': 200,
                'index_max_chars': 25000,
                'daily_projects': [{'name': 'app', 'root': 'app'}],
                'recall': 'tools/recall.py',
            },
            'checkpoints': {'files': ['docs/OPEN_THREADS.md'], 'globs': []},
            'vault': {'root': 'vault', 'freshness_hours': 24},
        }
        if not owner:
            del config['owner']
        self.write(self.config_path, json.dumps(config, indent=1, ensure_ascii=False))

    def build_fixture(self, hub=HUB, owner=True):
        self.write(self.memory(HUB) / 'MEMORY.md',
                   '# Memory Index\n\n'
                   '- [Export format decision](decision-export-format.md) — Owner chose ExampleVendor for batch export\n'
                   '- [Style notes](style-notes.md) — plain words, short lines\n')
        self.write(self.memory(HUB) / 'decision-export-format.md',
                   '---\nname: export format\ndescription: Owner chose ExampleVendor for batch export\n---\n'
                   'Owner decided to use ExampleVendor for the batch export pipeline.\n')
        self.write(self.memory(HUB) / 'style-notes.md', 'Keep lines short.\n')
        # no blank line after the heading: --unsync must still restore it exactly
        self.write(self.memory(APP) / 'MEMORY.md',
                   '# Memory Index\n'
                   '- [Vendor comparison](vendor-comparison.md) — ExampleVendor vs OtherVendor on latency\n')
        self.write(self.memory(APP) / 'vendor-comparison.md',
                   '---\ndescription: ExampleVendor vs OtherVendor on latency\n---\nExampleVendor beats OtherVendor.\n')
        today = self.today.isoformat()
        self.write(self.project / 'docs' / 'OPEN_THREADS.md',
                   '# Open threads\n\n## %s\n'
                   '- Owner decided: use ExampleVendor for the 「batch export pipeline」\n'
                   '- waiting for Owner to decide on the 「color theme refresh」\n' % today)
        self.write(self.project / 'app' / 'memory' / (today + '.md'), '# Today\n')
        self.write(self.project / 'tools' / 'recall.py', '# stand-in recall tool for this test\n')
        self.write(self.project / 'vault' / 'note.md', 'vault note\n')
        self.write_config(hub=hub, owner=owner)

    # ------------------------------------------------------------ running
    def run_audit(self, *args, **options):
        env = dict((k, v) for k, v in os.environ.items() if not k.startswith(('MUSE_', 'GIT_')))
        env['HOME'] = str(self.home)
        cmd = [sys.executable, '-I', str(SCRIPT)]
        if options.get('config', True):
            cmd += ['--config', str(self.config_path)]
        if options.get('projects', True):
            cmd += ['--projects-root', str(self.projects)]
        cmd += ['--now', self.now] + list(args)
        proc = subprocess.run(cmd, cwd=str(self.elsewhere), env=env, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, encoding='utf-8', timeout=120)
        self.assertNotIn('Traceback', proc.stderr + proc.stdout, proc.stderr + proc.stdout)
        return proc

    def audit_json(self, **options):
        proc = self.run_audit('--json', **options)
        return proc, json.loads(proc.stdout)

    @staticmethod
    def statuses(data):
        return dict((check['id'], check['status']) for check in data['checks'])

    @staticmethod
    def check(data, number):
        return [c for c in data['checks'] if c['id'] == number][0]

    def index_bytes(self, *names):
        return dict((n, (self.memory(n) / 'MEMORY.md').read_bytes()) for n in names)

    # ------------------------------------------------------------ tests
    def test_green_after_sync(self):
        self.build_fixture()
        sync = self.run_audit('--sync')
        self.assertEqual(sync.returncode, 0, sync.stdout)
        self.assertIn('RESULT: GREEN', sync.stdout)
        proc, data = self.audit_json()
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertEqual(data['result'], 'GREEN')
        self.assertEqual(self.statuses(data), dict((n, 'PASS') for n in range(1, 12)), proc.stdout)
        hub_index = (self.memory(HUB) / 'MEMORY.md').read_text(encoding='utf-8')
        self.assertIn('[BETA:vendor-comparison](', hub_index)
        self.assertIn('ExampleVendor→', hub_index)
        cross = (self.project / '.muse' / 'memory-cross-index.md').read_text(encoding='utf-8')
        self.assertIn('## ALPHA', cross)
        self.assertIn('vendor-comparison', cross)

    def test_broken_index_link_is_red(self):
        self.build_fixture()
        self.assertEqual(self.run_audit('--sync').returncode, 0)
        with open(str(self.memory(APP) / 'MEMORY.md'), 'a', encoding='utf-8') as fh:
            fh.write('- [Gone](gone-note.md) — removed long ago\n')
        text = self.run_audit()
        self.assertEqual(text.returncode, 1, text.stdout)
        self.assertIn('RESULT: RED', text.stdout)
        _, data = self.audit_json()
        self.assertEqual(self.statuses(data)[2], 'FAIL')
        self.assertTrue(any('BETA: index links a missing file: gone-note.md' in d
                            for d in self.check(data, 2)['details']), self.check(data, 2))

    def test_index_over_line_limit_is_red(self):
        self.build_fixture()
        self.assertEqual(self.run_audit('--sync').returncode, 0)
        with open(str(self.memory(HUB) / 'MEMORY.md'), 'a', encoding='utf-8') as fh:
            fh.write(''.join('- short note %d\n' % i for i in range(210)))
        proc, data = self.audit_json()
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(data['result'], 'RED')
        details = self.check(data, 2)['details']
        self.assertTrue(any(d.startswith('ALPHA: index is ') and 'over the 200-line' in d for d in details), details)

    def test_sync_then_unsync_restores_every_index_byte_for_byte(self):
        self.build_fixture()
        self.write(self.memory(GAMMA) / 'MEMORY.md', '# Notes\r\n\r\n- [a](a-note.md) — first\r\n')
        self.write(self.memory(GAMMA) / 'a-note.md', 'a\n')
        self.write(self.memory(DELTA) / 'MEMORY.md', '- [b](b-note.md) — no heading, no final newline')
        self.write(self.memory(DELTA) / 'b-note.md', 'b\n')
        names = (HUB, APP, GAMMA, DELTA)
        before = self.index_bytes(*names)
        first = self.run_audit('--sync')
        self.assertIn('RESULT: GREEN', first.stdout)
        second = self.run_audit('--sync')  # refresh in place: still exactly one block per index
        self.assertIn('RESULT: GREEN', second.stdout)
        for name, raw in self.index_bytes(*names).items():
            self.assertEqual(raw.count(b'<!-- CROSS-DIR:BEGIN'), 1, name)
            self.assertEqual(raw.count(b'<!-- CROSS-DIR:END -->'), 1, name)
            self.assertNotEqual(raw, before[name], name)
        undo = self.run_audit('--unsync')
        self.assertEqual(undo.stdout.count('block removed'), 4, undo.stdout)
        self.assertEqual(self.index_bytes(*names), before)
        again = self.run_audit('--unsync')
        self.assertEqual(again.stdout.count('no block'), 4, again.stdout)
        self.assertEqual(self.index_bytes(*names), before)

    def test_key_pattern_hit_reports_location_and_type_only(self):
        self.build_fixture()
        secret = 'sk-' + 'Zq7' * 15
        self.write(self.memory(APP) / 'vendor-comparison.md',
                   '---\ndescription: ExampleVendor vs OtherVendor on latency\n---\nold key was %s\n' % secret)
        self.write(self.memory(APP) / 'old-token.md', 'rotated\n')
        with open(str(self.memory(APP) / 'MEMORY.md'), 'a', encoding='utf-8') as fh:
            fh.write('- [Old token](old-token.md) — rotated token %s\n' % secret)
        sync = self.run_audit('--sync')
        proc, data = self.audit_json()
        text = self.run_audit()
        for output in (sync.stdout + sync.stderr, proc.stdout + proc.stderr, text.stdout + text.stderr):
            self.assertNotIn(secret, output)
            self.assertNotIn('Zq7Zq7', output)
        self.assertEqual(self.statuses(data)[11], 'FAIL')
        details = self.check(data, 11)['details']
        self.assertTrue(any(d.endswith('/-path-to-beta/memory/vendor-comparison.md:4 sk-') for d in details), details)
        # the index line moved down when --sync inserted the block, so only the file is pinned here
        self.assertTrue(any('/-path-to-beta/memory/MEMORY.md:' in d and d.endswith(' sk-') for d in details), details)
        self.assertIn('RESULT: RED', text.stdout)
        cross = (self.project / '.muse' / 'memory-cross-index.md').read_text(encoding='utf-8')
        self.assertNotIn(secret, cross)
        self.assertIn('rotated token [masked]', cross)
        for name in (HUB,):
            self.assertNotIn(secret, (self.memory(name) / 'MEMORY.md').read_text(encoding='utf-8'))

    def test_without_config_reports_unconfigured_and_refuses_to_sync(self):
        self.build_fixture()
        before = self.index_bytes(HUB, APP)
        # no --config, no --projects-root: the default projects root comes from the fake HOME
        proc = self.run_audit(config=False, projects=False)
        self.assertIn(proc.returncode, (0, 1), proc.stdout)
        self.assertIn('config none (UNCONFIGURED)', proc.stdout)
        self.assertIn('2 memory dirs under ~/.claude/projects', proc.stdout)
        for number in (4, 5, 6, 7, 8, 9):
            self.assertRegex(proc.stdout, r'\[UNCONFIGURED\] %d ' % number)
        self.assertRegex(proc.stdout, r'RESULT: (GREEN|RED) \(.*unconfigured=6\)')
        sync = self.run_audit('--sync', config=False, projects=False)
        self.assertEqual(sync.returncode, 2, sync.stdout)
        self.assertIn('UNCONFIGURED', sync.stdout)
        self.assertEqual(self.index_bytes(HUB, APP), before)
        self.assertFalse((self.project / '.muse' / 'memory-cross-index.md').exists())

    def test_hub_null_skips_hub_checks(self):
        self.build_fixture(hub=None)
        self.assertEqual(self.run_audit('--sync').returncode, 0)
        proc, data = self.audit_json()
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertEqual(self.statuses(data)[5], 'SKIP')
        self.assertIn('memory.hub is null', self.check(data, 5)['summary'])
        self.assertIn('n/a (memory.hub is null)', self.check(data, 7)['summary'])
        self.assertEqual(data['result'], 'GREEN')

    def test_owner_decision_without_memory_is_red_and_missing_owner_skips(self):
        self.build_fixture()
        yesterday = (self.today - datetime.timedelta(days=1)).isoformat()
        with open(str(self.project / 'docs' / 'OPEN_THREADS.md'), 'a', encoding='utf-8') as fh:
            fh.write('\n## %s\n'
                     '- Owner 定：改用新的发布节奏，每周一次\n'
                     '- 等 Owner 定 「夜间构建的时间表」\n'
                     '- Owner approved the 「night build schedule」 rollout\n' % yesterday)
        self.assertEqual(self.run_audit('--sync').returncode, 1)
        _, data = self.audit_json()
        backlog = self.check(data, 7)
        self.assertEqual(backlog['status'], 'FAIL', backlog)
        uncovered = [d for d in backlog['details'] if d.startswith('not in memory P1-owner-decision')]
        self.assertEqual(sorted(d.split()[5] for d in uncovered),
                         ['OPEN_THREADS.md:10', 'OPEN_THREADS.md:8'], backlog)
        self.write_config(owner=False)
        _, data = self.audit_json()
        self.assertEqual(self.statuses(data)[7], 'SKIP')
        self.assertIn('owner.name is not set', self.check(data, 7)['summary'])


if __name__ == '__main__':
    unittest.main()
