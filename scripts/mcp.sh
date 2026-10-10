#!/usr/bin/env bash
# Preserve the original entry point for existing callers.
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec "$ROOT_DIR/skills/mcp-setup/scripts/mcp.sh" "$@"
