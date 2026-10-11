---
name: basic-team
description: Coordinate native Codex or Claude agents through planning, parallel implementation, mandatory Karpathy and Ponytail reviews, and conditional design and E2E reviews. Use for a requested basic-team development workflow.
---

# Basic Team

The main session is the leader and user contact. It records evidence and dispatches the next ready task; Executors edit product files, strong planning agents make the plan, and independent reviewers assess it. Run the full workflow even for a small task when the user requests this workflow. A request to inspect or edit this skill is not a request to execute it.

Use Codex native collaboration or Claude's installed OMC `team` native-team path in the current main session. Do not launch tmux teams, another leader, or a CLI substitute. Frontend and Backend are work classifications, not a limit of one Executor per area. These review personas do not mean the named people reviewed the code.

## Invariants

- Follow the user's scope, amendments, permissions, budgets, and validation policy. This workflow grants no publishing, pushing, deployment, unrelated changes, or agent/global configuration changes. The scoped browser/MCP exception is specified in [references/e2e-review.md](references/e2e-review.md).
- Preserve the Planner, approved planning review, task ownership/contracts, progress page/receipts, ELI5 briefings, stage handoffs, independent final-revision reviews, validation, and verified host shutdown. Only a specific user instruction can omit a requirement; record it in Decisions & Blockers and the final compliance table. Missing capability means an honest gap or BLOCKED, not a silent waiver.
- The leader never edits product files. Children do not launch another workflow or write the progress page. Preserve pre-existing user changes and other agents' edits; one named owner per shared file.
- Review all finished implementation/integration edits on one frozen product revision. Every required reviewer must PASS that same final revision; any product edit supersedes earlier verdicts and affected tests. No self-review, elapsed time, timeout, or retry count replaces evidence.
- The HTML, handoffs, helper gates, and hook records are reporting/recovery data. They neither establish permission nor replace native task lifecycle, real host settings, or actual validation.

## Models, paths, and accepted invocation

Use this table for every new child, including replacements and conditional review helpers. Architect/Critic use the Planner tier. Never drop a reviewer or lower effort for capacity; queue or reuse compatible idle agents through supported host operations.

| Role | Codex model | Reasoning | Claude model | Effort |
| --- | --- | --- | --- | --- |
| Planner | `gpt-6.1-sol` | `high` | `claude-opus-5-5` | `medium` |
| Executor | `gpt-6-luna` | `max` | `claude-haiku-5-5` | `max` |
| Documentation Executor (only when the approved plan includes documentation work) | `gpt-6.1-sol` | `medium` | `claude-sonnet-5-5` | `medium` |
| Reviewer (each) | `gpt-6.1-sol` | `medium` | `claude-sonnet-5-5` | `high` |

At preflight read ONLY the current host reference: [Codex](references/host-codex.md) or [Claude](references/host-claude.md). Check the actual spawn schema, reply/resume/wait and termination capabilities. Unsupported required invocation or lifecycle operations remain BLOCKED; do not invent settings or configuration.

Resolve the installed `ralplan`, `plan`, `lukas-plugin:karpathy-guidelines`, `ponytail:ponytail`, and `eli5:eli5` SKILL.md paths. Use `plan` only if `ralplan` is absent. Both planning skills missing, either mandatory review skill missing, or eli5 missing is a dependency blocker. Claude also resolves and invokes `oh-my-claudecode:team` at preflight. For Frontend resolve `impeccable`; missing required guidance is a blocker. Load skills only when their stage needs them and pass exact paths to children.

New runs default to `invocation-evidence-v2`: correct model/effort call arguments accepted by the host permit work even when actual settings are `미확인`. Record requested, actual invocation, acceptance evidence, and observed settings separately. An argument, role definition, or child self-report is not actual host observation. Missing/rejected required arguments or a known actual mismatch block that child; use supported corrected invocation/recovery, never an unknown-setting exception to pass a known mismatch.

If the user requires proof of actual settings, initialize `strict-observation-v1`: unknown model or effort pauses substantive work unless the user explicitly permits that missing observation for that child. Existing pages without a policy retain strict v1, and resumed runs retain their recorded policy. Never relax a run through `update` or reinterpret an old exception as observation. See [references/progress-updates.md](references/progress-updates.md) for fields and commands.

## Leader runbook

`<bt>` is this skill's resolved directory. Run `uv run "<bt>/scripts/progress.py" ...` from the target project/worktree root; `PAGE` is an absolute path beneath its `docs/inprogress/`. Never use another Python interpreter. Missing `uv` is BLOCKED.

Read each stage's directly linked reference when entering it. Gate exit 0 with `ok` means saved-data checks passed; inspect underlying artifacts/host evidence too. Exit 1 gives unmet problem codes and targets: repair only those missing facts or route a blocker. Exit 2 is a command/input failure: read stderr, fix the call, retain pending work. A helper success does not prove the task happened.

| Step | Inputs and reference | Action | Pass evidence | Failure/wait recovery |
| --- | --- | --- | --- | --- |
| 1. Preflight | User request, project instructions, current host reference | Resolve skills and supported lifecycle; on Claude invoke native team | Required paths and host capabilities recorded | Missing required dependency/capability: investigate once, report specific BLOCKED/recovery |
| 2. Kickoff | [Progress updates](references/progress-updates.md), [template semantics](references/progress-template.md), eli5 | Init one page with policy and queued required reviewers; request host hook arm; brief | Successful save receipt, actual hook confirmation or manual fallback | Failed save stays pending; no nonexistent link. Missing hook support does not block work |
| 3. Draft | [Planning/allocation contracts](references/workflow-contracts.md); for Frontend/connected flows [conditional rules](references/conditional-reviews.md) | Generate Planner brief; spawn with explicit arguments; save accepted invocation/settings and draft | Draft revision, requirements, ownership/contracts, checks, conditional-review decisions | Routine authorized choices need no approval; material ambiguity goes through blocker recovery |
| 4. Plan review | Same draft + installed ralplan | Spawn Architect; collect result; then Critic with that draft AND Architect result. Use dedicated briefs | Ordered review artifacts for the approved plan revision; permitted plan fallback when ralplan absent | Required revisions: resume Planner, then obtain fresh ordered reviews. No draft-as-consensus claim |
| 5. Implementation release | Approved plan/allocation, task record, planning → implementation handoff | Save plan evidence; run `gate PAGE --stage implementation`; queue/dispatch ready owned tasks with Executor briefs | Saved checkpoint, actual handoff read, cleared gate and accepted calls under policy | Gate/input failures: repair missing evidence; keep affected tasks paused and independent work moving |
| 6. Implement | Ready tasks and replies | Dispatch within capacity; record factual reports; explicitly assign integration; save implementation → verification handoff | All implementation/integration edits finished, changed files and fresh allowed checks recorded | Ownership/contract change: ask leader before editing; consequential plan changes return to Planner |
| 7. Independent review | Frozen product revision, shared review inputs, conditional reviewer decisions | Save review target/required reviewers; run `gate PAGE --stage review`; dispatch independent read-only reviewers | Complete review set on same revision saved together, then ELI5 review briefing | Keep early verdicts/findings out of ALL page data until collection completes. Tool blockers may be reported immediately |
| 8. Fix/recovery | Complete findings or tool-blocker evidence | Save verification → fixes/recovery handoff; assign required fixes to owners; fresh checks and fixes → verification handoff | New frozen revision and all required fresh verdicts | Product edits clear prior verdicts; return to step 7. Tool failure alone is not a product defect |
| 9. Finish | Final reviews/validation, [exit contract](references/workflow-contracts.md), host lifecycle | `gate PAGE --stage ready`; shutdown/cleanup; disarm; completion handoff + final save; then `gate PAGE --stage complete` and `compliance PAGE` | Same-revision PASS, required checks, verified shutdown/cleanup, confirmed final receipt, no pending writes/updates | Cleanup runs on success, failure, or cancellation even when gates fail. Unverified exit remains BLOCKED; do not claim complete |

The planning order is **Planner → Architect → Critic**; Critic receives Architect evidence. Product reviewers are **independent of one another**. Do not apply product-review isolation to planning consensus. This applies the installed ralplan method through native agents, not OMX/OMC consensus runtime: no `omx ralplan run`, runtime-owned state writes, fabricated runtime gate, or handoff to ultragoal/ralph.

## Briefs and ready-task dispatch

The Planner groups the allocation into Phase TODOs. Save `taskPlanRevision` and the full `tasks` snapshot in the same progress HTML before implementation; match the approved plan and reuse task IDs in briefs/reports. The Plan tab shows per-Phase checklists and completed counts. Update statuses from actual reports and validation, require evidence for `done`, and reopen affected tasks when fixes invalidate completion. Publish independent review TODO outcomes only after the full review set is collected. See [progress-updates.md](references/progress-updates.md) for fields; no separate TODO file is needed.

Generate prompts with `brief --role <planner|architect|critic|executor|documentation_executor|reviewer> --input <fields.json>` and call arguments with `spawn-args --host <codex|claude> --role <role>`. Use generated arguments as actual tool arguments, not merely prompt text. Pass generated briefs unchanged; put task detail in their fields. When the approved plan includes documentation work, assign that task to `documentation_executor`; otherwise do not create this role.

Each brief requires `task_id`, `request` including amendments, `project_instructions`, `workdir`, `area`, `owned`, `inputs`, `deliverable`, `validation`, `contacts`, and `skills` (resolved paths). Reviewers additionally need `revision` and `reviewer`. Give read-only roles `owned: none (read-only)`. Architect Inputs contain plan revision/path; Critic Inputs contain that plan and Architect artifact. Executor Inputs contain agreed contracts, prerequisites, existing pattern paths and concrete input/output examples; Deliverable gives observable completion criteria and Validation gives exact allowed commands. The child confirms ownership in its first factual checkpoint and works without a redundant MODEL/leader-release exchange unless strict observation is pending.

Use stable task/agent IDs and reviewer IDs `karpathy`, `ponytail`, activated `impeccable`, `e2e`. Record every assignment as queued before launching, then actual outcome and accepted settings after launch. Record task ID, owner/files, prerequisites, acceptance criteria and observed status in Claude's native task surface or Codex's leader task record; HTML does not replace this record.

Split substantial independent work inside each area as well as across Frontend/Backend; do not manufacture parallelism from tiny edits. Explicitly classify unaffected areas as not needed. Define cross-area inputs, outputs, errors/auth and shared-file owners before release. Dispatch all ready independent tasks within capacity, start dependents when their own prerequisites succeed, and reuse compatible idle Executors for fixes. A finished task does not necessarily free an agent slot.

## Reviews, validation, and blockers

Load [references/workflow-contracts.md](references/workflow-contracts.md) at review/fix/exit. Both mandatory reviewers inspect correctness, regressions, scope, simplicity, affected callers and cross-area compatibility on actual files. Give all reviewers the same request, approved plan, criteria, full diff, relevant source, revision and validation evidence; each receives only its own review skill and no other verdict/self-approval. Give Impeccable its design brief/targets and E2E its scenarios/environment/fixtures/readiness.

Activate Impeccable for visible new/redesigned UI, layout, typography, color, navigation, interaction, responsive behavior or requested design judgment. Internal Frontend refactors without UX impact do not automatically activate it. Activate E2E for connected multi-screen/client-server-persistence/authentication/services/jobs outcomes or requested E2E. File count alone is not a trigger. Save both decisions/reasons and re-evaluate on scope change; never deactivate a reviewer to bypass findings. Read [references/conditional-reviews.md](references/conditional-reviews.md) when these conditions or changed external APIs/dependency versions apply; read [references/e2e-review.md](references/e2e-review.md) only for activated E2E or required browser interaction.

Publish all required verdicts together as PASS / CHANGES_REQUIRED / BLOCKED, with revision, severity/file:line/impact/required fix, evidence and unchecked scope. PASS needs met criteria, required validation evidence, and no required finding. Advisory improvements do not expand scope. Resolve conflicting findings against evidence; never overrule an unresolved finding and fabricate PASS.

Planner specifies smallest allowed checks proving acceptance and affected boundaries; preserve required project checks. Record command/action, product revision, environment, exit code, evidence and unchecked scope. Later product edits rerun affected checks and supersede stale evidence. Required failures, including baseline suite failures, prevent all-green completion unless the user explicitly changes acceptance scope. Forbidden/not-run checks are gaps, never passes.

For a blocker: identify affected task/failure → bounded code/config/docs/log investigation → smallest already-authorized remedy within ownership → verify/report. Reviewers stay read-only. Ask through the leader only for materially different unresolved outcomes, missing requirements/access, or needed authority; include evidence, recommendation and tradeoffs. Save the question/owner, pause dependent work, continue independent work, and resume once the real answer arrives. Silence is not approval; no repeated failed retries without new evidence.

## Checkpoints, briefings, and exit

The main session is the sole semantic page writer. Use one standalone HTML page `<project-root>/docs/inprogress/<task-slug>-<YYYYMMDD-HHmmss>-progress.html`, unique at kickoff and reused through fixes/resume/compaction. Never use the plugin directory or silently fall back to `/tmp`; keep artifacts out of product commits unless requested. Preserve the existing accessible tabs, graph/tooltips/modal, inline assets, honest empty states and reduced-motion behavior specified in [references/progress-template.md](references/progress-template.md).

Use easy Korean ELI5 explanations unless the user asks otherwise: what happened → confirmed result/remaining work → next action. Preserve technical facts and unknowns. Brief at kickoff, after planning, consequential decisions/blockers, review rounds, resume, and completion. Every briefing includes clickable page link, absolute path, confirmed receipt save time, artifact links, validation gaps and separate hook request/confirmation states. No new facts means reuse the receipt without another save.

Advance by **received facts → save pending patch → verify receipt → dependent dispatch/briefing**. Batch received reports, consume each once only after successful save, preserve failed patches, and never release a dependent stage after its save fails. Do not poll agents/files/mailboxes/capacity, send repeated status queries, or rewrite the page on a timer. When no ready work remains, use supported notification/event wait; timeout is neither success nor failure. Status inspection is limited to initial routing, explicit user request, real failure diagnosis or required lifecycle verification. Host-specific message/resume rules are in the current host reference.

Append stage handoff records to the same HTML page’s `handoffs` JSON array using [assets/stage-handoff-template.md](assets/stage-handoff-template.md), including completion and fix rounds. Read the saved record with `handoffs PAGE --id ID` before release. Do not create a separate MD per transition; reference an existing artifact when the user or host explicitly requires one. Resume using the exact saved path, last receipt, policy, pending patches and outstanding IDs; reconcile `status` with actual host/repository evidence. Never select the newest page or treat saved stage as execution authority.

Hooks default silent. Only Main executing this workflow arms after page creation/verification, rearms on continuing requests/resume, retains exact run_id, and disarms on completion/cancellation/failure/task switch. Missing host identity/confirmation uses manual checkpoints. Do not arm when discussing or editing the skill. Commands and confirmation limits are in the current host reference and progress updates.

After final readiness, perform scoped shutdown/cleanup once; timeout/unresponsive agent recovery and inactive-state evidence follow the current host. Never stop unrelated agents, delete state to hide workers, or claim unverified exit. Save final outcome, settings, reviews/checks/gaps, shutdown/cleanup, handoff and receipt before the complete gate. Every final report, including BLOCKED/cancelled, includes `compliance PAGE`'s table (`함 / 부분 / 안 함`) with concrete evidence, inapplicable reasons and explicit omissions. Use `complete` only after all required implementation, reviews, validation, saves and lifecycle checks succeed.
