# Claude native host

Read at preflight and reuse for dispatch, recovery, and exit. Resolve and invoke the installed `oh-my-claudecode:team` in the current main session; if it is a compact shim, load its referenced body. Let it check native runtime prerequisites and own teammate creation, tasks, messaging, waiting, and shutdown. Do not duplicate its protocol or invoke its CLI/tmux route/another leader. A tool name absent from older team docs is not itself a blocker.

## Launch and settings

Give team the task, basic-team's approved planning, ownership, model/effort, independent reviews, progress/handoff and completion contracts. Team supplies the native mechanism, not exceptions to those requirements. Complete its native task-list phase before implementation. Never create standalone agent definitions or request restart before its preflight merely to satisfy this skill.

Inspect the actual Agent schema. The supported per-call selection is `model` aliases (`sonnet|opus|haiku|fable`) and `effort` (`low|medium|high|xhigh|max`); exact support is checked on the running host. `spawn-args` emits Planner/Architect/Critic `model:opus, effort:medium`, Executor `model:haiku, effort:max`, Documentation Executor `model:sonnet, effort:medium`, and Reviewer `model:sonnet, effort:high` (no review helpers). Pass both as actual arguments on EVERY creating call/respawn, not prompt-only. OMC's spawn payload does not select them for you. Agent frontmatter can pin another tier, so omission may silently select the wrong model. Never use `subagent_type:fork` (ignores both settings) or pass a full ID where an alias is required.

Alias/role name is not evidence of exact table ID, effort, or application of user `modelSettings`. Requested, actual accepted arguments and host-observed values stay separate. Optional child's own system-context ID is only a self-report, not host proof. Under v2 accepted correct arguments permit work with `미확인`; under strict policy missing observations pause that child. Known actual mismatch always blocks; do not pass it through an unknown-setting exception.

`.claude/omc.jsonc` `team.roleRouting` is for tmux CLI workers, not native teammates; do not edit it. Check forced overrides/organization limits without bypassing settings. Native teams may require `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` at session start. Plugin install/reload can enable it in user settings, but this workflow does not authorize that settings change; a genuinely unavailable native team requires supported restart/recovery and remains BLOCKED meanwhile. Do not replace it with ordinary subagents.

Normal example: Planner creation uses native team's supported Agent call with `model:"opus", effort:"medium"` and generated Planner prompt. Save the accepted call/child ID source and actual argument object; exact model/effort remain `미확인` unless the host exposes them. V2 permits planning immediately; send its draft to Architect then Critic with Architect evidence. The child's self-report cannot upgrade this to host-observed evidence.

BLOCKED example: an organization limit rejects `effort:"max"` on an Executor call. Record the error and investigate supported matching invocation. Do not omit effort, reduce it, use fork, or create settings/agent files. Report the task BLOCKED with required versus accepted settings and recovery. A strict run with alias accepted but no exact ID evidence likewise pauses pending actual observation or its specific user exception.

## Coordination and exit

Delegate messaging, idle/resume, supported event waits and native task lifecycle to the invoked team. No second mailbox polling loop. Reuse assigned idle teammates for fixes with changed findings/revision; recover existing assignments on resume and consume duplicate outcomes once after the progress receipt succeeds.

Basic-team's required-pass continuation overrides team's default max_fix_loops preference for a new run, but never reset/bypass a mandatory runtime cap. A cap preventing work means BLOCKED with remaining findings.

On success/cancellation/failure, request shutdown once, wait team's documented timeout (otherwise one bounded 60-second event wait), and verify each worker's exit. Timeout records unresponsive identity, request/time and last evidence; diagnose once and use team's supported scoped recovery. Do not fabricate acknowledgement or delete live-worker state. After confirmed worker shutdown finish native cleanup and verify THIS run terminal/inactive through supported team evidence (`active=false` or confirmed supported removal where applicable). No manual flag edits or broad .omc/.omx deletion. Unverified/active state means cleanup BLOCKED and stops subsequent git mutations, including push.

## Source-bound progress records

Follow [evidence-progress.md](evidence-progress.md). Before dispatch save the assignment/task identity; bind it once to the actual host-returned identity on acceptance. Capture accepted call, child report, send receipt and recipient acknowledgement as different source records. If the host exposes no stable source reference or event time, record null/unknown with clearly labeled captured content; never invent telemetry or treat save time as event time. A captured file hash proves byte consistency, not host authenticity.

Reusing an idle agent for fixes requires a new assignment for the new obligations/revision; replacing an agent requires a new assignment and accepted identity. Previous results cannot complete the replacement task. Result received is neither PASS nor host termination. Before all independent reports arrive, save only redacted receipts and immediate tool blockers; keep report paths, bodies and outcomes in the leader’s private collection. Never infer delivery acknowledgement from a successful send.

## Progress hook

Only executing Main, after the exact page exists; Claude substitutes its skill-body session variable:

```sh
uv run "<bt>/scripts/basic-team-progress.py" arm "<absolute-progress-page>" --host claude --session-id "${CLAUDE_SESSION_ID}"
uv run "<bt>/scripts/basic-team-progress.py" disarm --host claude --session-id "<same substituted Main session ID>" --run-id "<retained-run-id>"
```

Never guess identity from a child/process environment. A request receipt is not matching PostToolUse confirmation. Missing support uses manual checkpoints. Armed Agent hooks can deny missing model/effort or fork; repair actual call arguments using spawn-args. Do not arm when merely editing the skill.

Official references: [Agent teams](https://code.claude.com/docs/en/agent-teams), [Subagent model and effort](https://code.claude.com/docs/en/sub-agents). Check actual host schema and installed team lifecycle before claiming these capabilities.
