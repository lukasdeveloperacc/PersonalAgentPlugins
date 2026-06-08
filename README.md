# PersonalPlugins

개인 프로젝트를 위한 Codex, Claude Plugin들을 관리합니다.

## Goal

이 저장소는 AI Native 개발 흐름을 역할별로 분리합니다.

- Codex: PM, Reviewer
- Claude: Designer, Developer
- Human lead: final merge / release approval

v0.x is still conservative: PM and Developer include Chrome DevTools MCP for read-only site/runtime investigation, while hooks and automatic deployment/write automation are not included.

## Structure

```text
codex/
  .agents/plugins/marketplace.json
  plugins/pm-plugin/
    .codex-plugin/plugin.json
    .mcp.json
    contracts/
    skills/
  plugins/reviewer-plugin/
    .codex-plugin/plugin.json
    .mcp.json
    contracts/
    skills/
claude/
  .claude-plugin/marketplace.json
  plugins/developer-plugin/
    .claude-plugin/plugin.json
    .mcp.json
    contracts/
    skills/
  plugins/designer-plugin/
    .claude-plugin/plugin.json
    .mcp.json
    contracts/
    skills/
docs/
test-fixtures/
```

## Codex Plugins

`pm-plugin` provides:

- `brainstorm`: start the PM conversation for first-project onboarding, feature shaping, refactor discovery, bug themes, or docs/handoff planning; investigate first, present a workflow decision gate, then produce PM/SDD/technical/TASK_SPEC/handoff bundles after confirmation.
- `brainstorm` may research current best practices first when upstream behavior or version-aware guidance matters.
- `brainstorm` can inspect user-provided sites with Chrome DevTools MCP for public read-only feasibility evidence.
- `task-spec`: create a scoped TASK_SPEC.

`reviewer-plugin` provides:

- `spec-review`: review PM workshop, PRD, SDD, RFC, and technical planning artifacts.
- `design-review`: review DESIGN_SPEC, SCREEN_SPEC, UX flow, component specs, Figma write scope, and visual QA brief before Developer handoff.
- `visual-qa-review`: review implemented UI against approved DESIGN_SPEC, Figma sources, screenshots, and viewport evidence.
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

`reviewer-plugin` includes Figma MCP for read/review evidence:

```json
{
  "mcpServers": {
    "figma": {
      "url": "http://127.0.0.1:3845/mcp"
    }
  }
}
```

Codex Reviewer uses this to inspect approved Figma sources during `design-review` and `visual-qa-review`. It must not mutate Figma; Figma writes belong to Claude Designer under approved write scope.

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

### Site feasibility discovery

```text
$pm-plugin:brainstorm

이 도매사 사이트를 보고 상품 데이터 수집 기능이 현실적으로 가능한지 판단해줘:
https://example-wholesale-site.test

Chrome DevTools MCP로 공개 페이지 구조, 네트워크 요청, 콘솔 에러,
로그인 필요 여부, 데이터 필드, 약관/자동화 리스크를 조사해줘.
로그인 세션이나 폼 제출이 필요하면 먼저 나에게 승인받고,
바로 구현하지 말고 USER_PROVIDED_SITE Discovery Dossier와 Workflow Decision Gate를 먼저 보여줘.
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

### PM to Designer to Reviewer to Developer flow

```text
$pm-plugin:brainstorm
-> Claude designer-plugin:design-intent
-> Claude designer-plugin:screen-spec
-> Claude designer-plugin:figma-draft when approved Figma draft writes are needed
-> reviewer-plugin:design-review
-> reviewer-plugin:spec-review
-> pm-plugin:task-spec
-> reviewer-plugin:task-spec-review
-> reviewer-plugin:handoff-review
-> Claude developer-plugin:implement-task
-> reviewer-plugin:visual-qa-review
```

For data or DB changes, add:

```text
-> reviewer-plugin:db-contract-review
```

### PM detects UI/UX work

```text
$pm-plugin:brainstorm

SmartStoreToolkit의 상품 수집 시작 화면을 새로 만들고 싶어.
사용자는 스마트스토어 운영자이고, 도매사 URL을 입력하면 수집 가능성 점검을 시작하는 화면이야.

이건 UI/UX 품질이 중요하니까 바로 TASK_SPEC로 가지 말고
DESIGN_REQUIRED 여부를 판단해줘.
필요하면 Claude Designer의 design-intent, screen-spec, figma-draft,
Codex design-review, visual-qa-review를 포함한 workflow gate를 먼저 제안해줘.
```

## Claude Plugin

`developer-plugin` provides:

- `intake-task`: check TASK_SPEC, DESIGN_SPEC, scope, testability, and OMC harness readiness before implementation.
- `implement-task`: implement from TASK_SPEC with direct or OMC harness routing.
- `omc-execute`: choose and run the right OMC harness for long-running or high-risk Developer work.
- `resume-task`: resume interrupted work from git state, OMC state, Ultragoal ledger, and prior evidence.
- `browser-debug`: inspect browser/runtime behavior with Chrome DevTools MCP and optional visual verdict.
- `fix-bug`: reproduce, diagnose, patch, and verify bugs.
- `verify-app`: run checks and report evidence.
- `write-tests`: add scoped tests.

Developer includes Chrome DevTools MCP for local/app runtime inspection:

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest"]
    }
  }
}
```

Developer does not mutate Figma. DESIGN_SPEC remains the design source of truth; Figma writes stay with Designer.

## Developer OMC Harness Examples

Use Developer after PM/Reviewer gates pass. The Developer plugin now selects OMC harnesses by task shape instead of blindly implementing.

### Intake before overnight work

```text
/developer-plugin:intake-task

TASK_SPEC: docs/tasks/TASK_SPEC-001.md
DESIGN_SPEC: docs/design/DESIGN_SPEC-collection-start.md

이 작업이 Claude가 오래 실행해도 되는 상태인지 확인해줘.
TASK_SPEC 누락, DESIGN_SPEC 누락, allowed/blocked files, acceptance criteria,
test plan, OMC harness 추천까지 판단해줘.
```

### Execute with OMC routing

```text
/developer-plugin:omc-execute

TASK_SPEC를 기준으로 구현하되,
작업이 작으면 direct로 진행하고,
완료 보장이 필요하면 /oh-my-claudecode:ralph,
병렬 작업이면 /oh-my-claudecode:team,
테스트/빌드 실패 반복이면 /oh-my-claudecode:ultraqa,
장기/재개 가능 작업이면 omc ultragoal을 선택해줘.
```

### Browser debugging

```text
/developer-plugin:browser-debug

로컬 앱에서 상품 수집 시작 화면을 열고
Chrome DevTools MCP로 console/network/DOM/screenshot 증거를 확인해줘.
DESIGN_SPEC와 다르면 visual-verdict가 필요한지 판단해줘.
```

### Resume interrupted work

```text
/developer-plugin:resume-task

이전 Claude 작업이 중간에 끊겼어.
git status, 변경 파일, .omc/ultragoal, .omc/state를 보고
어디서부터 이어가야 하는지 판단한 뒤 다음 acceptance criterion부터 진행해줘.
```

`designer-plugin` provides:

- `design-intent`: turn user intent and PM context into UI/UX design direction.
- `screen-spec`: create DESIGN_SPEC, SCREEN_SPEC, UX flow, screen states, responsive rules, and visual QA checklist.
- `figma-draft`: inspect Figma and create/modify approved draft Figma material through the local Figma MCP server.
- `component-spec`: define component anatomy, variants, states, token usage, and implementation notes.
- `visual-qa-brief`: prepare visual QA expectations for Codex review and Developer verification.

The Designer plugin includes plugin-local Figma MCP config:

```json
{
  "mcpServers": {
    "figma": {
      "type": "http",
      "url": "http://127.0.0.1:3845/mcp"
    }
  }
}
```

This requires the Figma desktop Dev Mode MCP server to be enabled. Figma writes are allowed only for explicitly approved draft, duplicate, branch, sandbox, or approved official targets. Markdown `DESIGN_SPEC` remains the handoff source of truth.

## Designer Skill Examples

Use Claude Designer when UI/UX quality materially affects the task. The normal handoff source of truth is:

```text
PM artifacts + TASK_SPEC candidate
-> Claude DESIGN_SPEC
-> Codex design-review
-> Claude Developer implementation
-> Codex visual-qa-review
```

### Design from user intent

```text
/designer-plugin:design-intent

SmartStoreToolkit의 첫 상품 수집 화면을 설계하고 싶어.
사용자는 스마트스토어 운영자이고, 도매사 URL이나 상품 소스를 넣으면
수집 가능성을 점검하고 안전하게 다음 단계로 넘어가는 흐름이 필요해.

PM 산출물과 기존 README/docs를 참고해서
사용자 의도, UX 원칙, 화면 방향, 열려 있는 디자인 결정을 정리해줘.
Figma 수정은 아직 하지 말고 디자인 방향만 먼저 잡아줘.
```

### Create a screen spec

```text
/designer-plugin:screen-spec

위 design-intent를 바탕으로 Claude Developer가 구현할 수 있는
DESIGN_SPEC, SCREEN_SPEC, UX_FLOW, COMPONENT_SPEC 초안을 만들어줘.

반드시 default/loading/empty/error/disabled 상태,
desktop/mobile responsive rule,
accessibility note,
visual QA checklist를 포함해줘.
```

### Draft in Figma

```text
/designer-plugin:figma-draft

Figma desktop Dev Mode MCP server는 켜져 있고 endpoint는:
http://127.0.0.1:3845/mcp

Target:
- File: SmartStoreToolkit draft duplicate
- Page: AI Drafts
- Frame: Wholesale Collection Start
- Write mode: duplicate
- Approval: 이 duplicate file은 draft write를 승인함

DESIGN_SPEC 기준으로 Figma draft frame을 생성/수정하고,
변경한 Figma object 요약과 업데이트된 DESIGN_SPEC,
visual QA checklist를 함께 남겨줘.

공식 design system component/token/published library는 수정하지 마.
삭제 작업도 하지 마.
```

### Review the design before implementation

```text
$reviewer-plugin:design-review

Claude Designer가 만든 DESIGN_SPEC와 Figma draft를 검토해줘.
Figma MCP로 승인된 Figma source를 조회할 수 있으면 직접 확인하고,
PM intent, Figma write scope, screen states, responsive rules,
implementation readiness, visual QA checklist를 기준으로 판단해줘.

Reviewer는 Figma를 수정하지 말고 read/review만 해.
```

### Implement after design approval

```text
/developer-plugin:implement-task

이 작업은 UI/UX가 중요하므로 TASK_SPEC와 승인된 DESIGN_SPEC를 둘 다 source of truth로 봐줘.
TASK_SPEC 범위 안에서만 구현하고, DESIGN_SPEC의 화면 상태와 responsive rule을 보존해줘.
Figma는 Developer 역할에서 수정하지 마.
구현 후 visual QA에 필요한 screenshot/viewport evidence를 남겨줘.
```

### Review visual QA after implementation

```text
$reviewer-plugin:visual-qa-review

구현 결과를 승인된 DESIGN_SPEC, Figma source, screenshot/viewport evidence와 비교해줘.
layout, spacing, hierarchy, typography, state coverage, responsive behavior를 확인하고
PR review로 넘어가도 되는지 판단해줘.

Reviewer는 Figma를 수정하지 말고 read/review만 해.
```

Local validation and marketplace setup:

```sh
claude plugin validate ./claude
claude plugin marketplace add ./claude
claude plugin install developer-plugin@personal-claude-tools
claude plugin install designer-plugin@personal-claude-tools
```

## Shared Contract

`docs/task-spec-contract.md` defines the shared TASK_SPEC schema. `docs/design-spec-contract.md` defines the DESIGN_SPEC schema for Claude Designer, Codex Reviewer, and Claude Developer. Installed plugins also carry plugin-local contract copies so skills can run after installation without reading repository-level docs.

Claude must not silently broaden TASK_SPEC scope. Codex Reviewer review is advisory. Only the human lead approves merge or release.

## Runtime Docs

Installed plugin agents should rely on plugin-local runtime docs:

- PM: `codex/plugins/pm-plugin/contracts/`
- Reviewer: `codex/plugins/reviewer-plugin/contracts/`
- Claude Developer: `claude/plugins/developer-plugin/contracts/`
- Claude Designer: `claude/plugins/designer-plugin/contracts/`

Root `docs/` files are maintainer-facing mirrors and release/security/workflow notes for this repository. If a skill must read a document after installation, put that document inside the plugin package and reference the plugin-local path from `SKILL.md`.
