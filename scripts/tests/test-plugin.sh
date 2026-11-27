#!/usr/bin/env bash
set -euo pipefail

# Keep the adapter checks offline even when the test replaces HOME.
UV_PYTHON="$(uv python find --offline "${UV_PYTHON:->=3.11}")" || {
  echo 'test-plugin.sh requires an installed Python >=3.11 (or UV_PYTHON); downloads are disabled.' >&2
  exit 1
}
export UV_PYTHON UV_OFFLINE=1

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT="$ROOT_DIR/scripts/plugin.sh"
PLUGIN_NAME="$(jq -r '.name' "$ROOT_DIR/.claude-plugin/plugin.json")"
MARKETPLACE_NAME="$(jq -r '.name' "$ROOT_DIR/.claude-plugin/marketplace.json")"
PLUGIN_ID="${PLUGIN_NAME}@${MARKETPLACE_NAME}"
DEP_ID="ponytail@ponytail"
DEP_SRC="DietrichGebert/ponytail"
ELI5_ID="eli5@claude-community"
ELI5_SRC="anthropics/claude-plugins-community"
SLACK_ID="slack@slack"
SLACK_SRC="slackapi/slack-skills-plugin"
GMAIL_ID="gmail@openai-curated-remote"
CLAUDE_DEP_ID="impeccable@impeccable"
CLAUDE_DEP_SRC="pbakaus/impeccable"
OMC_ID="oh-my-claudecode@omc"
OMC_SRC="Yeachan-Heo/oh-my-claudecode"
OBSIDIAN_ID="obsidian@obsidian-skills"
OBSIDIAN_SRC="kepano/obsidian-skills"
OBSIDIAN_CODEX_ADD="npx -y skills@latest add https://github.com/$OBSIDIAN_SRC --global --agent codex --skill obsidian-markdown obsidian-bases json-canvas obsidian-cli --copy --yes"
OBSIDIAN_CODEX_REMOVE="npx -y skills@latest remove --global --agent codex --skill obsidian-markdown obsidian-bases json-canvas obsidian-cli --yes"
OMX_SETUP="omx setup --scope user --plugin --merge-agents"
TRUST_HOOKS="trust-hooks $PLUGIN_ID oh-my-codex@oh-my-codex-local $DEP_ID $ELI5_ID $SLACK_ID"
MCP_NAMES=($(jq -r '.mcpServers | keys[]' "$ROOT_DIR/mcp/servers.json"))
IMPECCABLE_CODEX="npx -y impeccable@latest install --providers=codex --scope=user --yes --no-hooks"

SANDBOX="$(mktemp -d)"
trap 'rm -rf "$SANDBOX"' EXIT
STUB_BIN="$SANDBOX/bin"
FAKE_HOME="$SANDBOX/home"
INSTALLED="$SANDBOX/installed"
CALL_LOG="$SANDBOX/calls.log"
mkdir -p "$STUB_BIN" "$FAKE_HOME"
DESKTOP_CALLS=(
  "brew update"
  "brew list --formula node"
  "brew upgrade --formula --yes node"
  "brew --prefix node"
  "brew list --cask obsidian"
  "brew upgrade --cask --greedy --no-quit --yes obsidian"
)
cat > "$STUB_BIN/brew" <<STUB
#!/usr/bin/env bash
echo "brew \$*" >> "$CALL_LOG"
[[ "\$*" == "\${BREW_FAIL:-}" ]] && exit 20
[[ "\$*" == "--prefix node" ]] && echo "$SANDBOX"
exit 0
STUB
cat > "$STUB_BIN/uname" <<'STUB'
#!/usr/bin/env bash
echo Darwin
STUB
cat > "$STUB_BIN/pgrep" <<'STUB'
#!/usr/bin/env bash
exit 1
STUB
cat > "$STUB_BIN/node" <<'STUB'
#!/usr/bin/env bash
exit 0
STUB
chmod +x "$STUB_BIN/brew" "$STUB_BIN/uname" "$STUB_BIN/pgrep" "$STUB_BIN/node"
ln -s "$(command -v jq)" "$STUB_BIN/jq"
# The real Codex approval round trip is covered by test-codex-trust-hooks.sh.
cat > "$STUB_BIN/uv" <<STUB
#!/usr/bin/env bash
if [[ "\$2" == --script && "\$3" == */codex-trust-hooks.py ]]; then
  shift 3
  echo "trust-hooks \$*" >> "$CALL_LOG"
  exit 0
fi
exec "$(command -v uv)" "\$@"
STUB
chmod +x "$STUB_BIN/uv"

# codex/claude are stubbed so this test never touches the real CLIs or ~/.codex.
for name in codex claude npx; do
  cat > "$STUB_BIN/$name" <<STUB
#!/usr/bin/env bash
echo "$name \$*" >> "$CALL_LOG"
if [[ "$name" == npx && "\$*" == "-y skills@latest "* && "\${SKILLS_FAIL:-0}" == 1 ]]; then
  exit 19
fi
if [[ "$name" == claude && "\$1 \$2" == "plugin uninstall" && -n "\${CLAUDE_REMOVE_ERROR:-}" ]]; then
  echo "{\"failureCode\":\"\$CLAUDE_REMOVE_ERROR\"}"
  exit 1
fi
if [[ "$name" == codex && "\$*" == "plugin marketplace add \${CODEX_MARKETPLACE_CONFLICT:-} --json" && ! -e "$SANDBOX/conflict-cleared" ]]; then
  echo "Error: marketplace 'ponytail' is already added from a different source; remove it before adding this source" >&2
  exit 1
fi
[[ "\$*" == "plugin marketplace remove ponytail" ]] && touch "$SANDBOX/conflict-cleared"
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
  HOME="$FAKE_HOME" CLAUDE_CONFIG_DIR="$FAKE_HOME/.claude" CODEX_HOME="${TEST_CODEX_HOME:-$FAKE_HOME/.codex}" PATH="$STUB_BIN:/usr/bin:/bin" "$SCRIPT" "$@"
}
run_with_custom_claude_config() {
  HOME="$FAKE_HOME" CLAUDE_CONFIG_DIR="$SANDBOX/custom-claude-config" CODEX_HOME="${TEST_CODEX_HOME:-$FAKE_HOME/.codex}" PATH="$STUB_BIN:/usr/bin:/bin" "$SCRIPT" "$@"
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

expect_usage_error
expect_usage_error codex
expect_usage_error codex bogus
expect_usage_error bogus install

: > "$CALL_LOG"
run codex install >/dev/null
expect_calls \
  "${DESKTOP_CALLS[@]}" \
  "npm install -g @colbymchenry/codegraph@latest" \
  "codex plugin marketplace add $ROOT_DIR --json" \
  "codex plugin add $PLUGIN_ID --json" \
  "codex plugin marketplace add $DEP_SRC --json" \
  "codex plugin add $DEP_ID --json" \
  "codex plugin marketplace add $ELI5_SRC --json" \
  "codex plugin add $ELI5_ID --json" \
  "codex plugin marketplace add $SLACK_SRC --json" \
  "codex plugin add $SLACK_ID --json" \
  "codex plugin add $GMAIL_ID --json" \
  "$IMPECCABLE_CODEX" \
  "$OBSIDIAN_CODEX_ADD" \
  "npm install -g oh-my-codex@latest" \
  "omx setup --scope user --plugin --clear-merge-agents-policy" \
  "codex plugin list" \
  "$TRUST_HOOKS"
[[ -f "$FAKE_HOME/.codex/agents/basic_backend.toml" ]]

: > "$CALL_LOG"
mkdir -p "$FAKE_HOME/.agents/skills/impeccable"
run codex remove >/dev/null
expect_calls \
  "codex plugin remove $PLUGIN_ID --json" \
  "codex plugin remove $DEP_ID --json" \
  "codex plugin remove $ELI5_ID --json" \
  "codex plugin remove $SLACK_ID --json" \
  "codex plugin remove $GMAIL_ID --json" \
  "$OBSIDIAN_CODEX_REMOVE" \
  "${MCP_NAMES[@]/#/codex mcp remove }" \
  "npm uninstall -g @colbymchenry/codegraph"
[[ ! -e "$FAKE_HOME/.agents/skills/impeccable" ]]
[[ ! -e "$FAKE_HOME/.codex/agents/basic_backend.toml" ]]
[[ -x "$STUB_BIN/omx" ]]

: > "$CALL_LOG"
CACHE_DIR="$FAKE_HOME/.codex/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME"
echo 'Keep my user guidance' > "$FAKE_HOME/.codex/AGENTS.md"
mkdir -p "$CACHE_DIR" && touch "$CACHE_DIR/marker"
run codex reload >/dev/null
expect_calls \
  "${DESKTOP_CALLS[@]}" \
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
  "codex plugin marketplace add $SLACK_SRC --json" \
  "codex plugin marketplace upgrade slack --json" \
  "codex plugin remove $SLACK_ID --json" \
  "codex plugin add $SLACK_ID --json" \
  "codex plugin remove $GMAIL_ID --json" \
  "codex plugin add $GMAIL_ID --json" \
  "$IMPECCABLE_CODEX --force" \
  "$OBSIDIAN_CODEX_ADD" \
  "$OMX_SETUP" \
  "$TRUST_HOOKS"
[[ ! -e "$CACHE_DIR" ]]
[[ "$(cat "$FAKE_HOME/.codex/AGENTS.md")" == 'Keep my user guidance' ]]

# An orphaned marketplace root is removed and re-added instead of failing the install.
: > "$CALL_LOG"
CODEX_MARKETPLACE_CONFLICT="$DEP_SRC" run codex install >/dev/null 2>&1
grep -qx "codex plugin marketplace remove ponytail" "$CALL_LOG"
[[ "$(grep -cx "codex plugin marketplace add $DEP_SRC --json" "$CALL_LOG")" == 2 ]]
grep -qx "codex plugin add $DEP_ID --json" "$CALL_LOG"

# A custom Codex home must not remove the default home's plugin cache.
CUSTOM_CODEX_HOME="$SANDBOX/custom-codex"
CUSTOM_CACHE="$CUSTOM_CODEX_HOME/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME"
mkdir -p "$CACHE_DIR" "$CUSTOM_CACHE"
touch "$CACHE_DIR/keep" "$CUSTOM_CACHE/stale"
TEST_CODEX_HOME="$CUSTOM_CODEX_HOME" run codex reload >/dev/null
[[ -f "$CACHE_DIR/keep" && ! -e "$CUSTOM_CACHE" ]]
[[ -f "$CUSTOM_CODEX_HOME/agents/basic_backend.toml" ]]

: > "$CALL_LOG"
denied_count() { jq '[.deniedMcpServers[]? | select(.serverName == "claude.ai Notion")] | length' "$FAKE_HOME/.claude/settings.json"; }
mkdir -p "$FAKE_HOME/.claude" && echo '{"model":"keep"}' > "$FAKE_HOME/.claude/settings.json"
run claude install >/dev/null
expect_calls \
  "${DESKTOP_CALLS[@]}" \
  "npm install -g @colbymchenry/codegraph@latest" \
  "claude plugin marketplace add $DEP_SRC" \
  "claude plugin marketplace add $ELI5_SRC" \
  "claude plugin marketplace add $SLACK_SRC" \
  "claude plugin marketplace add $CLAUDE_DEP_SRC" \
  "claude plugin marketplace add $OMC_SRC" \
  "claude plugin marketplace add $OBSIDIAN_SRC" \
  "claude plugin marketplace add $ROOT_DIR" \
  "claude plugin install $PLUGIN_ID" \
  "claude plugin marketplace update claude-community" \
  "claude plugin update $ELI5_ID --scope user --yes" \
  "npm install -g oh-my-claude-sisyphus@latest" \
  "omc setup --quiet" \
  "claude plugin details $PLUGIN_ID"

: > "$CALL_LOG"
[[ "$(denied_count)" == 1 ]]
jq -e '((.env // {}) | has("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS") | not) and .env.MCP_TOOL_TIMEOUT == "325000"' "$FAKE_HOME/.claude/settings.json" >/dev/null

run claude remove >/dev/null
expect_calls \
  "claude plugin uninstall $PLUGIN_ID --keep-data --json" \
  "claude plugin uninstall $DEP_ID --keep-data --json" \
  "claude plugin uninstall $ELI5_ID --keep-data --json" \
  "claude plugin uninstall $SLACK_ID --keep-data --json" \
  "claude plugin uninstall $CLAUDE_DEP_ID --keep-data --json" \
  "claude plugin uninstall $OMC_ID --keep-data --json" \
  "claude plugin uninstall $OBSIDIAN_ID --keep-data --json" \
  "${MCP_NAMES[@]/#/claude mcp remove -s user }" \
  "npm uninstall -g @colbymchenry/codegraph"

: > "$CALL_LOG"
[[ "$(denied_count)" == 0 ]]
[[ -x "$STUB_BIN/omc" ]]
jq -e '.model == "keep" and (has("deniedMcpServers") | not) and ((.env // {}) | has("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS") or has("MCP_TOOL_TIMEOUT") | not)' "$FAKE_HOME/.claude/settings.json" >/dev/null

# Restore a pre-existing value on removal, but do not claim a setting that was already enabled.
echo '{"model":"keep","env":{"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS":"0","MCP_TOOL_TIMEOUT":"60000","OTHER":"keep"}}' > "$FAKE_HOME/.claude/settings.json"
run claude install >/dev/null
jq -e '.env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS == "0" and .env.OTHER == "keep"' "$FAKE_HOME/.claude/settings.json" >/dev/null
run claude remove >/dev/null
jq -e '.model == "keep" and .env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS == "0" and .env.MCP_TOOL_TIMEOUT == "60000" and .env.OTHER == "keep"' "$FAKE_HOME/.claude/settings.json" >/dev/null

echo '{"env":{"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS":"1"}}' > "$FAKE_HOME/.claude/settings.json"
run claude install >/dev/null
run claude remove >/dev/null
jq -e '.env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS == "1"' "$FAKE_HOME/.claude/settings.json" >/dev/null

# Preserve a later user override instead of restoring over it.
echo '{"model":"keep"}' > "$FAKE_HOME/.claude/settings.json"
run claude install >/dev/null
jq '.env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS = "0"' "$FAKE_HOME/.claude/settings.json" > "$SANDBOX/settings.json"
mv "$SANDBOX/settings.json" "$FAKE_HOME/.claude/settings.json"
run claude remove >/dev/null
jq -e '.model == "keep" and .env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS == "0"' "$FAKE_HOME/.claude/settings.json" >/dev/null

# Honor Claude's configured settings directory, including creating it when absent.
run_with_custom_claude_config claude install >/dev/null
jq -e '((.env // {}) | has("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS") | not)' "$SANDBOX/custom-claude-config/settings.json" >/dev/null
run_with_custom_claude_config claude remove >/dev/null
jq -e '((.env // {}) | has("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS") | not)' "$SANDBOX/custom-claude-config/settings.json" >/dev/null

# Pathless legacy records cannot prove which configuration they belong to.
legacy_state="$FAKE_HOME/.local/state/lukas-plugin"
mkdir -p "$legacy_state"
echo '{"managed":true,"had_value":true,"previous":"0"}' > "$legacy_state/agent-teams.json"
echo '{"managed":true,"had_value":true,"previous":"60000"}' > "$legacy_state/mcp-tool-timeout.json"
cp "$legacy_state/agent-teams.json" "$SANDBOX/legacy-teams.json"
cp "$legacy_state/mcp-tool-timeout.json" "$SANDBOX/legacy-timeout.json"
echo '{"env":{"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS":"1","MCP_TOOL_TIMEOUT":"325000"}}' > "$FAKE_HOME/.claude/settings.json"
cp "$FAKE_HOME/.claude/settings.json" "$SANDBOX/custom-claude-config/settings.json"
run_with_custom_claude_config claude install >/dev/null 2>"$SANDBOX/legacy-warning"
run_with_custom_claude_config claude remove >/dev/null 2>>"$SANDBOX/legacy-warning"
run claude install >/dev/null 2>>"$SANDBOX/legacy-warning"
run claude remove >/dev/null 2>>"$SANDBOX/legacy-warning"
grep -q 'state without matching settings path' "$SANDBOX/legacy-warning"
for settings in "$FAKE_HOME/.claude/settings.json" "$SANDBOX/custom-claude-config/settings.json"; do
  jq -e '.env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS == "1" and .env.MCP_TOOL_TIMEOUT == "325000"' "$settings" >/dev/null
done
cmp "$legacy_state/agent-teams.json" "$SANDBOX/legacy-teams.json"
cmp "$legacy_state/mcp-tool-timeout.json" "$SANDBOX/legacy-timeout.json"
rm "$legacy_state/agent-teams.json" "$legacy_state/mcp-tool-timeout.json"

# Each settings destination restores only its own timeout value.
echo '{"env":{"MCP_TOOL_TIMEOUT":"111"}}' > "$FAKE_HOME/.claude/settings.json"
echo '{"env":{"MCP_TOOL_TIMEOUT":"222"}}' > "$SANDBOX/custom-claude-config/settings.json"
run claude install >/dev/null
run_with_custom_claude_config claude install >/dev/null
for settings in "$FAKE_HOME/.claude/settings.json" "$SANDBOX/custom-claude-config/settings.json"; do
  state_dir="$legacy_state/claude-$(printf '%s' "$settings" | shasum -a 256 | cut -d ' ' -f 1)"
  jq -e --arg path "$settings" '.settings_path == $path' "$state_dir/mcp-tool-timeout.json" >/dev/null
done
run_with_custom_claude_config claude remove >/dev/null
jq -e '.env.MCP_TOOL_TIMEOUT == "222"' "$SANDBOX/custom-claude-config/settings.json" >/dev/null
jq -e '.env.MCP_TOOL_TIMEOUT == "325000"' "$FAKE_HOME/.claude/settings.json" >/dev/null
run claude remove >/dev/null
jq -e '.env.MCP_TOOL_TIMEOUT == "111"' "$FAKE_HOME/.claude/settings.json" >/dev/null

# A path-bound legacy record is restored only when its own configuration is used.
echo '{"model":"keep","env":{"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS":"1"}}' > "$FAKE_HOME/.claude/settings.json"
echo '{"env":{"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS":"1"}}' > "$SANDBOX/custom-claude-config/settings.json"
mkdir -p "$FAKE_HOME/.local/state/lukas-plugin"
jq -n --arg path "$FAKE_HOME/.claude/settings.json" \
  '{managed:true,settings_path:$path,had_value:false,previous:null}' > "$legacy_state/agent-teams.json"
run_with_custom_claude_config claude install >/dev/null 2>"$SANDBOX/legacy-warning"
run_with_custom_claude_config claude remove >/dev/null 2>>"$SANDBOX/legacy-warning"
jq -e '.env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS == "1"' "$SANDBOX/custom-claude-config/settings.json" >/dev/null
[[ -f "$legacy_state/agent-teams.json" ]]

run claude reload >/dev/null
run claude reload >/dev/null
[[ "$(denied_count)" == 1 ]]
jq -e '((.env // {}) | has("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS") | not)' "$FAKE_HOME/.claude/settings.json" >/dev/null
[[ ! -f "$legacy_state/agent-teams.json" ]]
: > "$CALL_LOG"
run claude reload >/dev/null
expect_calls \
  "${DESKTOP_CALLS[@]}" \
  "npm install -g @colbymchenry/codegraph@latest" \
  "claude update" \
  "npm install -g oh-my-claude-sisyphus@latest" \
  "claude plugin marketplace add $DEP_SRC" \
  "claude plugin marketplace add $ELI5_SRC" \
  "claude plugin marketplace add $SLACK_SRC" \
  "claude plugin marketplace add $CLAUDE_DEP_SRC" \
  "claude plugin marketplace add $OMC_SRC" \
  "claude plugin marketplace add $OBSIDIAN_SRC" \
  "claude plugin marketplace update $MARKETPLACE_NAME" \
  "claude plugin uninstall $PLUGIN_ID --keep-data --json" \
  "claude plugin install $PLUGIN_ID" \
  "claude plugin marketplace update ponytail" \
  "claude plugin update $DEP_ID --scope user --yes" \
  "claude plugin marketplace update claude-community" \
  "claude plugin update $ELI5_ID --scope user --yes" \
  "claude plugin marketplace update slack" \
  "claude plugin update $SLACK_ID --scope user --yes" \
  "claude plugin marketplace update impeccable" \
  "claude plugin update $CLAUDE_DEP_ID --scope user --yes" \
  "claude plugin marketplace update omc" \
  "claude plugin update $OMC_ID --scope user --yes" \
  "claude plugin marketplace update obsidian-skills" \
  "claude plugin update $OBSIDIAN_ID --scope user --yes" \
  "omc setup --quiet" \
  "claude plugin details $PLUGIN_ID"

for id in "$DEP_ID" "$ELI5_ID" "$SLACK_ID" "$CLAUDE_DEP_ID" "$OMC_ID" "$OBSIDIAN_ID"; do
  jq -e --arg n "${id%@*}" --arg m "${id#*@}" \
    '.dependencies[] | select(.name == $n and .marketplace == $m)' \
    "$ROOT_DIR/.claude-plugin/plugin.json" >/dev/null
  jq -e --arg m "${id#*@}" '.allowCrossMarketplaceDependenciesOn | index($m)' \
    "$ROOT_DIR/.claude-plugin/marketplace.json" >/dev/null
done

# Obsidian setup checks PATH without launching the app; its absence does not block Markdown use.
out="$(run codex install)"
[[ "$out" == *"Obsidian CLI: not on PATH."* ]]
cat > "$STUB_BIN/obsidian" <<STUB
#!/usr/bin/env bash
echo "obsidian \$*" >> "$CALL_LOG"
exit 99
STUB
chmod +x "$STUB_BIN/obsidian"
for tool in codex claude; do
  : > "$CALL_LOG"
  out="$(run "$tool" install)"
  [[ "$out" == *"Obsidian CLI: found on PATH (app connection not checked)."* ]]
  ! grep -q '^obsidian ' "$CALL_LOG"
done
rm "$STUB_BIN/obsidian"

# Dependency failures must propagate, with no setup or success status after a failed add.
for action in install reload; do
  : > "$CALL_LOG"
  if out="$(SKILLS_FAIL=1 run codex "$action" 2>&1)"; then
    echo "expected Obsidian skill installation failure for $action" >&2
    exit 1
  fi
  grep -qx "$OBSIDIAN_CODEX_ADD" "$CALL_LOG"
  ! grep -q '^omx setup' "$CALL_LOG"
  [[ "$out" != *"Obsidian CLI:"* ]]
done
: > "$CALL_LOG"
if SKILLS_FAIL=1 run codex remove >/dev/null 2>&1; then
  echo 'expected Obsidian skill removal failure' >&2
  exit 1
fi
! grep -q '^codex mcp remove' "$CALL_LOG"

# A failed CodeGraph install/update must stop before any plugin mutation.
for tool in codex claude; do
  for action in install reload; do
    : > "$CALL_LOG"
    if CODEGRAPH_NPM_FAIL=1 run "$tool" "$action" >/dev/null 2>&1; then
      echo "expected CodeGraph installation failure for $tool $action" >&2
      exit 1
    fi
    expect_calls "${DESKTOP_CALLS[@]}" "npm install -g @colbymchenry/codegraph@latest"
  done
done

# Desktop setup failures stop both hosts before npm or plugin mutation.
for tool in codex claude; do
  for action in install reload; do
    : > "$CALL_LOG"
    if BREW_FAIL=update run "$tool" "$action" >/dev/null 2>&1; then
      echo "expected desktop setup failure for $tool $action" >&2
      exit 1
    fi
    expect_calls "brew update"
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

# OMX warns about a stale plugin cache: setup runs the repair it asks for, once.
cat > "$STUB_BIN/omx" <<STUB
#!/usr/bin/env bash
echo "omx \$*" >> "$CALL_LOG"
[[ "\$*" == *--scope* ]] && echo "warning: local Codex plugin cache is not safe to use as current (run omx setup --plugin --repair-plugin-cache)"
exit 0
STUB
: > "$CALL_LOG"
run codex reload >/dev/null
[[ "$(grep -c '^omx setup --plugin --repair-plugin-cache$' "$CALL_LOG")" == 1 ]]
grep -q "^$OMX_SETUP$" "$CALL_LOG"
[[ "$(tail -2 "$CALL_LOG")" == "$(printf '%s\n' "omx setup --plugin --repair-plugin-cache" "$TRUST_HOOKS")" ]]

echo "ok"
