# HTML stage handoff record

This is a record shape and checklist, not an instruction to create a new Markdown file. Append records through `progress.py update PAGE --input -`; read the saved record with `progress.py handoffs PAGE --id ID`. One run keeps all rounds in its HTML’s `handoffs` array.

```json
{
  "handoffs": [{
    "id": "planning-to-implementation-r1",
    "transition": "planning-to-implementation",
    "round": 1,
    "revision": "approved-plan-r1",
    "outcome": "ready",
    "summary": "계획 검토를 마쳤고 구현 작업을 배정했습니다",
    "evidence": ["approved plan path + hash; gates.planReview", "native task IDs + ownership/criteria; gates.models"],
    "next": ["준비된 배정 작업을 실행"],
    "pending": []
  }]
}
```

Every field shown above is required. Optional `recordedAt` is an ISO datetime with timezone; the writer supplies the first save time for new records and preserves it on retries. `id` is a unique nonempty string; `round` is a positive integer. `transition` is `planning-to-implementation`, `implementation-to-verification`, `verification-to-fixes`, `fixes-to-verification`, or `completion`. `revision` identifies the approved plan for implementation release, or the frozen product revision for later transitions. `outcome` is `ready`, `BLOCKED`, or `cancelled`. `summary` is concise plain-language text; `evidence` is a nonempty string list of concrete references/results; `next` and `pending` are string lists and may be empty.

Saved records are immutable: an identical same-ID retry is allowed, but corrected content requires a new ID. Include task/question IDs and unsaved patches in `pending` when relevant; a ready completion must have `pending:[]`. Reference the saved record as `<absolute-page-path>#handoff-<id>` and retain its successful page receipt. Do not predict that receipt inside the record before the save succeeds.

Use the transition row in [../references/workflow-contracts.md](../references/workflow-contracts.md). Reference existing page fields, native task records, approved plan/review artifacts, and original validation results; do not repeat every report or model-settings table. Only the user or an explicit host requirement calls for an external handoff artifact; reference an existing artifact instead of generating duplicate MD exports. Older external handoffs remain readable on resume.

Before dependent dispatch, check the saved record against the actual evidence:

- Required source artifacts exist and identify the correct plan/product revision.
- Tasks have owners, prerequisites, acceptance criteria, and observed outcomes.
- Settings satisfy the run’s policy; accepted calls and actual observations stay distinct.
- Validation covers the latest relevant edit and states gaps.
- Reviews cover the same frozen revision; early independent findings stay out of all page JSON until the required set arrives.
- Tool failures remain BLOCKED without inferring a product defect.
- The page receipt is confirmed; briefing includes its path, saved time, and actual hook request/confirmation state.
- Completion additionally requires all PASS verdicts, validation, actual shutdown/cleanup, reconciled tasks, and no pending writes/updates.

An unmet required check blocks the transition. Mark genuine inapplicability with its reason and omissions with the specific user exception; a JSON record alone cannot prove host actions or grant permission.
