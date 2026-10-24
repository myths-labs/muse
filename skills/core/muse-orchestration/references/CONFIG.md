# `.muse/orchestration.json`

Optional. Copy `templates/orchestration.example.json` to `.muse/orchestration.json` and
edit. Lookup order for every tool: `--config PATH`, then `MUSE_ORCHESTRATION_CONFIG`, then
the nearest `.muse/orchestration.json` above the working directory. Relative paths
resolve against the project that holds `.muse/`; `~` and `${VAR}` are expanded. Only
non-secret variables expand (`HOME`, `PWD`, `TMPDIR`, `USER`, `XDG_*_HOME` and names that
start with `MUSE_`); any other name, or an unset one, is a configuration error. There are no author-machine defaults: a
check whose path is not configured reports SKIP or UNCONFIGURED.

| Key | Type | Default | Used by |
|---|---|---|---|
| `schema_version` | int | — (must be 1) | all |
| `owner.name` | string | none | vault coverage (quotes), memory audit (decision lines) |
| `owner.decision_words` | list of strings | built-in Chinese and English words | memory audit: words that mark "the owner decided" |
| `orchestrator` | object `{id, title, checkpoint, required_reads}` | none | `/handoff`, timers, `/away`, `/back` |
| `lanes` | list of `{id, title, checkpoint, required_reads}` | `[]` | `/handoff <lane id>` |
| `relay_runbook` | path | none | `/handoff save` snapshots |
| `heavy_lock` | path | none | patrol, heavy jobs |
| `board.status_glob` | glob | none | patrol stalled list |
| `board.stale_days` | int | 2 | patrol stalled list |
| `memory.projects_root` | path | `~/.claude/projects` | recall, memory audit, wall recover |
| `memory.hub` | directory name or null | null | memory audit: where shared decisions are written |
| `memory.labels` | object dir → label | `{}` | memory audit output |
| `memory.watch_terms` | list of `{name, pattern, compare}` | `[]` | memory audit: names that must stay visible; `compare: false` stops a term from marking comparison lines |
| `memory.index_max_lines` | int | 200 | memory audit |
| `memory.index_max_chars` | int | 25000 | memory audit |
| `memory.daily_projects` | list of `{name, root}` | `[]` | memory audit: today's daily memory file |
| `memory.cross_index` | path inside the project | `.muse/memory-cross-index.md` | memory audit `--sync` |
| `memory.ignore` | list of fnmatch patterns | `[]` | memory audit: project directories to leave out (key scan still covers them) |
| `memory.block_max_age_hours` | number | 36 | memory audit: freshness of the cross-directory block and index |
| `memory.decision_file_pattern` | regex or null | decision/provider/vendor/comparison/pricing words | memory audit: file names that count as decision memories (watch terms are added) |
| `memory.scan_extra_paths` | list of paths | `[]` | memory audit: extra files or folders for the key-pattern scan |
| `memory.extra_key_patterns` | list of `{name, pattern}` | `[]` | memory audit: extra key patterns |
| `checkpoints.files` | list of paths | `[]` | recall, memory audit |
| `checkpoints.globs` | list of globs | `[]` | recall, memory audit |
| `checkpoints.skip_pattern` | regex or null | patrol/sentinel/report words | memory audit: checkpoint lines that are routine logs, not decisions |
| `extra_search_globs` | list of globs | `[]` | recall |
| `removable_roots` | list of paths | `[]` | recall: paths under them are skipped unless mounted |
| `vault.root` | path or null | `OBSIDIAN_VAULT` in `.muse/paths.md` | vault steps and checks |
| `vault.freshness_hours` | number | 24 | vault freshness, memory audit |
| `vault.active_hours` | number | 6 | memory audit: a stale vault is a failure only if a checkpoint changed within this many hours |
| `vault.coverage_source` | path | none | vault coverage |
| `vault.coverage_skip` | path | none | vault coverage |
| `vault.coverage_dirs` | list of names | `["daily", "decisions"]` | vault coverage |
| `vault.id_patterns` | list of regexes | `[]` | vault coverage: ids that must be recorded (for example deployment ids) |

The memory directory index limits come from the client: the 200-line limit is documented
for Claude Code; the character limit was observed in one client build. Set both to what
your client loads.

Keep the cross-directory index and any copied memory out of version control; they can
contain private notes.

## Untrusted checkouts

A project config travels with the repository, so treat it as untrusted input:

- Tools that print file contents (`recall.py`, `memory_audit.py`, `vault_coverage_check.py`)
  read only plain notes (`.md`, `.markdown`, `.txt`, `.tsv`) and skip `.env*` files and
  credential folders such as `.ssh`, `.aws` and `.gnupg`.
- The only file a tool writes from config is `memory.cross_index`, and it must resolve
  inside the project root.
- `memory_audit.py --sync` writes into memory directories only under the default
  `~/.claude/projects`; when the config moves `memory.projects_root`, pass the same
  directory with `--projects-root` to confirm.
- The recall command written into memory indexes is always the bundled `recall.py`, and
  every path in generated commands is shell-quoted.
- Git runs on `memory.daily_projects` roots with hooks and fsmonitor disabled and without
  system configuration.
