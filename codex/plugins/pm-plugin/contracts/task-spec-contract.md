# TASK_SPEC Contract

`TASK_SPEC` is the compatibility contract between the Codex PM, Claude Developer, and Codex Reviewer roles.

Codex PM produces it. Claude consumes it. Codex Reviewer uses it as review context. Treat these fields as the source of truth for scoped implementation.

## Version

Current contract version: `1.0`

Change `spec_version` only when required fields or field semantics change. Backward-incompatible changes require updates to all consuming plugins in the same release.

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

## Conditional Design Fields

These fields are required when UI/UX is material to the task. They are optional for non-UI work and do not change `spec_version`.

```yaml
design_required: false
design_sources:
  - "DESIGN_SPEC path, SCREEN_SPEC path, Figma URL, or none"
figma_sources:
  - "Figma file/page/frame URL or none"
visual_qa_required: false
design_review_gate: "not_required|required|approved|waived_with_risk"
visual_qa_gate: "not_required|required|approved|waived_with_risk"
```

## Producer Responsibilities

Codex PM `task-spec` must:

- Emit every required field.
- Keep the task PR-sized.
- Mark ambiguity in `assumptions` or `risks`.
- Identify blocked files and permission-sensitive areas.
- Avoid authorizing production writes, secret access, merge, or release.
- If UI/UX is material, reference approved DESIGN_SPEC/Figma sources or explicitly mark the missing design gate as a risk.

## Consumer Responsibilities

Claude `implement-task` must:

- Treat the TASK_SPEC as the source of truth.
- Implement only inside `scope` and `allowed_files`.
- Avoid `blocked_files`.
- Report missing or contradictory required fields before implementation.
- Report needed scope expansion as a blocker or explicit assumption.
- For UI/UX work, treat approved DESIGN_SPEC as the design source of truth and report missing or contradictory design fields before implementation.

## Approval Boundary

Claude may implement and produce verification evidence.

Codex Reviewer may review and recommend a decision.

Only the human lead approves final merge and release.
