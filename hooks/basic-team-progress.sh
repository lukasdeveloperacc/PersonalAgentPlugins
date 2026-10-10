#!/usr/bin/env bash
set -u
SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../skills/basic-team/scripts" && pwd)/basic-team-progress.py"
event="${1:-}"
shift || true
host=""
if [[ "${1:-}" == "--host" ]]; then host="$2"; shift 2; fi
if [[ -z "$host" ]]; then host=auto; fi
command -v uv >/dev/null 2>&1 || exit 0
case "$event" in
  UserPromptSubmit|SessionStart|SessionEnd|PostToolUse) exec uv run --script "$SCRIPT" hook "$event" --host "$host" "$@" 2>/dev/null || true ;;
  *) exit 0 ;;
esac
