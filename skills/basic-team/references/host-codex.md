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

Before launch inspect the exposed native lifecycle operations. If scoped termination plus verification is supported, use it once at exit. If it is absent but native turn interruption and status verification are available, use **task quiescence** below; absence of agent-disposal APIs alone is not a preflight blocker. Do not substitute tmux/CLI workers, broad process kills, Claude TeamDelete, or invented state files. An explicit user requirement to dispose of agents still requires real termination support.

For task quiescence:

1. Track every accepted child identity, including planning and earlier/replaced agents, in assignments/dispatch records. Reconcile every assigned result and every command/process it launched; a final message alone does not establish that detached commands stopped. Children must report outstanding process/session handles, or explicitly that none remain. Wait for owned commands to finish, or use their supported scoped cancellation and verify completion; do not start detached writes without a tracked handle. Prefer having the owner reconcile commands before interrupting its turn. If a process handle is accessible only in the child’s tool scope, resume that owner with a cleanup-only instruction, obtain the actual command exit result, then verify its turn is inactive again. An unknown handle in Main’s scope is not proof of process exit.
2. Naturally completed/idle turns need no interruption. For a running turn that must stop (exit, cancellation or replacement), call scoped `interrupt_agent` once. Its returned previous status is not a stopped-state acknowledgement: inspect `list_agents` once after the call, or use another supported lifecycle result. Accept only observed completed/idle/interrupted state; running, absent or unknown remains unresolved. If interruption is not yet reflected, use one bounded event wait and one final verification, then report the specific unresolved work. Do not poll repeatedly.
3. Interruption stops the current turn, not the reusable agent object, and does not prove a running shell/process stopped or an unfinished task succeeded. Resume unfinished work with `followup_task` or reassign only after overlapping old work is confirmed inactive. Preserve original results and use a new assignment. Slot exhaustion is a capacity constraint: reuse an available compatible agent; do not assume interruption frees a slot.
4. After all required tasks/reviews/checks finish and all pending writes, messages, and background commands are reconciled, capture a fresh host status snapshot for exactly this run’s accepted identities. Save the capability record and `gates.lifecycle` task-quiescence evidence described in [progress updates](progress-updates.md). Later dispatch/progress/resume invalidates that snapshot; capture again after work stops.
5. Report **“작업 완료·실행 중인 작업 없음; 에이전트 객체 종료는 미확인”**. Keep shutdown compliance `부분`, never fabricate `terminated` observations or a shutdown `함`. Other cleanup, result, review, validation and completion gates still apply. An agent waiting for unfinished work is not a completed task.

For supported termination, request shutdown once for this run’s agents and use the documented timeout or one bounded 60-second event wait before verification. On timeout record the identity, request/time and last evidence, diagnose once and apply supported scoped recovery. A failed supported shutdown or unverified live work remains BLOCKED; do not switch to task-quiescence merely to hide that failure. Never stop unrelated agents.

## Source-bound progress records

Follow [evidence-progress.md](evidence-progress.md). Before dispatch save the assignment/task identity; bind it once to the actual host-returned identity on acceptance. Capture accepted call, child report, send receipt and recipient acknowledgement as different source records. If the host exposes no stable source reference or event time, record null/unknown with clearly labeled captured content; never invent telemetry or treat save time as event time. A captured file hash proves byte consistency, not host authenticity.

Reusing an idle agent for fixes requires a new assignment for the new obligations/revision; replacing an agent requires a new assignment and accepted identity. Previous results cannot complete the replacement task. Result received is neither PASS nor host termination. Before all independent reports arrive, save only redacted receipts and immediate tool blockers; keep report paths, bodies and outcomes in the leader’s private collection. Never infer delivery acknowledgement from a successful send.

## Progress hook

Only executing Main, after the exact page exists:

```sh
uv run "<bt>/scripts/basic-team-progress.py" arm "<absolute-progress-page>" --host codex
uv run "<bt>/scripts/basic-team-progress.py" disarm --host codex --run-id "<retained-run-id>"
```

The adapter uses current runtime identity; missing/mismatched identity leaves reminders unavailable. A command receipt is only a request. Actual matching PostToolUse confirmation is required for registration/removal claims. Use manual saves if unavailable; never arm while merely editing this skill.

Official reference: [Codex subagents and custom roles](https://developers.openai.com/codex/subagents). Actual visible tool support takes precedence over examples.
