# Team contract

All six team entrypoints use this contract. Main/root owns orchestration, reporting, integration and final verdicts; team leads own scoped execution and worker evidence. Here “worker” is an organizational role: use an appropriate native role such as `executor`. `agent_type=worker` is reserved for an active OMX Team runtime.

## Entry and result

Dispatch includes: purpose (`execute`, `review` or `plan`), scope/non-goals, absolute workdir, applicable plan, owned files, acceptance criteria and verification commands, parent identity, peer identities/contracts, revision, reporting writer/run context and artifact location. A review also requires comparison base and frozen revision. Main/root fills missing standalone context; delegated agents never expand it silently.

Each return includes status (complete/in-progress/blocked), changed files, actual check commands/results, revision, required/advisory findings, unchecked items, next dependencies and evidence paths. Save detailed worker results in run-specific Markdown artifacts; leads verify and aggregate them, preserving failures and gaps.

Include the actor's canonical ID, parent lead and requested model/effort; root, or a reporting lead for its team, fills observed values from the actor check below. Leads preserve this information for themselves and their leaves in their summary to root; root uses it for reporting without treating the summary card as a worker.

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

Workers report only to their own lead: no sibling/peer/user messages or direct Office/HTML writes. Put this boundary in every brief and restrict tools when the host supports it. Without tool enforcement it is an instruction boundary, not security isolation. Leads summarize upward; root alone addresses the user, selects reporting and owns the run, while leads write only their team's Office cards (see the reporting contract).

Workers notify their lead when work starts, finishes, fails or waits on a blocker. Leads promptly summarize those transitions and owner/model corrections to root, including their own status, without waiting for all leaves. These are evidence-backed status notifications, not periodic polling loops.

One file has one current owner. A handover requires root's recorded decision and a prerequisite `after` edge; subsequent findings go to the new owner. `after` means dependency, never parent/team membership. Agents are not alone in the worktree: preserve others' edits and escalate ownership conflicts. Under `basic-team`, a lead dispatches at least one worker for each implementation task and keeps to splitting, verifying and summarizing; the user expects to see the team working. A lead edits directly only for a trivial fix such as a single typo, and says `리드 직접 수행` with the reason in its summary. A lead cannot independently approve its own work.

A lead's own-team check is internal validation. For independent own-domain review, root assigns a fresh uninvolved read-only lead instance. Cross-team review also needs explicit scope and evidence. Domain findings remain separate from the external Karpathy/Ponytail/conditional Impeccable/E2E lineup. All required reviews share the frozen revision, three-round fix limit and final-check rules in [basic-team](../SKILL.md#review-and-fix); standalone implementation roots read and apply those sections without invoking basic-team recursively.

## Host and capacity gate

Before dispatch, confirm actual host tools and policies support peer lead creation/messages, lead-to-worker spawning, parent-only leaf return, waiting/resume/termination, depth and available capacity. Use host-supported tool names, not assumed aliases. Select a lead role that permits child spawning; a leaf-guarded role cannot be a lead. Verify the intended path rather than claiming support from API documentation for another host/version.

On Claude, check Agent Teams enablement and interactive operation plus foreground nested-subagent support. Claude Code's team roster is flat: only main/root can spawn named teammates, and a lead's own `Agent` call with `name` fails with `team roster is flat`. Leads therefore spawn leaves without `name`; those results return only to that lead. State this in every lead brief. A background/noninteractive leaf that returns directly to main violates this reporting structure. On Codex, check actual nested spawn/depth policy and result routing. If unsupported, report the exact limitation and supported separate execution path; do not silently flatten the hierarchy or promise behavior the runtime cannot supply.

Budget root, live leads, workers, harness roles and external reviewers together. Reserve room for a lead's workers before starting it; launch only ready teams. When capacity is full, wait for a batch and close finished owned agents where supported. Keep parents and required peers alive until dependents finish; never orphan leaves. Review batches must preserve revision and isolation of results. Do not copy a session's slot count into a universal limit.

If a lead unexpectedly disappears, root stops new dispatch for that branch and uses supported host controls to keep its live leaves quiescent/waiting while attempting to resume the same parent. Do not redirect worker reports to root/peers or invent reparenting. If the parent cannot recover, settle or stop only this run's affected leaves through supported controls, preserve their artifacts and mark the affected work blocked/failed in the evidence (using valid tracker statuses). If those controls are unavailable, report the limitation and keep dependent work blocked. A fresh lead must recheck file ownership, partial edits and evidence before reassignment; disappearance or recovered artifacts alone never prove completion.

## Implementation habits

Frontend and Backend leads and implementation workers load and apply the bundled [karpathy-guidelines](../../karpathy-guidelines/SKILL.md) and the installed `ponytail:ponytail` skill before editing. Root resolves actual skill paths; leads include those exact paths in every implementation brief, never guessed installation paths. Preserve the session's active Ponytail level (otherwise use its documented default). If either skill cannot be found/read, report that dependency gap to the parent instead of claiming it was applied. These implementation habits do not replace independent Karpathy/Ponytail reviews.

## Model policy

This skill explicitly requires model and effort on every spawn, including leads: omitting `effort` leaves nothing to report. Leads get main's model and main's effort (checked as below). Preserve the existing specialist policy below, subject to higher-priority host instructions. Pass supported settings as real spawn arguments (Claude `model` alias/`effort`; Codex `model`/`reasoning_effort`, using the host's required fork mode). Do not use Claude `subagent_type: fork`, which ignores overrides. If settings cannot be applied, disclose once and use supported inherited settings; never report an unobserved model as confirmed.

Role-fixed host settings can override or reject requested values. Verify the actual actor through supported runtime metadata; a policy table or spawn request is not observation. Root checks every agent's actual model and effort itself, root included (a reporting lead may run the same check for its team): both hosts record them locally for every agent at any depth, so "metadata unavailable" is not an answer until this check found no record for that agent. Do not ask agents to report their own settings. On Claude Code each assistant turn records them, and leaves of leads are in the same session:

```sh
d=$(ls -d ~/.claude/projects/*/$CLAUDE_CODE_SESSION_ID)/subagents
for m in "$d"/*.meta.json; do printf '%s\t%s\n' "$(jq -r '.name // .description' "$m")" "$(jq -r 'select(.type=="assistant") | "\(.message.model) \(.effort)"' "${m%.meta.json}.jsonl" | tail -1)"; done
```

Main's own value is the same `jq` on `~/.claude/projects/*/$CLAUDE_CODE_SESSION_ID.jsonl`. On Codex every thread has a rollout whose first line names its parent thread and `agent_path` (`/root/backend_lead/backend_contract`) and whose latest `turn_context` holds its settings; `CODEX_THREAD_ID` is root's own thread. This prints root and every descendant:

```sh
root=$CODEX_THREAD_ID  # rollout names start with their creation time, so parents sort before children
find ~/.codex/sessions -name 'rollout-*.jsonl' | awk -F/ '{print $NF "\t" $0}' | sort | awk -F'\t' -v r="$root" 'index($1, r) {on=1} on {print $2}' | while read -r f; do
  head -1 "$f" | jq -r --arg f "$f" '.payload | ((.source | objects | .subagent.thread_spawn) // {}) as $s | [.id, $s.parent_thread_id // "", $s.agent_path // "/root", $f] | @tsv'
done | awk -F'\t' -v r="$root" '$1 == r || $2 in ids { ids[$1]; print $3 "\t" $4 }' | while IFS=$'\t' read -r agent f; do
  printf '%s\t%s\n' "$agent" "$(grep '"type":"turn_context"' "$f" | tail -1 | jq -r '.payload | "\(.model) \(.effort)"')"
done
```

Until an agent's first turn its rollout shows inherited or no settings, so use it only after that turn; an empty value means no record yet. Run it after spawning and at every reporting checkpoint, and put those values on the cards. A running agent's effort cannot be changed: if a supported override can correct a policy mismatch, give remaining or follow-up work to a new spawn with that setting instead of resuming it. If the host fixes the role to another value (for example requested `max`, observed `medium`), report requested/observed values and the supported-host limit once, then use the supported setting; do not repeatedly respawn an unchangeable role. If that limit prevents meeting the task's acceptance criteria, escalate only the affected work for a supported role/path. If an agent has no record, retain the requested values as requested and mark actual values unverified, naming the missing file, instead of searching unrelated sessions.

| Role | Claude | Codex |
| --- | --- | --- |
| Team lead | main's model, main's effort (`high` if unknown) | main's model, main's effort |
| Executor | `haiku` (`claude-haiku-5-5`), `max` | `gpt-6-luna`, `max` |
| Documentation executor | `sonnet` (`claude-sonnet-5-5`), `medium` | `gpt-6.1-sol`, `medium` |
| Reviewer | `sonnet` (`claude-sonnet-5-5`), `high` | `gpt-6.1-sol`, `medium` |
| Planner, Architect, Critic (ralplan) | `opus` (`claude-opus-5-5`), `medium` (`high` for hard plans) | `gpt-6.1-sol`, `medium` (`high` for hard plans) |

Pass the Executor row even when the spawned role's default model differs. A lead raises one implementation worker only when haiku would take too long (`sonnet`) or the task proves hard (`opus`), with effort chosen for its difficulty, and tells root why; on Codex it raises `gpt-6-luna` to `gpt-6.1-sol` the same way. The lead still verifies every worker result.

Apply harness-role settings only through its supported invocation. Use host-valid native IDs, such as `frontend_lead` and `karpathy_agent` on hosts that require underscores; never reuse a rejected spelling. On Claude Code only root-spawned leads get a native name; a lead's leaves, reviewers included, have none, so identify them by the returned agent ID in evidence and resume them with `SendMessage` to that ID. Keep native IDs, canonical agent paths and Office display owners distinct. External reporting labels retain `Karpathy Agent`, `Ponytail Agent`, `Impeccable Agent`, `E2E Agent`. UI YAML describes skills; it does not register native agent types.
