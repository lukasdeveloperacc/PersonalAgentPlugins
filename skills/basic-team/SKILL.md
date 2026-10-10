---
name: basic-team
description: Coordinate native Codex or Claude agents through planning, implementation by owned area, and independent Karpathy and Ponytail reviews until both pass. Use for a requested basic-team development workflow.
---

# Basic Team

The main session is the leader and the user's contact. Run one Planner, as many Executors as the independent implementation areas need, and two independent reviewers: **Karpathy Agent** and **Ponytail Senior Agent**. These are review personas, not claims that the named people reviewed the code.

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

Every child brief includes: original request and latest amendments, applicable project instructions, working directory, role/model/effort, implementation area (Frontend, Backend, Shared/Integration, or Other), owned resources, inputs/dependencies, expected deliverable, validation policy, communication targets, and escalation boundaries. Tell Executors they share the codebase, must preserve others' edits, and must request ownership changes through the leader. Children do not launch another basic-team workflow.

## Main-session ELI5 briefings

Load `eli5` in the main session. Use it to explain progress and implementation decisions with familiar words, a concrete analogy when helpful, big pictures, and few words in an HTML artifact, as the installed skill requires. Maintain one local briefing artifact instead of producing a new page for each update; use simple inline diagrams and avoid external assets or publishing. Choose a task artifact location permitted by the project, and keep it out of the product change unless the user asks to include it.

Brief the user at kickoff, after the plan, on consequential decisions or blockers, after each review round, and at completion. Accompany artifact updates with short visible text so the user need not open the artifact to know the current status. Answer: what we are doing, why this decision, what changed, and what comes next. Preserve exact technical facts; mark assumptions and unverified claims. Do not send every internal message to the user.

## 1. Planner

Assign planning before any implementation. The Planner loads the installed host's **ralplan** and applies its planning method inside this native workflow; use **plan** only when ralplan is absent. Return the plan to this leader instead of handing execution to `ultragoal`, `team`, or `ralph`.

For ralplan-based planning, produce its principles, decision drivers, alternatives/tradeoffs, and decision record; conduct its Planner -> Architect -> Critic review/revision procedure using native agents. Preserve the installed method's review ordering and rules about what each reviewer receives. The leader dispatches helpers with the Planner model/effort and explicit planning briefs when the Planner cannot spawn them. Require an approved execution-ready plan; a single draft is insufficient.

This is **ralplan-based native planning**, not an invocation of the OMX/OMC consensus runtime: do not run `omx ralplan run`, write runtime-owned consensus state, claim a runtime gate passed, or fabricate host role-routing authority. Report the applied method and actual native review evidence. If the user explicitly requests the full ralplan runtime, follow its supported runtime entrypoint and preconditions separately. Existing user authorization controls implementation; planning artifacts do not grant additional authority.

The plan identifies requirements and acceptance criteria, evidence and affected files, dependencies, risks and alternatives, implementation areas with exclusive ownership, shared contracts, and allowed validation. Resolve repository facts by inspection. Ask about a material ambiguity through the leader; do not add approval rounds for routine choices already authorized.

### Frontend / Backend work allocation

Inspect the repository's actual boundaries before classifying work; a file's directory or framework alone does not establish its responsibility. Explicitly state whether the request needs Frontend, Backend, both, or neither. Mark an unaffected area as not needed rather than creating work for it.

- **Frontend:** user interface, browser/client behavior, client state, and API consumption.
- **Backend:** server/API behavior, authentication/authorization enforcement, business logic, persistence, and migrations.
- **Shared/Integration:** contracts, shared types, or wiring used by both areas; assign each shared file to one named owner.
- **Other:** work outside these areas, such as standalone tooling or documentation; state its actual responsibility.

Include a work allocation table with task, area, owned files/resources, named Executor, dependencies/shared contract, and acceptance criteria. Split work spanning Frontend and Backend into separate deliverables and assigned Executors; both use the existing Executor model/effort. Define their API/data contract (inputs, outputs, errors, and authentication expectations as applicable) before dispatch, and assign integration responsibility explicitly. Record which work can proceed against the agreed contract and which must wait for a prerequisite.

The leader checks the plan covers the request and ownership boundaries, briefs the user via eli5 with the Frontend/Backend allocation, and dispatches only execution-ready areas.

## 2. Executors

Run independent areas in parallel; run dependent areas after their prerequisites. One Executor owns a shared file at a time. Assign any integration edits explicitly. Keep the original diff baseline, including pre-existing user changes, so reviews can distinguish task edits from unrelated work.

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

If credentials, permissions, unsupported tooling, irreconcilable requirements, or repeated attempts without a viable recovery path prevent progress, report **BLOCKED**, the unresolved findings, and the needed input. Never call a blocked task complete. Honor user cancellation and explicit budgets; they are not reviewer PASS.

## Communication and completion

On Codex's current collaboration surface, agents can directly `send_message` to the leader and peers by the returned agent path/task name. Use `followup_task` for new work on an idle agent and the exposed wait/status tools to collect results; a wait timeout is not a failure. Provide known peer addresses in briefs or follow-up messages. If peer messaging is unavailable, the leader relays questions and answers.

On Claude, use the installed team skill's actual native teammate messaging surface for leader/peer coordination and its task lifecycle for assignments. Resolve teammate names/addresses from the real team surface; do not fabricate `TeamCreate`, `TeamDelete`, or `SendMessage` calls from older documentation. If required native messaging is unavailable, report the team capability blocker. During independent review, route review coordination through the leader on both hosts; share review feedback with Executors only after both verdicts are collected.

Complete only after both final PASS verdicts, the leader's integration check, and no pending worker writes. Brief the user via eli5 with delivered behavior, decisions, model/effort selection and observation status, both verdicts, validation evidence, and remaining gaps. On Claude, finish the team skill's native shutdown and acknowledgements; on Codex, terminate only this workflow's active agents using supported controls when needed. Leave unrelated agents and harness state alone.

## Host references

- [OpenAI native subagents and custom roles](https://developers.openai.com/codex/subagents)
- [Claude subagent model and effort selection](https://code.claude.com/docs/en/sub-agents)
