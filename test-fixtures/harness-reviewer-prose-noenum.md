# Fixture: reviewer verdict — unparseable (prose, no decision enum)

Drives the unparseable path: `.done` exists but the verdict body has no single valid
decision token (`GO|STOP|NEEDS_CHECK`).

## read-screen frame (tail)

```text
[reviewer] wrote docs/changes/REVIEW_L003_1.md
<<<HARNESS_VERDICT_DONE id=L003_1>>>
```

## verdict file: docs/changes/REVIEW_L003_1.md

```md
# Review Verdict — L003_1

I looked at the change and it mostly seems fine, though I have a few mixed feelings about
the error handling and I'm not totally sure about the test coverage. Overall it's probably
okay-ish but I didn't write a decision line.
```

## Expected orchestrator behavior

- Parse triggered by `.done`; no `## Review Decision` with exactly one enum token found.
- Route to the unparseable path: **retry once** (bump `attempt` → re-send) → if the retry
  is still unparseable → escalate **NEEDS_CHECK** + `cmux notify`.
- MUST NOT hang or silently time out, and MUST NOT fabricate a GO/STOP.
