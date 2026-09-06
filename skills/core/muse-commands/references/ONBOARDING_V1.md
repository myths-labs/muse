# Global default and reviewed first resume

The shared `continuity.json` selects daily-v1 for all supported roles and Lane names. No checkpoint, source ledger or active writer is batch migrated. An explicit guarded legacy-workflow marker overrides the default. A policy/marker error is a real failure, never permission to bypass the guard. User intent to continue this Lane authorizes the ordinary adoption procedure; a read-only inspection does not.

Run `prepare-resume --command '<full command>' --workspace '<absolute workspace>'` and inspect its status:

- `RECOVERY_REVIEW_REQUIRED`: existing daily Lane; use DAILY_V1.md claim/save rules.
- `MIGRATION_REVIEW_REQUIRED`: old checkpoint, original writer retained. Review all eight sections, scope warnings, required references and native user-source gaps, then adopt using the pinned original SHA.
- `NEW_LANE_REVIEW_REQUIRED`: no checkpoint. Strategy derives the Lane objective, acceptance criteria, constraints and workspace from the current request plus already-approved global/Lane goals; the user need not supply a new form. Apply _CONVENTIONS.md's autonomous Lane-selection rules and prepare all eight explicit sections yourself. Preserve the source of authorization, label derived planning as agent analysis, and do not invent an unrelated goal or overwrite another Lane. Preparation provisions only its cooperative lock before the Git observation.
- `RECORDED_WORKSPACE_REQUIRED`: the checkpoint records a different workspace. Check that absolute directory exists and belongs to this task, then prepare with it. A moved/missing or disputed directory requires resolving that concrete issue; do not silently rebind.
- `LEGACY`: preserve explicit legacy behavior.

A missing checkpoint does not establish that a Lane is new. If the user or shared records identify it as an existing paused Lane (for example Strategy B, reported 2026-09-06), locate its old conversation and recoverable work/memory first, using exact identity when available. Do not initialize a blank Lane over unresolved historical work, invent a completed Bye, or require a full retroactive Bye merely to resume. Record recovered facts and remaining gaps; request only essential unavailable identity information. The ordinary initialize path above applies after determining that this is actually new work, or after a specifically reviewed recovery with preserved provenance.

For a large workspace, prepare may return partial Git coverage. Review the actual task's file scope using DAILY_V1.md's schema and supply `--scope-file <json> --scope-sha256 <hash>` to prepare. Include its `{path,sha256}` as `scope` in adoption. Scope must reflect authorized work and list exclusions; it must not be reduced merely to force a pass. Scope expansion later requires the current writer's reviewed enable-daily update.

Existing-Lane adoption input:

All technical inputs below are prepared by the agent, not requested as a user questionnaire. A normal resume request plus current recorded goals suffices when identity/scope are clear. New-Lane initialization may be an agent-derived subdivision of an already-authorized goal under the user's explicit Lane-management delegation; cite both sources in the review instead of inventing a fresh human request.

```json
{
  "schema_version": 1,
  "command": "/resume strategy Lane A",
  "workspace": "<recorded absolute worktree>",
  "expected_sha256": "<prepare sha256>",
  "source": {"path": "<partial source note>", "sha256": "<note hash>", "coverage": "partial"},
  "review": {
    "git_sha256": "<prepare git.sha256>",
    "allowed_work": "<reviewed objective and boundaries>",
    "authorization_ref": "<actual user request and source location>",
    "source_tail": "unknown"
  }
}
```

Use `muse-doctor.sh adopt-lane --input <json>`. For a new Lane, use `initialize-lane`, set `expected_sha256` to null and add `sections` containing exactly Objective, Completed, Decisions, Open Issues, Next Action, Required Reads, Artifact Manifest, Verification. State explicit absence honestly (for example, no implementation completed yet); do not invent evidence. Runtime supplies the native receiver identity. `source_tail` can be verified only after actual source review.

Adoption preserves handoff and all existing section contents, appending only a transition and any verbatim legacy pre-section warning to Open Issues. Original bytes, reviewed source, request and after bytes are archived before publication. A known pre-section scope warning is preserved; other non-roundtrippable content is refused for explicit repair. A side-task warning still defines a side task after adoption; do not reinterpret it as the Lane's main work.

The helper checks current source hashes, Git contents, checkpoint version and native workspace. A Claude session rooted inside a configured project may target its own child worktree; it cannot reach an unrelated sibling or another configured project. A new receiver fences the old writer only when adopted. Never run two active writers on one Lane. The same rules apply to Codex-only, Claude-only and cross-provider continuation.

Activation writes an adoption-pending recovery record and guard before publishing the new checkpoint. While pending, ordinary writes and claims are refused. If interrupted, preserve the archived request and source and retry that exact operation; inspect canonical before/after hashes. If publication already happened, the native receiver can finish the pending recovery. A stale input is not fixed by blindly substituting a fresh SHA. A PREPARED archive alone is not success.

After readback, capture/review available native source deltas under SOURCES_V1.md, then continue the full authorized goal using ordinary save. An adoption source note is partial evidence, not complete transcript coverage. Source capture depends on the actual client adapter and hook receipt; do not claim a missing historical message was recovered.

User guide: `docs/CONTINUITY.md`.
