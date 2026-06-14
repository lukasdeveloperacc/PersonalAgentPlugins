# Socrates Workshop Contract

This contract defines the `/socrates`-style pre-planning workflow. It is intentionally
conversation-first: Claude does not jump straight to implementation. Claude hosts the workshop,
Codex/OMX acts as the visible thinking partner, and a document specialist produces the final
planning artifacts.

## 1. Purpose

Turn a raw product or app idea into implementation-ready planning documents through a guided
conversation that adapts to:

1. the user's preferred progression style, and
2. the user's experience level.

The expected output is not code. The expected output is a clear product brief / PRD / handoff
that can later feed `cmux-agent-harness-loop plan` or `loop`.


## 2. Language policy

All user-facing questions, menus, Codex/OMX partner summaries, and final planning artifacts
MUST be written in Korean by default. Use another language only when the user explicitly requests
it. Internal stage names and file names may remain English for machine-readability, but the content
inside the documents should be Korean.

## 3. Entry surface

Canonical plugin invocation:

```text
/cmux-agent-harness-loop-plugin:socrates
```

For a video-like bare command, a target project may install the alias template:

```text
.claude/commands/socrates.md
```

The alias delegates to the plugin skill. Plugin namespaces remain the portable, conflict-free
Claude Code form.

## 4. Required inputs

Socrates must collect these before synthesis:

- **Idea** — the raw app/product/change idea, in the user's words.
- **Progression mode** — one of:
  - `interview` — deeper Socratic interview, one high-leverage question at a time.
  - `debate` — Codex/PM challenges assumptions, alternatives, risks, and positioning.
  - `fast` — minimum questions, strongest reasonable assumptions, quick document output.
- **Experience level** — one of:
  - `beginner` — almost first time; explain concepts, avoid jargon.
  - `tutorial` — has followed tutorials; give examples and guardrails.
  - `solo_builder` — can build alone; focus on tradeoffs and scope control.
  - `professional` — practitioner; use concise product/engineering language.

If any input is missing, ask for it conversationally. Do not start implementation.

## 5. Conversation stages

Observable stages for `docs/changes/SOCRATES_STATE.json`:

```text
IDEA_CAPTURE → MODE_SELECT → EXPERIENCE_SELECT → DISCOVERY → CODEX_REFLECTION → DIRECTION_CHOICE → DOCUMENT_DRAFT → DOCUMENT_REVIEW → HANDOFF
```

### IDEA_CAPTURE
Capture the exact user idea and any constraints already given.

### MODE_SELECT
Offer the three progression modes. The default is `interview` unless the user requests speed or
a debate.

### EXPERIENCE_SELECT
Offer the four experience levels. The default is `solo_builder` only if the user appears already
technical; otherwise ask.

### DISCOVERY
Ask questions according to the selected mode:

| Mode | Behavior |
|---|---|
| `interview` | Ask exactly one high-leverage question per round. Build from the user's answer. Stop once target, user, pain, MVP, success criteria, constraints, and out-of-scope are clear. |
| `debate` | Gather enough context, then ask Codex/OMX for a challenge pass. Present the challenge plainly, then offer direction choices. |
| `fast` | Ask at most 1-2 blocker questions. If non-blocking gaps remain, state assumptions and continue. |

### CODEX_REFLECTION
Use cmux to involve the Codex/OMX partner pane whenever available:

1. Ensure or reuse the persistent reviewer/Codex pane from `.agent-harness/panes.json`.
2. If the pane is new, start `omx` interactively inside it using `cmux send --surface <ref> -- "omx\n"`;
   fall back to interactive `codex\n` only when OMX is unavailable.
3. Send a non-mutating prompt via `cmux send` / buffer paste into the already-running interactive OMX/Codex pane.
4. Observe via `cmux read-screen`.
5. Ask Codex for critique, missing assumptions, target-user clarity, MVP cut, risk, and next
   question suggestions.
6. Surface the Codex view back to the user. Do not hide the partner's reasoning as a private
   internal step.

If cmux/Codex is unavailable, continue the workshop but explicitly mark the Codex partner as
`unavailable` in `SOCRATES_STATE.json` and in the final handoff.

Recommended Codex companion plugin: install `socrates-codex-partner-plugin` from the repo-local
`codex/` marketplace so the Codex pane has matching `socrates-partner`,
`socrates-document-specialist`, and `harness-reviewer` skills.

Forbidden: `/ask`, `omc ask`, `omx ask`, raw one-shot provider ask calls, and default-use
non-interactive exec transport (`cmux omx exec`, `omx exec`, `codex exec`, `codex exec review`).

### DIRECTION_CHOICE
After Codex reflection, Socrates must offer choices comparable to the video flow:

```text
1. 이대로 진행
2. 문제/타겟 다시 잡기
3. 기능/차별화 다시 잡기
4. OUT 목록 조정
5. 질문 더 받기
```

If the user chooses anything except `이대로 진행`, return to DISCOVERY with that focus.

### DOCUMENT_DRAFT
Invoke the plugin-shipped `document-specialist` agent when available. The agent drafts planning
artifacts only; it does not implement source code.

Required artifacts:

- `docs/changes/SOCRATES_BRIEF.md` — concise idea, target, problem, value proposition, MVP.
- `docs/changes/PRD.md` — product requirements and acceptance criteria.
- `docs/changes/OUT_OF_SCOPE.md` — explicit non-goals and deferred ideas.
- `docs/changes/HANDOFF.md` — next prompt for `plan` / `loop`.

Optional artifacts:

- `docs/changes/EXPERIMENT_PLAN.md` — validation experiments if product risk is high.
- `docs/changes/QUESTIONS.md` — unresolved questions if planning cannot safely finish.

### DOCUMENT_REVIEW
Claude reviews the document-specialist output against the conversation and Codex reflection.
If it drifts from the user's answers, fix the document before handoff.

### HANDOFF
End with:

- chosen mode and experience level,
- files written,
- unresolved assumptions,
- recommended next command, usually:

```text
/cmux-agent-harness-loop-plugin:cmux-agent-harness-loop plan "<summarized request>"
```

## 6. State and memory

Write workshop memory under the target project:

```text
docs/changes/SOCRATES_STATE.json
docs/changes/SOCRATES_TRANSCRIPT.md
docs/changes/SOCRATES_BRIEF.md
docs/changes/PRD.md
docs/changes/OUT_OF_SCOPE.md
docs/changes/EXPERIMENT_PLAN.md  # optional
docs/changes/QUESTIONS.md        # optional
```

Do not write secrets. Redact token-like values using the safety contract.

## 7. Stop conditions

Socrates stops when one of these is true:

- final documents are written and reviewed,
- the user explicitly pauses/stops,
- a blocking ambiguity remains and the user cannot answer it,
- Codex/document-specialist tooling is unavailable and the user requested strict video-equivalent
  behavior.

Otherwise keep the conversation moving. Do not ask for permission to continue between obvious
safe planning steps.
