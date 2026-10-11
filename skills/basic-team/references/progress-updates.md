# Main-owned progress checkpoints

The Main session owns the meaning of each report. `scripts/progress.py` only validates and saves the page; a successful receipt does not prove that implementation, review, or user-facing briefing occurred. Use the same page for the same run across added requests, compaction, and session resume.

Before each save, apply the skill's ELI5-style plain-Korean rule to every changed user-facing field unless the user requested another language. Explain the result, what was verified or remains unresolved, and the next action; do not paste English reviewer reports into `reviewNotice`, `reviews`, `decisions`, or agent reports. Preserve verdict meaning, evidence, technical identifiers, and reported times. The script stores supplied text and does not translate or summarize it.

## Commands

Run from the executing project's root, not the plugin installation directory. Resolve the script from the installed basic-team skill directory. PAGE must be an absolute path beneath that project's `docs/inprogress`.

```sh
uv run "<basic-team-base>/scripts/progress.py" init "<project-root>/docs/inprogress/<task>-<start>-progress.html" --input - --checkpoint kickoff <<'JSON'
{"goal":"목록 API 개선","summary":"계획을 준비합니다","stage":"계획"}
JSON
uv run "<basic-team-base>/scripts/progress.py" update "<same-page>" --input - --checkpoint implementation-b1-report <<'JSON'
{"summary":"목록 API 구현을 확인했습니다","stage":"검증 준비"}
JSON
uv run "<basic-team-base>/scripts/progress.py" status "<same-page>"
```

Gate and helper commands (the runbook in SKILL.md says when to use each):

```sh
uv run "<bt>/scripts/progress.py" gate "<page>" --stage implementation|review|ready|complete   # exit 1 + problems list until satisfied
uv run "<bt>/scripts/progress.py" handoffs "<page>" --id "<handoff-id>"                # omit --id to read all records
uv run "<bt>/scripts/progress.py" compliance "<page>"                                    # final table; rows without evidence print 안 함
uv run "<bt>/scripts/progress.py" spawn-args --host claude|codex --role planner|architect|critic|executor|documentation_executor|reviewer
uv run "<bt>/scripts/progress.py" brief --role planner|architect|critic|executor|documentation_executor|reviewer --input "<fields.json>"
```

## Evidence fields and observation policy

New `init` defaults `gates.observationPolicy` to `invocation-evidence-v2`; use `init ... --observation-policy strict-observation-v1` when the user requires actual-setting proof. New pages also store script-owned `_progress.schemaVersion:3`; schema3 retains schema2’s accepted invocation and plan/conditional/validation/terminal checks under BOTH policies, and checks embedded stage handoffs. Legacy schema1/2 pages retain their existing checks, remain readable, and are not silently upgraded by update (missing policy means strict v1). Preserve the policy at resume; `update` cannot change/relax it. Policy is a check criterion, not host authority.

Save these `gates` fields with `update`:

- `planApproved`: approved plan revision; this label alone is not plan-review evidence.
- `planReview`: `{method:"ralplan", revision:<planApproved>, artifact:<plan path>, sha256:<actual plan file hash>, reviews:[{role:"architect",revision,artifact,sha256,verdict:"APPROVE"},{role:"critic",revision,artifact,sha256,verdict:"APPROVE"}]}`. These entries record actual ordered reviews on the same plan; Critic receives Architect evidence. With permitted `plan` fallback use `method:"plan"`, `reviews:[]`, and `fallbackEvidence` explaining verified absence of ralplan. File/hash checks do not prove approval quality or correct review execution.
- `conditionalReviews`: `{impeccable:{required:<boolean>,reason:<scope evidence>}, e2e:{required:<boolean>,reason:<scope evidence>}}`; both explicit decisions must agree with `requiredReviewers`. The Planner/leader judge actual UX/connected-flow facts; the helper does not infer them from filenames.
- `requiredReviewers`: reviewer IDs `karpathy`, `ponytail`, plus activated `impeccable`, `e2e`; `reviewTarget`: frozen PRODUCT revision/content digest, not the page save revision.
- `verdicts`: `{name:{revision,verdict}}`, saved only as the complete required set. `{}` clears superseded results for a new round. Any later product edit needs fresh verdicts from all required reviewers; use the scoped re-review in [workflow-contracts.md](workflow-contracts.md), never relabel an old PASS.
- `models`: `{agent-id:{role,requested,invocation,observed,observedEffort,observationEvidence,invocationArguments,invocationAccepted,invocationEvidence}}`. `requested` is the exact spawn-args ID; Architect/Critic have their own `role:"architect"|"critic"` records but use Planner tier; ralplan requires both role records. `invocation` is a human-readable call description, while `invocationArguments` is the ACTUAL call object (Codex `model`/`reasoning_effort`, Claude `model`/`effort`), `invocationAccepted:true` requires a successful host call, and `invocationEvidence` identifies that source/child ID. Accepted correct invocation permits v2 work when actual observations remain `미확인`. Host-observed values go in `observed`/`observedEffort` with `observationEvidence` (source/identity/time/output/path). Never copy arguments or child's self-report into these fields. Self-report stays in `agents[].observation`. Strict policy requires actual observations or a specific permitted missing-observation exception. Known mismatch, missing arguments or rejected call blocks under either policy.
- `exceptions`: `{agent-id:<specific user's approval for missing observation>}` for strict cases only. Clear stale exceptions on replacement with `null`; never use one for known mismatches.
- `validation`: `{revision:<reviewTarget>,status:"PASS"|"CHANGES_REQUIRED"|"BLOCKED",evidence,checks:[{command,revision,exitCode:0,evidence}]}`. Commands/checks identify final product revision and actual results. Only genuinely inapplicable validation uses `checks:[]` and `notApplicable:<reason>`; a missing/forbidden required test is a gap, not inapplicability or PASS.
- `evidence`: `{hook|eli5|planning|tasks|validation|shutdown|cleanup:{status,evidence}}`. Schema2/3 complete requires `tasks` with `status:"함"` and nonempty evidence identifying the reconciled task record and applicable saved stage/completion handoffs; `부분`, missing/null records or unsaved handoffs cannot clear it. It also requires shutdown `status:"함"` with real host lifecycle evidence; cleanup is `함`, or `안 함` with a concrete `해당 없음` reason. Hook absence uses the documented manual fallback and remains partial confirmation, never fabricated success.

`handoffs` is a top-level append-only array, not a gate field. Each record uses the shape in [../assets/stage-handoff-template.md](../assets/stage-handoff-template.md). IDs are unique across the run; an identical same-ID retry is a no-op for the record, while changed content needs a new ID. Read records with `handoffs PAGE [--id ID]`, which also returns confirmed page receipt metadata without writing. Save the handoff with the associated stage facts in one `update` patch and verify its receipt before release. Schema3 implementation requires a ready `planning-to-implementation` record for `planApproved`; review requires a ready `implementation-to-verification` or `fixes-to-verification` record for `reviewTarget`; ready requires that review-entry record, and complete also requires a ready `completion` record for `reviewTarget` with `pending:[]`. Gate checks use record append order: implementation requires the latest overall record to be `planning-to-implementation`; review/ready require the latest non-completion record to be `implementation-to-verification` or `fixes-to-verification`; complete additionally requires the latest overall record to be `completion`. Later recovery or replanning supersedes earlier review-entry evidence, even for the same revision: save a fresh review-entry record and a fresh completion after recovery. These checks do not prove host work occurred.

`models`, `evidence`, and `exceptions` merge per key; `null` removes a record, and other gate fields replace. Page/model/review compliance rows are derived, not supplied. All fields are leader-reported evidence; verify source artifacts and host facts before dependent dispatch.

`implementation` checks plan/settings; `review` checks review target/conditional decisions/settings; `ready` checks all final-revision required PASS and validation BEFORE shutdown. Then perform cleanup, save the completion handoff and reconciled final task record, record `gates.evidence.tasks`, lifecycle evidence and the final receipt, and run `complete`. `ready` deliberately does not require the final task/handoff evidence created afterward; legacy schema1 retains its previous gates. Never require evidence generated by cleanup before cleanup can start. Gate failure never prevents cancellation/failure cleanup. Stable `problemDetails` codes name missing/mismatched fields while `problems` describes them; repair recorded gaps or use blocker recovery, never fill invented PASS/evidence strings.

After readiness and actual cleanup/handoff saves, a final evidence patch can contain:

```json
{"gates":{"evidence":{"tasks":{"status":"함","evidence":"native task IDs t1/t2: 모든 배정 작업 결과 대조 완료; <absolute-page-path>#handoff-completion-r1: 최종 revision r2와 종료 근거 저장 확인"},"shutdown":{"status":"함","evidence":"현재 run의 모든 agent 종료를 host lifecycle 결과에서 확인"},"cleanup":{"status":"안 함","evidence":"해당 없음: browser/MCP를 사용하지 않은 실행"}}}}
```

These are example fields, not substitute facts: supply the actual task references, saved HTML handoff ID, revision and host evidence. Save the matching `completion` record in `handoffs` in the same patch. A completion gate cannot prove those actions occurred merely from the text.

Every successful save receipt includes a `briefing` line for user briefings. The helper checks saved values/artifact identities; it cannot prove host execution or task authorization.

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

Other arrays (`plan`, `reviews`, `decisions`, `flow`, `tasks`) replace their entire array when supplied; include the intended full snapshot. `agents: []` makes no agent changes. Omitted fields remain unchanged. Do not pass script-owned `path`, `updated`, or `_progress`. The script embeds checkpoint/save metadata under `_progress`, escapes report text, and rejects malformed or unknown fields without replacing the existing page. Prefer `--input -` with stdin for `init`, `update`, and `brief` so routine checkpoints do not create patch JSON files. File input remains available when needed; keep it temporary and free of secrets or private reasoning.

## Save before continuing

### Phase TODO snapshot

Save `taskPlanRevision` (source plan revision) and `tasks` at the top level. Each task has exactly six string fields: nonempty `id`, `phase`, `title`, `owner`; `status` is `pending`, `in_progress`, `blocked`, or `done`; `evidence` may be empty except that `done` needs completion evidence and `blocked` needs a concrete reason. IDs are unique across Phases. Example after actual implementation reports:

```json
{"taskPlanRevision":"plan-r1","tasks":[{"id":"api-1","phase":"Phase 1 · 구현","title":"할 일 저장 API 구현","owner":"backend-1","status":"done","evidence":"API 테스트 통과 · 구현 r1 · 실행 결과 경로"},{"id":"ui-1","phase":"Phase 1 · 구현","title":"할 일 입력 화면 구현","owner":"frontend-1","status":"in_progress","evidence":"입력창 구현 보고 수신, 연결 검증 대기"},{"id":"verify-1","phase":"Phase 2 · 검증","title":"연결된 사용 흐름 검증","owner":"e2e","status":"pending","evidence":""}]}
```

`tasks` replaces the full snapshot, like `plan`; include every retained task on each task update. A status-only fragment is invalid. Reopen affected tasks and replace stale evidence after fixes; remove tasks only when an approved scope change removes them. Save independent review outcomes together after the full set arrives. The renderer groups by first Phase occurrence and derives completed counts from statuses; counts are not effort estimates.

New pages contain `tasks:[]`. When this field is present, each gate requires a nonempty checklist whose `taskPlanRevision` matches `gates.planApproved`; `complete` also requires all tasks to be `done`. `ready` uses the existing review/validation checks and does not require all TODOs done, allowing cleanup to proceed; the all-done check belongs only to `complete`. Old pages without `tasks` retain their existing gates and renderer. Use the new template on the next run rather than recreating or migrating an active page. The checklist does not replace native task state or real validation.

### Checkpoint order

Collect already-received facts into one patch, save, inspect the successful receipt, then dispatch dependent work or brief the user. Do not wait for unrelated agents to finish. Save these events:

- Kickoff and assignment: record queued/not-launched assignments before launching, then record the actual launch outcome. Do not call a queued agent active.
- Planning: save approved plan revision, allocation/contracts, and relevant plan-review transitions before implementation starts.
- Implementation: save consumed agent reports, milestone completion, changed scope, and pending integration before dependent dispatch.
- Review: save review start/collection state; keep independent verdicts and findings out of all page data until all required reviews arrive. Then save their combined results against the actual fixed review target.
- Fixes: mark affected verdicts superseded before another review round. Save blockers, browser cleanup results, and other changes needed for the next decision.
- Completion or cancellation: save the final observed state. Completion requires no pending progress updates as well as the skill's implementation, review, and cleanup gates.

Mark a report handled only after its required save succeeds. Deduplicate already-handled reports. On save failure, keep the patch pending, disclose the error and last confirmed save, and repair/retry. Do not announce completion or cross a dependent stage whose checkpoint failed. Unaffected independent work can continue. There is no timer, extra progress agent, or periodic polling.

Every briefing includes `진행판: [<작업명>](<절대 경로>) — <절대 경로> · 마지막 저장: <확인된 시각>`. Use the receipt's actual timestamp. When no facts changed, reuse the last confirmed receipt without another write.

## Required briefing template

Use this for kickoff, plan, progress, review, blocker, resume, and completion. Fill every line in plain Korean unless the user requests another language; keep technical identifiers intact. Use known facts, not expected outcomes.

```text
쉬운 요약: <무엇을 했는지 → 확인한 결과 또는 남은 일 → 다음 행동>
진행판: [<작업명>](<절대 경로>) — <절대 경로> · 마지막 저장: <successful receipt.saved_at>
단계 / revision: <현재 단계와 확인 대상>
산출물: <이번 단계 handoff/계획/검증 자료 링크와 경로, 또는 아직 없음과 이유>
확인 / 빈틈: <명령·exit code·확인한 revision·결과, 또는 미실행/막힘과 이유>
Hook: arm 요청 <미요청/접수/실패> · 등록 <확인/미확인/사용 불가> · disarm 요청 <미요청/접수/실패> · 해제 <확인/미확인/사용 불가> · <run_id와 근거, 또는 없음> · <필요하면 수동 체크포인트>
```

If the page has not been saved successfully, report that gap and omit a nonexistent link or fabricated timestamp. When it exists, reuse the same confirmed receipt. The hook line records request acceptance and actual confirmation separately even when no new facts arrived; do not write again just to repeat it. A missing hook confirmation uses manual checkpoints and never removes the ELI5, link/path/time, or handoff requirements.

## Resume

Before compaction or handoff, preserve the exact page path, last confirmed checkpoint/revision/save time, unsaved patches, outstanding agent/task IDs, and actual implementation/review target. Put this in the existing handoff or context summary; do not write hook-owned OMX runtime state.

On resume, run `status` and read the relevant `handoffs` records on that exact page; reconcile them with real host messages and current repository evidence. Existing external handoff paths from older runs remain valid read-only recovery evidence; do not recreate or migrate them merely to resume. Restore pending updates before dependent dispatch or briefing. The saved stage and IDs are diagnostic information, never execution authority. Do not find a run by selecting the newest file or create a replacement page automatically. For an older page without checkpoint metadata, inspect its saved JSON and use the first verified `update` to adopt it; do not fabricate a previous receipt.

## Scoped nonblocking host reminders

The plugin's shared `hooks/hooks.json` invokes `hooks/basic-team-progress.sh`, backed by this skill's `scripts/basic-team-progress.py`. The handlers are silent by default, including outside basic-team. The progress-page command lives beside it in `scripts/`; reminder state never edits the HTML.

Only the coordinating Main actually executing basic-team requests `arm` after initializing or verifying the exact progress page. Use the current host reference linked from SKILL.md; Claude substitutes `${CLAUDE_SESSION_ID}` in that skill body. A helper receipt is an activation request, not proof of activation. Retain its `basic_team_hook.run_id`. The corresponding successful shell-tool `PostToolUse` must verify the one-time request against actual host identity and confirm registration before reminders are available. Missing identity, unsupported payloads, errors, and absent hooks leave reminders off; apply the existing save/receipt rule and continue without treating that as a workflow blocker.

Report `요청 접수 / 등록 미확인` after a successful helper request until a matching host confirmation for that run is observed. Only that confirmation permits `등록 확인`. A successful command exit or lack of an error is not registration evidence. Apply the same distinction to disarm (`해제 요청 접수 / 실제 해제 미확인` until confirmed). Store the request receipt and actual confirmation source separately in Decisions & Blockers and `gates.evidence.hook`; absent host confirmation remains `부분` with the manual fallback, rather than `함`. Consume event evidence as it arrives; do not poll registration files to improve the status.

At completion, explicit cancellation, failure exit, or a switch to unrelated work, request disarm for that exact `run_id`:

```sh
uv run "<basic-team-base>/scripts/basic-team-progress.py" disarm --host codex --run-id "<retained-run-id>"
uv run "<basic-team-base>/scripts/basic-team-progress.py" disarm --host claude --session-id "<Claude Main session ID>" --run-id "<retained-run-id>"
```

The Claude session ID comes from the substituted skill-body command, not a guessed process environment. Never reuse a child ID or select another session's registration. Late requests from an older run cannot disable its replacement.

Event roles: `PostToolUse` on shell tools consumes arm/disarm requests, and on `Agent`/wait tools returns a short save/briefing reminder (no new facts means no page rewrite). `UserPromptSubmit` and `SessionStart` reset the guard, so rearm at the first step of every continuing work interval, including automatic continuations and after resume or compaction. `SessionEnd` removes this session's own registration. On Claude, `PreToolUse` on `Agent` denies a main-session spawn that lacks `model` or `effort`, or uses `subagent_type: "fork"`, while a run is armed; the denial text names `spawn-args`, so retry with its arguments. Codex spawns are not guarded. Explicit disarm remains necessary because termination callbacks are not guaranteed.

Records and one-time requests live under `${XDG_STATE_HOME:-~/.local/state}/lukas-plugin/basic-team`, separate from OMX/OMC runtime state. They hold routing identifiers, generation, run ID, and page path, not transcripts or report text. While a run is armed, the same directory's `spawn-calls.jsonl` appends one line per main-session `Agent`/`spawn_agent` call with the argument names and the values of `model`, `effort`, `subagent_type`, and `name` (never prompt text); it is diagnostic only, used to learn what a future blocking check could rely on. Generation changes reject delayed requests after a reset. No transcript or prompt-content scans, periodic reads, or Stop/SubagentStop continuations are added; the only denial is the armed-run `Agent` spawn check above. Generic event callbacks may still execute outside basic-team, but return no model context.

Codex activation conservatively requires the observed local shell's `CODEX_THREAD_ID` and `CODEX_SESSION_ID` to match. The verified request is then bound to the actual hook session and turn. These environment variables are a local runtime adapter, not a documented guarantee for all Codex hosts; absent or differing values disable activation. Claude uses the explicit substituted session ID and rejects child events carrying `agent_id`. Missing scope fields suppress output. These checks route advisory context and never establish permission or lifecycle authority.

Wait names and shell-output layouts vary between hosts; unsupported events and async notifications can bypass reminders. Hook execution also depends on host version, plugin loading, and trust settings. Tests of these adapters do not establish live event coverage in every App/CLI host. See [Codex hooks](https://learn.chatgpt.com/docs/hooks), [Claude hooks](https://code.claude.com/docs/en/hooks), and [Claude skill substitutions](https://code.claude.com/docs/en/skills#available-string-substitutions).
