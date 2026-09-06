#!/usr/bin/env python3
"""Reviewed, source-bound activation of an existing or explicitly requested Lane."""
from datetime import datetime, timezone
import json
import uuid


def legacy(raw, D):
    """Allow only the known pre-section prose variation; reject every other loss."""
    I,S=D.INC,D.STATE
    try: return I.parse_exact(raw),''
    except S.MuseStateError as exc:
        if str(exc)!='UNREPRESENTABLE_CHECKPOINT':raise
    text=raw.decode('utf-8');front_end=text.find('\n---\n',4)
    first=text.find('\n## Objective\n',front_end+5)
    if front_end<0 or first<0:I.fail('UNREPRESENTABLE_CHECKPOINT')
    preamble=text[front_end+5:first].strip()
    if not preamble or any(line.startswith('## ') for line in preamble.splitlines()):I.fail('UNREPRESENTABLE_CHECKPOINT')
    canonical=text[:front_end+5]+'\n'+text[first+1:]
    parsed=I.parse_exact(canonical.encode())
    return parsed,preamble


def pending_path(path):
    return path.parent/'.daily'/(path.stem+'.adoption-pending')


def proposed_scope(ref,workspace,D):
    if ref is None:return None,None
    D.INC.keys(ref,('path','sha256'))
    scope,raw=D.request(ref['path']);D.validate_scope(scope,workspace)
    if D.INC.digest(raw)!=D.INC.hash_value(ref['sha256']):D.INC.fail('SCOPE_HASH_MISMATCH')
    return scope,raw


def snapshot(workspace,path,D,scope=None):
    if scope is None and D.scope_path(path).exists():
        scope,_=D.request(D.scope_path(path));D.validate_scope(scope,workspace)
    # These transaction files are verified separately by pinned bytes/archive hashes.
    excluded=[path,path.with_name('.'+path.name+'.lock'),path.parent/'.incremental'/path.stem]
    excluded.extend(path.parent/'.daily'/(path.stem+suffix) for suffix in ('.protocol','.scope.json','.adoption-pending'))
    return D.WORKSPACE.snapshot(workspace,scope=scope,exclude_paths=excluded)


def prepare(args,D):
    I=D.INC;identity,path=I.target(args.command,args.workspace)
    packet=dict(protocol='daily-v1',checkpoint_path=str(path),identity=identity,
        runtime=D.runtime_or_unknown(),source_tail='UNKNOWN',guard_active=D.STATE.daily_enabled(path),
        limits=['Routing does not activate or claim this Lane. Review original sources and recorded scope before adoption.'])
    if path.exists():
        raw=I.bounded_read(path);parsed,preamble=legacy(raw,D)
        # A recorded worktree is authoritative; report it instead of guessing.
        if parsed['workspace']!=identity['workspace']:
            I.check_identity(parsed,dict(identity,workspace=parsed['workspace']),parsed)
            return dict(packet,status='RECORDED_WORKSPACE_REQUIRED',workspace=parsed['workspace'],sha256=I.digest(raw))
        I.check_identity(parsed,identity,parsed)
        packet.update(status='MIGRATION_REVIEW_REQUIRED',sha256=I.digest(raw),checkpoint=parsed,
            writer={k:parsed[k] for k in ('platform','session_id')},legacy_preamble=preamble)
    else:packet.update(status='NEW_LANE_REVIEW_REQUIRED',sha256=None)
    # Provision only the cooperative lock, never the checkpoint or its writer.
    if not path.exists():
        with D.STATE.checkpoint_lock(path):pass
    ref=dict(path=str(args.scope_file),sha256=args.scope_sha256) if getattr(args,'scope_file',None) else None
    scope,_=proposed_scope(ref,identity['workspace'],D)
    if ref:packet['proposed_scope']=ref
    packet['git']=snapshot(identity['workspace'],path,D,scope)
    if pending_path(path).exists():packet['activation_recovery_required']=True
    return packet


def adopt(input_path,D,initialize=False):
    I,S=D.INC,D.STATE;data,request_raw=D.request(input_path)
    I.keys(data,('schema_version','command','workspace','expected_sha256','source','review'),('sections','scope'))
    if type(data['schema_version']) is not int or data['schema_version']!=1:I.fail('INVALID_SCHEMA')
    source=data['source'];I.keys(source,('path','sha256','coverage'))
    if source['coverage']!='partial':I.fail('INVALID_SOURCE_COVERAGE')
    source_raw=I.bounded_read(source['path'])
    if not source_raw.strip() or I.digest(source_raw)!=I.hash_value(source['sha256']):I.fail('SOURCE_MISMATCH')
    review=data['review'];I.keys(review,('git_sha256','allowed_work','authorization_ref','source_tail'))
    I.hash_value(review['git_sha256'])
    for key in ('allowed_work','authorization_ref'):
        if not isinstance(review[key],str) or not review[key].strip() or len(review[key])>2048:I.fail('INVALID_REVIEW')
    if review['source_tail'] not in ('verified','unknown'):I.fail('INVALID_REVIEW')
    identity,path=I.target(data['command'],data['workspace']);runtime=D.RUNTIME.identity()
    scope,scope_raw=proposed_scope(data.get('scope'),identity['workspace'],D)
    D.require_runtime_workspace(runtime,identity['workspace'])
    with S.checkpoint_lock(path):
        if not S.daily_workflow_enabled(path):I.fail('GLOBAL_DAILY_DISABLED')
        pending=I.safe_path(pending_path(path))
        if pending.exists():
            record,_=D.request(pending)
            if record['request_sha256']!=I.digest(request_raw):I.fail('ADOPTION_RECOVERY_REQUIRED: retry the archived request')
            if any(record['receiver'][k]!=runtime[k] for k in ('platform','session_id')):I.fail('WRITER_MISMATCH')
            archive=I.safe_path(record['receipt_dir']);receipt,_=D.request(archive/'receipt.json')
            if receipt['sha256']!=record['after_sha256']:I.fail('ADOPTION_ARCHIVE_MISMATCH')
            for name,wanted in receipt['artifacts'].items():
                if name not in ('before.md','after.md','input.json','source','scope.json'):I.fail('ADOPTION_ARCHIVE_MISMATCH')
                if I.digest(I.bounded_read(archive/name))!=wanted:I.fail('ADOPTION_ARCHIVE_MISMATCH')
            if path.exists() and I.digest(I.bounded_read(path))==record['after_sha256']:
                parsed=I.parse_exact(I.bounded_read(path))
                if any(parsed[k]!=runtime[k] for k in ('platform','session_id')):I.fail('WRITER_MISMATCH')
                _,manifest=D.SOURCES.current(path,parsed);D.SOURCES.verify_graph(path,manifest)
                pending.unlink();I.sync_directory(pending.parent)
                return dict(status='LANE_INITIALIZED' if initialize else 'LANE_ADOPTED',checkpoint_path=str(path),sha256=record['after_sha256'],recovered=True)
        if initialize:
            if path.exists():I.fail('LANE_ALREADY_EXISTS')
            if data['expected_sha256'] is not None:I.fail('INVALID_INITIAL_VERSION')
            sections=data.get('sections');I.keys(sections,S.REQUIRED_SECTIONS)
            before=b'';preamble=''
            payload=dict(schema_version=1,role_home=identity['role_home'],role=identity['role'],lane=identity['lane'],
                subject_projects=identity['subject_projects'],handoff_id='init-'+uuid.uuid4().hex,workspace=identity['workspace'],sections=sections)
        else:
            if S.daily_enabled(path) and not pending.exists():I.fail('LANE_ALREADY_ADOPTED: use claim-lane')
            before=I.bounded_read(path)
            if I.digest(before)!=I.hash_value(data['expected_sha256']):I.fail('STALE_VERSION')
            parsed,preamble=legacy(before,D);I.check_identity(parsed,identity,parsed)
            _,manifest=D.SOURCES.current(path,parsed);D.SOURCES.verify_graph(path,manifest)
            payload=I.payload_from(parsed)
            if preamble:payload['sections']['Open Issues']+='\n\nPreserved legacy scope warning (verbatim):\n'+preamble
        git=snapshot(identity['workspace'],path,D,scope)
        if git['status']!='AVAILABLE' or git['content_coverage']!='COMPLETE' or git['sha256']!=review['git_sha256']:I.fail('GIT_DRIFT_OR_UNAVAILABLE')
        transition=dict(kind='lane_initialization' if initialize else 'daily_adoption',receiver=runtime,review=review,source=source)
        payload['sections']['Verification']+='\n\nContinuity activation (not a product verdict): '+json.dumps(transition,ensure_ascii=False,sort_keys=True)
        payload.update(platform=runtime['platform'],session_id=runtime['session_id'],updated_at=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))
        if initialize:payload.update(branch=git['branch'],head=git['head'])
        S.validate_checkpoint_payload(payload);after=S.render_checkpoint(payload).encode()
        if len(after)>I.LIMIT:I.fail('TOO_LARGE')
        after_parsed=I.parse_exact(after)
        if I.payload_from(after_parsed)!=payload:I.fail('UNREPRESENTABLE_DELTA')
        _,after_manifest=D.SOURCES.current(path,after_parsed);D.SOURCES.verify_graph(path,after_manifest)
        parent=I.safe_path(path.parent/'.incremental'/path.stem);parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        archive=parent/uuid.uuid4().hex;archive.mkdir(mode=0o700)
        files={'before.md':before,'after.md':after,'input.json':request_raw,'source':source_raw}
        if scope_raw is not None:files['scope.json']=scope_raw
        receipt=dict(schema_version=1,status='PREPARED',checkpoint_path=str(path),receipt_dir=str(archive),
            before_sha256=I.digest(before),sha256=I.digest(after),artifacts={k:I.digest(v) for k,v in files.items()})
        for name,value in files.items():I.exclusive_write(archive/name,value)
        I.exclusive_write(archive/'receipt.json',I.encode(receipt));I.sync_directory(archive);I.sync_directory(parent);I.sync_directory(parent.parent)
        folder=I.safe_path(path.parent/'.daily');folder.mkdir(mode=0o700,exist_ok=True)
        record=dict(request_sha256=I.digest(request_raw),after_sha256=I.digest(after),receipt_dir=str(archive),receiver=runtime)
        S.atomic_write(pending,I.encode(record).decode())
        # Install the guard before publishing a new writer. A crash leaves a retryable record.
        S.atomic_write(folder/(path.stem+'.protocol'),'muse-daily-v1\n')
        if scope_raw is not None:S.atomic_write(D.scope_path(path),scope_raw.decode())
        if (path.exists() and I.bounded_read(path)!=before) or (not path.exists() and before):I.fail('STALE_VERSION')
        S.atomic_write(path,after.decode())
        if I.bounded_read(path)!=after:I.fail('POST_WRITE_MISMATCH')
        pending.unlink();I.sync_directory(folder)
        receipt.update(status='LANE_INITIALIZED' if initialize else 'LANE_ADOPTED',writer=runtime,source_tail=review['source_tail'])
        return receipt
