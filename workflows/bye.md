---
description: Route MUSE bye to the configured daily or explicit legacy workflow
---

# Bye

Use the installed `.agent/skills/muse-commands/SKILL.md` dispatch. Run `bye-workflow` with the exact role/Lane command and workspace. If it selects a daily workflow, follow that returned file only. If it selects this file, the Lane explicitly uses legacy handling; read `.agent/workflows/legacy/bye.md`. Do not silently fall back on corrupt or unknown protocol state.

Ordinary progress uses `/save`. Context pressure alone does not trigger Bye or a new conversation. A CLOSED Lane stays closed until its recorded reopen conditions are met.
