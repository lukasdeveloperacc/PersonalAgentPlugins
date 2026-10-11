#!/usr/bin/env bash
# usage: run.sh <leader-model> <label> [plugin-dir]   e.g. run.sh haiku new /path/to/repo
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
leader="$1"; label="$2"; plugin="${3:-}"
out="${EVAL_OUT:-$here/results}/$label-$leader-$(date +%H%M%S)"
mkdir -p "$out/work"
idx="${EVAL_INDEX:-0}"
fix="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["evals"][int(sys.argv[2])]["fixture"])' "$here/evals.json" "$idx")"
cp "$here/$fix"* "$out/work/"
git -C "$out/work" init -q && git -C "$out/work" add -A && git -C "$out/work" -c user.email=e@e -c user.name=e commit -qm fixture
prompt="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["evals"][int(sys.argv[2])]["prompt"])' "$here/evals.json" "$idx")"
args=(-p "$prompt" --model "$leader" --output-format stream-json --verbose --permission-mode bypassPermissions --max-budget-usd "${BUDGET:-8}")
[[ -n "$plugin" ]] && args+=(--plugin-dir "$plugin")
( cd "$out/work" && CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 perl -e 'alarm shift; exec @ARGV' "${TIMEOUT:-1800}" claude "${args[@]}" > "$out/stream.jsonl" 2> "$out/stderr.txt" ) || echo "exit $?" >> "$out/stderr.txt"
EVAL_INDEX="$idx" python3 "$here/analyze.py" "$out" | tee "$out/summary.json"
