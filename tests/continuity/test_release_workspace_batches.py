#!/usr/bin/env python3
"""Public full-scope budget, drift and proof-completeness regressions."""
import copy
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


REPO = Path(__file__).resolve().parents[2]
SCRIPTS = Path(os.environ.get('MUSE_TEST_SCRIPTS', str(REPO / 'skills/core/muse-commands/scripts')))


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


B = load('batches_test', 'muse-workspace-batches.py')
L = load('legacy_test', 'muse-workspace.py')


class WorkspaceBatchesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.git('init', '-q')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'user.name', 'MUSE Fixture')
        (self.root / 'tracked').write_text('baseline\n')
        self.git('add', 'tracked')
        self.git('commit', '-qm', 'fixture')
        self.binding = {'checkpoint_sha256': 'a' * 64,
                        'scope_file_sha256': 'b' * 64,
                        'source_revision': 'c' * 64,
                        'receiver': {'platform': 'codex', 'session_id': 'receiver'}}

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.root), *args], check=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout

    def scope(self, sizes=(10, 20)):
        files = []
        for i, size in enumerate(sizes):
            path = self.root / ('part-%03d.bin' % i)
            path.write_bytes(bytes([i % 255]) * size)
            files.append(str(path))
        files.append(str(self.root / 'missing'))
        return {'schema_version': 1, 'workspace': str(self.root), 'files': files,
                'excluded_work': 'Only declared fixture files',
                'authorization_ref': 'isolated-test-fixture'}

    def scan(self, scope):
        return B.snapshot(str(self.root), scope=scope, binding=self.binding)

    def test_large_scope_full_coverage_and_legacy_limit_unchanged(self):
        scope = self.scope((4 * 1024 * 1024,) * 5)
        legacy = L.snapshot(str(self.root), scope=scope)
        self.assertEqual(legacy['content_coverage'], 'PARTIAL')
        self.assertIn('CONTENT_SIZE_LIMIT', legacy['issues'])
        actual = self.scan(scope)
        self.assertEqual(actual['content_coverage'], 'COMPLETE', actual)
        self.assertEqual(actual['content_paths'], 6)
        self.assertEqual(actual['content_bytes'], 20 * 1024 * 1024)
        self.assertEqual(actual['passes'], 2)
        self.assertTrue(all(p['bytes'] <= B.MAX_BATCH for p in actual['batches']))
        covered = [name for p in actual['batches'] for name in p['paths']]
        self.assertEqual(covered, sorted(scope['files']))
        self.assertEqual(actual['sha256'], self.scan(scope)['sha256'])
        self.assertEqual(L.MAX_TOTAL, 16 * 1024 * 1024)

    def test_small_scope_and_declared_absence(self):
        actual = self.scan(self.scope())
        self.assertEqual(actual['content_coverage'], 'COMPLETE', actual)
        self.assertEqual(actual['content_paths'], 3)
        self.assertEqual(actual['absent_paths'], [str(self.root / 'missing')])

    def test_invalid_scopes_reject_without_complete(self):
        scope = self.scope()
        candidates = []
        duplicate = copy.deepcopy(scope)
        duplicate['files'].append(duplicate['files'][0])
        candidates.append(duplicate)
        relative = copy.deepcopy(scope)
        relative['files'][0] = 'relative.bin'
        candidates.append(relative)
        many = copy.deepcopy(scope)
        many['files'] = [str(self.root / str(i)) for i in range(3001)]
        candidates.append(many)
        for candidate in candidates:
            with self.subTest(candidate=candidate['files'][0]):
                self.assertEqual(self.scan(candidate)['content_coverage'], 'PARTIAL')

    def test_file_larger_than_limit_rejects(self):
        actual = self.scan(self.scope((B.MAX_FILE + 1,)))
        self.assertEqual(actual['content_coverage'], 'PARTIAL')
        self.assertIn('FILE_SIZE_LIMIT', actual['issues'])

    def test_growth_cannot_exceed_actual_batch_read_budget(self):
        scope = self.scope((4 * 1024 * 1024,) * 2)
        original = B.LEGACY.snapshot
        first = True
        def grow(*args, **kwargs):
            nonlocal first
            if first:
                first = False
                Path(scope['files'][0]).write_bytes(b'x' * (5 * 1024 * 1024))
            return original(*args, **kwargs)
        with patch.object(B.LEGACY, 'snapshot', side_effect=grow):
            actual = self.scan(scope)
        self.assertEqual(actual['content_coverage'], 'PARTIAL')
        self.assertTrue(any('BATCH_READ_INCOMPLETE:CONTENT_SIZE_LIMIT' in issue
                            for issue in actual['issues']), actual['issues'])

    def check_actual_read_growth(self, timing):
        scope = self.scope((4 * 1024 * 1024,) * 2)
        growing = scope['files'][1]
        original_open, original_fdopen = os.open, os.fdopen
        tracked = {}
        observed = {'bytes': 0, 'grew': False}

        def grow():
            if not observed['grew']:
                observed['grew'] = True
                with Path(growing).open('ab') as stream:
                    stream.write(b'x' * 65536)

        def open_counted(path, flags, *args, **kwargs):
            if str(path) == growing and timing == 'before_open':
                grow()
            fd = original_open(path, flags, *args, **kwargs)
            if str(path) in scope['files']:
                tracked[fd] = str(path)
            return fd

        class CountedStream:
            def __init__(self, stream, fd, filename):
                self.stream, self.fd, self.filename = stream, fd, filename

            def __enter__(self):
                self.stream.__enter__()
                return self

            def __exit__(self, *args):
                tracked.pop(self.fd, None)
                return self.stream.__exit__(*args)

            def fileno(self):
                return self.stream.fileno()

            def read(self, count=-1):
                if self.filename == growing and timing == 'during_read':
                    grow()
                data = self.stream.read(count)
                observed['bytes'] += len(data)
                return data

        def fdopen_counted(fd, *args, **kwargs):
            stream = original_fdopen(fd, *args, **kwargs)
            if fd in tracked:
                return CountedStream(stream, fd, tracked[fd])
            return stream

        with patch.object(os, 'open', side_effect=open_counted), \
                patch.object(os, 'fdopen', side_effect=fdopen_counted):
            result = self.scan(scope)
        self.assertTrue(observed['grew'])
        self.assertEqual(result['content_coverage'], 'PARTIAL', result)
        self.assertLessEqual(observed['bytes'], B.MAX_BATCH)

    def test_growth_after_lstat_before_open_never_overreads_batch(self):
        self.check_actual_read_growth('before_open')

    def test_growth_during_read_never_overreads_batch(self):
        self.check_actual_read_growth('during_read')

    def test_symlink_leaf_parent_and_directory_reject(self):
        scope = self.scope()
        target = Path(scope['files'][0])
        link = self.root / 'link'
        link.symlink_to(target)
        parent = self.root / 'linked-parent'
        parent.symlink_to(self.root, target_is_directory=True)
        for name in (str(link), str(parent / target.name), str(self.root)):
            with self.subTest(path=name):
                scope['files'] = [name]
                self.assertEqual(self.scan(scope)['content_coverage'], 'PARTIAL')

    def test_unreadable_file_rejects(self):
        scope = self.scope((10,))
        path = Path(scope['files'][0])
        path.chmod(0)
        try:
            self.assertEqual(self.scan(scope)['content_coverage'], 'PARTIAL')
        finally:
            path.chmod(0o600)

    def mutate_after_first_batch(self, action):
        original = B.LEGACY.snapshot
        count = 0
        def wrapped(*args, **kwargs):
            nonlocal count
            result = original(*args, **kwargs)
            count += 1
            if count == 1:
                action()
            return result
        return patch.object(B.LEGACY, 'snapshot', side_effect=wrapped)

    def test_same_size_edit_after_scanned_batch_rejects(self):
        scope = self.scope((4 * 1024 * 1024,) * 3)
        path = Path(sorted(scope['files'])[1])
        with self.mutate_after_first_batch(lambda: path.write_bytes(b'x' * path.stat().st_size)):
            actual = self.scan(scope)
        self.assertEqual(actual['content_coverage'], 'PARTIAL', actual)

    def test_absence_appearing_during_scan_rejects(self):
        scope = self.scope()
        with self.mutate_after_first_batch(lambda: Path(scope['files'][-1]).write_text('new')):
            actual = self.scan(scope)
        self.assertEqual(actual['content_coverage'], 'PARTIAL', actual)

    def test_git_index_or_branch_drift_rejects(self):
        for kind in ('index', 'branch'):
            scope = self.scope()
            def mutate():
                if kind == 'index':
                    (self.root / 'tracked').write_text('changed\n')
                    self.git('add', 'tracked')
                else:
                    self.git('checkout', '-qb', 'changed-branch')
            with self.subTest(kind=kind), self.mutate_after_first_batch(mutate):
                self.assertEqual(self.scan(scope)['content_coverage'], 'PARTIAL')

    def test_interruption_propagates_without_complete(self):
        scope = self.scope()
        with patch.object(B.LEGACY, 'snapshot', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.scan(scope)

    def test_every_batch_is_read_in_both_passes(self):
        scope = self.scope((4 * 1024 * 1024,) * 3)
        with patch.object(B.LEGACY, 'snapshot', wraps=B.LEGACY.snapshot) as reader:
            actual = self.scan(scope)
        self.assertEqual(actual['content_coverage'], 'COMPLETE', actual)
        expected = [batch['paths'] for batch in actual['batches']] * 2
        observed = [call[1]['scope']['files'] for call in reader.call_args_list]
        self.assertEqual(observed, expected)

    def test_second_content_pass_detects_drift_with_metadata_signal_held_constant(self):
        scope = self.scope()
        names = sorted(scope['files'])
        original_metadata = B._metadata
        pinned = original_metadata(names)
        original_reader = B.LEGACY.snapshot
        count = 0
        def read(*args, **kwargs):
            nonlocal count
            count += 1
            if count == 2:
                Path(scope['files'][0]).write_bytes(b'x' * 10)
            return original_reader(*args, **kwargs)
        def metadata(paths):
            return pinned if paths == names else original_metadata(paths)
        with patch.object(B.LEGACY, 'snapshot', side_effect=read), \
                patch.object(B, '_metadata', side_effect=metadata):
            actual = self.scan(scope)
        self.assertEqual(count, 2)
        self.assertEqual(actual['content_coverage'], 'PARTIAL')
        self.assertIn('CONTENT_CHANGED_BETWEEN_PASSES', actual['issues'])

    def test_proof_aggregation_rejects_tampering(self):
        scope = self.scope((4 * 1024 * 1024,) * 3)
        result = self.scan(scope)
        self.assertEqual(result['content_coverage'], 'COMPLETE', result)
        proofs = result['batches']
        cases = [proofs[:-1], proofs + proofs[:1], list(reversed(proofs))]
        for key, value in [('protocol', 'legacy-v1'), ('plan_sha256', '0' * 64),
                           ('binding_sha256', '0' * 64), ('git_sha256', '0' * 64),
                           ('paths', []), ('bytes', B.MAX_BATCH + 1)]:
            changed = copy.deepcopy(proofs)
            changed[0][key] = value
            cases.append(changed)
        for value in (None, 'not-a-content-hash'):
            changed = copy.deepcopy(proofs)
            if value is None:
                del changed[0]['content_sha256']
            else:
                changed[0]['content_sha256'] = value
            changed[0]['sha256'] = B.digest({k: v for k, v in changed[0].items() if k != 'sha256'})
            cases.append(changed)
        for i, changed in enumerate(cases):
            with self.subTest(case=i), self.assertRaises(ValueError):
                B.aggregate(result['plan'], changed, self.binding, result['git'])


if __name__ == '__main__':
    unittest.main()
