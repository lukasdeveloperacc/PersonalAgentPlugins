# Release Checklist

## Schema Gate

- Verify current official Codex plugin manifest and marketplace schema.
- Verify current official Claude plugin manifest and marketplace schema.
- Record schema evidence before publishing.
- Update manifests if official schemas differ from this repository.

## Local Validation

- Parse every JSON manifest.
- Validate Codex plugin with the Codex plugin validator when available.
- Validate Claude plugin or marketplace with `claude plugin validate`.
- Confirm every required skill file exists.
- Confirm every skill has role, workflow, rules, and output format.

## Smoke Tests

- Run Codex PM `task-spec` on `test-fixtures/sample-feature-request.md`.
- Feed the generated TASK_SPEC shape to Claude `implement-task`.
- Run Codex Reviewer `pr-review` on `test-fixtures/sample-pr-diff.md`.
- Run Claude `fix-bug` on `test-fixtures/sample-bug-report.md`.

## Publishing

- Tag releases after local validation.
- Keep v0.1 skill-only.
- Add MCP, hooks, or automation only in later versions with a separate review.
