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
- Run Codex PM `brainstorm` on `test-fixtures/pm-workshop-standard.md`.
- Run Codex PM `brainstorm` on `test-fixtures/pm-workshop-full-epic.md`.
- Run Codex PM `brainstorm` on `test-fixtures/pm-workshop-db-schema.md`.
- Confirm `brainstorm` can switch into research-first mode when current best practices or upstream behavior matter.
- Confirm `brainstorm` emits `Discovery Dossier` before final artifact generation.
- Confirm `brainstorm` emits `Workflow Decision Gate` and asks for human confirmation before final PRD/SDD/RFC/TASK_SPEC/handoff artifacts on ambiguous or long-running work.
- Confirm `brainstorm` emits `OMX Harness Decision` and executes or falls back according to the fixture branch.
- Run Codex PM `backlog-groom` on `test-fixtures/pm-workshop-backlog.md`.
- Run Codex PM `pm-sync` on `test-fixtures/pm-workshop-sync-drift.md`.
- Run Codex Reviewer `spec-review` on a PM full-bundle artifact.
- Run Codex Reviewer `handoff-review` on a Claude handoff draft.
- Run Codex Reviewer `task-spec-review` on a generated TASK_SPEC.
- Run Codex Reviewer `db-contract-review` on a data-impact planning artifact.
- Run Codex Reviewer `omx-branch-review` on a PM harness decision section.
- Feed the generated TASK_SPEC shape to Claude `implement-task`.
- Run Codex Reviewer `pr-review` on `test-fixtures/sample-pr-diff.md`.
- Run Claude `fix-bug` on `test-fixtures/sample-bug-report.md`.

## Publishing

- Tag releases after local validation.
- Keep v0.1 skill-only.
- Add MCP, hooks, or automation only in later versions with a separate review.
