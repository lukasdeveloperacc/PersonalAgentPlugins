# Main-owned progress checkpoints

The Main session owns the meaning of each report. `scripts/progress.py` only validates and saves the page; a successful receipt does not prove that implementation, review, or user-facing briefing occurred. Use the same page for the same run across added requests, compaction, and session resume.

## Commands

Run from the executing project's root, not the plugin installation directory. Resolve the script from the installed basic-team skill directory. PAGE must be an absolute path beneath that project's `docs/inprogress`.

```sh
uv run "<basic-team-base>/scripts/progress.py" init "<project-root>/docs/inprogress/<task>-<start>-progress.html" --input "<initial-data.json>" --checkpoint kickoff
uv run "<basic-team-base>/scripts/progress.py" update "<same-page>" --input "<patch.json>" --checkpoint implementation-b1-report
uv run "<basic-team-base>/scripts/progress.py" status "<same-page>"
```

Always launch these scripts with `uv run`; never call `python3` or `python` directly. Both scripts declare inline Python metadata with no external dependencies, so `uv run` ignores the executing project's dependencies. If `uv` is not installed, report BLOCKED instead of falling back to another interpreter. To run the focused CLI tests from any directory:

```sh
uv run "<basic-team-base>/scripts/tests/test_progress.py" -v
```

`init` creates a page from the common template and refuses an existing file. `update` preserves its renderer and saves atomically. `status` reads without writing. Successful commands print a JSON receipt containing `path`, `saved_at`, `checkpoint`, and `revision`. Retain that receipt for the next briefing. `revision` counts page saves; it is not the implementation revision or review target.

Pass only changed fields in the input JSON. Agent patches merge by stable `id`, preserving omitted fields and other agents. A new agent needs its name, role, area, and status; supply the remaining report/model/graph fields when known. Older agents without IDs remain untouched and cannot receive individual patches without an explicit data migration. New dependency IDs must refer to agents already present or created in the same input; untouched legacy unresolved relationships remain readable. Do not invent relationships to satisfy validation.

```json
{
  "agents": [{
    "id": "backend-b1",
    "status": "완료",
    "tone": "good",
    "reported": "2026-10-10T20:30:00+09:00",
    "result": "목록 API 테스트 통과",
    "next": "고정된 변경에 대한 독립 리뷰"
  }],
  "stage": "독립 리뷰 준비"
}
```

Other arrays (`plan`, `reviews`, `decisions`, `flow`) replace their entire array when supplied; include the intended full snapshot. `agents: []` makes no agent changes. Omitted fields remain unchanged. Do not pass script-owned `path`, `updated`, or `_progress`. The script embeds checkpoint/save metadata under `_progress`, escapes report text, and rejects malformed or unknown fields without replacing the existing page. Keep input files temporary and free of secrets or private reasoning.

## Save before continuing

Collect already-received facts into one patch, save, inspect the successful receipt, then dispatch dependent work or brief the user. Do not wait for unrelated agents to finish. Save these events:

- Kickoff and assignment: record queued/not-launched assignments before launching, then record the actual launch outcome. Do not call a queued agent active.
- Planning: save approved plan revision, allocation/contracts, and relevant plan-review transitions before implementation starts.
- Implementation: save consumed agent reports, milestone completion, changed scope, and pending integration before dependent dispatch.
- Review: save review start/collection state; keep independent verdicts and findings out of all page data until all required reviews arrive. Then save their combined results against the actual fixed review target.
- Fixes: mark affected verdicts superseded before another review round. Save blockers, browser cleanup results, and other changes needed for the next decision.
- Completion or cancellation: save the final observed state. Completion requires no pending progress updates as well as the skill's implementation, review, and cleanup gates.

Mark a report handled only after its required save succeeds. Deduplicate already-handled reports. On save failure, keep the patch pending, disclose the error and last confirmed save, and repair/retry. Do not announce completion or cross a dependent stage whose checkpoint failed. Unaffected independent work can continue. There is no timer, extra progress agent, or periodic polling.

Every briefing includes `진행판: [<작업명>](<절대 경로>) — <절대 경로> · 마지막 저장: <확인된 시각>`. Use the receipt's actual timestamp. When no facts changed, reuse the last confirmed receipt without another write.

## Resume

Before compaction or handoff, preserve the exact page path, last confirmed checkpoint/revision/save time, unsaved patches, outstanding agent/task IDs, and actual implementation/review target. Put this in the existing handoff or context summary; do not write hook-owned OMX runtime state.

On resume, run `status` on that exact page and reconcile it with real host messages and current repository evidence. Restore pending updates before dependent dispatch or briefing. The saved stage and IDs are diagnostic information, never execution authority. Do not find a run by selecting the newest file or create a replacement page automatically. For an older page without checkpoint metadata, inspect its saved JSON and use the first verified `update` to adopt it; do not fabricate a previous receipt.

## Scoped nonblocking host reminders

The plugin's shared `hooks/hooks.json` invokes `hooks/basic-team-progress.sh`, backed by this skill's `scripts/basic-team-progress.py`. The handlers are silent by default, including outside basic-team. The progress-page command lives beside it in `scripts/`; reminder state never edits the HTML.

Only the coordinating Main actually executing basic-team requests `arm` after initializing or verifying the exact progress page. Use the host-specific commands in SKILL.md; Claude substitutes `${CLAUDE_SESSION_ID}` in that skill body. A helper receipt is an activation request, not proof of activation. Retain its `basic_team_hook.run_id`. The corresponding successful shell-tool `PostToolUse` must verify the one-time request against actual host identity and confirm registration before reminders are available. Missing identity, unsupported payloads, errors, and absent hooks leave reminders off; apply the existing save/receipt rule and continue without treating that as a workflow blocker.

At completion, explicit cancellation, failure exit, or a switch to unrelated work, request disarm for that exact `run_id`:

```sh
uv run "<basic-team-base>/scripts/basic-team-progress.py" disarm --host codex --run-id "<retained-run-id>"
uv run "<basic-team-base>/scripts/basic-team-progress.py" disarm --host claude --session-id "<Claude Main session ID>" --run-id "<retained-run-id>"
```

The Claude session ID comes from the substituted skill-body command, not a guessed process environment. Never reuse a child ID or select another session's registration. Late requests from an older run cannot disable its replacement.

The event roles are:

- `PostToolUse` on supported shell tools consumes valid arm/disarm requests. Registered Main agent-tool returns receive a short save/briefing reminder. Agent launch and wait timeout are not completion; no new facts means no page rewrite.
- `UserPromptSubmit` silently resets the current session's existing guard. Rearm at the first step of every continuing basic-team work interval. Claude can emit this event for automatic continuations, including background reports; rearm then too. A missed rearm suppresses reminders.
- `SessionStart` on startup/resume/clear/compact resets an existing guard. Recover the same page and explicitly rearm when basic-team actually continues. This conservative reset avoids carrying an old registration into another task.
- `SessionEnd` removes only this session's own registration as supplementary cleanup. Main's explicit disarm and new-input reset remain necessary because termination callbacks are not guaranteed after a crash.

Records and one-time requests live under `${XDG_STATE_HOME:-~/.local/state}/lukas-plugin/basic-team`, separate from OMX/OMC runtime state. They hold routing identifiers, generation, run ID, and page path, not transcripts or report text. Generation changes reject delayed requests after a reset. No transcript or prompt-content scans, periodic reads, permission decisions, tool denials, or Stop/SubagentStop continuations are added. Generic event callbacks may still execute outside basic-team, but return no model context.

Codex activation conservatively requires the observed local shell's `CODEX_THREAD_ID` and `CODEX_SESSION_ID` to match. The verified request is then bound to the actual hook session and turn. These environment variables are a local runtime adapter, not a documented guarantee for all Codex hosts; absent or differing values disable activation. Claude uses the explicit substituted session ID and rejects child events carrying `agent_id`. Missing scope fields suppress output. These checks route advisory context and never establish permission or lifecycle authority.

Wait names and shell-output layouts vary between hosts; unsupported events and async notifications can bypass reminders. Hook execution also depends on host version, plugin loading, and trust settings. Tests of these adapters do not establish live event coverage in every App/CLI host. See [Codex hooks](https://learn.chatgpt.com/docs/hooks), [Claude hooks](https://code.claude.com/docs/en/hooks), and [Claude skill substitutions](https://code.claude.com/docs/en/skills#available-string-substitutions).
