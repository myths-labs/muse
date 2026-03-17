# 📜 MUSE Protocol Specification (v1.0)

> "AGENTS.md defines the format. MUSE builds the system."

The MUSE Protocol is a zero-dependency, pure Markdown standard for AI Agent governance. It defines how multiple autonomous coding agents can coordinate, maintain persistent memory across isolated conversations, and communicate asynchronously using standard file system interactions.

By implementing the MUSE Protocol, any MCP server, IDE plugin, or CLI tool can make AI agents "MUSE-native"—unlocking multi-role collaboration and permanent context retention without requiring complex external databases like vector stores or graph databases.

---

## 1. The Layered Architecture

MUSE operates at the **L2 Governance System** layer, orchestrating protocols beneath it:

*   **L3: Memory Infrastructure** (e.g., mem0, MemOS) — Specialized databases for agent memory.
*   **L2: Governance System (MUSE)** — Project oversight, role isolation, and inter-agent coordination.
*   **L1: Workflow Kits** (e.g., Spec Kit) — Pre-defined steps for humans to interact with agents.
*   **L0: Format Specs** (e.g., `AGENTS.md`, `.cursorrules`) — Basic prompt formatting rules for a single agent context.

MUSE coordinates L0 specs into a cohesive L2 system.

---

## 2. File Discovery & Routing

All MUSE-compliant projects MUST follow this directory convention:

```text
ProjectRoot/
├── .muse/                  # Role state & governance
│   ├── build.md            # Example role file
│   ├── qa.md               # Example role file
│   └── archive/            # Ignored by parsers
├── memory/                 # Short-term logs
│   ├── YYYY-MM-DD.md       # Daily session logs
│   └── archive/            # Ignored by parsers
├── CLAUDE.md / GEMINI.md   # Project-level constitution
├── USER.md                 # User preferences
└── MEMORIES.md             # Long-term knowledge (distilled)
```

**Rule 2.1:** Any `.md` file in `.muse/` (excluding the `archive/` subdirectory) is considered a **Role File**.
**Rule 2.2:** Multi-project workspaces can host `.muse/` directories in sub-folders, but a master `CLAUDE.md` MAY specify absolute paths to cross-project role files (e.g., `> strategy.md absolute path: /path/to/strategy.md`).

---

## 3. The L0 Header (Machine-Readable State API)

Every `.muse/*.md` role file MUST begin with exactly one **L0 Header Comment** on line 1.

**Format:**
```html
<!-- L0: {version} | {top_priority} | {status_flags} -->
```

*   `version`: Current project version (e.g., `v2.22.0`).
*   `top_priority`: The most important concurrent task for this role.
*   `status_flags`: Comma-separated indicators (e.g., `PASS`, `3 pending`).

### Why L0?
L0 acts as a constant-time `O(1)` state API. A script can run `grep "<!-- L0:" .muse/*.md` to instantly retrieve the entire project's multi-agent status in ~400 tokens, rather than loading thousands of lines of context.

---

## 4. Context Isolation Rules

To prevent context window bloat and AI hallucination, MUSE enforces strict Read/Write boundaries across roles.

### 4.1. Reading Boundaries
When an agent assumes a specific role (e.g., `build`), it:
*   ✅ **MUST** read its own role file (`.muse/build.md`) completely.
*   ✅ **MUST** read the L0 summary lines of *all other* role files.
*   ✅ **MUST** read `MEMORIES.md`, `CLAUDE.md`, and `USER.md`.
*   ❌ **MUST NOT** read the full contents of other role files unless explicitly requested.

### 4.2. Writing Boundaries
*   ✅ **MUST** write updates only to its own role file.
*   ✅ **MUST** write short-term logs to `memory/YYYY-MM-DD.md`.
*   ❌ **MUST NOT** directly edit another role's `.muse/*.md` file.

---

## 5. Cross-Role Communication (The Directive Queue)

Since agents cannot directly edit each other's state, they communicate asynchronously via the **Directive Protocol** (`📡`).

### 5.1 Syntax

When sending a message to another role, the Agent appends this rigidly formatted blockquote to its *own* role file:

```markdown
📡 **{ID}→{TARGET_ROLE}**: {STATUS} **{TITLE}**
> {DETAILED_BODY}
```

*   `{ID}`: A sequential identifier (e.g., `S047`).
*   `{TARGET_ROLE}`: The destination (e.g., `MUSE/BUILD` or simply `QA`).
*   `{STATUS}`: Must be exactly `🟡` (Pending/Unread) or `✅` (Received/Delivered).
*   `{TITLE}`: One-line summary.
*   `{DETAILED_BODY}`: The payload.

### 5.2 Handshake Protocol
1.  **Send:** Role A creates `📡 S001→Role B: 🟡 Task X` in `RoleA.md`.
2.  **Poll:** Role B starts a session, scans `RoleA.md` (and other L0-linked files) for `🟡` targeting itself.
3.  **Accept:** Role B extracts the directive, acts on it, and writes an acknowledgment into `RoleB.md` under `## 📡 Received Directives`.
4.  **Confirm:** Role B reaches back into `RoleA.md` and modifies the *original* sender's prefix from `🟡` to `✅`.

This ensures guaranteed, collision-free message delivery across isolated LLM context windows.

---

## 6. Memory Lifecycle & Semantic Compression

MUSE operates a dual-layer memory architecture to survive context window resets.

### 6.1 Short-Term (The `memory/` Directory)
*   Every session end (e.g., `/bye`) MUST generate an appended log in `memory/YYYY-MM-DD.md`.
*   **Semantic Compression:** Lengthy sessions must condense output based on turn count:
    *   ≤ 5 turns: 1:1 detailed summary.
    *   6-15 turns: 3:1 condensation, categorized by storyline.
    *   ≥ 16 turns: 5:1 condensation.

### 6.2 Mid-Conversation (Session Checkpoints)
*   Agents SHOULD generate silent `📍 Checkpoint` logs into the `memory/` directory every 15 interaction rounds to prevent silent context degradation in ultra-long sessions.

### 6.3 Long-Term (`MEMORIES.md`)
*   Periodic distillation condenses the `memory/` directory into `MEMORIES.md`.
*   Records must use strict typing: `[FACT]`, `[DECISION]`, `[LESSON]`.
*   `[DECAY]` tags must be applied to stale entries older than 30 days.

---

## 7. Tool Integration & Parsing

Because the MUSE Protocol is 100% Markdown-based, integrating it is trivial.

### Bash / CLI Parsers
```bash
# Get Project Status:
grep "<!-- L0:" .muse/*.md

# Check for Pending Cross-Role Directives:
grep -r "🟡" .muse/

# Check Bloat (Warn if role files > 800 lines):
wc -l .muse/*.md
```

### Model Context Protocol (MCP) Server
MUSE officially provides a Bash-native MCP server (`scripts/mcp-server.sh`) mapping the protocol to standard JSON-RPC tools for Claude, Cursor, and Windsurf:
*   `muse_get_status`
*   `muse_list_roles`
*   `muse_get_role`
*   `muse_send_directive`
*   `muse_write_memory`
*   `muse_search_memory`

---
*MUSE Protocol v1.0 — Zero dependencies. Pure Markdown. Supreme clarity.*
