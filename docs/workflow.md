# PM / Developer Workflow

This repository defines a paired AI-native workflow:

- Codex has separate PM and Reviewer plugins.
- Claude acts as Developer.
- The human lead approves final merge and release.

## Standard Flow

1. Codex PM creates a TASK_SPEC with `pm-plugin:task-spec`.
2. Claude Developer implements the TASK_SPEC with `developer-plugin:implement-task`.
3. Claude runs verification with `developer-plugin:verify-app`.
4. Codex Reviewer reviews the diff or PR with `reviewer-plugin:pr-review`.
5. The human lead decides whether to merge or release.

## Role Boundaries

Codex PM:

- Defines scope, non-goals, acceptance criteria, and reviewer checklist.
- Does not implement code.
- Does not perform final PR review.

Claude Developer:

- Implements inside the TASK_SPEC.
- Produces verification evidence.
- Does not approve merge or release.

Codex Reviewer:

- Reviews changes and recommends `APPROVE`, `REQUEST_CHANGES`, or `COMMENT_ONLY`.
- Does not create the PM TASK_SPEC.
- Does not perform final merge or release approval.

Human lead:

- Owns final merge and release decisions.

## Versioning

Use `0.x` releases while the plugin schemas and TASK_SPEC contract are still stabilizing.

Any backward-incompatible TASK_SPEC contract change must update both the Codex and Claude skills in the same release.
