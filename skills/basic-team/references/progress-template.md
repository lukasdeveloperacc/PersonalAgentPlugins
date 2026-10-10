# Populate the progress template

Copy `assets/progress-template.html` from the resolved basic-team skill directory to `<executing-project-root>/docs/inprogress/<task-slug>-<YYYYMMDD-HHmmss>-progress.html`. Create the directory when absent; derive the root from the target project/worktree, not the skill installation. Reuse the same file when the task continues or resumes, preserve completed runs, and never overwrite another run’s file. It opens via `file://` with no network, build, server, or periodic refresh. Preserve its styles and interaction code; update the embedded `script#progress-data` JSON on incoming reports and stage transitions. Read the asset when first creating the page, not on every report.

## Data

- `goal`, `summary`, `stage`, `updated`: concise goal, plain-language next step, observed stage, and last saved timestamp with timezone. Do not advance the report timestamp of a silent agent.
- `path`: the progress file's actual absolute path. Include a clickable link and this absolute path in every main-session briefing: kickoff, plan, progress, review, blocker/question, resume, and completion. Keep the same path throughout the run and label the link with the task name. The page falls back to its own local URL path when omitted; clipboard refusal has a manual-copy message.
- `blockers`: `{ "text": "<observed blocker summary>", "tone": "neutral" }`. Never infer no blockers from silence.
- `flow`: ordered `{ "title": "<stage or lane>", "body": "<tasks, parallel branches and prerequisites>" }` entries. Include only task-relevant areas and required reviewers. Group parallel Frontend/Backend work in the same implementation stage rather than implying sequential execution.
- `plan`, `reviews`, `decisions`: arrays of `{ "title": "<short heading>", "body": "<facts>", "meta": "<optional revision, time or evidence path>" }`. Plan includes draft/approved revision, work allocation with task IDs/owners/files/dependencies/contracts/acceptance criteria. Reviews include review round, content identity, validation evidence/gaps and Impeccable activation reason. Decisions include rationale, blockers, options and unresolved user questions.
- `agents`: `{ "name", "role", "area", "status", "tone", "reported", "owned", "result", "next", "blocker", "model", "observation" }` objects with string fields. Show requested model/effort separately from actually observed settings. Use one entry per assigned agent including helpers; disclose not-launched/queued states rather than fabricating reports.
- `reviewNotice`: review collection state in plain language. Keep early independent verdicts and findings out of the HTML's JSON as well as the visible page until all required reviews arrive. Mark superseded verdicts and missing evidence explicitly.

Allowed `tone` values are `neutral`, `active`, `good`, `warn`, `bad`. Color supplements visible status text; it never implies a percentage. Empty arrays display explanatory empty states, not demo achievements. Optional `meta` is plain text, not executable HTML.

Serialize JSON with a real JSON serializer and replace every literal `<` with `\u003c` before embedding so report text cannot close the script element. Rendered report values use `textContent`; preserve that boundary. Keep the remaining template unchanged and save the complete page atomically when practical. Do not insert source HTML, secrets, private reasoning, or unverified claims. Translate fixed UI labels and `lang` when needed without changing tab IDs.

The template is a saved view. It does not start agents, poll, fetch external resources, automatically reload, or replace basic-team's reviewer and final-revision gates.
