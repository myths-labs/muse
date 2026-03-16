# 🎭 MUSE VS Code Extension

**Memory-Unified Skills & Execution** — browse roles, skills, and memory directly in VS Code.

## Features

| Feature | Description |
|---------|-------------|
| **Activity Bar** | MUSE explorer with Roles, Skills, and Memory tree views |
| **Dashboard** | In-editor webview showing role status, memory timeline, and stats |
| **Skill Search** | QuickPick search across all installed MUSE skills |
| **Context Health** | Check memory file accumulation and distill reminders |
| **Dashboard Generator** | Run `dashboard.sh` to generate the full HTML dashboard |

## Commands

| Command | Action |
|---------|--------|
| `MUSE: Show Dashboard` | Open in-editor dashboard webview |
| `MUSE: Browse Skills` | Refresh skill tree view |
| `MUSE: Search Skills` | Search skills by keyword |
| `MUSE: Context Health Check` | Check memory status |
| `MUSE: Show Memory Timeline` | Refresh memory tree |
| `MUSE: Show Role Status` | Refresh role tree |
| `MUSE: Open Skill` | Open a specific skill file |
| `MUSE: Generate Web Dashboard` | Run dashboard.sh |

## Installation

### From Source

```bash
cd vscode-extension
npm install
npm run compile
```

Then press `F5` in VS Code to launch the extension in development mode.

### From VSIX

```bash
cd vscode-extension
npm install
npx @vscode/vsce package
code --install-extension muse-context-os-0.1.0.vsix
```

## Activation

The extension auto-activates when it detects:
- `CLAUDE.md` in the workspace
- `.muse/` directory
- `.agent/skills/` directory

## Requirements

- VS Code 1.85+
- A MUSE-enabled project (with `.muse/`, `memory/`, or `skills/`)

## License

MIT © [Myths Labs](https://github.com/myths-labs)
