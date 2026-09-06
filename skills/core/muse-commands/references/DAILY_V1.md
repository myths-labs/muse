# Daily v1 helper input

Read the shared `save.md` / `daily-resume.md` workflow for semantics. The canonical schema1 Lane checkpoint remains authoritative; `.daily/<checkpoint-stem>.protocol` selects this mode and contains no second copy of writer identity.

## Save input

```json
{
  "schema_version": 1,
  "command": "/resume strategy Lane A",
  "workspace": "/path/to/project",
  "expected": {"sha256": "<reviewed checkpoint SHA>", "platform": "codex", "session_id": "<current native task ID>", "handoff_id": "<existing ID>"},
  "source": {"path": "<absolute partial source-note path>", "sha256": "<source SHA>", "coverage": "partial"},
  "append": {"Completed": "Verified result this turn.", "Decisions": "New constraint with source."},
  "replace": {"Next Action": "Concrete next step."}
}
```

Call `save-daily --input <path>`. Other appendable fields are Objective, Open Issues, Artifact Manifest, Verification. Required Reads may also be replaced. Preserved fields are never silently rewritten by this entry. Source and input/checkpoint are capped at 256 KiB, symlinks and lossy Markdown are rejected. The native runtime must equal the checkpoint writer on registered Lanes, even for direct low-level `save-delta`.

## New-session claim input

Use the same schema_version, command, workspace, expected and source fields as above. `expected` refers to the **old writer**. The receiver is obtained from runtime, never from a user-supplied receiver ID. Replace append/replace with:

```json
{
  "intent": "continue_this_lane",
  "review": {
    "checkpoint_sha256": "<reviewed checkpoint SHA>",
    "git_sha256": "<prepare-resume git.sha256>",
    "source_tail": "unknown",
    "allowed_work": "Explicit safe continuation scope after reviewing any source gap.",
    "authorization_ref": "Location of the user's request to continue this Lane here."
  }
}
```

Call `claim-lane --input <path>`. `source_tail` is `unknown` or `verified`; this is the executor's review record, not a helper certification. Unknown scope cannot authorize dependent work. The helper compares the pinned checkpoint and fresh Git evidence, archives original bytes/source/input before publishing, preserves handoff and all section bodies, and appends one writer transition to Verification. It returns WRITER_CLAIMED only after canonical readback. Two same-base claimants have one winner. Environment variables are trusted native integration inputs, not cryptographic authentication against local same-user tampering.

Git evidence includes dirty tracked/untracked content and staged blob IDs, not just status/path names. A file over 5 MiB is not opened; the total content budget is 16 MiB, at most 3000 paths and two nested-repository levels. Exceeding these bounds or encountering unreadable/unsupported content yields PARTIAL and refuses a new writer claim. Recovery still returns the checkpoint and uncertainty; do not automatically read oversized files or bypass the refusal. Git-ignored files and production environment state need their separate task obligations. This is a bounded Git-relevant observation, not a frozen filesystem snapshot. Future scoped baselines may handle larger worktrees; they are not silently assumed here.

For an explicitly limited Lane such as MX, the current writer may register a reviewed file scope using `enable-daily ... --scope-file <json> --scope-sha256 <hash>` while pinning the checkpoint SHA. The scope schema has exactly schema_version=1, workspace, files (absolute regular/missing file paths within configured projects), excluded_work and authorization_ref. It must describe the user's actual authorized task, not manufacture permission. The helper hashes every selected file's bytes, including ignored files explicitly selected, plus Git refs/index/tracked status. Scope contents and exclusions are bound into git.sha256; scope/content changes invalidate an outstanding claim. COMPLETE then means complete **within that named scope**, not the whole product. The scope is a policy file beside the protocol marker, not a duplicate current/writer state. Prior scope bytes are preserved before a scope update. The initial live MX scope covers MUSE executable/workflow/constitution/continuity files and explicitly excludes product implementation, other Lanes and production actions.

## Native full writes and formal Bye

Registered Lanes require `write-checkpoint --input <path> --expected-sha256 <reviewed SHA>` and the same native runtime writer. The full-write path may update a formal Bye's handoff ID after its required checks; it may not transfer writer identity. Unknown protocol, missing expected SHA, stale SHA, old runtime writer or lossy content fail closed. Legacy Lanes retain their old contract.

Failure after atomic replacement can leave a new canonical file despite nonzero exit. Compare its hash with the archived before/after hashes and inspect the recorded source. A PREPARED receipt alone is never success. Do not restore an old backup over newer work.

## Runtime capture

Codex uses CODEX_THREAD_ID already provided by the desktop/CLI. Claude's project SessionStart hook invokes `muse-runtime.py capture-claude-session`; it captures only session ID and cwd from the native event and appends shell-quoted MUSE_RUNTIME_* exports to CLAUDE_ENV_FILE, preserving other hooks' exports. It does not save work or call a model itself. An unavailable/malformed environment rejects writes. [Claude's native hook contract](https://code.claude.com/docs/en/hooks#sessionstart) defines these fields.

Global default routing applies to all supported roles/Lanes. Existing checkpoints activate only on their next reviewed resume; new Lanes require an explicit objective and eight sections. See ONBOARDING_V1.md. Guard activation remains per Lane, explicit legacy opt-out overrides the default, and unknown markers fail closed. Source capture/review is documented in SOURCES_V1.md; receipt queries and a latest-state-preserving workflow opt-out in CLOSEOUT_V1.md. No automatic complete transcript coverage, shared-user tamper resistance or product QA is claimed. Native continuation evidence and measured limits live in the MX continuity-release-01 report.
