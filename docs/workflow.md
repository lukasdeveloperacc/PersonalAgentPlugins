# PM / Developer Workflow

This repository defines a paired AI-native workflow:

- Codex has separate PM and Reviewer plugins.
- Claude acts as Developer.
- The human lead approves final merge and release.

## Standard Flow

1. Codex PM starts with `pm-plugin:brainstorm` as the conversational entry point for first-project onboarding, feature shaping, user-provided site investigation, refactor discovery, bug themes, or docs/handoff planning.
2. Codex PM researches current external best practices first when upstream behavior, standards, or version-aware guidance matters.
3. Codex PM produces a `Discovery Dossier` from available docs/code/schema/backlog evidence and the research pass.
4. Codex PM presents a `Workflow Decision Gate` and asks the human to confirm whether to interview more, research first, plan first, create a full bundle, create a standard bundle, or produce TASK_SPEC only.
5. Codex PM ranks and grooms backlog with `pm-plugin:roadmap-rank`, `pm-plugin:backlog-groom`, or `pm-plugin:pm-sync` when needed.
6. Codex Reviewer gates PM artifacts with `reviewer-plugin:spec-review` when the work is large, ambiguous, technical, or long-running.
7. Codex PM creates a TASK_SPEC and Claude handoff with `pm-plugin:task-spec`.
8. Codex Reviewer checks Developer readiness with `reviewer-plugin:task-spec-review`, `reviewer-plugin:handoff-review`, and `reviewer-plugin:db-contract-review` when data surfaces are affected.
9. Claude Developer implements the TASK_SPEC with `developer-plugin:implement-task`.
10. Claude runs verification with `developer-plugin:verify-app`.
11. Codex Reviewer reviews the diff or PR with `reviewer-plugin:pr-review`.
12. The human lead decides whether to merge or release.

## Role Boundaries

Codex PM:

- Defines scope, non-goals, acceptance criteria, and reviewer checklist.
- Uses `brainstorm` as the first PM conversation before turning uncertainty into documents or TASK_SPECs.
- Investigates available project evidence before drafting final artifacts.
- Uses Chrome DevTools MCP for public read-only site investigation when the user provides a URL.
- Uses external research when current best practices or upstream behavior matter.
- Asks the human to confirm the workflow path before producing final document bundles.
- Produces PM workshop, SDD, backlog, TASK_SPEC, and Claude handoff drafts.
- Uses GitHub as state/tracking and Markdown as decision/spec/handoff SoT.
- Does not implement code.
- Does not run Claude directly.
- Does not perform final PR review.

Claude Developer:

- Implements inside the TASK_SPEC.
- Produces verification evidence.
- Does not approve merge or release.

Codex Reviewer:

- Reviews PM artifacts and Claude handoffs before implementation starts.
- Reviews changes and recommends `APPROVE`, `REQUEST_CHANGES`, or `COMMENT_ONLY`.
- Does not create the PM TASK_SPEC.
- Does not run Claude directly.
- Does not perform final merge or release approval.

Human lead:

- Owns final merge and release decisions.
- Owns ambiguous product/technical decisions that the PM workshop cannot safely resolve.

## Versioning

Use `0.x` releases while the plugin schemas and TASK_SPEC contract are still stabilizing.

Any backward-incompatible TASK_SPEC contract change must update both the Codex and Claude skills in the same release.
