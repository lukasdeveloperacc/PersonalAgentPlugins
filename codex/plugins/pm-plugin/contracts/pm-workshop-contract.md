# PM Workshop Contract

This contract defines how the Codex PM plugin turns ideas into document bundles, backlog state proposals, TASK_SPEC candidates, and Claude handoffs.

## Operating Model

- GitHub is the state and tracking surface.
- Markdown is the decision, spec, and handoff source of truth.
- Slack is optional notification only and must not be treated as source of truth.
- Claude direct execution is out of v1 scope.
- Human approval is required for ambiguous decisions, final PR merge, release, and go-live.

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
- TASK_SPEC candidates
- Claude handoff

### Full Bundle

Escalate to full bundle when any condition applies:

- Work spans two or more PRs.
- Claude is expected to work for most of a day or longer.
- There are two or more viable product or technical options.
- API, DB, auth, payment, route, or state machine changes are involved.
- Multiple SDD documents are affected.
- Roadmap or priority conflicts exist.
- Human strategy decision is required.

Full bundle adds:

- RFC
- Roadmap/backlog ranking
- GitHub Issue/Project update plan
- Explicit decision log
- Multi-TASK_SPEC execution sequence

## OMX Harness Branching

The PM plugin may use OMX harnesses as planning and validation surfaces when the current Codex session supports OMX runtime workflows. Harnesses are not Developer execution and must not run Claude.

Use the lightest branch that can produce a safe handoff:

- `none`: small, clear, low-risk work; produce a standard bundle directly.
- `$deep-interview`: unclear product intent, user value, non-goals, constraints, or human approval points.
- `$ralplan`: clear enough requirements but unresolved architecture, sequencing, tradeoff, DB/API/auth/payment/state-machine, or test strategy concerns.
- `$ultragoal`: clear goal and plan but needs durable repo-native artifacts, multi-goal sequencing, execution packets, or long-running Claude handoff documents.
- `$team`: large or multi-lane work needing parallel document, architecture, data, test, or risk analysis before a long Claude handoff.
- `$ultraqa`: critical journey, auth, payment, data-integrity, state-transition, regression-heavy, or release-readiness work needing adversarial QA scenarios.

When several branches apply, run at most one harness first unless its result makes the next branch clearly necessary. Prefer this order:

1. `$deep-interview`
2. `$ralplan`
3. `$ultragoal`
4. `$team`
5. `$ultraqa`

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
- Options considered
- Risks and assumptions
- Open decisions
- Required SoT documents
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

## PM / Reviewer Boundary

PM plugin may prepare reviewer checklist candidates and PM-document quality checks.

PM plugin must not produce final PR/diff verdicts, approve implementation correctness, or replace `reviewer-plugin:pr-review`.

Future PM document review should be a separate Reviewer plugin skill.
