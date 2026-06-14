# Review Verdict Contract

Defines the verdict the reviewer emits, the **normative ordering** for writing it, and how
the orchestrator parses it deterministically. Authoritative for the REVIEW state.

## 1. Verdict format (reviewer output)

The reviewer MUST write a verdict file containing a `## Review Decision` section with
**exactly one** of these tokens, mirroring the repo's reviewer convention
("Use exactly one"):

```text
GO | STOP | NEEDS_CHECK
```

Verdict file body:

```md
# Review Verdict — <loop_id>_<attempt>

## Review Decision
<one of: GO | STOP | NEEDS_CHECK>

## Findings
1. [critical|major|minor] <finding> — <file:line if known>
2. ...

## Suggested Fixes
- ...

## Questions For Orchestrator
- ... (if any; presence implies NEEDS_CHECK)
```

- `GO` — no blocking issues; proceed.
- `STOP` — blocking issues found; do not proceed until addressed.
- `NEEDS_CHECK` — the reviewer is uncertain or is asking a clarifying question; the human
  / orchestrator must resolve before proceeding.

## 2. Normative write ordering (reviewer) — MUST follow exactly

Two completion signals exist (the `.done` marker file and the screen sentinel). To make
them race-free, the reviewer MUST produce them in this strict happens-before order:

1. Write the verdict to `docs/changes/REVIEW_<loop_id>_<attempt>.md.tmp`; flush.
2. **Atomically rename** `.tmp` → `docs/changes/REVIEW_<loop_id>_<attempt>.md`.
   *(Rename is the commit point: a reader never observes a half-written final file.)*
3. **Only after** the rename returns, create the marker
   `docs/changes/REVIEW_<loop_id>_<attempt>.md.done`.
4. **Only after** `.done` exists, print the screen sentinel
   `<<<HARNESS_VERDICT_DONE id=<loop_id>_<attempt>>>>`.

The reviewer prompt template (`prompts/reviewer.md`) instructs the reviewer to do exactly
this, with the concrete `loop_id`/`attempt`/paths injected.

## 3. Orchestrator parse rule — MUST follow exactly

- **The parse trigger is `.done` file existence. NEVER the screen sentinel.** The sentinel
  is only a liveness/latency hint that tells the orchestrator to begin/accelerate polling
  for `.done`.
- Both the verdict file and the `.done` marker are keyed by `{loop_id}+{attempt}` so a
  post-respawn re-send (a new `attempt`) can never read a stale prior-attempt `.done`.
- The orchestrator reads `REVIEW_<loop_id>_<attempt>.md` **only** once
  `REVIEW_<loop_id>_<attempt>.md.done` exists.

## 4. Failure / edge handling

| Situation | Handling |
|---|---|
| `.done` never appears within timeout | Failed-turn path: `respawn-pane`/`new-split`, bump `attempt`, re-send the same prompt. On a **second** timeout → `NEEDS_CHECK` + `cmux notify` the human. |
| `.done` exists but the verdict file is **missing or unparseable** (no single valid decision token) | Route to the unparseable path: **retry once** (bump `attempt`, re-send) → still unparseable → `NEEDS_CHECK` + `cmux notify`. Never hang or silently time out. |
| Verdict body contains a clarifying question / no decision token | Treat as `NEEDS_CHECK`; surface the question to the human. Do not fabricate a GO/STOP. |
| Reviewer pane dies mid-review | `respawn-pane` → if it fails, `new-split` a fresh reviewer; bump `attempt`; re-send (idempotent because files are keyed by `loop_id+attempt`); record the recovery in `REVIEW_LOG.md`. |

## 5. Mapping verdict → DECIDE

- `GO` → orchestrator may converge (subject to `remaining_criteria == 0`).
- `STOP` → orchestrator runs DECIDE on each finding (ACCEPT/REJECT/NEEDS_CHECK/DEFER);
  ACCEPT items become TODO and feed NEXT_LOOP.
- `NEEDS_CHECK` → orchestrator surfaces to the human; does not converge.

See `harness-loop-contract.md` §2 for how repeated `STOP` with identical findings triggers
the `NO_PROGRESS` break.
