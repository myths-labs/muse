#!/usr/bin/env python3
"""Capture one native Claude prompt without blocking model processing."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import uuid

SPEC=importlib.util.spec_from_file_location('hook_sources',Path(__file__).with_name('muse-sources.py'))
SRC=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(SRC)


def registered(session,workspace,prompt):
    explicit=None
    first=prompt.lstrip().splitlines()[0]
    if first.startswith('/resume '):
        try:explicit=SRC.STATE.parse_resume(first,workspace)
        except ValueError:pass
    if explicit and not explicit['secondary_roles']:
        target=Path(explicit['checkpoint_path'])
        if SRC.STATE.daily_workflow_enabled(target):return True
    for root in SRC.STATE.ROOTS.values():
        lanes=root/'memory/lanes'
        for marker in (lanes/'.daily').glob('*.protocol'):
            checkpoint=lanes/(marker.stem+'.md')
            if not SRC.STATE.daily_workflow_enabled(checkpoint):continue
            p=SRC.INC.parse_exact(SRC.INC.bounded_read(checkpoint))
            native=Path(workspace).resolve();recorded=Path(p['workspace']).resolve()
            if native!=recorded and native not in recorded.parents:continue
            if p['platform']=='claude' and p['session_id']==session:return True
            if explicit and all(p[k].lower()==explicit[k].lower() for k in ['role_home','role','lane']):return True
    return False


def main():
    try:
        raw=sys.stdin.buffer.read(256*1024+1)
        if len(raw)>256*1024:raise ValueError('input too large')
        d=json.loads(raw,object_pairs_hook=SRC.INC.unique_object)
        if d.get('hook_event_name')!='UserPromptSubmit':return 0
        session=SRC.clean_string(d.get('session_id'));workspace=SRC.clean_string(d.get('cwd'))
        prompt=SRC.clean_string(d.get('prompt'),65536);pid=d.get('prompt_id')
        if '--registered-only' in sys.argv and not registered(session,workspace,prompt):return 0
        if pid is not None:SRC.clean_string(pid)
        # Older native versions have no stable prompt ID. Preserve each observed
        # invocation rather than collapsing two identical human messages.
        ident=pid or 'invocation-'+uuid.uuid4().hex
        record=dict(schema_version=1,kind='claude_user_prompt',source_kind='claude_UserPromptSubmit',session_id=session,
                    workspace=workspace,prompt_id=pid,source_id=ident,text=SRC.redact(prompt),raw_text_sha256=hashlib.sha256(prompt.encode()).hexdigest(),incomplete=False,stable_native_id=bool(pid))
        root=os.environ.get('MUSE_SOURCE_SPOOL',str(SRC.STATE.ROOTS[SRC.STATE.CENTER]/'memory/.muse-source-inbox'))
        folder=SRC.INC.safe_path(root)/hashlib.sha256(session.encode()).hexdigest();folder.mkdir(parents=True,exist_ok=True,mode=0o700)
        path=folder/(hashlib.sha256(ident.encode()).hexdigest()+'.json');body=SRC.INC.encode(record)
        if path.exists():
            if SRC.INC.bounded_read(path)!=body:raise ValueError('conflicting prompt identity')
        else:
            try:SRC.INC.exclusive_write(path,body)
            except FileExistsError:
                if SRC.INC.bounded_read(path)!=body:raise ValueError('conflicting prompt identity')
        SRC.INC.sync_directory(folder)
        return 0
    except Exception:
        # No raw prompt, credentials, or provider paths in diagnostics. The
        # workflow must check actual inbox coverage; hook success is not assumed.
        print('MUSE_SOURCE_CAPTURE_UNAVAILABLE: source coverage requires review.',file=sys.stderr)
        return 0


if __name__=='__main__':raise SystemExit(main())
