---
name: thegame-basic-team
description: TheGame variant of basic-team. Runs the full basic-team workflow (ralplan planning, parallel Frontend/Backend executors, Karpathy and Ponytail reviews plus Impeccable/E2E when needed, fix loop) and also keeps the run's task list as one Task in TheGame's Notion Task Board, with a clean checklist that is ticked off as tasks finish. Use when the user asks for thegame-basic-team, or wants a basic-team run tracked as a Notion Task or Notion TODO list. Not for explaining or editing this skill.
---

# TheGame Basic Team

This is basic-team with one addition: the run's task list also lives as one Task page in TheGame's Notion Task Board, so teammates can follow it without opening the progress page.

Resolve `<bt>` as the sibling `basic-team` skill directory (`<this skill's directory>/../basic-team`). Read `<bt>/SKILL.md` and follow it completely; its links and `<skill-dir>/scripts/progress.py` commands resolve against `<bt>`. The progress page stays the source of truth. Notion mirrors it for people: it never decides what runs next, and a Notion failure never blocks product work. A request to inspect or edit this skill is not a request to run it.

## Notion target

- Task Board data source: `collection://33b8a6cf-b7d4-8106-bca5-000bef4c35a9` (database https://app.notion.com/p/33b8a6cfb7d48026833cc7effb3b6111).
- Tools: Notion MCP `notion-fetch`, `notion-get-self`, `notion-create-pages`, `notion-update-page`. If they are missing, enable `notion` with the `lukas-plugin:mcp-setup` skill and ask the user to authenticate in `/mcp` (Codex: new session). If it is still unavailable, add a `Notion Task` decision saying so and run the rest of basic-team normally.
- Properties used: `업무명` (title), `Status` (`TODO`, `IN PROGRESS`, `DONE`), `작성자` and `담당자` (the connected user from `notion-get-self`), `작업유형` (one of `feature`, `fix`, `refactor`, `docs`, `chore`, `uiux`), `프로젝트` (multi-select). Leave the other properties empty. If a create call rejects a property or option, fetch the data source again and use what it shows; the schema may have changed.

## When to touch Notion

**Create (end of basic-team step 2, right after the progress page is created).** One `notion-create-pages` call with parent `data_source_id` above, icon `✅`, no template (the default template adds a placeholder to-do):

- `업무명`: a short Korean summary of what is being built or fixed, the same as the progress page `--title`.
- `Status`: `IN PROGRESS`. `작성자`, `담당자`: the connected user.
- `작업유형`: the closest single type for the request.
- `프로젝트`: the option whose name matches the repository directory name, if one exists. Otherwise leave it empty; do not invent options.
- Content (Notion markdown, nothing else):

```markdown
<one or two lines: the goal of the request>

진행 페이지: `<absolute progress page path>`

### 계획
- [x] ralplan 계획
### 구현
- [ ] OpenAPI 계약 갱신 + 타입 재생성
- [ ] 가져오기 안에서 음성 검증까지 처리
### 리뷰
### 수정
### 마무리
- [ ] 최종 검사 · 에이전트 종료 · 보고
```

One to-do per progress-page task, under the heading for its `lane` (`plan` 계획, `build` 구현, `review` 리뷰, `fix` 수정, `finish` 마무리), using the task's exact `title` so the two pages can be compared line by line. Checked means the task is `완료` on the progress page. Omit a lane heading until it has a task. Then add a decision to the progress page: `{"title": "Notion Task", "body": "<page URL>"}`. That URL is how a resumed run finds the Task again; never create a second Task for the same run and never pick one by searching titles.

**Sync (every progress `update` that adds tasks or changes a status).** In the same checkpoint, edit the same Notion page with `notion-update-page` `update_content`, smallest edits only: `- [ ] <title>` → `- [x] <title>` when a task becomes `완료`, back to `- [ ]` if a fix reopens it, and new tasks (review rounds, fixes) appended under their lane heading. Fetch the page first when unsure of its current text. Do not rewrite the goal line, the path line or anything a person added.

**Finish (basic-team step 6).** After the final report is ready, make sure every to-do matches the progress page, then set `Status` to `DONE` with a separate `update_properties` call (`update_content` ignores `properties` passed alongside it), and fetch the page once to confirm the status and checkboxes. If the run stops blocked or the user cancels, keep `IN PROGRESS`, leave the to-dos as they are, and insert one line at the top: `막힘: <reason>`. Include the Task URL in the final report.

## Keep it clean

The Task is read by teammates who did not watch the run: goal, link and checklist only. Do not copy model IDs, effort, owners, review findings, test output or file lists into Notion; those stay on the progress page. Write in Korean unless the user asks otherwise. A failed Notion write is noted in the next briefing and retried at the next checkpoint; it never pauses agents or repeats product work.
