# Orchestration tools

All scripts live in `.agent/skills/core/muse-orchestration/scripts/`, use the Python
standard library (3.7+), make no network calls and never open `.env*` or credential
files. Run them with `python3 -I`. Each accepts `--config PATH`; otherwise it uses
`MUSE_ORCHESTRATION_CONFIG` or the nearest `.muse/orchestration.json` (see `CONFIG.md`).
Exit code 2 always means bad input or missing configuration, never "nothing found".
A project config may come from an untrusted checkout: tools that print file contents read
only plain notes, and the only configured write target must stay inside the project (see
"Untrusted checkouts" in `CONFIG.md`).

## orchestration_config.py

`python3 -I orchestration_config.py [--config PATH]` prints the resolved config file,
project root, lane ids and vault root as JSON (`PASS`, `UNCONFIGURED` or `FAIL`).
The other scripts load it with `importlib`, because `-I` keeps the script directory off
`sys.path`.

## recall.py

```bash
python3 -I recall.py [--projects-root DIR] <word> [<synonym> ...]
```

Searches every memory directory under `memory.projects_root`, the lane checkpoints in
`checkpoints.files` / `checkpoints.globs`, and `extra_search_globs`. Keywords are OR-ed
and case-insensitive; give synonyms in every language your notes use. Output is grouped
by file (`path:line` and the first 200 characters, at most 8 lines per file and 80 in
total); the last line is the total. A path under an unmounted `removable_roots` entry is
skipped with a warning, because "not found" then does not mean "not there". Exit 0 after
any search, including zero hits.

## memory_audit.py

```bash
python3 -I memory_audit.py            # read-only audit; last line RESULT GREEN|RED
python3 -I memory_audit.py --sync     # write the cross-directory block into every MEMORY.md
python3 -I memory_audit.py --unsync   # remove that block again
```

Checks the client's auto-memory directories: every directory readable with an index;
index links resolve, topic files are indexed, the index fits `memory.index_max_lines` /
`memory.index_max_chars`; cross-directory blocks and the cross-directory index are fresh;
decision files of other directories are visible from the hub; every `memory.watch_terms`
name is visible in each loaded index; decision lines of the owner in recent checkpoints
have a memory; the vault was written within `vault.freshness_hours` while lanes are
active; today's daily memory file exists for each `memory.daily_projects` entry;
`recall.py` exists; key patterns in memory files are reported as `file:line` and type
only, never the value. Checks that need a missing setting report SKIP or UNCONFIGURED.
`--sync` writes only when asked, atomically, and refuses a file that changed meanwhile.
Run `--help` for the test options (`--json`, `--days`, `--all`).

Why the cross-directory block exists: a client loads only the memory index of the current
working directory, and only its first part (the documented 200 lines; a character cap
was observed in at least one client build, so check yours). Decisions written while
working in another directory are otherwise invisible.

## negative_claim_guard.py (Stop hook)

Blocks the end of a turn whose last answer claims something is absent from memory
("not in my records", "记录里没有", …, outside code and quotes) when no shell call in that
turn ran `recall.py` successfully. The reason tells the agent to run `recall.py` with
synonyms first. Fail-open: any error, timeout (2.5 s) or oversized transcript lets the
stop through, and `stop_hook_active` never loops.

```bash
python3 -I negative_claim_guard.py --selftest
python3 -I negative_claim_guard.py --install   [--settings PATH] [--backup-dir DIR]
python3 -I negative_claim_guard.py --uninstall [--settings PATH] [--backup-dir DIR]
```

The default target is `.claude/settings.json` under the current directory; use
`--settings ~/.claude/settings.json` for every project of this user. The file is backed
up into `.muse-hook-backups/` next to it, only this entry is added or removed, the result
is re-parsed and restored from the backup if anything else changed. The installed
command contains the absolute path of the Python that ran `--install`; install with a
long-lived interpreter, not a temporary virtual environment.

## licence_stop_guard.py (optional policy Stop hook)

Encodes one project policy: a licence is one line of fact, not by itself a reason to skip
evaluating an open-source project, model, dataset or paper. It blocks a sentence that
pairs a licence word with a stop word ("non-commercial, so skip it") unless the sentence
follows the policy (the licence goes to human review, or the licence itself forbids
evaluation). The default reason asks the agent to record the licence in one line, keep
evaluating where the licence permits evaluation and raise licence limits for human review
before production use. It is not legal advice. Install it only if your project adopts
this policy; `MUSE_LICENCE_GUARD_REASON` replaces the reason text. Same `--selftest`,
`--install` and `--uninstall` options as above.

## vault_coverage_check.py

```bash
python3 -I vault_coverage_check.py --from N [--to M] [--source FILE] [--vault DIR] [--skip FILE] [--owner NAME]
```

For lines N..M of `vault.coverage_source`, every quote of `owner.name` (text in 「」, 『』
or “” within 40 characters after the name, at least 4 characters) and every id matching
`vault.id_patterns` must appear in `vault.coverage_dirs` (default `daily`, `decisions`),
compared on the first 10 characters with whitespace removed. Skip file rows:
`key<TAB>source line<TAB>reason`. Exit 0 and `RESULT: GREEN`, or 1 and `RESULT: RED` with
each missing item and its source line.

## vault_freshness.py

`python3 -I vault_freshness.py [--vault DIR] [--max-hours H]` — exit 0 when the newest
note is younger than `vault.freshness_hours` (default 24), 1 when stale or empty, 2 when
no vault is configured or readable.

## wall_recover.py

```bash
python3 -I wall_recover.py <old-session-id> [--since 2026-01-31T09:20] [--chars 300] [--projects-root DIR]
```

Reads the old session's local transcript and its subagent transcripts (Claude Code
layout: `<projects root>/<project>/<session>.jsonl` and `<session>/subagents/agent-*.jsonl`)
and lists every subagent active since `--since` (local time), whether the parent received
its completion notice, and the last assistant text of unfinished ones. Tool inputs and
results are never printed. Write the result into the lane checkpoint, then re-dispatch
only the unfinished work.
