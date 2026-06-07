# PM Workshop Fixture: Full Bundle Epic

## Input

Design a multi-step reservation lifecycle redesign that changes user, driver, and manager flows over several PRs.

## Expected Skill

`pm-plugin:brainstorm`

## Expected Output Class

Full bundle.

## Expected OMX Harness Branch

- Selected branch: `$ralplan`
- Reason: The request spans multiple PRs and affects state machine, route behavior, sequencing, and test strategy.
- Follow-up branch: `$ultragoal` should be recommended after `$ralplan` to produce durable repo-native artifacts and multi-TASK_SPEC execution packets. `$team` may be recommended if the plan needs parallel document, architecture, test, or data analysis.
- Execution: Run `$ralplan` automatically when OMX runtime is available; otherwise emit the fallback command and expected artifact.

## Escalation Reasons

- Work spans two or more PRs.
- State machine and route behavior are affected.
- Multiple SDD documents are affected.
- Claude is expected to work for most of a day or longer.

## Expected Documents

- BRAINSTORM
- PRD or FEATURE_SPEC
- STATE_MACHINE draft
- ROUTE_MAP draft
- RFC
- Roadmap/backlog ranking
- GitHub Issue/Project update plan
- Multi-TASK_SPEC sequence
- Claude handoff
