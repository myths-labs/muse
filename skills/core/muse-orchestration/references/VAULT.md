# Optional Obsidian vault

A vault gives the user one readable history across lanes. It is optional: with no vault
configured every vault step is skipped silently. The vault root is `vault.root` in
`.muse/orchestration.json`, or `OBSIDIAN_VAULT` in `.muse/paths.md`.

The vault has been forgotten twice in practice, each time for days, because the flows that
ran did not include a vault step. So every flow below writes it, and two tools check it.

## Who writes what

| Flow | `daily/` | `decisions/` | `_index.md` |
|---|---|---|---|
| `/save` | one short section | no | no |
| `/bye` (daily-bye) | one section | major decisions | recent activity line |
| `/handoff save` | one section per lane | every new user decision | orchestrator only |
| Orchestrator reports | the report points | no | no |

## Formats

`daily/YYYY-MM-DD.md` (create with `# YYYY-MM-DD` when missing, otherwise append):

```markdown
## Session N (HH:MM-HH:MM) — <role or lane> <title>
- **Done**: one item per line
- **Decision**: [[decisions/YYYY-MM-DD-short-name]] — short reason
- **Next**: key next step
```

`/handoff save` may use `## <lane id> · HH:MM` with three to eight lines of
`- **Done** / **Decision** / **Problem** / **Next**: one sentence (source: file:line)`,
where the source points at the checkpoint just written.

`decisions/YYYY-MM-DD-short-name.md`: title, time, who decided, the user's words verbatim,
Background, Options, Decision, Rationale, Risks, Execution status, Source. Skip when a file
for the same decision already exists.

`bugs/YYYY-MM-DD-BUG-ID.md` (only for a real diagnosis and fix): Symptoms, Root cause, Fix,
Impact, Lessons learned.

`_index.md` "Recent activity": add `- YYYY-MM-DD: <role> — <one-line summary> →
[[daily/YYYY-MM-DD]]` at the top; keep ten lines and turn older ones into an HTML comment.

Rules: append only, never rewrite earlier text; never write keys, passwords, `.env`
content, phone numbers or personal email addresses.

## Checks

- `vault_freshness.py` — exit 0 when the newest note is within `vault.freshness_hours`
  (default 24), 1 when stale, 2 when no vault is configured or readable. `memory_audit.py`
  reports the same condition as one of its checks while lanes are active.
- `vault_coverage_check.py --from N [--to M]` — every quote of the owner (`owner.name`,
  text in 「」, 『』 or “” within a short distance after the name) and every id matching
  `vault.id_patterns` in lines N..M of `vault.coverage_source` must appear verbatim in
  `daily/` or `decisions/`. False positives go into `vault.coverage_skip` (TSV:
  `key<TAB>source line<TAB>reason`). Last line `RESULT: GREEN` or `RESULT: RED`.
