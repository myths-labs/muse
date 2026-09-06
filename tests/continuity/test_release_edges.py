#!/usr/bin/env python3
"""Bounded additional release checks in disposable retained projects."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import uuid

REPO = Path(__file__).resolve().parents[2]

class ReleaseCases(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='muse release edge cases ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.project = self.root/'project with spaces'
        self.project.mkdir()
        self.env = dict(os.environ, MUSE_PYTHON=sys.executable, PYTHONDONTWRITEBYTECODE='1')
        for key in ['DYA_ROOT','PROMETHEUS_ROOT','MUSE_OSS_ROOT','MUSE_CONFIG']:
            self.env.pop(key, None)

    def call(self, argv, stdin=None):
        result = subprocess.run(argv, input=stdin, env=self.env, capture_output=True, text=True, timeout=60)
        (self.root/('call-'+uuid.uuid4().hex[:8]+'.json')).write_text(json.dumps(dict(argv=argv,returncode=result.returncode,stdout=result.stdout,stderr=result.stderr),indent=2))
        return result

    def install(self, extra=None, stdin=None):
        return self.call(['bash',str(REPO/'scripts/install.sh'),'--core-only','--target',str(self.project),*(extra or [])],stdin)

    def test_resolved_duplicate_project_config_rejected_without_installing(self):
        folder=self.project/'.muse';folder.mkdir()
        config=folder/'config.json'
        config.write_text(json.dumps(dict(schema_version=1,role_home='home',projects={'home':'.','alias':'./'})))
        before=config.read_bytes()
        result=self.install(['--tool','codex'])
        self.assertNotEqual(result.returncode,0,'Installer accepts config that installed runtime rejects as ambiguous.')
        self.assertEqual(config.read_bytes(),before)
        self.assertFalse((self.project/'AGENTS.md').exists())

    def test_reversed_managed_markers_rejected_without_policy_rewrite(self):
        policy=self.project/'AGENTS.md'
        policy.write_text('User policy before\n<!-- MUSE CONTINUITY END -->\nKeep this user boundary.\n<!-- MUSE CONTINUITY START -->\nUser policy after\n')
        before=policy.read_bytes()
        result=self.install(['--tool','codex'])
        self.assertNotEqual(result.returncode,0,'Reversed managed markers were accepted and rewritten.')
        self.assertEqual(policy.read_bytes(),before)

    def isolated_detection(self):
        bindir=self.root/'bin';bindir.mkdir()
        for name in ['claude','codex']:
            path=bindir/name;path.write_text('#!/bin/sh\nexit 99\n');path.chmod(0o700)
        self.env['PATH']=str(bindir)+':/usr/bin:/bin:/usr/sbin:/sbin'

    def assert_installed_routes(self):
        doctor=self.project/'.agent/skills/muse-commands/scripts/muse-doctor.sh'
        self.assertTrue(doctor.is_file())
        result=self.call(['bash',str(doctor),'resume-workflow','--command','/resume strategy Lane A','--workspace',str(self.project)])
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout.strip(),str(self.project/'.agent/workflows/daily-resume.md'))
        self.assertFalse((self.project/'memory/lanes/strategy-lane-a.md').exists())

    def test_interactive_codex_installs_same_runtime(self):
        self.isolated_detection()
        result=self.install(stdin='6\n')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assert_installed_routes()

    def test_all_detected_native_clients_share_runtime_and_preserve_policy(self):
        self.isolated_detection()
        (self.project/'AGENTS.md').write_text('Keep Codex user policy.\n')
        (self.project/'CLAUDE.md').write_text('Keep Claude user policy.\n')
        result=self.install(['--tool','all'])
        self.assertEqual(result.returncode,0,result.stderr)
        self.assert_installed_routes()
        for name,marker in [('AGENTS.md','Keep Codex'),('CLAUDE.md','Keep Claude')]:
            self.assertIn(marker,(self.project/name).read_text())
        self.assertEqual((self.project/'.agents/skills/muse-commands').resolve(),(self.project/'.claude/skills/muse-commands').resolve())

    def test_damaged_rollback_backup_refuses_without_losing_current_files(self):
        (self.project/'AGENTS.md').write_text('Preserve original user policy.\n')
        result=self.install(['--tool','codex'])
        self.assertEqual(result.returncode,0,result.stderr)
        receipt_path=Path(json.loads(result.stdout)['receipt_path'])
        receipt=json.loads(receipt_path.read_text())
        def observed(rel):
            path=self.project/rel
            if path.is_symlink():return ('link',os.readlink(path))
            if not path.exists():return ('absent',)
            return ('file',hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mode&0o777)
        before={change['path']:observed(change['path']) for change in receipt['changes']}
        policy_change=next(change for change in receipt['changes'] if change['path']=='AGENTS.md')
        policy_change['before']['mode']='damaged-mode'
        receipt_path.write_text(json.dumps(receipt))
        result=self.call([sys.executable,str(REPO/'scripts/install-continuity.py'),'--rollback',str(receipt_path)])
        self.assertNotEqual(result.returncode,0)
        self.assertEqual({rel:observed(rel) for rel in before},before)

    def test_existing_private_policy_permissions_are_not_broadened(self):
        policy=self.project/'AGENTS.md';policy.write_text('Private user policy; retain permissions.\n');policy.chmod(0o600)
        result=self.install(['--tool','codex'])
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(policy.stat().st_mode&0o777,0o600)

    def test_new_command_and_ignore_integration_preserves_user_content_and_rolls_back(self):
        command=self.project/'.claude/commands/resume.md';command.parent.mkdir(parents=True)
        command.write_text('Existing user resume behavior.\n')
        ignore=self.project/'.gitignore';ignore.write_text('*.cache\n!keep.cache\n')
        result=self.install(['--tool','claude']);self.assertEqual(result.returncode,0,result.stderr)
        receipt=Path(json.loads(result.stdout)['receipt_path'])
        self.assertEqual(command.read_text(),'Existing user resume behavior.\n')
        self.assertTrue(ignore.read_text().startswith('*.cache\n!keep.cache\n'))
        self.assertIn('/.muse/installations/',ignore.read_text())
        self.assertIn('/memory/.muse-source-inbox/',ignore.read_text())
        self.assertTrue((command.parent/'save.md').is_file())
        result=self.call([sys.executable,str(REPO/'scripts/install-continuity.py'),'--rollback',str(receipt)])
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(ignore.read_text(),'*.cache\n!keep.cache\n')
        self.assertEqual(command.read_text(),'Existing user resume behavior.\n')

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ReleaseCases)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
