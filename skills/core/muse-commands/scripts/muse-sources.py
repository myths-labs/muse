#!/usr/bin/env python3
"""Content-addressed user-source revisions referenced by the v1 checkpoint."""
from __future__ import annotations
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import re
from pathlib import Path

SPEC=importlib.util.spec_from_file_location('source_incremental',Path(__file__).with_name('muse-incremental.py'))
INC=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(INC)
STATE=INC.STATE
MARKER='MUSE_SOURCE_LEDGER_V1: '
KINDS={'administrative','requirement','decision','question','context'}
DISPOSITIONS={'received','executed','verified','answered','superseded','reference','administrative'}


def redact(text):
    # Match the quoted value by its own opening delimiter: only that delimiter
    # ends the value, and a backslash always consumes the next character, so an
    # opposite quote inside the value cannot abort the match and an escaped
    # closing quote cannot terminate it early. Output keeps the original
    # delimiter, so valid JSON stays valid JSON.
    text=re.sub(r'(?i)(["\x27](?:password|api[_-]?key|secret|access[_-]?token)["\x27]\s*:\s*)("(?:\\.|[^"\\])*"|\x27(?:\\.|[^\x27\\])*\x27)',lambda m:m[1]+m[2][0]+'[REDACTED]'+m[2][0],text)
    for pattern in [r'\b(?:sk|pk)_(?:live|test)_[A-Za-z0-9_-]+',r'\b(?:sk-proj-|sk-ant-|whsec_|ghp_|github_pat_)[A-Za-z0-9_-]+',r'(?i)\bBearer\s+[^\s"\x27]+',r'(?im)\b(?:password|api_key|secret|access_token)\s*[:=]\s*[^\s,;]+']:
        text=re.sub(pattern,'[REDACTED]',text)
    return text


def has_secret(value):
    if isinstance(value,str):return redact(value)!=value
    if isinstance(value,list):return any(has_secret(v) for v in value)
    if isinstance(value,dict):return any(has_secret(v) for v in value.values())
    return False


def clean_string(value,maximum=8192):
    if not isinstance(value,str) or not value or len(value)>maximum or '\x00' in value:INC.fail('INVALID_SOURCE_FIELD')
    return value


def source_key(platform,session,source_id):
    return INC.digest(INC.encode([platform,session,source_id]))


class Objects:
    def __init__(self,checkpoint):
        self.folder=INC.safe_path(checkpoint.parent/'.sources'/checkpoint.stem)
        self.bytes_read=0

    def path(self,key):
        return INC.safe_path(self.folder/(INC.hash_value(key)+'.json'))

    def read(self,key,kind=None):
        raw=INC.bounded_read(self.path(key))
        self.bytes_read+=len(raw)
        if self.bytes_read>16*1024*1024:INC.fail('SOURCE_READ_BUDGET_EXCEEDED')
        if INC.digest(raw)!=key:INC.fail('SOURCE_OBJECT_CORRUPT')
        obj=json.loads(raw,object_pairs_hook=INC.unique_object)
        if kind and obj.get('kind')!=kind:INC.fail('SOURCE_OBJECT_KIND')
        return obj

    def put(self,obj):
        raw=INC.encode(obj)
        if len(raw)>INC.LIMIT:INC.fail('SOURCE_OBJECT_TOO_LARGE')
        key=INC.digest(raw);path=self.path(key)
        self.folder.mkdir(parents=True,exist_ok=True,mode=0o700)
        if path.exists():
            if INC.bounded_read(path)!=raw:INC.fail('SOURCE_OBJECT_CORRUPT')
        else:
            try:INC.exclusive_write(path,raw)
            except FileExistsError:
                if INC.bounded_read(path)!=raw:INC.fail('SOURCE_OBJECT_CORRUPT')
        return key


def empty_manifest(parsed):
    return dict(kind='manifest',schema_version=1,lane_key='/'.join([parsed['role_home'],parsed['role'],parsed['lane'].lower()]),sessions={},shards={},counts=dict(events=0,pending=0,reviewed=0))


def current(checkpoint,parsed):
    lines=[line for line in parsed['sections']['Artifact_Manifest'].splitlines() if line.startswith(MARKER)]
    if len(lines)>1:INC.fail('SOURCE_POINTER_AMBIGUOUS')
    if not lines:return None,empty_manifest(parsed)
    key=lines[0][len(MARKER):];obj=Objects(checkpoint).read(key,'manifest')
    if obj.get('schema_version')!=1 or obj.get('lane_key')!=empty_manifest(parsed)['lane_key']:INC.fail('SOURCE_LANE_MISMATCH')
    return key,obj


def verify_graph(checkpoint,manifest):
    objects=Objects(checkpoint);count=0
    for eid,item in entries(objects,manifest):
        count+=1
        if count>12000:INC.fail('SOURCE_READ_BUDGET_EXCEEDED')
        event=event_body(objects,item)
        if source_key(event['platform'],event['session_id'],event['source_id'])!=eid:INC.fail('SOURCE_OBJECT_ID_MISMATCH')
        if item.get('review'):
            review=objects.read(item['review'],'review')
            if review['event_id']!=eid or review['text_sha256']!=INC.digest(event['text'].encode()):INC.fail('SOURCE_REVIEW_MISMATCH')
    return count


def shard_entries(objects,manifest,prefix):
    item=manifest['shards'].get(prefix)
    return objects.read(item['sha256'],'shard')['entries'] if item else {}


def entries(objects,manifest):
    for prefix in sorted(manifest['shards']):
        for key,item in sorted(shard_entries(objects,manifest,prefix).items()):yield key,item


def event_body(objects,item):
    return objects.read(item['event'],'event')


def is_business(objects,item):
    if not item.get('review'):return True
    return any(p['kind']!='administrative' for p in objects.read(item['review'],'review')['parts'])


def codex_page(raw,selection,workspace):
    data=json.loads(raw,object_pairs_hook=INC.unique_object)
    if data.get('schemaVersion')!=1:INC.fail('SOURCE_SCHEMA_UNKNOWN')
    thread=data.get('thread',{})
    if thread.get('kind')!='codex' or thread.get('id')!=selection['session_id']:INC.fail('SOURCE_SESSION_MISMATCH')
    if thread.get('cwd')!=workspace:INC.fail('SOURCE_WORKSPACE_MISMATCH')
    page=data.get('page',{})
    if page.get('order')!='newest_first' or type(page.get('hasMore')) is not bool:INC.fail('SOURCE_PAGE_UNKNOWN')
    if page['hasMore'] and not page.get('nextCursor'):INC.fail('SOURCE_CURSOR_MISSING')
    turns=data.get('turns')
    if not isinstance(turns,list) or len(turns)>50:INC.fail('SOURCE_PAGE_TOO_LARGE')
    events=[]
    for turn in reversed(turns):
        clean_string(turn.get('id'))
        for position,item in enumerate(turn.get('items',[])):
            if item.get('type')!='userMessage':continue
            ident=clean_string(item.get('id'));blocks=item.get('content')
            if not isinstance(blocks,list):INC.fail('SOURCE_MESSAGE_UNKNOWN')
            text=''.join(b['text'] for b in blocks if b.get('type')=='text' and isinstance(b.get('text'),str))
            if len(text)>65536:INC.fail('SOURCE_MESSAGE_TOO_LARGE')
            incomplete=not text or any(b.get('type')!='text' or not isinstance(b.get('text'),str) for b in blocks) or bool(item.get('truncated'))
            events.append(dict(kind='event',platform='codex',session_id=selection['session_id'],source_id=ident,
                               turn_id=turn['id'],text=redact(text),raw_text_sha256=INC.digest(text.encode()),
                               incomplete=incomplete,position=position,source_kind='codex_app_read_thread_schema1'))
    return events,page


def hook_record(raw,selection,workspace):
    d=json.loads(raw,object_pairs_hook=INC.unique_object)
    if d.get('schema_version')!=1 or d.get('kind')!='claude_user_prompt':INC.fail('SOURCE_SCHEMA_UNKNOWN')
    if d.get('session_id')!=selection['session_id']:INC.fail('SOURCE_SESSION_MISMATCH')
    if d.get('workspace')!=workspace:INC.fail('SOURCE_WORKSPACE_MISMATCH')
    ident=clean_string(d.get('source_id'));text=clean_string(d.get('text'),65536)
    INC.hash_value(d['raw_text_sha256'])
    event=dict(kind='event',platform='claude',session_id=d['session_id'],source_id=ident,turn_id=d.get('prompt_id') or ident,
               text=redact(text),raw_text_sha256=d['raw_text_sha256'],incomplete=bool(d.get('incomplete')),
               position=0,source_kind=d.get('source_kind','claude_UserPromptSubmit'))
    return [event],dict(hasMore=False,nextCursor=None)


def review_value(value,event,runtime):
    INC.keys(value,('event_id','text_sha256','parts','reason'))
    if event['incomplete']:INC.fail('INCOMPLETE_SOURCE_EVENT')
    if value['text_sha256']!=INC.digest(event['text'].encode()):INC.fail('REVIEW_SOURCE_MISMATCH')
    clean_string(value['reason']);parts=value['parts']
    if not isinstance(parts,list) or not parts or len(parts)>100:INC.fail('REVIEW_COVERAGE_GAP')
    end=0
    for p in parts:
        INC.keys(p,('start','end','kind','meaning','disposition','evidence','supersedes'),('affects',))
        if type(p['start']) is not int or type(p['end']) is not int or p['start']!=end or p['end']<=end:INC.fail('REVIEW_COVERAGE_GAP')
        end=p['end']
        if p['kind'] not in KINDS or p['disposition'] not in DISPOSITIONS:INC.fail('INVALID_REVIEW_CLASSIFICATION')
        if (p['kind']=='administrative')!=(p['disposition']=='administrative'):INC.fail('INVALID_REVIEW_CLASSIFICATION')
        clean_string(p['meaning'])
        if not isinstance(p['evidence'],list) or not p['evidence'] or not isinstance(p['supersedes'],list):INC.fail('REVIEW_EVIDENCE_REQUIRED')
        for ref in p['evidence']+p['supersedes']:clean_string(ref)
        if 'affects' in p:
            if not isinstance(p['affects'],list) or not p['affects']:INC.fail('INVALID_REVIEW_AFFECTS')
            for ref in p['affects']:clean_string(ref,128)
    if end!=len(event['text']):INC.fail('REVIEW_COVERAGE_GAP')
    if has_secret(value):INC.fail('SECRET_IN_REVIEW')
    # Classification is a source-bound semantic assertion by the executor, not
    # proof that the implementation happened or the model understood correctly.
    return dict(kind='review',**value,reviewer={k:runtime[k] for k in ['platform','session_id']})


def update(input_path):
    raw=INC.bounded_read(input_path);data=json.loads(raw,object_pairs_hook=INC.unique_object)
    INC.keys(data,('schema_version','command','workspace','expected','captures','reviews'))
    if data['schema_version']!=1 or not isinstance(data['captures'],list) or not isinstance(data['reviews'],list):INC.fail('INVALID_INPUT')
    if len(data['captures'])>100 or len(data['reviews'])>100:INC.fail('SOURCE_BATCH_TOO_LARGE')
    expected=data['expected'];INC.keys(expected,('sha256','platform','session_id','handoff_id'));INC.hash_value(expected['sha256'])
    identity,checkpoint=INC.target(data['command'],data['workspace']);objects=Objects(checkpoint)
    captures=[]
    for c in data['captures']:
        INC.keys(c,('kind','path','sha256','session_id','request_cursor','selection_ref'))
        clean_string(c['selection_ref']);clean_string(c['session_id']);INC.hash_value(c['sha256'])
        blob=INC.bounded_read(c['path'])
        if INC.digest(blob)!=c['sha256']:INC.fail('SOURCE_MISMATCH')
        parse={'codex_page':codex_page,'claude_hook':hook_record}.get(c['kind'])
        if not parse:INC.fail('SOURCE_SCHEMA_UNKNOWN')
        events,page=parse(blob,c,identity['workspace']);captures.append((c,events,page))
    with STATE.checkpoint_lock(checkpoint):
        if not STATE.daily_enabled(checkpoint):INC.fail('DAILY_DISABLED')
        before=INC.bounded_read(checkpoint)
        if INC.digest(before)!=expected['sha256']:INC.fail('STALE_VERSION')
        parsed=INC.parse_exact(before);INC.check_identity(parsed,identity,expected);STATE.require_daily_writer(parsed)
        runtime={k:parsed[k] for k in ['platform','session_id']}
        old_key,old=current(checkpoint,parsed);manifest=copy.deepcopy(old);changed={}
        verify_graph(checkpoint,old)
        def get_shard(event_id):
            prefix=event_id[:2]
            if prefix not in changed:changed[prefix]=copy.deepcopy(shard_entries(objects,manifest,prefix))
            return changed[prefix]
        for c,events,page in captures:
            platform='codex' if c['kind']=='codex_page' else 'claude'
            skey=source_key(platform,c['session_id'],'session');session=manifest['sessions'].get(skey)
            if len(manifest['sessions'])>=512 and session is None:INC.fail('SOURCE_SESSION_LIMIT')
            cursor=c['request_cursor'];ids=[e['source_id'] for e in events]
            if cursor is not None and (not session or session.get('pending_cursor')!=cursor):INC.fail('SOURCE_CURSOR_MISMATCH')
            if session is None:
                session=dict(platform=platform,session_id=c['session_id'],history='UNKNOWN',through_source_id=None,pending_cursor=None,tail_gap=False,anchor_required=None)
            if platform=='codex':
                if cursor is None:
                    previous=session['through_source_id']
                    if previous and previous not in ids and ids and not session['tail_gap']:
                        session['tail_gap']=True;session['anchor_required']=previous
                    if ids:session['through_source_id']=ids[-1]
                    if session['history']=='UNKNOWN' or session['tail_gap']:session['pending_cursor']=page['nextCursor']
                else:session['pending_cursor']=page['nextCursor']
                if session.get('anchor_required') in ids:
                    session['tail_gap']=False;session['anchor_required']=None
                    if session['history']=='API_HISTORY_ENUMERATED':session['pending_cursor']=None
                if not page['hasMore']:
                    if session['tail_gap']:INC.fail('SOURCE_ANCHOR_MISSING')
                    session['history']='API_HISTORY_ENUMERATED';session['pending_cursor']=None
            else:
                if ids:session['through_source_id']=ids[-1]
                # A hook proves its own prompt, not the absence of missed hooks.
                session['history']='HOOK_OBSERVED_ONLY'
            for event in events:
                eid=source_key(event['platform'],event['session_id'],event['source_id']);shard=get_shard(eid)
                if eid in shard:
                    existing=event_body(objects,shard[eid])
                    stable=['platform','session_id','source_id','turn_id','text','raw_text_sha256','incomplete']
                    if any(existing[k]!=event[k] for k in stable):INC.fail('SOURCE_EVENT_CONFLICT')
                else:shard[eid]=dict(event=objects.put(event),review=None)
            manifest['sessions'][skey]=session
        for value in data['reviews']:
            eid=INC.hash_value(value.get('event_id'));shard=get_shard(eid)
            if eid not in shard:INC.fail('SOURCE_EVENT_NOT_FOUND')
            item=shard[eid];event=event_body(objects,item)
            item['review']=objects.put(review_value(value,event,runtime))
        for prefix,shard in changed.items():
            pending=sum(not v.get('review') for v in shard.values())
            business=sum(is_business(objects,v) for v in shard.values())
            manifest['shards'][prefix]=dict(sha256=objects.put(dict(kind='shard',entries=shard)),events=len(shard),pending=pending,business=business)
        manifest['counts']={k:sum(s[k] for s in manifest['shards'].values()) for k in ['events','pending']}
        manifest['counts']['reviewed']=manifest['counts']['events']-manifest['counts']['pending']
        if manifest==old:return dict(status='UNCHANGED',sha256=INC.digest(before),source_revision=old_key)
        key=objects.put(manifest);INC.sync_directory(objects.folder);INC.sync_directory(objects.folder.parent)
        payload=INC.payload_from(parsed)
        body=payload['sections']['Artifact Manifest']
        body='\n'.join(line for line in body.splitlines() if not line.startswith(MARKER)).rstrip()
        payload['sections']['Artifact Manifest']=body+'\n\n'+MARKER+key
        payload['updated_at']=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        safe_request=INC.encode(data)
        if has_secret(data):INC.fail('SECRET_IN_SOURCE_REQUEST')
        evidence=INC.encode(dict(kind='source_revision',revision=key,captures=[dict(kind=c['kind'],sha256=c['sha256'],session_id=c['session_id']) for c,_,_ in captures],scope='User-source observations; not product execution or complete native transcript.'))
        receipt=INC.publish_change(checkpoint,before,payload,safe_request,evidence)
        receipt.update(source_revision=key,counts=manifest['counts']);return receipt


def status(checkpoint,parsed,limit=20):
    key,manifest=current(checkpoint,parsed);objects=Objects(checkpoint)
    verify_graph(checkpoint,manifest)
    pending=[];requirements=[]
    for prefix,info in sorted(manifest['shards'].items()):
        if (not info['pending'] or len(pending)>=limit) and (not info['business'] or len(requirements)>=limit):continue
        for eid,item in sorted(shard_entries(objects,manifest,prefix).items()):
            if not item.get('review') and len(pending)<limit:
                e=event_body(objects,item);pending.append(dict(event_id=eid,text=e['text'],incomplete=e['incomplete'],text_sha256=INC.digest(e['text'].encode()),source_id=e['source_id'],session_id=e['session_id'],platform=e['platform']))
            elif item.get('review') and len(requirements)<limit:
                review=objects.read(item['review'],'review')
                for part in review['parts']:
                    if part['kind']!='administrative' and len(requirements)<limit:requirements.append(dict(event_id=eid,**part))
    sessions=list(manifest['sessions'].values())
    gap=any(s['tail_gap'] for s in sessions)
    coverage='UNKNOWN' if not key or gap else ('CAPTURED_RANGE_PENDING_REVIEW' if manifest['counts']['pending'] else 'CAPTURED_RANGE_REVIEWED')
    return dict(status='SOURCE_LEDGER_READABLE' if key else 'SOURCE_LEDGER_ABSENT',source_revision=key,manifest_path=str(objects.path(key)) if key else None,
                coverage=coverage,counts=manifest['counts'],sessions=sessions,pending=pending,pending_truncated=manifest['counts']['pending']>len(pending),requirements=requirements,
                latest_certified=False,limits=['Recheck exact native source before claiming a current cutoff.','Classifications record semantic review; they do not verify execution.','API enumeration and hook observations do not certify unseen native or pre-registration history.'])
