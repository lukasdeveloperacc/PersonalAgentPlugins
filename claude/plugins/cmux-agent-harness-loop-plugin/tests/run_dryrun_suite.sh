#!/usr/bin/env bash
# Dry-run CI gate for cmux-agent-harness-loop. Runnable with no live cmux pane.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "== template mirror diff gate (fail-closed) =="
python3 "$HERE/sync_templates.py" check

echo
echo "== docs mirror diff gate (fail-closed) =="
bash "$HERE/check_docs_mirror.sh"

echo
echo "== dry-run transport-shim suite =="
python3 "$HERE/test_harness.py"

echo
echo "ALL DRY-RUN GATES PASSED"
