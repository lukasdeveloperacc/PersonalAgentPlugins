# Reporting contract

Main/root is the only backend selector and writer for a run, including standalone team invocations. Leads receive the selected context and send summaries to root; workers report to their lead. Office is a visibility surface, not the scheduler or an authority grant. Use plain Korean for public progress.

## Select once; resume the same mode

Inspect available tools and actual configuration. Missing tools alone do not prove Office absent. When enabled tools are missing, use supported discovery and the installed `lukas-plugin:mcp-setup` diagnostic guidance; do not change global configuration, install or restart shared services merely to choose a backend.

| Evidence | Action |
| --- | --- |
| Office `report` and `ask` callable, initial report succeeds | Select `office`, save returned run ID; create no progress HTML |
| Office explicitly absent or disabled | Select `html`, use existing progress.py; do not require Office enablement |
| Office configured/enabled/expected but tools missing or initial report fails | NOT READY: diagnose and recover; never reinterpret as absent |
| Configuration unknown | UNKNOWN: resolve configuration; do not claim a working selected backend |
| Saved mode on resume | Keep mode and existing run ID/page; never create a replacement run |

There is no automatic mid-run Office↔HTML switch, full local snapshot or migration/merge system. A user-requested switch is separate scope. NOT READY/UNKNOWN or an outage need not stop independent product work: use terminal summaries and explicitly say reporting is unsynchronized.

Keep only minimal reconnection metadata at `<project>/docs/inprogress/<task-slug>.office.json`: `mode`, absolute `project_path`, `run_id`/`url` for Office, `page` for HTML, pending ask IDs and IDs awaiting closure. Preserve old `run_id`/`url` files as Office mode; establish and validate their project identity before a write. No tasks/reviews/decisions/full state belong in this sidecar. Existing plans and worker evidence are separate task artifacts, not a replicated tracker.

Write small JSON to a temporary file in the same directory, validate it, then atomically rename over the sidecar. Save mode/run ID only after successful creation. If the creation response is lost, do not blindly create again or claim selection completed: identify the exact run or report unresolved identity. Validate saved project path and run/page identity on resume; mismatch is a blocker for reporting writes, not a reason to create another run.

## Office

Initial `report` uses absolute `project_path`, title, known spec `doc_path` if applicable, and the first progress patch. Every subsequent `report` supplies both `project_path` and saved `run_id`. Use `http://127.0.0.1:4780/#/run/<run_id>` as the local Office link unless the deployed configuration specifies another address. Switch doc_path to the approved plan only after approval.

The MCP response is `{run_id, doc_changes}`, not the complete state. An empty patch is still a write; never use report as a getter. For resume or uncertain responses, first verify the deployed read-only HTTP contract, then use `GET http://127.0.0.1:4780/api/state` and inspect only the exact project_path/run_id. Do not output unrelated project data or save the entire response as local state. If neither identity nor prior task/review evidence can be recovered, state what cannot be verified; never invent prior state or PASS verdicts.

Validation errors, `isError`, wrong run IDs and project mismatches require correcting the cause. For connection errors/timeouts, inspect the cause and attempt one supported discovery/reconnection recovery; retry only with new evidence. Preserve stable task IDs, decision titles and review round/reviewer keys. If still unavailable, keep Office mode, explicitly report unsynchronized progress and continue independent work. Do not mark synchronization successful without a successful response.

Questions requiring the user use `ask(run_id, question, options, recommended)` with 2–4 options. An answered result supplies the answer. A pending result supplies an ask_id: persist it, continue independent work and poll that same ID rather than creating duplicate questions. If the terminal supplies the answer, use it and queue the ID for closure. Send `close_ask_ids` as a **top-level report argument**, never inside patch; clear closure metadata only after success. An outage may move the conversation to the terminal without changing reporting mode. Close remaining asks on finish/stop when possible, and expose pending synchronization if not.

If doc_changes is nonempty, read the diff and explain its impact; hold only affected work and ask whether to replan (`재계획` / `그대로 진행`). Replan through root-owned Plan lifecycle or record the reason to retain the plan. Do not invent approval questions for routine progress.

Report meaningful team state changes. At execution-loop checkpoints after 30 minutes without a change, send a summary heartbeat; do not create a timer daemon. Long ask calls require an appropriate host timeout (server hold is up to 295 seconds; configured Claude MCP_TOOL_TIMEOUT or Codex tool_timeout_sec must exceed it). Diagnose timeout settings without silently modifying global config.

## Public payload

Use only the existing schema; see [progress-example.md](progress-example.md). Team tasks summarize meaningful deliverables, with owners such as `frontend-lead`, `backend-lead`, `docs-lead`, `plan-lead`. A short note contains done/total, current work, blocker, next step and detail-artifact path. Paths are evidence references, not guaranteed clickable Office links. Office does not provide a team/worker tree: do not send `team`, `parent` or `report_to` fields.

- `tasks` merge by `id`; `decisions` by `title`; `reviews` by `round` + `reviewer`.
- Stage begins with `계획`, `구현`, `리뷰`, `수정`, `마무리`, `완료` or `중단`. `중단` means abandoned, not waiting for an answer. Keep current stage while waiting; put the question in todo/blockers.
- Task lane is work kind: `plan`, `build`, `review`, `fix`, `finish`. Task status is `대기중`, `진행중`, `완료`, `중단`; all nonwaiting tasks carry a one-line note. `after` is dependency only.
- Domain reviews are normal `lane: review` tasks with frozen revision, verdict and evidence in note. `reviews.reviewer` accepts only `Karpathy Agent`, `Ponytail Agent`, `Impeccable Agent`, `E2E Agent`.
- `todo` is a user action/decision, or `없음`. Failure/unchecked worker evidence must remain visible in the team summary.
- Put a model/effort on a card only for the actual agent represented. Preserve full requested model ID vs host-confirmed distinction; do not attach worker models to an aggregate lead card or fabricate observed settings. Root-owned PLAN/DONE cards need no model.
- Keep required review tasks open until root verifies same-revision acceptable evidence. The reducer only checks task closure; it does not independently establish review PASS. Close a finish task only after real completion.

Brief the user at plan conclusion, blockers, review-round outcomes and finish: done, remaining, user actions, blockers and link. At finish distinguish product completion from reporting synchronization and unresolved asks.

## HTML only when selected initially

Use `<project>/docs/inprogress/<task-slug>-<YYYYMMDD-HHmm>.html`. Initialize once, then send only changed fields via update; resume the saved page. Never initialize HTML because an Office run became unavailable. Run Python skill commands with `uv run`:

```sh
uv run "<basic-team-dir>/scripts/progress.py" init "<page>" --title "<작업 이름>"
uv run "<basic-team-dir>/scripts/progress.py" update "<page>" --input "<patch.json>"
uv run "<basic-team-dir>/scripts/progress.py" status "<page>"
```

The existing helper timestamps tasks and marks completion when a finish task is complete and no tasks remain open. Root must still verify required reviews and final checks. Ask questions in the terminal in HTML mode. Do not add a reporting helper or duplicate state store.
