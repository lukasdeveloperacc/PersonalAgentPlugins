# Harness Loop Contract

Defines the loop the `cmux-agent-harness-loop` skill drives. The **5 observable states**
are authoritative for execution; the 13-state narrative is documentation only.

## 1. Observable states (authoritative)

The loop advances a single authoritative cursor: `state.json.stage`. Persist after every
transition so a session restart resumes exactly where it left off.

```text
INTAKE → EXECUTE → REVIEW → DECIDE → HANDOFF → (DONE | NEXT_LOOP)
```

| State | Action | Writes |
|---|---|---|
| **INTAKE** | Capture the request; assign `loop_id` + `attempt`; ensure `.agent-harness/` exists (else run `setup`). Folds classify + load_context + plan: classify into one request type (§3), gather branch/`git status -s`/`git diff --stat`, summarize project docs, draft the step plan. | `state.json` (`stage`, `loop_id`, `classified_type`), `docs/changes/TASK_SPEC.md` |
| **EXECUTE** | Orchestrator (Claude/OMC) makes the file changes for the plan. Worker/test/browser panes are **deferred to v0.2**; v0.1 executes in the orchestrator. | source files (orchestrator only) |
| **REVIEW** | Both-channels round-trip (see `cmux-transport-contract.md` §4 and `review-verdict.md`): ensure reviewer pane, inject the 9-item context, `cmux send` the exec, poll `read-screen` for the sentinel, parse the verdict file when `.done` exists. | `docs/changes/REVIEW_<loop_id>_<attempt>.md`, `REVIEW_LOG.md` |
| **DECIDE** | Claude judges each reviewer finding: ACCEPT / REJECT / NEEDS_CHECK / DEFER (§4). Only ACCEPT items become TODO. | `docs/changes/DECISIONS.md`, `docs/changes/TODO.md` |
| **HANDOFF** | Folds record: write REVIEW_LOG / TODO / DECISIONS / HANDOFF; `cmux notify` STOP/GO; set `last_loop_at`; evaluate termination (§2). | `docs/changes/HANDOFF.md`, `state.json` (`last_loop_at`, `loop_count`) |

## 2. Termination spec (must prevent infinite loops)

After HANDOFF, the `loop` driver evaluates termination using `state.json`:

- **Convergence predicate (success → DONE):** `last_decision == GO && remaining_criteria == 0`.
  When true, mark `state.json.converged = true`, clear the active `/goal` if this is an
  aggregate run's final story, and stop.
- **Iteration guard:** `state.json.loop_count` increments each completed loop. A hard
  ceiling `max_loops` (default **5**, from `harness.yaml`). On reaching the ceiling without
  convergence → terminate with `NEEDS_CHECK` + `cmux notify`. **Never terminate silently.**
- **No-progress detection:** if two consecutive loops produce **identical STOP findings**
  (same reviewer findings, no new ACCEPT items actioned), break to the human with reason
  `NO_PROGRESS` + `cmux notify`. This catches a reviewer that keeps rejecting the same way.
- **NEXT_LOOP:** otherwise re-enter INTAKE with the ACCEPT TODO items as the next request;
  bump `attempt`/`loop_id` as appropriate.

`state.json` fields backing termination: `loop_count`, `max_loops`, `converged`,
`last_decision`, `last_stop_findings_hash`, `remaining_criteria`.

## 3. Request classification (INTAKE)

Classify the request into exactly one type; record in `state.json.classified_type`:

```text
feature  bugfix  refactor  review  test  docs
architecture  security  performance  handoff  status  setup
```

The classification tunes the reviewer prompt emphasis and the plan shape; it does not
change the state machine.

## 4. DECIDE criteria

For each reviewer finding, Claude assigns one decision and records the rationale:

| Decision | Meaning |
|---|---|
| **ACCEPT** | Real, in-scope, worth doing this loop → becomes a TODO. |
| **REJECT** | Not a real issue, or out of scope / contradicts the user request. |
| **NEEDS_CHECK** | Plausible but unverified, or a clarifying question — surface to human. |
| **DEFER** | Real but better handled in a later loop / out of current scope. |

Judgement criteria: (1) matches real code; (2) matches the user request; (3) in-scope for
this loop; (4) implementation cost vs value; (5) hallucination risk. Claude does NOT
rubber-stamp the reviewer — the reviewer is advisory.

## 5. Roles

- **Orchestrator** (Claude / OMC): analyzes the request, plans, drives panes, makes the
  final judgement, edits files, records state. The only role that mutates source.
- **Reviewer / PM** (OMX / Codex): runs in a persistent pane; reviews requirement mismatch,
  bugs, security, architecture, missing tests, over-complexity, maintainability; returns a
  STOP/GO verdict + itemized findings. Does **not** modify source unless explicitly told.
- **Worker** (optional, v0.2): scoped implementation/test/refactor/docs work in its own pane.

## 6. 13-state narrative (documentation only — maps onto the 5 observable states)

The original PRD state machine, mapped to the authoritative cursor:

```text
IDLE         → (pre-INTAKE; stage = "IDLE")
INTAKE       → INTAKE
CLASSIFY     → INTAKE (folded)
LOAD_CONTEXT → INTAKE (folded)
PLAN         → INTAKE (folded)
DISPATCH     → EXECUTE (folded: choose orchestrator-direct vs worker)
EXECUTE      → EXECUTE
OBSERVE      → REVIEW (folded: collect changes + reviewer output)
REVIEW       → REVIEW
DECIDE       → DECIDE
RECORD       → HANDOFF (folded)
HANDOFF      → HANDOFF
DONE/NEXT    → termination (§2)
```

This mapping exists so readers of the PRD can trace each PRD stage, but the skill MUST
drive only the 5 observable states with `state.json.stage` as the cursor.
