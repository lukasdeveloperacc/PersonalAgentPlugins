---
name: basic-team
description: Orchestrate peer Frontend, Backend, Docs and Reviewer team leads with root-owned ralplan planning and summarized progress. Use to run or resume a basic-team development workflow. Not for explaining, inspecting or editing the skills, or for a standalone specialist review.
---

# Basic Team

Main/root coordinates the teams, integrates their evidence and owns final verification and user reporting. It delegates product edits to team leads and their workers. Select only teams the request needs; do not create every team by default. Follow the user's scope and permissions; this workflow grants no commits, pushes, deployments or global configuration changes.

Read [team-contract.md](references/team-contract.md) and [reporting.md](references/reporting.md) in full before dispatch, never cut short with `head`. Use [briefs.md](references/briefs.md) for assignments and [progress-example.md](references/progress-example.md) for public patches; read [office-operations.md](references/office-operations.md) in Office mode. These contracts also govern standalone team skills.

In Office mode, at every checkpoint:

- Answer every pending `checks` entry of the last `report` response that no reporting lead owns before other reporting, through `check_replies` (see the reporting contract); it is easy to miss after a long `state`.
- Call `ask` again with each pending `ask_id` until it returns answered or, on newer Office, a `report` response's `asks` lists it answered. Office does not notify you of the user's answer, and a pending result, backgrounded or not, is not one.
- Put actual model/effort on every working card of a real agent from the team-contract actor check, root-owned cards (PLAN, DONE) with root's own; a reporting lead fills its team's; aggregate cards carry none.

## Plan and publish work

1. Check actual host hierarchy, messaging and capacity using the shared contract. Select or recover the reporting destination once using the reporting contract.
2. Main/root uses [basic-plan-team](../basic-plan-team/SKILL.md) for any needed planning, before execution teams start. Reuse an applicable approved plan rather than repeat planning. The installed ralplan harness owns its lifecycle; do not reproduce it or bypass its handoff. A plan path or Critic PASS alone is not execution authorization. Respect the user's existing execution authorization and any genuine unresolved decision. Root may skip ralplan and write `<artifact-dir>/plan.md` itself only when the user already fixed the requirement wording, no server/API/data change is involved and at most two teams own files; record decisions, owned files, checks and review scope there and publish a `계획 생략` decision with the reason, noted on the PLAN card too. Execution authority still comes only from the user's request. Otherwise run basic-plan-team.
3. Turn the plan into owned tasks with IDs, files, dependencies, acceptance criteria and exact verification commands. Choose [Frontend](../basic-frontend-team/SKILL.md), [Backend](../basic-backend-team/SKILL.md) and/or [Docs](../basic-docs-team/SKILL.md) leads. Name cross-team API and error contracts before implementation. One owner per file; record handovers and prerequisite `after` edges.
4. Decide required domain reviews and [Reviewer](../basic-reviewer-team/SKILL.md) coverage: Karpathy and Ponytail are required for implementation; Impeccable for visible UI changes; E2E for flows across screens, server or storage. Record reasons for conditional coverage. For UI/runtime changes, fix viewports, languages, themes, states/dialogs, app startup and seed data in an acceptance matrix shared by builders and reviewers. When Impeccable or E2E applies, confirm now that the app can start (Docker, images/registry login, seed data); ask the user about a blocker at this point, not when reviewers are waiting.
5. Give every card a phase TODO list before work starts, so the user watches each agent's checklist fill in: the lead card holds coordination items (split, verify, summarize) and each worker task gets its own card (see the reporting contract) with 3–8 `todos` grouped by `phase` (for example `준비`, `구현`, `검증`), each item one short line with optional `detail`, in work order (see the reporting contract). Send `todos` only when the Office `report` schema advertises them; otherwise keep `done/total` and the current item in the note (see the reporting contract). Leads return their worker split and todos before dispatching workers.
6. Publish meaningful team tasks with those todos. Brief the user on the plan, remaining work, decisions needed and reporting link. This is the **work published** checkpoint used by wrappers.

## Build and integrate

Spawn ready leads as peers under main/root; each lead owns its leaves. Allocate worker slots across the whole tree. Start dependent work only when its prerequisite evidence is accepted. Leads agree cross-team contracts and report confirmed decisions upward. Reuse idle owners for follow-ups in their scope.

Verify lead summaries against worker artifacts. A skipped check, partial assertion or unexpected behavior is an open finding, never silently a completed task. Resolve it before review or expose it as blocked. When builds finish, assign one owner the project's required full checks. Save each check's full output to `<artifact-dir>/checks-<revision>.log` and show only the summary; never pipe it through `tail` alone. On any failure, record the failing test names and first error line before rerunning. Do not run full checks while agents are editing or heavy startup is in progress. Where supported, tick todos as the reporting contract says (`{"id":"FE","todos":[{"id":"FE-2","done":true}]}`). Office check-ins in a `report` response go to that task's owner through its lead; reply with the real state through `check_replies` (see the reporting contract). Publish meaningful changes through the **status changed** checkpoint; do not relay raw worker messages to the user.

## Review and fix

Freeze the owned change: no edits to its files while reviewers work. If every change on the branch since `<base>` belongs to this run, `git diff --binary --full-index <base> > rN.patch` plus its hash is the whole freeze; the rest of this paragraph applies to shared worktrees. Record the exact base commit, explicit file list and original patch (`git diff --binary --full-index <base> -- <owned-files>`), then hash the saved patch. Include owned new files through scoped intent-to-add or a temporary index; preserve other work's staging and never use repository-wide `git add -A -N` in a shared worktree. Keep freeze artifacts outside the file list. Give every required domain reviewer and the Reviewer lead this same base, file list, patch, digest, acceptance matrix and evidence. Reviewers remain read-only and cannot see each other's results; capacity-limited batches are allowed without changing revision.

The file-scoped command assumes each included diff belongs wholly to this task. If unrelated hunks already share a file, reconcile ownership first and construct only the agreed owned patch in a temporary index or isolated checkout, or obtain explicit agreement to include the broader change. Freeze and review that exact content; merely listing the file does not isolate its hunks. Keep validation tied to the reviewed content and distinguish connected-context inspection from permission to commit external changes.

Recompute the approved diff from the same base and file/hunk selection before accepting reviews and finishing. Unrelated concurrent edits do not broaden the approved scope; assess connected changes for integration risk separately. Changed owned files need a new freeze and review. Preserve the original patch so a later authorized partial commit can be compared against it using the prospective staged diff from the same base, without reverting other work.

Wait for every reviewer, including follow-up measurements, before assigning fixes. Main/root checks all required verdicts and evidence; a tracker closing tasks does not prove review PASS. Missing required evidence is BLOCKED. Route required findings to the current file owner; advisory findings are optional. Resolve contradictory advice using a test, documentation or measurement and record the decision.

After a fix, rerun affected checks, freeze a new revision and resume reviewers with the delta and connected context. Previous PASS does not approve the new revision. Continue until all required reviews PASS on the same revision. After three nonconverging rounds, stop further fixes and present open findings and a recommendation for the user's decision.

Finalize owned product documentation before freezing when possible. If a later delta is documentation-only, reviewers still approve the new revision but may reuse named prior runtime evidence when its code, environment and acceptance criteria remain applicable; explain omitted reruns rather than silently waiving checks.

## Finish

Run required checks on the final revision. Audit every card's todos, including interrupted ones: each must be really done before its task or the run can complete, otherwise end the run `중단` with the remaining work listed. A card dropped from scope ticks a todo only after the replacement card verified that work, naming it in `detail`. Close only agents this run owns, after their results and dependents are settled. Publish the **run finished** checkpoint only when build, required review and verification evidence supports completion. Put the run's `retro` in that final report (see the reporting contract), built from the leads' `스킬 마찰` lines and your own observations. State product outcome and reporting synchronization separately; unresolved asks or an Office outage must remain visible. Return changed files, review and check results, remaining gaps, and the reporting link.

For blockers, inspect the error and relevant context, try a bounded fix within ownership, and keep independent work moving. Retry only with new evidence. Ask only for missing requirements/access or materially different outcomes, with a recommendation.
