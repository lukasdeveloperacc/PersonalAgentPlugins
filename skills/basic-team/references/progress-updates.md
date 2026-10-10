# Main-owned progress checkpoints

The Main session owns the meaning of each report. `scripts/progress.py` only validates and saves the page; a successful receipt does not prove that implementation, review, or user-facing briefing occurred. Use the same page for the same run across added requests, compaction, and session resume.

## Commands

Run from the executing project's root, not the plugin installation directory. Resolve the script from the installed basic-team skill directory. PAGE must be an absolute path beneath that project's `docs/inprogress`.

```sh
uv run "<basic-team-base>/scripts/progress.py" init "<project-root>/docs/inprogress/<task>-<start>-progress.html" --input "<initial-data.json>" --checkpoint kickoff
uv run "<basic-team-base>/scripts/progress.py" update "<same-page>" --input "<patch.json>" --checkpoint implementation-b1-report
uv run "<basic-team-base>/scripts/progress.py" status "<same-page>"
```

Both scripts declare inline Python metadata with no external dependencies, so `uv run` ignores the executing project's dependencies. Plain `python3` (3.10+) also works. To run the focused CLI tests from any directory:

```sh
uv run "<basic-team-base>/scripts/test_progress.py" -v
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

## Nonblocking host reminders

The plugin's shared `hooks/hooks.json` adds only `additionalContext` reminders through `scripts/progress-reminder.sh`, for Codex and Claude:

- `SessionStart`, matching `resume|compact`: remind the coordinating Main of an already-active basic-team run to recover its exact page and pending reports.
- `PostToolUse`, matching `Agent|spawn_agent|wait_agent|wait`: remind Main to save newly received facts before dependent dispatch or briefing. A spawn result or wait timeout is not completion. No new facts means no save.

These reminders do not identify an active run mechanically. Ignore them outside an already-active basic-team coordinator; they do not start a workflow. They read no transcripts, store no session state, modify no files, and return no permission, blocking, or continuation decision. No new `PreToolUse`, `Stop`, or `SubagentStop` gate is installed. In particular, `SubagentStop` feedback can continue a child rather than instruct Main.

Codex documents the `Agent` alias for `spawn_agent`; wait names are compatibility matches, not a guaranteed completion signal. Unsupported events, async notifications, and silent periods can bypass these reminders, so Main's save/receipt rule still applies. Hook execution depends on host version, plugin loading, and host trust settings; do not claim live coverage merely because the scripts pass tests. See [Codex hooks](https://learn.chatgpt.com/docs/hooks) and [Claude hooks](https://code.claude.com/docs/en/hooks).
