#!/usr/bin/env bash
# usage: EVAL_HOST=claude run.sh <leader-model> <label> [source-plugin-dir]
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$here/runner.py" "$@"
