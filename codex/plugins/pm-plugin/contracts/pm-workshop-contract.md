# PM Workshop Contract

This contract defines how the Codex PM plugin turns ideas into discovery dossiers, research-backed workflow decisions, design-aware document bundles, backlog state proposals, TASK_SPEC candidates, and Claude handoffs.

## Operating Model

- GitHub is the state and tracking surface.
- Markdown is the decision, spec, and handoff source of truth.
- Slack is optional notification only and must not be treated as source of truth.
- Claude direct execution is out of v1 scope.
- Human approval is required for ambiguous decisions, final PR merge, release, and go-live.
- PM workshop output must be discovery-first. Brainstorm is the conversational entry point for first-project onboarding, feature shaping, UI/UX design shaping, refactor discovery, bug-theme investigation, user-provided site investigation, and docs/handoff planning. The PM should investigate available project evidence, permitted public browser evidence, design materiality, and confirm the workflow path with the human before producing final artifact bundles.
- If the question depends on current external best practices, upstream behavior, standards, or version-aware guidance, the PM should run a bounded research pass first and let that evidence shape the workshop direction.

## Discovery-First Gate

Before final artifact generation, the PM must produce a `Discovery Dossier` and `Workflow Decision Gate` unless the request is explicitly small, already approved, and low risk.

### Discovery Dossier

- Conversation mode
- Evidence inspected
- External evidence gathered, if any
- Site evidence gathered with Chrome DevTools MCP, if any
- Relevant existing docs/code/schema/backlog state
- Missing evidence
- Current assumptions
- Affected product, technical, data, and QA surfaces
- Design materiality: `DESIGN_REQUIRED` or `DESIGN_NOT_REQUIRED`
- Figma sources, existing design-system evidence, screenshots, or missing design evidence
- Investigation gaps that could affect Claude execution

### Workflow Decision Gate

Before choosing a workflow path, classify the workshop mode:

- `PROJECT_KICKOFF`
- `FEATURE_SHAPING`
- `REFACTOR_DISCOVERY`
- `BUG_THEME`
- `USER_PROVIDED_SITE`
- `UI_UX_DESIGN`
- `DOCS_AND_HANDOFF`

Use one:

- `MORE_INTERVIEW`: ask more product/PM questions before planning.
- `RESEARCH_FIRST`: inspect docs/code/schema/backlog or official references before planning.
- `PLAN_FIRST`: run planning/tradeoff work before artifact generation.
- `FULL_BUNDLE`: generate full PM/SDD/technical/TASK_SPEC/handoff bundle after confirmation.
- `STANDARD_BUNDLE`: generate a smaller scoped bundle after confirmation.
- `TASK_SPEC_ONLY`: produce TASK_SPEC from already-approved upstream documents.
- `DESIGN_REQUIRED`: route to Claude Designer before TASK_SPEC/Developer handoff, then require Codex `design-review`.
- `RESEARCH_THEN_DECIDE`: gather external evidence first, then re-open the workflow gate.

The gate must include:

- Recommended path
- Why this path fits
- Deliverables to generate
- Human decisions required before artifact generation
- OMX harness to use, if any
- Designer route to use, if UI/UX is material

The PM must ask one concise confirmation question and wait for confirmation or correction before producing final PRD, SDD, RFC, TASK_SPEC, or Claude handoff artifacts.

## Designer Routing Gate

The PM must mark `DESIGN_REQUIRED` when any of these are material:

- New screens, screen redesigns, or user-flow changes.
- Figma references, Figma draft creation/modification, or design-system decisions.
- Component anatomy, variants, states, responsive behavior, or accessibility expectations.
- Visual QA criteria that could block PR readiness.

If `DESIGN_REQUIRED`, the PM output must include:

- Required Claude Designer skills:
  - `/designer-plugin:design-intent`
  - `/designer-plugin:screen-spec`
  - `/designer-plugin:component-spec`
  - `/designer-plugin:figma-draft`
  - `/designer-plugin:visual-qa-brief`
- Required Codex Reviewer gates:
  - `$reviewer-plugin:design-review` before Developer handoff.
  - `$reviewer-plugin:visual-qa-review` after implementation before normal PR review.
- DESIGN_SPEC source-of-truth path, or a blocking note that it must be created.
- Figma sources and write-scope approval status.

The PM must not create a final Developer handoff for material UI/UX work unless one of these is true:

- Approved DESIGN_SPEC already exists and is referenced.
- Human explicitly chooses to proceed without Designer routing and residual design risk is recorded.
- The UI/UX surface is intentionally trivial and marked `DESIGN_NOT_REQUIRED` with rationale.

## GitHub Write Policy

Default mode: `propose-only`.

In `propose-only` mode, PM skills may read available GitHub context and propose updates. They must not write GitHub state.

Future write-mode support must explicitly configure:

- `github_write_mode`: `propose-only` or `enabled`
- `allowed_issue_fields`: title, body, labels, milestone, assignee, project status
- `allowed_project_fields`: status, priority, owner, target date, custom fields
- `forbidden_operations`: issue delete, irreversible close, PR merge, release, branch deletion, production deployment
- `approval_required_for`: ambiguous prioritization, irreversible closure, roadmap reorder, major scope split, status Done, release/go-live

## Bundle Depth

### Standard Bundle

Use by default:

- `BRAINSTORM.md`
- `PRD` or `FEATURE_SPEC` if product behavior needs definition
- Required technical SoT drafts only where affected
- Required design SoT drafts when `DESIGN_REQUIRED`
- TASK_SPEC candidates
- Claude handoff

### Full Bundle

Escalate to full bundle when any condition applies:

- Work spans two or more PRs.
- Claude is expected to work for most of a day or longer.
- There are two or more viable product or technical options.
- API, DB, auth, payment, route, or state machine changes are involved.
- Multiple SDD documents are affected.
- UI/UX requires Figma write, new design-system primitives, major flow changes, or multi-screen visual QA.
- Roadmap or priority conflicts exist.
- Human strategy decision is required.

Full bundle adds:

- RFC
- Roadmap/backlog ranking
- GitHub Issue/Project update plan
- Explicit decision log
- Multi-TASK_SPEC execution sequence
- DESIGN_SPEC and visual QA sequence when UI/UX is material

## OMX Harness Branching

The PM plugin may use OMX harnesses as planning and validation surfaces when the current Codex session supports OMX runtime workflows. Harnesses are not Developer execution and must not run Claude.

### Active Harness Use

The PM should use OMX harnesses as evidence and planning surfaces when they materially improve the workshop, not only list them as suggestions. If the current Codex surface cannot execute a selected harness, the PM must record the fallback command, expected artifact, and why the PM output is still provisional.

Use the lightest branch that can produce a safe handoff:

- `none`: small, clear, low-risk work; produce a standard bundle directly.
- `chrome-devtools`: user-provided site needs public read-only browser evidence before PM can judge feasibility or implementation direction.
- `$best-practice-research`: current external best practices, official upstream behavior, standards, SDK/API behavior, or version-aware guidance may change the option set.
- `$deep-interview`: unclear product intent, user value, non-goals, constraints, or human approval points.
- `$ralplan`: clear enough requirements but unresolved architecture, sequencing, tradeoff, DB/API/auth/payment/state-machine, or test strategy concerns.
- `$ultragoal`: clear goal and plan but needs durable repo-native artifacts, multi-goal sequencing, execution packets, or long-running Claude handoff documents.
- `$team`: large or multi-lane work needing parallel document, architecture, data, test, or risk analysis before a long Claude handoff.
- `$ultraqa`: critical journey, auth, payment, data-integrity, state-transition, regression-heavy, or release-readiness work needing adversarial QA scenarios.

When several branches apply, run at most one harness first unless its result makes the next branch clearly necessary. Prefer this order:

1. `chrome-devtools`
2. `$best-practice-research`
3. `$deep-interview`
4. `$ralplan`
5. `$ultragoal`
6. `$team`
7. `$ultraqa`

If OMX runtime is unavailable, the PM output must include:

- Selected branch
- Reason
- Recommended next command
- Expected artifact
- Fallback PM bundle

## Required Schemas

### BRAINSTORM.md

- Problem statement
- User/customer value
- Business goal
- Conversation mode
- Discovery dossier
- Research notes, when external evidence was needed
- Site investigation notes, when a URL or external site was inspected
- Design materiality notes and Designer routing decision
- Workflow decision gate
- Options considered
- Risks and assumptions
- Open decisions
- Required SoT documents
- Required design SoT documents, if any
- Recommended bundle depth
- OMX harness decision
- Human approval points

### RFC

- Context
- Decision to make
- Options
- Tradeoffs
- Recommendation
- Rejected alternatives
- Human decision record
- Follow-up TASK_SPEC candidates

### Decision Log

- Decision
- Decider
- Date/status
- Drivers
- Alternatives rejected
- Consequences
- Follow-ups

### Claude Handoff

- Work objective
- Source-of-truth documents
- DESIGN_SPEC / Figma sources / visual QA checklist, when UI/UX is material
- Ordered implementation tasks
- Explicit non-goals
- Allowed files or areas
- Blocked files or areas
- Acceptance criteria
- Test commands
- Stop conditions
- Pre-implementation OMX harness requirement, if any
- Artifact-generation OMX harness requirement, if any
- Post-implementation QA/review harness requirement, if any
- Required design-review and visual-qa-review gates, if any
- What to report in PR notes

### Multi-TASK_SPEC Sequence

- Sequence overview
- TASK_SPEC candidates
- Dependency order
- Parallelizable vs sequential work
- Shared SoT
- Shared risks
- Completion gate for each TASK_SPEC

## Technical / DB SoT Roles

When work touches data or persistence, include draft roles for:

- Data model changes
- Database schema changes
- RLS or permission changes
- Migration/rollback policy
- Seed/test data impact
- API/query/RPC contract impact

PM plugin must not apply migrations, execute production schema changes, or grant/revoke production permissions.

## Design SoT Roles

When work touches material UI/UX, include draft roles for:

- Design intent
- Screen and UX flow
- Component anatomy, variants, and states
- Responsive behavior
- Accessibility notes
- Figma source and write-scope approval
- Visual QA checklist

PM plugin must not run Claude Designer directly or mutate Figma. PM only routes and packages the Designer handoff.

## PM / Reviewer Boundary

PM plugin may prepare reviewer checklist candidates and PM-document quality checks.

PM plugin must not produce final PR/diff verdicts, approve implementation correctness, or replace `reviewer-plugin:pr-review`.

Future PM document review should be a separate Reviewer plugin skill.
