#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT="$ROOT_DIR/scripts/plugin.sh"
PLUGIN_NAME="$(jq -r '.name' "$ROOT_DIR/.claude-plugin/plugin.json")"
MARKETPLACE_NAME="$(jq -r '.name' "$ROOT_DIR/.claude-plugin/marketplace.json")"
PLUGIN_ID="${PLUGIN_NAME}@${MARKETPLACE_NAME}"
DEP_ID="ponytail@ponytail"
DEP_SRC="DietrichGebert/ponytail"
ELI5_ID="eli5@claude-community"
ELI5_SRC="anthropics/claude-plugins-community"
CLAUDE_DEP_ID="impeccable@impeccable"
CLAUDE_DEP_SRC="pbakaus/impeccable"
OMC_ID="oh-my-claudecode@omc"
OMC_SRC="Yeachan-Heo/oh-my-claudecode"
OMX_SETUP="omx setup --scope user --plugin --merge-agents"
MCP_NAMES=($(jq -r '.mcpServers | keys[]' "$ROOT_DIR/mcp/servers.json"))
IMPECCABLE_CODEX="npx -y impeccable@latest install --providers=codex --scope=user --yes --no-hooks"

SANDBOX="$(mktemp -d)"
trap 'rm -rf "$SANDBOX"' EXIT
STUB_BIN="$SANDBOX/bin"
FAKE_HOME="$SANDBOX/home"
INSTALLED="$SANDBOX/installed"
CALL_LOG="$SANDBOX/calls.log"
mkdir -p "$STUB_BIN" "$FAKE_HOME"
for name in jq python3; do
  ln -s "$(command -v "$name")" "$STUB_BIN/$name"
done

# Fake installed copy of the dependency so its hooks can be trusted.
mkdir -p "$INSTALLED/ponytail/.codex-plugin" "$INSTALLED/ponytail/hooks"
echo '{"name":"ponytail","hooks":"./hooks/codex-hooks.json"}' > "$INSTALLED/ponytail/.codex-plugin/plugin.json"
echo '{"hooks":{"SessionStart":[{"hooks":[{"type":"command","command":"true"}]}]}}' > "$INSTALLED/ponytail/hooks/codex-hooks.json"

# codex/claude are stubbed so this test never touches the real CLIs or ~/.codex.
for name in codex claude npx; do
  cat > "$STUB_BIN/$name" <<STUB
#!/usr/bin/env bash
echo "$name \$*" >> "$CALL_LOG"
if [[ "$name" == claude && "\$1 \$2" == "plugin uninstall" && -n "\${CLAUDE_REMOVE_ERROR:-}" ]]; then
  echo "{\"failureCode\":\"\$CLAUDE_REMOVE_ERROR\"}"
  exit 1
fi
[[ "\$*" == *"plugin list"* ]] && echo "$PLUGIN_NAME"
[[ "\$1 \$2" == "plugin add" ]] && echo "{\"installedPath\":\"$INSTALLED/\${3%@*}\"}"
exit 0
STUB
  chmod +x "$STUB_BIN/$name"
done

# A missing harness is installed into our fake PATH; never invoke real npm.
cat > "$STUB_BIN/npm" <<STUB
#!/usr/bin/env bash
echo "npm \$*" >> "$CALL_LOG"
if [[ "\$*" == "install -g @colbymchenry/codegraph@latest" ]]; then
  [[ "\${CODEGRAPH_NPM_FAIL:-0}" == 1 ]] && exit 18
  exit 0
fi
[[ "\$*" == "uninstall -g @colbymchenry/codegraph" ]] && exit 0
[[ "\${HARNESS_NPM_FAIL:-0}" == 1 ]] && exit 17
case "\${3:-}" in
  oh-my-codex@latest) harness=omx ;;
  oh-my-claude-sisyphus@latest) harness=omc ;;
  *) exit 1 ;;
esac
cat > "$STUB_BIN/\$harness" <<CLI
#!/usr/bin/env bash
echo "\$harness \\\$*" >> "$CALL_LOG"
CLI
chmod +x "$STUB_BIN/\$harness"
STUB
chmod +x "$STUB_BIN/npm"

run() {
  HOME="$FAKE_HOME" CODEX_HOME="${TEST_CODEX_HOME:-$FAKE_HOME/.codex}" PATH="$STUB_BIN:/usr/bin:/bin" "$SCRIPT" "$@"
}

expect_usage_error() {
  local out
  if out="$("$SCRIPT" "$@" 2>&1)"; then
    echo "expected usage error for args: $*" >&2
    exit 1
  fi
  [[ "$out" == usage:* ]]
}

expect_calls() {
  [[ "$(cat "$CALL_LOG")" == "$(printf '%s\n' "$@")" ]] || {
    echo "unexpected calls:" >&2; cat "$CALL_LOG" >&2; exit 1
  }
}

trust_count() {
  grep -c "^\[hooks.state.\"$1:" "$FAKE_HOME/.codex/config.toml"
}

expect_usage_error
expect_usage_error codex
expect_usage_error codex bogus
expect_usage_error bogus install

: > "$CALL_LOG"
run codex install >/dev/null
expect_calls \
  "npm install -g @colbymchenry/codegraph@latest" \
  "codex plugin marketplace add $ROOT_DIR --json" \
  "codex plugin add $PLUGIN_ID --json" \
  "codex plugin marketplace add $DEP_SRC --json" \
  "codex plugin add $DEP_ID --json" \
  "codex plugin marketplace add $ELI5_SRC --json" \
  "codex plugin add $ELI5_ID --json" \
  "$IMPECCABLE_CODEX" \
  "npm install -g oh-my-codex@latest" \
  "omx setup --scope user --plugin --clear-merge-agents-policy" \
  "codex plugin list"
[[ "$(trust_count "$PLUGIN_ID:hooks/hooks.json:pre_tool_use")" == 1 ]]
[[ "$(trust_count "$PLUGIN_ID:hooks/hooks.json:session_start")" == 2 ]]
[[ "$(trust_count "$PLUGIN_ID:hooks/hooks.json:post_tool_use")" == 1 ]]
[[ "$(trust_count "$PLUGIN_ID:hooks/hooks.json:user_prompt_submit")" == 1 ]]
[[ "$(trust_count "$PLUGIN_ID:hooks/hooks.json:session_end")" == 1 ]]
[[ "$(trust_count "$DEP_ID:hooks/codex-hooks.json:session_start")" == 1 ]]
grep -qE '^trusted_hash = "sha256:[0-9a-f]{64}"$' "$FAKE_HOME/.codex/config.toml"

: > "$CALL_LOG"
mkdir -p "$FAKE_HOME/.agents/skills/impeccable"
run codex remove >/dev/null
expect_calls \
  "codex plugin remove $PLUGIN_ID --json" \
  "codex plugin remove $DEP_ID --json" \
  "codex plugin remove $ELI5_ID --json" \
  "${MCP_NAMES[@]/#/codex mcp remove }" \
  "npm uninstall -g @colbymchenry/codegraph"
[[ ! -e "$FAKE_HOME/.agents/skills/impeccable" ]]
[[ -x "$STUB_BIN/omx" ]]

: > "$CALL_LOG"
CACHE_DIR="$FAKE_HOME/.codex/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME"
echo 'Keep my user guidance' > "$FAKE_HOME/.codex/AGENTS.md"
mkdir -p "$CACHE_DIR" && touch "$CACHE_DIR/marker"
run codex reload >/dev/null
expect_calls \
  "npm install -g @colbymchenry/codegraph@latest" \
  "codex update" \
  "npm install -g oh-my-codex@latest" \
  "codex plugin remove $PLUGIN_ID --json" \
  "codex plugin marketplace add $ROOT_DIR --json" \
  "codex plugin add $PLUGIN_ID --json" \
  "codex plugin marketplace add $DEP_SRC --json" \
  "codex plugin marketplace upgrade ponytail --json" \
  "codex plugin remove $DEP_ID --json" \
  "codex plugin add $DEP_ID --json" \
  "codex plugin marketplace add $ELI5_SRC --json" \
  "codex plugin marketplace upgrade claude-community --json" \
  "codex plugin remove $ELI5_ID --json" \
  "codex plugin add $ELI5_ID --json" \
  "$IMPECCABLE_CODEX --force" \
  "$OMX_SETUP"
[[ ! -e "$CACHE_DIR" ]]
[[ "$(cat "$FAKE_HOME/.codex/AGENTS.md")" == 'Keep my user guidance' ]]
[[ "$(trust_count "$PLUGIN_ID")" == 2 ]]
[[ "$(trust_count "$DEP_ID")" == 1 ]]

# A custom Codex home must not remove the default home's plugin cache.
CUSTOM_CODEX_HOME="$SANDBOX/custom-codex"
CUSTOM_CACHE="$CUSTOM_CODEX_HOME/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME"
mkdir -p "$CACHE_DIR" "$CUSTOM_CACHE"
touch "$CACHE_DIR/keep" "$CUSTOM_CACHE/stale"
TEST_CODEX_HOME="$CUSTOM_CODEX_HOME" run codex reload >/dev/null
[[ -f "$CACHE_DIR/keep" && ! -e "$CUSTOM_CACHE" ]]

: > "$CALL_LOG"
denied_count() { jq '[.deniedMcpServers[]? | select(.serverName == "claude.ai Notion")] | length' "$FAKE_HOME/.claude/settings.json"; }
mkdir -p "$FAKE_HOME/.claude" && echo '{"model":"keep"}' > "$FAKE_HOME/.claude/settings.json"
run claude install >/dev/null
expect_calls \
  "npm install -g @colbymchenry/codegraph@latest" \
  "claude plugin marketplace add $DEP_SRC" \
  "claude plugin marketplace add $ELI5_SRC" \
  "claude plugin marketplace add $CLAUDE_DEP_SRC" \
  "claude plugin marketplace add $OMC_SRC" \
  "claude plugin marketplace add $ROOT_DIR" \
  "claude plugin install $PLUGIN_ID" \
  "claude plugin marketplace update claude-community" \
  "claude plugin update $ELI5_ID --scope user --yes" \
  "npm install -g oh-my-claude-sisyphus@latest" \
  "omc setup --quiet" \
  "claude plugin details $PLUGIN_ID"

: > "$CALL_LOG"
[[ "$(denied_count)" == 1 ]]

run claude remove >/dev/null
expect_calls \
  "claude plugin uninstall $PLUGIN_ID --keep-data --json" \
  "claude plugin uninstall $DEP_ID --keep-data --json" \
  "claude plugin uninstall $ELI5_ID --keep-data --json" \
  "claude plugin uninstall $CLAUDE_DEP_ID --keep-data --json" \
  "claude plugin uninstall $OMC_ID --keep-data --json" \
  "${MCP_NAMES[@]/#/claude mcp remove -s user }" \
  "npm uninstall -g @colbymchenry/codegraph"

: > "$CALL_LOG"
[[ "$(denied_count)" == 0 ]]
[[ -x "$STUB_BIN/omc" ]]
jq -e '.model == "keep" and (has("deniedMcpServers") | not)' "$FAKE_HOME/.claude/settings.json" >/dev/null

run claude reload >/dev/null
run claude reload >/dev/null
[[ "$(denied_count)" == 1 ]]
: > "$CALL_LOG"
run claude reload >/dev/null
expect_calls \
  "npm install -g @colbymchenry/codegraph@latest" \
  "claude update" \
  "npm install -g oh-my-claude-sisyphus@latest" \
  "claude plugin marketplace add $DEP_SRC" \
  "claude plugin marketplace add $ELI5_SRC" \
  "claude plugin marketplace add $CLAUDE_DEP_SRC" \
  "claude plugin marketplace add $OMC_SRC" \
  "claude plugin marketplace update $MARKETPLACE_NAME" \
  "claude plugin uninstall $PLUGIN_ID --keep-data --json" \
  "claude plugin install $PLUGIN_ID" \
  "claude plugin marketplace update ponytail" \
  "claude plugin update $DEP_ID --scope user --yes" \
  "claude plugin marketplace update claude-community" \
  "claude plugin update $ELI5_ID --scope user --yes" \
  "claude plugin marketplace update impeccable" \
  "claude plugin update $CLAUDE_DEP_ID --scope user --yes" \
  "claude plugin marketplace update omc" \
  "claude plugin update $OMC_ID --scope user --yes" \
  "omc setup --quiet" \
  "claude plugin details $PLUGIN_ID"

for id in "$DEP_ID" "$ELI5_ID" "$CLAUDE_DEP_ID" "$OMC_ID"; do
  jq -e --arg n "${id%@*}" --arg m "${id#*@}" \
    '.dependencies[] | select(.name == $n and .marketplace == $m)' \
    "$ROOT_DIR/.claude-plugin/plugin.json" >/dev/null
  jq -e --arg m "${id#*@}" '.allowCrossMarketplaceDependenciesOn | index($m)' \
    "$ROOT_DIR/.claude-plugin/marketplace.json" >/dev/null
done

# A failed CodeGraph install/update must stop before any plugin mutation.
for tool in codex claude; do
  for action in install reload; do
    : > "$CALL_LOG"
    if CODEGRAPH_NPM_FAIL=1 run "$tool" "$action" >/dev/null 2>&1; then
      echo "expected CodeGraph installation failure for $tool $action" >&2
      exit 1
    fi
    expect_calls "npm install -g @colbymchenry/codegraph@latest"
  done
done

# Keep the shared CLI when the other tool's MCP is enabled, in either direction.
echo '{"mcpServers":{"codegraph":{}}}' > "$FAKE_HOME/.claude.json"
: > "$CALL_LOG"
run codex remove >/dev/null
! grep -q '^npm uninstall -g @colbymchenry/codegraph$' "$CALL_LOG"
echo '{}' > "$FAKE_HOME/.claude.json"
printf '\n[mcp_servers.codegraph]\ncommand = "codegraph"\n' >> "$FAKE_HOME/.codex/config.toml"
: > "$CALL_LOG"
run claude remove >/dev/null
! grep -q '^npm uninstall -g @colbymchenry/codegraph$' "$CALL_LOG"
sed '/^\[mcp_servers.codegraph\]/,$d' "$FAKE_HOME/.codex/config.toml" > "$SANDBOX/config.toml"
mv "$SANDBOX/config.toml" "$FAKE_HOME/.codex/config.toml"

# A failed package install must stop before setup or reporting installation success.
for tool in codex claude; do
  if [[ "$tool" == codex ]]; then harness=omx; else harness=omc; fi
  rm "$STUB_BIN/$harness"
  : > "$CALL_LOG"
  if HARNESS_NPM_FAIL=1 run "$tool" install >/dev/null 2>&1; then
    echo "expected harness installation failure for $tool" >&2
    exit 1
  fi
  ! grep -q "^$harness setup" "$CALL_LOG"
done

# Missing plugins are harmless, but actual uninstall errors must stop removal.
: > "$CALL_LOG"
CLAUDE_REMOVE_ERROR=not_installed run claude remove >/dev/null
grep -q '^claude mcp remove' "$CALL_LOG"
: > "$CALL_LOG"
if CLAUDE_REMOVE_ERROR=permission_denied run claude remove >/dev/null 2>&1; then
  echo 'expected real uninstall error to stop removal' >&2
  exit 1
fi
! grep -q '^claude mcp remove' "$CALL_LOG"

# Removing Codex must leave the shared tunnel running while Claude still uses it.
sleep 20 &
FORWARD_TEST_PID=$!
trap 'kill "$FORWARD_TEST_PID" 2>/dev/null || true; wait "$FORWARD_TEST_PID" 2>/dev/null || true; rm -rf "$SANDBOX"' EXIT
mkdir -p "$FAKE_HOME/.local/state/lukas-plugin"
echo "$FORWARD_TEST_PID" > "$FAKE_HOME/.local/state/lukas-plugin/glitchtip-forward.pid"
echo '{"mcpServers":{"glitchtip":{}}}' > "$FAKE_HOME/.claude.json"
run codex remove >/dev/null
kill -0 "$FORWARD_TEST_PID"
[[ -f "$FAKE_HOME/.local/state/lukas-plugin/glitchtip-forward.pid" ]]

echo "ok"
