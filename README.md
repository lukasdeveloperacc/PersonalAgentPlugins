# PersonalPlugins

개인 프로젝트를 위한 Claude Plugin과 Codex companion Plugin들을 관리합니다.

현재 이 저장소는 Claude Code 플러그인 **cmux-agent-harness-loop-plugin**과 Codex companion plugin **socrates-codex-partner-plugin**을 제공합니다.

## Goal

특정 프레임워크·앱·도메인에 종속되지 않는, **cmux pane 기반의 지속형 멀티 에이전트 하니스 루프**를 일반 소프트웨어 개발에 적용할 수 있게 한다.

- Orchestrator: Claude / OMC (파일 수정 가능)
- Reviewer / PM: OMX / Codex (지속형 pane, 기본적으로 소스 수정 금지, STOP/GO 판단)
- Socrates: 아이디어를 사용자가 Codex/PM과 함께 토론·인터뷰하며 기획문서로 정제하는 pre-planning workflow
- Harness loop의 에이전트 호출과 Socrates의 Codex 파트너 호출은 **cmux pane**을 통해서만 수행한다 (`/ask`, `omc ask`, `omx ask` 계열 금지)
- 공유 메모리는 대상 프로젝트의 `docs/changes/*.md`로 관리한다

## Structure

```text
claude/
  .claude-plugin/marketplace.json
  plugins/cmux-agent-harness-loop-plugin/
    .claude-plugin/plugin.json
    .mcp.json
    agents/document-specialist.md
    contracts/
    skills/cmux-agent-harness-loop/SKILL.md
    skills/socrates/SKILL.md
    templates/
codex/
  .agents/plugins/marketplace.json
  plugins/socrates-codex-partner-plugin/
    .codex-plugin/plugin.json
    contracts/
    skills/socrates-partner/SKILL.md
    skills/socrates-document-specialist/SKILL.md
    skills/harness-reviewer/SKILL.md
docs/
test-fixtures/
```

## cmux-agent-harness-loop-plugin

두 개의 스킬이 동작합니다. 플러그인 설치 시 Claude Code의 portable invocation은 namespaced 형태입니다.

- `/cmux-agent-harness-loop-plugin:cmux-agent-harness-loop` — 구현/리뷰 하니스 루프
- `/cmux-agent-harness-loop-plugin:socrates` — 아이디어→인터뷰/토론→Codex reflection→기획문서 산출 워크숍

`cmux-agent-harness-loop`는 서브커맨드로 동작합니다.

- `setup`: cmux 내부 실행 여부 확인, runtime(cmux/claude/omc/omx/codex) 탐색, 대상 프로젝트에 `.agent-harness/` + `docs/changes/` 스캐폴딩.
- `status`: runtime 가용성, reviewer pane 생존, 마지막 loop 시각, 미해결 TODO 수를 읽기 전용으로 보고.
- `plan "<요청>"`: INTAKE 단계만 수행하여 `TASK_SPEC.md` 작성 (pane 불필요, 실행 없음).
- `review`: reviewer pane을 확보하고 컨텍스트를 주입한 뒤 cmux send로 interactive OMX/Codex pane에 프롬프트를 주입하고, read-screen sentinel + verdict 파일로 결과를 수집하여 ACCEPT/REJECT/NEEDS_CHECK/DEFER 판단.
- `loop "<요청>"`: 5개 관찰 가능 상태(INTAKE→EXECUTE→REVIEW→DECIDE→HANDOFF)를 `state.json.stage` 커서로 구동하는 thin driver. 수렴 조건 / `max_loops` / no-progress 종료 가드 포함.
- `handoff`: 현재 상태로 `HANDOFF.md` 작성, STOP/GO를 `cmux notify`로 알림.

### Socrates pre-planning workflow

`/cmux-agent-harness-loop-plugin:socrates`는 영상형 `/socrates` 경험을 목표로 합니다.

1. 아이디어를 입력받습니다.
2. 진행방식 선택: `인터뷰모드` / `토론모드` / `질문최소로 빠르게`.
3. 경험수준 선택: `거의처음` / `튜토리얼 정도` / `혼자 만들 수 있음` / `실무개발자`.
4. Claude가 사용자를 인터뷰하고, Codex/OMX 파트너 pane이 문제·타겟·기능·차별화·OUT 목록을 비판합니다.
5. 토론모드에서는 `이대로 진행`, `문제/타겟 다시 잡기`, `기능/차별화 다시 잡기`, `OUT 목록 조정`, `질문 더 받기` 메뉴로 되돌아갈 수 있습니다.
6. 마지막에는 plugin-shipped `document-specialist` agent가 기본 기획문서와 Ralplan-ready handoff bundle을 작성합니다.
7. 질문, 선택지, Codex 요약, 최종 기획문서 산출물은 한국어를 기본값으로 사용합니다.

기본 기획문서:

- `docs/changes/SOCRATES_BRIEF.md`
- `docs/changes/PRD.md`
- `docs/changes/OUT_OF_SCOPE.md`
- `docs/changes/HANDOFF.md`

Ralplan-ready handoff bundle:

- `docs/changes/RALPLAN_BRIEF.md`
- `docs/changes/INTERVIEW_EVIDENCE.md`
- `docs/changes/RALPLAN_DR_SEED.md`
- `docs/changes/ULTRAGOAL_DRAFT.md` — Claude `/ultragoal` prompt draft only; 자동 실행 아님.
- `docs/changes/ROLE_PANE_MAP.md`
- `docs/changes/MCP_READINESS_CHECKLIST.md`

영상처럼 bare `/socrates`를 원하면 target project에 `templates/project-commands/socrates.md.tmpl`를 `.claude/commands/socrates.md`로 복사해 alias로 사용할 수 있습니다. 플러그인 배포형 기본 명령은 namespace 충돌 방지를 위해 `/cmux-agent-harness-loop-plugin:socrates`입니다.

### Transport (cmux-only, both-channels)

모든 review는 세 가지를 모두 사용합니다.

1. `cmux send` — 이미 실행 중인 interactive OMX/Codex pane에 프롬프트를 직접 주입합니다.
2. `cmux read-screen` — pane 생존과 종료 sentinel(`<<<HARNESS_VERDICT_DONE id=...>>>`)을 관찰.
3. 구조화된 verdict 파일(`docs/changes/REVIEW_<loop>_<attempt>.md`) — 결정의 권위 있는 파싱 소스. orchestrator는 `.done` 마커가 존재할 때만 파싱합니다.

기본 transport는 `omx`/`codex`를 pane 안에 켜둔 뒤 `cmux send`/buffer paste로 대화하는 방식입니다. `cmux omx exec`, `omx exec`, `codex exec`, `codex exec review` 같은 비대화형 exec는 지속 대화를 우회하므로 기본 금지입니다.

### 템플릿 해석

스킬은 `${CLAUDE_PLUGIN_ROOT}` → marketplace cache → skill-dir → **SKILL.md 내부 인라인 heredoc(항상 동작)** 순으로 템플릿 소스를 해석합니다. 인라인 heredoc이 정본이며 `templates/`는 byte-identical mirror입니다(릴리스 게이트에서 diff 검증).


## Codex companion plugin

Claude의 `/socrates`가 Codex/OMX pane을 단순 조언자가 아니라 같은 계약을 아는 파트너로 쓰도록, Codex 쪽 companion plugin도 함께 제공합니다.

- `socrates-partner`: 아이디어를 PM/비판자 관점에서 한국어로 점검하고 다음 질문을 제안.
- `socrates-document-specialist`: Socrates transcript를 한국어 PRD/브리프/HANDOFF와 Ralplan-ready bundle로 작성.
- `harness-reviewer`: 구현 루프에서 `REVIEW_<loop>_<attempt>.md` + `.done` + sentinel 계약을 지키는 리뷰어.
- `socrates-pm`, `idea-reviewer`, `design-reviewer`, `code-reviewer`, `ai-researcher`, `surfer-researcher`, `ralplan-partner`: Codex PM/Reviewer/Researcher lane profile.

각 Codex 역할은 `SKILL.md` entrypoint와 `agents/openai.yaml` agent profile을 함께 제공합니다. 현재 Codex plugin에서 검증 가능한 agent 배포 표면은 이 skill+agent-profile 쌍입니다.

설치:

```sh
codex plugin marketplace add ./codex
codex plugin add socrates-codex-partner-plugin@personal-agent-plugins-codex
```

자세한 내용은 `docs/codex-companion-plugin.md`를 참고하세요.

## Local validation and marketplace setup

```sh
claude plugin validate ./claude
claude plugin marketplace add ./claude
claude plugin install cmux-agent-harness-loop-plugin@personal-claude-tools

python3 /Users/chaejin/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py codex/plugins/socrates-codex-partner-plugin
python3 codex/plugins/socrates-codex-partner-plugin/tests/test_static.py
```

## Shared Contracts

플러그인 런타임 계약은 플러그인 로컬 `contracts/`에 둡니다.

- `contracts/cmux-transport-contract.md`: 검증된 cmux CLI 표면 + cmux-only + both-channels 규칙.
- `contracts/harness-loop-contract.md`: 5개 관찰 가능 상태 + 13-state 내러티브 + 종료 스펙.
- `contracts/review-verdict.md`: GO|STOP|NEEDS_CHECK enum + sentinel + atomic ordering 계약.
- `contracts/safety-contract.md`: ask-family 금지 범위, 위험 플래그, redaction, negative test.
- `contracts/socrates-workshop-contract.md`: `/socrates`식 아이디어 워크숍, Codex reflection, document-specialist 산출물 계약.

루트 `docs/`는 유지보수자용 미러이며 릴리스 노트입니다. 설치 후 스킬이 읽어야 하는 문서는 플러그인 패키지 안에 두고 `SKILL.md`에서 플러그인 로컬 경로를 참조합니다.

`.agent-harness/`와 `docs/changes/`는 **대상 프로젝트의 런타임 산출물**이며 이 플러그인 저장소에 커밋하지 않습니다. 대상 프로젝트의 `.gitignore`에 `.agent-harness/`를 추가하세요.

Reviewer 결과는 advisory이며 Claude orchestrator가 최종 판단합니다. merge/release 승인은 사람만 합니다.
