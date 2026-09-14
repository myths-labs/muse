#!/usr/bin/env python3
"""Public batched-claim regressions with synthetic writer and source fixtures."""
import argparse
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


REPO = Path(__file__).resolve().parents[2]
SCRIPTS = Path(os.environ.get('MUSE_TEST_SCRIPTS', str(REPO / 'skills/core/muse-commands/scripts')))
PROTOCOL = 'full-scope-batches-v1'


class DailyBatchesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.home = self.root / 'home'
        self.repo = self.root / 'project'
        self.library = self.root / 'library'
        for directory in (self.home, self.repo, self.library):
            directory.mkdir()
        config = self.root / 'config.json'
        config.write_text(json.dumps(dict(schema_version=1, role_home='home',
            projects={'home': str(self.home), 'project': str(self.repo), 'library': str(self.library)})))
        excluded = {'DYA_ROOT', 'PROMETHEUS_ROOT', 'MUSE_OSS_ROOT', 'MUSE_CONFIG', 'MUSE_PROJECT_ROOT'}
        env = {k: v for k, v in os.environ.items()
               if not k.startswith('MUSE_RUNTIME_') and k not in excluded}
        env.update(MUSE_CONFIG=str(config), CODEX_THREAD_ID='fixture-receiver', PYTHONDONTWRITEBYTECODE='1')
        self.environment = patch.dict(os.environ, env, clear=True)
        self.environment.start()
        spec = importlib.util.spec_from_file_location('daily_fixture', SCRIPTS / 'muse-daily.py')
        self.daily = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = self.daily
        spec.loader.exec_module(self.daily)
        self.git('init', '-q')
        self.git('config', 'user.name', 'MUSE Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        (self.repo / 'tracked').write_text('baseline\n')
        self.git('add', 'tracked')
        self.git('commit', '-qm', 'fixture')
        sections = {name: 'Preserved ' + name for name in self.daily.STATE.REQUIRED_SECTIONS}
        sections.update({'Objective': 'Continue a large documentation worktree without dropping selected files.',
                         'Decisions': 'Keep user decisions, receipts, source evidence and explicit publication boundaries.',
                         'Open Issues': 'fixture-failure-v1 remains open; no product acceptance is implied.',
                         'Verification': 'Historical partial evidence only; no product verdict.'})
        self.payload = dict(schema_version=1, role_home='home', role='strategy', lane='B',
                            platform='codex', session_id='fixture-old-writer',
                            handoff_id='fixture-handoff-20260914', updated_at='2026-09-14T00:00:00Z',
                            workspace=str(self.repo), subject_projects=['project'],
                            branch=self.git('symbolic-ref', '--short', 'HEAD').decode().strip(),
                            head=self.git('rev-parse', 'HEAD').decode().strip(), sections=sections)
        self.checkpoint = self.home / 'memory/lanes/strategy-lane-b.md'
        self.checkpoint.parent.mkdir(parents=True)
        objects = self.daily.SOURCES.Objects(self.checkpoint)
        key = objects.put(self.daily.SOURCES.empty_manifest(self.payload))
        self.manifest_path = objects.path(key)
        sections['Artifact Manifest'] += '\n' + self.daily.SOURCES.MARKER + key
        self.checkpoint.write_text(self.daily.STATE.render_checkpoint(self.payload))
        self.before = self.checkpoint.read_bytes()
        self.scope_file = self.daily.scope_path(self.checkpoint)
        self.scope_file.parent.mkdir()
        self.scope_file.with_name('strategy-lane-b.protocol').write_text('muse-daily-v1\n')
        self.source_file = self.home / 'fixture-source.json'
        self.source_file.write_text('{"text":"Native fixture user authorizes continuation"}\n')
        self.write_scope()

    def tearDown(self):
        self.environment.stop()
        self.tmp.cleanup()

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args], check=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout

    def write_scope(self, large=False):
        files = []
        for i in range(5 if large else 2):
            path = self.repo / ('part-%d.bin' % i)
            path.write_bytes(bytes([i]) * (4 * 1024 * 1024 if large else 10))
            files.append(str(path))
        files.append(str(self.repo / 'missing'))
        self.scope = dict(schema_version=1, workspace=str(self.repo), files=files,
                          excluded_work='Fixture scope only', authorization_ref='fixture-original-writer')
        self.scope_file.write_text(json.dumps(self.scope, sort_keys=True) + '\n')

    def prepare(self, protocol=PROTOCOL):
        return self.daily.prepare(argparse.Namespace(command='/resume strategy Lane B',
                                  workspace=str(self.repo), snapshot_protocol=protocol))

    def claim_input(self, receiver='fixture-receiver', protocol=PROTOCOL):
        with patch.dict(os.environ, CODEX_THREAD_ID=receiver):
            prepared = self.prepare(protocol)
        self.assertEqual(prepared['git']['content_coverage'], 'COMPLETE', prepared['git'])
        parsed = self.daily.INC.parse_exact(self.before)
        expected = {k: parsed[k] for k in ('platform', 'session_id', 'handoff_id')}
        expected['sha256'] = self.daily.INC.digest(self.before)
        data = dict(schema_version=1, command='/resume strategy Lane B', workspace=str(self.repo),
                    expected=expected, source=dict(path=str(self.source_file),
                    sha256=self.daily.INC.digest(self.source_file.read_bytes()), coverage='partial'),
                    intent='continue_this_lane', review=dict(checkpoint_sha256=expected['sha256'],
                    git_sha256=prepared['git']['sha256'], source_tail='verified',
                    allowed_work='Continue fixture Lane B with all failures and constraints preserved.',
                    authorization_ref='Isolated native-style fixture; no live authorization.'))
        path = self.home / (receiver + '-claim.json')
        path.write_text(json.dumps(data) + '\n')
        return path

    def test_large_scope_explicit_claim_preserves_semantics_and_revokes_old_writer(self):
        self.write_scope(large=True)
        legacy = self.prepare('legacy-v1')
        self.assertEqual(legacy['git']['content_coverage'], 'PARTIAL')
        scope_before = self.scope_file.read_bytes()
        manifest_before = self.manifest_path.read_bytes()
        receipt = self.daily.claim(self.claim_input(), PROTOCOL)
        self.assertEqual(receipt['status'], 'WRITER_CLAIMED')
        after = self.daily.INC.parse_exact(self.checkpoint.read_bytes())
        before = self.daily.INC.parse_exact(self.before)
        for key in before:
            if key not in ('sections', 'session_id', 'updated_at'):
                self.assertEqual(after[key], before[key], key)
        for key, text in before['sections'].items():
            if key == 'Verification':
                self.assertTrue(after['sections'][key].startswith(text + '\n\nWriter transition'))
                self.assertIn(PROTOCOL, after['sections'][key])
            else:
                self.assertEqual(after['sections'][key], text, key)
        self.assertEqual(after['session_id'], 'fixture-receiver')
        self.assertEqual(self.scope_file.read_bytes(), scope_before)
        self.assertEqual(self.manifest_path.read_bytes(), manifest_before)
        archive = Path(receipt['receipt_dir'])
        self.assertEqual((archive / 'before.md').read_bytes(), self.before)
        self.assertEqual((archive / 'after.md').read_bytes(), self.checkpoint.read_bytes())
        with patch.dict(os.environ, CODEX_THREAD_ID='fixture-old-writer'):
            with self.assertRaisesRegex(ValueError, 'WRITER_MISMATCH'):
                self.daily.STATE.require_daily_writer(self.daily.INC.payload_from(after))

    def test_legacy_default_matches_original_and_still_claims_small_scope(self):
        explicit = self.daily.git_snapshot(str(self.repo), self.checkpoint, 'legacy-v1')
        default = self.daily.git_snapshot(str(self.repo), self.checkpoint)
        self.assertEqual(explicit, default)
        self.assertEqual(default, self.daily.WORKSPACE.snapshot(str(self.repo), scope=self.scope))
        receipt = self.daily.claim(self.claim_input(protocol='legacy-v1'))
        self.assertEqual(receipt['status'], 'WRITER_CLAIMED')

    def test_stale_content_review_rejects_without_write(self):
        request = self.claim_input()
        Path(self.scope['files'][0]).write_bytes(b'x' * 10)
        with self.assertRaisesRegex(ValueError, 'GIT_DRIFT_OR_UNAVAILABLE'):
            self.daily.claim(request, PROTOCOL)
        self.assertEqual(self.checkpoint.read_bytes(), self.before)

    def test_unknown_protocol_cannot_fallback(self):
        with self.assertRaisesRegex(ValueError, 'UNKNOWN_SNAPSHOT_PROTOCOL'):
            self.daily.git_snapshot(str(self.repo), self.checkpoint, 'unknown')

    def run_claim_mutation(self, action, error):
        request = self.claim_input()
        original = self.daily.git_snapshot
        def changed(*args, **kwargs):
            result = original(*args, **kwargs)
            action()
            return result
        with patch.object(self.daily, 'git_snapshot', side_effect=changed):
            with self.assertRaisesRegex(ValueError, error):
                self.daily.claim(request, PROTOCOL)

    def test_scope_change_after_scan_rejects(self):
        def mutate():
            changed = dict(self.scope, authorization_ref='changed')
            self.scope_file.write_text(json.dumps(changed) + '\n')
        self.run_claim_mutation(mutate, 'SCOPE_CHANGED_DURING_CLAIM')
        self.assertEqual(self.checkpoint.read_bytes(), self.before)

    def test_protocol_marker_change_after_scan_rejects(self):
        marker = self.scope_file.with_name('strategy-lane-b.protocol')
        self.run_claim_mutation(lambda: marker.write_text('muse-daily-v1-legacy-workflow\n'),
                                'PROTOCOL_CHANGED_DURING_CLAIM')
        self.assertEqual(self.checkpoint.read_bytes(), self.before)

    def test_receiver_can_save_and_original_writer_cannot(self):
        self.daily.claim(self.claim_input(), PROTOCOL)
        parsed = self.daily.INC.parse_exact(self.checkpoint.read_bytes())
        expected = {k: parsed[k] for k in ('platform', 'session_id', 'handoff_id')}
        expected['sha256'] = self.daily.INC.digest(self.checkpoint.read_bytes())
        delta = dict(schema_version=1, command='/resume strategy Lane B', workspace=str(self.repo),
                     expected=expected, source=dict(path=str(self.source_file),
                     sha256=self.daily.INC.digest(self.source_file.read_bytes()), coverage='partial'),
                     append={'Completed': 'Receiver fixture stage saved; continue full objective.'}, replace={})
        path = self.home / 'fixture-save.json'
        path.write_text(json.dumps(delta) + '\n')
        before_save = self.checkpoint.read_bytes()
        with patch.dict(os.environ, CODEX_THREAD_ID='fixture-old-writer'):
            with self.assertRaisesRegex(ValueError, 'WRITER_MISMATCH'):
                self.daily.save(path)
        self.assertEqual(self.checkpoint.read_bytes(), before_save)
        self.assertEqual(self.daily.save(path)['status'], 'SAVED')
        self.assertIn('Receiver fixture stage saved', self.checkpoint.read_text())

    def test_source_file_change_after_scan_rejects(self):
        self.run_claim_mutation(lambda: self.source_file.write_text('changed\n'),
                                'SOURCE_CHANGED_DURING_CLAIM')
        self.assertEqual(self.checkpoint.read_bytes(), self.before)

    def test_source_graph_corruption_after_scan_rejects(self):
        self.run_claim_mutation(lambda: self.manifest_path.write_text('{}\n'),
                                'SOURCE_OBJECT_CORRUPT')
        self.assertEqual(self.checkpoint.read_bytes(), self.before)

    def test_checkpoint_change_after_scan_rejects_without_overwrite(self):
        changed = self.before.replace(b'fixture-failure-v1', b'fixture-failure-v2')
        self.run_claim_mutation(lambda: self.checkpoint.write_bytes(changed), 'STALE_VERSION')
        self.assertEqual(self.checkpoint.read_bytes(), changed)

    def test_content_change_after_scan_rejects(self):
        self.run_claim_mutation(lambda: Path(self.scope['files'][0]).write_bytes(b'x' * 10),
                                'SCOPE_CONTENT_CHANGED_DURING_CLAIM')
        self.assertEqual(self.checkpoint.read_bytes(), self.before)

    def test_interrupted_scan_never_publishes(self):
        request = self.claim_input()
        with patch.object(self.daily, 'git_snapshot', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.daily.claim(request, PROTOCOL)
        self.assertEqual(self.checkpoint.read_bytes(), self.before)
        self.assertFalse((self.checkpoint.parent / '.incremental').exists())

    def test_review_bound_to_native_receiver(self):
        request = self.claim_input(receiver='different-fixture-receiver')
        with self.assertRaisesRegex(ValueError, 'GIT_DRIFT_OR_UNAVAILABLE'):
            self.daily.claim(request, PROTOCOL)
        self.assertEqual(self.checkpoint.read_bytes(), self.before)

    def test_concurrent_receivers_only_one_claims_expected_version(self):
        requests = {receiver: self.claim_input(receiver=receiver)
                    for receiver in ('fixture-receiver-a', 'fixture-receiver-b')}
        running = []
        for receiver, request in requests.items():
            env = dict(os.environ, CODEX_THREAD_ID=receiver)
            command = [sys.executable, str(SCRIPTS / 'muse-daily.py'),
                       'claim-lane', '--input', str(request), '--snapshot-protocol', PROTOCOL]
            running.append(subprocess.Popen(command, env=env, stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE, text=True))
        results = [(process, process.communicate(timeout=20)) for process in running]
        self.assertEqual(sorted(p.returncode for p, _ in results), [0, 2], results)
        winners = [json.loads(output[0]) for p, output in results if p.returncode == 0]
        self.assertEqual(winners[0]['status'], 'WRITER_CLAIMED')
        self.assertIn('STALE_VERSION', ''.join(output[1] for p, output in results if p.returncode))
        parsed = self.daily.INC.parse_exact(self.checkpoint.read_bytes())
        self.assertEqual(parsed['session_id'], winners[0]['writer']['session_id'])
        self.assertEqual(parsed['handoff_id'], self.payload['handoff_id'])


if __name__ == '__main__':
    unittest.main()
