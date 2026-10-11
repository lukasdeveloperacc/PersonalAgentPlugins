# Codex native host

Read at preflight and reuse for dispatch, recovery, and exit. Inspect the visible tools before claiming capability.

## Launch and settings

Use native `spawn_agent` with explicit `model` and `reasoning_effort` from `spawn-args`, unique `task_name`, and `fork_turns: "none"` when supported. Use `agent_type: "default"` if installed role profiles override the requested settings. If per-call overrides are unavailable, an existing custom role is usable only after its model/effort are verified to match. Do not substitute inherited settings, a CLI process, global config changes, or a tmux team.

Architect/Critic use `--role architect|critic`; their arguments map to Planner settings while their briefs remain distinct. The four product-review roles use Reviewer settings; no review helpers are dispatched. Queue within host capacity; never lower effort or omit roles.

Record requested ID/effort, actual argument object, accepted call/returned agent identity and source, and actual host-observed model/effort separately. Hidden observations remain `미확인`; an accepted explicit invocation permits work under v2 but does not confirm exact running settings. Strict policy pauses unknown settings. Any known mismatch blocks regardless of policy/unknown-setting exception.

Normal example: `spawn-args --host codex --role executor` produces model `gpt-6-luna`, reasoning `max`. A planned documentation task uses `--role documentation_executor`, which produces `gpt-6.1-sol`, reasoning `medium`. Main passes the generated fields to a native default-role spawn with the matching generated brief. The accepted response identifies the child. Save the actual `invocationArguments`, `invocationAccepted:true`, source evidence, and `observed:"미확인"` / `observedEffort:"미확인"` when host observations are absent. Under v2 the child confirms owned files and implements the authorized task; do not fabricate an observation or demand a redundant identity handshake.

BLOCKED example: required reasoning override is rejected by the visible spawn tool. Save the failed invocation/error; no accepted launch is recorded. Check an existing matching role or supported corrected call once. Without a supported matching invocation, block the task; do not edit custom-role configuration to bypass it. Under strict policy an accepted call with unknown effort is also blocked pending actual evidence or the specific user's exception.

## Replies, resume, and shutdown

Provide returned agent paths/task names as contact addresses. `send_message` reaches a running agent; `followup_task` starts/resumes an idle one. Send each report once. Collect pushed results through `wait_agent` when idle; do not loop over `list_agents`. On duplicate completion notification, reuse the handled result/checkpoint and do not repeat dispatch. On resume, recover existing assigned IDs before any replacement spawn; saved IDs require reconciliation with host evidence.

Before launch, identify the host's supported scoped termination and verification surface. On exit request shutdown once for this run's agents, use the documented timeout or one bounded 60-second event wait, and verify stopped/terminal status through supported lifecycle evidence. An idle/completed task is not proof of terminated agent. If shutdown times out, record agent ID, request/time and last evidence, diagnose that agent once, then apply only a supported scoped stop. Missing termination proof is cleanup BLOCKED. Do not require Claude's TeamDelete/inactive team-state file on Codex; do not invent one. No broad process kill or unrelated agent stop.

## Progress hook

Only executing Main, after the exact page exists:

```sh
uv run "<bt>/scripts/basic-team-progress.py" arm "<absolute-progress-page>" --host codex
uv run "<bt>/scripts/basic-team-progress.py" disarm --host codex --run-id "<retained-run-id>"
```

The adapter uses current runtime identity; missing/mismatched identity leaves reminders unavailable. A command receipt is only a request. Actual matching PostToolUse confirmation is required for registration/removal claims. Use manual saves if unavailable; never arm while merely editing this skill.

Official reference: [Codex subagents and custom roles](https://developers.openai.com/codex/subagents). Actual visible tool support takes precedence over examples.
