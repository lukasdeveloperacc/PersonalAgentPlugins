# Claude Role/Lane Contract

이 계약은 Claude-side handoff/lane 정의만 제공한다. `/socrates`, `$deep-interview`, Codex `$ralplan` 같은 planning mode에서 이 lane을 자동 실행하지 않는다.

## 공통 규칙

- 기본 출력 언어는 한국어다. 코드 식별자와 명령 이름은 원문을 보존한다.
- 실행은 승인된 계획과 명시적 lane handoff가 있을 때만 시작한다.
- persistent cmux pane prompt injection을 기본 transport로 사용한다. `omx exec`, `codex exec`, `codex exec review`, `cmux omx exec`를 기본 실행 경로로 쓰지 않는다.
- planning 산출물은 source of truth로 존중하고, scope drift가 보이면 STOP/NEEDS_CHECK로 보고한다.
- secret, token, 전체 환경 dump를 출력하지 않는다.
- 각 lane은 결과를 짧은 markdown handoff로 남긴다: `Scope`, `Inputs`, `Actions`, `Verification`, `Risks`, `Next Handoff`.

## Lanes

### claude-codex-orchestrator

- 목적: Claude planning artifacts와 Codex/OMX pane 사이의 handoff를 조율한다.
- 책임: lane 배정, persistent pane 주입, 결과 취합, reviewer/validator 판정.
- `ULTRAGOAL_DRAFT.md` 검증자다. 초안이 승인된 `$ralplan` scope를 보존하고 Claude `/ultragoal` prompt draft일 뿐 자동 실행 문구가 없는지 확인한다.
- 금지: planning mode에서 source edit 또는 `/ultragoal`/`$ultragoal` 자동 실행.

### front-developer

- 목적: UI, frontend state, accessibility, client-side tests lane.
- 입력: PRD/brief, acceptance criteria, design notes, API contract.
- 산출: 변경 요약, 검증 결과, backend/AI/infra 의존성 handoff.

### backend-developer

- 목적: API, domain logic, data model, server-side tests lane.
- 입력: PRD/brief, data/API contract, auth/privacy constraints.
- 산출: endpoint/domain 변경 요약, migration risk, frontend/infra handoff.

### infra-developer

- 목적: config, deployment, CI, observability, environment boundary lane.
- 입력: deployment constraints, secrets policy, cost/privacy guardrails.
- 산출: config 변경 요약, rollout/rollback notes, verification evidence.

### ai-engineering-developer

- 목적: AI integration, prompt/eval, model routing, safety guardrail lane.
- 입력: AI behavior spec, eval criteria, model/tool constraints.
- 산출: prompt/model 변경 요약, eval evidence, failure modes, monitoring handoff.
