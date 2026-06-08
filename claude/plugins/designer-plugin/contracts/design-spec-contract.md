# DESIGN_SPEC Contract

`DESIGN_SPEC` is the compatibility contract between Claude Designer, Codex PM, Codex Reviewer, and Claude Developer.

Claude Designer produces it. Codex Reviewer checks it. Claude Developer consumes it with the TASK_SPEC. Markdown remains the durable source of truth even when Figma is used.

## Required Fields

```yaml
design_spec_version: "1.0"
design_task_id: "DESIGN-000"
title: ""
source_pm_artifacts:
  - "path or issue URL"
figma_sources:
  - "Figma file/page/frame URL or none"
figma_write_scope:
  mode: "none|read_only|draft|duplicate|branch|sandbox|approved_official"
  target: ""
  approved_by: ""
target_users:
  - ""
design_intent: ""
ux_flow:
  - ""
screens:
  - name: ""
    purpose: ""
    layout: ""
    states:
      - "default"
component_specs:
  - name: ""
    anatomy: ""
    variants:
      - ""
responsive_rules:
  - ""
accessibility_notes:
  - ""
content_rules:
  - ""
implementation_constraints:
  - ""
visual_qa_checklist:
  - ""
open_decisions:
  - ""
human_approval_required:
  - ""
```

## Figma Write Policy

Designer may write to Figma only when the target file/page/frame is explicitly identified and approved for the current task.

Allowed without additional approval only when already authorized by the task:

- Draft frames in an approved draft, duplicate, branch, or sandbox file.
- Annotations, layout variants, and component-state mockups inside the approved write target.
- Markdown updates that record Figma changes.

Blocked unless the current task explicitly approves it:

- Production/source-of-truth Figma components.
- Shared tokens, variables, libraries, or published components.
- Deletions of frames, pages, components, assets, or design-system objects.
- Broad rebrands, information architecture changes, or user-flow changes.
- Authenticated Figma access outside the configured project/workspace boundary.

## Producer Responsibilities

Claude Designer must:

- Produce every required field.
- Mark missing Figma context or missing approval explicitly.
- Keep Figma writes inside the declared `figma_write_scope`.
- Update Markdown after Figma changes.
- Preserve PM scope, non-goals, and acceptance criteria.

## Consumer Responsibilities

Claude Developer must:

- Treat `DESIGN_SPEC` as binding when UI/UX is material.
- Use TASK_SPEC for implementation scope and DESIGN_SPEC for UI/UX intent.
- Report missing, contradictory, or unapproved design fields before implementation.
- Avoid implementing design changes that are outside TASK_SPEC or unapproved Figma scope.

Codex Reviewer must:

- Check PM alignment, Figma write policy, implementation readiness, visual QA criteria, and human approval gaps.
