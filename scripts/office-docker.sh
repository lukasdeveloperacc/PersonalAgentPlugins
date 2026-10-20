#!/usr/bin/env bash
# Runs the TaskReporter (office) container while the office MCP (skills/mcp-setup/scripts/mcp.sh) is enabled.
# One long-lived container, not per-session `docker run -i`: the web UI, port 4780 and the DB are shared by every session.
set -euo pipefail
NAME=lukas-office
IMAGE="${OFFICE_IMAGE:-ghcr.io/lukasdeveloperacc/taskreporter:latest}"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$HOME/orca}"
# Same volume name TaskReporter's docker compose creates, so both share one office DB.
VOLUME=taskreporter_office-data

enabled() {
  jq -e '.mcpServers.office' "$HOME/.claude.json" >/dev/null 2>&1 ||
    grep -q '^\[mcp_servers\.office\]' "${CODEX_HOME:-$HOME/.codex}/config.toml" 2>/dev/null
}
serving() { curl -s -o /dev/null --max-time 3 "http://127.0.0.1:4780/"; }

case "${1:-}" in
  start)
    # Already served (this container or TaskReporter's own compose): nothing to do.
    serving && exit 0
    if docker inspect "$NAME" >/dev/null 2>&1; then
      docker start "$NAME" >/dev/null
    else
      # shortcut: uses a local image if present (built from TaskReporter), else pulls; `docker pull` + disable/enable to update.
      docker run -d --name "$NAME" --restart unless-stopped \
        -p 127.0.0.1:4780:4780 \
        -v "$VOLUME:/data" -v "$WORKSPACE_ROOT:$WORKSPACE_ROOT:ro" \
        -e WORKSPACE_ROOT="$WORKSPACE_ROOT" \
        "$IMAGE" >/dev/null
    fi
    ;;
  stop)
    # Data stays in the volume.
    docker rm -f "$NAME" >/dev/null 2>&1 || true
    ;;
  enabled) enabled ;;
  *) echo "usage: $(basename "$0") <start|stop|enabled>" >&2; exit 1 ;;
esac
