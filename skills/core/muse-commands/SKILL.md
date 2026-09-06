---
name: muse-commands
description: Run MUSE /resume, /save and /bye for continuous work in Codex or Claude Code, preserving the selected role, Lane, decisions and source evidence across sessions.
---

# MUSE continuity commands

Read only the workflow needed for the current action. The installed shared runtime
is `.agent/skills/muse-commands`, its workflows are `.agent/workflows`, and project
configuration is `.muse/config.json`. Paths in this guide are relative to the
installed project; use the absolute resolved script path when the shell cwd differs.

## User interaction

The user may say `continue`, `/resume strategy Lane A`, `/save`, or `/bye`.
The agent derives the goal, acceptance checks, constraints and next action from
the request, shared role record and relevant checkpoint. Do not require the user
to fill a goal/acceptance/constraints form. Do not change role based on cwd,
provider or project. A project may have Strategy implement work directly; respect
its policy. Do not introduce a Strategy-to-Build handoff unless actually requested.

Keep the same Lane by default. Use a new logical Lane only when independent scope
or continuation warrants it within user authorization; changing provider or
reaching a context threshold does not create one. A new app task is separate and
requires user intent. Do not silently reopen a CLOSED Lane; first read its explicit
reopen conditions. A missing checkpoint does not prove an old task is new.

## Dispatch

Use `bash .agent/skills/muse-commands/scripts/muse-doctor.sh` as the helper prefix.
It never calls a model or executes product tasks by itself.

1. On `/resume`, run `parse-resume '<exact command>' '<workspace>'` and lock the
   returned role_home/role/Lane. Run `resume-workflow --command '<exact command>'
   --workspace '<workspace>'`, then read only the returned daily or legacy workflow.
2. On ordinary save, read `.agent/workflows/save.md`; use `save-daily`, not full Bye.
3. On explicit Bye, select `bye-workflow --command '<locked resume>' --workspace
   '<workspace>'` and follow that workflow. A valid unchanged closeout receipt can
   be checked; changed requirements/evidence or failing gates must be addressed.
4. Other commands use `resolve /<command> '<workspace>'` and the returned workflow.

## State and identity

`memory/lanes/<role>-lane-<name>.md` under the configured role home is canonical.
Schema1 is retained. The provider/session is a writer identity, not the role.
Use helpers to update state; do not hand-rewrite checkpoints or bypass markers.
Before writing, verify the expected hash, native writer and current workspace.
New writers review and explicitly claim/adopt; old writers are rejected. Do not
reuse another session ID, fabricate a native ID, or clear environment guards.

Read `references/DAILY_V1.md` for save/claim fields and
`references/ONBOARDING_V1.md` for reviewed initialization and legacy adoption.
Read `references/SOURCES_V1.md` for native source import/review and
`references/CLOSEOUT_V1.md` before formal closeout.

## Context and evidence

Save meaningful deltas and at least every ten interaction rounds if there are
unsaved changes. At observed 80% pressure, save, compact if available, verify the
current Lane and continue. If occupancy is unavailable, say UNKNOWN; cumulative
tokens and model specifications do not establish current occupancy. After
compaction, load the checkpoint and necessary evidence rather than full Boot.

Source coverage is not guaranteed. Missing native messages remain unknown; a
partial source note does not prove complete transcript coverage. A hook exit0,
hash, successful save or successful compilation is not product QA. Verify the
actual user flows relevant to the changed scope before claiming completion.

Use the installed `doctor` for configuration/files preflight, not as a QA verdict.
