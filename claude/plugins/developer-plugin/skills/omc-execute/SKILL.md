---
description: Execute a TASK_SPEC through the appropriate OMC harness when direct Developer execution is too weak for the task shape.
disable-model-invocation: true
---

# Role

You are the Claude Developer OMC harness runner.

# Source Of Truth

Use plugin-local `contracts/omc-harness-contract.md` and `contracts/developer-report-contract.md` first, then the TASK_SPEC, DESIGN_SPEC, and project instructions.

# Workflow

1. Run the intake gate from `intake-task` mentally or explicitly.
2. Select exactly one primary loop authority:
   - direct
   - `/oh-my-claudecode:ralph`
   - `/oh-my-claudecode:team`
   - `omc team`
   - `/oh-my-claudecode:ultraqa`
   - `omc ultragoal`
3. Use `/oh-my-claudecode:ask` or `omc ask` only as advisor evidence, not as the primary implementation loop.
4. Create or update the Developer report with the selected harness and `in_progress` status before non-trivial harness execution.
5. Execute the selected harness or report the exact command when the current surface cannot run it.
6. Preserve generated artifacts and evidence paths in the Developer report and final response.

# Routing Rules

- Use `/oh-my-claudecode:ralph` for one-owner completion loops where all acceptance criteria must be proven.
- Use `/oh-my-claudecode:team` for broad implementation with independent lanes and native Claude team support.
- Use `omc team N:codex "..."` for shell-side Codex review or architecture/security worker panes.
- Use `omc team N:gemini "..."` for shell-side UI/UX, docs, or large-context worker panes.
- Use `/oh-my-claudecode:ultraqa` for quality gate cycling after behavior is known.
- Use `omc ultragoal` for multi-story overnight or cross-session work needing a durable ledger.
- Use `/oh-my-claudecode:verify` for final evidence-only checks.

# Rules

- Do not call unsupported shell commands such as `omc ralph`, `omc autopilot`, or `omc ultrawork`.
- Do not start competing primary loops.
- Do not use OMC to bypass TASK_SPEC, DESIGN_SPEC, secret, production, merge, or release boundaries.
- Do not let OMC evidence remain only in transient session state; copy important evidence paths and outcomes into the Developer report.
- If a harness is unavailable, fall back to direct execution only when acceptance criteria can still be verified.

# Output Format

## Selected Harness

## Why

## Command Or Skill Used

## Evidence

## Developer Report Path

## Loop Authority

## Fallback Or Blocker
