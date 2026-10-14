---
name: basic-team
description: Coordinate native Codex or Claude agents through planning, parallel implementation, mandatory Karpathy and Ponytail reviews, and conditional design and E2E reviews. Use when the user asks to run or resume a basic-team development workflow. Not for explaining, inspecting or editing this skill or its progress helper, and not for a standalone Karpathy or Ponytail code review.
---

# Basic Team

Raise the quality of a change with a small team: plan with ralplan, build in parallel Frontend/Backend lanes, review independently, fix, repeat until the required reviewers pass. The main session is the leader: it splits the plan, dispatches agents, relays findings, keeps the progress page and talks to the user. It never edits product files itself. A request to inspect or edit this skill is not a request to run it.

Follow the user's scope and permissions. This workflow grants no commits, pushes, deploys or global config changes unless the user asks.

## Models

Pass both values as real spawn arguments on every creating call (Claude `Agent`: `model` alias and `effort`; Codex `spawn_agent`: `model`, `reasoning_effort`). The Claude alias selects the model ID shown in parentheses; if the host reports a different ID, use the reported one. Never use `subagent_type: "fork"`, which ignores them.

| Role | Claude | Codex |
| --- | --- | --- |
| Executor | `haiku` (`claude-haiku-5-5`), `max` | `gpt-6-luna`, `max` |
| Documentation executor (only for docs tasks) | `sonnet` (`claude-sonnet-5-5`), `medium` | `gpt-6.1-sol`, `medium` |
| Reviewer | `sonnet` (`claude-sonnet-5-5`), `high` | `gpt-6.1-sol`, `medium` |

On Claude, named `Agent` calls become teammates when agent teams are enabled; message them by name with `SendMessage`. On Codex, use native collaboration (`spawn_agent`, `send_input`, `wait`). If the host cannot set a model or effort, tell the user once and continue.

## Workflow

**1. Plan.** Run the installed `ralplan` skill on the request (fall back to `plan` if ralplan is absent). Ralplan runs its own Planner, Architect and Critic; do not re-implement or re-order them. Use its approved plan. Ask the user only when the plan leaves a real product decision open.

**2. Split.** Turn the plan into tasks. Each task has an id, owner, owned files, acceptance criteria and the exact test command that proves it. Split Frontend and Backend into separate lanes, and split further only when two pieces can really run in parallel without touching the same files. One owner per file. Name the cross-lane contract (API shape, errors) before building. Decide here whether Impeccable (visible UI change) and E2E (a flow across screens, server or storage) reviews are needed, and record the reason as a decision. Create the progress page (below).

**3. Build.** Dispatch all ready tasks at once with the executor brief in [references/briefs.md](references/briefs.md). Start a dependent task when its prerequisite reports done. Reuse an idle executor for follow-up work in its own lane instead of spawning a new one. Each executor runs its own tests and reports changed files and results. When all build tasks are done, have one executor run the project's required full checks.

**4. Review.** Freeze the change: no edits while reviewers work. Record the revision as `git add -A -N && git diff <base> | shasum -a 256` (`-N` makes new files visible to the diff). Dispatch the reviewers in parallel with the reviewer brief, all on that same revision:
- `Karpathy Agent` (required): requirements, assumptions, cross-lane contracts, scope.
- `Ponytail Agent` (required): implementation, callers, edge cases, simplicity.
- `Impeccable Agent` (if decided in step 2): design quality of the changed UI.
- `E2E Agent` (if decided in step 2): the connected flow in a real browser.

Reviewers are read-only and do not see each other's results. Wait for all of them before acting on any finding.

**5. Fix.** If any reviewer returns `CHANGES_REQUIRED`, send each required finding to the owner of that file. The owner fixes it and reruns the affected tests. Then freeze a new revision and send it to the same reviewers (resume them; they review the delta and whatever it touches). Advisory findings are optional. Repeat until every required reviewer returns `PASS` on the same revision. After 3 rounds without convergence, stop and ask the user, with the open findings and your recommendation.

**6. Finish.** Run the required checks once more on the final revision. Shut down the agents you started (Claude: `SendMessage` a shutdown request to each teammate; Codex: close them). Report to the user: what changed, review results, check results, and anything left unchecked.

## Blockers

When something blocks a task: read the error and the relevant code once, try the smallest fix inside the task's own files, and keep independent tasks moving meanwhile. Ask the user only for a missing requirement, missing access, or a choice between materially different outcomes, and include your recommendation. Do not retry a failing step without new information.

## Progress page

One standalone HTML page per run at `<project>/docs/inprogress/<task-slug>-<YYYYMMDD-HHmm>.html`. It shows the stage, the user's to-dos, a task graph (lanes Plan → Build → Review → Fix → Finish, cards 대기중 / 진행중 / 완료 / 중단 with elapsed time, arrows for prerequisites), review results, blockers and decisions, and reloads itself every 30 seconds until the run is done. Update it when something changes, not on a timer. Write user-facing text in plain Korean.

```sh
uv run "<skill-dir>/scripts/progress.py" init "<page>" --title "<작업 이름>"
uv run "<skill-dir>/scripts/progress.py" update "<page>" --input - <<'JSON'
{"stage": "구현", "summary": "백엔드 API 구현 중", "todo": "없음", "blockers": "없음",
 "tasks": [{"id": "BE-1", "title": "목록 API 페이지네이션", "owner": "backend-1", "lane": "build", "status": "진행중", "after": ["PLAN"]}],
 "decisions": [{"title": "E2E 리뷰 생략", "body": "화면 하나만 바뀌고 서버 흐름은 그대로"}]}
JSON
uv run "<skill-dir>/scripts/progress.py" status "<page>"
```

[references/progress-example.md](references/progress-example.md) shows a full run's patches at each checkpoint (split, blocker, each review round dispatched and returned, fix, finish); follow its conventions. Send only what changed:
- `tasks` merge by `id`, `decisions` by `title`, `reviews` by `round` + `reviewer` (`{"round": 1, "reviewer": "Karpathy Agent", "verdict": "PASS", "note": "..."}`).
- `stage` starts with `계획`, `구현`, `리뷰`, `수정`, `마무리`, `완료` or `중단`; detail may follow after a space (`수정 (2라운드)`). `중단` means the run is abandoned (the user cancelled or it cannot continue). While waiting for the user's answer, keep the current stage and put the question in `todo` (or `blockers` if it stops the run).
- `lane` is the kind of work, not when it happened: `plan`, `build`, `review`, `fix` or `finish` (see the example's conventions).
- `status` is `대기중`, `진행중`, `완료` or `중단` (dropped or replaced work).
- `reviewer` is exactly one of the four agent names in step 4.
- `todo` is what the user must do or decide (`없음` when nothing).
- The script stamps task times, and sets stage `완료` itself when the last finish task closes (at least one finish task `완료`) with nothing else open.
- Give agent tasks the full model ID and effort from the table, not the alias (for example `"model": "claude-haiku-5-5", "effort": "max"`); the card shows them as the requested model, not a host-confirmed one.
- Run every Python command in this skill with `uv run`, never `python` directly.

Brief the user at plan approval, after each review round, on a blocker and at the end: current stage, done, remaining, the user's to-dos (`todo`), blocker, and the page link.
