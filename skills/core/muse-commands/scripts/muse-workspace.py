#!/usr/bin/env python3
"""Bounded Git-relevant content evidence, never a frozen whole-filesystem image."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess

MAX_FILE=5*1024*1024
MAX_TOTAL=16*1024*1024
MAX_PATHS=3000


def digest(data): return hashlib.sha256(data).hexdigest()
def encode(value): return (json.dumps(value,sort_keys=True,ensure_ascii=True)+'\n').encode()


def snapshot(workspace,budget=None,depth=0,scope=None,exclude_paths=None):
    budget=budget if budget is not None else {'bytes':0,'paths':0}
    def run(*args):
        r=subprocess.run(['git','--no-optional-locks','-C',workspace,*args],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=10)
        if len(r.stdout)>256*1024: raise ValueError('GIT_OUTPUT_TOO_LARGE')
        return r.returncode,r.stdout
    result={'status':'UNAVAILABLE','workspace':workspace,'content_coverage':'PARTIAL'}
    try:
        code,root_raw=run('rev-parse','--show-toplevel')
        if code: raise ValueError('NOT_A_GIT_WORKSPACE')
        root=Path(os.fsdecode(root_raw).strip()).resolve()
        exclusions=[Path(p) for p in (exclude_paths or [])]
        def filtered(raw):
            if not exclusions:return raw
            parts=raw.split(b'\0');kept=[];i=0
            while i<len(parts) and parts[i]:
                entry=parts[i];i+=1;group=[entry];names=[os.fsdecode(entry[3:])]
                if b'R' in entry[:2] or b'C' in entry[:2]:
                    group.append(parts[i]);names.append(os.fsdecode(parts[i]));i+=1
                if not all(any(root/name==p or p in (root/name).parents for p in exclusions) for name in names):kept.extend(group)
            return b'\0'.join(kept)+b'\0' if kept else b''
        untracked='no' if scope else 'all'
        status,dirty=run('status','--porcelain=v1','-z','--untracked-files='+untracked)
        dirty=filtered(dirty)
        if exclusions:result['excluded_control_paths']=[str(p) for p in exclusions]
        if status: raise ValueError('GIT_STATUS_UNAVAILABLE')
        head_code,head=run('rev-parse','--verify','HEAD')
        branch_code,branch=run('symbolic-ref','--short','-q','HEAD')
        staged_code,staged=run('diff','--cached','--raw','--no-abbrev','-z','--no-ext-diff')
        if staged_code: raise ValueError('GIT_INDEX_UNAVAILABLE')
        result.update(status='AVAILABLE',root=str(root),head=head.decode().strip() if head_code==0 else None,branch=branch.decode().strip() if branch_code==0 else None,dirty=bool(dirty),dirty_sha256=digest(dirty),staged_sha256=digest(staged))
        tokens=dirty.split(b'\0');paths=[];index=0
        while index<len(tokens) and tokens[index]:
            entry=tokens[index];index+=1
            if len(entry)<4: raise ValueError('INVALID_GIT_STATUS')
            paths.append(os.fsdecode(entry[3:]))
            if b'R' in entry[:2] or b'C' in entry[:2]:
                paths.append(os.fsdecode(tokens[index]));index+=1
        if scope:
            paths=scope['files']
            result.update(scope_kind='explicit_files',scope_sha256=digest(encode(scope)),excluded_work=scope['excluded_work'])
        else:result['scope_kind']='git_relevant'
        evidence=[];issues=[]
        for relative in sorted(set(paths)):
            budget['paths']+=1
            if budget['paths']>MAX_PATHS:
                issues.append('PATH_LIMIT');break
            rel=Path(relative)
            if '..' in rel.parts or (rel.is_absolute() and not scope): raise ValueError('UNSAFE_GIT_PATH')
            path=rel if scope else root/rel
            try: info=path.lstat()
            except FileNotFoundError:
                evidence.append([relative,'absent']);continue
            if any(parent.is_symlink() for parent in path.parents if parent!=root and root in parent.parents):
                issues.append('SYMLINK_PARENT');continue
            if stat.S_ISLNK(info.st_mode):
                evidence.append([relative,'symlink',os.readlink(path)]);continue
            if stat.S_ISDIR(info.st_mode):
                if depth>=2 or not (path/'.git').exists():
                    issues.append('UNVERIFIED_DIRECTORY');continue
                child=snapshot(str(path),budget,depth+1)
                evidence.append([relative,'nested_repo',child['sha256']])
                if child['content_coverage']!='COMPLETE':issues.append('NESTED_REPO_PARTIAL')
                continue
            if not stat.S_ISREG(info.st_mode):
                issues.append('UNSUPPORTED_FILE_TYPE');continue
            if info.st_size>MAX_FILE or budget['bytes']+info.st_size>MAX_TOTAL:
                issues.append('CONTENT_SIZE_LIMIT');continue
            fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
            with os.fdopen(fd,'rb') as handle:
                initial=os.fstat(handle.fileno())
                if not stat.S_ISREG(initial.st_mode) or initial.st_size>MAX_FILE:
                    issues.append('FILE_CHANGED_OR_TOO_LARGE');continue
                h=hashlib.sha256();count=0
                while True:
                    chunk=handle.read(min(65536,MAX_FILE-count+1))
                    if not chunk:break
                    count+=len(chunk);budget['bytes']+=len(chunk)
                    if count>MAX_FILE or budget['bytes']>MAX_TOTAL:raise ValueError('CONTENT_SIZE_LIMIT')
                    h.update(chunk)
                final=os.fstat(handle.fileno())
                if (initial.st_size,initial.st_mtime_ns,initial.st_ctime_ns)!=(final.st_size,final.st_mtime_ns,final.st_ctime_ns):issues.append('FILE_CHANGED_DURING_READ')
                evidence.append([relative,'file',stat.S_IMODE(initial.st_mode),count,h.hexdigest()])
        status2,dirty2=run('status','--porcelain=v1','-z','--untracked-files='+untracked)
        dirty2=filtered(dirty2)
        head2_code,head2=run('rev-parse','--verify','HEAD')
        staged2_code,staged2=run('diff','--cached','--raw','--no-abbrev','-z','--no-ext-diff')
        if status2 or dirty2!=dirty or head2!=head or head2_code!=head_code or staged2_code or staged2!=staged:issues.append('GIT_CHANGED_DURING_READ')
        result.update(content_coverage='PARTIAL' if issues else 'COMPLETE',content_sha256=digest(encode(evidence)),content_paths=len(evidence),issues=sorted(set(issues)))
    except (ValueError,OSError,subprocess.SubprocessError,IndexError) as exc:
        result.update(content_coverage='PARTIAL',issues=[str(exc) if isinstance(exc,ValueError) else type(exc).__name__])
    result['sha256']=digest(encode(result))
    return result
