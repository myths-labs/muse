# Orchestrator timers

Session timers live only inside a session. Every new orchestrator recreates them from
this file on takeover and writes the job ids into its checkpoint. Edit the prompts here
first, then recreate the timers, so the wording does not drift across handoffs.

Paths below use the installed layout. `$SCRIPTS` is
`.agent/skills/core/muse-orchestration/scripts`; `$CHECKPOINT`, `$BOARD`, `$LOCK` are
`orchestrator.checkpoint`, `board.status_glob` and `heavy_lock` from
`.muse/orchestration.json`. Avoid minute :00 and :30.

| Timer | cron (local time) | Prompt |
|---|---|---|
| Patrol | `13,43 * * * *` | "Patrol" below |
| Morning report | `2 7 * * *` | "Report" below, with "morning" |
| Evening report | `57 20 * * *` | "Report" below, with "evening" |
| Quota sentinel | `4,14,24,34,44,54 * * * *` | "Quota sentinel" below |
| Tight sentinel (weekly ≥ 85% only) | `2-59/5 * * * *` | "Quota sentinel" below |
| Self-resume (every lane, one-shot) | short-window reset + 1 minute | "Continue from the last line of your progress file." |

## Quota sentinel

> [Quota sentinel] Do only these steps; no subagents, no other files. Run `date`. Read
> account usage (plan, short window %, weekly %). Compare with the previous sentinel or
> patrol reading in `$CHECKPOINT`: weekly burn per minute and minutes to exhaustion
> (remaining points ÷ burn; burn 0 → "will not hit"). Read machine load (`uptime`, swap
> usage, memory pressure such as `memory_pressure`, top processes by resident memory);
> load guard tripped (free swap below the threshold and memory pressure below its
> threshold, or load above its threshold; `ORCHESTRATOR.md`, "Shared machine") →
> identify the lane owning the largest process and ask it to pause at its next safe
> point. Save line: weekly exhaustion within 20 minutes, or weekly ≥ 95%, whichever comes
> first → the first time in this cycle, message every lane "Global save: run /handoff save, then keep
> working until the wall; no deployments or production data windows while critical",
> run /handoff save yourself and tell the user "snapshots written; switch accounts at
> the wall". Already sent → only check that every snapshot is written. Weekly ≥ 85% →
> if no tight sentinel exists, create one with this prompt; delete it after the switch
> or when weekly falls below 85%. Short window: record only, never send a global save.
> Nothing triggered → append one line to `$CHECKPOINT`: "- sentinel HH:MM: short x%,
> weekly y%, burn z/min, n min to exhaustion; load a, free swap b GB, free memory c%".
> Timers fire only while the session is idle; if you are busy for more than 20 minutes,
> read usage yourself.

## Patrol

> [Orchestrator patrol] Run `date`. Dispatch one small read-only subagent (no edits,
> never open `.env*` or credentials) to return raw results:
> (0) whether every path in `removable_roots` is a real mount point (offline → do not
> mount, repair or write there; skip steps that need it and write "offline");
> (1) the current production version from your deployment tool, read-only;
> (2) the main branch tip and its latest CI runs;
> (3) open pull requests: total, failing checks, conflicts, newly green;
> (4) the content of `$LOCK`;
> (5) stalled list: rows in `$BOARD` (last line per id wins) whose status is in progress,
> open for review, not started or blocked and whose newest dated note is at least
> `board.stale_days` old (read every date format the notes use, such as `M/DD` and
> `YYYY-MM-DD`, and take the latest): id, status, date, first 60 characters of the note.
> Then yourself: ask each stalled row's owner "where is it stuck, who does it, when will
> it land"; a row stalled two patrols in a row goes to the user as one line with a
> recommendation. Memory audit and vault checks are not part of the patrol; they run once
> a day in the evening report. Read machine load as in the sentinel. Read usage and apply
> the save line as in the sentinel. Chase anything stuck for more than 30 minutes. Wake
> after the wall: idle lanes whose last turn hit a usage limit with no activity since →
> send "window reset, continue from the last line of your progress file"; a lane that
> saved because it expected more than 60 minutes idle with more than 300k tokens of
> context is not woken: have a fresh session take over from its checkpoint and run
> `wall_recover.py`. Idle dispatch: while weekly usage is below 100%, idle lanes that
> ended normally get their next task that waits on nobody (commit or write to disk at
> each step, work until the wall); none → write "idle: <lane> has nothing dispatchable
> (reason)". Append one line to `$CHECKPOINT`: "- **Patrol HH:MM**: production …; main …;
> PRs …; stalled …; load …; usage short/weekly …; context …". If nothing needs the user,
> do not message the user. Do not hand off by context percentage: at about 80% context
> update your checkpoint incrementally and keep working.

## Report

> [Orchestrator morning report] (or evening) Run `date`. Dispatch one small read-only
> subagent to collect: board status counts; ids that became verified since the previous
> report (the time of the previous "report points" section in `$CHECKPOINT`); the gate
> count from the verification lane's index; the production version; pull requests merged
> since then. Then write to the user, plain language, conclusion first: (1) newly verified
> items and the gate count; (2) what is live and what users can notice; (3) at most three
> decisions for the user, each with a recommendation; (4) one line of things only the user
> can do. Write the same points as a new section "MM/DD HH:MM morning report points" in
> `$CHECKPOINT` and, with a vault configured, append them to the vault's daily note under
> "## Orchestrator morning report HH:MM" (append only). Evening report only: also do the
> daily maintenance (`ORCHESTRATOR.md`, "Daily maintenance"). With a vault configured,
> append each lane's section and the day's new user decisions to the vault, then run
> `python3 -I $SCRIPTS/vault_coverage_check.py --from <last checked line + 1>`; GREEN →
> write "vault checked to line N GREEN"; RED → add each missing item verbatim to that
> day's vault note (non-quotes go into the skip file with a reason) and rerun to GREEN.
> Run `python3 -I $SCRIPTS/memory_audit.py` (read-only, last line RESULT GREEN/RED);
> write GREEN or RED with failing items and send gaps to the lanes that own them (the
> report itself never edits memory; when only the cross-directory block is stale, run
> `--sync` yourself as a separate command). Put both results into the report points.

## Timer hygiene

- Restarting the desktop app keeps a session's timers; switching to a new session or
  account does not. Recreate them on every takeover.
- Recurring timers in some clients expire after a fixed number of days; recreate them
  when the checkpoint shows they expired.
- A retired orchestrator deletes its own timers before retiring; otherwise an app restart
  revives them and wakes the old session. When a new orchestrator sees a retired session
  turn busy, it checks whether a stale timer woke it.
- When every lane is stopped waiting for a reset, the orchestrator may delete the patrol
  and sentinels, keep the reports, and add one one-shot timer at reset + 1 minute that
  recreates them and runs a patrol at once. Never do this while any lane is working.
