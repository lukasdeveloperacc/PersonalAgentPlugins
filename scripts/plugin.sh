#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "usage: $(basename "$0") <codex|claude> <install|remove|reload>" >&2
  exit 1
}

TOOL="${1:-}"
ACTION="${2:-}"
[ -n "$TOOL" ] && [ -n "$ACTION" ] || usage

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
  python3 "$ROOT_DIR/scripts/codex-trust-hooks.py" \
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
  npx -y impeccable install --providers=codex --scope=user --yes --no-hooks
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
CLAUDE_SETTINGS="$HOME/.claude/settings.json"

edit_claude_settings() {
  local tmp
  [ -f "$CLAUDE_SETTINGS" ] || echo '{}' > "$CLAUDE_SETTINGS"
  tmp="$(mktemp)"
  jq --arg n "$DENIED_CONNECTOR" "$1" "$CLAUDE_SETTINGS" > "$tmp" && mv "$tmp" "$CLAUDE_SETTINGS"
}
deny_claude_connector() { edit_claude_settings '.deniedMcpServers = ((.deniedMcpServers // []) - [{serverName: $n}] + [{serverName: $n}])'; }
allow_claude_connector() { edit_claude_settings '.deniedMcpServers = ((.deniedMcpServers // []) - [{serverName: $n}]) | if .deniedMcpServers == [] then del(.deniedMcpServers) else . end'; }

# Claude installs dependencies itself, but only from marketplaces it already knows.
add_claude_dep_marketplaces() {
  local dep id src
  for dep in "${CLAUDE_DEPS[@]}"; do
    read -r id src <<<"$dep"
    claude plugin marketplace add "$src"
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
        "$ROOT_DIR/scripts/mcp.sh" codex disable
        ;;
      reload)
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
        ;;
      remove)
        remove_claude_plugin "$PLUGIN_ID"
        remove_claude_deps
        "$ROOT_DIR/scripts/mcp.sh" claude disable
        allow_claude_connector
        ;;
      reload)
        add_claude_dep_marketplaces
        claude plugin marketplace update "$MARKETPLACE_NAME"
        # `plugin update` is a no-op while the version stays 0.1.0, so reinstall to refresh the cache.
        remove_claude_plugin "$PLUGIN_ID"
        claude plugin install "$PLUGIN_ID"
        claude plugin marketplace update "$ELI5_MARKETPLACE"
        claude plugin update "$ELI5_ID" --scope user --yes
        deny_claude_connector
        setup_claude_harness
        claude plugin details "$PLUGIN_ID"
        ;;
      *) usage ;;
    esac
    ;;
  *) usage ;;
esac
