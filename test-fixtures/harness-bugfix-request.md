# Fixture: bugfix request

Used to exercise INTAKE + classification (`bugfix`).

## Request

Fix the TypeError in `parseConfig()` when the config file is empty — it should return the
default config instead of throwing.

## Expected classification

`bugfix`

## Expected INTAKE artifacts

- `docs/changes/TASK_SPEC.md` with Classified Type = `bugfix`.
- A plan that reproduces, patches, and verifies (no scope broadening).
