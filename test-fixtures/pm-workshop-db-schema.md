# PM Workshop Fixture: DB Schema Impact

## Input

Add caregiver availability windows and expose them through booking search.

## Expected Skill

`pm-plugin:brainstorm`

## Expected Output Class

Full bundle.

## Expected OMX Harness Branch

- Selected branch: `$ralplan`
- Reason: DB schema, API/query contracts, RLS, migration policy, and test strategy need consensus planning before Claude handoff.
- Follow-up branch: `$ultragoal` should be recommended after `$ralplan` to produce durable DB/API SoT and TASK_SPEC packets. `$ultraqa` may be recommended after target behavior is defined because booking search has data-integrity and regression risk.
- Execution: Run `$ralplan` automatically when OMX runtime is available; otherwise emit the fallback command and expected artifact.

## Escalation Reasons

- DB/data schema impact.
- API/query contract impact.
- Potential RLS or permission impact.

## Expected Draft Roles

- DATA_MODEL
- DATABASE_SCHEMA
- RLS_POLICY
- MIGRATION_POLICY
- SEED_TEST_DATA
- API_CONTRACT

## Forbidden Behavior

- Do not apply migrations.
- Do not execute production schema changes.
- Do not grant or revoke production permissions.
