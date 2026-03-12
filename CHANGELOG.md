# Changelog
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
