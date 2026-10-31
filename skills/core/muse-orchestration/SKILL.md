---
name: muse-orchestration
description: Run several long-lived AI coding sessions ("lanes") as one team led by an orchestrator lane. Covers account relay when usage runs out (/handoff save, /handoff <lane>, /handoff status), away mode (/away and /back, aliases /托 and /回), /boot, orchestrator timers (patrol, quota sentinel, twice-daily reports), memory recall and audit tools, Stop-hook guards and optional Obsidian vault writes. Use when a project runs parallel sessions, must switch accounts at a usage wall, or leaves agents working while the user is away.
---

# MUSE multi-lane orchestration

Optional layer on top of `muse-commands` continuity. A single-lane project needs none of
it: `/save`, `/resume` and `/bye` stay the same. Read only the reference for the current
action.

## Configuration

`.muse/orchestration.json` in the project (template `templates/orchestration.example.json`,
keys in `references/CONFIG.md`). It names the orchestrator and the user's own lanes: id,
title, checkpoint file and required reads. MUSE ships no fixed lane names and no
author-machine paths; tools without a configured path report it as unconfigured instead
of guessing. `python3 -I scripts/orchestration_config.py` prints what was resolved.

## Commands

| Command | Workflow | Use |
|---|---|---|
| `/handoff save` · `/handoff <lane id>` · `/handoff status` | `.agent/workflows/handoff.md` | Account relay: save before the switch, continue under the new account |
| `/away` (`/托`) | `.agent/workflows/away.md` | User leaves; decide what can be decided, queue the rest |
| `/back` (`/回`) | `.agent/workflows/back.md` | User returns; deliver the return list, ask once |
| `/boot` | same as `/resume` | Alias for restoring a role or lane |

## Roles

- **Orchestrator** (总管): the user's single entry point; board, dispatch, follow-up,
  reports, account relay; does not write product code by default.
  `references/ORCHESTRATOR.md` (rules), `references/ORCHESTRATOR_CRON.md` (timer prompts).
- **Lanes**: whatever the project defines (for example build, verification, design).
  Each owns its checkpoint, reports to the orchestrator and messages other lanes directly.

## Working mode (3.9)

Sessions run on automatic compaction and rolling checkpoints. A session is replaced only
for an account switch, a confused session, or a long idle wait with a large context;
never because its context reached a percentage. Parallel work inside a lane goes to that
lane's subagents, not to extra sessions. Full test suites run in CI or on a remote
runner, not on the local machine. `/handoff save` writes only the checkpoint, the relay
snapshot and the user's new decisions; the orchestrator runs vault and memory maintenance
once a day with the evening report. See `references/ACCOUNT_RELAY.md` and
`references/ORCHESTRATOR.md`.

## Tools (`scripts/`, Python 3 standard library, read-only unless stated)

| Script | Purpose |
|---|---|
| `recall.py <word> <synonym> …` | Search every memory directory and checkpoint before saying "not in my records" |
| `memory_audit.py [--sync]` | Audit memory indexes, cross-directory visibility, decision backlog, vault freshness, key patterns; `--sync` writes cross-directory blocks |
| `negative_claim_guard.py` | Stop hook: blocks a negative memory claim made without running `recall.py` |
| `licence_stop_guard.py` | Optional Stop hook encoding a policy: a licence is one line of fact, not by itself a reason to skip evaluation |
| `vault_coverage_check.py` | Every owner quote and tracked id in a checkpoint range exists in the vault |
| `vault_freshness.py` | The vault was written recently |
| `wall_recover.py` | After an unsaved wall, list the old session's unfinished subagents |

Usage, exit codes and hook installation: `references/TOOLS.md`. Vault formats:
`references/VAULT.md`. Relay mechanics: `references/ACCOUNT_RELAY.md`.

## Boundaries

Roles, approvals and receipts never widen authority. Deployments, production data
changes, payments, external messages and deletions still need the user's explicit
consent in the current session. Never open or print `.env*` or credential files. Write
times from `date`, not estimates. A tool PASS is not product QA.
