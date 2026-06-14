# Codex Partner Contract

이 Codex plugin은 Claude `cmux-agent-harness-loop-plugin`의 companion surface입니다.
Claude가 Socrates workshop 또는 harness review를 cmux로 진행할 때 Codex/OMX pane이 일관된
역할, 언어, transport, write-scope 규칙을 따르도록 합니다.

## 1. 언어 정책

사용자-facing output은 **한국어 우선**입니다. 사용자가 명시적으로 요청할 때만 다른 언어를 씁니다.
Harness가 요구하는 machine-readable verdict token(`GO`, `STOP`, `NEEDS_CHECK`)과 파일명은 English를
유지합니다.

## 2. 제공 역할

핵심 역할:

- `socrates-partner` — idea discovery/debate용 PM/critic partner.
- `socrates-document-specialist` — Socrates handoff용 planning artifact writer.
- `harness-reviewer` — cmux harness loop용 file-authoritative STOP/GO reviewer.

얇은 Codex companion lanes:

- `socrates-pm` — product framing, MVP cuts, roadmap tradeoffs, acceptance criteria.
- `idea-reviewer` — early idea, target, differentiation, validation critique.
- `design-reviewer` — UX, flow, information architecture, copy, accessibility, state review.
- `code-reviewer` — read-only implementation diff review; verdict file은 `harness-reviewer` 사용.
- `ai-researcher` — AI/model/API/agent research with evidence-vs-inference boundaries.
- `surfer-researcher` — market, competitor, UX, public-source observations.
- `ralplan-partner` — consensus-plan critique, test shape, implementation-readiness risks.

각 lane은 두 표면을 함께 가진다.

1. `skills/<role>/SKILL.md` — 사용자가 명시적으로 호출하거나 plugin이 라우팅할 때 읽는 실행 계약.
2. `skills/<role>/agents/openai.yaml` — Codex UI/agent 표면용 metadata profile.

현재 Codex plugin manifest는 top-level native subagent bundle이 아니라 skill discovery와 skill별
agent metadata를 검증한다. 따라서 이 plugin에서 “Codex agent”는 **skill entrypoint + agent profile**
쌍으로 배포한다. Project-local `.codex/agents/*.toml` native subagent가 필요할 때는 이 계약을
동일하게 참조하는 별도 설치/동기화 산출물로 다룬다.

`agents/openai.yaml`의 `allow_implicit_invocation`은 Codex UI/agent routing discovery를 위한
metadata hint일 뿐, Claude↔Codex transport 권한을 바꾸지 않는다. Socrates/harness 협업에서의
정본 transport는 계속 persistent cmux pane prompt injection이며, ask-family 또는 exec-family
shortcuts를 허용하지 않는다.

## 3. Transport 기대값

Claude orchestrator는 one-shot advisor call이 아니라 persistent cmux/OMX pane으로 Codex를 호출해야 합니다.
Codex side는 다음 forbidden transports를 제안하거나 요구하지 않습니다.

```text
/ask
omc ask
omx ask
provider ask
```

Claude side가 cmux 안에서 실행할 수 있는 allowed transport 예:

```text
cmux send --surface <codex-pane> -- "omx\n"
cmux send --surface <codex-pane> -- "codex\n"        # fallback only
cmux set-buffer --name socrates "<prompt>"
cmux paste-buffer --name socrates --surface <codex-pane>
cmux send --surface <codex-pane> -- "\n"
```

`cmux omx exec`, `omx exec`, `codex exec`, `codex exec review`는 persistent Claude ↔ Codex 대화를
우회하므로 기본 금지입니다.

## 4. 공통 lane 규칙

각 skill file이 더 엄격하지 않은 한 모든 Socrates/Codex companion lane은 다음을 따릅니다.

- Korean-first user-facing markdown.
- Persistent cmux/OMX/Codex pane transport; no ask-family or exec-family shortcuts.
- Structured markdown with clear headings, evidence, assumptions, risks, and next decision.
- No application source edits unless the active lane explicitly grants implementation authority.
- Planning/research notes are concise and stay in the orchestrator-provided planning path.
- Secret-like 값은 `[REDACTED]`로 마스킹합니다.

## 5. Socrates partner output

`socrates-partner`는 간결한 한국어 markdown reflection을 반환합니다.

```md
# Codex 리플렉션

## 내가 이해한 아이디어

## 가장 강한 반론

## 문제/타겟 점검

## 기능/차별화 점검

## OUT 후보

## 다음에 물어볼 질문 1개

## 방향 선택 추천
- 이대로 진행 / 문제·타겟 다시 / 기능·차별화 다시 / OUT 목록 조정 / 질문 더 받기
```

Source files를 수정하지 않습니다. Reflection 파일 작성 요청이 있을 때는 `docs/changes/` 아래에만 씁니다.

## 6. Document specialist output

`socrates-document-specialist`는 한국어 planning artifacts와 Ralplan-ready handoff bundle만 작성합니다.

```text
docs/changes/SOCRATES_BRIEF.md
docs/changes/PRD.md
docs/changes/OUT_OF_SCOPE.md
docs/changes/HANDOFF.md
docs/changes/RALPLAN_BRIEF.md
docs/changes/INTERVIEW_EVIDENCE.md
docs/changes/RALPLAN_DR_SEED.md
docs/changes/ULTRAGOAL_DRAFT.md
docs/changes/ROLE_PANE_MAP.md
docs/changes/MCP_READINESS_CHECKLIST.md
```

`ULTRAGOAL_DRAFT.md`는 Claude `/ultragoal` prompt draft only이며 `/socrates`, `$deep-interview`, Codex `$ralplan`, Codex `$ultragoal`에서 자동 실행하지 않습니다. 작성 책임은 document-specialist, 검증 책임은 claude-codex-orchestrator입니다.

Optional:

```text
docs/changes/EXPERIMENT_PLAN.md
docs/changes/QUESTIONS.md
```

Application code를 구현하지 않습니다.

## 7. Harness reviewer output

`harness-reviewer`는 Claude plugin의 review verdict contract를 정확히 따릅니다.

1. `docs/changes/REVIEW_<loop_id>_<attempt>.md.tmp` 작성,
2. `docs/changes/REVIEW_<loop_id>_<attempt>.md`로 atomic rename,
3. `docs/changes/REVIEW_<loop_id>_<attempt>.md.done` 생성,
4. `<<<HARNESS_VERDICT_DONE id=<loop_id>_<attempt>>>>` 출력.

Verdict file에는 정확히 하나의 `## Review Decision` token만 포함합니다.

```text
GO | STOP | NEEDS_CHECK
```

Reviewer는 advisory입니다. 최종 결정은 Claude orchestrator가 내립니다.
