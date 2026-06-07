# PersonalPlugins

개인 프로젝트를 위한 Codex, Claude Plugin들을 관리합니다.

## Goal

이 저장소는 AI Native 개발 흐름을 역할별로 분리합니다.

- Codex: PM, Reviewer
- Claude: Developer
- Human lead: final merge / release approval

v0.1은 skill-only 플러그인입니다. MCP, hooks, 자동 배포 권한은 포함하지 않습니다.

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

- `task-spec`: create a scoped TASK_SPEC.

`reviewer-plugin` provides:

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

`docs/task-spec-contract.md` defines the TASK_SPEC schema that Codex PM produces and Claude consumes.

Claude must not silently broaden TASK_SPEC scope. Codex Reviewer review is advisory. Only the human lead approves merge or release.
