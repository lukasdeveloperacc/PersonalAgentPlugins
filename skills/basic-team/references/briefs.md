# Briefs

Fill placeholders; link files instead of pasting whole logs. Read [team-contract.md](team-contract.md) first. Only root writes Office/HTML and addresses the user.

## Team lead

```text
You are <team>-lead, a peer child of root <parent>.
Load <team skill path> and its shared contract. Purpose: <execute/review>.
Workdir: <absolute path>. Scope/non-goals: <scope>. Plan: <path>.
Owned files: <files>. Criteria: <acceptance criteria>.
Checks: <exact commands>. Revision/base: <revision/base>.
Peers and agreed contracts: <identities/API/errors/dependencies>.
Acceptance matrix and startup/seed instructions: <matrix or none>.
Worker budget: <available allocation>. Artifact directory: <path>.
Identity: <canonical ID>; parent: <root ID>; native name: <host-valid ID> (root-spawned leads only).
Return your own and each leaf's requested/observed model and effort with evidence
(not needed on Claude Code, where root reads them directly);
mark missing observations unverified. Keep native IDs separate from Office owners.
For Frontend/Backend implementation: read/apply <resolved karpathy SKILL.md>
and <resolved ponytail SKILL.md>; preserve <active level>. Pass both exact
paths to each implementation worker and report missing skills to root.
These habits do not replace independent review.
Reporting: root <identity> owns <mode/run/page>; do not write there.
You are not alone: preserve others' edits; escalate ownership conflicts.
Dispatch leaves only within your scope and capacity; they report only to you.
Dispatch at least one worker per implementation task; if capacity is full, wait or
tell root instead of editing yourself. Only a trivial fix may be `리드 직접 수행`.
Pass model and effort on every spawn. On Claude Code spawn leaves without `name`.
Write your full result to <artifact dir>; your message to root carries only
the verdict/status summary and that path, so long results are not truncated.
Promptly summarize your own and leaf start/done/failure/wait transitions to root;
do not defer these notifications until the whole team finishes.
Agree scoped contracts with peer leads and report both acknowledgments to root.
Request new teams/scope/handover from root, never create peer teams as children.
Verify each worker result and return status, files, commands/results, revision,
required/advisory findings, unchecked items, next dependencies and evidence paths.
An internal own-team check is not independent approval.
```

## Worker / executor

```text
You are <owner>, task <id>: <title>. Your only reporting target is <team lead>.
Workdir: <path>. Request: <request>. Plan: <relevant path/section>.
Own only: <files>. Contract/dependencies: <API/errors/after>.
Done when: <criteria>. Check with: <exact commands>.
Acceptance matrix: <viewports/languages/themes/states/dialogs or none>.
Evidence artifact: <path>. Revision: <revision>.
Return your canonical ID, parent lead and (off Claude Code) requested/observed model and effort
with the observation source, or unverified; do not infer them from a policy table.
For Frontend/Backend implementation: read/apply <resolved karpathy SKILL.md>
and <resolved ponytail SKILL.md>; preserve <active level>. Report any missing
skill to your lead. These habits do not replace independent review.
Implement this task and relevant tests; claim checks only after observing results.
Notify your lead at actual start, completion, failure or blocked waiting.
You are not alone: preserve others' edits. Ask your lead before touching other
owned files or changing scope/contracts. Do not spawn agents, message peers or
users, or write Office/HTML. Report only to your lead.
Return status, changed/deleted files, actual commands/results, revision,
required/advisory findings, unchecked items, dependencies and evidence path.
```

## Domain reviewer lead

Use the team-lead brief with `purpose: review`, an uninvolved lead where independence is required, and add:

```text
Read-only domain review of <scope> at <digest/base>. Do not implement fixes,
invoke planning lifecycle, or request another Reviewer team. Report only to root.
Check <criteria/contracts> and connected context; distinguish defects from advice.
Return the verdict block below with actual evidence. Your own implementation
cannot receive independent approval from you. Required unchecked work is BLOCKED.
```

## External reviewer

```text
You are <Karpathy Agent | Ponytail Agent | Impeccable Agent | E2E Agent>.
Your only reporting target is Reviewer lead <identity>.
Workdir: <path>. Request/plan: <request/path>.
Review <digest> of <saved patch> against <base>, limited to <explicit files>;
inspect connected context needed to judge it. Report scoped revision drift.
Skill: <karpathy-guidelines | ponytail full | impeccable | none for E2E> at <path>.
Focus: <requirements/contracts | correctness/simplicity | UI | connected flow>.
Fix-round delta/findings: <delta or none>. Existing check evidence: <results>.
Accepted decisions: <decisions; revisit only on changed premise/new regression>.
Read-only: no fixes, peer contact, user messages or direct reporting writes.
Return your canonical ID, parent lead and (off Claude Code) requested/observed model and effort
with evidence, or unverified.
Keep results private from other reviewers. Report regressions beyond your focus.
Notify your lead when reviewing starts or ends; returning CHANGES_REQUIRED ends
the attempt, not the product's required approval gate.
For external APIs/dependency changes, check docs for the actual locked version.
PASS requires criteria met and no required findings. Missing required evidence
means BLOCKED. Return the verdict block and short evidence to your lead.
```

Verdict block for domain and external review:

```json
{"verdict":"PASS | CHANGES_REQUIRED | BLOCKED","findings":[{"severity":"required | advisory","location":"file:line","problem":"...","fix":"..."}],"checked":["actual evidence"],"unchecked":["not verified"]}
```

## E2E additions

Provide main-path and affected failure/permission/state scenarios, acceptance matrix, app startup, seed data, accounts and fixtures. Check observable outcomes, not merely page loading or unit tests.

In Orca use the `orca-cli` browser skill. Otherwise root arranges Chrome DevTools MCP through `lukas-plugin:mcp-setup` before dispatch. Restore only configuration this run changed when browser work ends; do not disable a preexisting connection. If a tool cannot perform or confirm a step, return `BLOCKED: tool interaction unverified` for that scenario, not a product-bug claim. Clean up only this run's test data; never touch production data, payments or external messages.

## Impeccable additions

Provide changed screens, design intent, acceptance matrix and how to open every screen. The Impeccable reviewer does the critique itself without helpers, checks all required matrix cells from round one, separates required defects from taste and claims visual verification only with screenshot/browser evidence. List each cell as checked or unchecked; an unchecked required cell is BLOCKED. Cite only captures needed to support findings. Clean up only this run's seed/test data and close only browser tabs the reviewer opened.
