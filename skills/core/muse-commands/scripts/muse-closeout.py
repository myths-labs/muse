#!/usr/bin/env python3
"""Version-bound closeout receipts and read-only validity queries."""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import importlib.util
import json
from pathlib import Path
import sys

SPEC=importlib.util.spec_from_file_location('closeout_sources',Path(__file__).with_name('muse-sources.py'))
SRC=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(SRC)
INC=SRC.INC;STATE=INC.STATE
SURFACES={'product_code','verification','operator_contract','migration','delivery_docs','role_consistency','carrier_manifest','secrets_default_deny','cross_lane','numeric_sampling'}


def date(value):
    try:
        d=datetime.fromisoformat(value.replace('Z','+00:00'))
        if d.tzinfo is None:raise ValueError()
        return d
    except (ValueError,TypeError,AttributeError):INC.fail('INVALID_EVIDENCE_TIME')


def safe_artifact(path):
    p=INC.safe_path(path)
    if any(part=='.env' or part.startswith('.env.') or part.lower() in ['.envrc','keychain','credentials','credentials.json','secrets.json'] or part.lower().endswith(('.env','.pem','.key','.p12','.pfx')) for part in p.parts):INC.fail('CREDENTIAL_ARTIFACT_NOT_ALLOWED')
    return p


def reference(ref):
    INC.keys(ref,('path','sha256'));INC.hash_value(ref['sha256'])
    raw=INC.bounded_read(safe_artifact(ref['path']))
    if INC.digest(raw)!=ref['sha256']:INC.fail('EVIDENCE_CHANGED')
    return raw


def read_json(ref):return json.loads(reference(ref),object_pairs_hook=INC.unique_object)


def validator_hashes():
    names=['muse-closeout.py','muse-sources.py','muse-session-state.py','muse-incremental.py','muse-daily.py','muse-runtime.py','muse-workspace.py','muse-config.py','muse-cli.py','muse-doctor.sh','muse-hook.sh']
    result={n:INC.digest(INC.bounded_read(Path(__file__).with_name(n))) for n in names}
    for name,path in [('muse-onboarding.py',Path(__file__).with_name('muse-onboarding.py')),('continuity.json',INC.STATE.SKILL_ROOT/'continuity.json')]:
        result[name]=INC.digest(INC.bounded_read(path)) if path.exists() else 'ABSENT'
    result['project_configuration'] = INC.digest(INC.encode({'role_home':INC.STATE.CENTER,'projects':{k:str(v) for k,v in INC.STATE.ROOTS.items()}}))
    return result


def contract(parsed):
    data={k:parsed[k] for k in ['role_home','role','lane','workspace','handoff_id']}
    data['sections']={k:v.rstrip() for k,v in parsed['sections'].items() if k!='Verification'}
    data['sections']['Artifact_Manifest']='\n'.join(line for line in data['sections']['Artifact_Manifest'].splitlines() if not line.startswith(SRC.MARKER)).rstrip()
    return INC.digest(INC.encode(data))


def source_observation(value,checkpoint,manifest):
    INC.keys(value,('observed_at','captures','gaps'))
    age=(datetime.now(timezone.utc)-date(value['observed_at'])).total_seconds()
    if age<0 or age>300 or value['gaps']:INC.fail('SOURCE_OBSERVATION_UNAVAILABLE')
    if manifest['counts']['pending'] or not manifest['counts']['events'] or any(s['tail_gap'] for s in manifest['sessions'].values()):INC.fail('SOURCE_REVIEW_INCOMPLETE')
    objects=SRC.Objects(checkpoint);seen=set()
    for c in value['captures']:
        INC.keys(c,('kind','path','sha256','session_id','request_cursor','selection_ref'))
        if c['request_cursor'] is not None:INC.fail('SOURCE_REFRESH_MUST_START_AT_HEAD')
        parse={'codex_page':SRC.codex_page,'claude_hook':SRC.hook_record}.get(c['kind'])
        if not parse:INC.fail('SOURCE_SCHEMA_UNKNOWN')
        events,_=parse(reference({k:c[k] for k in ['path','sha256']}),c,checkpoint_workspace(checkpoint))
        if not events:INC.fail('SOURCE_REFRESH_EMPTY')
        platform=events[0]['platform'];skey=SRC.source_key(platform,c['session_id'],'session')
        session=manifest['sessions'].get(skey)
        if not session or events[-1]['source_id']!=session['through_source_id']:INC.fail('SOURCE_TAIL_NOT_IMPORTED')
        for event in events:
            eid=SRC.source_key(platform,c['session_id'],event['source_id']);shard=SRC.shard_entries(objects,manifest,eid[:2])
            if eid not in shard:INC.fail('SOURCE_TAIL_NOT_IMPORTED')
            actual=SRC.event_body(objects,shard[eid])
            if any(actual[k]!=event[k] for k in ['text','raw_text_sha256','incomplete','turn_id']):INC.fail('SOURCE_EVENT_CONFLICT')
        seen.add(skey)
    if seen!=set(manifest['sessions']):INC.fail('SOURCE_SESSION_REFRESH_MISSING')


def checkpoint_workspace(path):return INC.parse_exact(INC.bounded_read(path))['workspace']


def dependency_signature(dep):
    if dep['kind']=='file':
        INC.keys(dep,('kind','path','sha256'));return INC.digest(reference({k:dep[k] for k in ['path','sha256']}))
    if dep['kind']=='inventory':
        INC.keys(dep,('kind','root','entries','excluded_prefixes'))
        root=safe_artifact(dep['root']);found=[]
        if not root.is_dir():INC.fail('INVENTORY_ROOT_MISSING')
        for p in root.rglob('*'):
            rel=p.relative_to(root).as_posix()
            if any(rel==x or rel.startswith(x.rstrip('/')+'/') for x in dep['excluded_prefixes']):continue
            if p.is_symlink():INC.fail('UNSAFE_INVENTORY_SYMLINK')
            if p.is_file():found.append(rel)
            if len(found)>3000:INC.fail('INVENTORY_TOO_LARGE')
        if sorted(found)!=sorted(dep['entries']):INC.fail('ARTIFACT_INVENTORY_CHANGED')
        return INC.digest(INC.encode(sorted(found)))
    if dep['kind']=='observation':
        INC.keys(dep,('kind','path','sha256'))
        d=read_json({k:dep[k] for k in ['path','sha256']})
        INC.keys(d,('observation_id','observed_at','valid_until','value_sha256','checker_sha256','result'))
        now=datetime.now(timezone.utc)
        if d['result']!='PASS' or not date(d['observed_at'])<=now<=date(d['valid_until']):INC.fail('DEPENDENCY_OBSERVATION_STALE')
        INC.hash_value(d['value_sha256']);INC.hash_value(d['checker_sha256'])
        return INC.digest(INC.encode({k:d[k] for k in ['observation_id','value_sha256','checker_sha256']}))
    INC.fail('UNKNOWN_DEPENDENCY_KIND')


def run_evidence(ref):
    d=read_json(ref)
    for name in ['run_id','executor']:SRC.clean_string(d.get(name))
    if type(d.get('returncode')) is not int or d['returncode']!=0 or not isinstance(d.get('command'),list) or not d['command']:INC.fail('ROUND_NOT_EXECUTED_SUCCESSFULLY')
    if not date(d['started_at'])<=date(d['completed_at'])<=datetime.now(timezone.utc):INC.fail('INVALID_EVIDENCE_TIME')
    if not reference(d['log']):INC.fail('ROUND_LOG_EMPTY')
    return d


def obligations(value):
    result={}
    for o in value:
        INC.keys(o,('id','depends_on'));SRC.clean_string(o['id'],128)
        if o['id'] in result or not isinstance(o['depends_on'],list):INC.fail('INVALID_OBLIGATIONS')
        result[o['id']]=o['depends_on']
    if not SURFACES<=set(result):INC.fail('MISSING_COVERAGE_SURFACE')
    for key,deps in result.items():
        if not set(deps)<=set(result) or key in deps:INC.fail('INVALID_OBLIGATION_DEPENDENCY')
    def visit(key,path):
        if key in path:INC.fail('OBLIGATION_CYCLE')
        for dep in result[key]:visit(dep,path+[key])
    for key in result:visit(key,[])
    return result


def store_receipt(checkpoint,receipt):
    folder=INC.safe_path(checkpoint.parent/'.closeouts'/checkpoint.stem);folder.mkdir(parents=True,exist_ok=True,mode=0o700)
    raw=INC.encode(receipt);key=INC.digest(raw)
    if len(raw)>INC.LIMIT:INC.fail('CLOSEOUT_TOO_LARGE')
    path=folder/(key+'.json')
    if path.exists():reference(dict(path=str(path),sha256=key))
    else:INC.exclusive_write(path,raw)
    INC.sync_directory(folder);INC.sync_directory(folder.parent)
    return dict(path=str(path),sha256=key)


def validate_material(rounds,obs,dependency_ids,key,review):
    if not isinstance(rounds,list) or len(rounds)!=2:INC.fail('TWO_REAL_ROUNDS_REQUIRED')
    run_ids=set();fingerprints=set();regression_ids=set();executors=set();last_end=None
    for rnd in rounds:
        INC.keys(rnd,('execution','regression','checks','residual_risks'))
        execution=run_evidence(rnd['execution']);regression=run_evidence(rnd['regression'])
        fingerprint=INC.digest(INC.encode({k:execution[k] for k in ['command','started_at','completed_at','log']}))
        if execution['run_id'] in run_ids or fingerprint in fingerprints or regression['run_id'] in regression_ids:INC.fail('DUPLICATED_ROUND_EVIDENCE')
        if last_end and date(execution['started_at'])<last_end:INC.fail('ROUNDS_NOT_SEQUENTIAL')
        last_end=date(execution['completed_at']);executors.add(execution['executor'])
        run_ids.add(execution['run_id']);fingerprints.add(fingerprint);regression_ids.add(regression['run_id'])
        if execution['executor']==regression['executor']:INC.fail('INDEPENDENT_REGRESSION_REQUIRED')
        checked=set()
        for item in rnd['checks']:
            INC.keys(item,('id','state','dependencies','finding'))
            if item['id'] not in obs or item['id'] in checked or item['state']!='checked_clear':INC.fail('COVERAGE_UNCHECKED_OR_DEFECT')
            if not item['dependencies'] or not set(item['dependencies'])<=set(dependency_ids):INC.fail('COVERAGE_EVIDENCE_MISSING')
            SRC.clean_string(item['finding']);checked.add(item['id'])
        if checked!=set(obs):INC.fail('MISSING_COVERAGE_SURFACE')
        if not isinstance(rnd['residual_risks'],list):INC.fail('RESIDUAL_RISKS_REQUIRED')
        for risk in rnd['residual_risks']:SRC.clean_string(risk)
    INC.keys(review,('reviewer','verdict','evidence','source_revision','note'))
    if review['verdict']!='PASS' or review['source_revision']!=key or review['reviewer'] in executors:INC.fail('INDEPENDENT_SEMANTIC_REVIEW_REQUIRED')
    SRC.clean_string(review['note']);body=read_json(review['evidence'])
    if body.get('reviewer')!=review['reviewer'] or body.get('verdict')!='PASS' or body.get('source_revision')!=key:INC.fail('SEMANTIC_EVIDENCE_MISMATCH')


def seal(data):
    INC.keys(data,('schema_version','command','workspace','expected_sha256','source_revision','source_observation','scope','dependencies','obligations','rounds','semantic_review'))
    identity,checkpoint=INC.target(data['command'],data['workspace']);SRC.clean_string(data['scope'])
    with STATE.checkpoint_lock(checkpoint):
        if not STATE.daily_enabled(checkpoint):INC.fail('DAILY_DISABLED')
        before=INC.bounded_read(checkpoint)
        if INC.digest(before)!=data['expected_sha256']:INC.fail('STALE_VERSION')
        parsed=INC.parse_exact(before);INC.check_identity(parsed,identity,parsed);STATE.require_daily_writer(parsed)
        key,manifest=SRC.current(checkpoint,parsed)
        SRC.verify_graph(checkpoint,manifest)
        if key!=data['source_revision']:INC.fail('SOURCE_REVISION_CHANGED')
        source_observation(data['source_observation'],checkpoint,manifest)
        obs=obligations(data['obligations']);signatures={k:dependency_signature(d) for k,d in data['dependencies'].items()}
        review=data['semantic_review']
        validate_material(data['rounds'],obs,signatures,key,review)
        if INC.bounded_read(checkpoint)!=before:INC.fail('STALE_VERSION')
        for name,dep in data['dependencies'].items():
            if dependency_signature(dep)!=signatures[name]:INC.fail('DEPENDENCY_CHANGED_DURING_REVIEW')
        receipt=dict(kind='muse_closeout_v1',schema_version=1,lane_key=manifest['lane_key'],scope=data['scope'],checkpoint_sha256=INC.digest(before),contract_sha256=contract(parsed),source_revision=key,source_observation=data['source_observation'],validators=validator_hashes(),dependencies=data['dependencies'],signatures=signatures,obligations=data['obligations'],rounds=data['rounds'],semantic_review=review,created_at=datetime.now(timezone.utc).isoformat(),verdict='DECLARED_SCOPE_CLOSEOUT_VERIFIED',product_launch_authorized=False)
        ref=store_receipt(checkpoint,receipt)
        return dict(status=receipt['verdict'],receipt=ref,scope=data['scope'],new_round=False,limits=['Valid only for declared source and work scope; evidence semantics require independent review.','This receipt does not authorize merge, deployment or product launch.'])


def check(data):
    INC.keys(data,('schema_version','command','workspace','receipt','source_observation'),('observations',))
    identity,checkpoint=INC.target(data['command'],data['workspace'])
    parsed=INC.parse_exact(INC.bounded_read(checkpoint));INC.check_identity(parsed,identity,parsed)
    if not STATE.daily_enabled(checkpoint):INC.fail('DAILY_DISABLED')
    receipt=read_json(data['receipt']);key,manifest=SRC.current(checkpoint,parsed)
    SRC.verify_graph(checkpoint,manifest)
    INC.keys(receipt,('kind','schema_version','lane_key','scope','checkpoint_sha256','contract_sha256','source_revision','source_observation','validators','dependencies','signatures','obligations','rounds','semantic_review','created_at','verdict','product_launch_authorized'))
    if type(receipt['schema_version']) is not int or receipt['schema_version']!=1 or receipt['verdict']!='DECLARED_SCOPE_CLOSEOUT_VERIFIED' or receipt['product_launch_authorized'] is not False:INC.fail('UNKNOWN_CLOSEOUT_SCHEMA')
    expected_folder=checkpoint.parent/'.closeouts'/checkpoint.stem
    refpath=safe_artifact(data['receipt']['path'])
    if refpath.parent!=expected_folder or refpath.name!=data['receipt']['sha256']+'.json':INC.fail('CLOSEOUT_NOT_PUBLISHED_HERE')
    if receipt.get('kind')!='muse_closeout_v1' or receipt.get('lane_key')!=manifest['lane_key']:INC.fail('CLOSEOUT_LANE_MISMATCH')
    obs=obligations(receipt['obligations']);affected=set();reasons=[]
    def result(status):return dict(status=status,receipt=data['receipt'],affected_ids=sorted(affected),reasons=reasons,new_round=False,scope=receipt['scope'],source_observed_at=data['source_observation'].get('observed_at'),source_revision=key,latest_certified=False)
    try:validate_material(receipt['rounds'],obs,receipt['dependencies'],receipt['source_revision'],receipt['semantic_review'])
    except (ValueError,OSError,KeyError,TypeError):
        affected.update(obs);reasons.append('Sealed execution or review material invalid or unavailable');return result('STALE')
    try:source_observation(data['source_observation'],checkpoint,manifest)
    except (ValueError,OSError,KeyError) as exc:
        reasons.append('Source refresh/review unavailable: '+str(exc));return result('BLOCKED')
    if receipt['validators']!=validator_hashes():affected.update(obs);reasons.append('Checker version changed')
    if receipt['contract_sha256']!=contract(parsed):affected.update(obs);reasons.append('Checkpoint work contract changed')
    try:
        for rnd in receipt['rounds']:
            run_evidence(rnd['execution']);run_evidence(rnd['regression'])
        reference(receipt['semantic_review']['evidence'])
    except (ValueError,OSError,KeyError):affected.update(obs);reasons.append('Sealed execution or review evidence changed')
    objects=SRC.Objects(checkpoint);base=objects.read(receipt['source_revision'],'manifest')
    old=dict(SRC.entries(objects,base));now=dict(SRC.entries(objects,manifest))
    if any(now.get(eid)!=item for eid,item in old.items()):affected.update(obs);reasons.append('Covered source or review prefix changed')
    for eid,item in now.items():
        if eid in old:continue
        if not item.get('review'):reasons.append('Unreviewed event');return result('BLOCKED')
        review=objects.read(item['review'],'review')
        for part in review['parts']:
            if part['kind']!='administrative':
                targets=set(part.get('affects',obs))
                if not targets<=set(obs):reasons.append('Unknown affected obligation');return result('BLOCKED')
                affected.update(targets);reasons.append('New business requirement: '+eid)
    overrides=data.get('observations',{})
    if any(k not in receipt['dependencies'] or receipt['dependencies'][k]['kind']!='observation' for k in overrides):INC.fail('INVALID_OBSERVATION_OVERRIDE')
    changed_deps=set()
    for name,dep in receipt['dependencies'].items():
        try:
            if dependency_signature(overrides.get(name,dep))!=receipt['signatures'][name]:changed_deps.add(name)
        except (ValueError,OSError,KeyError):changed_deps.add(name)
    for rnd in receipt['rounds']:
        for item in rnd['checks']:
            if set(item['dependencies'])&changed_deps:affected.add(item['id'])
    if changed_deps:reasons.append('Changed or unavailable dependencies: '+','.join(sorted(changed_deps)))
    while True:
        expanded=affected|{name for name,deps in obs.items() if set(deps)&affected}
        if expanded==affected:break
        affected=expanded
    return result('STALE' if affected else 'VALID')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['verify-closeout','check-closeout']);p.add_argument('--input',type=Path,required=True);args=p.parse_args()
    try:
        data=json.loads(INC.bounded_read(args.input),object_pairs_hook=INC.unique_object)
        if data.get('schema_version')!=1:INC.fail('INVALID_INPUT')
        result=seal(data) if args.action=='verify-closeout' else check(data)
        print(INC.encode(result).decode(),end='');return 0
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print('ERROR: '+(str(exc) if isinstance(exc,ValueError) else type(exc).__name__),file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
