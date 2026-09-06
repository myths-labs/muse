---
name: context-health-check
description: Check actual session context observations; save and reassess after compaction without forcing Bye or guessing model limits.
---

# Context health

Use metrics exposed by the current client for the exact current session. Record
observation time and limitations. Model specifications, user preferences, cached
or cumulative token totals do not establish current context occupancy. A recent
request input is an observation, not a prediction of remaining space.

If reliable metrics are unavailable, report UNKNOWN. Do not estimate occupancy
from turn counts, source-file sizes, model names, or an old static model table.

At observed 80% pressure, save meaningful current-role/Lane deltas, reduce the next
read batch, compact if the client supports it, verify the current checkpoint and
continue the same work. A percentage alone never triggers full Bye, a new Lane,
or a new conversation. After compaction, obtain a fresh observation; prior counts
are stale. Compaction does not prove that all memory survived.

Preserve decisions, user corrections, constraints, unfinished failures, relevant
evidence and the next action. The agent fills the save fields; the user need not
write a template. Save at least every ten interaction rounds if changes remain
unsaved. Only a legacy session without a Lane uses CRASH_CONTEXT.md; never
replace another Lane's state.

Stop for an actual inability to continue, failed recovery, unresolved critical
state contradictions, or an explicit user handoff request. Save confirmed facts
and state what is missing. Do not represent partial recovery as a complete Bye.
