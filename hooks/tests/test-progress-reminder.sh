#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT="$ROOT/skills/basic-team/scripts/progress-reminder.sh"
SANDBOX="$(mktemp -d)"
trap 'rm -rf "$SANDBOX"' EXIT
cd "$SANDBOX"
printf 'unchanged' > progress.html

for event in SessionStart PostToolUse; do
  output="$(printf '{"session_id":"private-id","tool_response":"private-report"}' | bash "$SCRIPT" "$event")"
  printf '%s' "$output" | jq -e --arg event "$event" '
    keys == ["hookSpecificOutput"] and
    (.hookSpecificOutput | keys == ["additionalContext", "hookEventName"]) and
    .hookSpecificOutput.hookEventName == $event and
    (.hookSpecificOutput.additionalContext | contains("already-active basic-team"))
  ' >/dev/null
  [[ "$output" != *private-id* && "$output" != *private-report* ]]
done
[[ -z "$(bash "$SCRIPT" Stop)" ]]
[[ -z "$(bash "$SCRIPT")" ]]
[[ "$(cat progress.html)" == unchanged ]]
[[ "$(find . -type f | wc -l | tr -d ' ')" == 1 ]]

# Execute the packaged commands with either host's root variable, including spaces.
ln -s "$ROOT" "$SANDBOX/plugin root"
for event in SessionStart PostToolUse; do
  command="$(jq -r --arg event "$event" '.hooks[$event][] | .hooks[] | select(.command | contains("progress-reminder.sh")) | .command' "$ROOT/hooks/hooks.json")"
  for host in codex claude; do
    if [[ "$host" == codex ]]; then
      output="$(env -u CLAUDE_PLUGIN_ROOT PLUGIN_ROOT="$SANDBOX/plugin root" bash -c "$command")"
    else
      output="$(env -u PLUGIN_ROOT CLAUDE_PLUGIN_ROOT="$SANDBOX/plugin root" bash -c "$command")"
    fi
    printf '%s' "$output" | jq -e --arg event "$event" '.hookSpecificOutput.hookEventName == $event' >/dev/null
  done
done
echo "ok: nonblocking progress reminders and both plugin root conventions"
