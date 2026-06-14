# Fixture: reviewer verdict — clarifying question (NEEDS_CHECK)

Drives the clarifying-question path: the reviewer emits NEEDS_CHECK with a question.

## read-screen frame (tail)

```text
[reviewer] wrote docs/changes/REVIEW_L004_1.md
[reviewer] verdict: NEEDS_CHECK
<<<HARNESS_VERDICT_DONE id=L004_1>>>
```

## verdict file: docs/changes/REVIEW_L004_1.md

```md
# Review Verdict — L004_1

## Review Decision
NEEDS_CHECK

## Findings
1. [major] The request says "add auth" but does not specify the auth method.

## Suggested Fixes
- Confirm intended auth method before implementing.

## Questions For Orchestrator
- Should this use session cookies, JWT, or an external IdP? The choice changes the design.
```

## Expected orchestrator behavior

- Parse on `.done`; decision token is `NEEDS_CHECK`.
- Surface the question to the human via `cmux notify`; record under HANDOFF / DECISIONS.
- Do NOT converge; do NOT fabricate a GO/STOP. Loop pauses pending human input.
