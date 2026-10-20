# Team contract

All six team entrypoints use this contract. Main/root owns orchestration, reporting, integration and final verdicts; team leads own scoped execution and worker evidence. Here “worker” is an organizational role: use an appropriate native role such as `executor`. `agent_type=worker` is reserved for an active OMX Team runtime.

## Entry and result

Dispatch includes: purpose (`execute`, `review` or `plan`), scope/non-goals, absolute workdir, applicable plan, owned files, acceptance criteria and verification commands, parent identity, peer identities/contracts, revision, reporting writer/run context and artifact location. A review also requires comparison base and frozen revision. Main/root fills missing standalone context; delegated agents never expand it silently.

Each return includes status (complete/in-progress/blocked), changed files, actual check commands/results, revision, required/advisory findings, unchecked items, next dependencies and evidence paths. Save detailed worker results in run-specific Markdown artifacts; leads verify and aggregate them, preserving failures and gaps.

| Invocation | Root responsibility | Child responsibility |
| --- | --- | --- |
| `basic-team` | Select needed teams and report one run | Peer Frontend/Backend/Docs/Reviewer leads own their leaves |
| Standalone Frontend/Backend/Docs | Coordinate requested team and needed support | Requested lead and Reviewer lead are peer children |
| Standalone Reviewer | Coordinate review and return findings | Reviewer lead dispatches external reviewers only |
| Standalone Plan or prerequisite planning | Own installed ralplan lifecycle before execution teams | Harness owns its internal roles |
| Domain review | Assign bounded independent read-only scope | A lead reviews its domain without launching implementation or ralplan |

Standalone skills use this contract directly, never recursively invoke basic-team. A delegated lead requests other teams from root; it does not create a sibling team as its child. Reviewer never creates another Reviewer team. Plan-only and review-only requests do not trigger implementation. Root planning is the default unless the installed harness demonstrably supports an embedded return path with correct lifecycle ownership; do not assume `--advisory` composes with execution.

## Communication and ownership

Leads may message known peer leads to agree contracts and order within scope. Record a decision ID, participating teams, API/error/file agreement, affected tasks and revision. Both leads acknowledge; root records the final decision. Unresolved disagreements or expanded scope go to root; pause only dependent work.

Workers report only to their own lead: no sibling/peer/user messages or direct Office/HTML writes. Put this boundary in every brief and restrict tools when the host supports it. Without tool enforcement it is an instruction boundary, not security isolation. Leads summarize upward; root alone addresses the user and selects/writes reporting.

One file has one current owner. A handover requires root's recorded decision and a prerequisite `after` edge; subsequent findings go to the new owner. `after` means dependency, never parent/team membership. Agents are not alone in the worktree: preserve others' edits and escalate ownership conflicts. Leads may do small tasks themselves, but cannot independently approve their own work.

A lead's own-team check is internal validation. For independent own-domain review, root assigns a fresh uninvolved read-only lead instance. Cross-team review also needs explicit scope and evidence. Domain findings remain separate from the external Karpathy/Ponytail/conditional Impeccable/E2E lineup. All required reviews share the frozen revision, three-round fix limit and final-check rules in [basic-team](../SKILL.md#review-and-fix); standalone implementation roots read and apply those sections without invoking basic-team recursively.

## Host and capacity gate

Before dispatch, confirm actual host tools and policies support peer lead creation/messages, lead-to-worker spawning, parent-only leaf return, waiting/resume/termination, depth and available capacity. Use host-supported tool names, not assumed aliases. Select a lead role that permits child spawning; a leaf-guarded role cannot be a lead. Verify the intended path rather than claiming support from API documentation for another host/version.

On Claude, check Agent Teams enablement and interactive operation plus foreground nested-subagent support. A background/noninteractive leaf that returns directly to main violates this reporting structure. On Codex, check actual nested spawn/depth policy and result routing. If unsupported, report the exact limitation and supported separate execution path; do not silently flatten the hierarchy or promise behavior the runtime cannot supply.

Budget root, live leads, workers, harness roles and external reviewers together. Reserve room for a lead's workers before starting it; launch only ready teams. When capacity is full, wait for a batch and close finished owned agents where supported. Keep parents and required peers alive until dependents finish; never orphan leaves. Review batches must preserve revision and isolation of results. Do not copy a session's slot count into a universal limit.

If a lead unexpectedly disappears, root stops new dispatch for that branch and uses supported host controls to keep its live leaves quiescent/waiting while attempting to resume the same parent. Do not redirect worker reports to root/peers or invent reparenting. If the parent cannot recover, settle or stop only this run's affected leaves through supported controls, preserve their artifacts and mark the affected work blocked/failed in the evidence (using valid tracker statuses). If those controls are unavailable, report the limitation and keep dependent work blocked. A fresh lead must recheck file ownership, partial edits and evidence before reassignment; disappearance or recovered artifacts alone never prove completion.

## Implementation habits

Frontend and Backend leads and implementation workers load and apply the bundled [karpathy-guidelines](../../karpathy-guidelines/SKILL.md) and the installed `ponytail:ponytail` skill before editing. Root resolves actual skill paths; leads include those exact paths in every implementation brief, never guessed installation paths. Preserve the session's active Ponytail level (otherwise use its documented default). If either skill cannot be found/read, report that dependency gap to the parent instead of claiming it was applied. These implementation habits do not replace independent Karpathy/Ponytail reviews.

## Model policy

New leads inherit main's supported model/effort policy. Preserve the existing specialist policy below, subject to higher-priority host instructions. Pass supported settings as real spawn arguments (Claude `model` alias/`effort`; Codex `model`/`reasoning_effort`, using the host's required fork mode). Do not use Claude `subagent_type: fork`, which ignores overrides. If settings cannot be applied, disclose once and use supported inherited settings; never report an unobserved model as confirmed.

| Role | Claude | Codex |
| --- | --- | --- |
| Executor | `haiku` (`claude-haiku-5-5`), `max` | `gpt-6-luna`, `max` |
| Documentation executor | `sonnet` (`claude-sonnet-5-5`), `medium` | `gpt-6.1-sol`, `medium` |
| Reviewer | `sonnet` (`claude-sonnet-5-5`), `high` | `gpt-6.1-sol`, `medium` |
| Planner, Architect, Critic (ralplan) | `opus` (`claude-opus-5-5`), `medium` (`high` for hard plans) | `gpt-6.1-sol`, `medium` (`high` for hard plans) |

Apply harness-role settings only through its supported invocation. Spawn/message names have no spaces (`frontend-lead`, `karpathy-agent`); external reporting labels retain `Karpathy Agent`, `Ponytail Agent`, `Impeccable Agent`, `E2E Agent`. UI YAML describes skills; it does not register native agent types.
