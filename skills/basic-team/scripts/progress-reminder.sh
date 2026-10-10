#!/usr/bin/env bash
# Stateless guidance only: no transcript reads, state writes, or blocking decisions.
case "${1:-}" in
  SessionStart)
    reminder='Only if you are the coordinating main session of an already-active basic-team run: recover its exact existing progress page and pending reports from the handoff, check the saved receipt with progress.py status, and reconcile actual evidence before continuing. Do not create a replacement page or start a workflow because of this reminder. Otherwise ignore.'
    ;;
  PostToolUse)
    reminder='Only if you are the coordinating main session of an already-active basic-team run: save newly received progress facts with progress.py and confirm its receipt before dependent dispatch or briefing. Reuse the same page and include its link, absolute path, and confirmed save time. Agent launch or wait timeout is not completion; no new facts means no rewrite. Otherwise ignore.'
    ;;
  *) exit 0 ;;
esac
printf '{"hookSpecificOutput":{"hookEventName":"%s","additionalContext":"%s"}}\n' "$1" "$reminder"
