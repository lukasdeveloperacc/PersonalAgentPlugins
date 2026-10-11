# Conditional review rules

Read the section you need when its condition applies; the main SKILL.md holds only the unconditional workflow.

## Impeccable guidance for Frontend planning

When planning Frontend work, the Planner loads `impeccable`, follows its context setup once in its session for the named target, and consults the installed `reference/shape.md` planning criteria. Use these criteria inside ralplan/plan to clarify the audience/job, primary flow, existing visual authority, layout/interaction intent, responsive behavior, relevant loading/empty/error states, accessibility, and reusable components. Return a concise design brief and observable design acceptance criteria with the implementation plan. This is planning guidance, not a separate standalone `shape` command: route consequential unresolved questions through the leader using the existing blocker procedure, without repeating settled decisions or adding routine approval rounds.

Propose whether Impeccable reviewer is needed and name the affected surfaces and evaluation criteria. Activate it for new/redesigned UI or changes to visible layout, typography, color, navigation, interactions, responsive behavior, or other user experience needing design judgment; also activate it when the user requests design evaluation. Frontend internal refactors with no design/UX impact do not automatically need it. The leader confirms this decision from the actual implementation scope and re-evaluates it if scope changes; never deactivate a required review to bypass an unresolved finding. Planning does not authorize UI edits, context-file repairs, or replacing a pinned design direction.


## Impeccable single-agent review and budget

Within basic-team, one Impeccable Agent performs design assessment, detector/browser evidence collection and synthesis itself. This explicitly adapts standalone critique's two-subagent orchestration to the four-reviewer budget; neither the leader nor the reviewer spawns design, detector, browser or synthesis helpers. Include this section in the reviewer's brief along with the installed Impeccable path, so its standalone delegation instructions do not reintroduce helpers. A separately requested standalone critique retains its own procedure.

Record the design assessment before reading detector output, then run the detector/browser checks and synthesize one verdict. Report `⚠️ DEGRADED: single-context (basic-team four-reviewer budget)` in the critique evidence; this preserves ordering, not two-agent independence. Follow the installed context-launcher fallback, detector failure accounting, inspection/confirmation budget and cleanup procedure. Missing visual evidence is a gap, never visual verification; missing required evidence remains BLOCKED. Keep product/context files unchanged and any permitted snapshots in task artifacts. Reuse still-current evidence and do not reset the inspection budget through fixes or replacement agents.

Basic-team also replaces standalone critique's follow-up question gate: return the common verdict to the leader, who assigns authorized fixes and asks only about consequential unresolved choices. Record `Questions skipped: basic-team leader handles fixes and unresolved decisions`. Do not claim the standalone orchestration or question gate was satisfied.


## E2E review planning

Activate an independent E2E reviewer when changed behavior connects multiple screens, client/server/persistence, authentication and protected actions, or services/jobs whose complete outcome requires runtime validation across boundaries; also activate it when the user requests E2E validation. File count alone is not a trigger. Isolated styling, copy, internal refactors, and documentation changes do not automatically need it. The Planner records the decision, affected flows, observable success/failure criteria, target environment, fixtures/accounts, prerequisites, and allowed validation; the leader re-evaluates on scope changes without dropping a required review to bypass findings. Use the Reviewer model/effort and a distinct task name such as `basic_team_e2e`.

Load [e2e-review.md](e2e-review.md) only when E2E review is activated or another required reviewer needs browser interaction. It covers runtime evidence, browser selection, and MCP cleanup; apply its browser lifecycle to Impeccable too when applicable. Do not enable MCPs at kickoff or for source-only reviews.


## Conditional library documentation checks

For both Frontend and Backend changes, Karpathy and Ponytail reviewers use Context7 MCP when the diff introduces or changes an external library/framework/ORM/SDK API, depends on version-specific behavior, changes a dependency version, or leaves a material uncertainty about supported options, deprecation, or documented error handling. Pure styling, copy, and project-internal logic do not require documentation lookup unless they depend on such behavior.

- Establish the project's actual resolved dependency version from lockfiles or installed metadata, using manifests as declared-version evidence when resolution is unavailable. Query the relevant library's matching-version documentation through Context7; inspect the available tool schema rather than assuming tool names. Latest documentation alone does not prove compatibility with the project's version. Do not recommend an upgrade merely to match newer examples.
- **Karpathy:** check API assumptions, documented constraints, and whether the implementation meets the request using the supported behavior. **Ponytail:** check compatible API usage, affected callers, edge cases, error handling, and whether existing platform/library features can simplify the change.
- If a reviewer cannot access Context7, the leader can retrieve factual documentation for it; preserve independent verdicts. If the MCP is unavailable or lacks the matching version, use version-specific official documentation or upstream source instead. Record missing evidence; use `BLOCKED` when an unresolved compatibility question prevents a reliable verdict, rather than blocking solely because Context7 is unavailable.
- Keep queries focused on changed APIs. In `Evidence and unchecked areas`, state why the check applied (or was unnecessary), the package and resolved/declared version, source links or library/version identifiers, compatibility findings, and any version mismatch or uncertainty. Documentation supplements code inspection and validation; it does not prove project-specific business rules or runtime correctness. The leader summarizes applicable evidence and gaps in the progress page after all required independent reviews arrive.

