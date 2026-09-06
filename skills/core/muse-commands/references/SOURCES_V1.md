# Source coverage without replaying the full conversation

The canonical Lane checkpoint contains one `MUSE_SOURCE_LEDGER_V1: <hash>` pointer. It references immutable source/review objects under `memory/lanes/.sources/<checkpoint-stem>/`. An orphan object is not current. Normal save, claim and native full writes preserve this pointer; only `source-update` changes it under the same writer/version lock.

## Daily use

1. Resolve the exact Lane and native session. Fetch only new user-channel messages, with an overlapping known message ID when paging. Do not choose the latest same-cwd session. A native user-channel message can also be a controller delegation: record that origin; it does not create new human authorization.
2. Run `source-status --command '<resume>' --workspace '<workspace>'`. It returns a bounded pending list, counts, per-session observed cutoffs and missing-history/gap state. Review the next batch after classifying the current batch. `latest_certified=false` means a stored record never proves that no newer native message exists.
3. Import captured source with `source-update --input <json>`. Review every captured message's complete safe text, including mixed confirmation/new instructions. `received`, `executed` and `verified` are different. Preserve refusals and explicit supersedes. An executor's classification is not automatic execution/authorization proof.
4. Before a new action or a closeout-validity query, refresh the exact native tail. Missing, malformed, non-text, over-limit or unknown-version input stays pending/UNKNOWN. Continue only work that does not depend on that gap. Do not read an oversized raw log to clear a warning.
5. Use ordinary `/save` for actual progress; then continue the authorized objective. Internal milestones are not reasons to wait for another "next step" from the user.

## Update input

```json
{
  "schema_version": 1,
  "command": "/resume strategy Lane A",
  "workspace": "<actual workspace>",
  "expected": {"sha256":"<current checkpoint hash>","platform":"<current writer>","session_id":"<native writer session>","handoff_id":"<existing handoff>"},
  "captures": [{"kind":"codex_page","path":"<absolute projected page>","sha256":"<file hash>","session_id":"<exact selected native session>","request_cursor":null,"selection_ref":"<why this exact session belongs to the Lane>"}],
  "reviews": []
}
```

Use `kind: claude_hook` for a native prompt spool record. `captures` or `reviews` may be empty. Sources are capped per object/batch and content-addressed; repeated IDs with changed content fail. Equal messages with different native IDs remain different events.

A review has `event_id`, `text_sha256`, `reason`, and `parts`. Every part contains `start`, `end`, `kind`, `meaning`, `disposition`, `evidence` and `supersedes`. Offsets count Unicode characters in the safe text; ordered spans must cover the whole text without gaps or overlaps. Kinds: administrative, requirement, decision, question, context. Dispositions: administrative, received, executed, verified, answered, superseded, reference. Only genuinely administrative parts use administrative disposition. Optional `affects` names the related closeout obligation IDs; unknown impact conservatively invalidates all obligations. The executing agent must justify this mapping from the actual instruction.

## Codex Desktop capture

Use the existing `read_thread` tool with the exact `CODEX_THREAD_ID`, a small `turnLimit` and `includeOutputs:false`. In the tool orchestration code, immediately project only `schemaVersion`, thread id/kind/cwd, native page metadata, and each turn's id/status/timestamps plus `userMessage` items. Do not print or persist tool output, reasoning or agent text. Save the small projected JSON and the request cursor separately. The source importer rejects unknown schema, wrong session/workspace, modified IDs and broken page chains.

On the first import, page through `nextCursor` until the required anchor or `hasMore:false`. Existing history gaps remain explicit. Later refreshes begin at the native head and overlap the previous cutoff; if the previous cutoff is absent, follow the returned cursor until the original missing anchor is reached. Repeated refreshes must not replace that original anchor. A compaction summary is not raw source; only native user-message records enter this ledger. If the native tool is unavailable, retain UNKNOWN and a clearly partial source note.

## Claude capture

The native `UserPromptSubmit` hook runs `muse-source-hook.py`. It stores a redacted prompt, exact session ID and native prompt ID under `<role-home>/memory/.muse-source-inbox/<sha256(session_id)>/`. Use the specific session directory and inspect its small records; do not read another session or pick a latest same-workspace transcript. The hook never blocks the prompt or calls a model. Verify the actual record exists before claiming capture.

Recent native versions supply `prompt_id`; retries of that ID are idempotent. If it is absent, the helper preserves separate observed invocations instead of collapsing equal user messages. Such capture has weaker retry identity. Hook observations prove the captured prompts only; they cannot prove that an earlier hook ran or that pre-installation history was complete. SessionStart still supplies native writer identity independently. Both hooks are enhancements: explicit command/phase saves remain the fallback.

The shared user/project installation invokes `--registered-only`: capture when the native session is an active daily Lane's current Claude writer, or the prompt begins with an explicit single-role `/resume` selected by the global daily-v1 policy, including first-time/new Lanes. Guarded legacy opt-out and unrelated prompts before claim are ignored. A new session's initial non-resume prompt before claim can therefore be absent; retain that gap rather than asserting capture. The unfiltered mode is for explicitly isolated verification only. Existing SessionStart and unrelated settings/hooks are preserved.

Native source: [Claude hook input contract](https://code.claude.com/docs/en/hooks#common-input-fields). Actual installed behavior is verified in the release evidence; documentation alone is not an execution result.
