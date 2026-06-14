# Fixture: reviewer verdict — STOP (3 findings)

Drives the STOP path and the no-progress detector (when the same STOP is returned twice).

## read-screen frame (tail)

```text
[reviewer] wrote docs/changes/REVIEW_L002_1.md
[reviewer] verdict: STOP
<<<HARNESS_VERDICT_DONE id=L002_1>>>
```

## verdict file: docs/changes/REVIEW_L002_1.md

```md
# Review Verdict — L002_1

## Review Decision
STOP

## Findings
1. [critical] Missing input validation in handleUpload() — src/upload.ts:42
2. [major] No test covers the empty-file branch — tests/upload.test.ts
3. [minor] Magic number 1048576 should be a named constant — src/upload.ts:55

## Suggested Fixes
- Validate file size and type before write.
- Add an empty-file unit test.
- Extract MAX_UPLOAD_BYTES.

## Questions For Orchestrator
(none)
```

## Expected orchestrator behavior

- Parse on `.done`.
- DECIDE: #1 ACCEPT, #2 ACCEPT, #3 DEFER → 2 TODO items; NEXT_LOOP.
- If a subsequent loop returns an **identical** STOP findings set (same hash) → NO_PROGRESS
  break to human + notify.
