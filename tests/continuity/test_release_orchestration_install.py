#!/usr/bin/env python3
"""Installer and command-routing checks for the multi-lane orchestration layer.

All writes go to temporary projects created from a copy of this distribution.
Run: python3 -m unittest discover -s tests/continuity -p test_release_orchestration_install.py -v
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
ORCHESTRATION = {'handoff': 'handoff', 'away': 'away', '托': 'away', 'back': 'back', '回': 'back'}


class OrchestrationInstallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = tempfile.TemporaryDirectory(prefix='muse orchestration distribution ')
        cls.distribution = Path(cls.archive.name).resolve() / 'release source'
        shutil.copytree(REPO, cls.distribution, symlinks=True,
                        ignore=shutil.ignore_patterns('.git', '__pycache__', 'node_modules'))

    @classmethod
    def tearDownClass(cls):
        cls.archive.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='muse orchestration install ')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.project = self.base / 'project with spaces'
        self.env = {k: v for k, v in os.environ.items() if not k.startswith('MUSE_')
                    and k not in {'CODEX_THREAD_ID', 'CLAUDE_SESSION_ID', 'CLAUDE_ENV_FILE'}}
        self.env['PATH'] = str(Path(sys.executable).parent) + os.pathsep + self.env.get('PATH', '')
        self.env['PYTHONDONTWRITEBYTECODE'] = '1'

    def run_cli(self, args, ok=True, cwd=None):
        proc = subprocess.run(args, cwd=str(cwd or self.base), env=self.env, universal_newlines=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
        if ok:
            self.assertEqual(proc.returncode, 0, proc.stdout[-1500:] + proc.stderr[-1500:])
        return proc

    def install(self, tool='claude'):
        return self.run_cli(['bash', str(self.distribution / 'scripts/install.sh'), '--tool', tool,
                             '--target', str(self.project)])

    def receipt(self, proc):
        decoder = json.JSONDecoder()
        for index in range(len(proc.stdout) - 1, -1, -1):
            if proc.stdout[index] != '{':
                continue
            try:
                value, _ = decoder.raw_decode(proc.stdout[index:])
            except ValueError:
                continue
            if isinstance(value, dict) and isinstance(value.get('receipt_path'), str):
                return value['receipt_path']
        self.fail('no receipt: ' + proc.stdout[-800:])

    def doctor(self, *args):
        return self.run_cli(['bash', str(self.project / '.agent/skills/muse-commands/scripts/muse-doctor.sh'), *args])

    def test_claude_install_adds_commands_skill_and_workflows(self):
        self.install('claude')
        commands = self.project / '.claude/commands'
        for name, workflow in ORCHESTRATION.items():
            text = (commands / (name + '.md')).read_text(encoding='utf-8')
            self.assertIn('.agent/workflows/' + workflow + '.md', text, name)
            self.assertIn('muse-orchestration/SKILL.md', text, name)
        boot = (commands / 'boot.md').read_text(encoding='utf-8')
        self.assertIn('Execute MUSE /resume $ARGUMENTS', boot)
        skill = self.project / '.agent/skills/core/muse-orchestration'
        for relative in ['SKILL.md', 'scripts/orchestration_config.py', 'scripts/recall.py',
                         'templates/orchestration.example.json', 'references/ACCOUNT_RELAY.md']:
            self.assertTrue((skill / relative).is_file(), relative)
        self.assertTrue((self.project / '.claude/skills/muse-orchestration').is_symlink())
        for name in ('handoff', 'away', 'back'):
            self.assertTrue((self.project / '.agent/workflows' / (name + '.md')).is_file(), name)
        self.assertIn('muse-orchestration/SKILL.md', (self.project / 'CLAUDE.md').read_text(encoding='utf-8'))
        self.assertIn('/.muse/memory-cross-index.md', (self.project / '.gitignore').read_text(encoding='utf-8').splitlines())

    def test_user_command_with_same_name_is_preserved_and_rollback_restores(self):
        own = self.project / '.claude/commands/handoff.md'
        own.parent.mkdir(parents=True)
        own.write_text('My own handoff command.\n', encoding='utf-8')
        receipt = self.receipt(self.install('claude'))
        self.assertEqual(own.read_text(encoding='utf-8'), 'My own handoff command.\n')
        self.assertTrue((own.parent / 'away.md').is_file())
        self.run_cli([sys.executable, str(self.distribution / 'scripts/install-continuity.py'), '--rollback', receipt])
        self.assertEqual(own.read_text(encoding='utf-8'), 'My own handoff command.\n')
        self.assertFalse((own.parent / 'away.md').exists())
        self.assertFalse((own.parent / '托.md').exists())

    def test_resolve_maps_commands_and_aliases_for_every_client(self):
        self.install('codex')
        expected = {'/handoff save': 'handoff.md', '/away': 'away.md', '/托': 'away.md',
                    '/back': 'back.md', '/回': 'back.md', '/boot': 'resume.md'}
        for command, workflow in expected.items():
            route = self.doctor('resolve', command, str(self.project)).stdout.strip()
            self.assertTrue(route.endswith('.agent/workflows/' + workflow), (command, route))
        doctor = self.run_cli(['bash', str(self.project / '.agent/skills/muse-commands/scripts/muse-doctor.sh'),
                               'doctor', str(self.project)], ok=False)
        report = json.loads(doctor.stdout)
        # Only the new commands are asserted here; an unrelated pre-existing gap stays visible in `missing`.
        self.assertFalse([m for m in report['missing'] if Path(m).stem in ('handoff', 'away', 'back')], report)
        refused = self.run_cli(['bash', str(self.project / '.agent/skills/muse-commands/scripts/muse-doctor.sh'),
                                'resolve', '/not-a-command', str(self.project)], ok=False)
        self.assertNotEqual(refused.returncode, 0)

    def test_installed_config_loader_reads_example_lanes(self):
        self.install('codex')
        skill = self.project / '.agent/skills/core/muse-orchestration'
        (self.project / '.muse').mkdir(exist_ok=True)
        shutil.copy(str(skill / 'templates/orchestration.example.json'), str(self.project / '.muse/orchestration.json'))
        out = self.run_cli([sys.executable, '-I', str(skill / 'scripts/orchestration_config.py')], cwd=self.project)
        report = json.loads(out.stdout)
        self.assertEqual(report['status'], 'PASS')
        self.assertEqual(report['lanes'], ['orchestrator', 'build', 'verify'])
        self.assertIsNone(report['vault'])

    def test_release_check_covers_orchestration_files(self):
        out = self.run_cli([sys.executable, str(self.distribution / 'scripts/check-release.py')])
        self.assertEqual(json.loads(out.stdout)['status'], 'PASS')
        leaked = self.distribution / 'skills/core/muse-orchestration/references/LEAK.md'
        leaked.write_text('see /Volumes/External/notes\n', encoding='utf-8')
        try:
            out = self.run_cli([sys.executable, str(self.distribution / 'scripts/check-release.py')], ok=False)
            self.assertIn('AUTHOR_PATH: skills/core/muse-orchestration/references/LEAK.md', json.loads(out.stdout)['errors'])
        finally:
            leaked.unlink()


if __name__ == '__main__':
    unittest.main()
