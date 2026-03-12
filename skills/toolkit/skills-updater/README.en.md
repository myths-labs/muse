# Skills Updater

Manage, update, and discover Claude Code skills across multiple installation sources.

[中文](README.md)

## Features

- **Update Checker** - Scan installed skills and check for available updates
- **Auto-Install** - Automatically reinstall affected skills after marketplace updates
- **Skill Recommendations** - Discover trending skills from skills.sh
- **i18n Support** - Auto-detect locale (English/Chinese)

## Installation

In Claude Code, simply ask it to clone and install:

```
Clone https://github.com/yizhiyanhua-ai/skills-updater to ~/.claude/skills/
```

Or just say:

```
Install the skills-updater skill
```

## Usage

After installation, trigger with natural language or commands in Claude Code:

### Check for Updates

```
Check for skill updates
```

```
/skills-updater
```

### Update a Marketplace

```
Update the anthropic-agent-skills marketplace
```

### Discover New Skills

```
Recommend some useful skills
```

```
What are some popular skills?
```

## Examples

**Example 1: Check for Updates**

```
You: Check for skill updates

Claude: Checking for skill updates...

📦 Installed Skills Status
━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Up-to-date (15):
   • skill-creator@daymade-skills (1.2.2)
   ...

⬆️ Updates Available (1):
   • document-skills@anthropic-agent-skills
     Local: e5c60158 → Remote: 69c0b1a0
```

**Example 2: Update and Auto-Install**

```
You: Update the anthropic-agent-skills marketplace

Claude:
📡 Fetching remote updates...

Current commit: e5c60158df67
Remote commit: 69c0b1a06741
Status: Behind by 6 commits

📦 Affected skills: document-skills

Confirm update? Enter 'yes' to proceed.

You: yes

Claude:
📥 Updating marketplace: anthropic-agent-skills
✅ Marketplace updated successfully
✅ Reinstalled: document-skills
```

**Example 3: Discover New Skills**

```
You: Recommend some useful skills

Claude:
🔥 Trending Skills
━━━━━━━━━━━━━━━━━━

From skills.sh (Top 10):
 1. vercel-react-best-practices (25.5K installs)
 2. web-design-guidelines (19.2K installs)
 ...

💡 Personalized Recommendations
Based on your installed skills:
• playwright-skill - Browser automation testing
• github-ops - GitHub CLI operations
```

## Trigger Summary

| Feature | Natural Language | Command |
|---------|------------------|---------|
| Check updates | "Check for skill updates" | `/skills-updater` |
| Update marketplace | "Update xxx marketplace" | - |
| Skill recommendations | "Recommend some skills" | - |
| Update all | "Update all skills" | - |

## Language Support

Automatically displays in English or Chinese based on your system language. Claude Code will auto-detect your locale.

## Documentation

- [SKILL.md](SKILL.md) - Complete skill documentation
- [references/marketplaces.md](references/marketplaces.md) - Supported marketplaces list

## License

MIT
