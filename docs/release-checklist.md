# Release Checklist — cmux-agent-harness-loop-plugin

## Schema Gate

- Verify current official Claude plugin manifest and marketplace schema.
- Record schema evidence before publishing.
- Update manifests if official schemas differ from this repository.

## Local Validation

- Parse every JSON manifest (`marketplace.json`, `plugin.json`, `.mcp.json`).
- Validate the Claude plugin/marketplace with `claude plugin validate ./claude` when available.
- Confirm the required skill file exists: `claude/plugins/cmux-agent-harness-loop-plugin/skills/cmux-agent-harness-loop/SKILL.md`.
- Confirm the harness skill has role, subcommand dispatch, transport playbook, loop spec, and output format.
- Confirm the Socrates skill exists, collects idea/mode/experience, uses Codex reflection, offers the direction-choice menu, and hands off to `document-specialist`.
- Confirm `agents/document-specialist.md` exists, is document-only, owns `ULTRAGOAL_DRAFT.md`, and writes the six-file Ralplan-ready bundle.
- Confirm Claude lane agents exist and do not auto-run from planning modes: `claude-codex-orchestrator`, `front-developer`, `backend-developer`, `infra-developer`, `ai-engineering-developer`.
- Confirm all six core contracts exist: `cmux-transport-contract.md`, `harness-loop-contract.md`, `review-verdict.md`, `safety-contract.md`, `socrates-workshop-contract.md`, `role-lane-contract.md`.
- Confirm Socrates bundle templates exist in both Claude and Codex plugin mirrors: `RALPLAN_BRIEF.md`, `INTERVIEW_EVIDENCE.md`, `RALPLAN_DR_SEED.md`, `ULTRAGOAL_DRAFT.md`, `ROLE_PANE_MAP.md`, `MCP_READINESS_CHECKLIST.md`.
- Confirm root `docs/cmux-transport-contract.md` mirror is synced with the plugin-local `contracts/cmux-transport-contract.md`.

## Inlined-template / mirror diff gate (FAIL-CLOSED)

- The inlined heredoc templates in `SKILL.md` are **canonical**. The `templates/` directory is a byte-identical mirror.
- Run `tests/run_dryrun_suite.sh` (which runs `python3 tests/sync_templates.py check` first). A byte mismatch **blocks release**.
- When a mismatch is found, fix `templates/` to match the SKILL.md heredocs (heredocs are the source of truth), never the reverse.

## Codex companion validation

- Parse `codex/.agents/plugins/marketplace.json` and `codex/plugins/socrates-codex-partner-plugin/.codex-plugin/plugin.json`.
- Run `python3 /Users/chaejin/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py codex/plugins/socrates-codex-partner-plugin`.
- Run `python3 codex/plugins/socrates-codex-partner-plugin/tests/test_static.py`.
- Confirm all Codex companion skills are Korean-first and forbid `/ask`/`omc ask`/`omx ask`.
- Confirm every Codex role skill has `skills/<role>/agents/openai.yaml` agent metadata.
- Confirm existing core roles remain valid: `socrates-partner`, `socrates-document-specialist`, `harness-reviewer`.
- Confirm new Codex companion lanes exist: `socrates-pm`, `idea-reviewer`, `design-reviewer`, `code-reviewer`, `ai-researcher`, `surfer-researcher`, `ralplan-partner`.
- Confirm `socrates-document-specialist` writes the Ralplan-ready bundle and marks `ULTRAGOAL_DRAFT.md` as draft-only/no-auto-run.

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
6. Run `/cmux-agent-harness-loop-plugin:socrates` on a sample idea → choose `토론모드` + one experience level → verify Codex reflection is surfaced, direction menu appears, and docs/changes/SOCRATES_BRIEF.md + PRD.md + OUT_OF_SCOPE.md + HANDOFF.md plus `RALPLAN_BRIEF.md`, `INTERVIEW_EVIDENCE.md`, `RALPLAN_DR_SEED.md`, `ULTRAGOAL_DRAFT.md`, `ROLE_PANE_MAP.md`, and `MCP_READINESS_CHECKLIST.md` are produced.
7. Optional alias smoke: copy `templates/project-commands/socrates.md.tmpl` to target `.claude/commands/socrates.md`, reload Claude, and verify bare `/socrates` delegates to the plugin skill.
8. Codex companion live smoke: install `socrates-codex-partner-plugin`, then from the Codex pane run a sample `socrates-partner` reflection and one role-agent profile such as `socrates-pm` or `ralplan-partner`; verify Korean structured output.

## Publishing

- Tag releases after local validation and the dry-run suite pass.
- Keep v0.x conservative; worker/test/browser panes are deferred to v0.2.
- Add new MCP, hooks, or automation only in later versions with a separate review.
