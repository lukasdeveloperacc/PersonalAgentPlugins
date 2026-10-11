# Evidence-backed progress (schema 4)

Read this before saving assignments, releasing review, or publishing results. This extends the existing [checkpoint commands](progress-updates.md), model policy and [workflow gates](workflow-contracts.md); it does not replace native lifecycle or grant authority. New pages are saved observations, not live monitors. A report says what its source reported, not that the system proved exhaustive reading or host authenticity.

## Capture facts before displaying them

1. Save the task allocation and a frozen assignment before dispatch. Include task ID, logical agent ID and obligations; for review include artifact identity, criterion IDs/targets and leader-approved required/applicable flags. Explain predeclared exclusions. Do not derive obligations from the returned report.
2. On actual accepted dispatch capture the returned host identity and source response, then bind that assignment once. Accepted dispatch means “호출 수락”, not “작업 중”. A rejected call cannot bind an identity. Reusing an agent for a new revision or replacing an agent requires a new assignment; old-host or old-assignment results cannot complete its replacement.
3. Capture received progress, result, blocker and termination records with their source. Distinguish host response, child report, command result and leader record. Use the actual stable message/call reference when exposed; otherwise use null plus labeled captured content. Preserve actual observation time when available; unknown remains unknown. Saving the page never creates a fresh observation.
4. Executor reports identify assignment/task IDs, actual changed paths (including deletions), completion evidence and unchecked areas. A task result is not whole-agent completion or host termination. Keep host shutdown evidence separate.
5. Save through `update`, inspect the receipt, then release dependent work. A valid save proves consistency of saved records, not that the reported work actually happened.

Evidence is exactly one captured body or a local artifact path with its actual SHA256. Preserve original report bytes; translate explanatory UI text separately without replacing the source or changing verdict meaning. Hashes bind bytes, not source authenticity. Do not store secrets or private reasoning. An accepted send is not a recipient acknowledgement; only a captured recipient response supports that stronger claim.

Artifact-backed evidence is a durable source, including past review rounds: keep its original path and bytes available. Every helper validation rechecks those sources; a missing or changed historical report blocks updates until its exact bytes are restored. Prefer captured original report text when long-term file retention cannot be guaranteed. The saved HTML remains a historical snapshot, not a substitute for the missing source.

For new basic-team runs, file-backed evidence uses the leader's recorded private `ARTIFACT_DIR` under `/tmp`, outside the worktree. This location does not guarantee retention: do not delete referenced files at completion, disclose possible OS cleanup, and preserve the exact directory in resume context. If a source disappears, report the missing-evidence blocker; never fabricate replacement bytes or approval. Existing runs keep their original referenced paths.

## Freeze the reviewed change

After implementation/integration finishes, freeze the original baseline inventory, approved enumeration roots/patterns and declared unrelated/pre-existing exclusions. The manifest lists sorted relative changed paths with operation and content SHA256 (or explicit deletion), binding baseline, scope and exclusions into its digest. Keep progress/report artifacts outside product scope or explicitly exclude them before freeze; do not shrink scope afterwards to avoid failures.

Create an immutable artifact ID for this manifest. `gates.reviewTarget` selects that ID; the manifest digest goes to every reviewer as `revision`. Freeze assignments and the complete required assignment batch before review dispatch. Reviewers receive the same product target with their persona-specific criteria, not a claim that every reviewer must examine every Executor or file. Record inapplicability before dispatch with a reason; reviewers cannot waive their own required obligations.

At review release and ready/complete, re-enumerate the same approved scope and compare both membership and bytes. Include new untracked paths absent from the first manifest. Changed files, additions, deletions or baseline/scope/exclusion drift require a new artifact and fresh assignments/batch; preserve older rounds as history. A matching caller-supplied revision label is insufficient. Freeze edits during review and the final gate; a later product mutation invalidates affected evidence.

The HTML shows only the last verification snapshot. It cannot detect a later disk change while sitting open. Display the last verified/observed time separately from save time; absent event time stays “미확인”.

## Relationships mean different things

| Kind | Endpoints | Supported claim |
| --- | --- | --- |
| `prerequisite` | task → task | Declared prerequisite, backed by plan evidence; not delivery or execution |
| `contributes` | task → artifact | Completed source report names outputs present in that exact manifest; reported contribution, not review coverage |
| `review_assignment` | artifact → review task | Frozen assignment has an accepted host dispatch; queued assignment alone cannot create this edge |
| `delivery` | task → task | Captured source/destination assignment and host identities with `sent` or recipient-evidenced `acknowledged` |

Only create relations supported by their source records. No stage adjacency, tone, shared area, transitive path or silence creates an edge. For six implementation tasks and four reviewers, draw supported contributions → frozen artifact → accepted review tasks; never create 24 implicit individual-review edges. Later acknowledgement is a new immutable record, not a rewrite of the send. Show relation names, evidence source and unknowns in accessible text; color/motion cannot supply missing meaning. No flowing lines or pulsing nodes imply live work.

## Review results and isolation

Use the [reviewer brief](../assets/briefs/reviewer.md). Each reviewer returns exactly one structured JSON result block with `assignmentId`, `revisionDigest`, `verdict`, `criteria`, `findings`, `reportedScope` and `uncheckedScope`. The helper parses source-bound bytes, not a leader-written verdict copy. It rejects malformed/multiple result blocks, duplicate JSON keys, wrong assignment/revision and unknown/duplicate/missing criterion IDs. Every applicable assigned criterion occurs exactly once as checked or unchecked; checked criteria include evidence. Unchecked required criteria or unresolved required findings prevent PASS. Predeclared inapplicable criteria are exclusions, never reviewed coverage.

Before all required reports arrive, keep full reports, artifact paths, findings, verdicts and checked/unchecked outcomes in the leader's existing private collection, outside ALL page fields. A `result_received` observation may expose only a redacted structured receipt `captured:{"assignmentId":"<frozen ID>","hostAgentId":"<actual source identity>","receipt":true}`; immediate tool blockers may appear in `blocker` only on a `blocked` observation, without review findings, paths or arbitrary receipt text. A missing report remains missing.

Publish report evidence and one complete review round in the same atomic update. Its reports must match exactly the required assignment set frozen before dispatch; the caller cannot shrink that set to fit received reports. Do not write separate `gates.verdicts`, agent success/result summaries or editable review outcomes. Public verdicts, coverage and badges derive from the parsed source reports. A corrected result requires a new batch; previous rounds remain immutable history. PASS refers to reported assigned criteria on one target, not proof that every file was read. All required same-target PASS still needs the existing validation, task, handoff and shutdown gates.

## Frozen records and retries

`evidence`, `observations`, `artifacts`, `assignments`, `assignmentBatches`, `relations` and `reviewRounds` append by stable ID. Omission preserves records; an identical replay is a no-op. Same-ID content changes, null/deletion or conflicting host rebinding fail atomically. Use new IDs for new obligations, replacements and revisions. Preserve the complete required assignment set in the review dispatch batch. These append-only collections do not use ordinary array replacement semantics. Current target/batch selects applicability; old results cannot turn a new pending target green.

Review tasks whose latest assignment belongs only to batches preceding the selected batch remain history and are excluded from the current checklist and completion gate, without being relabeled PASS. Current required assignments still need their own reports; later or unbatched assignments remain pending rather than disappearing. Main-owned lifecycle tasks remain in the checklist and flow, outside the agent graph; never invent a child dispatch for them. Record their actual result as `source:"leader_record"`, `purpose:"leader_task_result"`, with `captured:{"taskId":"<task owned by main>","completed":true,"verification":["<actual host or command result reference>"]}` and ordinary source/time fields. This source variant cannot complete child-owned or review tasks and does not replace shutdown/cleanup gates.

## Legacy pages and explicit regeneration

Schema 1–3 remains readable/updatable with its original renderer and gate behavior. Receipts disclose its evidence limitations. Installing the new skill or updating old JSON does not repair old visuals or establish schema-4 guarantees. Do not infer missing identities, observation times, contributions or coverage from historic colors, status strings or dependencies.

For an explicitly requested regeneration, preserve the original page and copy it as history, then initialize a separately named new page through the existing `init` command. Re-enter only independently available source evidence using current assignments/manifests and clearly label unknown history. Do not manually change `_progress.schemaVersion`, copy legacy success labels into evidence, or overwrite the original. If faithful conversion is impossible, keep the old run as history and start a new v4 run with unknowns disclosed. There is no automatic migration command. Do not modify another project's existing progress page as part of a skill update.

## Helper input examples

Generate a manifest with the existing helper's snapshot operation, from the target project:

```sh
uv run "<bt>/scripts/progress.py" snapshot --input - <<'JSON'
{"root":"<absolute-project-root>","baseline":"<actual-baseline-commit>","scope":["src","tests"],"exclusions":[]}
JSON
```

Use the returned manifest as captured manifest evidence and the returned digest for the artifact. Replace example scope with the approved task scope before freezing; do not reuse example hashes/host IDs. Snapshot capture does not itself create an artifact, assign a reviewer or publish a report.

These fragments describe records to append in a complete `update` patch; referenced tasks, agents, manifest evidence and artifacts must already exist or be saved together:

```json
{
  "assignments": [{"id":"review-k-r2","taskId":"review-k-task-r2","agentId":"karpathy","artifactId":"r2","criteria":[{"id":"contract-1","target":"supplier API contract","required":true,"applicable":true}]}],
  "assignmentBatches": [{"id":"batch-r2","artifactId":"r2","requiredAssignments":["review-k-r2","review-p-r2"]}],
  "gates": {"reviewTarget":"r2","reviewBatch":"batch-r2"}
}
```

The example batch assumes the corresponding Ponytail assignment is also saved; add every activated reviewer. `assignmentBatches` is append-only and immutable like the other frozen collections. Never change the saved required set when a report is missing.

After actual accepted dispatch, capture the actual response with `source:"host_response"`, `sourceRef` and `observedAt` (null when unavailable), and `captured:{"assignmentId":"review-k-r2","hostAgentId":"<actual returned identity>","accepted":true}`. Add a `dispatch_accepted` observation referring to that evidence and assignment. Its accepted assignment relation connects `{"type":"artifact","id":"r2"}` to `{"type":"task","id":"review-k-task-r2"}`; it is not a direct Executor/reviewer edge.

Only in the full-set publication patch append each report's evidence with `purpose:"review_result"`, `source:"child_report"`, the frozen `assignmentId`, actual source `hostAgentId`, `sourceRef`, `observedAt`, and either `captured` containing the original result text or `artifact` plus `sha256`. In that same patch append:

```json
{"reviewRounds":[{"id":"round-r2","batchId":"batch-r2","artifactId":"r2","requiredAssignments":["review-k-r2","review-p-r2"],"reports":{"review-k-r2":"report-k-r2","review-p-r2":"report-p-r2"}}]}
```

This example is complete only when those are exactly the batch's required assignments and both referenced source reports are included/valid. Use `gate PAGE --stage review` before review dispatch, `gate PAGE --stage ready` before cleanup and `gate PAGE --stage complete` after final lifecycle evidence; failed manifest/report checks require repair, not rewriting success labels.

For a non-review task result, the structured captured receipt uses `assignmentId`, actual source `hostAgentId`, `completed` (true only with the report’s acceptance evidence), `paths` (actual relative outputs, including deletions), and `verification` (a nonempty array of actual check/result references when `completed:true`). Preserve the received report and completion evidence in that captured record; attribute it as `source:"child_report"`, not host confirmation. A `result_received` observation refers to this evidence. Use that same source record for a `contributes` relation only when its output paths occur in the selected manifest. Do not manufacture completed/paths/verification when a report omits them; obtain the missing result from its owner.

For a `prerequisite`, use `source:"leader_record"` with `captured:{"fromTaskId":"<source task>","toTaskId":"<dependent task>","planRevision":"<actual plan revision>"}`. The captured endpoints must match the relation. This is declared plan evidence, not a host event.

For `delivery`, the captured record carries `sourceAssignmentId`, `destinationAssignmentId`, `sourceHostAgentId`, `destinationHostAgentId` and `state:"sent"` or `"acknowledged"`. The assignments and accepted host identities must match both task endpoints. Acknowledgement requires `source:"child_report"` and top-level `hostAgentId` equal to the recipient’s actual identity; a send receipt cannot supply it.
