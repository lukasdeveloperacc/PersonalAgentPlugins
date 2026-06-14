#!/usr/bin/env bash
# Verify docs/cmux-transport-contract.md mirrors the plugin-local contract byte-for-byte,
# ignoring the leading MIRROR banner (first 2 lines of the docs copy).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$HERE/../../../.." && pwd)"

SRC="$REPO_ROOT/claude/plugins/cmux-agent-harness-loop-plugin/contracts/cmux-transport-contract.md"
MIRROR="$REPO_ROOT/docs/cmux-transport-contract.md"

if [[ ! -f "$SRC" || ! -f "$MIRROR" ]]; then
  echo "DOCS MIRROR: missing file(s)"; exit 1
fi

# Strip the 2-line banner (comment + blank) from the mirror, compare the body to the source.
if diff <(tail -n +3 "$MIRROR") "$SRC" >/dev/null; then
  echo "OK: docs/cmux-transport-contract.md body matches the plugin-local contract"
  exit 0
else
  echo "DOCS MIRROR DRIFT: docs/cmux-transport-contract.md body differs from the plugin-local contract"
  echo "  (the plugin-local contract is canonical; resync the docs/ mirror)"
  exit 1
fi
