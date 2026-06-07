# PersonalPlugins

개인 프로젝트를 위한 Codex, Claude Plugin들을 관리합니다.

## Goal

이 저장소는 AI Native 개발 흐름을 역할별로 분리합니다.

- Codex: PM, Reviewer
- Claude: Developer
- Human lead: final merge / release approval

v0.x는 skill-only 플러그인입니다. MCP, hooks, 자동 배포 권한은 포함하지 않습니다.

## Structure

```text
codex/
  .agents/plugins/marketplace.json
  plugins/pm-plugin/
    .codex-plugin/plugin.json
    skills/
  plugins/reviewer-plugin/
    .codex-plugin/plugin.json
    skills/
claude/
  .claude-plugin/marketplace.json
  plugins/developer-plugin/
    .claude-plugin/plugin.json
    skills/
docs/
test-fixtures/
```

## Codex Plugins

`pm-plugin` provides:

- `brainstorm`: run a discovery-first PM workshop, present a workflow decision gate, then produce PM/SDD/technical/TASK_SPEC/handoff bundles after confirmation.
- `brainstorm` may research current best practices first when upstream behavior or version-aware guidance matters.
- `task-spec`: create a scoped TASK_SPEC.

`reviewer-plugin` provides:

- `spec-review`: review PM workshop, PRD, SDD, RFC, and technical planning artifacts.
- `handoff-review`: review whether Claude can safely start long-running work from a handoff.
- `task-spec-review`: validate TASK_SPEC contract completeness before Developer work.
- `db-contract-review`: review DB/schema/RLS/migration/API contract readiness.
- `omx-branch-review`: review PM OMX harness branch selection and fallback quality.
- `pr-review`: review PRs and diffs.
- `architecture-review`: review boundaries and architecture risk.

Local marketplace root:

```sh
codex plugin marketplace add ./codex
codex plugin list
codex plugin add pm-plugin@personal-codex-tools
codex plugin add reviewer-plugin@personal-codex-tools
```

## Claude Plugin

`developer-plugin` provides:

- `implement-task`: implement from TASK_SPEC.
- `fix-bug`: reproduce, diagnose, patch, and verify bugs.
- `verify-app`: run checks and report evidence.
- `write-tests`: add scoped tests.

Local validation and marketplace setup:

```sh
claude plugin validate ./claude
claude plugin marketplace add ./claude
claude plugin install developer-plugin@personal-claude-tools
```

## Shared Contract

`docs/task-spec-contract.md` defines the shared TASK_SPEC schema. Installed plugins also carry plugin-local contract copies so skills can run after installation without reading repository-level docs.

Claude must not silently broaden TASK_SPEC scope. Codex Reviewer review is advisory. Only the human lead approves merge or release.
