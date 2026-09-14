# Continuous work with MUSE 3.7.1

New to MUSE? Read the [beginner guide](QUICKSTART.md), then follow the setup instructions below.

MUSE keeps role/Lane checkpoints in your project so Codex and Claude Code can each
continue the same work. Use one client, switch clients, or use different Lanes for
independent work. Provider choice does not change your role. MUSE combines a
Python runtime with Markdown skills; local macOS/Linux with Python 3.7+
and Git are supported. Native Windows and network filesystem durability are not
certified by this release.

## Install or upgrade

From a MUSE checkout:

```bash
bash scripts/install.sh --tool codex --target /path/to/project
bash scripts/install.sh --tool claude --target /path/to/project
```

Install only the client you use, or both against the same project. Core and toolkit
skills remain the default; add `--core-only` to omit toolkit. Your existing
AGENTS.md/CLAUDE.md are retained with a small MUSE routing block; skills load on
demand rather than being concatenated into the entry file. Claude settings and
existing hooks are merged. Restart the client if it does not discover newly added
skill directories. Python can be selected with `MUSE_PYTHON=/path/to/python3`.

The command returns `receipt_path`. Known original 3.5 workflows are backed up and
upgraded. Unknown edits in managed runtime/workflow paths stop installation before
overwriting them; review and reconcile those edits, then rerun. Installation does
not adopt, initialize or modify your Lane checkpoints.

## Check the Python environment

Version 3.7.1 adds an optional check of the Python environment a workflow actually
uses. It reports the selected runtime under isolation, so packages visible only
in an ordinary shell do not produce a misleading success. Ordinary saves and
recovery still use the Python standard library.

For workflows that explicitly need image decoding, the same check can verify and
fully decode both PNG and JPEG fixtures. Pillow is optional and is not installed
with MUSE. This check does not add native attachment support or replace testing
the affected workflow. Ask the agent to follow the installed
[runtime dependency guide](../skills/core/muse-commands/references/RUNTIME_DEPENDENCIES.md),
then rerun the real workflow with the same interpreter.

## Daily use

| What you want | Say |
|---|---|
| Continue in this conversation | `continue` |
| Recover an existing role and Lane | `/resume strategy Lane A` |
| Save progress and keep working | `/save` |
| Formally close out the declared work | `/bye` |

These may be ordinary messages in Codex; a custom native slash menu is not required.
If necessary explicitly invoke `$muse-commands` in Codex or `/muse-commands` in
Claude, followed by the requested action. The agent writes the objective,
acceptance checks, constraints and helper inputs from the actual request and
saved evidence. You do not need to fill a handoff template.

Use the role that your project has chosen. If Strategy directly develops the
product, keep using Strategy. Build remains available for projects that want it;
technical work does not force a role switch. Default to the same Lane. Create a
new one only for independently continuing scope, not for every stage or model
change. A logical Lane does not automatically create a new client conversation.

## Switch clients or recover an interrupted session

1. If possible, `/save` in the current client and stop that writer's work.
2. In the receiving client, resume the exact same role/Lane.
3. The receiving agent checks the checkpoint, current workspace, source gaps and
   unfinished obligations, then explicitly adopts/claims it. Stale writers cannot
   save over the new owner through the MUSE helpers.

You do not need a full Bye merely to switch. If the old client crashed or never
performed Bye, the agent recovers saved state and checks uncommitted work. Missing
old records are not replaced with an empty new Lane. If the Lane itself is CLOSED,
resume may read it but work only restarts under its recorded reopen conditions.

At actual observed 80% context pressure, save, compact if the client supports it,
verify current state and continue. If occupancy is unavailable, report UNKNOWN.
Automatic compaction is not proof that every detail survived; reread missing
evidence as needed, without replaying every historical conversation.

## Larger worktrees

Version 3.7 can recover a registered task scope larger than the default 16 MiB
budget without dropping files. The receiving agent explicitly selects
`full-scope-batches-v1` for both preparation and claim, then reviews the new proof.
You keep using the same resume request; the agent handles the helper arguments.

Each batch reads at most 8 MiB, each file stays within 5 MiB and the scope may
contain at most 3000 paths. All paths are checked in two content passes and read
again during the guarded claim. Changed content, missing proof, unknown protocols
and concurrent stale writers are refused. The default legacy limits stay in place.
Complete coverage refers to the registered scope, including its stated exclusions.
It does not certify files outside that scope or product readiness.

See the installed [daily protocol reference](../skills/core/muse-commands/references/DAILY_V1.md)
for the two commands and review input. Keep the same protocol on both commands.

## When a checkpoint approaches its size limit

The incremental save input, selected source note and checkpoint each have a
256 KiB limit (262,144 UTF-8 bytes). The final checkpoint includes metadata and
separators, so character counts or the size of the new text alone are insufficient.
The larger-worktree protocol above does not expand this limit.

Keep detailed test results and logs in evidence files. The agent saves the
necessary facts and short references, using a source note that also fits its own
limit. Only `Next Action` and `Required Reads` can be replaced; earlier decisions,
constraints, unresolved issues and evidence remain preserved.

If saving reports `TOO_LARGE`, retain the failed attempt and its evidence. The
agent checks the current state and writer, prepares a smaller supported delta,
then uses the guarded save and verifies the archive and actual checkpoint. If
that still cannot fit, retain the unsaved evidence for a separate storage review.
Do not raise limits or delete history to make the save pass. Short references do
not provide unlimited checkpoint capacity.

The installed [checkpoint capacity guide](../skills/core/muse-commands/references/CHECKPOINT_CAPACITY.md)
describes the exact preservation and readback steps. This documents existing
behavior; it does not add automatic history compaction or change release 3.7.1.

## What is stored

- `.muse/config.json`: stable project names and the role-home mapping.
- `memory/lanes/`: canonical schema1 checkpoints and guarded incremental history.
- `.agent/skills/muse-commands/`: one shared runtime for the two clients.
- `.agents/skills/` and `.claude/skills/`: relative discovery links to installed skills.
- `memory/.muse-source-inbox/`: redacted Claude prompt captures when available.
- `.muse/installations/`: private installation/rollback receipts; do not publish them.

The default config is `{ "schema_version": 1, "role_home": "home",
"projects": { "home": "." } }`. Relative project roots resolve against the
project containing `.muse/config.json`. The agent can configure additional project
names and a shared role home when needed. Install the shared command center's
workflows there as well. Set `MUSE_CONFIG` when working outside the configured tree.
Explicit MUSE_CONFIG takes precedence over explicit legacy root environment
variables, which take precedence over automatic discovery. Preserve historical
role-home IDs during migration instead of renaming old checkpoint headers.

## Verification, limits and rollback

Saving confirms the declared checkpoint version was written and read back; it
does not certify product completion. Native source access varies by client. Claude
uses SessionStart/UserPromptSubmit hooks; Codex uses its actual session identity
and available native messages. When source access is incomplete, the agent keeps
a partial note and the missing-source boundary instead of claiming perfect memory.
No project-specific transcript exporter is silently assumed to exist.

Formal Bye verifies the declared scope and produces a reusable receipt. Rechecking
unchanged valid evidence does not manufacture another full closeout. Changed
requirements, code, configuration, validators or evidence invalidate affected
checks. Existing product failures remain open until their actual acceptance passes.

To undo a specific installation, stop clients using those installed files and run:

```bash
python3 scripts/install-continuity.py --rollback /path/from/receipt_path
```

Rollback checks all affected files before restoring their previous bytes/links.
If someone edited a managed file after installation, rollback refuses to overwrite
it. Undo successive installations in reverse order. Receipts contain backups of
local policy/configuration and must remain private. User data outside the recorded
installation changes is not removed. Full machine failure, hostile same-user
filesystem changes and arbitrary external writes are outside the cooperative
writer/installer guarantees.

See [中文说明](CONTINUITY_CN.md) and the installed skill's protocol references.
