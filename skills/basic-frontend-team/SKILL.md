---
name: basic-frontend-team
description: Run or resume a frontend team with owned implementation workers and independent reviews, or perform an assigned frontend-domain review. Use when the user requests basic-frontend-team. Not for explaining or editing this skill.
---

# Basic Frontend Team

Deliver the requested UI behavior with explicit state, accessibility and API acceptance criteria.

Read the [team contract](../basic-team/references/team-contract.md) for invocation, hierarchy, models, capacity, ownership and completion gates. Use the leader/worker or domain-review brief in [briefs](../basic-team/references/briefs.md).

For implementation, both the Frontend lead and every implementation worker load and apply [Karpathy guidelines](../karpathy-guidelines/SKILL.md) and the installed `ponytail:ponytail` skill. Preserve an already active Ponytail level; otherwise use its default. Include both in each worker brief. If a dependency is unavailable, report that gap without claiming it was applied. These working guidelines do not replace independent reviews.

## Entry mode

- **Standalone:** main/root establishes the missing execution context, reads [reporting](../basic-team/references/reporting.md), and creates a Frontend lead plus needed peer support such as a Reviewer lead. Root owns coordination and reporting; do not recursively invoke `basic-team`.
- **Delegated execution:** the Frontend lead accepts the parent's scope and worker budget, creates only its own implementation leaves, verifies their results and reports to the parent. Request additional teams or planning from root.
- **Domain review:** inspect the assigned revision read-only and return findings; do not build or create a Reviewer team. Self-review is internal validation, not independent approval.

## Frontend work

1. Check whether the request already has sufficient scope and acceptance criteria. Do not replan a small clear change. Escalate unresolved design decisions to root for a `basic-plan-team` stage before dependent execution.
2. Fix the UI acceptance matrix before implementation: affected viewports, languages, themes, loading/empty/error/success states, dialogs and relevant keyboard/accessibility behavior. Include app startup and seed data. Share it with workers and the applicable Impeccable/E2E reviewers.
3. Agree API shapes, errors and responsibility boundaries with the Backend lead when present. Record both leads' agreement through root before dispatching dependent work. Split by owned files; request a recorded handover before touching another owner's files.
4. Dispatch ready implementation work using the shared worker brief. Use the host's appropriate leaf role (`executor` outside active OMX Team), not a second team orchestrator. Workers send results and blockers only to this lead.
5. Verify the implemented states and the changed component's callers with the relevant checks. Preserve skipped checks, unexpected behavior and partial assertions as open findings.
6. Send the bounded result to root for the shared frozen-revision review/fix cycle. Require Karpathy and Ponytail; visible UI changes require Impeccable, and connected flows across screens/server/storage require E2E. The peer Reviewer team owns those external reviewers.

## Return

Return the common result with changed files, revision, actual check results, acceptance-matrix coverage, outstanding findings and evidence paths. Complete only after root's required checks and review gates pass; a finished worker alone does not make the team complete.
