#!/usr/bin/env python3
"""Shared daily save, explicit writer claim and bounded recovery preparation."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys


def load(name, filename):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(filename))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


INC=load('muse_incremental','muse-incremental.py')
RUNTIME=load('muse_runtime','muse-runtime.py')
WORKSPACE=load('muse_workspace','muse-workspace.py')
SOURCES=load('muse_sources','muse-sources.py')
STATE=INC.STATE


def request(path):
    raw=INC.bounded_read(path)
    return json.loads(raw,object_pairs_hook=INC.unique_object),raw


def scope_path(checkpoint):
    return INC.safe_path(checkpoint.parent/'.daily'/(checkpoint.stem+'.scope.json'))


def validate_scope(data,workspace):
    INC.keys(data,('schema_version','workspace','files','excluded_work','authorization_ref'))
    if type(data['schema_version']) is not int or data['schema_version']!=1 or data['workspace']!=workspace:INC.fail('INVALID_WORKSPACE_SCOPE')
    if not isinstance(data['files'],list) or not 1<=len(data['files'])<=3000 or len(set(data['files']))!=len(data['files']):INC.fail('INVALID_WORKSPACE_SCOPE')
    for name in ['excluded_work','authorization_ref']:
        if not isinstance(data[name],str) or not data[name].strip():INC.fail('INVALID_WORKSPACE_SCOPE')
    for filename in data['files']:
        path=INC.safe_path(filename)
        if not any(STATE.path_is_within(path,root) for root in STATE.ROOTS.values()):INC.fail('SCOPE_OUTSIDE_PROJECTS')
        if path.is_dir():INC.fail('SCOPE_FILES_ONLY')
    return data


def git_snapshot(workspace,checkpoint=None):
    scope=None
    if checkpoint and scope_path(checkpoint).exists():
        data,raw=request(scope_path(checkpoint));scope=validate_scope(data,workspace)
    return WORKSPACE.snapshot(workspace,scope=scope)


def runtime_or_unknown():
    try: return RUNTIME.identity()
    except ValueError: return dict(status='UNKNOWN')


def require_runtime_workspace(runtime, workspace):
    RUNTIME.require_workspace(runtime,workspace)


def enable(args):
    identity,path=INC.target(args.command,args.workspace)
    with STATE.checkpoint_lock(path):
        raw=INC.bounded_read(path)
        if INC.digest(raw)!=INC.hash_value(args.expected_sha256): INC.fail('STALE_VERSION')
        parsed=INC.parse_exact(raw)
        INC.check_identity(parsed,identity,parsed)
        STATE.require_daily_writer(parsed)
        enabled=STATE.daily_enabled(path)
        folder=INC.safe_path(path.parent/'.daily');folder.mkdir(mode=0o700,exist_ok=True)
        scope_changed=False
        if args.scope_file:
            data,scope_raw=request(args.scope_file);validate_scope(data,identity['workspace'])
            if INC.digest(scope_raw)!=INC.hash_value(args.scope_sha256):INC.fail('SCOPE_HASH_MISMATCH')
            target=scope_path(path)
            if not target.exists() or INC.bounded_read(target)!=scope_raw:
                if target.exists():
                    old=INC.bounded_read(target);archive=target.with_name(target.name+'.before-'+INC.digest(old))
                    if not archive.exists():INC.exclusive_write(archive,old)
                STATE.atomic_write(target,scope_raw.decode('utf-8'));scope_changed=True
        elif args.scope_sha256:INC.fail('SCOPE_FILE_REQUIRED')
        if enabled and STATE.daily_workflow_enabled(path):return dict(status='DAILY_SCOPE_UPDATED' if scope_changed else 'UNCHANGED',protocol='daily-v1')
        marker=INC.safe_path(folder/(path.stem+'.protocol'))
        STATE.atomic_write(marker,'muse-daily-v1\n')
        INC.sync_directory(path.parent)
        return dict(status='DAILY_ENABLED',checkpoint_path=str(path),sha256=INC.digest(raw),protocol='daily-v1')


def disable(args):
    identity,path=INC.target(args.command,args.workspace)
    with STATE.checkpoint_lock(path):
        raw=INC.bounded_read(path)
        if INC.digest(raw)!=INC.hash_value(args.expected_sha256):INC.fail('STALE_VERSION')
        parsed=INC.parse_exact(raw);INC.check_identity(parsed,identity,parsed);STATE.require_daily_writer(parsed)
        if not STATE.daily_enabled(path):return dict(status='LEGACY_UNREGISTERED',sha256=INC.digest(raw))
        _,manifest=SOURCES.current(path,parsed);SOURCES.verify_graph(path,manifest)
        marker=INC.safe_path(path.parent/'.daily'/(path.stem+'.protocol'))
        STATE.atomic_write(marker,'muse-daily-v1-legacy-workflow\n')
        if INC.bounded_read(path)!=raw:INC.fail('CHECKPOINT_CHANGED_DURING_DISABLE')
        return dict(status='LEGACY_WORKFLOW_GUARDED',sha256=INC.digest(raw),checkpoint_unchanged=True,limits=['Current checkpoint, source objects, archives, scope and writer/version guards retained. Do not restore old helper binaries or delete the guard marker.'])


def prepare(args):
    identity,path=INC.target(args.command,args.workspace)
    if (path.parent/'.daily'/(path.stem+'.adoption-pending')).exists():
        return load('muse_onboarding','muse-onboarding.py').prepare(args,sys.modules[__name__])
    if not STATE.daily_enabled(path) or not path.exists():
        if STATE.daily_workflow_enabled(path):
            return load('muse_onboarding','muse-onboarding.py').prepare(args,sys.modules[__name__])
        return dict(status='LEGACY',role_home=identity['role_home'],role=identity['role'],lane=identity['lane'])
    raw=INC.bounded_read(path);parsed=INC.parse_exact(raw)
    INC.check_identity(parsed,identity,parsed)
    git=git_snapshot(identity['workspace'],path)
    source_ledger=SOURCES.status(path,parsed)
    return dict(status='RECOVERY_REVIEW_REQUIRED',protocol='daily-v1',sha256=INC.digest(raw),checkpoint_path=str(path),checkpoint=parsed,writer={k:parsed[k] for k in ('platform','session_id')},runtime=runtime_or_unknown(),git=git,checkpoint_git_matches=(git.get('branch')==parsed['branch'] and git.get('head')==parsed['head']),source_tail='UNKNOWN',source_ledger=source_ledger,next_action=parsed['sections']['Next_Action'],required_reads=parsed['sections']['Required_Reads'],review_required=['current_policy_and_role','source_tail_and_user_constraints','pending_propagation','production_scope_env_alias_if_applicable','unresolved_failures_and_product_regression','workspace_git_and_work_baseline','explicit_writer_claim_before_new_session_writes'],limits=['The stored source ledger is not a fresh native-tail observation.','Readability, writer identity and Git evidence are not product QA or execution authorization.'])


def claim(path):
    data,raw=request(path)
    INC.keys(data,('schema_version','command','workspace','expected','source','intent','review'))
    if type(data['schema_version']) is not int or data['schema_version']!=1 or data['intent']!='continue_this_lane': INC.fail('INVALID_CLAIM_INTENT')
    expected=data['expected'];INC.keys(expected,('sha256','platform','session_id','handoff_id'));INC.hash_value(expected['sha256'])
    source=data['source'];INC.keys(source,('path','sha256','coverage'));INC.hash_value(source['sha256'])
    if source['coverage']!='partial': INC.fail('INVALID_SOURCE_COVERAGE')
    source_raw=INC.bounded_read(source['path'])
    if INC.digest(source_raw)!=source['sha256']: INC.fail('SOURCE_MISMATCH')
    review=data['review'];INC.keys(review,('checkpoint_sha256','git_sha256','source_tail','allowed_work','authorization_ref'))
    for name in ['allowed_work','authorization_ref']:
        if not isinstance(review[name],str) or not review[name].strip() or len(review[name])>2048: INC.fail('INVALID_REVIEW')
    if review['checkpoint_sha256']!=expected['sha256'] or review['source_tail'] not in ['verified','unknown']: INC.fail('INVALID_REVIEW')
    INC.hash_value(review['git_sha256'])
    identity,checkpoint=INC.target(data['command'],data['workspace'])
    runtime=RUNTIME.identity();require_runtime_workspace(runtime,identity['workspace'])
    with STATE.checkpoint_lock(checkpoint):
        if (checkpoint.parent/'.daily'/(checkpoint.stem+'.adoption-pending')).exists():INC.fail('ADOPTION_RECOVERY_REQUIRED')
        if not STATE.daily_enabled(checkpoint): INC.fail('DAILY_DISABLED')
        before=INC.bounded_read(checkpoint)
        if INC.digest(before)!=expected['sha256']: INC.fail('STALE_VERSION')
        parsed=INC.parse_exact(before);INC.check_identity(parsed,identity,expected)
        _,manifest=SOURCES.current(checkpoint,parsed);SOURCES.verify_graph(checkpoint,manifest)
        git=git_snapshot(identity['workspace'],checkpoint)
        if git['status']!='AVAILABLE' or git['content_coverage']!='COMPLETE' or git['sha256']!=review['git_sha256']: INC.fail('GIT_DRIFT_OR_UNAVAILABLE')
        if all(parsed[k]==runtime[k] for k in ['platform','session_id']): return dict(status='UNCHANGED',sha256=INC.digest(before),writer=runtime)
        payload=INC.payload_from(parsed)
        record=dict(kind='writer_claim',previous={k:parsed[k] for k in ['platform','session_id']},receiver=runtime,source=source,review=review)
        payload['sections']['Verification']+='\n\nWriter transition (identity only; not a full handoff or product verdict): '+json.dumps(record,ensure_ascii=False,sort_keys=True)
        payload.update(platform=runtime['platform'],session_id=runtime['session_id'],updated_at=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))
        receipt=INC.publish_change(checkpoint,before,payload,raw,source_raw)
        receipt.update(status='WRITER_CLAIMED',writer=runtime,scope=review['allowed_work'],source_tail=review['source_tail'])
        return receipt


def save(path):
    return INC.save_delta(path,require_daily=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__);subs=parser.add_subparsers(dest='action',required=True)
    for action in ['enable-daily','disable-daily','prepare-resume','resume-workflow','bye-workflow','source-status']:
        sub=subs.add_parser(action);sub.add_argument('--command',required=True);sub.add_argument('--workspace',required=True)
        if action in ['enable-daily','disable-daily']:
            sub.add_argument('--expected-sha256',required=True)
        if action in ['enable-daily','prepare-resume']:
            sub.add_argument('--scope-file',type=Path)
            sub.add_argument('--scope-sha256')
    for action in ['claim-lane','save-daily','source-update','adopt-lane','initialize-lane']:
        sub=subs.add_parser(action);sub.add_argument('--input',type=Path,required=True)
    args=parser.parse_args()
    try:
        if args.action in ['resume-workflow','bye-workflow']:
            identity,path=INC.target(args.command,args.workspace)
            name='resume' if args.action=='resume-workflow' else 'bye'
            workflow=('daily-' if STATE.daily_workflow_enabled(path) else '')+name+'.md'
            print(STATE.WORKFLOWS/workflow);return 0
        if args.action=='enable-daily': result=enable(args)
        elif args.action=='disable-daily':result=disable(args)
        elif args.action=='prepare-resume':result=prepare(args)
        elif args.action=='source-status':
            identity,path=INC.target(args.command,args.workspace)
            parsed=INC.parse_exact(INC.bounded_read(path));INC.check_identity(parsed,identity,parsed)
            result=SOURCES.status(path,parsed)
        elif args.action=='source-update':result=SOURCES.update(args.input)
        elif args.action=='claim-lane':result=claim(args.input)
        elif args.action in ['adopt-lane','initialize-lane']:
            result=load('muse_onboarding','muse-onboarding.py').adopt(args.input,sys.modules[__name__],initialize=args.action=='initialize-lane')
        else:result=save(args.input)
        print(INC.encode(result).decode(),end='');return 0
    except (ValueError,TypeError,OSError,KeyError,subprocess.SubprocessError) as exc:
        message=str(exc) if isinstance(exc,(STATE.MuseStateError,ValueError)) else type(exc).__name__
        print('ERROR: '+message,file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
