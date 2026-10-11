# Main-owned progress checkpoints

Records in `flow`, `plan`, `reviews`, `decisions`, `tasks`, `agents`, and `handoffs` accept optional `recordedAt` (ISO datetime with timezone). The writer supplies the first save time for new records when omitted; it is a recording time, not proof of when the underlying event occurred. Resending an existing ID or unchanged list entry preserves its time; do not copy timestamps into newly created records. Legacy entries without a known time remain undated. Agent `reported` remains the separate actual report time/text. Lists display oldest first, with stable ordering for equal times and undated entries last; Phase/stage grouping and flow dependency order remain intact. Stored handoff append order still controls gates. Existing HTML renderers are preserved by `update`; the new display applies to pages created from the updated template.


The Main session owns the meaning of each report. `scripts/progress.py` only validates and saves the page; a successful receipt does not prove that implementation, review, or user-facing briefing occurred. Use the same page for the same run across added requests, compaction, and session resume.

Before each save, apply the skill's ELI5-style plain-Korean rule to every changed user-facing field unless the user requested another language. Explain the result, what was verified or remains unresolved, and the next action; do not paste English reviewer reports into explanatory `reviewNotice`, `decisions`, or agent text. Preserve original source evidence unchanged for parsing; schema-4 review outcomes derive from it. Preserve verdict meaning, evidence, technical identifiers, and reported times. The script stores supplied text and does not translate or summarize it.

## Commands

Run from the executing project's root, not the plugin installation directory. Resolve the script from the installed basic-team skill directory. PAGE must be an absolute path beneath that project's `docs/inprogress`.

Only PAGE belongs in `docs/inprogress`. At kickoff create `ARTIFACT_DIR` with `mktemp -d /tmp/basic-team-XXXXXX`, record its exact path in Decisions, and include it in child Inputs and resume context. Put file-backed plans, planning reviews, reports, validation outputs, helper inputs, and the leader task record there. `gates.planReview.artifact` and its review entries accept these absolute temporary paths with their actual SHA256; the gate still reads and verifies the same bytes. Prefer stdin and captured reports when no file is required. Do not delete referenced artifacts during cleanup; `/tmp` removal can leave a readable HTML snapshot whose file-backed verification/resume is blocked.

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

New schema-4 source, assignment, manifest, relation and review publication rules are in [evidence-progress.md](evidence-progress.md). Read that reference before dispatch. The policy/model/plan/validation/lifecycle checks below continue to apply; legacy verdict/status examples are explicitly marked and must not be copied into v4 patches.

New `init` defaults `gates.observationPolicy` to `invocation-evidence-v2`; use `init ... --observation-policy strict-observation-v1` when the user requires actual-setting proof. New pages store script-owned `_progress.schemaVersion:4`, adding evidence-backed relationships/reviews while retaining the accepted invocation, plan/conditional/validation/terminal checks and embedded stage handoffs under BOTH policies. Legacy schema1–3 pages retain their existing checks and renderer, remain readable, and are not silently upgraded by update (missing policy means strict v1). Their receipts explicitly disclose legacy evidence limitations; no schema-4 guarantee applies to them. Preserve the policy at resume; `update` cannot change/relax it. Policy is a check criterion, not host authority.

Save these `gates` fields with `update`:

- `planApproved`: approved plan revision; this label alone is not plan-review evidence.
- `planReview`: `{method:"ralplan", revision:<planApproved>, artifact:<plan path>, sha256:<actual plan file hash>, reviews:[{role:"architect",revision,artifact,sha256,verdict:"APPROVE"},{role:"critic",revision,artifact,sha256,verdict:"APPROVE"}]}`. These entries record actual ordered reviews on the same plan; Critic receives Architect evidence. With permitted `plan` fallback use `method:"plan"`, `reviews:[]`, and `fallbackEvidence` explaining verified absence of ralplan. File/hash checks do not prove approval quality or correct review execution.
- `conditionalReviews`: `{impeccable:{required:<boolean>,reason:<scope evidence>}, e2e:{required:<boolean>,reason:<scope evidence>}}`; both explicit decisions must agree with `requiredReviewers`. The Planner/leader judge actual UX/connected-flow facts; the helper does not infer them from filenames.
- `requiredReviewers`: reviewer IDs `karpathy`, `ponytail`, plus activated `impeccable`, `e2e`; `reviewTarget`: the selected frozen artifact ID in schema 4 (legacy: PRODUCT revision/content identity), never the page save revision.
- `verdicts`: derived from a complete source-bound `reviewRounds` publication in schema 4; callers cannot supply it. Legacy schema1–3 only: `{name:{revision,verdict}}`, saved as the complete required set, with `{}` clearing superseded results. Product edits require a new frozen artifact/assignment batch and fresh reports from all required reviewers; retain old rounds, never relabel an old PASS.
- `models`: `{agent-id:{role,requested,invocation,observed,observedEffort,observationEvidence,invocationArguments,invocationAccepted,invocationEvidence}}`. `requested` is the exact spawn-args ID; Architect/Critic have their own `role:"architect"|"critic"` records but use Planner tier; ralplan requires both role records. `invocation` is a human-readable call description, while `invocationArguments` is the ACTUAL call object (Codex `model`/`reasoning_effort`, Claude `model`/`effort`), `invocationAccepted:true` requires a successful host call, and `invocationEvidence` identifies that source/child ID. Accepted correct invocation permits v2 work when actual observations remain `미확인`. Host-observed values go in `observed`/`observedEffort` with `observationEvidence` (source/identity/time/output/path). Never copy arguments or child's self-report into these fields. Legacy self-report stays in `agents[].observation`; schema 4 stores it as labeled `child_report` source evidence bound to the accepted assignment, never as host observation. Strict policy requires actual observations or a specific permitted missing-observation exception. Known mismatch, missing arguments or rejected call blocks under either policy.
- `exceptions`: `{agent-id:<specific user's approval for missing observation>}` for strict cases only. Clear stale exceptions on replacement with `null`; never use one for known mismatches.
- `validation`: `{revision:<reviewTarget>,status:"PASS"|"CHANGES_REQUIRED"|"BLOCKED",evidence,checks:[{command,revision,exitCode:0,evidence}]}`. Commands/checks identify final product revision and actual results. Only genuinely inapplicable validation uses `checks:[]` and `notApplicable:<reason>`; a missing/forbidden required test is a gap, not inapplicability or PASS.
- `evidence`: `{hook|eli5|planning|tasks|validation|shutdown|cleanup:{status,evidence}}`. Schema2–4 complete requires `tasks` with `status:"함"` and nonempty evidence identifying the reconciled task record and applicable saved stage/completion handoffs; `부분`, missing/null records or unsaved handoffs cannot clear it. It also requires shutdown `status:"함"` with real termination evidence, except the schema-4 Codex task-quiescence path below, which retains shutdown `부분`; cleanup is `함`, or `안 함` with a concrete `해당 없음` reason. Hook absence uses the documented manual fallback and remains partial confirmation, never fabricated success.


For schema-4 Codex sessions without native object termination/verification, follow [host-codex.md](host-codex.md) and save `gates.lifecycle`:

```json
{"host":"codex","mode":"task-quiescence","terminationSupported":false,"terminationRequired":false,"capabilityEvidence":"native-capabilities","snapshotEvidence":"native-idle-snapshot"}
```

`terminationRequired` records whether the user explicitly requires object disposal; true blocks this fallback. This path cannot replace a supported shutdown that failed or apply to Claude/legacy pages. Missing terminate API alone does not block preflight.

Append these ordinary immutable evidence records with real source references/times (null when unknown):

- `native-capabilities`: `source:"leader_record"`, `captured:{"tools":["collaboration.spawn_agent","collaboration.interrupt_agent","collaboration.list_agents"],"terminationSupported":false}` based on the actual exposed tool descriptions, not these example names copied as proof.
- `native-idle-snapshot`: `source:"host_response"`, `captured:{"agents":[{"hostAgentId":"<accepted native identity>","state":"completed"}],"pending":[],"observationsDigest":"<fresh status receipt lifecycleObservationsDigest>"}`. Capture every accepted identity in this run, including planning and replaced agents; use actual host-observed `completed`, `idle`, or `interrupted`. Omission, running/unknown states, or pending work fails. Preserve raw host output in the source reference; the captured shape is a normalized status extract, not a termination acknowledgement.

`pending:[]` means the leader has reconciled unfinished tasks/messages, writes and ALL owned background commands. It is not an assertion that interrupt automatically killed processes. Capture command completion or supported scoped cancellation results before clearing pending. Every accepted model invocation must have tracked agent/assignment/dispatch evidence. Read `status PAGE` to obtain `lifecycleObservationsDigest`, capture the corresponding fresh native status, and save without intervening work. New dispatch/progress/observations invalidate the snapshot; resume must save a new assignment/dispatch before reactivation. Record `gates.evidence.shutdown` as `부분` with “실행 중인 작업 없음; 에이전트 객체 종료 미확인”. The helper independently checks task/review completion, exact tracked identities and snapshot freshness; `compliance` never turns this path into shutdown `함`.

`handoffs` is a top-level append-only array, not a gate field. Each record uses the shape in [../assets/stage-handoff-template.md](../assets/stage-handoff-template.md). IDs are unique across the run; an identical same-ID retry is a no-op for the record, while changed content needs a new ID. Read records with `handoffs PAGE [--id ID]`, which also returns confirmed page receipt metadata without writing. Save the handoff with the associated stage facts in one `update` patch and verify its receipt before release. Schema3/4 implementation requires a ready `planning-to-implementation` record for `planApproved`; review requires a ready `implementation-to-verification` or `fixes-to-verification` record for `reviewTarget`; ready requires that review-entry record, and complete also requires a ready `completion` record for `reviewTarget` with `pending:[]`. Gate checks use record append order: implementation requires the latest overall record to be `planning-to-implementation`; review/ready require the latest non-completion record to be `implementation-to-verification` or `fixes-to-verification`; complete additionally requires the latest overall record to be `completion`. Later recovery or replanning supersedes earlier review-entry evidence, even for the same revision: save a fresh review-entry record and a fresh completion after recovery. These checks do not prove host work occurred.

`gates.models`, `gates.evidence`, and `gates.exceptions` merge per key; `null` removes a record, and other gate fields replace. Page/model/review compliance rows are derived, not supplied. All fields are leader-reported evidence; verify source artifacts and host facts before dependent dispatch.

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

For renderer verification, use an already installed Playwright package and Chrome; do not install a dependency for this check. Point `NODE_PATH` at the existing directory containing `playwright`:

```sh
NODE_PATH="<existing-node_modules-directory>" node "<basic-team-base>/scripts/tests/test_progress_browser.cjs"
```

The harness checks desktop 1194×801 and narrow 390×844 relation endpoints, static states, evidence details, escaping, keyboard/modal behavior, history and legacy rendering. Narrow screens use the text relationship list instead of overlapping SVG lines. It prints its temporary screenshot directory; those fixtures are renderer checks, not source evidence for a real run. Missing installed Playwright or Chrome is an explicit browser-verification gap, not a passing check.

`init` creates a page from the common template and refuses an existing file. `update` preserves its renderer and saves atomically. `status` reads without writing. Successful commands print a JSON receipt containing `path`, `saved_at`, `checkpoint`, and `revision`. Retain that receipt for the next briefing. `revision` counts page saves; it is not the implementation revision or review target.

Pass only changed fields in the input JSON. Agent patches merge by stable `id`, preserving omitted fields and other agents. A new agent needs its stable id, name, role and area (legacy schema1–3 also require status); supply allocation/model fields when known. Schema 4 rejects editable status, tone, result, reported, observation and dependsOn on agents/tasks; use assignments, evidence and observations. Older agents without IDs remain untouched and cannot receive individual patches without an explicit data migration. For legacy pages, new dependency IDs must refer to agents already present or created in the same input; untouched legacy unresolved relationships remain readable. Do not invent relationships to satisfy validation.

Legacy schema1–3 update example only (v4 uses source-bound observations, not editable success labels):

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

Ordinary arrays (`plan`, `decisions`, `flow`, `tasks`, and legacy `reviews`) replace their entire array when supplied; include the intended full snapshot. `agents: []` makes no agent changes. Omitted fields remain unchanged. Do not pass script-owned `path`, `updated`, or `_progress`. The script embeds checkpoint/save metadata under `_progress`, escapes report text, and rejects malformed or unknown fields without replacing the existing page. Prefer `--input -` with stdin for `init`, `update`, and `brief` so routine checkpoints do not create patch JSON files. File input remains available when needed; keep it temporary and free of secrets or private reasoning.

## Save before continuing

### Phase TODO snapshot

Save `taskPlanRevision` (source plan revision) and `tasks` at the top level. Schema 4 allocation records have nonempty `id`, `phase`, `title`, `owner` and optional explanatory `evidence`; omit `status`, which is derived from the current owned assignment and source observations/reports. Legacy schema1–3 records have six string fields: `id`, `phase`, `title`, `owner`, `status` (`pending`, `in_progress`, `blocked`, `done`) and `evidence`; done/blocked requires evidence. IDs are unique across Phases. Legacy status example after actual implementation reports (v4 additionally requires matching assignment/result evidence; the label alone proves nothing):

```json
{"taskPlanRevision":"plan-r1","tasks":[{"id":"api-1","phase":"Phase 1 · 구현","title":"할 일 저장 API 구현","owner":"backend-1","status":"done","evidence":"API 테스트 통과 · 구현 r1 · 실행 결과 경로"},{"id":"ui-1","phase":"Phase 1 · 구현","title":"할 일 입력 화면 구현","owner":"frontend-1","status":"in_progress","evidence":"입력창 구현 보고 수신, 연결 검증 대기"},{"id":"verify-1","phase":"Phase 2 · 검증","title":"연결된 사용 흐름 검증","owner":"e2e","status":"pending","evidence":""}]}
```

`tasks` replaces the full snapshot, like `plan`; include every retained task on each task update. A status-only fragment is invalid. Reopen affected tasks and replace stale evidence after fixes; remove tasks only when an approved scope change removes them. For an approved plan task replacement, retain the old task as history with `supersededBy` naming its replacement; exclude it from current counts without calling it complete. Save independent review outcomes together after the full set arrives. The renderer groups by first Phase occurrence and derives completed counts from evidence-backed task views in schema 4 (legacy: saved statuses); counts are not effort estimates.

New pages contain `tasks:[]`. When this field is present, each gate requires a nonempty checklist whose `taskPlanRevision` matches `gates.planApproved`; `complete` also requires all tasks to be `done`. `ready` uses the existing review/validation checks and does not require all TODOs done, allowing cleanup to proceed; the all-done check belongs only to `complete`. Old pages without `tasks` retain their existing gates and renderer. Use the new template on the next run; explicit regeneration limits are in evidence-progress.md. The checklist does not replace native task state or real validation.

### Checkpoint order

Within a released phase, dispatch newly ready tasks from verified prerequisites before batching the received facts into one checkpoint. Do not wait for unrelated agents or perform one save per reply. Save these meaningful events:

- Kickoff and assignment: freeze obligations before launching; batch assignment and actual launch receipts without a separate HTML roundtrip per child. Queued assignments remain 대기중; accepted dispatch moves workflow status to 진행중 (responsibility accepted), without claiming observed live execution.
- Planning: save approved plan revision, allocation/contracts, and relevant plan-review transitions before implementation starts.
- Implementation: batch received reports, milestone completion, changed scope and pending integration. Ready tasks inside the released phase need real prerequisite evidence, not a fresh HTML receipt.
- Review: save review start/collection state; keep independent verdicts and findings out of all page data until all required reviews arrive. Then save their combined results against the actual fixed review target.
- Fixes: mark affected verdicts superseded before another review round. Save blockers, browser cleanup results, and other changes needed for the next decision.
- Completion or cancellation: save the final observed state. Completion requires no pending progress updates as well as the skill's implementation, review, and cleanup gates.

Track consumed outcomes separately from pending page patches: consume each outcome once, and clear its pending patch only after a successful save. On save failure, retain the patch and last confirmed receipt, repair/retry at the next checkpoint, and disclose the gap. Continue ready authorized work within the released phase; required phase gates and final completion still need their saved evidence. There is no timer, extra progress agent, or periodic polling.

Every briefing includes `진행판: [<작업명>](<절대 경로>) · 마지막 저장: <확인된 시각>`; the absolute path stays in the link and page copy control. Use the receipt's actual timestamp. When no facts changed, reuse the last confirmed receipt without another write.

## Routine briefings

Keep routine updates short and factual, for example:

```text
현재: 독립 리뷰 · 4명 중 2명 결과 수신
완료: 구현·통합·필수 검사
남은 일: 리뷰 결과 처리 → 최종 확인
막힌 일: 없음
진행판: [<작업명>](<절대 경로>) · 마지막 저장: <confirmed receipt.saved_at>
```

Use only **대기중 / 진행중 / 완료** for task and agent status. Not started is 대기중; accepted responsibility, work, review, fixes or a blocked started task is 진행중; 완료 requires acceptance evidence (reviews require the complete published batch). Show a short blocker reason beside 진행중. Receipt counts may be exposed during review collection, but findings and verdicts stay private until the complete set arrives. Events such as 호출 수락/결과 수신 and verdicts are details, not statuses.

Put commands, revision/hash identities, artifact links, model/effort and hook request/confirmation evidence in expandable details and the final compliance report instead of repeating them in each update. Mention relevant validation gaps or reporting failures briefly. If no successful save exists, disclose that and omit a nonexistent link or timestamp. Reuse the confirmed receipt when no facts changed; missing hook confirmation uses manual checkpoints without slowing ready work.

## Resume

Before compaction or handoff, preserve the exact page path, last confirmed checkpoint/revision/save time, unsaved patches, outstanding agent/task IDs, and actual implementation/review target. Put this in the existing handoff or context summary; do not write hook-owned OMX runtime state.

On resume, run `status` and read the relevant `handoffs` records on that exact page; reconcile them with real host messages and current repository evidence. Existing external handoff paths from older runs remain valid read-only recovery evidence; do not recreate or migrate them merely to resume. Restore pending updates before a required phase gate or final completion; after reconciling actual prerequisites, independent work in an already released phase may continue. The saved stage and IDs are diagnostic information, never execution authority. Do not find a run by selecting the newest file or create a replacement page automatically. For an older page without checkpoint metadata, inspect its saved JSON and use the first verified `update` to adopt it; do not fabricate a previous receipt.

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
