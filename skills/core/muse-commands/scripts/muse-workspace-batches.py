#!/usr/bin/env python3
"""Versioned, bounded full-scope evidence for a cooperative writer handoff."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess


PROTOCOL = 'full-scope-batches-v1'
MAX_FILE = 5 * 1024 * 1024
MAX_BATCH = 8 * 1024 * 1024
MAX_PATHS = 3000

_spec = importlib.util.spec_from_file_location(
    'muse_batch_legacy', Path(__file__).with_name('muse-workspace.py'))
LEGACY = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(LEGACY)


def encode(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=True) + '\n').encode()


def digest(value):
    return hashlib.sha256(encode(value)).hexdigest()


def _metadata(names):
    records = []
    for name in names:
        path = Path(name)
        for parent in path.parents:
            if parent.is_symlink():
                raise ValueError('SYMLINK_PARENT')
        try:
            info = path.lstat()
        except FileNotFoundError:
            records.append({'path': name, 'kind': 'absent', 'bytes': 0})
            continue
        if stat.S_ISLNK(info.st_mode):
            raise ValueError('SYMLINK_FILE')
        if not stat.S_ISREG(info.st_mode):
            raise ValueError('UNSUPPORTED_FILE_TYPE')
        if info.st_size > MAX_FILE:
            raise ValueError('FILE_SIZE_LIMIT')
        if not info.st_mode & 0o444:
            raise ValueError('UNREADABLE_FILE')
        records.append({'path': name, 'kind': 'file', 'bytes': info.st_size,
                        'mode': stat.S_IMODE(info.st_mode), 'device': info.st_dev,
                        'inode': info.st_ino, 'mtime_ns': info.st_mtime_ns,
                        'ctime_ns': info.st_ctime_ns})
    return records


def plan_scope(scope):
    if not isinstance(scope, dict) or not isinstance(scope.get('files'), list):
        raise ValueError('EXPLICIT_SCOPE_REQUIRED')
    names = scope['files']
    if not 1 <= len(names) <= MAX_PATHS or any(type(n) is not str for n in names):
        raise ValueError('PATH_LIMIT_OR_TYPE')
    if len(set(names)) != len(names):
        raise ValueError('DUPLICATE_SCOPE_PATH')
    for name in names:
        path = Path(name)
        if not path.is_absolute() or '..' in path.parts or os.path.normpath(name) != name:
            raise ValueError('UNSAFE_SCOPE_PATH')
    records = _metadata(sorted(names))
    batches = []
    current = {'index': 0, 'paths': [], 'bytes': 0}
    for record in records:
        if current['paths'] and current['bytes'] + record['bytes'] > MAX_BATCH:
            batches.append(current)
            current = {'index': len(batches), 'paths': [], 'bytes': 0}
        current['paths'].append(record['path'])
        current['bytes'] += record['bytes']
    batches.append(current)
    return {'protocol': PROTOCOL, 'scope_sha256': digest(scope),
            'metadata': records, 'batches': batches,
            'content_paths': len(records),
            'content_bytes': sum(r['bytes'] for r in records)}


def _index_hash(path):
    if not path.exists():
        return None
    before = _metadata([str(path)])[0]
    h = hashlib.sha256()
    count = 0
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError('UNSAFE_GIT_INDEX')
        for chunk in iter(lambda: stream.read(65536), b''):
            count += len(chunk)
            if count > MAX_FILE:
                raise ValueError('GIT_INDEX_SIZE_LIMIT')
            h.update(chunk)
    if _metadata([str(path)])[0] != before:
        raise ValueError('GIT_INDEX_CHANGED_DURING_READ')
    return h.hexdigest()


def git_state(workspace):
    def run(*args, required=True):
        result = subprocess.run(['git', '--no-optional-locks', '-C', workspace, *args],
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                timeout=10)
        if len(result.stdout) > 256 * 1024:
            raise ValueError('GIT_OUTPUT_TOO_LARGE')
        if result.returncode and required:
            raise ValueError('GIT_STATE_UNAVAILABLE')
        return result.stdout if not result.returncode else None
    root = str(Path(os.fsdecode(run('rev-parse', '--show-toplevel')).strip()).resolve())
    head = run('rev-parse', '--verify', 'HEAD', required=False)
    branch = run('symbolic-ref', '--short', '-q', 'HEAD', required=False)
    dirty = run('status', '--porcelain=v1', '-z', '--untracked-files=no')
    staged = run('diff', '--cached', '--raw', '--no-abbrev', '-z', '--no-ext-diff')
    index = Path(os.fsdecode(run('rev-parse', '--git-path', 'index')).strip())
    if not index.is_absolute():
        index = Path(workspace) / index
    return {'root': root, 'head': os.fsdecode(head).strip() if head else None,
            'branch': os.fsdecode(branch).strip() if branch else None,
            'dirty': bool(dirty), 'dirty_sha256': hashlib.sha256(dirty).hexdigest(),
            'staged_sha256': hashlib.sha256(staged).hexdigest(),
            'index_sha256': _index_hash(index)}


def aggregate(plan, proofs, binding, git):
    if plan.get('protocol') != PROTOCOL or len(proofs) != len(plan['batches']):
        raise ValueError('INCOMPLETE_BATCH_SET')
    binding_hash, git_hash, plan_hash = digest(binding), digest(git), digest(plan)
    covered = []
    for expected, proof in zip(plan['batches'], proofs):
        fixed = {'protocol': PROTOCOL, 'plan_sha256': plan_hash,
                 'binding_sha256': binding_hash, 'git_sha256': git_hash,
                 'batch_index': expected['index'], 'paths': expected['paths'],
                 'bytes': expected['bytes']}
        if set(proof) != set(fixed) | {'content_sha256', 'sha256'}:
            raise ValueError('BATCH_SCHEMA_MISMATCH')
        content_hash = proof['content_sha256']
        if not isinstance(content_hash, str) or len(content_hash) != 64 or any(
                char not in '0123456789abcdef' for char in content_hash):
            raise ValueError('BATCH_CONTENT_HASH_INVALID')
        if any(proof.get(key) != value for key, value in fixed.items()):
            raise ValueError('BATCH_BINDING_MISMATCH')
        if not 0 <= proof['bytes'] <= MAX_BATCH:
            raise ValueError('BATCH_SIZE_LIMIT')
        body = {key: value for key, value in proof.items() if key != 'sha256'}
        if proof.get('sha256') != digest(body):
            raise ValueError('BATCH_HASH_MISMATCH')
        covered.extend(proof['paths'])
    expected_names = [r['path'] for r in plan['metadata']]
    if covered != expected_names or len(set(covered)) != len(covered):
        raise ValueError('BATCH_MEMBERSHIP_MISMATCH')
    return digest(proofs)


def snapshot(workspace, scope=None, binding=None):
    result = {'status': 'UNAVAILABLE', 'workspace': workspace,
              'protocol': PROTOCOL, 'content_coverage': 'PARTIAL', 'issues': []}
    try:
        if not isinstance(binding, dict) or not binding:
            raise ValueError('RECOVERY_BINDING_REQUIRED')
        if not scope or scope.get('workspace') != workspace:
            raise ValueError('SCOPE_WORKSPACE_MISMATCH')
        git = git_state(workspace)
        plan = plan_scope(scope)
        plan_hash = digest(plan)
        previous = None
        for pass_index in range(2):
            proofs = []
            for batch in plan['batches']:
                batch_scope = dict(scope, files=batch['paths'])
                budget = {'bytes': LEGACY.MAX_TOTAL - MAX_BATCH, 'paths': 0,
                          'strict_reads': True}
                scan = LEGACY.snapshot(workspace, scope=batch_scope, budget=budget)
                if scan['status'] != 'AVAILABLE' or scan['content_coverage'] != 'COMPLETE':
                    raise ValueError('BATCH_READ_INCOMPLETE:' + ','.join(scan.get('issues', [])))
                if scan['content_paths'] != len(batch['paths']):
                    raise ValueError('BATCH_PATH_COUNT_MISMATCH')
                if scan['scope_sha256'] != digest(batch_scope):
                    raise ValueError('BATCH_SCOPE_MISMATCH')
                if any(scan.get(key) != value for key, value in git.items()
                       if key != 'index_sha256') or git_state(workspace) != git:
                    raise ValueError('GIT_CHANGED_DURING_READ')
                proof = {'protocol': PROTOCOL, 'plan_sha256': plan_hash,
                         'binding_sha256': digest(binding), 'git_sha256': digest(git),
                         'batch_index': batch['index'], 'paths': batch['paths'],
                         'bytes': batch['bytes'], 'content_sha256': scan['content_sha256']}
                proof['sha256'] = digest(proof)
                proofs.append(proof)
            combined = aggregate(plan, proofs, binding, git)
            if _metadata([r['path'] for r in plan['metadata']]) != plan['metadata']:
                raise ValueError('SCOPE_CHANGED_DURING_READ')
            if previous is not None and previous != combined:
                raise ValueError('CONTENT_CHANGED_BETWEEN_PASSES')
            previous = combined
        if git_state(workspace) != git:
            raise ValueError('GIT_CHANGED_DURING_READ')
        result.update(status='AVAILABLE', content_coverage='COMPLETE', passes=2,
                      scope_kind='explicit_files', scope_sha256=plan['scope_sha256'],
                      excluded_work=scope.get('excluded_work'), binding=binding,
                      plan_sha256=plan_hash, plan=plan, batches=proofs, git=git,
                      content_sha256=combined, content_paths=plan['content_paths'],
                      content_bytes=plan['content_bytes'],
                      absent_paths=[r['path'] for r in plan['metadata'] if r['kind'] == 'absent'],
                      **git)
    except (ValueError, OSError, subprocess.SubprocessError, KeyError, TypeError) as exc:
        result['issues'] = [str(exc) if isinstance(exc, ValueError) else type(exc).__name__]
    result['sha256'] = digest(result)
    return result
