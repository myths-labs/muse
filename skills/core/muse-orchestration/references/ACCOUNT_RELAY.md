# Account relay

`/handoff` (workflow `.agent/workflows/handoff.md`) moves a team of lanes from one AI
account to another when usage runs out. Sessions cannot move between accounts, but
everything they need is on the local machine: checkpoints, the board, the relay runbook,
memory directories, worktrees and local scheduled tasks. A new session under the new
account reads the files and continues.

## Why save early but switch late

Two failure modes shaped the rules:

- **Everyone hits the wall at once.** In one recorded case every lane resumed together
  after a reset and dispatched dozens of subagents; weekly usage went from 79% to 100% in
  34 minutes and all lanes hit the wall within 30 seconds. Nobody had saved, because the
  only trigger was a fixed percentage read by a patrol that was busy at the time.
- **Saving too early wastes the account.** A fixed 85% trigger left real capacity unused.

So the save line is a forecast, not a fixed percentage:

```
burn per minute      = (weekly % now - weekly % at previous reading) / minutes between
minutes to exhaustion = (100 - weekly % now) / burn per minute
save when minutes to exhaustion <= 20  or  weekly % >= 95
```

`/handoff save` took 3–5 minutes per lane when measured, and a sentinel every 10 minutes
still sees the line with at least 10 minutes left. At the fastest burn observed
(0.62 points/minute) 20 minutes is about 12 points, so the earliest save lands near 88%;
at a typical 0.3–0.4 points/minute it lands near 92–94%. After saving, lanes keep working
until the wall and switch only then; they keep their rolling checkpoints current in the
meantime.

Short windows (for example a 5-hour window) reset on their own without a new account, so
they never trigger a global save. Each lane relies on its rolling checkpoint and keeps a
one-shot self-resume timer at reset + 1 minute. A lane once deleted its own timer, hit the
short wall and sat idle for two hours because nothing woke it.

## Rolling checkpoints

Each lane updates its checkpoint's "current state" whenever it dispatches or collects a
batch of subagents and whenever it closes a package: which subagents and branches are
running, the next step, who it is waiting for. Before re-dispatching ten or more subagents
at once (after a wake-up or a switch), write the checkpoint first.

## Switching accounts (the user, about 2 minutes)

1. Sign out of the client and sign in with the next account.
2. Open one session and paste one line: `/handoff orchestrator`, plus the list of lanes to
   reopen. The orchestrator opens the other lanes itself where the client allows it, or
   gives the user one first line per lane from the relay runbook.
3. Re-authorise anything that follows the account rather than the machine: the browser
   extension's sign-in and any per-session connectors (databases, hosting) in the
   sessions that need them.

The new orchestrator checks the plan first: a much smaller plan reaches the short wall in
minutes with every lane open, so it asks the user before opening the rest.

## When the wall came before the save

`wall_recover.py <old session id> --since <last checkpoint time>` reads the old session's
local transcript (read-only) and lists the subagents that were running after that time,
whether the parent received their completion notices, and each one's last words. Tool
results are never printed. Find the old session id by modification time and title under
the client's local projects directory. Write the result into the lane checkpoint, then
re-dispatch only the unfinished work.

## What survives and what does not

| Survives the switch | Lost with the old account |
|---|---|
| Checkpoints, board, relay runbook | Running subagents and background jobs |
| Memory directories | Addresses between sessions (list sessions again) |
| Worktrees and progress files | Session timers |
| Local scheduled tasks | Browser extension connection and per-session connectors |
| Browser and CLI sign-ins | |

Old sessions remain listed under their titles. Rename them "retired, do not message" or
archive them, after detaching any live session they started.

## Snapshot format

The relay runbook ends with a "Relay snapshots" section. Each `/handoff save` appends one
entry; the newest entry per lane wins (see `templates/RELAY_RUNBOOK.example.md`):

```
### Relay snapshot · <lane id> · YYYY-MM-DD HH:MM (<trigger: global save / context 70% / final>)
- Doing: …
- Next: …
- Waiting for: …
- Unsaved or uncommitted: … (branch / file)
- Running subagents: … (progress file paths)
```

The orchestrator's entry also records the main branch commit, the production version and
the decisions waiting for the user.
