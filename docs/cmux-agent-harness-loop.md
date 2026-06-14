# cmux-agent-harness-loop — Usage & Design Notes

A maintainer-facing companion to the plugin. The authoritative runtime rules live in the
plugin-local contracts (`claude/plugins/cmux-agent-harness-loop-plugin/contracts/`); this
file is a mirror and explainer.

## What it is

A generalized, persistent, cmux-pane-based multi-agent harness loop for general software
development. A **Claude/OMC orchestrator** drives a persistent **OMX/Codex reviewer pane**
through cmux, accumulates shared memory in the target project's `docs/changes/`, and gates
each loop on the reviewer's STOP/GO verdict. It is not tied to any framework, app, or domain.

## Commands

```text
/cmux-agent-harness-loop setup
/cmux-agent-harness-loop status
/cmux-agent-harness-loop plan "<request>"
/cmux-agent-harness-loop review
/cmux-agent-harness-loop loop "<request>"
/cmux-agent-harness-loop handoff
```

## Transport — cmux-only, both-channels

Every review uses all three mechanisms; none is replaced by file-only handoff:

1. **`cmux send` / buffer paste** injects the prompt into an already-running
   interactive OMX/Codex pane.
2. **`cmux read-screen`** observes pane liveness + an end-of-turn sentinel.
3. **A structured verdict file** (`docs/changes/REVIEW_<loop>_<attempt>.md`) is the
   *authoritative* parse, read only after its `.done` marker exists.

This honors the literal acceptance criteria ("sends prompt via cmux send" and "reads
response via cmux read-screen") while keeping the decision deterministic (the file parse,
gated on `.done`, not on the screen sentinel).

## Ask-family ban scope, and why interactive OMX prompt injection is allowed

The plugin forbids the **one-shot advisor family**: `/oh-my-claudecode:ask`, `omc ask`,
`omx ask`, raw provider one-shot advisors, and API-router one-shot calls. The ban is about
*transport*: a fire-and-forget advisor call made outside cmux.

Starting `omx` (or fallback `codex`) **inside a cmux pane once**, then injecting prompts with
`cmux send`/`set-buffer`/`paste-buffer`, is NOT the ask family. It is persistent,
multi-turn, pane-resident orchestration observed via `read-screen`.

By contrast, `cmux omx exec`, `omx exec`, `codex exec`, and `codex exec review` are forbidden
by default because they create a one-shot/non-interactive path and lose the live conversation
the user wants. Use those exec forms only if a human explicitly asks for non-interactive exec
instead of pane conversation.

## Distinction from `omc team N:codex`

`omc team N:codex` is a fire-and-forget worker mechanism: spin up a worker, get a result,
done. This plugin instead keeps a **persistent, stateful reviewer pane** that the
orchestrator reuses across loops, with durable context re-injected each review from
`docs/changes/*.md` + `state.json`. The persistence lives in the filesystem (durable,
re-injectable), not in fragile TUI scrollback. They are complementary mechanisms for
different shapes of work; this plugin deliberately chooses the persistent-pane shape.

## Plugin definition vs runtime artifacts

The plugin repo ships: `SKILL.md` (with canonical inlined templates), the `templates/`
mirror, the contracts, and the manifests. It does **not** commit per-project runtime state.

`setup` generates the runtime artifacts in the **target project**:

```text
<target>/.agent-harness/{harness.yaml,state.json,panes.json,prompts/*}
<target>/.agent-harness/prompts/tmp/<loop-id>.txt
<target>/docs/changes/{TASK_SPEC,DECISIONS,REVIEW_LOG,TODO,HANDOFF}.md
<target>/docs/changes/REVIEW_<loop>_<attempt>.md (+ .md.done)
```

Add `.agent-harness/` to the **target project's** `.gitignore` (it is per-run runtime state,
not source). `setup` refuses to scaffold into the plugin repo itself.

## Template resolution (never DOA)

`${CLAUDE_PLUGIN_ROOT}/.../templates/` → marketplace cache glob → skill-dir-relative →
**inlined heredocs in SKILL.md (always works)**. The inlined heredocs are canonical;
`templates/` is a byte-identical mirror verified by `tests/sync_templates.py check` and
gated in `docs/release-checklist.md`.

## Loop termination (no infinite loops)

- Converge → DONE when `last_decision == GO && remaining_criteria == 0`.
- Hard ceiling `max_loops` (default 5) → terminate with `NEEDS_CHECK` + notify.
- Two consecutive identical-STOP loops → break to human with reason `NO_PROGRESS`.
- Never terminate silently.

## Scope (v0.1)

v0.1 ships orchestrator + reviewer + the loop. Worker, test, and browser panes are
deferred to v0.2.

## Verification

- The dry-run transport-shim suite (`tests/`) is runnable with no live cmux pane and is the
  CI gate. It asserts both-channels, setup idempotency, template fallback, verdict
  robustness, termination guards, and the safety negative checks.
- A manual scripted e2e checklist (in `docs/release-checklist.md`) covers the live-pane
  path before release.
