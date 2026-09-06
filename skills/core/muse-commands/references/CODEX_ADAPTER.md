# Codex Adapter for MUSE Workflows

This file defines platform translations only. The workflow selected from `.agent/workflows/` remains authoritative for business logic, ordering, files, and verification.

## Authority and context

| MUSE concept | Codex implementation |
|---|---|
| Durable repo constitution | `AGENTS.md` first, then applicable nested `AGENTS.md` files |
| Claude context file | Read `CLAUDE.md` as MUSE/project context when requested; it cannot override Codex instructions |
| Reusable workflow | `muse-commands` Skill routing to `.agent/workflows/*.md` |
| MUSE task skill | Read from `.agent/skills/<name>/SKILL.md`; official Codex discovery may additionally expose `.agents/skills` |
| Plan mode | Use the active Codex Plan mode when available; otherwise maintain an explicit `update_plan` plan and state that the app mode itself was not switched |
| User question tool | Use the current Codex input mechanism only when a material decision truly blocks work |
| Parallel agents | Use Codex collaboration agents only when the user or applicable instructions explicitly authorize delegation |

## `/resume`

For every supported role/Lane selected by the shared global daily-v1 policy (with explicit legacy opt-out preserved), `muse-doctor.sh resume-workflow` selects the shared `daily-resume.md`; follow it instead of the legacy boot sequence below. `CODEX_THREAD_ID` supplies the current native writer identity. A new task may read the old checkpoint, but must explicitly claim the Lane after reviewing the user's continuation request before writing. `/save` follows shared `save.md`; see [daily helper inputs](DAILY_V1.md). Unknown protocol or runtime identity must not be replaced with guessed values. Use ONBOARDING_V1.md for unregistered existing or new Lanes at their next reviewed resume; this is no longer restricted to MX.

1. Run the doctor, resolve `resume.md`, and call `muse-doctor.sh parse-resume` with the full original command. Lock `role_home + role + lane`; do not infer them again from cwd or work volume.
2. Use current client/session evidence for context observations via `context-health-check`; `USER.md` supplies preferences, not live usage or a default window. After compaction, invalidate older measurements and continue from the current Lane.
3. Follow the layered boot order: constitution, all role L0/status lines, current role file, recent memory, then targeted historical evidence.
4. Prefer live disk and Git evidence over old conversation claims.
5. If the requested lane has an explicit instruction file, load it only after the base boot sequence establishes current state and drift warnings.
6. Keep `subject_projects` separate from startup identity. `/resume strategy Lane A` remains Strategy under the configured role home when its cwd is another configured subject project.
7. Do not claim the lane is resumed until the role, lane checkpoint, project root, branch/worktree, current task, blockers, and next action are all identified.

## `/bye` transcript export

Project-specific transcript exporters are optional and are not shipped or assumed by this runtime. A Claude JSONL exporter must not be applied to Codex data.

If the project supplies a verified exporter, bind it to the exact task ID:

1. Use `CODEX_THREAD_ID` from the Codex shell when present. Use it only when the exporter documents exact-ID selection. Never print unrelated environment values.
2. Resolve the current exact task ID, then run `<project-provided-exact-session-exporter> "[title]" --project-root "$CONVO_ROOT" --session-id THREAD_ID --handoff-id HANDOFF_ID`.
3. Verify the exported header's Session ID equals the current task ID. This is mandatory when multiple Codex tasks share a `cwd`.
4. Verify the exported file exists, is non-empty, contains the first and latest user messages, and contains no raw secrets.
5. Verify the shared handoff ID across the checkpoint, role-home memory, every required project memory, and the transcript with `muse-doctor.sh verify-handoff`.
6. Check whether the active turn is actually present in the exported source. Append only content that is provably absent; do not duplicate messages.

Fallback when the exporter or local session JSONL is unavailable:

1. Identify the current task with the Codex task tools. Prefer the calling thread ID when supplied; otherwise use `list_threads` and match active status, exact `cwd`, newest update time, title, and preview.
2. Read it with `read_thread`, paging through `nextCursor` until `hasMore` is false.
3. Export user and assistant messages in chronological order under the convo root selected by `_CONVENTIONS.md`.
4. Exclude hidden reasoning and raw tool output by default; include concise evidence summaries when required.

Final fallback when neither JSONL export nor Codex task tools are available:

- Write a clearly labeled `CODEX_SUMMARY_ONLY` session summary containing completed work, decisions, unresolved items, file paths, and next steps.
- Do not call it a full conversation export.
- Tell the user that transcript export was degraded and why.

## Claude-only constructs

| Source construct | Codex translation |
|---|---|
| Claude Code session JSONL | Codex `list_threads` + `read_thread` |
| Claude workflow/task agents | Codex collaboration tools, only when delegation is explicitly authorized |
| `AskUserQuestion` | Ask a concise blocking question through the available Codex input surface |
| Claude Plan mode command | Current Codex collaboration mode plus `update_plan`; never claim the UI mode changed unless it actually did |
| Claude auto-memory paths | Project `memory/`, Codex memory instructions, and task transcript evidence; keep the stores distinct |
| Claude `/compact`, `/rewind`, `/clear` | Do not emulate unavailable commands. Save the current Lane, let supported native compaction finish, verify current state, and continue the same task. Start/fork only for a real handoff or unrecoverable client limitation; 80% alone is a save reminder |

## Safety translations

- External communication and publication still require explicit confirmation.
- Destructive operations, migrations, large refactors, and deletions still require explicit confirmation.
- Never inspect or print secret values. Verify only names, presence, redacted suffixes when the governing workflow explicitly permits it, or ask the user to perform a local check when default-deny applies.
- Preserve demo/prod availability. Audits are read-only; implementation must use an isolated branch/worktree until replacement readiness is proven.

## Completion language

- `PASS`: every required step and verification completed.
- `PARTIAL`: safe subset completed, with exact missing steps listed.
- `BLOCKED`: an external capability or user decision is required.
- Never use `PASS`, `complete`, or `launch-ready` for routing-only, HTTP-only, build-only, or summary-only evidence.
