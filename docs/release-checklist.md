# Release Checklist — cmux-agent-harness-loop-plugin

## Schema Gate

- Verify current official Claude plugin manifest and marketplace schema.
- Record schema evidence before publishing.
- Update manifests if official schemas differ from this repository.

## Local Validation

- Parse every JSON manifest (`marketplace.json`, `plugin.json`, `.mcp.json`).
- Validate the Claude plugin/marketplace with `claude plugin validate ./claude` when available.
- Confirm the required skill file exists: `claude/plugins/cmux-agent-harness-loop-plugin/skills/cmux-agent-harness-loop/SKILL.md`.
- Confirm the skill has role, subcommand dispatch, transport playbook, loop spec, and output format.
- Confirm all four contracts exist: `cmux-transport-contract.md`, `harness-loop-contract.md`, `review-verdict.md`, `safety-contract.md`.
- Confirm root `docs/cmux-transport-contract.md` mirror is synced with the plugin-local `contracts/cmux-transport-contract.md`.

## Inlined-template / mirror diff gate (FAIL-CLOSED)

- The inlined heredoc templates in `SKILL.md` are **canonical**. The `templates/` directory is a byte-identical mirror.
- Run `tests/run_dryrun_suite.sh` (which runs `python3 tests/sync_templates.py check` first). A byte mismatch **blocks release**.
- When a mismatch is found, fix `templates/` to match the SKILL.md heredocs (heredocs are the source of truth), never the reverse.

## Smoke / Dry-run tests (no live cmux pane required)

- Run the dry-run transport-shim suite `tests/run_dryrun_suite.sh`; it must pass with `CMUX_SURFACE_ID` unset.
  - Both-channels assertion: a single `review` emits a `cmux send`, a `cmux read-screen` that detects the sentinel, and a parse of the verdict file.
  - `setup` idempotency: run twice → no corruption, write-missing-only.
  - Template fallback: `CLAUDE_PLUGIN_ROOT` unset → resolves to inlined heredocs.
  - Verdict robustness: unparseable verdict → retry once → NEEDS_CHECK; clarifying question → NEEDS_CHECK; pane death mid-review → respawn/new-split recovery.
  - Termination: identical STOP findings twice → break to human (`NO_PROGRESS`); `max_loops`+1 non-converging rounds → terminate with NEEDS_CHECK.
- Run the safety negative tests: no secret patterns in emitted commands/pane input; no dangerous flags; no `/ask`/`omc ask`/`omx ask` transport strings.

## Manual E2E (live cmux pane, required before release)

Inside a real cmux pane:

1. `/cmux-agent-harness-loop setup` → reviewer pane created, runtime launched, panes.json populated, template source printed.
2. `/cmux-agent-harness-loop review` on a real diff → observe real `send`, real read-screen sentinel, verdict file parsed, verdict surfaced.
3. Kill the reviewer pane mid-review → recovery via respawn/new-split → review completes.
4. `/cmux-agent-harness-loop status` → correct liveness + last_loop_at.
5. Confirm no secrets in `REVIEW_LOG.md`; no dangerous flags in any emitted command.

## Publishing

- Tag releases after local validation and the dry-run suite pass.
- Keep v0.x conservative; worker/test/browser panes are deferred to v0.2.
- Add new MCP, hooks, or automation only in later versions with a separate review.
