---
name: basic-team
description: Coordinate native Codex or Claude agents through planning, implementation by owned area, and independent Karpathy and Ponytail reviews until both pass. Use for a requested basic-team development workflow.
---

# Basic Team

The main session is the leader and the user's contact. Run one Planner, multiple Executors for independent work within and across implementation areas, and two independent reviewers: **Karpathy Agent** and **Ponytail Senior Agent**. Frontend and Backend are work classifications, not a limit of one Executor each; size the active Executor group to the ready work and host capacity. These are review personas, not claims that the named people reviewed the code.

Use native agents in the current host: Codex native collaboration or the installed OMC `team` skill's Claude native-team path. Keep orchestration in the main session; do not launch OMX/OMC tmux teams or another leader. Follow the user's scope, permissions, and test policy. Invoking this skill does not authorize publishing, pushing, deployment, or unrelated changes.

## Models and launch

Use the host column for every stage; both reviewers use the Reviewer settings.

| Role | Codex model | Reasoning | Claude model | Effort |
| --- | --- | --- | --- | --- |
| Planner | `gpt-6.1-sol` | `medium` | `claude-opus-5-5` | `medium` |
| Executor | `gpt-6-luna` | `max` | `claude-haiku-5-5` | `max` |
| Reviewer (each) | `gpt-6-luna` | `max` | `claude-sonnet-5-5` | `high` |

Inspect the actual tool schema and installed skill catalog before launching. Resolve `ralplan`, `plan`, `lukas-plugin:karpathy-guidelines`, `ponytail:ponytail`, and `eli5:eli5` (or the host's equivalent qualified names) to their real SKILL.md paths. On Claude also resolve and load `oh-my-claudecode:team`. Load only the skills needed by the current stage. Pass exact paths to children; they may not inherit the leader's skill context. Missing `ralplan` selects `plan`; if both planning skills, either review skill, eli5, or Claude's native team skill are missing, report the dependency blocker rather than inventing their contents.

- **Codex:** use the visible native `spawn_agent` and explicitly set `model` and `reasoning_effort`. Use `fork_turns: "none"` when supported, with a complete task brief. On the current collaboration surface, use unique `task_name` values such as `basic_team_planner`, `basic_team_executor_frontend_ui`, `basic_team_executor_backend_api`, `basic_team_karpathy`, and `basic_team_ponytail`. Avoid an installed `agent_type` whose profile overrides the requested settings; use `default` when it has no conflicting override. If spawn overrides are unavailable, use an already installed custom role only after verifying its model and effort match the table. Do not silently inherit the leader's model, change global configuration, or substitute a CLI process.
- **Claude:** use the installed `oh-my-claudecode:team` skill's native-team lifecycle, task assignment, messaging, and shutdown procedure. Keep the current main session as leader. Select its native route, not its `omc team` CLI/tmux route. This basic-team request supplies the stage order and explicit role model/effort instead of OMC's default tier routing. Spawn distinct named Planner, Executors, and both reviewers using the active native Agent/Task team surface, explicitly passing the full `model` ID and `effort`. Use a general-purpose teammate or a matching custom definition without conflicting settings. Claude Code 2.1.293+ supports this model set and invocation effort. Check whether `CLAUDE_CODE_EFFORT_LEVEL`, forced subagent models, or organization limits override the requested values; do not unset user settings to bypass them. Honor native-team enablement and the installed skill's genuine lifecycle preconditions; if the native route is unavailable, report BLOCKED rather than replacing it with ordinary subagents.
- Never encode the model only in the prompt. If an exact model/effort cannot be selected, stop before implementation and report the specific limitation. Inspect effective settings when the host exposes them; distinguish a requested setting from an observed setting and report any mismatch. A mismatch is not a successful stage.
- Respect available concurrency. Queue roles when needed; never drop a reviewer or reduce effort to fit capacity. Ralplan's Architect/Critic helpers, when needed, are planning roles and use the Planner model/effort unless the user specifies otherwise. The leader can dispatch these helpers on the Planner's behalf when nested native agents are unavailable.

Every child brief includes: original request and latest amendments, applicable project instructions, working directory, role/model/effort, implementation area (Frontend, Backend, Shared/Integration, or Other), owned resources, inputs/dependencies, expected deliverable, validation policy, communication targets, the blocker recovery and reply-driven coordination rules below, and escalation boundaries. Tell Executors they share the codebase, must preserve others' edits, and must request ownership changes through the leader. Children do not launch another basic-team workflow.

## Main-session ELI5 briefings and shared HTML progress page

Load `eli5` in the main session. Use it to explain progress and implementation decisions with familiar words, a concrete analogy when helpful, big pictures, and few words in an HTML artifact, as the installed skill requires. Maintain **one HTML progress page per basic-team run**, at a stable path, instead of producing a new page for each update. Choose a task artifact location permitted by the project, and keep it out of the product change unless the user asks to include it. Use a standalone HTML file with inline styles/diagrams; it must open locally without a build, server, or external assets.

Organize the page into major-domain **tabs**: **Plan**, **Agent Progress**, **Reviews & Validation**, and **Decisions & Blockers**, with labels in the user's language. Keep the goal, current stage, overall blockers, and last updated time visible above all tabs. Put the plan/allocation diagram in Plan, each agent's latest report in Agent Progress, verdicts/evidence in Reviews & Validation, and decision history/required input in Decisions & Blockers. Use visible tab labels, keyboard-accessible controls, and a clear active tab; preserve the selected tab across refreshes when local browser storage is available. All panels and their data stay in the same file; inline tab-switching code needs no network or polling.

Include across these tabs:

- Overall goal, current stage, last updated time, and a simple Planner -> Frontend/Backend Executors -> two Reviewers diagram. Show only the areas needed for this task.
- The current plan: task allocation, dependencies, acceptance criteria, and short explanations of decisions. Show parallel task branches within Frontend/Backend and which tasks are ready or awaiting prerequisites. Mark a draft as draft and distinguish approved plan revisions.
- One row/card for each assigned agent, including planning helpers: name, role, Frontend/Backend or other area, selected model/effort and observation status, owned task/files, latest reported status/time, completed work, next step, and blocker if any. Distinguish not launched, queued, working, waiting, blocked, and finished using actual reports; do not invent completion percentages or treat silence as failure.
- Review round, reviewed revision, both verdicts, unresolved findings, and validation evidence/gaps. Publish verdicts only after both independent reviews are collected; while waiting, show review progress without exposing the first verdict. Mark previous verdicts as superseded when product edits invalidate them.
- A short record of consequential decisions and changes, plus what happens next. Summarize reported plans/results rather than copying internal conversations or private reasoning.

The main session is the sole writer of this page. Children report factual checkpoints through the existing communication surface when they finish a planning/implementation milestone, change scope or dependencies, encounter a blocker, or complete a review; they do not edit the HTML. Update it when those reports arrive and at stage transitions, combining reports already received into one update and using safely escaped text for reported content. Do not solicit agent status or rewrite the file on a timer to keep the page looking active. The page is a view of observed workflow evidence, not task-lifecycle authority or a continuous live feed; keep last-report times visible so stale information is clear. Users can reopen/refresh the same file to see saved updates.

Brief the user at kickoff, after the plan, on consequential decisions or blockers, after each review round, and at completion. Provide a clickable artifact link/path at kickoff and completion, including through any artifact surface the host supports. Accompany updates with short visible text so the user need not open the page to know the current status. Answer: what we are doing, why this decision, what changed, and what comes next. Preserve exact technical facts; mark assumptions and unverified claims.

## 1. Planner

Assign planning before any implementation. The Planner loads the installed host's **ralplan** and applies its planning method inside this native workflow; use **plan** only when ralplan is absent. Return the plan to this leader instead of handing execution to `ultragoal`, `team`, or `ralph`.

For ralplan-based planning, produce its principles, decision drivers, alternatives/tradeoffs, and decision record; conduct its Planner -> Architect -> Critic review/revision procedure using native agents. Preserve the installed method's review ordering and rules about what each reviewer receives. The leader dispatches helpers with the Planner model/effort and explicit planning briefs when the Planner cannot spawn them. Require an approved execution-ready plan; a single draft is insufficient.

This is **ralplan-based native planning**, not an invocation of the OMX/OMC consensus runtime: do not run `omx ralplan run`, write runtime-owned consensus state, claim a runtime gate passed, or fabricate host role-routing authority. Report the applied method and actual native review evidence. If the user explicitly requests the full ralplan runtime, follow its supported runtime entrypoint and preconditions separately. Existing user authorization controls implementation; planning artifacts do not grant additional authority.

The plan identifies requirements and acceptance criteria, evidence and affected files, dependencies, risks and alternatives, implementation areas with exclusive ownership, shared contracts, and allowed validation. Resolve repository facts by inspection. Investigate material ambiguities using the blocker recovery procedure below, then ask through the leader when a consequential decision remains; do not add approval rounds for routine choices already authorized.

### Frontend / Backend work allocation

Inspect the repository's actual boundaries before classifying work; a file's directory or framework alone does not establish its responsibility. Explicitly state whether the request needs Frontend, Backend, both, or neither. Mark an unaffected area as not needed rather than creating work for it.

- **Frontend:** user interface, browser/client behavior, client state, and API consumption.
- **Backend:** server/API behavior, authentication/authorization enforcement, business logic, persistence, and migrations.
- **Shared/Integration:** contracts, shared types, or wiring used by both areas; assign each shared file to one named owner.
- **Other:** work outside these areas, such as standalone tooling or documentation; state its actual responsibility.

Include a work allocation table with task ID, area, owned files/resources, named Executor, prerequisite task IDs/shared contract, and acceptance criteria. Split work spanning Frontend and Backend into separate deliverables and assigned Executors; all use the existing Executor model/effort. Define their API/data contract (inputs, outputs, errors, and authentication expectations as applicable) before dispatch, and assign integration responsibility explicitly. Record which work can proceed against the agreed contract and which must wait for a prerequisite.

### Parallel decomposition within each area

The Planner explicitly looks for independent work **inside Frontend and inside Backend**, as well as across them. Split substantial independent features, components, endpoints, services, or jobs into deliverables with separate Executors when their files/resources and contracts permit concurrent implementation. Do not stop decomposition at one Frontend task and one Backend task.

For each task, identify its prerequisites and whether it can start now, after contract approval, or only after another task completes. Produce a dependency graph or equivalent prerequisite table, identify the tasks controlling completion, and propose the Executor allocation for the host's available capacity. Give each parallel task exclusive write ownership and observable completion criteria; shared files/resources require a single owner and explicit handoff. Explain any remaining serial work using actual dependencies, overlapping writes, or coordination cost. Do not manufacture parallelism by splitting tiny edits or speculating about repository boundaries.

The leader dispatches all ready independent tasks up to available capacity, including multiple Frontend and multiple Backend Executors when useful. Queue additional ready tasks and release them when a slot becomes available or a prerequisite result arrives. Completion does not necessarily free a host agent slot: reuse a compatible idle Executor with the new task brief, or release this workflow's idle agents only through supported controls before spawning replacements. Avoid whole-area barriers: an unrelated Backend task need not wait for all Frontend tasks, and a dependent task starts as soon as its own prerequisites are satisfied. Adjust allocation when reported scope/dependency changes affect the plan; preserve ownership and the agreed contracts.

The leader checks the plan covers the request and ownership boundaries, briefs the user via eli5 with the Frontend/Backend allocation, and dispatches only execution-ready areas.

## 2. Executors

Run independent tasks within and across areas in parallel; run dependent tasks after their prerequisites. Each Executor owns its assigned task/files, not the entire Frontend or Backend area. One Executor owns a shared file at a time. Assign any integration edits explicitly. Keep the original diff baseline, including pre-existing user changes, so reviews can distinguish task edits from unrelated work.

Each Executor confirms its assigned area and owned files before editing, implements within that boundary, and labels its report with the area. Frontend Executors consume the agreed contract; Backend Executors implement it. Shared/Integration owners coordinate changes affecting both. If work requires another area's files or a contract change, report it before editing; the leader reassigns ownership, coordinates dependent Executors, and returns material plan changes to the Planner.

Executors implement their areas, follow the agreed contracts, and return changed files, validation evidence, assumptions, and blockers. Report cross-area impact immediately; the leader resolves ownership and relays contract changes. Run or add tests only when the user's instructions authorize them. When validation is unavailable, report the gap instead of claiming it passed.

## 3. Two independent senior reviews

Wait for all implementation/integration edits to finish. Identify the exact reviewed revision using the baseline and current diff/content digest, or an isolated snapshot when appropriate. Freeze task edits during review. Give both reviewers the same request, plan, acceptance criteria, full diff, relevant files, and validation evidence. Each reviewer receives only its own required review skill; do not provide the other reviewer's verdict or the author's self-approval before its independent verdict.

- **Karpathy Agent:** load `lukas-plugin:karpathy-guidelines`. Review assumptions, requirement coverage, simplicity, surgical scope, and observable success criteria.
- **Ponytail Senior Agent:** load `ponytail:ponytail` at **full** level. Review the smallest complete solution, reuse, affected callers/configuration, edge cases, error handling, and missing evidence. End the review with unchecked areas and remaining risks as that skill requires.

Both reviewers also check correctness, regressions, completion of the assigned Frontend/Backend deliverables, and compatibility across their shared contract when both are involved. Reviewers do not edit product files or apply fixes. They inspect actual files and return:

```text
Reviewer: Karpathy Agent | Ponytail Senior Agent
Reviewed revision: <baseline and content/diff identity>
Verdict: PASS | CHANGES_REQUIRED | BLOCKED
Findings: <severity, file:line, impact, required fix; or none>
Evidence and unchecked areas: <what was examined and what remains unknown>
```

`PASS` means the request and acceptance criteria are met, required validation has evidence, and no required finding remains. A partial, missing, failed, or unverifiable review is not PASS. Advisory improvements outside the request do not expand scope; state them separately.

## 4. Continue until both PASS

On Claude, these continuation and stop rules override OMC team's default `max_fix_loops` retry ceiling for a new basic-team run. Do not invent or reset existing lifecycle counters to bypass a mandatory runtime cap; if such a cap prevents further work, report BLOCKED with the remaining findings.

The leader collects both independent reviews, reconciles conflicting findings against the request and evidence, and assigns required fixes to the owning Executors. Do not bypass an unresolved finding by overruling a reviewer and declaring PASS. Scope or contract changes go back through the Planner when necessary.

After fixes and allowed validation, freeze the new revision and obtain fresh verdicts from **both** reviewers. Any product edit invalidates earlier PASS verdicts. Continue implementation, review, and fixes until Karpathy Agent **and** Ponytail Senior Agent both return `PASS` for the same final revision. One PASS, a self-review, elapsed time, or an iteration count cannot complete the task.

If missing credentials/permissions, unsupported tooling, irreconcilable requirements, or other obstacles still prevent progress after supported investigation and recovery below, report **BLOCKED**, the unresolved findings, and the needed input. Ask the user when their answer can resolve the blocker. Never call a blocked task complete. Honor user cancellation and explicit budgets; they are not reviewer PASS.

## Investigate blockers, then ask when needed

Apply this at planning, implementation, integration, and review stages, within each role's existing authority. Reviewers remain read-only and independent; they report evidence and proposed remedies to the leader, who assigns fixes after both verdicts are collected.

1. **Establish the problem.** Identify the affected task, observed failure or missing decision, its impact, and what evidence would distinguish likely causes. Report the blocker and intended investigation to the leader once so unrelated work can continue; a recoverable obstacle is not an automatic workflow stop.
2. **Investigate autonomously.** Inspect relevant code/callers, project instructions, configuration, existing patterns, dependency versions, and available error/log evidence. Consult official/upstream documentation when external behavior or current compatibility matters. Use allowed diagnostics/validation; do not add or run tests without authorization. Prefer bounded, targeted investigation over repeated broad searches, new agents for every issue, or retries of the same failed action without new evidence.
3. **Choose a reasonable remedy.** Compare viable options against the user's requirements, correctness, existing architecture, compatibility, change scope, and coordination cost. Select the smallest complete solution supported by evidence and apply already authorized, reversible changes within the assigned ownership. Report the rationale and verify the affected behavior using allowed checks. The leader handles ownership changes and returns material contract/scope changes to the Planner. Do not silently substitute required models/skills, weaken review gates, bypass permissions, or expand scope to remove a blocker.
4. **Ask for the missing decision.** If investigation leaves materially different outcomes, an unresolved product requirement, missing access/information, or an action needing user authorization, the main session asks the user a concise question. Include what was investigated, the remaining decision, a recommended option with its reason, and alternatives/tradeoffs when useful. Prefer the host's available structured question tool; otherwise ask one clear plain-text question and wait for the answer. Do not ask the user to investigate repository facts that the agents can obtain or reconfirm routine authorized work.
5. **Resume on the answer.** Record the question and recommendation in the HTML Decisions & Blockers tab and mark affected tasks as waiting for user input. Continue unaffected work; keep dependent work paused until the actual answer or required authority arrives. Time elapsed, a preselected option, or silence is not approval. The leader updates the plan/contracts as needed and resumes the affected Planner, Executor, or Reviewer through supported host controls with the decision and changed inputs once. If no meaningful recovery remains, state the specific BLOCKED condition and required input; do not keep retrying without new evidence or claim completion.

Keep investigation notes concise: evidence/cause, options considered, chosen remedy or open question, validation, and resulting next action. Update the progress page on these meaningful events through the leader; do not turn investigation or user-question waiting into polling.

## Communication and completion

### Reply-driven coordination and token use

Advance work on actual incoming replies, completion notifications, and dependency changes. Do not run periodic status/mailbox/task-list/file checks, send repeated "are you done?" messages, or create sleep-and-check loops. These rules govern the agents' orchestration; do not claim they eliminate any polling internal to the host runtime.

- Dispatch each ready task once with its dependencies and expected reply. Keep a small leader-owned record of assigned tasks, outstanding questions, and received outcomes in the current session. On a completion/capacity notification or prerequisite reply, dispatch the newly ready work that fits the available slots; do not poll for capacity or wait for unrelated tasks to finish. Release dependent work only when the required successful result/approved contract arrives; silence or a timeout cannot satisfy a prerequisite. Keep both-reviewer and final-revision gates intact.
- Send concise replies for completion, required decisions, blockers, contract changes, and useful milestones. Include the task and revision/round when applicable, what changed, evidence/artifact paths, and the next action or specific question. Send the necessary result once through the host's completion surface or a targeted message; do not duplicate the full report in both, broadcast it to unrelated peers, or require extra acknowledgements unless the native lifecycle requires them.
- When a child needs an answer, ask the responsible agent or leader once. Continue independent assigned work if available; otherwise enter the host's supported wait/idle state. The leader resumes that work when the answer arrives. A question awaiting a reply is waiting, not proof that the entire workflow is BLOCKED. Do not keep the model reasoning or emitting "still waiting" turns.
- When the leader has no ready work, use native notification delivery or a blocking event wait that wakes on messages, completions, or user input. Prefer a substantial wait within the host's responsiveness/tool limits over many short waits. If a bounded wait expires without an event, re-arm the supported event wait without status queries or reminder messages; do not retry the task or infer failure. User-facing updates required by the host may summarize the last known state without probing agents.
- Use status/task inspection only to establish initial routing, verify a required lifecycle transition, answer an explicit user request, or diagnose concrete failure evidence. Scope recovery to the affected task; do not turn a diagnostic check into recurring polling. If the host cannot deliver replies or provide a supported wait/resume path, report that capability blocker instead of inventing a polling loop.
- Consume each outcome once: a duplicate notification must not dispatch the same dependent task or repeat a dashboard update. Resume an existing Executor for required fixes with only the changed requirements, revision, findings, and relevant artifact paths. Preserve required initial briefs and review inputs; reduce repeated coordination text, not review coverage or model settings.

On Codex's current collaboration surface, agents can directly `send_message` to the leader and peers by the returned agent path/task name. Provide known peer addresses in briefs or follow-up messages. Use `send_message` for a running agent and `followup_task` to deliver new work or resume an idle agent; `send_message` alone does not start an idle agent's turn. Collect pushed results through `wait_agent` when no independent work remains; do not loop over `list_agents`. If peer messaging is unavailable, the leader relays necessary questions and answers once.

On Claude, use the installed team skill's actual native teammate messaging, incoming notifications, and idle/resume behavior for leader/peer coordination, with its required task lifecycle for assignments. Resolve teammate names/addresses from the real team surface; do not fabricate `TeamCreate`, `TeamDelete`, or `SendMessage` calls from older documentation. Do not add repeated task-list/mailbox reads around native message delivery. If required native messaging is unavailable, report the team capability blocker. During independent review, route review coordination through the leader on both hosts; share review feedback with Executors only after both verdicts are collected.

Complete only after both final PASS verdicts, the leader's integration check, and no pending worker writes. Brief the user via eli5 with delivered behavior, decisions, model/effort selection and observation status, both verdicts, validation evidence, and remaining gaps. On Claude, finish the team skill's native shutdown and acknowledgements; on Codex, terminate only this workflow's active agents using supported controls when needed. Leave unrelated agents and harness state alone.

## Host references

- [OpenAI native subagents and custom roles](https://developers.openai.com/codex/subagents)
- [Claude subagent model and effort selection](https://code.claude.com/docs/en/sub-agents)
