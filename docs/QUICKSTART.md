# MUSE basics: pick up where you left off

[简体中文](QUICKSTART_CN.md) · [Web guide](https://muse.mythslabs.ai/guide-en.html) · [Installation and details](CONTINUITY.md)

## Meet MUSE in 30 seconds

**Think of MUSE as your AI's project notebook.**

Imagine building a small shop website together. Today you choose colors and finish the homepage. Tomorrow you need the product page.
MUSE helps your AI record decisions, progress, open problems and the next step in your project.
When you return, the AI reads those notes and checks the actual files before continuing.

**You explain what you want. The AI plans, works, checks and records progress.** It asks you when a decision needs your input.

## Why use it?

- **Repeat less:** a new conversation can read saved progress instead of asking you to explain everything again.
- **Keep working:** ordinary saves let you continue without a daily cycle of closeouts and new conversations.
- **Change assistants more easily:** use Codex alone, Claude Code alone, or let one pick up the other's saved work.
- **See what's left:** completed work, unfinished tasks and failed checks have a place in the project notes.

## How do I start?

A project is the folder holding the files for your work. Choose the existing folder, or ask your AI to create one if you are starting fresh.
Install MUSE in your project, then **open that project in Codex or Claude Code**.
If you need help, give a file-capable coding assistant the [installation guide](CONTINUITY.md), tell it where your project is, and ask it to check and install MUSE.
Once installed, say:

> Help me build a small shop website. Check what already exists and work out what we should do next.

The AI prepares a plan from your request and existing records. **You do not need to fill in a goals, acceptance criteria and constraints form.**

## Remember three requests

| What you need | What you can say | Command |
|---|---|---|
| Pick up previous work | Resume the workstream we were using. | `/resume strategy Lane A` |
| Keep current progress | Save our progress. | `/save` |
| Formally wrap up a stage | Check the results and open issues, then close out this stage. | `/bye` |

`strategy` and `Lane A` are examples. Use your project's actual role and workstream.
If you forget the name, ask the AI to find it in the records instead of inventing a new one.
Send commands in the **AI chat**, not a terminal. Plain language works too; the AI should interpret it against the current work.

**In an ongoing conversation, just say “continue.” You do not need to Resume after every step.**

## A day at the little shop

1. **Start:** “Continue the shop website.” In a new conversation, recover the existing workstream first.
2. **Work:** “Give the homepage warmer colors.” The AI edits, checks and saves meaningful progress.
3. **Stop for the day:** “Save and pause here for today.” A daily Bye is usually unnecessary.
4. **Return tomorrow:** say “continue” in the same conversation, or resume the same role and workstream in a new one.
5. **Formally finish a stage:** “Run `/bye` for this stage.” The AI reviews the records, results and remaining problems.

**Save keeps progress. Bye creates a reviewed record of a stage.** Bye does not automatically close the whole workstream or prove the website is ready to launch.

## What are Role and Lane?

**Role means what the AI is responsible for.** Strategy can make overall decisions and implement directly when that is your project's arrangement. A separate Build role is optional.

**Lane means a workstream: a chapter in the notebook.** Chapter A might cover the shop website; chapter B might cover another job that needs its own follow-up.
One is usually enough to start. The AI can suggest another when the work needs it, not simply because a day passed or you changed models.

## Switching from Codex to Claude Code?

1. Ask the original conversation to save and pause. Wait for confirmed saving and for it to stop editing.
2. Open **the same project** in the other client. Have it check that MUSE is installed and available for that client, and that it can read the latest saved records.
3. Resume **the same role and Lane**. The AI checks progress and files before taking over. A full Bye is usually unnecessary.

If you change computers, bring the project files and latest records too. MUSE does not automatically sync computers.
Ask the AI to use the [detailed guide](CONTINUITY.md) to check that the records came across; do not bring only the code.

## A few useful things to know

- **Does this work automatically in a regular ChatGPT web chat?** No. This guide describes Codex and Claude Code with MUSE installed and access to project files.
- **Will it remember everything forever?** No. It helps save important information; unsaved or lost records may not be recoverable.
- **What if saving fails?** Ask the AI to investigate and fix it. Do not assume the handoff is ready until saving is confirmed.
- **Can two AIs edit the same Lane at once?** Stop the previous writer before switching. For simultaneous jobs, have the AI arrange separate scopes and isolated files.
- **Will it save tokens?** Incremental saving and selective reading can reduce repeated processing. The effect depends on the task; there is no fixed savings guarantee.
- **Do I need Bye every evening?** No. Save and pause for a daily stop; use Bye when you want a formal review and record of a stage.
- **Is it free?** MUSE is free and open source. Your AI tools may charge separately.

**Say what you want. Save progress. Come back and continue. Use Bye for a formal wrap-up.**

For MUSE 3.6 · Updated 2026-09-06. See the [detailed guide](CONTINUITY.md) for setup requirements and advanced use.
