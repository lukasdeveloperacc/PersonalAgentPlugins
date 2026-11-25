#!/usr/bin/env bash
set -eu
plugin=$(cd "$(dirname "$0")/../.." && pwd)
helper="$plugin/skills/thegame-work-task/scripts/task_state.py"
command=$(python3 -c 'import json,sys; print(next(h["command"] for group in json.load(open(sys.argv[1]))["hooks"]["SessionStart"] for h in group["hooks"] if "task_state.py" in h["command"]))' "$plugin/hooks/hooks.json")
intake=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"])' "$plugin/hooks/hooks.json")
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
cd "$tmp"
task() { python3 "$helper" "$@"; }
hook() {
  python3 -c 'import json,sys;print(json.dumps({"cwd":sys.argv[1]}))' "$1" | bash -c "$command"
}
export PLUGIN_ROOT="$plugin"
unset CLAUDE_PLUGIN_ROOT
[[ -z "$(hook "$tmp")" ]]
git init -q repo
cd repo
git -c user.email=test@example.test -c user.name=test commit --allow-empty -qm initial
git worktree add -q --detach ../other
url=https://www.notion.so/11223344556677889900aabbccddeeff
other=https://www.notion.so/11223344556677889900aabbccddeeee
[[ -z "$(task show)" ]]
task remember 'https://app.notion.com/p/My-Task-11223344556677889900aabbccddeeff?source=copy_link'
task remember "$url"
[[ "$(task show)" = "$url" ]]
if task remember "$other" || task clear "$other"; then exit 1; fi
mkdir child
cd child
[[ "$(task show)" = "$url" ]]
for host in codex claude; do
  if [[ "$host" = claude ]]; then unset PLUGIN_ROOT; export CLAUDE_PLUGIN_ROOT="$plugin"; fi
  bash -c "$intake" | python3 -c 'import json,sys; h=json.load(sys.stdin)["hookSpecificOutput"]; assert h["hookEventName"] == "UserPromptSubmit" and "thegame-work-task" in h["additionalContext"]'
  hook "$PWD" | python3 -c 'import json,sys; h=json.load(sys.stdin)["hookSpecificOutput"]; assert h["hookEventName"]=="SessionStart" and sys.argv[1] in h["additionalContext"] and "thegame-work-task" in h["additionalContext"]' "$url"
done
[[ -z "$(hook "$tmp/other")" ]]
[[ -z "$(git status --porcelain)" ]]
task clear "$url"
task clear "$url"
[[ -z "$(hook "$PWD")" ]]
if task remember 'https://example.org/11223344556677889900aabbccddeeff'; then exit 1; fi
echo "thegame-work-task tests passed"
