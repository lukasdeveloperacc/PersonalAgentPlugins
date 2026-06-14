# Socrates Workshop — video-style planning flow

This plugin now has a pre-implementation workshop surface in addition to the cmux harness loop.
The goal is to reproduce the video pattern: the user does not just give an instruction; the user
and Claude/Codex shape the idea together until planning artifacts are ready.

## Command surface

Portable plugin invocation:

```text
/cmux-agent-harness-loop-plugin:socrates
```

Optional video-like alias in a target project:

```text
/socrates
```

To create the alias, copy:

```text
claude/plugins/cmux-agent-harness-loop-plugin/templates/project-commands/socrates.md.tmpl
```

to the target project's:

```text
.claude/commands/socrates.md
```

Claude Code plugins are namespaced by default, so the plugin command remains the canonical form.


## Language policy

사용자에게 보이는 질문, 선택지, Codex/OMX 파트너 요약, 최종 기획문서 본문은 한국어가 기본입니다. 파일명과 상태명은 기계 판독성을 위해 영어를 유지할 수 있지만, 문서 내용은 사용자가 별도 요청하지 않는 한 한국어로 작성합니다.

## User-facing flow

1. **Idea input** — capture the raw idea in the user's own words.
2. **Progression mode**
   - `인터뷰모드`: one high-leverage question per round.
   - `토론모드`: Codex/PM challenges assumptions and alternatives.
   - `질문최소로 빠르게`: ask only blockers, then proceed with assumptions.
3. **Experience level**
   - `거의처음`
   - `튜토리얼 정도`
   - `혼자 만들 수 있음`
   - `실무개발자`
4. **Discovery** — target user, problem, workaround, MVP, differentiation, success metric,
   constraints, OUT list.
5. **Codex reflection** — through cmux/OMX/Codex pane, not `/ask`.
6. **Direction menu** — especially in debate mode:
   - 이대로 진행
   - 문제/타겟 다시 잡기
   - 기능/차별화 다시 잡기
   - OUT 목록 조정
   - 질문 더 받기
7. **Document specialist** — drafts planning artifacts and the Ralplan-ready handoff bundle.
8. **Handoff** — gives the next `$ralplan`, `plan`, or explicit Claude `/ultragoal` draft prompt.

## Codex collaboration

The workshop is explicit about Codex participation. Codex is not a hidden private thought. The
Socrates host sends a critique prompt to the persistent OMX/Codex pane through cmux and then
summarizes Codex's pushback back to the user.

If Codex/cmux is unavailable, Socrates can still continue, but the final report must say the Codex
partner was unavailable.

## Artifacts

Written under the target project's `docs/changes/`:

```text
SOCRATES_STATE.json
SOCRATES_TRANSCRIPT.md
SOCRATES_BRIEF.md
PRD.md
OUT_OF_SCOPE.md
HANDOFF.md
EXPERIMENT_PLAN.md  # optional
QUESTIONS.md        # optional
RALPLAN_BRIEF.md
INTERVIEW_EVIDENCE.md
RALPLAN_DR_SEED.md
ULTRAGOAL_DRAFT.md
ROLE_PANE_MAP.md
MCP_READINESS_CHECKLIST.md
```

The six-file Ralplan-ready bundle is meant to remove hidden context between the workshop and
Codex planning:

- `RALPLAN_BRIEF.md` — compact input for Codex `$ralplan`.
- `INTERVIEW_EVIDENCE.md` — answers, Codex critique, assumptions, and unresolved questions.
- `RALPLAN_DR_SEED.md` — decision drivers, options, recommendation, risks, and test-shape seed.
- `ULTRAGOAL_DRAFT.md` — Claude `/ultragoal` prompt draft only; it is not auto-run.
- `ROLE_PANE_MAP.md` — Codex PM/reviewer/researcher panes and Claude orchestrator/developer lanes.
- `MCP_READINESS_CHECKLIST.md` — servers/tools/credentials/manual smoke checks before execution.

`ULTRAGOAL_DRAFT.md` is owned by `document-specialist` and validated by
`claude-codex-orchestrator`. `/socrates`, `$deep-interview`, and `$ralplan` may create or review
the draft but must not execute it automatically.

## Why this exists before the loop

The existing `cmux-agent-harness-loop` is for implementation and review. Socrates is for deciding
what should be implemented in the first place. The intended handoff is:

```text
Korean-first `/socrates` planning conversation
  → Codex `$ralplan` handoff bundle
  → Claude `/ultragoal` prompt draft only
  → explicit user-selected execution lane
```

Plugin-local contracts/templates/skills are canonical. Root `docs/` files are mirrors and release
explanations; if this page conflicts with
`claude/plugins/cmux-agent-harness-loop-plugin/contracts/socrates-workshop-contract.md`, the
plugin-local contract wins.
