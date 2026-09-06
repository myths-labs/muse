#!/usr/bin/env python3
"""Validate distributable source without requiring an author's private role files."""
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent.parent
errors = []
required = ['scripts/install-continuity.py', 'docs/CONTINUITY.md', 'docs/CONTINUITY_CN.md',
            'workflows/save.md', 'workflows/daily-resume.md', 'workflows/daily-bye.md',
            'workflows/legacy/resume.md', 'workflows/legacy/bye.md',
            'skills/core/muse-commands/SKILL.md', 'skills/core/muse-commands/continuity.json']
for relative in required:
    if not (ROOT/relative).is_file(): errors.append('MISSING: '+relative)
skill = ROOT/'skills/core/muse-commands'
files = [p for p in skill.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
files += [ROOT/p for p in ['scripts/install-continuity.py','docs/CONTINUITY.md','docs/CONTINUITY_CN.md']]
for path in files:
    if path.is_symlink(): errors.append('SYMLINK: '+str(path.relative_to(ROOT))); continue
    if path.stat().st_size > 5*1024*1024: errors.append('OVERSIZED: '+path.name); continue
    raw = path.read_bytes()
    if re.search(rb'/Users/[^/\s]+/|/Desktop/(DYA|Prometheus)', raw):
        errors.append('AUTHOR_PATH: '+str(path.relative_to(ROOT)))
    if path.suffix == '.py':
        try: compile(raw,str(path),'exec')
        except SyntaxError: errors.append('PYTHON_SYNTAX: '+path.name)
for relative in ['scripts/install.sh','scripts/generate-agents-md.sh',
                 'skills/core/muse-commands/scripts/muse-doctor.sh','skills/core/muse-commands/scripts/muse-hook.sh']:
    if subprocess.run(['bash','-n',str(ROOT/relative)],capture_output=True).returncode:
        errors.append('SHELL_SYNTAX: '+relative)
version = re.search(r'^## \[([^]]+)\]',(ROOT/'CHANGELOG.md').read_text()).group(1)
for relative in ['README.md','README_CN.md','docs/index.html']:
    if version not in (ROOT/relative).read_text(): errors.append('VERSION: '+relative)
count = len(list((ROOT/'skills').rglob('SKILL.md')))
if 'Total: '+str(count)+' skills' not in (ROOT/'SKILL_INDEX.md').read_text(): errors.append('SKILL_COUNT')
for relative in ['templates/CLAUDE.md','AGENTS.md','skills/core/context-health-check/SKILL.md','workflows/ctx.md']:
    if re.search(r'must exit|immediately run `/bye`|estimate context usage', (ROOT/relative).read_text(),re.I):
        errors.append('OBSOLETE_CONTEXT_POLICY: '+relative)
print(json.dumps({'status':'FAIL' if errors else 'PASS','version':version,'skills':count,
                  'scope':'Release source, syntax, packaging and metadata; behavioral suites run separately','errors':errors}))
raise SystemExit(bool(errors))
