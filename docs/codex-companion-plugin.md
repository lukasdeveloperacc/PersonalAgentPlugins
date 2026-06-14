# Codex Companion Plugin — Socrates Partner

The Claude plugin hosts the conversation, but the video-like workflow works better when the Codex
pane also has a matching plugin contract. This repository therefore ships a Codex companion plugin:

```text
codex/plugins/socrates-codex-partner-plugin
```

## Install

From this repository root:

```sh
codex plugin marketplace add ./codex
codex plugin add socrates-codex-partner-plugin@personal-agent-plugins-codex
```

## Why it exists

Claude `/cmux-agent-harness-loop-plugin:socrates` asks the user questions and orchestrates the
workflow. The Codex companion plugin makes the Codex/OMX pane predictable when Claude calls it
through cmux:

- Codex knows it should answer in Korean by default.
- Codex knows not to implement source code during the planning workshop.
- Codex returns a structured PM critique instead of random advice.
- Codex can write PRD/brief/handoff documents under `docs/changes/` only.
- Codex can write harness verdict files with the required `.done` marker and sentinel.

Transport expectation: Claude starts or reuses an interactive `omx` pane, injects prompts with
`cmux send`/buffer paste, and reads via `cmux read-screen`. `omx exec`/`codex exec` are not the
default path because they bypass the visible multi-turn conversation.

## Shipped Codex skills

### `socrates-partner`

PM/critic partner for idea discovery. It returns:

- 내가 이해한 아이디어
- 가장 강한 반론
- 문제/타겟 점검
- 기능/차별화 점검
- OUT 후보
- 다음에 물어볼 질문 1개
- 방향 선택 추천

### `socrates-document-specialist`

Planning-document writer. It writes Korean documents only:

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

### `harness-reviewer`

Reviewer for implementation loops. It follows the file-authoritative verdict contract:

```text
REVIEW_<loop_id>_<attempt>.md.tmp
→ REVIEW_<loop_id>_<attempt>.md
→ REVIEW_<loop_id>_<attempt>.md.done
→ <<<HARNESS_VERDICT_DONE id=<loop_id>_<attempt>>>>
```

## Claude ↔ Codex loop

```text
User
  ↓
Claude /socrates host
  ↓ cmux send / buffer paste into live omx pane
Codex socrates-partner critique
  ↓ cmux read-screen
Claude summarizes back to user
  ↓ direction menu
Codex socrates-document-specialist writes docs
  ↓
Claude hands off to harness plan/loop
```

No `/ask`, `omc ask`, `omx ask`, `omx exec`, `codex exec`, dangerous flags, or source edits by
default.
