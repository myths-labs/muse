# Changelog

## [2.9.0] - 2026-03-14

### Added
- **`/bye` Iron Rule** — Mandatory 6-step execution enforcement. Agent can no longer skip SOP steps or give short summaries instead of full sync+memory+archive
- **Memory System Declaration** — Explicit declaration that MUSE uses `.muse/*.md` role files, NOT trio-status-sop (`STATUS.md`). Prevents erroneous file creation
- **Complete Project-Role Routing Table** — 13-combination routing table (3 projects × 4+ roles) mapping each conversation type to its correct `.muse/` sync target
- **`/bye` Step 5 CAUTION block** — Convo export step explicitly marked as non-skippable

### Fixed
- **`/bye` not auto-executing SOP** — Agent would give brief summary and stop. Now enforced with `NEVER skip` iron rule language
- **`/bye` creating wrong status files** — Agent confused trio-status-sop SKILL with MUSE role system, creating `STATUS.md` / `MARKETING_STATUS.md` in project roots. Now explicitly banned
- **`/bye` missing project routing** — Only had 5 identity types. Now has 13 with fallback rules

## [2.8.1] - 2026-03-13

### Added
- **[nah](https://github.com/manuelscgipper/nah) recommended companion** — Context-aware permission guard for Claude Code. Added to README, README_CN, install.sh post-install tip, and Credits section
- **P1 features** — Cursor rules generator (`scripts/generate-cursorrules.sh`), skill dependency declarations, memory archive lifecycle
- **GEO/SEO skill** in CLAUDE.md template speed reference table

### Fixed
- **MUSE project routing** — Added missing MUSE project routes to `resume.md` (only DYA/Prometheus had routes)
- **Cursor rules generator** — Target dir validation fix

## [2.8.0] - 2026-03-13

### Added
- **Multi-tool installer** (`scripts/install.sh`) — One command to install MUSE on any supported AI coding tool:
  - **Claude Code / OpenClaw**: `.agent/skills/` + `CLAUDE.md` (native format)
  - **Cursor**: `.cursor/rules/*.mdc` (YAML frontmatter with `alwaysApply`)
  - **Windsurf**: `.windsurf/rules/*.md` (activation comments)
  - **Gemini CLI**: `.gemini/skills/` + `GEMINI.md` (native skill format)
  - **Codex CLI**: `AGENTS.md` (single concatenated file)
- Auto-detection of installed tools (`--list`)
- Interactive + CLI modes (`--tool`, `--target`, `--core-only`)
- README.md + README_CN.md: Added tool support table and multi-tool quick start (Option B)

## [2.7.2] - 2026-03-13

### Fixed
- **QA↔BUILD sync gap** — `/sync receive` in BUILD now checks `build.md` itself for QA→BUILD notifications (previously only checked `strategy.md` + `qa.md`, missing QA broadcasts entirely)
- **`/resume build` dual QA check** — Now checks both `qa.md` for FAIL reports AND `build.md` for QA→BUILD notifications
- **QA broadcast format standardized** — Fixed section header (`📡 QA→BUILD 通知`) + searchable marker (`🟡 待 BUILD 处理`) so agents can grep-find notifications
- **QA iron rule #7: READ-ONLY** — QA must never modify source code directly; only report bugs and route to BUILD via standard notification format
- **Search keyword reference table** — Added to `sync.md` so agents know exactly what to grep for each notification type

## [2.7.1] - 2026-03-13

### Added
- **Auto QA Re-Verify** — `/resume qa` auto-detects FAIL items from `qa.md` "Pending Re-Verify" section and re-verifies them. User just types `/resume qa` — zero manual input
- **qa.md template** — Added "Pending Re-Verify" section for structured FAIL item tracking

### Fixed
- **`/settings language` enforcement** — Language changes now MUST update `CLAUDE.md` Iron Rule #1 (not just `USER.md`). Added `[!CAUTION]` block + verify step + immediate language switch. Prevents silent language change failures
- **MUSE repo self-configuration** — Added `.agent/` symlinks, `memory/`, `CLAUDE.md`, `MEMORIES.md` so the MUSE repo itself works as a MUSE workspace

## [2.7.0] - 2026-03-13

### Added
- **`/settings` command** — Unified preference management: language, AI model, docs convention, code style. Replaces `/model` (backward-compatible alias kept)
- **Pre-Flight Check in `/resume`** — Detects missing `CLAUDE.md` / `USER.md` / `memory/` / `.muse/` and redirects to `/start` instead of crashing
- **Mid-Conversation Sync** — `/sync receive` pulls updates from other roles without ending the conversation (e.g., build pulls QA results live)
- **`/start` in README Commands** — First-time setup now prominently listed

### Changed
- **`resume.md` fully genericized** — Removed all DYA/Prometheus hardcoded tables and paths. Now works for any project out of the box
- **`resume.md` rewritten in English** — All instructions localized to English for open-source users
- **`start.md` updated** — Added `/settings` to command tutorial and post-setup notes
- **`setup.sh` updated** — Next steps now mention `/start` and `/settings`
- **README.md + README_CN.md** — Commands table updated with `/start`, `/settings`, `/sync receive`

### Removed
- **`model.md`** — Replaced by `/settings` (which handles model + language + docs + code style)
## [2.6.0] - 2026-03-13

### Added
- **QA System v2.0** — Complete rewrite of `qa.md` with:
  - 🚀 Quick Start guide (3 launch methods: Strategy-assigned / Build-completed / Pre-release regression)
  - 📋 7-step SOP (AC source → environment → verify → error paths → report → judge → routing)
  - 📝 3 complete use cases with step-by-step examples
  - 📡 Result routing table (PASS/FAIL → where to write, who to notify)
- **`/resume [project] qa`** — New QA-specific resume route in `resume.md`
- **Quick Start sections** — Added to all role files (`build.md`, `growth.md`, `ops.md`, `research.md`, `fundraise.md`)
- **QA routes in MUSE.md** — `/resume qa` and `/resume prometheus qa` in routing table

### Fixed
- **`bye.md` convo naming bug** — Replaced hardcoded example date with dynamic rules (use current date, check folder for max sequence number). Added ❌/✅ error/correct examples
- **`resume.md` memory scanning** — Now detects `🔲` + `- [ ]` + `➡️ 下一步` items (was only `🔲`)
- **`bye.md` distill detection** — Improved MEMORIES.md timestamp check (stat + grep dual method)

## [2.5.0] - 2026-03-12

### Added
- **Ecosystem Packs** — 7 optional technology-specific skill packs (13 skills):
  - `react-nextjs` (3): react-best-practices, frontend-patterns, vercel-react-best-practices
  - `backend-database` (3): backend-patterns, postgres-patterns, database-reviewer
  - `expo-mobile` (3): expo-app-design, expo-deployment, upgrading-expo
  - `javascript-typescript` (1): javascript-typescript
  - `vercel` (1): vercel-deploy-claimable
  - `remotion` (1): remotion-best-practices
  - `web-artifacts` (1): web-artifacts-builder
- **New Toolkit skill**: `coding-standards` (universal coding standards for JS/TS/React/Node.js)
- Skill totals: 4 Core + 37 Toolkit + 13 Ecosystem = **54 skills**

### Fixed
- Cleaned DYA-specific references from `database-reviewer`
- Fixed merge conflict markers in `coding-standards`

## [2.4.1] - 2026-03-12

### Added
- **10 more toolkit skills** (total: 4 Core + 35 Toolkit = 39 skills)
  - `api-design-principles`, `dispatching-parallel-agents`, `doc-coauthoring`
  - `markitdown`, `using-git-worktrees`, `theme-factory`
  - `github-pr-merge`, `doc-updater`, `e2e-runner`, `subagent-driven-development`, `ralph-wiggum`

### Fixed
- Cleaned DYA-specific references from `doc-updater` and `e2e-runner`
## [2.4.0] - 2026-03-12

### Added
- **21 new skills** (total: 4 Core + 25 Toolkit = 29 skills)
  - **Core**: `using-superpowers` — meta-skill for effective skill usage
  - **Toolkit — Dev Flow**: `code-refactoring`, `code-documentation`, `security-review`, `tdd-workflow`, `changelog-generator`, `skill-creator`, `skills-updater`, `webapp-testing`
  - **Toolkit — Collaboration**: `github-pr-creation`, `github-pr-review`, `receiving-code-review`, `requesting-code-review`, `finishing-a-development-branch`
  - **Toolkit — Planning & Design**: `brainstorming`, `writing-plans`, `executing-plans`, `planner-agent`, `architect-agent`, `frontend-design`, `ui-ux-pro-max`

### Improved
- **README_CN.md**: Expanded from 142 → 310 lines (Architecture, LCM mapping, Defensive Auto-Save, Directory Convention, Customization, FAQ)
- **resume.md**: Added ②.5 unchecked items scan, 2.7 bloat check, 4.1 conflict resolution, 4.2 consistency check
- **bye.md**: Added 4.5 bloat check, triple cross-check (cross-file + intra-file + memory retroactive)
- **Assets**: banner.png compressed -36%
- **.gitignore**: Added `.muse/` `memory/` `convo/`


All notable changes to MUSE are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/).

---

## [2.3] — 2026-03-12

### Added
- **`/start` onboarding workflow** — 8-step interactive guide for first-time users (project naming, language, model, roles, skills, command tutorial)
- **`setup.sh`** — shell-based interactive setup wizard (language, model, skills install)
- **Role file lifecycle management** — auto-detect bloated .muse/ files, archive historical content
  - `/resume` step 2.7: >800 lines → auto-archive before work
  - `/bye` step 4.5: check all role files, warn if >800 lines
  - Archive pattern: `.muse/archive/` for historical decisions, directives, logs
- **Memory scan on resume** — `/resume` step 2.5: scan memory for 🔲 unfinished items, proactively remind user
- **MUSE.md lifecycle spec** — documented data flow: active (≤500 lines) → archive → MEMORIES.md

### Changed
- All Core SKILL.md files translated from Chinese to English (`context-health-check`, `strategic-compact`, `verification-before-completion`)
- README Quick Start now offers Option A (interactive `./setup.sh`) and Option B (manual copy)
- Footer links updated: Myths Labs → github.com/myths-labs, added creator JC profile and social links

### Fixed
- Broken `mythslabs.ai` link in README footer → corrected to `github.com/myths-labs`

---

## [2.2] — 2026-03-12

### Added
- **Directory Convention** — standardized naming for memory logs, conversations, role files
- **Distill scope control** — `/distill` global vs `/distill [project]` project-specific
- **Auto-distill detection** — `/bye` checks memory/ accumulation, suggests `/distill` when needed
- **L0 Defensive Auto-Save** — silent `CRASH_CONTEXT.md` update every 10 turns
- **Cheat Sheet** — quick reference card for all commands and role hierarchy

---

## [2.1] — 2026-03-12

### Added
- **GM (General Manager) role** — project-level CEO with L1/L2 autonomous decision authority
- **Multi-project architecture** — workspace-first design with shared skills/workflows, project-specific roles
- **Constitution inheritance** — global CLAUDE.md → project CLAUDE.md override chain
- **`/sync` workflow** — cross-role synchronization (strategy↔GM↔roles)
- **`/resume crash`** — context blowout recovery via CRASH_CONTEXT.md
- **`/model`** — AI model preference switching
- **`/role`** — interactive new role creation
- **QA role** — independent verification with veto power (anti-fraud)

---

## [2.0] — 2026-03-11

### Added
- **Role system** — `.muse/` directory with specialized role files (strategy, build, qa, growth, ops, research, fundraise)
- **Trio-status architecture** — STRATEGY_STATUS.md, STATUS.md, MARKETING_STATUS.md
- **`/distill` workflow** — condense memory/ daily logs into MEMORIES.md long-term lessons
- **`/ctx` skill** — context window health check with 🟢🟡🔴 levels
- **Strategic compact** — focus-aware context compaction

---

## [1.0] — 2026-03-03

### Added
- Initial MUSE implementation
- **Constitution** — CLAUDE.md iron rules
- **Memory layer** — memory/YYYY-MM-DD.md short-term + MEMORIES.md long-term
- **`/resume`** — context assembly boot sequence
- **`/bye`** — zero-input session wrap-up
- **Skill-driven execution** — `.agent/skills/` with trigger-based loading
- Inspired by LCM paper and lossless-claw
