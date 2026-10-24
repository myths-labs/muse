# Relay runbook (example)

Copy to the path set as `relay_runbook` in `.muse/orchestration.json` and edit. Sessions
cannot move between accounts; files on this machine can. This runbook says how to switch
and holds the snapshots each lane writes with `/handoff save`.

## Lanes

| Lane id | Session title | Working directory | Model / effort | First line in a new session |
|---|---|---|---|---|
| orchestrator | Orchestrator | `.` | strongest available | `/handoff orchestrator` |
| build | Build lane | `.` (new worktree) | strongest available | `/handoff build` |
| verify | Verification lane | `.` | strong | `/handoff verify` |

## Before the switch (orchestrator)

1. At the save line (weekly exhaustion within 20 minutes or weekly ≥ 95%), send every
   lane "Global save: run /handoff save, then keep working until the wall".
2. Check that every lane below has a snapshot newer than the global save.
3. Tell the user: "snapshots written; switch accounts at the wall".

## At the switch (user)

1. Sign out, sign in with the next account.
2. Open one session in the orchestrator's working directory and paste:
   `/handoff orchestrator, then reopen build and verify`.
3. Re-authorise the browser extension and per-session connectors where needed.

## Relay snapshots

<!-- Each /handoff save appends one entry below. The newest entry per lane wins. -->

### Relay snapshot · orchestrator · YYYY-MM-DD HH:MM (global save)
- Main: <commit>  Production: <version>  Gate: <n>/<total>
- Doing: …
- Next: …
- Waiting for the user: …
