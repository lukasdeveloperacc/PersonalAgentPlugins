---
name: basic-docs-team
description: Run or resume a documentation team with owned writers and independent reviews, or perform an assigned documentation-domain review. Use when the user requests basic-docs-team. Not for explaining or editing this skill.
---

# Basic Docs Team

Make the requested documentation agree with the implementation, contracts and intended audience. A docs-only task can finish without Frontend or Backend implementation teams.

Read the [team contract](../basic-team/references/team-contract.md) for invocation, hierarchy, models, capacity, ownership and completion gates. Use the leader/worker or domain-review brief in [briefs](../basic-team/references/briefs.md).

## Entry mode

- **Standalone:** main/root establishes the missing execution context, reads [reporting](../basic-team/references/reporting.md), and creates a Docs lead plus needed peer support such as a Reviewer lead. Root owns coordination and reporting; do not recursively invoke `basic-team`.
- **Delegated execution:** the Docs lead accepts the parent's scope and worker budget, owns its documentation leaves, verifies results and reports to the parent. Request missing implementation evidence from peer leads, and scope changes from root.
- **Domain review:** compare the assigned documentation revision with its sources read-only. Return findings without writing or creating a Reviewer team. Self-review is internal validation, not independent approval.

## Documentation work

1. Identify the audience, owned documents and source evidence: implementation, approved plan, API contracts or observed commands. Reuse a clear assignment; request a root-owned planning stage only for unresolved decisions that affect the work.
2. Split independent documents by ownership. Use the documentation executor model policy and shared worker brief. Workers report only to this lead and request a handover before changing another owner's file.
3. Reconcile statements with the actual source revision. Ask the relevant lead about a discrepancy instead of documenting a guessed behavior. Keep examples, links and entrypoint names consistent with their callers.
4. Run relevant link, format, example or command checks where safe and supported. Identify any unexecuted examples and unsupported claims explicitly.
5. Submit the bounded docs change to root for Karpathy and Ponytail reviews through the peer Reviewer team and the shared fix cycle. Do not invent UI/E2E work for text alone; apply those conditional reviews only when the actual change meets their criteria.

## Return

Return the common result with changed documents, source/review revision, verified links/examples, commands and actual results, open discrepancies and evidence paths. Complete only after root's required reviews and final checks.
