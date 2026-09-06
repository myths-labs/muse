#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
case "${1:-}" in
  start) exec "${MUSE_PYTHON:-python3}" "$SCRIPT_DIR/muse-runtime.py" capture-claude-session ;;
  source) exec "${MUSE_PYTHON:-python3}" "$SCRIPT_DIR/muse-source-hook.py" --registered-only ;;
  *) exit 2 ;;
esac
