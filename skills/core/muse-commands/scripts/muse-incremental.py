#!/usr/bin/env python3
"""Opt-in, same-writer incremental saves on the existing MUSE v1 checkpoint."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import sys
import uuid

SPEC = importlib.util.spec_from_file_location('muse_state', Path(__file__).with_name('muse-session-state.py'))
STATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(STATE)
LIMIT = 256 * 1024
APPEND = {'Objective', 'Completed', 'Decisions', 'Open Issues', 'Artifact Manifest', 'Verification'}
REPLACE = {'Next Action', 'Required Reads'}


def fail(code):
    raise STATE.MuseStateError(code)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe_path(value):
    path = Path(value)
    if not path.is_absolute() or '..' in path.parts:
        fail('UNSAFE_PATH')
    for item in (path, *path.parents):
        if item.is_symlink():
            fail('UNSAFE_PATH')
    return path


def bounded_read(path):
    path = safe_path(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as handle:
        info = os.fstat(handle.fileno())
        if not stat.S_ISREG(info.st_mode):
            fail('UNSAFE_PATH')
        if info.st_size > LIMIT:
            fail('TOO_LARGE')
        data = handle.read(LIMIT + 1)
        if len(data) > LIMIT:
            fail('TOO_LARGE')
        return data


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            fail('DUPLICATE_JSON_KEY')
        result[key] = value
    return result


def keys(value, required, optional=()):
    if not isinstance(value, dict) or not set(required) <= set(value) or set(value) - set(required) - set(optional):
        fail('INVALID_INPUT')


def hash_value(value):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
        fail('INVALID_INPUT')
    return value


def payload_from(parsed):
    payload = dict(parsed)
    payload['sections'] = {k: parsed['sections'][k.replace(' ', '_')] for k in STATE.REQUIRED_SECTIONS}
    return payload


def parse_exact(raw):
    parsed = STATE.parse_checkpoint_content(raw.decode('utf-8'))
    payload = payload_from(parsed)
    # Exact source roundtrip rejects duplicate/extra headings and metadata too.
    if STATE.render_checkpoint(payload).encode('utf-8') != raw:
        fail('UNREPRESENTABLE_CHECKPOINT')
    return parsed


def target(command, workspace):
    safe_path(workspace)
    identity = STATE.parse_resume(command, workspace)
    if identity['secondary_roles']:
        fail('INVALID_INPUT: single role only')
    return identity, safe_path(identity['checkpoint_path'])


def check_identity(parsed, identity, expected):
    wanted = {k: identity[k] for k in ('role_home', 'role', 'workspace')}
    wanted.update({k: expected[k] for k in ('platform', 'session_id', 'handoff_id')})
    if any(parsed.get(k) != v for k, v in wanted.items()) or parsed['lane'].lower() != identity['lane'].lower():
        fail('IDENTITY_MISMATCH')


def exclusive_write(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def save_delta(input_path, require_daily=False):
    raw = bounded_read(input_path)
    delta = json.loads(raw, object_pairs_hook=unique_object)
    keys(delta, ('schema_version', 'command', 'workspace', 'expected', 'source', 'append', 'replace'))
    if type(delta['schema_version']) is not int or delta['schema_version'] != 1:
        fail('INVALID_INPUT')
    expected = delta['expected']
    keys(expected, ('sha256', 'platform', 'session_id', 'handoff_id'))
    hash_value(expected['sha256'])
    source = delta['source']
    keys(source, ('path', 'sha256', 'coverage'))
    hash_value(source['sha256'])
    if source['coverage'] != 'partial':
        fail('INVALID_INPUT: only explicit partial source coverage is supported')
    keys(delta['append'], (), APPEND)
    keys(delta['replace'], (), REPLACE)
    if not delta['append'] and not delta['replace']:
        fail('INVALID_INPUT: empty delta')
    for value in [*delta['append'].values(), *delta['replace'].values()]:
        if not isinstance(value, str) or not value or value != value.strip() or '\r' in value or '\x00' in value or any(line.startswith('## ') for line in value.splitlines()):
            fail('UNREPRESENTABLE_DELTA')
    identity, checkpoint = target(delta['command'], delta['workspace'])
    source_raw = bounded_read(source['path'])
    if digest(source_raw) != source['sha256']:
        fail('SOURCE_MISMATCH')
    with STATE.checkpoint_lock(checkpoint):
        if (checkpoint.parent/'.daily'/(checkpoint.stem+'.adoption-pending')).exists():fail('ADOPTION_RECOVERY_REQUIRED')
        before = bounded_read(checkpoint)
        if digest(before) != expected['sha256']:
            fail('STALE_VERSION')
        parsed = parse_exact(before)
        check_identity(parsed, identity, expected)
        enabled = STATE.daily_enabled(checkpoint)
        if require_daily and not enabled:
            fail('DAILY_DISABLED')
        if enabled:
            STATE.require_daily_writer(parsed)
        payload = payload_from(parsed)
        for name, addition in delta['append'].items():
            payload['sections'][name] += '\n\n' + addition
        payload['sections'].update(delta['replace'])
        if enabled:
            STATE.require_source_preserved(checkpoint,parsed,payload)
        if payload == payload_from(parsed):
            return dict(status='UNCHANGED', sha256=digest(before), checkpoint_path=str(checkpoint), handoff_id=parsed['handoff_id'])
        payload['updated_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        return publish_change(checkpoint, before, payload, raw, source_raw)


def publish_change(checkpoint, before, payload, raw, source_raw):
    """Publish a validated v1 change; the caller must hold checkpoint_lock."""
    parsed = parse_exact(before)
    STATE.validate_checkpoint_payload(payload)
    after = STATE.render_checkpoint(payload).encode('utf-8')
    if len(after) > LIMIT:
        fail('TOO_LARGE')
    if payload_from(parse_exact(after)) != payload:
        fail('UNREPRESENTABLE_DELTA')
    # No new authority: the existing canonical checkpoint remains authoritative.
    parent = safe_path(checkpoint.parent / '.incremental' / checkpoint.stem)
    parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    archive = parent / uuid.uuid4().hex
    archive.mkdir(mode=0o700)
    receipt = dict(schema_version=1, status='PREPARED', before_sha256=digest(before), sha256=digest(after), checkpoint_path=str(checkpoint), receipt_dir=str(archive), source_coverage='partial', handoff_id=parsed['handoff_id'])
    files = {'before.md': before, 'after.md': after, 'input.json': raw, 'source': source_raw}
    receipt['artifacts'] = {k: digest(v) for k, v in files.items()}
    for name, data in files.items():
        exclusive_write(archive / name, data)
    exclusive_write(archive / 'receipt.json', encode(receipt))
    sync_directory(archive)
    sync_directory(parent)
    sync_directory(parent.parent)
    sync_directory(checkpoint.parent)
    # Detect a bypass visible before publication; not a CAS against arbitrary writers.
    if bounded_read(checkpoint) != before:
        fail('STALE_VERSION')
    STATE.atomic_write(checkpoint, after.decode('utf-8'))
    if bounded_read(checkpoint) != after:
        fail('POST_WRITE_MISMATCH: inspect canonical checkpoint and prepared receipt')
    receipt['status'] = 'SAVED'
    return receipt


def recover(args):
    identity, checkpoint = target(args.command, args.workspace)
    # Atomic v1 replacement makes one open/read sufficient; recovery never writes.
    raw = bounded_read(checkpoint)
    if args.expected_sha256 and digest(raw) != hash_value(args.expected_sha256):
        fail('STALE_VERSION')
    parsed = parse_exact(raw)
    check_identity(parsed, identity, dict(platform=args.source_platform, session_id=args.source_session, handoff_id=args.handoff_id))
    return dict(schema_version=1, status='CHECKPOINT_READABLE', coverage='checkpoint_only', sha256=digest(raw), checkpoint_path=str(checkpoint), checkpoint=parsed, required_reads=parsed['sections']['Required_Reads'], next_action=parsed['sections']['Next_Action'], limits=['No transcript-tail coverage, authorization inference, full boot, handoff, or product QA verdict.', 'Recheck live workspace/Git/policies and task-specific evidence before execution.', 'Same-writer save only; a new session/platform requires explicit legacy handoff.'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='action', required=True)
    save = subs.add_parser('save-delta')
    save.add_argument('--input', type=Path, required=True)
    read = subs.add_parser('recover')
    for flag in ('command', 'workspace', 'source-platform', 'source-session', 'handoff-id'):
        read.add_argument('--' + flag, required=True)
    read.add_argument('--expected-sha256')
    args = parser.parse_args()
    try:
        result = save_delta(args.input) if args.action == 'save-delta' else recover(args)
        print(encode(result).decode('utf-8'), end='')
        return 0
    except (STATE.MuseStateError, OSError, ValueError, TypeError, KeyError) as exc:
        # Paths and raw source contents are deliberately absent from diagnostics.
        message = str(exc) if isinstance(exc, STATE.MuseStateError) else type(exc).__name__
        print('ERROR: ' + message, file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
