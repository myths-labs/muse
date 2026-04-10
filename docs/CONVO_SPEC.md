# MUSE Conversation Export Specification (L1)

> Version 1.0 — 2026-04-10
> Canonical format for cross-tool session exports.

## Directory Layout

```
<project-root>/
  convo/
    YYMMDD/
      YYMMDD-01-session-title.md
      YYMMDD-02-another-session.md
    YYMMDD/
      ...
```

- **`YYMMDD`**: 2-digit year + 2-digit month + 2-digit day (e.g., `260410` for 2026-04-10)
- **`NN`**: Zero-padded sequence number, auto-incremented per day (01, 02, ...)
- **`title`**: 2-5 word kebab-case summary (e.g., `cc-bridge-setup`, `s114-volcengine-migration`)

## File Format

### Header (required)

```markdown
# Session — <title>

- **Exported:** YYYY-MM-DD HH:MM
- **Tool:** <tool-id>
- **Project:** <project-path>
- **Messages:** <count>

---
```

**Tool IDs** (canonical, lowercase):

| ID | Platform |
|----|----------|
| `claude-code` | Claude Code |
| `openclaw` | OpenClaw |
| `opencode` | OpenCode |
| `cursor` | Cursor |
| `windsurf` | Windsurf |
| `gemini` | Gemini CLI |
| `codex` | Codex CLI |
| `copilot` | GitHub Copilot |
| `aider` | Aider |
| `antigravity` | Antigravity |
| `manual` | Manual paste (no auto-export) |

### Body

Each message uses a level-2 heading with role emoji:

```markdown
## 👤 User

<user message content>

## 🤖 Assistant

<assistant response content>

## 👤 User

<next user message>
```

### Special Content Blocks

**Tool calls** (automated adapters only):

````markdown
```json
// Tool: <tool-name>
{
  "name": "read_file",
  "input": { "path": "src/main.ts" }
}
```
````

**Tool results** (truncated at 1500 chars):

````markdown
```
// Result: <tool-name>
<output, truncated if >1500 chars>
```
````

**Thinking blocks** (Claude-family tools):

```markdown
<details>
<summary>Thinking</summary>

<thinking content>

</details>
```

### Prior Summary (optional)

If the tool provides a session summary (e.g., Claude Code's context compression), include it before the first message:

```markdown
## 📝 Prior Summary

<summary content>

---
```

## Manual Export Template

For tools without programmatic session access, adapters generate a file with this template:

```markdown
# Session — <title>

- **Exported:** YYYY-MM-DD HH:MM
- **Tool:** <tool-id>
- **Project:** <project-path>
- **Messages:** 0

---

> Paste your conversation below. Use `## 👤 User` and `## 🤖 Assistant` headers
> to separate messages. Delete this instruction block after pasting.
```

## Adapter Contract

Each adapter script (`scripts/adapters/export_<tool>_session.sh`) must:

1. Accept `<title>` as first positional argument
2. Accept `--project-root <path>` to override output location (default: git repo root)
3. Output exactly one file to `<project-root>/convo/YYMMDD/YYMMDD-NN-title.md`
4. Auto-increment `NN` by scanning existing files in the date directory
5. Print the output file path to stdout on success
6. Exit 0 on success, non-zero on failure
7. Have zero external dependencies (shell builtins + Python3 stdlib only)

## Sequence Number Algorithm

```bash
DATE_DIR="$PROJECT_ROOT/convo/$YYMMDD"
mkdir -p "$DATE_DIR"
LAST=$(ls "$DATE_DIR"/"$YYMMDD"-*.md 2>/dev/null | sort | tail -1 | grep -o "$YYMMDD-[0-9]*" | grep -o '[0-9]*$' || echo "00")
NN=$(printf "%02d" $((10#$LAST + 1)))
```

## Backward Compatibility

Existing convo files (pre-L1) are not required to match this spec. The spec applies only to new exports. Tools that read `convo/` should handle both legacy and L1 formats gracefully.
