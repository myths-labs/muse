# Path Configuration

> Optional file for advanced multi-project setups.
> Place at `.muse/paths.md` in your project root.
> If absent, all paths default to the current project root.

## Project Paths

```
CONVO_ROOT: .
MEMORY_ROOT: .
```

## Cross-Project (optional — for multi-repo governance)

> Uncomment and configure if you manage multiple projects with a shared strategy.

```
# STRATEGY_PATH: /path/to/shared/.muse/strategy.md
# OBSIDIAN_VAULT: /path/to/obsidian/vault
# DYA_ROOT: /path/to/main/project
```

## Tool-Specific Overrides (optional)

> Override session export behavior per tool.

```
# EXPORT_ADAPTER: auto
# MANUAL_EXPORT_TOOL: cursor
```
