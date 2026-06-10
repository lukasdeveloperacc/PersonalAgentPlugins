# Fixture: Developer OMC Harness Routing

Use with:

```text
/developer-plugin:intake-task
```

or:

```text
/developer-plugin:omc-execute
```

## Prompt

TASK_SPEC says to implement SmartStoreToolkit's 상품 수집 시작 flow.

The work includes:

- `developer_report_path: docs/ai-handoffs/TASK_SPEC-001/DEVELOPER_REPORT.md`
- new UI screen and existing DESIGN_SPEC
- two backend validation modules
- one integration test suite
- browser verification against a local app
- acceptance criteria that must all be proven before handoff
- expected overnight execution if Claude continues autonomously

No production writes, no release, no Figma mutation.

## Expected Behavior

- Do not jump directly into code before intake.
- Confirm TASK_SPEC/DESIGN_SPEC readiness.
- Confirm `developer_report_path` and that the path is in `allowed_files` before long-running work.
- Select one primary loop authority:
  - direct only if the task is narrowed to one small PR slice
  - `/oh-my-claudecode:ralph` for single-owner complete-and-verify execution
  - `/oh-my-claudecode:team` for parallel UI/backend/test lanes
  - `/oh-my-claudecode:ultraqa` only for known failing quality gates
  - `omc ultragoal` when durable overnight/cross-session tracking is needed
- Use Chrome DevTools MCP for browser verification.
- Use `/oh-my-claudecode:ask codex` only as advisor evidence, not as the main implementation loop.
- Forbid unsupported shell commands such as `omc ralph`, `omc autopilot`, or `omc ultrawork`.
- Report an `OMC Harness Decision` with reason, execution status, and evidence.
- Create or update `docs/ai-handoffs/TASK_SPEC-001/DEVELOPER_REPORT.md` with harness decision, files changed, acceptance criteria evidence, verification evidence, blockers, and PM follow-up.
