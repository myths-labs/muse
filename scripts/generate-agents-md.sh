#!/usr/bin/env bash
# Preserve user policy and install a compact, on-demand Codex entry.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
TARGET_DIR="."
while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) TARGET_DIR="$2"; shift 2 ;;
    --help|-h) echo 'Usage: generate-agents-md.sh [--target DIR]'; exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done
exec "${MUSE_PYTHON:-python3}" "$SCRIPT_DIR/install-continuity.py" --tool codex --target "$TARGET_DIR"
