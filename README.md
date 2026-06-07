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

- `brainstorm`: start the PM conversation for first-project onboarding, feature shaping, refactor discovery, bug themes, or docs/handoff planning; investigate first, present a workflow decision gate, then produce PM/SDD/technical/TASK_SPEC/handoff bundles after confirmation.
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

## PM Skill Examples

Use `pm-plugin:brainstorm` as the first PM conversation, not as a document generator. It should investigate the project, research external guidance when useful, choose an OMX harness, then ask you to confirm the workflow before producing final artifacts.

### First project kickoff

```text
$pm-plugin:brainstorm

SmartStoreToolkit에서 첫 PM 워크숍을 시작하자.
이 프로젝트의 목적, 사용자, 현재 README/docs/code 구조를 조사하고,
필요하면 외부 best practice도 확인하면서 구현 가능한 방향을 같이 잡아줘.
첫 산출물은 바로 만들지 말고 PROJECT_KICKOFF로 분류한 뒤
Discovery Dossier와 Workflow Decision Gate를 먼저 보여줘.
```

### Feature shaping

```text
$pm-plugin:brainstorm

도매사 상품 데이터를 수집해서 스마트스토어 운영자가 쓸 수 있는 기능을 만들고 싶어.
내가 말하는 도매사가 어떤 유형인지, 어떤 데이터 소스가 현실적인지,
법적/기술적 제약이 있는지 대화하면서 구현 초안을 잡아줘.
필요하면 best-practice-research나 deep-interview를 사용하고,
바로 TASK_SPEC로 가지 말고 먼저 FEATURE_SHAPING 워크플로우를 제안해줘.
```

### Refactor discovery

```text
$pm-plugin:brainstorm

현재 프로젝트의 크롤링/상품수집 쪽 구조가 복잡해지는 것 같아.
기능 동작은 유지하면서 어떤 리팩토링이 필요한지 같이 판단하고 싶어.
관련 파일과 문서를 조사한 뒤 REFACTOR_DISCOVERY로 분류하고,
ralplan이나 team이 필요한지 판단해서 workflow gate를 제안해줘.
```

### Bug theme investigation

```text
$pm-plugin:brainstorm

상품 수집 결과가 자주 불안정하고 원인이 한 가지가 아닌 것 같아.
증상과 재현 조건, 데이터 소스 문제, 파싱 문제, 네트워크 문제를 분리해서
BUG_THEME 관점으로 조사 계획과 구현 전 확인할 질문을 만들어줘.
```

### PM to Reviewer to Developer flow

```text
$pm-plugin:brainstorm
-> reviewer-plugin:spec-review
-> pm-plugin:task-spec
-> reviewer-plugin:task-spec-review
-> reviewer-plugin:handoff-review
-> Claude developer-plugin:implement-task
```

For data or DB changes, add:

```text
-> reviewer-plugin:db-contract-review
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
