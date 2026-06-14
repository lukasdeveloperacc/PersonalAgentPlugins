# Codex Companion Plugin — Socrates Partner

Claude plugin이 사용자 대화를 host하고, Codex pane은 비디오 콜의 동료처럼 PM/리서치/리뷰
역할을 맡습니다. 이 repository는 그 동작을 예측 가능하게 만들기 위해 Codex companion plugin을
제공합니다.

```text
codex/plugins/socrates-codex-partner-plugin
```

## 설치

Repository root에서:

```sh
codex plugin marketplace add ./codex
codex plugin add socrates-codex-partner-plugin@personal-agent-plugins-codex
```

## 존재 이유

Claude `/cmux-agent-harness-loop-plugin:socrates`가 질문과 orchestrator 역할을 맡고,
Codex companion plugin은 cmux로 호출된 Codex/OMX pane의 기본 행동을 고정합니다.

- 한국어 우선 응답.
- planning workshop 중 source implementation 금지.
- 무작위 조언 대신 구조화된 PM critique/research/review.
- `docs/changes/` planning artifact 작성 가능.
- harness verdict 파일은 `.done` marker와 sentinel 계약 준수.
- PM, idea, design, code, AI research, surfer research, ralplan critique lane 제공.

Transport 기대값: Claude가 interactive `omx` pane을 시작/재사용하고 `cmux send`/buffer paste로
prompt를 주입한 뒤 `cmux read-screen`으로 읽습니다. `omx exec`/`codex exec`는 visible multi-turn
conversation을 우회하므로 기본 경로가 아닙니다.

## 제공 Codex skills

현재 Codex plugin 배포/검증 표면은 top-level native subagent bundle이 아니라
`skills/<role>/SKILL.md`와 optional `skills/<role>/agents/openai.yaml` metadata입니다. 따라서 이
plugin은 각 역할을 **skill entrypoint + agent profile**로 제공합니다. Project-local
`.codex/agents/*.toml` native subagent가 필요하면 이 계약을 참조하는 별도 동기화 산출물로 추가합니다.
`agents/openai.yaml`의 `allow_implicit_invocation`은 Codex UI discovery/routing hint이며,
Claude↔Codex 협업 transport를 바꾸지 않습니다. Socrates/harness 협업의 정본 경로는 여전히
persistent cmux pane prompt injection입니다.

### 핵심 skills

- `socrates-partner` — 아이디어 탐색 PM/critic. 반론, 타겟/문제 점검, OUT 후보, 다음 질문을 반환합니다.
- `socrates-document-specialist` — `SOCRATES_BRIEF.md`, `PRD.md`, `OUT_OF_SCOPE.md`, `HANDOFF.md` 작성.
- `harness-reviewer` — `REVIEW_<loop_id>_<attempt>.md` + `.done` + sentinel을 쓰는 formal reviewer.

### 얇은 companion lanes

각 lane은 `contracts/codex-partner-contract.md`를 참조하고, 한국어 우선/구조화 markdown/영속 cmux
transport/no source edits 기본값을 공유합니다.

| Skill | 목적 | 기본 권한 |
| --- | --- | --- |
| `socrates-pm` | 제품 framing, MVP 축소, 수용 기준 | Planning only |
| `idea-reviewer` | 아이디어 검증, target/problem critique, 차별화 | Review only |
| `design-reviewer` | UX flow, IA/copy, accessibility/state review | Review/docs only |
| `code-reviewer` | Diff와 implementation critique | Read-only review |
| `ai-researcher` | AI/model/API/agent evidence summary | Research only |
| `surfer-researcher` | Market/competitor/public-source observations | Research only |
| `ralplan-partner` | Consensus-plan critique와 test-shape review | Planning only |

Formal STOP/GO verdict가 필요한 Claude loop에서는 `code-reviewer`가 아니라 `harness-reviewer`를 사용합니다.

## Claude ↔ Codex loop

```text
User
  ↓
Claude /socrates host
  ↓ cmux send / buffer paste into live omx pane
Codex role critique/research/review
  ↓ cmux read-screen
Claude summarizes back to user
  ↓ direction menu / handoff
Codex document or harness specialist
```

기본적으로 `/ask`, `omc ask`, `omx ask`, `provider ask`, `omx exec`, `codex exec`, 위험 권한 flag, source edits를
권장하지 않습니다.
