# Planning, execution, review, and exit contracts

Load the relevant section at its runbook stage. Host operations are in the host reference linked directly from SKILL.md.

## 1. Planner

Assign planning before any implementation. The Planner loads the installed host's **ralplan** and applies its planning method inside this native workflow; use **plan** only when ralplan is absent. The planning teammate returns its approved plan to the current leader; it does not start another team or hand execution to `ultragoal` or `ralph`. On Claude, the current leader continues through the already invoked team skill.

For ralplan-based planning, produce its principles, decision drivers, alternatives/tradeoffs, and decision record; conduct its Planner -> Architect -> Critic review/revision procedure using native agents. Preserve the installed method's review ordering and rules about what each reviewer receives. The leader always dispatches Architect then Critic with the Planner model/effort and their dedicated briefs. The Critic receives the same plan revision and Architect assessment; the Planner does not spawn helpers. Require an approved execution-ready plan; a single draft is insufficient.

Before implementation, verify the Planner received the resolved ralplan/plan SKILL.md path and, for Frontend, the Impeccable base path. Record actual Architect/Critic review evidence for ralplan; team invocation cannot replace it. If ralplan is absent, disclose the permitted plan fallback. Any other omitted planning/review step needs the specific user exception or a BLOCKED report; never describe an unreviewed draft as consensus-approved.

This is **ralplan-based native planning**, not an invocation of the OMX/OMC consensus runtime: do not run `omx ralplan run`, write runtime-owned consensus state, claim a runtime gate passed, or fabricate host role-routing authority. Report the applied method and actual native review evidence. If the user explicitly requests the full ralplan runtime, follow its supported runtime entrypoint and preconditions separately. Existing user authorization controls implementation; planning artifacts do not grant additional authority.

The plan identifies requirements and acceptance criteria, evidence and affected files, dependencies, risks and alternatives, implementation areas with exclusive ownership, shared contracts, and allowed validation. Resolve repository facts by inspection. Investigate material ambiguities using the blocker recovery procedure below, then ask through the leader when a consequential decision remains; do not add approval rounds for routine choices already authorized.

### Frontend / Backend work allocation

Inspect the repository's actual boundaries before classifying work; a file's directory or framework alone does not establish its responsibility. Explicitly state whether the request needs Frontend, Backend, both, or neither. Mark an unaffected area as not needed rather than creating work for it.

- **Frontend:** user interface, browser/client behavior, client state, and API consumption.
- **Backend:** server/API behavior, authentication/authorization enforcement, business logic, persistence, and migrations.
- **Shared/Integration:** contracts, shared types, or wiring used by both areas; assign each shared file to one named owner.
- **Other:** work outside these areas, such as standalone tooling or documentation; state its actual responsibility.

Include a work allocation table with task ID, area, owned files/resources, named Executor, prerequisite task IDs/shared contract, and acceptance criteria. Split work spanning Frontend and Backend into separate deliverables and assigned Executors; all use the existing Executor model/effort. Define their API/data contract (inputs, outputs, errors, and authentication expectations as applicable) before dispatch, and assign integration responsibility explicitly. Record which work can proceed against the agreed contract and which must wait for a prerequisite.

### Conditional rules

Read [conditional-reviews.md](conditional-reviews.md) now when any of these applies, and give the child the relevant section's path in its brief `skills` list:

- **Frontend planning or UI changes:** the "Impeccable guidance for Frontend planning" section, and for the Impeccable reviewer the critique helpers section. Activate the Impeccable reviewer for new or redesigned UI or visible layout, typography, color, navigation, interaction, or responsive changes, or when the user asks for design evaluation; the leader confirms from the actual scope and re-evaluates on scope changes, and never deactivates it to bypass a finding.
- **Connected behavior across screens, client/server/persistence, authentication, or jobs, or a user request for E2E:** the "E2E review planning" section. File count alone is not a trigger.
- **A diff that adds or changes an external library API or dependency version:** the "Conditional library documentation checks" section, for the Karpathy and Ponytail reviewers.

### Parallel decomposition within each area

The Planner explicitly looks for independent work **inside Frontend and inside Backend**, as well as across them. Split substantial independent features, components, endpoints, services, or jobs into deliverables with separate Executors when their files/resources and contracts permit concurrent implementation. Do not stop decomposition at one Frontend task and one Backend task.

For each task, identify its prerequisites and whether it can start now, after contract approval, or only after another task completes. Produce a dependency graph or equivalent prerequisite table, identify the tasks controlling completion, and propose the Executor allocation for the host's available capacity. Give each parallel task exclusive write ownership and observable completion criteria; shared files/resources require a single owner and explicit handoff. Explain any remaining serial work using actual dependencies, overlapping writes, or coordination cost. Do not manufacture parallelism by splitting tiny edits or speculating about repository boundaries.

The leader dispatches all ready independent tasks up to available capacity, including multiple Frontend and multiple Backend Executors when useful. Queue additional ready tasks and release them when a slot becomes available or a prerequisite result arrives. Completion does not necessarily free a host agent slot: reuse a compatible idle Executor with the new task brief, or release this workflow's idle agents only through supported controls before spawning replacements. Avoid whole-area barriers: an unrelated Backend task need not wait for all Frontend tasks, and a dependent task starts as soon as its own prerequisites are satisfied. Adjust allocation when reported scope/dependency changes affect the plan; preserve ownership and the agreed contracts.

The leader checks the plan covers the request and ownership boundaries, briefs the user via eli5 with the Frontend/Backend allocation, and dispatches only execution-ready areas.

### Task list and stage handoffs

On Claude, complete the invoked team skill's task-list phase (Phase 4 when named that way) through its native task surface before implementation. On Codex, retain the leader-owned task/allocation record. Each task needs an ID, owner, prerequisites, acceptance criteria, and observed status; the HTML view does not replace the native task list.

Group the approved allocation into named Phases and publish the HTML `tasks` checklist with `taskPlanRevision` identifying that plan. Reuse task IDs and owners in dispatch and reports; keep dependencies, ownership boundaries, and acceptance criteria in the existing plan/task record. Include integration, required review/validation, and cleanup. Phases are display groups, not whole-team barriers: dispatch follows each task's prerequisites. The leader updates the full snapshot from observed results, marks `done` only with acceptance evidence, and reopens invalidated tasks with current evidence. Reconcile the checklist after an approved plan change. Keep early independent review outcomes out of TODO statuses/evidence. Cleanup TODOs may remain open at `ready`; all TODOs must be done at `complete`.

Stage handoff records are required in the progress HTML’s embedded `handoffs` JSON array. Use [../assets/stage-handoff-template.md](../assets/stage-handoff-template.md) for each transition below, append a unique record ID, and preserve previous rounds. This is the single handoff source for both hosts: do not export a new MD at every transition. If the user or invoked host workflow explicitly requires an external handoff artifact, reference the existing artifact instead of duplicating its content. Retain the approved plan, independent planning review artifacts, and original validation evidence as needed; the HTML references their exact identities. Native task state remains the actual host lifecycle source, not the HTML.

| Transition | Required artifacts before release | Completion check |
| --- | --- | --- |
| Planning -> implementation | Approved plan/allocation and contracts, ralplan review evidence or permitted fallback, native/leader task record, settings records satisfying the run’s observation policy, handoff | Each ready task has an owner, prerequisites, acceptance criteria, minimum validation commands, and a cleared settings gate. |
| Implementation -> verification | Executor/integration reports and changed-file list, frozen revision, validation results/gaps, required reviewer/scenario list, handoff | Edits stopped; review inputs and test evidence identify the same revision. |
| Verification -> fixes/recovery | Complete independent review set, findings or tool blocker evidence, assigned fixes or recovery action, handoff | Product fixes follow demonstrated findings; a tool-only blocker remains BLOCKED pending recovery. |
| Fixes -> verification | Fix report, new frozen revision, fresh affected-check results, superseded prior verdicts, handoff | Every required reviewer receives the new revision; earlier tests cannot cover later edits. |
| Final completion | Final validation results and all required PASS verdicts, reconciled tasks, shutdown/state and cleanup evidence, final page receipt, completion handoff | No unresolved required item, pending write, or unsaved update remains. |

The leader reads each saved handoff with `handoffs PAGE --id ID` and checks the transition requirements against its evidence before dependent dispatch. Missing artifacts or unchecked required items stop that transition; mark genuinely inapplicable items with a reason and omissions with the specific user exception. Identify records as `<absolute-page-path>#handoff-<id>` in briefings and `gates.evidence.tasks`; a helper `ok` cannot waive these checks. Reference existing page fields and source artifacts rather than copying every report or settings table into each handoff. Preserve pending updates and outstanding IDs on compaction/resume. Use supported team operations for runtime state; handoff artifacts do not authorize writes to hook-owned state.

## 2. Executors

Run independent tasks within and across areas in parallel; run dependent tasks after their prerequisites. Each Executor owns its assigned task/files, not the entire Frontend or Backend area. One Executor owns a shared file at a time. Assign any integration edits explicitly. Keep the original diff baseline, including pre-existing user changes, so reviews can distinguish task edits from unrelated work.

Each Executor confirms its assigned area and owned files before editing, implements within that boundary, and labels its report with the area. Frontend Executors consume the agreed contract; Backend Executors implement it. Shared/Integration owners coordinate changes affecting both. If work requires another area's files or a contract change, report it before editing; the leader reassigns ownership, coordinates dependent Executors, and returns material plan changes to the Planner.

Executors implement their areas, follow the agreed contracts, and return changed files, validation evidence, assumptions, and blockers. Report cross-area impact immediately; the leader resolves ownership and relays contract changes. Run or add tests only when the user's instructions authorize them. When validation is unavailable, report the gap instead of claiming it passed.

## 3. Independent reviews

Wait for all implementation/integration edits to finish. Identify the exact reviewed revision using the baseline and current diff/content digest, or an isolated snapshot when appropriate. Freeze task edits during review. Give all required reviewers the same request, plan, acceptance criteria, full diff, relevant files, and validation evidence; additionally give Impeccable reviewer the design brief and affected UI targets. Each reviewer receives only its own required review skill; do not provide another reviewer's verdict or the author's self-approval before its independent verdict.

- **Karpathy Agent:** load `lukas-plugin:karpathy-guidelines`. Review assumptions, requirement coverage, simplicity, surgical scope, and observable success criteria.
- **Ponytail Senior Agent:** load `ponytail:ponytail` at **full** level. Review the smallest complete solution, reuse, affected callers/configuration, edge cases, error handling, and missing evidence. End the review with unchecked areas and remaining risks as that skill requires.
- **E2E reviewer (conditional):** follow [e2e-review.md](e2e-review.md). Independently validate the planned connected flows on the frozen implementation and report observed outcomes, failures, and unchecked boundaries. Receive the scenario plan, environment, fixtures, and browser readiness from the leader in addition to the common review inputs.
- **Impeccable reviewer (conditional):** load `impeccable` and evaluate the Frontend Executors' delivered design against the user's brief and Planner's criteria. Follow its context setup once in this reviewer's session and the installed `reference/critique.md` evaluation procedure. Inspect the affected UI/source and available current visual evidence; assess hierarchy, layout, typography, color, consistency, cognitive load, interaction/state clarity, responsiveness, and accessibility. Preserve the intended design direction and distinguish required defects from optional taste/polish.

The two mandatory reviewers also check correctness, regressions, completion of the assigned Frontend/Backend deliverables, and compatibility across their shared contract when both are involved. All reviewers remain read-only on product files and do not apply fixes. They inspect actual files and return:

```text
Reviewer: Karpathy Agent | Ponytail Senior Agent | Impeccable reviewer | E2E reviewer
Reviewed revision: <baseline and content/diff identity>
Verdict: PASS | CHANGES_REQUIRED | BLOCKED
Findings: <severity, file:line, impact, required fix; or none>
Evidence and unchecked areas: <what was examined and what remains unknown>
```

`PASS` means the request and acceptance criteria are met, required validation has evidence, and no required finding remains. A partial, missing, failed, or unverifiable review is not PASS. Advisory improvements outside the request do not expand scope; state them separately.

## 4. Continue until all required reviewers PASS

On Claude, these continuation and stop rules override OMC team's default `max_fix_loops` retry ceiling for a new basic-team run. Do not invent or reset existing lifecycle counters to bypass a mandatory runtime cap; if such a cap prevents further work, report BLOCKED with the remaining findings.

The leader collects all required independent reviews, reconciles conflicting findings against the request and evidence, and assigns required fixes to the owning Executors, including Frontend design fixes. Do not bypass an unresolved finding by overruling a reviewer and declaring PASS. Scope or contract changes go back through the Planner when necessary.

After fixes and allowed validation, freeze the new revision and obtain fresh verdicts from **all required** reviewers. Any product edit invalidates earlier PASS verdicts. Continue implementation, review, and fixes until Karpathy Agent **and** Ponytail Senior Agent, plus **Impeccable and E2E reviewers when activated**, return `PASS` for the same final revision. One PASS, a self-review, elapsed time, or an iteration count cannot complete the task.

### Minimum validation on the final revision

The Planner names the smallest allowed checks that prove the acceptance criteria and the affected boundaries. Use targeted tests for changed behavior and affected callers; include lint/typecheck/build or connected-flow checks only where the change or project policy requires them. For instructions/templates, validate their format, links, rendered briefs, and affected helper behavior. Record exact command, checked revision, exit code, result/evidence, and unchecked scope. Required project checks remain required.

After any later edit, including review fixes, refactoring, formatting, or final cleanup, rerun the checks affected by that edit; supersede earlier results for those checks. A progress-page/handoff-only save does not invalidate product tests. After all required reviewers PASS and the final revision is verified, finish the required shutdown/cleanup/save steps once; do not repeat temporary-file, status, or test checks without a new edit, failure, explicit user request, or required lifecycle transition. Final reporting distinguishes `passed`, `failed`, `not run`, and `superseded`; never describe an earlier revision's test as final evidence.

If missing credentials/permissions, unsupported tooling, irreconcilable requirements, or other obstacles still prevent progress after supported investigation and recovery below, report **BLOCKED**, the unresolved findings, and the needed input. Ask the user when their answer can resolve the blocker. Never call a blocked task complete. Honor user cancellation and explicit budgets; they are not reviewer PASS.

## Investigate blockers, then ask when needed

Apply this at planning, implementation, integration, and review stages, within each role's existing authority. Reviewers remain read-only and independent; they report evidence and proposed remedies to the leader, who assigns fixes after all required verdicts are collected.

1. **Establish the problem.** Identify the affected task, observed failure or missing decision, its impact, and what evidence would distinguish likely causes. Report the blocker and intended investigation to the leader once so unrelated work can continue; a recoverable obstacle is not an automatic workflow stop.
2. **Investigate autonomously.** Inspect relevant code/callers, project instructions, configuration, existing patterns, dependency versions, and available error/log evidence. Consult official/upstream documentation when external behavior or current compatibility matters. Use allowed diagnostics/validation; do not add or run tests without authorization. Prefer bounded, targeted investigation over repeated broad searches, new agents for every issue, or retries of the same failed action without new evidence.
3. **Choose a reasonable remedy.** Compare viable options against the user's requirements, correctness, existing architecture, compatibility, change scope, and coordination cost. Select the smallest complete solution supported by evidence and apply already authorized, reversible changes within the assigned ownership. Report the rationale and verify the affected behavior using allowed checks. The leader handles ownership changes and returns material contract/scope changes to the Planner. Do not silently substitute required models/skills, weaken review gates, bypass permissions, or expand scope to remove a blocker.
4. **Ask for the missing decision.** If investigation leaves materially different outcomes, an unresolved product requirement, missing access/information, or an action needing user authorization, the main session asks the user a concise question. Include what was investigated, the remaining decision, a recommended option with its reason, and alternatives/tradeoffs when useful. Prefer the host's available structured question tool; otherwise ask one clear plain-text question and wait for the answer. Do not ask the user to investigate repository facts that the agents can obtain or reconfirm routine authorized work.
5. **Resume on the answer.** Record the question and recommendation in the HTML Decisions & Blockers tab and mark affected tasks as waiting for user input. Continue unaffected work; keep dependent work paused until the actual answer or required authority arrives. Time elapsed, a preselected option, or silence is not approval. The leader updates the plan/contracts as needed and resumes the affected Planner, Executor, or Reviewer through supported host controls with the decision and changed inputs once. If no meaningful recovery remains, state the specific BLOCKED condition and required input; do not keep retrying without new evidence or claim completion.

Keep investigation notes concise: evidence/cause, options considered, chosen remedy or open question, validation, and resulting next action. Update the progress page on these meaningful events through the leader; do not turn investigation or user-question waiting into polling.

## Communication and completion

### Reply-driven coordination and token use

Advance work on actual incoming replies, completion notifications, and dependency changes. Do not run periodic status/mailbox/task-list/file checks, send repeated "are you done?" messages, or create sleep-and-check loops. These rules govern the agents' orchestration; do not claim they eliminate any polling internal to the host runtime.

- Dispatch each ready task once with its dependencies and expected reply. Keep a small leader-owned record of assigned tasks, outstanding questions, and received outcomes in the current session. On a completion/capacity notification or prerequisite reply, dispatch the newly ready work that fits the available slots; do not poll for capacity or wait for unrelated tasks to finish. Release dependent work only when the required successful result/approved contract arrives; silence or a timeout cannot satisfy a prerequisite. Keep all-required-reviewer and final-revision gates intact.
- Send concise replies for completion, required decisions, blockers, contract changes, and useful milestones. Include the task and revision/round when applicable, what changed, evidence/artifact paths, and the next action or specific question. Send the necessary result once through the host's completion surface or a targeted message; do not duplicate the full report in both, broadcast it to unrelated peers, or require extra acknowledgements unless the native lifecycle requires them.
- When a child needs an answer, ask the responsible agent or leader once. Continue independent assigned work if available; otherwise enter the host's supported wait/idle state. The leader resumes that work when the answer arrives. A question awaiting a reply is waiting, not proof that the entire workflow is BLOCKED. Do not keep the model reasoning or emitting "still waiting" turns.
- When the leader has no ready work, use native notification delivery or a blocking event wait that wakes on messages, completions, or user input. Prefer a substantial wait within the host's responsiveness/tool limits over many short waits. If a bounded wait expires without an event, re-arm the supported event wait without status queries or reminder messages; do not retry the task or infer failure. User-facing updates required by the host may summarize the last known state without probing agents.
- Use status/task inspection only to establish initial routing, verify a required lifecycle transition, answer an explicit user request, or diagnose concrete failure evidence. Scope recovery to the affected task; do not turn a diagnostic check into recurring polling. If the host cannot deliver replies or provide a supported wait/resume path, report that capability blocker instead of inventing a polling loop.
- Consume each outcome once: a duplicate notification must not dispatch the same dependent task or repeat a dashboard update. Mark the outcome handled only after its required progress save succeeds; preserve pending updates across retries. Resume an existing Executor for required fixes with only the changed requirements, revision, findings, and relevant artifact paths. Preserve required initial briefs and review inputs; reduce repeated coordination text, not review coverage or model settings.

Use the current host reference for addresses, messages, resume, waits, and termination. Independent review coordination goes through the leader; send feedback to Executors only after all required verdicts arrive.

### Exit checklist and unresponsive teammates

Apply this on success, cancellation, and failure; cleanup does not make an incomplete task successful.

1. **Validation and reviews:** record allowed commands, exit codes, evidence, and unchecked scope on the final revision, plus all required independent verdicts and the integration result. Required tests must pass. A failing full suite, including pre-existing failures, cannot be reported as an all-green completion; distinguish baseline failures from regressions and report CHANGES_REQUIRED or BLOCKED until resolved or the user explicitly changes the acceptance scope. Tests not run, forbidden, or unverifiable are gaps, not passes. Reviewer PASS does not override a failed required check.
2. **Tasks and handoffs:** reconcile each assigned task with its real outcome, preserve unresolved work, and save all applicable handoff records in the same HTML. No pending worker writes may remain on a successful exit.
3. **Native shutdown (apply the current host reference):** request shutdown once for this run's teammates and wait within the invoked team's documented timeout. If none is defined, use one bounded 60-second event wait. A timeout records `응답 없음` with agent ID, request/time, and last known evidence; it does not prove exit. Diagnose that agent once, then use the host's supported scoped stop/recovery procedure when its authority and preconditions permit. Do not repeat shutdown requests indefinitely, fabricate an acknowledgement, delete state to hide a live worker, or stop unrelated agents. If exit cannot be verified, record cleanup BLOCKED and the exact recovery needed.
4. **Host lifecycle:** verify termination using the current host reference. Claude requires confirmed native team cleanup/inactive state; Codex uses its available agent lifecycle evidence, not Claude team-state files. Unverified termination remains BLOCKED; do not manually edit flags, delete unrelated state, or perform subsequent git mutations while cleanup is blocked.
5. **Browser/MCP and hook:** perform applicable cleanup from [e2e-review.md](e2e-review.md); request disarm for the retained exact hook run ID and report confirmed versus unavailable cleanup. If arm had no valid identity/receipt, disclose that gap rather than guessing an ID. Missing reminder support means manual checkpoint saves, as in [progress-updates.md](progress-updates.md).
6. **Final save and briefing:** after readiness and cleanup, save the completion handoff and reconciled final task record; record the native/leader task reference and HTML handoff ID/revision in `gates.evidence.tasks` with `status:"함"` and nonempty evidence. This final evidence is required by schema2/3 `complete`, not by the earlier `ready` gate; schema3 additionally checks the saved handoff’s transition, revision, outcome, and empty completion `pending` list. Save the observed final outcome, shutdown/state evidence, and all gaps to the same progress page; verify its receipt and leave no pending updates on success. Brief via eli5 with the clickable page link, absolute path, confirmed save time, delivered behavior, decisions, per-agent requested/invoked/observed settings, verdicts, validation, and cleanup. Before compaction/handoff, preserve the same recovery fields in the handoff record; resume using read-only `status` plus actual host evidence, not the saved stage as authority.

### Required final compliance table

Every final report, including BLOCKED/cancelled results, includes this table using `함 / 부분 / 안 함` and concrete evidence or a gap. A non-applicable conditional item uses `안 함 — 해당 없음` with its reason; an approved omission names the user's exception. The table reports behavior and never substitutes for it.

| Requirement | 함 / 부분 / 안 함 | Evidence, gap, or approved exception |
| --- | --- | --- |
| HTML progress page, final save, link/absolute path/save time | | |
| Hook arm/disarm and actual confirmation or manual fallback | | |
| eli5 kickoff, plan, progress/review/blocker, completion briefings | | |
| Per-call model/effort arguments, alias resolution evidence, requested/invocation/observed report | | |
| Planner skill paths, ralplan Architect/Critic evidence or permitted fallback | | |
| Native task list/allocation record and HTML stage handoff records | | |
| All required independent reviews on the final revision | | |
| Required validation/test outcomes and unmet criteria | | |
| Teammate shutdown, unresponsive-agent recovery, inactive team-state verification | | |
| Applicable browser/MCP cleanup and configuration boundary | | |

Use `complete` only when the required implementation, validation, reviews, progress saves, and shutdown/state checks all succeeded within the authorized scope. Otherwise name the actual outcome and unfinished requirement.


## Why this structure

These are design choices, not measured Haiku/Luna improvements. [Skill authoring guidance](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) motivates specific small-model instructions and one-hop conditional references. [Effective agents](https://www.anthropic.com/engineering/building-effective-agents) supports fixed workflows with programmatic checks; [context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) supports enough context at the needed stage instead of mere brevity. [Tool design](https://www.anthropic.com/engineering/writing-tools-for-agents) motivates actionable errors and call/cost measurement. [Agent evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) motivates repeated trials and independent final-outcome checks. Invocation-only versus host-observed runs must be reported separately; these sources do not prove exact host model/effort or authorize weakening strict runs.
