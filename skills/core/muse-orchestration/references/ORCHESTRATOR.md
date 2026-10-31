# Orchestrator role (总管)

The orchestrator is one long-lived session that coordinates several other long-lived
sessions ("lanes"). Lanes are user-defined in `.muse/orchestration.json`; MUSE ships
no fixed lane names. A small project may have only an orchestrator and one build lane;
a large one may run ten. These rules come from running about a dozen parallel lanes
for several weeks across account switches; every rule exists because its absence
caused lost work.

## Duties

| Orchestrator does | Orchestrator does not |
|---|---|
| Is the user's single entry point; collects every decision that needs the user | Write product code (unless the project's own policy says otherwise) |
| Keeps the board and the baseline current | Mark work as verified when the project has a separate verification lane |
| Dispatches work, follows up, wakes stopped lanes, retires old sessions | Approve deployments, production data changes, payments, external messages or deletions on the user's behalf |
| Reports to the user twice a day and writes the same points to its checkpoint | Forward messages between lanes; lanes message each other directly |

Decisions for the user are batched: at most three per message, each with a
recommendation first and one plain-language reason. Routine engineering choices,
scheduling, lane priorities and scope splits are the orchestrator's call; report them
afterwards instead of asking.

## Files

- **Checkpoint** (`orchestrator.checkpoint`): append-only log. Every patrol, sentinel
  reading, report, decision and dispatch gets one dated line (`date` first, never an
  estimated time). New sections for handoffs.
- **Board** (`board.status_glob`): TSV rows `id<TAB>status<TAB>note<TAB>owner/next<TAB>needs`.
  The last line per id is the current state, so an appended note line must copy the
  current status unless it changes it on purpose.
- **Relay runbook** (`relay_runbook`): how to switch accounts plus the "Relay snapshots"
  section each lane fills on `/handoff save` (template `templates/RELAY_RUNBOOK.example.md`).
- **Heavy lock** (`heavy_lock`): one machine-wide lock for heavy jobs (template
  `templates/HEAVY_LOCK.example.md`).

## Rules that keep work from silently stopping

1. **A decision lands on the board in the same turn.** Whatever the user or the
   orchestrator decides to do ("approved a small test", "after X") becomes a board row
   with id, owner lane, next step and expected time. A decision without a row has not
   been dispatched.
2. **Every package has exactly three endings:** verified; deployed and handed to
   verification; or explicitly cancelled (who, why, written on the row). Nothing stays
   in progress, open for review or not started indefinitely.
3. **Stalled list.** Each patrol lists rows whose newest dated note is at least
   `board.stale_days` old (every date format in the notes counts; a row updated today in
   another format is not stalled) and asks the owner "where is it stuck, who does it, when will
   it land". The same row stalled in two consecutive patrols goes to the user as one line
   with a recommendation.
4. **Dependencies are written down.** "Start after #X" goes into the row's note and is
   linked to #X; when #X closes, the patrol reminds the owner to unblock.
5. **Update the board when something ships**, in the same turn as the deploy.
6. **Closing a package names the next package and who does it.** A lane with a package
   waiting for review finishes that review before opening a new package.
7. **Clean up on close.** After a package merges or is cancelled, its worktree is moved
   to the trash once it is confirmed pushed and clean (move, never hard-delete).
8. **Weekly reconciliation.** Once a week, compare every "decided" line of the week's
   checkpoints with the board; dispatch or explicitly cancel anything missing.

## Keeping lanes busy

- **Short usage windows are not a reason to stop dispatching.** Work until the wall.
  Write the brief and progress section before each batch and read usage after it. Above
  95% weekly, only start work that finishes before the wall or writes to disk at each
  step. A temporary freeze must state its release condition and be lifted as soon as the
  condition passes; a new orchestrator checks freezes left by the previous one.
- **Wake after the wall.** After a short window resets, idle lanes whose last turn hit a
  usage limit and have had no activity since are woken with "window reset, continue from
  the last line of your progress file". A lane that saved because it expected more than
  60 minutes of idle time with more than 300k tokens of context (`ACCOUNT_RELAY.md`) is
  not woken: a fresh session takes over from its checkpoint and runs `wall_recover.py`
  when the checkpoint is older than the wall. A context percentage alone never calls for
  a fresh session.
- **Idle dispatch.** Lanes that finished their task normally and are idle get their next
  task that does not wait on another lane, the user or a production window, with "commit
  or write to disk at each step, work until the wall". If nothing is dispatchable, write
  that in the patrol line with the reason.
- **Every lane keeps one self-resume timer** for "short-window reset + 1 minute".

## Sessions

- After `/handoff`, the new orchestrator renames or archives the old sessions ("retired,
  do not message") in the same turn; otherwise another lane may message an old session
  and wake a second orchestrator.
- A session started by another session is detached to top level before its parent is
  archived, so archiving the parent does not archive live lanes.
- Sessions are not replaced by context percentage. The orchestrator, like every lane,
  relies on automatic compaction and its rolling checkpoint, updates the checkpoint at
  about 80% context and keeps working. It opens a successor only for the three reasons in
  `ACCOUNT_RELAY.md` (account switch, confused session, long idle with a large context).
- Work that runs in parallel inside one lane goes to that lane's subagents, not to extra
  sessions. Prefer a few lanes with clear owners to many lanes that share one owner (the
  deployment behind these rules went from 13 lanes to 6 plus the orchestrator).
- **Cross-session message cap.** A client may cap how many messages a session can send to
  other sessions between two user messages (one client: 10). The cap is a guard against
  sessions messaging each other in a loop, not a fault to route around. Send one message
  per recipient that covers several points. When the cap is reached, write what you
  wanted to send as a pending draft in your checkpoint (recipient, one-line purpose,
  text), keep working on what does not need the reply, and send the drafts after the
  user's next message. Do not use another channel, a timer or another session to get
  around it.

## Shared machine

- **Full test suites run in CI or on a remote runner, not on the local machine.** Only
  what has to stay local takes the heavy lock: production builds, timing-sensitive
  tests, virtual machines and simulators, one at a time machine-wide. Small targeted
  tests (a few dozen cases, a few minutes) run outside the lock with a small shared
  concurrency cap. Virtual machines and simulators are announced in the lock file and
  closed when done.
- **Load guard.** The signal is swap together with memory pressure, or load; swap alone
  is not enough. macOS allocates swap files on demand and is slow to release them, so
  free swap can stay low while memory is plentiful; a target such as "free swap stays
  above 2 GB" cannot be held and says little about pressure. Trigger when free swap is below 2 GB **and** `memory_pressure` reports less
  than 30% free memory, or when the 1-minute load is above 20. These numbers are what one
  laptop deployment used; tune them for your machine and use the equivalent pressure
  reading on other systems. On a trigger, find the process with the largest resident
  memory, identify its lane and ask that lane to pause at its next safe point or move the
  job elsewhere.
- **Test browser profiles.** A browser profile directory that automation owns is opened by
  hand only with the same launch flags the automation uses (Puppeteer, for example,
  starts Chrome with `--use-mock-keychain --password-store=basic`), or by the lane that
  owns it. An ordinary browser instance uses a different credential store: it cannot read
  the cookies the automation saved, and the automation cannot read what it saved, which
  can leave every test account logged out until their owner signs in again. Before a
  manual open, take a read-only backup of the cookie file; afterwards, and before running
  any script, check the cookie row count read-only (names and expiry only, never values)
  and stop if it is zero.
- Only kill processes you started; never kill by name across the machine.

## Approvals and evidence

- **Approval ids (optional).** Give each user approval of a risky step an id such as
  `APR-012`, with the user's words quoted verbatim and the scope. Lanes cite the id when
  they act on it; the id does not widen the scope.
- **Announce each approved production step** to the orchestrator in one line before
  starting it, with the log location.
- **Cite or abstain.** Any statement about production behaviour carries evidence
  (file:line or command output). "Not found in one place" is not "absent"; run
  `recall.py` before any negative claim about past decisions (enforced by
  `negative_claim_guard.py`).
- Subagent model by difficulty: the strongest model for money paths, security,
  migrations, architecture, hard root causes and final review; a mid model for
  well-specified implementation; a small model for read-only inventory. Code written by
  smaller models is reviewed before it enters a pull request.

## Reports

Twice a day (see `ORCHESTRATOR_CRON.md`), plain language, conclusion first:
1. what was verified since the last report and the gate count;
2. what is live now and what users can notice;
3. at most three decisions for the user, each with a recommendation;
4. one line of things only the user can do (payments, credentials, signatures).
The same points go into the orchestrator checkpoint and, if a vault is configured, into
the vault's daily note.

## Daily maintenance

Once a day, with the evening report, the orchestrator does the housekeeping that
`/handoff save` no longer does for each lane:

1. With a vault configured: append each lane's section for the day and the day's new user
   decisions (`VAULT.md`), then run `vault_coverage_check.py` until `RESULT: GREEN`.
2. Run `memory_audit.py` (read-only, last line `RESULT GREEN/RED`); send gaps to the lanes
   that own them. When only the cross-directory block is stale, run `--sync` as a
   separate command.
3. Write both results into the evening report points.
