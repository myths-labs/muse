#!/usr/bin/env python3
"""Install shared continuity without replacing user policy; retain reversible receipts."""
from __future__ import annotations
import argparse
import base64
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import tempfile
import uuid

REPO = Path(__file__).resolve().parent.parent
BEGIN = '<!-- MUSE CONTINUITY START -->'
END = '<!-- MUSE CONTINUITY END -->'
BLOCK = BEGIN + '''
MUSE commands: read `.agent/skills/muse-commands/SKILL.md` on `/resume`, `/save` or `/bye`.
Preserve the selected role and Lane across clients. Derive plans and acceptance checks
from the user's request and saved evidence; do not demand a form or switch roles.
Save useful deltas, compact if needed, verify and continue. Context pressure does not
force Bye or a new conversation. Closed Lanes require their recorded reopen conditions.
'''+END


def digest(data): return hashlib.sha256(data).hexdigest()
def encode(data): return (json.dumps(data, indent=2, ensure_ascii=False)+'\n').encode()
def metadata(state): return {k:v for k,v in state.items() if k != 'content'}


def unique(items):
    result = {}
    for k, v in items:
        if k in result: raise ValueError('DUPLICATE_JSON_KEY')
        result[k] = v
    return result


def safe_path(root, rel):
    p = Path(rel)
    if p.is_absolute() or '..' in p.parts or not p.parts:
        raise ValueError('UNSAFE_INSTALL_PATH')
    target = root/p
    for parent in target.parents:
        if parent == root: break
        if parent.is_symlink(): raise ValueError('SYMLINK_INSTALL_PARENT: '+rel)
    return target


def snapshot(path):
    if path.is_symlink():
        value = os.readlink(path)
        return {'kind': 'link', 'target': value, 'sha256': digest(value.encode())}
    if not path.exists(): return {'kind': 'absent'}
    if not path.is_file() or path.stat().st_size > 5*1024*1024:
        raise ValueError('UNSUPPORTED_INSTALL_FILE: '+str(path))
    raw = path.read_bytes()
    return {'kind': 'file', 'sha256': digest(raw), 'mode': stat.S_IMODE(path.stat().st_mode),
            'content': base64.b64encode(raw).decode()}


def file_state(raw, mode=0o644):
    return {'kind': 'file', 'sha256': digest(raw), 'mode': mode, 'content': base64.b64encode(raw).decode()}


def json_file(path, default):
    state = snapshot(path)
    if state['kind'] == 'absent': return default
    if state['kind'] != 'file': raise ValueError('UNSAFE_JSON_FILE: '+str(path))
    return json.loads(base64.b64decode(state['content']), object_pairs_hook=unique)


def write_state(path, state):
    path.parent.mkdir(parents=True, exist_ok=True)
    if state['kind'] == 'absent':
        if path.exists() or path.is_symlink(): path.unlink()
        return
    temp = path.with_name('.'+path.name+'.muse-'+uuid.uuid4().hex)
    try:
        if state['kind'] == 'link': os.symlink(state['target'], temp)
        else:
            fd = os.open(temp, os.O_WRONLY|os.O_CREAT|os.O_EXCL, state['mode'])
            with os.fdopen(fd, 'wb') as out:
                out.write(base64.b64decode(state['content'])); out.flush(); os.fsync(out.fileno())
            os.chmod(temp, state['mode'])
        os.replace(temp, path)
    finally:
        if temp.exists() or temp.is_symlink(): temp.unlink()


def entry_bytes(path):
    old = snapshot(path)
    if old['kind'] not in ('absent', 'file'): raise ValueError('UNSAFE_POLICY_ENTRY')
    raw = base64.b64decode(old['content']) if old['kind'] == 'file' else b''
    text = raw.decode('utf-8')
    if text.count(BEGIN) != text.count(END) or text.count(BEGIN) > 1:
        raise ValueError('INVALID_MANAGED_POLICY_BLOCK')
    if BEGIN in text and text.index(END) < text.index(BEGIN):
        raise ValueError('INVALID_MANAGED_POLICY_BLOCK')
    if BEGIN in text:
        start = text.index(BEGIN); end = text.index(END) + len(END)
        text = text[:start]+BLOCK+text[end:]
    else: text += ('\n\n' if text else '')+BLOCK+'\n'
    return text.encode()


def plan_install(root, tool, core_only=False):
    desired = {}
    old_manifest = json_file(safe_path(root, '.muse/install-state.json'), {'schema_version': 1, 'files': {}})
    if not isinstance(old_manifest, dict) or old_manifest.get('schema_version') != 1 or not isinstance(old_manifest.get('files'), dict):
        raise ValueError('INVALID_INSTALL_STATE')
    legacy = json_file(REPO/'scripts/continuity-legacy-hashes.json', {})
    config_path = safe_path(root, '.muse/config.json')
    if config_path.exists() or config_path.is_symlink():
        config = json_file(config_path, None)
        if not isinstance(config, dict) or set(config) != {'schema_version','role_home','projects'} or type(config['schema_version']) is not int or config['schema_version'] != 1 or not isinstance(config['projects'], dict) or config['role_home'] not in config['projects']:
            raise ValueError('INVALID_MUSE_CONFIG')
        if any(not re.fullmatch(r'[a-z][a-z0-9_-]{0,31}', k) or not isinstance(v,str) or not v.strip() for k,v in config['projects'].items()):
            raise ValueError('INVALID_MUSE_PROJECTS')
        spec = importlib.util.spec_from_file_location('install_config', REPO/'skills/core/muse-commands/scripts/muse-config.py')
        config_module = importlib.util.module_from_spec(spec); spec.loader.exec_module(config_module)
        config_module.load(config_path)
        # The target's runtime may share a separate role home; configuration stays user-owned.
    else:
        desired['.muse/config.json'] = file_state(encode({'schema_version':1,'role_home':'home','projects':{'home':'.'}}))
    skill_paths = []
    for tier in (['core'] if core_only else ['core', 'toolkit']):
        directory = REPO/'skills'/tier
        if not directory.is_dir(): continue
        for skill in sorted(directory.iterdir()):
            if not skill.is_dir() or not (skill/'SKILL.md').is_file(): continue
            prefix = '.agent/skills/muse-commands' if skill.name == 'muse-commands' else '.agent/skills/'+tier+'/'+skill.name
            skill_paths.append((skill.name,prefix))
            for source in sorted(skill.rglob('*')):
                if '__pycache__' in source.parts or source.suffix == '.pyc': continue
                if source.is_symlink(): raise ValueError('RELEASE_SOURCE_SYMLINK')
                if source.is_file():
                    state = snapshot(source); desired[prefix+'/'+str(source.relative_to(skill))] = state
    for source in sorted((REPO/'workflows').rglob('*.md')):
        desired['.agent/workflows/'+str(source.relative_to(REPO/'workflows'))] = snapshot(source)
    discovery = '.agents/skills' if tool == 'codex' else '.claude/skills'
    for name, prefix in skill_paths:
        dest = discovery+'/'+name; target = os.path.relpath(root/prefix, (root/dest).parent)
        desired[dest] = {'kind':'link','target':target,'sha256':digest(target.encode())}
    entry = 'AGENTS.md' if tool == 'codex' else 'CLAUDE.md'
    entry_path = safe_path(root, entry)
    desired[entry] = file_state(entry_bytes(entry_path), snapshot(entry_path).get('mode',0o644))
    ignore_path = safe_path(root, '.gitignore')
    old_ignore = snapshot(ignore_path)
    if old_ignore['kind'] not in ('absent', 'file'): raise ValueError('UNSAFE_GITIGNORE')
    ignore = base64.b64decode(old_ignore['content']).decode() if old_ignore['kind']=='file' else ''
    private_rules = ['/.muse/installations/', '/.muse/install-state.json', '/.muse/install.lock', '/memory/.muse-source-inbox/']
    missing_rules = [rule for rule in private_rules if rule not in ignore.splitlines()]
    if missing_rules:
        ignore += ('\n' if ignore and not ignore.endswith('\n') else '')+'\n# Private MUSE installation receipts and prompt inbox\n'+'\n'.join(missing_rules)+'\n'
    desired['.gitignore'] = file_state(ignore.encode(), old_ignore.get('mode',0o644))
    if tool == 'claude':
        for command_name in ('resume', 'save', 'bye'):
            rel = '.claude/commands/'+command_name+'.md'
            command_file = safe_path(root, rel)
            # Preserve unrelated user commands; explicit /muse-commands is available too.
            if (not command_file.exists() and not command_file.is_symlink()) or rel in old_manifest['files']:
                raw = ('---\ndescription: MUSE '+command_name+' with shared role and Lane continuity\n---\n\n'
                       'Execute MUSE /'+command_name+' $ARGUMENTS. Read this project\'s '
                       '`.agent/skills/muse-commands/SKILL.md` and the selected shared workflow. '
                       'Preserve the requested role/Lane; derive helper inputs from actual intent. '
                       'Do not use another project\'s same-named command or initialize an old Lane as blank.\n').encode()
                desired[rel] = file_state(raw)
        settings = json_file(safe_path(root, '.claude/settings.json'), {})
        if not isinstance(settings,dict): raise ValueError('INVALID_CLAUDE_SETTINGS')
        hooks = settings.setdefault('hooks', {})
        if not isinstance(hooks,dict): raise ValueError('INVALID_CLAUDE_HOOKS')
        for event, action in [('SessionStart','start'), ('UserPromptSubmit','source')]:
            group = hooks.setdefault(event, [])
            if not isinstance(group,list): raise ValueError('INVALID_CLAUDE_HOOKS')
            command = 'bash "${CLAUDE_PROJECT_DIR}/.agent/skills/muse-commands/scripts/muse-hook.sh" '+action
            item = {'hooks':[{'type':'command','command':command}]}
            if item not in group: group.append(item)
        desired['.claude/settings.json'] = file_state(encode(settings), snapshot(safe_path(root,'.claude/settings.json')).get('mode',0o600))
    files = {}; changes = []
    allowed_merge = {entry, '.claude/settings.json', '.gitignore'}
    for rel, wanted in desired.items():
        path = safe_path(root,rel); current = snapshot(path)
        if current['kind'] == 'link' and wanted['kind'] != 'link': raise ValueError('UNSAFE_EXISTING_SYMLINK: '+rel)
        if current['kind'] != 'absent' and current != wanted and rel not in allowed_merge:
            previous = old_manifest['files'].get(rel)
            known_legacy = current.get('sha256') in legacy.get(rel, [])
            if metadata(current) != previous and not known_legacy:
                raise ValueError('UNMANAGED_OR_MODIFIED_CONFLICT: '+rel)
        if current != wanted: changes.append({'path':rel,'before':current,'after':wanted})
        files[rel] = metadata(wanted)
    merged = dict(old_manifest['files']); merged.update(files)
    state_path = '.muse/install-state.json'; current = snapshot(safe_path(root,state_path))
    wanted = file_state(encode({'schema_version':1,'files':merged}),0o600)
    if current != wanted: changes.append({'path':state_path,'before':current,'after':wanted})
    return changes


def transact(root, changes, operation):
    # Preflight all paths before any file mutation. A lock serializes installers.
    control = safe_path(root, '.muse/install.lock')
    if control.is_symlink(): raise ValueError('UNSAFE_INSTALL_LOCK')
    root.mkdir(parents=True, exist_ok=True); control.parent.mkdir(parents=True, exist_ok=True)
    with open(control, 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        for change in changes:
            if snapshot(safe_path(root,change['path'])) != change['before']:
                raise ValueError('INSTALL_STATE_CHANGED: '+change['path'])
        receipt_dir = safe_path(root, '.muse/installations/'+uuid.uuid4().hex)
        receipt_dir.mkdir(parents=True, mode=0o700)
        receipt = {'schema_version':1,'operation':operation,'target':str(root),'status':'PREPARED','changes':changes}
        receipt_path = receipt_dir/'receipt.json'
        write_state(receipt_path,file_state(encode(receipt),0o600))
        applied = []
        try:
            for change in changes:
                write_state(safe_path(root,change['path']),change['after']); applied.append(change)
            for change in changes:
                if snapshot(safe_path(root,change['path'])) != change['after']: raise ValueError('INSTALL_READBACK_FAILED')
            receipt['status'] = 'APPLIED'
            write_state(receipt_path,file_state(encode(receipt),0o600))
        except Exception:
            for change in reversed(applied): write_state(safe_path(root,change['path']),change['before'])
            receipt['status'] = 'ROLLED_BACK_ON_FAILURE'
            write_state(receipt_path,file_state(encode(receipt),0o600)); raise
        return {'status':'UNCHANGED' if not changes else 'INSTALLED' if operation=='install' else 'ROLLED_BACK','receipt_path':str(receipt_path),'changed_files':len(changes)}


def rollback(path):
    receipt = json_file(path, None)
    if not isinstance(receipt,dict) or receipt.get('schema_version') != 1 or receipt.get('status') != 'APPLIED' or receipt.get('operation') != 'install':
        raise ValueError('INVALID_ROLLBACK_RECEIPT')
    root = Path(receipt['target'])
    if root.is_symlink() or not root.is_absolute() or path.resolve().parent.parent != (root/'.muse/installations').resolve():
        raise ValueError('ROLLBACK_RECEIPT_LOCATION_MISMATCH')
    changes = []
    for change in reversed(receipt['changes']):
        current = snapshot(safe_path(root,change['path']))
        if current != change['after']: raise ValueError('ROLLBACK_USER_CHANGES: '+change['path'])
        changes.append({'path':change['path'],'before':current,'after':change['before']})
    return transact(root,changes,'rollback')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tool', choices=['codex','claude']); p.add_argument('--target',default='.')
    p.add_argument('--core-only',action='store_true'); p.add_argument('--rollback',type=Path)
    args = p.parse_args()
    if args.rollback: return rollback(args.rollback)
    if not args.tool: raise ValueError('TOOL_REQUIRED')
    root = Path(args.target).expanduser().absolute()
    if any(x.is_symlink() for x in (root,*root.parents)): raise ValueError('SYMLINK_TARGET_ROOT')
    return transact(root,plan_install(root,args.tool,args.core_only),'install')


if __name__ == '__main__':
    try: print(json.dumps(main()))
    except (ValueError,OSError,TypeError,KeyError) as exc:
        print('MUSE_INSTALL_ERROR: '+str(exc),file=sys.stderr)
        raise SystemExit(2)
