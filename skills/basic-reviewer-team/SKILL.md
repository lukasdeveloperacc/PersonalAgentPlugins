---
name: basic-reviewer-team
description: Run or resume the Karpathy and Ponytail review team, with conditional Impeccable and E2E reviews, for a fixed change revision. Use when the user requests basic-reviewer-team. Not for explaining or editing this skill or requesting a single named reviewer.
---

# Basic Reviewer Team

Coordinate the existing external review lineup and return an evidence-backed verdict. This team is read-only; fixes belong to the implementation owners.

Read the [team contract](../basic-team/references/team-contract.md) for invocation, independence, capacity, revision and result requirements. Read the external reviewer, Impeccable and E2E sections of [briefs](../basic-team/references/briefs.md) as applicable.

## Entry mode

- **Standalone:** main/root establishes review scope, comparison base, revision and acceptance criteria, reads [reporting](../basic-team/references/reporting.md), then creates the Reviewer lead. Return the review result without starting implementation.
- **Delegated:** the Reviewer lead receives the frozen scope and worker budget from root, dispatches only the external reviewers below, verifies their evidence and returns the aggregate. Never create another Reviewer team or select/write a reporting backend.

Frontend, Backend, Docs and Plan leads can perform separately assigned domain reviews. They are peers coordinated by root, not additional personas in this team's lineup. Their findings use the common domain-review contract, not Office's external `reviews.reviewer` field.

## Review round

1. Confirm root has frozen the change with a comparison base and digest that includes new files. No edits during the round. Carry the request, acceptance criteria, existing check evidence, prior decisions and any fix delta into each brief.
2. Dispatch independent reviewers with the shared model policy:
   - **Karpathy Agent** (required): requirements, assumptions, cross-team contracts and scope; load `karpathy-guidelines`.
   - **Ponytail Agent** (required): implementation, callers, edge cases and simplicity; load `ponytail` at full level.
   - **Impeccable Agent** (visible UI changes): design quality; load `impeccable` and supply the acceptance matrix.
   - **E2E Agent** (flows across screens, server or storage): observable connected behavior; supply scenarios, matrix, startup and fixtures.
3. Record why conditional reviews apply or are omitted. Use the existing display names above, with host-valid native IDs from the shared contract (on Claude Code reviewers have no native name; use the returned agent ID); native IDs and Office owners are separate. Missing skills or tools required for a review mean BLOCKED, not silent omission.
4. Reviewers report only to this lead and do not see each other's findings. Run in small batches if capacity requires, preserving the same revision and independence. Keep follow-up measurements in the same round; collect every review before returning findings for fixes.
5. Verify the digest still matches and all required coverage has evidence. A changed revision invalidates that round's PASS. An unchecked required matrix cell or unavailable required check is BLOCKED. Browser interaction failure is not proof of a product defect.
6. Return every verdict and required/advisory finding, checked and unchecked areas, revision and evidence. Root combines this with any domain reviews, routes fixes to current file owners, and manages the shared three-round convergence limit. Resume reviewers against a new frozen revision after fixes; never reuse old PASS as current approval.

## Return

Use the common result contract and each reviewer's JSON verdict from the brief. Notify root promptly when each review starts or finishes. A completed attempt with CHANGES_REQUIRED or BLOCKED is not product approval: report the transition and verdict to root; root closes any execution-only card with its verdict preserved and keeps the aggregate required approval gate open. When no represented reviewer is working, that gate is `대기중`; while other reviewers still work it remains `진행중`. If one card represents both, record the completed attempt's verdict without implying approval. Required approval gates close only with accepted same-revision PASS evidence. A standalone review can finish with CHANGES_REQUIRED or BLOCKED as its result; that does not approve the product change.
