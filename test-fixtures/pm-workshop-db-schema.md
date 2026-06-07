# PM Workshop Fixture: DB Schema Impact

## Input

Add caregiver availability windows and expose them through booking search.

## Expected Skill

`pm-plugin:brainstorm`

## Expected Output Class

Full bundle.

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
