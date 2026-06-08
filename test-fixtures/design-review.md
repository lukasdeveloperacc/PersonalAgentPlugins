# Fixture: Codex Design Review

Use with:

```text
reviewer-plugin:design-review
```

## Prompt

Review this DESIGN_SPEC before Claude Developer implementation.

```yaml
design_spec_version: "1.0"
design_task_id: "DESIGN-001"
title: "Wholesale Collection Start"
source_pm_artifacts:
  - "docs/pm/agentic-marketplace-workshop.md"
figma_sources:
  - "https://figma.com/file/example?node-id=1-2"
figma_write_scope:
  mode: "duplicate"
  target: "AI Drafts / Wholesale Collection Start"
  approved_by: "human lead"
target_users:
  - "SmartStore operator"
design_intent: "Make the first collection step clear, low-risk, and operational."
ux_flow:
  - "Choose wholesale source"
  - "Inspect feasibility"
  - "Start draft collection"
screens:
  - name: "Collection start"
    purpose: "Start data source investigation"
    layout: "Header, source input, risk summary, start action"
    states:
      - "default"
      - "loading"
      - "error"
component_specs:
  - name: "Source input"
    anatomy: "label, URL input, helper text, validation message"
    variants:
      - "empty"
      - "valid"
      - "invalid"
responsive_rules:
  - "Mobile stacks fields vertically."
accessibility_notes:
  - "Input has visible label and validation text."
content_rules:
  - "Avoid promising scraping success before feasibility check."
implementation_constraints:
  - "Do not add new UI library."
visual_qa_checklist:
  - "Default/loading/error states captured on desktop and mobile."
open_decisions: []
human_approval_required: []
```

## Expected Behavior

- Check DESIGN_SPEC required fields.
- Check Figma write scope and approval.
- Check implementation readiness and screen/state coverage.
- Return `APPROVE` only if no blocking gaps exist.
