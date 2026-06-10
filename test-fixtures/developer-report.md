# Fixture: Developer Report

Use with:

```text
/developer-plugin:report-result
```

## Prompt

TASK_SPEC says:

```yaml
task_id: "TASK_SPEC-001"
task_spec: "docs/tasks/TASK_SPEC-001.md"
design_spec: "docs/design/DESIGN_SPEC-collection-start.md"
developer_report_path: "docs/ai-handoffs/TASK_SPEC-001/DEVELOPER_REPORT.md"
allowed_files:
  - "src/collection/**"
  - "tests/collection/**"
  - "docs/ai-handoffs/TASK_SPEC-001/DEVELOPER_REPORT.md"
```

Developer result:

- primary harness: `/oh-my-claudecode:ralph`
- status: partial
- changed files: `src/collection/source-intake.ts`, `tests/collection/source-intake.test.ts`
- verification: targeted unit test passed, browser evidence not captured
- blocker: local app does not boot because an unrelated dependency install is missing
- PM follow-up: decide whether browser verification can move to a follow-up TASK_SPEC or must block PR review

## Expected Behavior

- Create or update `docs/ai-handoffs/TASK_SPEC-001/DEVELOPER_REPORT.md`.
- Use `developer_status: "partial"`.
- Preserve the TASK_SPEC and DESIGN_SPEC as source of truth.
- Mark browser evidence as not captured instead of claiming completion.
- Record PM follow-up needed.
- Do not approve merge or release.
