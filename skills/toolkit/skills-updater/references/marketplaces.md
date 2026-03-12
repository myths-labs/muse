# Supported Skill Marketplaces

This document lists the skill marketplaces supported by the skills-updater.

## Claude Code Plugins (Official)

### anthropics/skills
- **URL**: https://github.com/anthropics/skills
- **Type**: Official Anthropic example skills
- **Install**: `claude /install <skill-name>@anthropic-agent-skills`
- **Notable Skills**: document-skills (xlsx, docx, pptx, pdf), frontend-design, canvas-design

### anthropics/claude-plugins-official
- **URL**: https://github.com/anthropics/claude-plugins-official
- **Type**: Official Claude plugins collection
- **Install**: `claude /install <plugin-name>@claude-plugins-official`
- **Notable Plugins**: hookify, github, playwright, code-review, commit-commands

## Community Marketplaces

### daymade/claude-code-skills
- **URL**: https://github.com/daymade/claude-code-skills
- **Type**: Community skills collection
- **Install**: `claude /install <skill-name>@daymade-skills`
- **Notable Skills**: skill-creator, github-ops, youtube-downloader, macos-cleaner, fact-checker

### obra/superpowers-marketplace
- **URL**: https://github.com/obra/superpowers-marketplace
- **Type**: Extended capabilities marketplace
- **Install**: `claude /install <skill-name>@superpowers-marketplace`
- **Notable Skills**: superpowers, double-shot-latte

### kepano/obsidian-skills
- **URL**: https://github.com/kepano/obsidian-skills
- **Type**: Obsidian integration skills
- **Install**: `claude /install obsidian@obsidian-skills`

### lackeyjb/playwright-skill
- **URL**: https://github.com/lackeyjb/playwright-skill
- **Type**: Browser automation skill
- **Install**: `claude /install playwright-skill@playwright-skill`

### OthmanAdi/planning-with-files
- **URL**: https://github.com/OthmanAdi/planning-with-files
- **Type**: File-based planning workflow
- **Install**: `claude /install planning-with-files@planning-with-files`

## npx skills Marketplaces

### skills.sh
- **URL**: https://skills.sh/
- **Type**: Community skills leaderboard
- **Install**: `npx skills add <owner/repo>`
- **Features**:
  - Install count rankings
  - Category browsing
  - One-command installation

### skillsmp.com
- **URL**: https://skillsmp.com/
- **Type**: Curated skills marketplace
- **Install**: `npx skills add <owner/repo>`
- **Note**: May require authentication or have access restrictions

## Version Tracking Mechanisms

### Semantic Versioning (marketplace.json)

Most marketplaces use semantic versioning in their `marketplace.json`:

```json
{
  "plugins": [
    {
      "name": "skill-name",
      "version": "1.2.3",
      ...
    }
  ]
}
```

### Commit SHA Tracking

Some skills track by git commit SHA instead of semantic version:

```json
{
  "installPath": "...",
  "version": "e30768372b41",
  "gitCommitSha": "e30768372b41c97d13054211657275029ca8b6d"
}
```

### Auto-Update Configuration

Some marketplaces support auto-update flags in `known_marketplaces.json`:

```json
{
  "planning-with-files": {
    "autoUpdate": true
  }
}
```

## Adding New Marketplaces

To register a new marketplace:

```bash
# Via GitHub repository
claude /marketplace add github:<owner>/<repo>

# Via git URL
claude /marketplace add git:https://github.com/<owner>/<repo>.git
```

## Data Locations

| File | Purpose |
|------|--------|
| `~/.claude/plugins/installed_plugins.json` | Tracks installed skills with versions |
| `~/.claude/plugins/known_marketplaces.json` | Registered marketplace sources |
| `~/.claude/plugins/cache/` | Downloaded skill files |
| `~/.claude/plugins/marketplaces/` | Cloned marketplace repositories |
| `~/.skills/` | npx skills installation directory |
