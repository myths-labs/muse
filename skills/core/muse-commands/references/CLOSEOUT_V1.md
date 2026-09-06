# Closeout receipt contract

Daily save continues work. Formal Bye closes a declared work/source scope. A receipt binds evidence at a cutoff, not perfect software or permission to launch. Read daily-bye.md first.

CLI: `muse-doctor.sh verify-closeout --input <json>` or `check-closeout --input <json>`. Seal schema1 has:

- schema_version, command (locked resume identity), workspace, expected_sha256, source_revision, scope.
- source_observation: observed_at (UTC, within300seconds), gaps (empty within declared scope), captures (SOURCES_V1 references; fresh head for each recorded session).
- dependencies: named objects: file (path,sha256), inventory (root,entries,excluded_prefixes), observation (path,sha256).
- obligations: id and depends_on; all ten daily-bye IDs plus real work obligations; references exist, no cycles.
- rounds: exactly two objects with execution reference, regression reference, checks, residual_risks. Every obligation has a check: id, state=checked_clear, dependencies (dependency IDs), finding (actual result/scope basis).
- semantic_review: reviewer, verdict=PASS, evidence reference, source_revision, note. Evidence JSON itself binds the same reviewer/PASS/source_revision. The primary executor must not fabricate an independent review.

A reference is path (absolute) and sha256 (actual bytes). Execution/regression JSON: run_id, executor, command (actual argv list), started_at, completed_at, returncode=0, log reference. Record from actual execution, never fictional successful runs. Distinct IDs alone do not suffice: command/time/log fingerprints and execution order are checked. Regression identity differs from execution identity. Logs contain actual assertions/results; the independent reviewer checks their meaning. Synthetic fixtures test the verifier but do not prove a real actor performed a full Bye.

Observation JSON: observation_id, observed_at, valid_until, value_sha256, checker_sha256, result=PASS. It records actually checked external/non-file state using safe normalized hashes, never credentials. Refresh can retain value hash with a new time; changed value/checker invalidates dependencies. Files detect content changes, inventories new/deleted paths, observations expiry. Include all relevant kinds.

Seal returns DECLARED_SCOPE_CLOSEOUT_VERIFIED and an immutable reference under `.closeouts/<lane-stem>/`. Query input: schema_version, command, workspace, receipt, source_observation; optional observations may override only named observation dependencies. Output: VALID/STALE/BLOCKED, affected_ids, reasons, always new_round=false. Unknown schema/unpublished path is an input error. Missing sealed material is STALE; missing current source is BLOCKED. Fully reviewed administrative additions reuse receipt. Business additions use justified affects mapping, otherwise invalidate all; dependency closure expands affected work.

Never rewrite an existing receipt, reset failures or auto-reseal to suppress invalidation. Changing an old event review changes the covered prefix. Each query needs an actual native refresh; cached bytes with a new timestamp are not fresh source. Hook-only history stays HOOK_OBSERVED_ONLY; unknown history cannot become whole-conversation completeness.

Limits: native environment and evidence are trusted local integration inputs, not cryptographic protection against same-user tampering. An enum cannot prove semantic review. Helpers validate coverage structure, dependencies and publication; quality requires actual tests and independent review. Product readiness is separate.

Preserve the same Lane's unresolved product failures, accepted baseline and existing regression obligations even during documentation-only closeout. Execute regressions needed for the declared completion scope; missing required evidence prevents sealing that scope. Out-of-scope obligations stay explicitly open with ownership/continuation references. Scope boundaries do not erase failures or imply product readiness; do not take over other Lanes without authorization.

## Safe opt-out

Current native writer reviews latest prepare-resume, then `disable-daily --command '<resume>' --workspace '<workspace>' --expected-sha256 '<current SHA>'`. Only routing becomes legacy; checkpoint bytes, source objects, archives, scope and writer/version guards remain. Marker becomes muse-daily-v1-legacy-workflow. Full writes still need current SHA and unchanged source pointer. Do not delete marker, install old helpers or restore an old checkpoint. `enable-daily` with current SHA restores new routing. Unregistered Lanes remain unchanged.
