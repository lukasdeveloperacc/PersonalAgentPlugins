#!/usr/bin/env bash
set -euo pipefail

SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/codex-trust-hooks.py"
SANDBOX="$(mktemp -d)"
trap 'rm -rf "$SANDBOX"' EXIT
export CODEX_HOME="$SANDBOX/codex"
MARKET="$SANDBOX/market"
CONFIG="$CODEX_HOME/config.toml"
KEY='fixture@local:hooks/hooks.json:session_start:0:0'

mkdir -p "$MARKET/.agents/plugins" "$CODEX_HOME"
echo 'model = "fixture-model"' > "$CONFIG"
cat > "$MARKET/.agents/plugins/marketplace.json" <<'JSON'
{"name":"local","plugins":[
  {"name":"fixture","source":{"source":"local","path":"./fixture"}},
  {"name":"unmanaged","source":{"source":"local","path":"./unmanaged"}}
]}
JSON

for name in fixture unmanaged; do
  mkdir -p "$MARKET/$name/.codex-plugin" "$MARKET/$name/hooks"
  jq -n --arg name "$name" '{name:$name,version:"1.0.0"}' > "$MARKET/$name/.codex-plugin/plugin.json"
  cat > "$MARKET/$name/hooks/hooks.json" <<'JSON'
{"hooks":{"SessionStart":[{"hooks":[{"type":"command","command":"sh \"${PLUGIN_ROOT}/hooks/start.sh\""}]}]}}
JSON
  echo 'exit 0' > "$MARKET/$name/hooks/start.sh"
done

codex plugin marketplace add "$MARKET" --json >/dev/null
installed="$(codex plugin add fixture@local --json | jq -er '.installedPath')"
codex plugin add unmanaged@local --json >/dev/null
cat >> "$CONFIG" <<TOML

[hooks.state."$KEY"]
enabled = false
TOML

approve() {
  uv run --script "$SCRIPT" fixture@local
}

approve | grep -qFx "trusted $KEY"
declaration="$(sed -n 's/^trusted_hash = "\(.*\)"/\1/p' "$CONFIG")"
content="$(sed -n 's/^trusted_content_hash = "\(.*\)"/\1/p' "$CONFIG")"
[[ "$declaration" == sha256:* && "$content" == sha256:* ]]

# A change to a script in the installed bundle invalidates approval even with identical hooks.json.
echo '# Same declarations, changed bundle' >> "$installed/hooks/start.sh"
approve | grep -qFx "trusted $KEY"
grep -qFx "trusted_hash = \"$declaration\"" "$CONFIG"
updated_content="$(sed -n 's/^trusted_content_hash = "\(.*\)"/\1/p' "$CONFIG")"
[[ "$updated_content" == sha256:* && "$updated_content" != "$content" ]]

approve >/dev/null
grep -qFx "trusted_content_hash = \"$updated_content\"" "$CONFIG"
grep -qFx 'enabled = false' "$CONFIG"
grep -qFx 'model = "fixture-model"' "$CONFIG"
! grep -q 'hooks.state."unmanaged@local:' "$CONFIG"
[[ "$(grep -c '^\[hooks.state\.' "$CONFIG")" == 1 ]]

echo "ok"
