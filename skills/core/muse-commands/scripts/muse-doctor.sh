#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
exec "${MUSE_PYTHON:-python3}" "$SCRIPT_DIR/muse-cli.py" "$@"
