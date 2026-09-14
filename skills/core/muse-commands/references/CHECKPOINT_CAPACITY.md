# Checkpoint capacity and evidence storage

Use this guidance with the installed `save.md` workflow and
[daily save input contract](DAILY_V1.md). It describes the existing incremental
save limits; it does not change storage policy or add automatic history compaction.

## Keep the limits separate

The incremental runtime caps each input JSON, selected source file, canonical
checkpoint and proposed rendered checkpoint at **262,144 bytes (256 KiB)**.
Measure UTF-8 bytes, including metadata and Markdown separators, rather than
characters or tokens. A rendered checkpoint over this limit is refused before
the save creates an archive or publishes a new canonical checkpoint.

The default 16 MiB Git-content recovery budget and `full-scope-batches-v1` govern
workspace evidence. A complete Git scan does not increase checkpoint capacity or
prove that a proposed save fits.

## Prepare a bounded save

1. Keep detailed new validation in evidence artifacts. Use a small source note or
   evidence index that records the actual decision, result, failure and next step,
   with precise references to the retained evidence. The selected source/index
   file must itself fit the 256 KiB read limit; reference larger logs instead of
   passing them as the source input.
2. Append only necessary new facts and evidence pointers. Only `Next Action` and
   `Required Reads` may be replaced. Preserve historical sections, decisions,
   constraints, unresolved issues, source coverage, writer and handoff identity.
   Replacing current pointers does not authorize deleting their retained evidence.
3. Check the proposed rendered size before saving, not just the current file or
   delta size. Use the official guarded save with the reviewed checkpoint and
   source hashes and the actual native writer. Do not edit canonical state by hand.

## Handle `TOO_LARGE`

Retain the failed input, stdout and stderr, the selected source evidence and the
canonical hash. Read back the canonical checkpoint to establish whether it changed;
a failed command or a leftover archive directory is not a successful save receipt.

Review the current checkpoint, source and native writer before refreshing their
expected hashes. Narrow repeated prose in the proposed delta to evidence pointers,
or replace the two supported current-pointer sections while preserving the history
and evidence they refer to. Then retry through the official guarded save.

For `SAVED`, verify the returned hashes against the canonical readback and the
archive's `before.md`, `after.md`, `input.json` and `source`. `UNCHANGED` is a no-op
and does not create a new archive. An uncertain write requires inspection of the
canonical state and prepared receipt; never restore an old file over newer work.

If supported replacements still cannot fit, retain the unsaved evidence and raise
a separate storage/migration design review. Do not increase limits, delete
historical sections, change writer identity or claim that saving succeeded. Short
pointers are a bounded operating practice, not an unlimited history solution.

## Future storage changes

A storage-policy change needs a near-limit successful save, an over-limit refusal
with an unchanged canonical checkpoint, complete receipt/readback verification and
recovery of retained decisions and evidence. Run the relevant real workflows;
passing full-scope Git recovery is separate evidence. This guidance alone does not
establish that a storage change or a user's product has passed acceptance.
