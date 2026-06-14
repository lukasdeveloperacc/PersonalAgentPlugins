# Fixture: reviewer verdict — GO

Represents a completed reviewer turn. The shim returns the read-screen frame (with the
sentinel) and the verdict file content; the `.done` marker is simulated as present.

## read-screen frame (tail)

```text
[reviewer] wrote docs/changes/REVIEW_L001_1.md
[reviewer] verdict: GO
<<<HARNESS_VERDICT_DONE id=L001_1>>>
```

## verdict file: docs/changes/REVIEW_L001_1.md

```md
# Review Verdict — L001_1

## Review Decision
GO

## Findings
(none blocking)

## Suggested Fixes
- Consider adding a negative-path test later (minor).

## Questions For Orchestrator
(none)
```

## Expected orchestrator behavior

- Parse triggered by `.done` existence (not the sentinel).
- DECIDE: the minor suggestion → DEFER (not blocking). `remaining_criteria` may reach 0.
- With `remaining_criteria == 0`, convergence predicate holds → DONE.
