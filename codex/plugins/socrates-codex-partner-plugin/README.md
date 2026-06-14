# socrates-codex-partner-plugin

Claude `cmux-agent-harness-loop-plugin`와 함께 쓰는 **Codex 동반자 플러그인**입니다.
Socrates 워크숍과 하니스 리뷰에서 Codex/OMX pane이 한국어 우선, 구조화된 markdown,
영속 cmux transport 규칙을 따르도록 역할 프로필을 제공합니다.

## 제공 역할

각 역할은 `skills/<role>/SKILL.md` entrypoint와 `skills/<role>/agents/openai.yaml` agent
profile을 함께 제공합니다. 현재 Codex plugin manifest/validator가 안정적으로 검증하는 배포 단위는
top-level native subagent bundle이 아니라 이 **skill + agent-profile 쌍**입니다.
`allow_implicit_invocation`은 Codex UI discovery/routing hint이며, persistent cmux pane prompt
injection이라는 협업 transport 정본을 대체하지 않습니다.

핵심 역할:

- `socrates-partner` — 아이디어 탐색 중 PM/비평 파트너.
- `socrates-document-specialist` — PRD/brief/handoff 작성자.
- `harness-reviewer` — cmux loop용 file-authoritative STOP/GO reviewer.

얇은 동반자 lane:

- `socrates-pm` — 제품 framing, MVP 축소, 우선순위, 수용 기준.
- `idea-reviewer` — 아이디어/타겟/차별화/검증 리스크 리뷰.
- `design-reviewer` — UX flow, IA/copy, 접근성, 상태 처리 리뷰.
- `code-reviewer` — 읽기 전용 diff/구현 리뷰. verdict 파일은 `harness-reviewer` 사용.
- `ai-researcher` — AI/model/API/agent 근거 요약.
- `surfer-researcher` — 시장/경쟁/UX/public-source 관찰.
- `ralplan-partner` — consensus plan, test shape, 구현 전 리스크 점검.

## 설치

Repository root에서:

```sh
codex plugin marketplace add ./codex
codex plugin add socrates-codex-partner-plugin@personal-agent-plugins-codex
```

## Claude ↔ Codex flow

1. Claude `/cmux-agent-harness-loop-plugin:socrates`가 사용자 대화를 진행합니다.
2. Claude가 interactive `omx` pane을 시작/재사용하고 `cmux send` 또는 buffer paste로 prompt를 주입합니다.
3. Codex는 필요한 role skill로 한국어 critique/research/review를 반환합니다.
4. 사용자가 `이대로 진행`을 선택하면 `socrates-document-specialist`가 planning docs를 작성할 수 있습니다.
5. 구현 loop에서는 `harness-reviewer`가 deterministic review verdict 파일을 작성합니다.

## 공통 계약

모든 role은 `contracts/codex-partner-contract.md`를 공유합니다.

- 한국어 우선 응답.
- 구조화된 markdown.
- persistent cmux/OMX/Codex pane transport.
- `/ask`, `omc ask`, `omx ask`, `provider ask`, `omx exec`, `codex exec` 계열 기본 금지.
- lane이 명시적으로 허용하지 않으면 source edits 금지.
- secret-like 값은 `[REDACTED]`로 마스킹.
