# Fixture: feature request

Used to exercise INTAKE + classification (`feature`) and the both-channels review path.

## Request

Add a `/health` endpoint that returns `{ "status": "ok" }` with HTTP 200, and a unit test
covering the happy path.

## Expected classification

`feature`

## Expected INTAKE artifacts

- `docs/changes/TASK_SPEC.md` created with Request, Classified Type = `feature`, a Plan, and
  Acceptance Criteria.
- No cmux pane required for `plan`.
