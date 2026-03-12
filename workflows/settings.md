---
description: Change user preferences at any time. Updates language, AI model, docs convention, and code style in USER.md. Replaces /model command.
---

## Usage

```
/settings                     — Show current settings + menu
/settings language [lang]     — Change communication language
/settings model [model-name]  — Change AI model preference
/settings docs [preference]   — Change documentation language convention
```

Examples:
- `/settings` — show all current settings
- `/settings language 简体中文`
- `/settings model claude opus 4`
- `/settings docs english`

---

## Steps

// turbo-all

### 1. Read Current Settings

Read `USER.md`. If it doesn't exist, offer to create it:

```
⚠️ No USER.md found. Run /start first, or I'll create a default one now.
Create USER.md with defaults? (y/n)
```

If yes → create `USER.md` from template with sensible defaults (English, auto-detect current model).

### 2. Parse Subcommand

| Subcommand | What it does |
|------------|-------------|
| *(none)* | Show current settings + offer change menu |
| `language [lang]` | Update Communication Language in USER.md |
| `model [name]` | Update AI Model + Context Window in USER.md |
| `docs [pref]` | Update Docs Language preference in USER.md |

### 3. Execute Change

**For `language`:**
1. Update `USER.md` → `**Language**: [new language]`
2. Update `CLAUDE.md` Iron Rule #1 → `All communication in [new language]`
3. Confirm:
   ```
   ✅ Language: [old] → [new]
   CLAUDE.md Iron Rule #1 updated.
   All future conversations will use [new language].
   ```

**For `model`:**
1. Fuzzy-match input to known models (e.g., `opus` → `Claude Opus 4`)
2. Update `USER.md` → `**Preferred Model**: [new model]` + `**Context Window**: [size]`
3. Confirm:
   ```
   ✅ Model: [old] → [new]
   Context window: [old size] → [new size]
   This affects /ctx calculations going forward.
   ```

**For `docs`:**
1. Update `USER.md` → `**Docs Language**: [new preference]`
2. Confirm:
   ```
   ✅ Docs language: [old] → [new]
   ```

**For *(no subcommand)*:**

Display current state and menu:
```
⚙️ Current Settings:

  Language:    English
  AI Model:    Claude Opus 4 (200K tokens)
  Docs:        English for code, 简体中文 for discussions
  Code Style:  ESLint + Prettier
  Git:         Conventional Commits

What would you like to change?
  [1] Language    [2] Model    [3] Docs
  [4] Code style  [5] Git convention
  [0] Done — no changes

Choice: ___
```

### 4. Handle Code Style & Git (if requested)

These are less common but still supported:
- `code style` → Update `USER.md` → `**Code Style**: [value]`
- `git` → Update `USER.md` → `**Git**: [value]`

---

## Supported Models (reference)

| Model | Context Window |
|-------|:--------------:|
| Claude Opus 4 | 200K tokens |
| Claude Sonnet 4 | 200K tokens |
| GPT-4o | 128K tokens |
| GPT-o1 / o3 | 200K tokens |
| Gemini 2.5 Pro | 1M tokens |
| DeepSeek V3 | 128K tokens |

> This list is not exhaustive. Users can specify any model name and context window size.

---

## Notes

- All preferences are stored in `USER.md` (private, not committed)
- `/ctx` uses model setting to calculate context usage percentage
- Language change updates both `USER.md` AND `CLAUDE.md` Iron Rule #1
- Changing models mid-conversation sets preference for **future sessions**
- Previously called `/model` — `/model` still works as an alias for `/settings model`

---

## Backward Compatibility

- `/model [name]` → automatically treated as `/settings model [name]`
