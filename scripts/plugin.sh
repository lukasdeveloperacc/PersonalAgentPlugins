#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "usage: $(basename "$0") <codex|claude> <install|remove|reload>" >&2
  exit 1
}

TOOL="${1:-}"
ACTION="${2:-}"
[ -n "$TOOL" ] && [ -n "$ACTION" ] || usage
case "$TOOL" in codex|claude) ;; *) usage ;; esac
case "$ACTION" in
  install|reload) npm install -g @colbymchenry/codegraph@latest ;;
  remove) ;;
  *) usage ;;
esac

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLUGIN_NAME="$(jq -r '.name' "$ROOT_DIR/.claude-plugin/plugin.json")"
MARKETPLACE_NAME="$(jq -r '.name' "$ROOT_DIR/.claude-plugin/marketplace.json")"
PLUGIN_ID="${PLUGIN_NAME}@${MARKETPLACE_NAME}"

# "<plugin>@<marketplace> <marketplace source>". Claude also needs each in .claude-plugin/plugin.json "dependencies".
ELI5_MARKETPLACE="claude-community"
ELI5_ID="eli5@$ELI5_MARKETPLACE"
ELI5_SRC="anthropics/claude-plugins-community"
CODEX_DEPS=(
  "ponytail@ponytail DietrichGebert/ponytail"
  "$ELI5_ID $ELI5_SRC"
)
# impeccable ships no Codex plugin, so install_codex_deps puts its skill in ~/.agents/skills via its own CLI.
CLAUDE_DEPS=(
  "${CODEX_DEPS[@]}"
  "impeccable@impeccable pbakaus/impeccable"
  "oh-my-claudecode@omc Yeachan-Heo/oh-my-claudecode"
)

setup_claude_harness() {
  if ! command -v omc >/dev/null 2>&1; then
    npm install -g oh-my-claude-sisyphus@latest
  fi
  omc setup --quiet </dev/null
}

setup_codex_harness() {
  if ! command -v omx >/dev/null 2>&1; then
    npm install -g oh-my-codex@latest
  fi
  # OMX's merge flag skips initial AGENTS.md creation; use it only for an existing file.
  if [ -e "${CODEX_HOME:-$HOME/.codex}/AGENTS.md" ]; then
    omx setup --scope user --plugin --merge-agents </dev/null
  else
    omx setup --scope user --plugin --clear-merge-agents-policy </dev/null
  fi
}

# Codex skips plugin hooks until trusted; write the trust hashes it would write after TUI review.
trust_codex_hooks() {
  local root="$1" id="$2" hooks_rel manifest="$1/.codex-plugin/plugin.json"
  [ -f "$manifest" ] || return 0
  hooks_rel="$(jq -r '.hooks // empty' "$manifest")"
  [ -n "$hooks_rel" ] || return 0
  hooks_rel="${hooks_rel#./}"
  uv run --script "$ROOT_DIR/scripts/codex-trust-hooks.py" \
    "$root/$hooks_rel" "$id:$hooks_rel" "${CODEX_HOME:-$HOME/.codex}/config.toml"
}

install_codex_deps() {
  local dep id src out refresh="${1:-}"
  for dep in "${CODEX_DEPS[@]}"; do
    read -r id src <<<"$dep"
    codex plugin marketplace add "$src" --json
    if [ "$refresh" = "--refresh" ]; then
      codex plugin marketplace upgrade "${id#*@}" --json
      codex plugin remove "$id" --json
    fi
    out="$(codex plugin add "$id" --json)"
    echo "$out"
    trust_codex_hooks "$(jq -r '.installedPath' <<<"$out")" "$id"
  done
  # --no-hooks: its Codex hook is project-local (.codex/hooks.json), not something a user-scope install can set up.
  if [ "$refresh" = "--refresh" ]; then
    npx -y impeccable@latest install --providers=codex --scope=user --yes --no-hooks --force
  else
    npx -y impeccable@latest install --providers=codex --scope=user --yes --no-hooks
  fi
}

remove_codex_deps() {
  local dep id src
  for dep in "${CODEX_DEPS[@]}"; do
    read -r id src <<<"$dep"
    codex plugin remove "$id" --json
  done
  # impeccable's CLI has no uninstall; this is the folder install_codex_deps created.
  rm -rf "$HOME/.agents/skills/impeccable"
}

# Not --prune: it skips deps the user had installed by hand before (no "auto" flag).
remove_claude_plugin() {
  local result
  if result="$(claude plugin uninstall "$1" --keep-data --json 2>/dev/null)"; then
    echo "$result"
  elif [ "$(jq -r '.failureCode // empty' <<<"$result")" = not_installed ]; then
    echo "Already removed: $1"
  else
    echo "Failed to uninstall $1: $result" >&2
    return 1
  fi
}

remove_claude_deps() {
  local dep id src
  for dep in "${CLAUDE_DEPS[@]}"; do
    read -r id src <<<"$dep"
    remove_claude_plugin "$id"
  done
}

# claude.ai's Notion connector is tied to the claude.ai login's Notion account; block it so
# mcp/servers.json's notion (own OAuth, any account) is the only one. User settings honor deniedMcpServers.
DENIED_CONNECTOR="claude.ai Notion"
CLAUDE_SETTINGS="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/settings.json"
CLAUDE_AGENT_TEAMS_KEY="CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"
CLAUDE_AGENT_TEAMS_STATE="$HOME/.local/state/lukas-plugin/agent-teams.json"

edit_claude_settings() {
  local filter="$1" tmp
  shift
  mkdir -p "$(dirname "$CLAUDE_SETTINGS")"
  [ -f "$CLAUDE_SETTINGS" ] || echo '{}' > "$CLAUDE_SETTINGS"
  tmp="$(mktemp)"
  jq "$@" "$filter" "$CLAUDE_SETTINGS" > "$tmp" && mv "$tmp" "$CLAUDE_SETTINGS"
}
deny_claude_connector() { edit_claude_settings '.deniedMcpServers = ((.deniedMcpServers // []) - [{serverName: $n}] + [{serverName: $n}])' --arg n "$DENIED_CONNECTOR"; }
allow_claude_connector() { edit_claude_settings '.deniedMcpServers = ((.deniedMcpServers // []) - [{serverName: $n}]) | if .deniedMcpServers == [] then del(.deniedMcpServers) else . end' --arg n "$DENIED_CONNECTOR"; }

enable_claude_agent_teams() {
  local had_value=false previous=null tmp state_dir
  if [ -f "$CLAUDE_AGENT_TEAMS_STATE" ] && ! jq -e \
    '.managed == true and (.had_value | type == "boolean") and has("previous")' \
    "$CLAUDE_AGENT_TEAMS_STATE" >/dev/null; then
    echo "Cannot configure Claude Agent Teams: invalid state file $CLAUDE_AGENT_TEAMS_STATE" >&2
    return 1
  fi
  if [ -f "$CLAUDE_SETTINGS" ]; then
    jq -e '(.env // {}) | type == "object"' "$CLAUDE_SETTINGS" >/dev/null || {
      echo "Cannot configure Claude Agent Teams: .env in $CLAUDE_SETTINGS must be an object" >&2
      return 1
    }
    if jq -e --arg key "$CLAUDE_AGENT_TEAMS_KEY" '.env[$key] == "1"' "$CLAUDE_SETTINGS" >/dev/null; then
      return 0
    fi
  fi

  if [ ! -f "$CLAUDE_AGENT_TEAMS_STATE" ]; then
    if [ -f "$CLAUDE_SETTINGS" ] && jq -e --arg key "$CLAUDE_AGENT_TEAMS_KEY" '.env | has($key)' "$CLAUDE_SETTINGS" >/dev/null; then
      had_value=true
      previous="$(jq -c --arg key "$CLAUDE_AGENT_TEAMS_KEY" '.env[$key]' "$CLAUDE_SETTINGS")"
    fi
    state_dir="$(dirname "$CLAUDE_AGENT_TEAMS_STATE")"
    mkdir -p "$state_dir"
    tmp="$(mktemp "$state_dir/agent-teams.XXXXXX")"
    jq -n --argjson had_value "$had_value" --argjson previous "$previous" \
      '{managed: true, had_value: $had_value, previous: $previous}' > "$tmp"
    mv "$tmp" "$CLAUDE_AGENT_TEAMS_STATE"
  fi

  edit_claude_settings '.env = ((.env // {}) + {($key): "1"})' --arg key "$CLAUDE_AGENT_TEAMS_KEY"
}

restore_claude_agent_teams() {
  local had_value previous
  [ -f "$CLAUDE_AGENT_TEAMS_STATE" ] || return 0
  jq -e '.managed == true and (.had_value | type == "boolean") and has("previous")' \
    "$CLAUDE_AGENT_TEAMS_STATE" >/dev/null || {
    echo "Cannot restore Claude Agent Teams setting: invalid state file $CLAUDE_AGENT_TEAMS_STATE" >&2
    return 1
  }

  if [ -f "$CLAUDE_SETTINGS" ] && jq -e --arg key "$CLAUDE_AGENT_TEAMS_KEY" \
    '(.env | type) == "object" and .env[$key] == "1"' "$CLAUDE_SETTINGS" >/dev/null; then
    had_value="$(jq -r '.had_value' "$CLAUDE_AGENT_TEAMS_STATE")"
    if [ "$had_value" = true ]; then
      previous="$(jq -c '.previous' "$CLAUDE_AGENT_TEAMS_STATE")"
      edit_claude_settings '.env = ((.env // {}) + {($key): $previous})' \
        --arg key "$CLAUDE_AGENT_TEAMS_KEY" --argjson previous "$previous"
    else
      edit_claude_settings 'del(.env[$key]) | if .env == {} then del(.env) else . end' \
        --arg key "$CLAUDE_AGENT_TEAMS_KEY"
    fi
  fi
  rm "$CLAUDE_AGENT_TEAMS_STATE"
}

# Claude installs dependencies itself, but only from marketplaces it already knows.
add_claude_dep_marketplaces() {
  local dep id src
  for dep in "${CLAUDE_DEPS[@]}"; do
    read -r id src <<<"$dep"
    claude plugin marketplace add "$src"
  done
}

update_claude_deps() {
  local dep id src
  for dep in "${CLAUDE_DEPS[@]}"; do
    read -r id src <<<"$dep"
    claude plugin marketplace update "${id#*@}"
    claude plugin update "$id" --scope user --yes
  done
}

case "$TOOL" in
  codex)
    case "$ACTION" in
      install)
        codex plugin marketplace add "$ROOT_DIR" --json
        codex plugin add "$PLUGIN_ID" --json
        trust_codex_hooks "$ROOT_DIR" "$PLUGIN_ID"
        install_codex_deps
        setup_codex_harness
        codex plugin list | grep "$PLUGIN_NAME"
        ;;
      remove)
        codex plugin remove "$PLUGIN_ID" --json
        remove_codex_deps
        "$ROOT_DIR/skills/mcp-setup/scripts/mcp.sh" codex disable
        ;;
      reload)
        codex update </dev/null
        npm install -g oh-my-codex@latest
        codex plugin remove "$PLUGIN_ID" --json
        rm -rf "${CODEX_HOME:-$HOME/.codex}/plugins/cache/${MARKETPLACE_NAME}/${PLUGIN_NAME}"
        codex plugin marketplace add "$ROOT_DIR" --json
        codex plugin add "$PLUGIN_ID" --json
        trust_codex_hooks "$ROOT_DIR" "$PLUGIN_ID"
        install_codex_deps --refresh
        setup_codex_harness
        ;;
      *) usage ;;
    esac
    ;;
  claude)
    case "$ACTION" in
      install)
        add_claude_dep_marketplaces
        claude plugin marketplace add "$ROOT_DIR"
        claude plugin install "$PLUGIN_ID"
        claude plugin marketplace update "$ELI5_MARKETPLACE"
        claude plugin update "$ELI5_ID" --scope user --yes
        deny_claude_connector
        setup_claude_harness
        claude plugin details "$PLUGIN_ID"
        enable_claude_agent_teams
        ;;
      remove)
        remove_claude_plugin "$PLUGIN_ID"
        remove_claude_deps
        "$ROOT_DIR/skills/mcp-setup/scripts/mcp.sh" claude disable
        allow_claude_connector
        restore_claude_agent_teams
        ;;
      reload)
        claude update </dev/null
        npm install -g oh-my-claude-sisyphus@latest
        add_claude_dep_marketplaces
        claude plugin marketplace update "$MARKETPLACE_NAME"
        # `plugin update` is a no-op while the version stays 0.1.0, so reinstall to refresh the cache.
        remove_claude_plugin "$PLUGIN_ID"
        claude plugin install "$PLUGIN_ID"
        update_claude_deps
        deny_claude_connector
        setup_claude_harness
        claude plugin details "$PLUGIN_ID"
        enable_claude_agent_teams
        ;;
      *) usage ;;
    esac
    ;;
  *) usage ;;
esac

if [ "$ACTION" = remove ]; then
  # Keep the shared CLI while the other tool still has its MCP enabled.
  if [ "$TOOL" = codex ]; then other_tool=claude; else other_tool=codex; fi
  if ! "$ROOT_DIR/skills/mcp-setup/scripts/mcp.sh" "$other_tool" list | grep -qx 'codegraph on'; then
    npm uninstall -g @colbymchenry/codegraph
  fi
fi
