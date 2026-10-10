#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT="$ROOT_DIR/skills/mcp-setup/scripts/mcp.sh"
SANDBOX="$(mktemp -d)"
trap 'rm -rf "$SANDBOX"' EXIT
STUB_BIN="$SANDBOX/bin"
CALL_LOG="$SANDBOX/calls.log"
mkdir -p "$STUB_BIN" "$SANDBOX/home"

for name in codex claude; do
  printf '#!/usr/bin/env bash\nprintf "%%s|" %s "$@" >> "%s"; echo >> "%s"\n' "$name" "$CALL_LOG" "$CALL_LOG" > "$STUB_BIN/$name"
  chmod +x "$STUB_BIN/$name"
done

run() { HOME="$SANDBOX/home" XDG_STATE_HOME="$SANDBOX/state" PATH="$STUB_BIN:$PATH" "$SCRIPT" "$@"; }

expect_calls() {
  [[ "$(cat "$CALL_LOG")" == "$(printf '%s\n' "$@")" ]] || {
    echo "unexpected calls:" >&2; cat "$CALL_LOG" >&2; exit 1
  }
}

# HTTP server with a bearer token: Claude gets headers only, Codex gets the env var flag.
: > "$CALL_LOG"
run claude enable glitchtip
expect_calls 'claude|mcp|add-json|-s|user|glitchtip|{"type":"http","url":"http://localhost:38088/mcp","headers":{"Authorization":"Bearer ${GLITCHTIP_MCP_TOKEN}"}}|'
: > "$CALL_LOG"
run codex enable glitchtip
expect_calls 'codex|mcp|add|glitchtip|--url|http://localhost:38088/mcp|--bearer-token-env-var|GLITCHTIP_MCP_TOKEN|'

# stdio server: literal env kept, "${VAR}" pass-through dropped for Codex.
: > "$CALL_LOG"
run codex enable aws-eks
expect_calls 'codex|mcp|add|aws-eks|--env|FASTMCP_LOG_LEVEL=ERROR|--|uvx|awslabs.eks-mcp-server@latest|--allow-write|--allow-sensitive-data-access|'

# CodeGraph is registered as a local stdio server for both tools.
: > "$CALL_LOG"
run codex enable codegraph
expect_calls 'codex|mcp|add|codegraph|--|codegraph|serve|--mcp|'
: > "$CALL_LOG"
run claude enable codegraph
expect_calls 'claude|mcp|add-json|-s|user|codegraph|{"command":"codegraph","args":["serve","--mcp"]}|'
run codex list | grep -x 'codegraph off' >/dev/null
run claude list | grep -x 'codegraph off' >/dev/null

# Browser and documentation servers use their existing npx package commands.
: > "$CALL_LOG"
run codex enable chrome-devtools
expect_calls 'codex|mcp|add|chrome-devtools|--|npx|-y|chrome-devtools-mcp@latest|'
: > "$CALL_LOG"
run claude enable context7
expect_calls 'claude|mcp|add-json|-s|user|context7|{"command":"npx","args":["-y","@upstash/context7-mcp"]}|'

# disable with no names removes every catalog server.
: > "$CALL_LOG"
run claude disable
[[ "$(wc -l < "$CALL_LOG")" -eq "$(jq '.mcpServers | length' "$ROOT_DIR/mcp/servers.json")" ]]

# list reports per-tool state from each tool's user config.
echo '{"mcpServers":{"glitchtip":{}}}' > "$SANDBOX/home/.claude.json"
mkdir -p "$SANDBOX/home/.codex" && printf '[mcp_servers.notion]\nurl = "x"\n' > "$SANDBOX/home/.codex/config.toml"
run claude list | grep -x "glitchtip on" >/dev/null
run claude list | grep -x "notion off" >/dev/null
run codex list | grep -x "notion on" >/dev/null
run codex list | grep -x "glitchtip off" >/dev/null

if run claude enable nope 2>/dev/null; then
  echo 'expected unknown server to fail' >&2
  exit 1
fi

# The original entry point forwards arguments and preserves failures from any cwd.
(
  cd "$SANDBOX"
  for tool in codex claude; do
    : > "$CALL_LOG"
    run "$tool" enable codegraph
    expected="$(cat "$CALL_LOG")"
    : > "$CALL_LOG"
    SCRIPT="$ROOT_DIR/scripts/mcp.sh" run "$tool" enable codegraph
    [[ "$(cat "$CALL_LOG")" == "$expected" ]]
    [[ "$(SCRIPT="$ROOT_DIR/scripts/mcp.sh" run "$tool" list)" == "$(run "$tool" list)" ]]
    : > "$CALL_LOG"
    if SCRIPT="$ROOT_DIR/scripts/mcp.sh" run "$tool" enable nope 2>/dev/null; then
      echo "expected unknown server to fail through the original entry point: $tool" >&2
      exit 1
    fi
    [[ ! -s "$CALL_LOG" ]]
  done
)
echo "ok"
