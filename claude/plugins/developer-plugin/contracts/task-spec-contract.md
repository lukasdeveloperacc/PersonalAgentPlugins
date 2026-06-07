# TASK_SPEC Contract

`TASK_SPEC` is the compatibility contract between the Codex PM, Claude Developer, and Codex Reviewer roles.

Codex PM produces it. Claude consumes it. Codex Reviewer uses it as review context. Treat these fields as the source of truth for scoped implementation.

## Version

Current contract version: `1.0`

## Required Fields

```yaml
spec_version: "1.0"
task_id: "stable task identifier"
title: "short task title"
context: "why this work exists"
goal: "what must be achieved"
non_goals:
  - "explicitly out of scope"
scope:
  - "work items included in this task"
allowed_files:
  - "paths or globs the Developer may edit"
blocked_files:
  - "paths or globs the Developer must not edit"
acceptance_criteria:
  - "testable product or engineering outcome"
test_plan:
  - "specific checks to run"
risks:
  - "known risk or uncertainty"
assumptions:
  - "assumption made to avoid blocking"
definition_of_done:
  - "completion condition"
reviewer_checklist:
  - "review point for Codex Reviewer"
```

## Consumer Responsibilities

Claude `implement-task` must:

- Treat the TASK_SPEC as the source of truth.
- Implement only inside `scope` and `allowed_files`.
- Avoid `blocked_files`.
- Report missing or contradictory required fields before implementation.
- Report needed scope expansion as a blocker or explicit assumption.

## Approval Boundary

Claude may implement and produce verification evidence.

Codex Reviewer may review and recommend a decision.

Only the human lead approves final merge and release.
