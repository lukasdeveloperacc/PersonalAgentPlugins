---
name: basic-backend-team
description: Run or resume a backend team with owned implementation workers and independent reviews, or perform an assigned backend-domain review. Use when the user requests basic-backend-team. Not for explaining or editing this skill.
---

# Basic Backend Team

Deliver the requested API or data behavior with explicit contracts and failure-case verification.

Read the [team contract](../basic-team/references/team-contract.md) for invocation, hierarchy, models, capacity, ownership and completion gates. Use the leader/worker or domain-review brief in [briefs](../basic-team/references/briefs.md).

For implementation, both the Backend lead and every implementation worker load and apply [Karpathy guidelines](../karpathy-guidelines/SKILL.md) and the installed `ponytail:ponytail` skill. Preserve an already active Ponytail level; otherwise use its default. Include both in each worker brief. If a dependency is unavailable, report that gap without claiming it was applied. These working guidelines do not replace independent reviews.

## Entry mode

- **Standalone:** main/root establishes missing execution context, reads [reporting](../basic-team/references/reporting.md), and creates a Backend lead plus needed peer support such as a Reviewer lead. Root owns coordination and reporting; do not recursively invoke `basic-team`.
- **Delegated execution:** the Backend lead accepts the parent's scope and worker budget, owns its implementation leaves, verifies their results and reports to the parent. Request other teams or planning from root rather than spawning peer teams as children.
- **Domain review:** review the assigned revision read-only against the backend contract. Return findings without implementing or creating a Reviewer team. Self-review is internal validation, not independent approval.

## Backend work

1. Reuse an adequate plan or clear task contract. Send unresolved architectural decisions to root for a `basic-plan-team` stage before dependent execution; do not require planning again for an already bounded change.
2. Define affected inputs/outputs, validation, error semantics, authorization and data invariants. Include migration or compatibility behavior only where the change affects it. With a Frontend lead, agree the API contract and record both leads' confirmation through root.
3. Split by file ownership and dependency. Give each worker the exact contract, acceptance criteria and check commands; a shared file needs a recorded ownership handover before another worker edits it.
4. Dispatch ready leaves with the shared worker brief and host's appropriate leaf role (`executor` outside active OMX Team). Workers report only to this lead. Keep independent work moving while a dependency is blocked.
5. Verify the changed callers and relevant success, validation, permission and failure cases. Surface skipped checks or uncertain data behavior as open findings, not a successful check.
6. Return the bounded change to root for the shared frozen-revision review/fix cycle. Karpathy and Ponytail remain required; request E2E when the changed flow crosses screens, server or storage. Request other domain review only where its scope adds needed evidence.

## Return

Return the common result with changed files, revision, actual check results, contract decisions, open findings and evidence paths. Root owns required-review and final-check completion; do not turn a partial worker result into team completion.
