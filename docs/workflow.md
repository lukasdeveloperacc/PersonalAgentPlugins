# PM / Developer Workflow

This repository defines a paired AI-native workflow:

- Codex has separate PM and Reviewer plugins.
- Claude acts as Developer.
- The human lead approves final merge and release.

## Standard Flow

1. Codex PM runs a workshop with `pm-plugin:brainstorm` when the idea is vague or large.
2. Codex PM ranks and grooms backlog with `pm-plugin:roadmap-rank`, `pm-plugin:backlog-groom`, or `pm-plugin:pm-sync` when needed.
3. Codex Reviewer gates PM artifacts with `reviewer-plugin:spec-review` when the work is large, ambiguous, technical, or long-running.
4. Codex PM creates a TASK_SPEC and Claude handoff with `pm-plugin:task-spec`.
5. Codex Reviewer checks Developer readiness with `reviewer-plugin:task-spec-review`, `reviewer-plugin:handoff-review`, and `reviewer-plugin:db-contract-review` when data surfaces are affected.
6. Claude Developer implements the TASK_SPEC with `developer-plugin:implement-task`.
7. Claude runs verification with `developer-plugin:verify-app`.
8. Codex Reviewer reviews the diff or PR with `reviewer-plugin:pr-review`.
9. The human lead decides whether to merge or release.

## Role Boundaries

Codex PM:

- Defines scope, non-goals, acceptance criteria, and reviewer checklist.
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
