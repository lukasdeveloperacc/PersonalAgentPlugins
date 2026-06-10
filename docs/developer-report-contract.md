# Developer Report Contract

`DEVELOPER_REPORT.md` is the durable status bridge from Claude Developer back to Codex PM and Codex Reviewer.

The report must live in the repository so PM can inspect it later without relying on chat history, Claude session state, or transient OMC logs.

## Default Path

Use this path unless the TASK_SPEC explicitly provides another one:

```text
docs/ai-handoffs/<task_id>/DEVELOPER_REPORT.md
```

The PM TASK_SPEC should include this path in `allowed_files` so Claude Developer can update it during implementation.

## Status Values

Use one:

- `not_started`
- `in_progress`
- `completed`
- `blocked`
- `partial`
- `failed`

## Required Front Matter

```yaml
task_id: ""
task_spec: ""
design_spec: ""
developer_status: "not_started|in_progress|completed|blocked|partial|failed"
primary_harness: "direct|ralph|team|omc-team|ultraqa|verify|visual-verdict|ultragoal|ask|blocked"
branch: ""
commit: ""
pr: ""
updated_at: "YYYY-MM-DDTHH:MM:SSZ"
```

## Required Sections

```markdown
# Developer Report: <task_id>

## Summary

## Source Of Truth

## Scope Executed

## Files Changed

## Acceptance Criteria Evidence

| Criterion | Status | Evidence |
| --- | --- | --- |

## Verification Evidence

## Browser / Visual Evidence

## OMC Harness Evidence

## Deviations From TASK_SPEC

## Blockers

## Residual Risk

## PM Follow-up Needed

## Reviewer Notes
```

## Developer Responsibilities

Claude Developer must:

- Create or update the report at intake/start with `in_progress` for non-trivial work.
- Update the report before final response, even when blocked or partially complete.
- Map every acceptance criterion to pass/fail/untested evidence.
- Link command output, screenshots, OMC artifacts, PRs, or commits when available.
- Record scope deviations and PM decisions needed instead of hiding them in chat.

## PM Responsibilities

Codex PM must:

- Include the report path in TASK_SPEC handoff material.
- Treat the report as PM-visible implementation state.
- Use `pm-sync` to detect missing reports, stale status, missing evidence, or report/TASK_SPEC drift.

## Boundary

The report is evidence, not approval. Human lead still owns final merge/release decisions. Codex Reviewer still owns review recommendations.
