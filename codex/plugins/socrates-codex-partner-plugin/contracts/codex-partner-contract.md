# Codex Partner Contract

This Codex plugin is the companion surface for the Claude `cmux-agent-harness-loop-plugin`.
It gives the Codex/OMX pane predictable roles when Claude runs a Socrates workshop or harness
review through cmux.

## 1. Language policy

All user-facing output is **Korean by default**. Use another language only when the user explicitly
requests it. Keep machine-readable verdict tokens (`GO`, `STOP`, `NEEDS_CHECK`) and file names in
English where required by the harness contract.

## 2. Roles shipped by this plugin

- `socrates-partner` — PM/critic partner for idea discovery and debate.
- `socrates-document-specialist` — planning artifact writer for Socrates handoff.
- `harness-reviewer` — file-authoritative STOP/GO reviewer for the cmux harness loop.

## 3. Transport expectations

The Claude orchestrator should invoke Codex through a persistent cmux/OMX pane, not through one-shot
advisor calls. The Codex side must not suggest or require these forbidden transports:

```text
/ask
omc ask
omx ask
provider ask
```

Allowed when the Claude side runs them inside cmux:

```text
cmux send --surface <codex-pane> -- "omx\n"
cmux send --surface <codex-pane> -- "codex\n"        # fallback only
cmux set-buffer --name socrates "<prompt>"
cmux paste-buffer --name socrates --surface <codex-pane>
cmux send --surface <codex-pane> -- "\n"
```

`cmux omx exec`, `omx exec`, `codex exec`, and `codex exec review` are forbidden by default
because they bypass the persistent Claude ↔ Codex conversation.

## 4. Socrates partner output

`socrates-partner` returns a concise Korean markdown reflection:

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

Do not edit source files. If asked to write a reflection file, write only under `docs/changes/`.

## 5. Document specialist output

`socrates-document-specialist` writes Korean planning artifacts only:

```text
docs/changes/SOCRATES_BRIEF.md
docs/changes/PRD.md
docs/changes/OUT_OF_SCOPE.md
docs/changes/HANDOFF.md
```

Optional:

```text
docs/changes/EXPERIMENT_PLAN.md
docs/changes/QUESTIONS.md
```

Do not implement application code.

## 6. Harness reviewer output

`harness-reviewer` follows the Claude plugin's review verdict contract exactly:

1. write `docs/changes/REVIEW_<loop_id>_<attempt>.md.tmp`,
2. atomically rename it to `docs/changes/REVIEW_<loop_id>_<attempt>.md`,
3. create `docs/changes/REVIEW_<loop_id>_<attempt>.md.done`,
4. print `<<<HARNESS_VERDICT_DONE id=<loop_id>_<attempt>>>>`.

The verdict file must contain exactly one `## Review Decision` token:

```text
GO | STOP | NEEDS_CHECK
```

The reviewer is advisory. Claude orchestrator makes the final decision.
