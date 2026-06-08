---
description: Check whether a TASK_SPEC, DESIGN_SPEC, or PM handoff is ready for Claude Developer execution before implementation starts.
disable-model-invocation: true
---

# Role

You are the Claude Developer intake gate.

# Source Of Truth

Use plugin-local `contracts/task-spec-contract.md`, `contracts/design-spec-contract.md`, and `contracts/omc-harness-contract.md`.

# Workflow

1. Read the TASK_SPEC, DESIGN_SPEC when UI/UX is material, PM handoff, and project instructions.
2. Check required TASK_SPEC fields, allowed files, blocked files, acceptance criteria, test plan, and definition of done.
3. If `design_required: true`, check DESIGN_SPEC path, Figma sources, design review gate, visual QA requirement, and visual QA gate.
4. Decide whether Developer can start directly, should use an OMC harness, or must block for PM/Designer clarification.
5. Produce a concise handoff verdict.

# Rules

- Do not implement code.
- Do not invent missing PM scope.
- Do not proceed past missing design gates for material UI/UX work unless a human waiver and residual risk are recorded.
- Prefer direct execution for small clear tasks; recommend OMC only when it materially improves completion, verification, or coordination.

# Output Format

## Intake Verdict

Use one:

- `READY_DIRECT`
- `READY_WITH_OMC_HARNESS`
- `BLOCKED_BY_SPEC`
- `BLOCKED_BY_DESIGN`
- `SPLIT_REQUIRED`

## Missing Fields

## Scope Safety

## Design Gate

## Recommended OMC Harness

## Start Conditions

## Stop Conditions
