#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT="$ROOT_DIR/scripts/desktop-tools.sh"
REAL_NODE="$(command -v node)"
SANDBOX="$(mktemp -d)"
trap 'rm -rf "$SANDBOX"' EXIT
STUB_BIN="$SANDBOX/bin"
MANAGED_NODE="$SANDBOX/managed"
CALL_LOG="$SANDBOX/calls.log"
mkdir -p "$STUB_BIN" "$MANAGED_NODE/bin" "$SANDBOX/home"

cat > "$STUB_BIN/uname" <<'STUB'
#!/usr/bin/env bash
echo "${TEST_OS:-Darwin}"
STUB
cat > "$STUB_BIN/pgrep" <<'STUB'
#!/usr/bin/env bash
[[ "${OBSIDIAN_RUNNING:-0}" == 1 ]]
STUB
cat > "$STUB_BIN/brew" <<STUB
#!/usr/bin/env bash
echo "brew \$*" >> "$CALL_LOG"
[[ "\$*" == "\${BREW_FAIL:-}" ]] && exit 23
case "\$*" in
  "list --formula node") [[ "\${NODE_INSTALLED:-1}" == 1 ]] ;;
  "list --cask obsidian") [[ "\${OBSIDIAN_INSTALLED:-1}" == 1 ]] ;;
  "--prefix node") echo "$MANAGED_NODE" ;;
esac
STUB
# A stale Node earlier on PATH must not run after Homebrew prepares its Node.
cat > "$STUB_BIN/node" <<'STUB'
#!/usr/bin/env bash
exit 99
STUB
cat > "$MANAGED_NODE/bin/node" <<STUB
#!/usr/bin/env bash
echo "managed node" >> "$CALL_LOG"
exec "$REAL_NODE" -e 'Object.defineProperty(process.versions, "node", {value: process.argv[1]}); Object.defineProperty(process, "version", {value: "v" + process.argv[1]}); eval(process.argv[2]);' "\${TEST_NODE_VERSION:-22.20.0}" "\$2"
STUB
chmod +x "$STUB_BIN/uname" "$STUB_BIN/pgrep" "$STUB_BIN/brew" "$STUB_BIN/node" "$MANAGED_NODE/bin/node"

run() {
  HOME="$SANDBOX/home" PATH="$STUB_BIN:/usr/bin:/bin" bash "$SCRIPT"
}
expect_calls() {
  [[ "$(cat "$CALL_LOG")" == "$(printf '%s\n' "$@")" ]] || {
    echo "unexpected calls:" >&2
    cat "$CALL_LOG" >&2
    exit 1
  }
}
expect_failure() {
  if run > "$SANDBOX/output" 2>&1; then
    echo 'expected desktop setup failure' >&2
    exit 1
  fi
}

: > "$CALL_LOG"
run >/dev/null
expect_calls \
  'brew update' \
  'brew list --formula node' \
  'brew upgrade --formula --yes node' \
  'brew --prefix node' \
  'managed node' \
  'brew list --cask obsidian' \
  'brew upgrade --cask --greedy --no-quit --yes obsidian'

: > "$CALL_LOG"
NODE_INSTALLED=0 OBSIDIAN_INSTALLED=0 run >/dev/null
expect_calls \
  'brew update' \
  'brew list --formula node' \
  'brew install --formula --yes node' \
  'brew --prefix node' \
  'managed node' \
  'brew list --cask obsidian' \
  'brew install --cask --force --yes obsidian'

# Rejected prerequisites must stop before changing installed software.
for condition in platform running; do
  : > "$CALL_LOG"
  if [[ "$condition" == platform ]]; then
    TEST_OS=Linux expect_failure
  else
    OBSIDIAN_RUNNING=1 expect_failure
  fi
  [[ ! -s "$CALL_LOG" ]]
done
mv "$STUB_BIN/brew" "$SANDBOX/brew"
: > "$CALL_LOG"
expect_failure
[[ ! -s "$CALL_LOG" ]]
mv "$SANDBOX/brew" "$STUB_BIN/brew"

# A pinned or otherwise stale Node must not allow Obsidian/plugin work to continue.
for version in 21.99.0 22.19.9; do
  : > "$CALL_LOG"
  TEST_NODE_VERSION="$version" expect_failure
  ! grep -q 'obsidian' "$CALL_LOG"
done
TEST_NODE_VERSION=23.0.0 run >/dev/null

# Preserve the first failing command; no downstream mutation follows it.
for command in update 'upgrade --formula --yes node' '--prefix node' 'upgrade --cask --greedy --no-quit --yes obsidian'; do
  : > "$CALL_LOG"
  BREW_FAIL="$command" expect_failure
  [[ "$(tail -1 "$CALL_LOG")" == "brew $command" ]]
done
for command in 'install --formula --yes node' 'install --cask --force --yes obsidian'; do
  : > "$CALL_LOG"
  NODE_INSTALLED=0 OBSIDIAN_INSTALLED=0 BREW_FAIL="$command" expect_failure
  [[ "$(tail -1 "$CALL_LOG")" == "brew $command" ]]
done

echo 'ok'
