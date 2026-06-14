# PersonalPlugins

개인 프로젝트를 위한 Claude Plugin들을 관리합니다.

현재 이 저장소는 하나의 Claude Code 플러그인을 제공합니다: **cmux-agent-harness-loop**.

## Goal

특정 프레임워크·앱·도메인에 종속되지 않는, **cmux pane 기반의 지속형 멀티 에이전트 하니스 루프**를 일반 소프트웨어 개발에 적용할 수 있게 한다.

- Orchestrator: Claude / OMC (파일 수정 가능)
- Reviewer / PM: OMX / Codex (지속형 pane, 기본적으로 소스 수정 금지, STOP/GO 판단)
- 모든 에이전트 호출은 **cmux pane**을 통해서만 수행한다 (`/ask`, `omc ask`, `omx ask` 계열 금지)
- 공유 메모리는 대상 프로젝트의 `docs/changes/*.md`로 관리한다

## Structure

```text
claude/
  .claude-plugin/marketplace.json
  plugins/cmux-agent-harness-loop-plugin/
    .claude-plugin/plugin.json
    .mcp.json
    contracts/
    skills/cmux-agent-harness-loop/SKILL.md
    templates/
docs/
test-fixtures/
```

## cmux-agent-harness-loop-plugin

하나의 스킬 `cmux-agent-harness-loop`가 서브커맨드로 동작합니다.

- `setup`: cmux 내부 실행 여부 확인, runtime(cmux/claude/omc/omx/codex) 탐색, 대상 프로젝트에 `.agent-harness/` + `docs/changes/` 스캐폴딩.
- `status`: runtime 가용성, reviewer pane 생존, 마지막 loop 시각, 미해결 TODO 수를 읽기 전용으로 보고.
- `plan "<요청>"`: INTAKE 단계만 수행하여 `TASK_SPEC.md` 작성 (pane 불필요, 실행 없음).
- `review`: reviewer pane을 확보하고 컨텍스트를 주입한 뒤 cmux send로 비대화형 exec를 실행하고, read-screen sentinel + verdict 파일로 결과를 수집하여 ACCEPT/REJECT/NEEDS_CHECK/DEFER 판단.
- `loop "<요청>"`: 5개 관찰 가능 상태(INTAKE→EXECUTE→REVIEW→DECIDE→HANDOFF)를 `state.json.stage` 커서로 구동하는 thin driver. 수렴 조건 / `max_loops` / no-progress 종료 가드 포함.
- `handoff`: 현재 상태로 `HANDOFF.md` 작성, STOP/GO를 `cmux notify`로 알림.

### Transport (cmux-only, both-channels)

모든 review는 세 가지를 모두 사용합니다.

1. `cmux send` — reviewer pane 안에서 비대화형 exec(`codex exec review` 또는 `cmux omx exec`)를 실행.
2. `cmux read-screen` — pane 생존과 종료 sentinel(`<<<HARNESS_VERDICT_DONE id=...>>>`)을 관찰.
3. 구조화된 verdict 파일(`docs/changes/REVIEW_<loop>_<attempt>.md`) — 결정의 권위 있는 파싱 소스. orchestrator는 `.done` 마커가 존재할 때만 파싱합니다.

`cmux omx exec` / `cmux omc`는 금지된 one-shot advisor(`omx ask` 등)가 아니라 in-pane orchestration이며 명시적으로 허용됩니다.

### 템플릿 해석

스킬은 `${CLAUDE_PLUGIN_ROOT}` → marketplace cache → skill-dir → **SKILL.md 내부 인라인 heredoc(항상 동작)** 순으로 템플릿 소스를 해석합니다. 인라인 heredoc이 정본이며 `templates/`는 byte-identical mirror입니다(릴리스 게이트에서 diff 검증).

## Local validation and marketplace setup

```sh
claude plugin validate ./claude
claude plugin marketplace add ./claude
claude plugin install cmux-agent-harness-loop-plugin@personal-claude-tools
```

## Shared Contracts

플러그인 런타임 계약은 플러그인 로컬 `contracts/`에 둡니다.

- `contracts/cmux-transport-contract.md`: 검증된 cmux CLI 표면 + cmux-only + both-channels 규칙.
- `contracts/harness-loop-contract.md`: 5개 관찰 가능 상태 + 13-state 내러티브 + 종료 스펙.
- `contracts/review-verdict.md`: GO|STOP|NEEDS_CHECK enum + sentinel + atomic ordering 계약.
- `contracts/safety-contract.md`: ask-family 금지 범위, 위험 플래그, redaction, negative test.

루트 `docs/`는 유지보수자용 미러이며 릴리스 노트입니다. 설치 후 스킬이 읽어야 하는 문서는 플러그인 패키지 안에 두고 `SKILL.md`에서 플러그인 로컬 경로를 참조합니다.

`.agent-harness/`와 `docs/changes/`는 **대상 프로젝트의 런타임 산출물**이며 이 플러그인 저장소에 커밋하지 않습니다. 대상 프로젝트의 `.gitignore`에 `.agent-harness/`를 추가하세요.

Reviewer 결과는 advisory이며 Claude orchestrator가 최종 판단합니다. merge/release 승인은 사람만 합니다.
