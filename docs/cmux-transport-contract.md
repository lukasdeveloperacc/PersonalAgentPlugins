<!-- MIRROR: synced with claude/plugins/cmux-agent-harness-loop-plugin/contracts/cmux-transport-contract.md — edit the plugin-local copy, then resync. Verified by tests/check_docs_mirror.sh. -->

# cmux Transport Contract

This contract defines the **only** transport the harness may use to run agents, deliver
prompts, and observe results. It is authoritative for the `cmux-agent-harness-loop` skill.

## 1. cmux-only rule

All agent execution, prompt delivery, and result observation MUST go through cmux panes.

**Forbidden (the "ask family" — one-shot advisor calls):**

```text
/oh-my-claudecode:ask
omc ask
omx ask
provider ask (raw codex/claude/gemini one-shot advisor)
any API-router / one-shot advisor call
```

**Allowed transport verbs:**

```text
cmux new-split          cmux send            cmux send-key
cmux read-screen        cmux list-panels     cmux respawn-pane
cmux notify             cmux set-buffer      cmux paste-buffer
cmux workspace          cmux browser
cmux omc                cmux omx             (interactive pane bootstrap only — see §5)
```

## 2. Verify CLI syntax first (session-scoped gate)

The PRD's command shapes were assumptions. The CLI surface below is the **verified**
truth as of plugin authoring, but cmux/omx/codex versions drift. Therefore:

- Before the **first** cmux / omx / codex command of a session, run `<cmd> --help` once
  for each subcommand you will use and confirm the flag surface.
- Cache the result in `.agent-harness/state.json` under `cli_verified` as
  `{ "<cmd>": { "checked_at": "<iso>", "surface_hash": "<hash>" } }`.
- Skip the probe when the cache is fresh for the current session.
- The dry-run suite asserts the cached surface matches this table; a mismatch FAILS LOUDLY.
- Never hardcode a command shape that has not been `--help`-confirmed this session.

## 3. Verified CLI surface

| Need | Command | Notes |
|---|---|---|
| split for a reviewer pane | `cmux new-split <left\|right\|up\|down> [--surface <ref>] [--focus true\|false]` | the handle is `--surface` (refs like `surface:N`), **NOT `--pane`**; default `--focus false` so it does not steal focus |
| deliver a prompt / command | `cmux send [--surface <ref>] [--] "text\n"` | `\n`/`\r` → Enter, `\t` → Tab |
| send a raw key event | `cmux send-key [--surface <ref>] <key>` | e.g. interrupts |
| read pane output | `cmux read-screen [--surface <ref>] [--scrollback] [--lines <n>]` | liveness probe + sentinel scan |
| enumerate surfaces | `cmux list-panels [--workspace <ref>]` | discover/reuse a reviewer surface; liveness |
| recreate a dead pane | `cmux respawn-pane [--surface <ref>] [--command <cmd>]` | mid-loop recovery |
| notify the human | `cmux notify --title <t> --body <b> [--surface <ref>]` | STOP/GO surfacing |
| stage large text | `cmux set-buffer --name <n> <text>` | escaping-safe long prompts |
| paste staged text | `cmux paste-buffer --name <n> [--surface <ref>]` | pair with set-buffer |

Environment handles:

```text
$CMUX_SURFACE_ID     the current (orchestrator) pane; empty ⇒ NOT inside cmux ⇒ dry-run only
$CMUX_WORKSPACE_ID   the workspace; used for list-panels --workspace
```

## 4. Both-channels review transport (literal PRD compliance + determinism)

Every `review` MUST exercise all three mechanisms. None may be dropped or replaced by a
file-only handoff.

1. **`cmux send` — injects the prompt into a live interactive pane.** The orchestrator
   starts or reuses an interactive OMX/Codex reviewer surface, then pastes/sends the prompt
   directly into that running TUI/REPL. Long prompt bodies are staged to
   `.agent-harness/prompts/tmp/<loop-id>.txt` and injected via `set-buffer` +
   `paste-buffer` + Enter, or by `cmux send` chunks. **Do not use `omx exec`,
   `codex exec`, or any non-interactive exec path by default.**

2. **`cmux read-screen` — liveness + latency hint.** The orchestrator polls
   `cmux read-screen --surface <reviewer> --scrollback --lines 200` for pane liveness and
   the end-of-turn sentinel `<<<HARNESS_VERDICT_DONE id=<loop_id>_<attempt>>>>`.
   *(Satisfies "reads response via cmux read-screen".)* **The sentinel is NEVER the parse
   trigger** — see `review-verdict.md`.

3. **Verdict file — authoritative parse.** The reviewer writes the structured verdict to
   `docs/changes/REVIEW_<loop_id>_<attempt>.md`, then creates a `.done` marker. The
   orchestrator parses the **file** only after the `.done` marker exists. Ordering and
   atomicity are normative in `review-verdict.md`.

`read-screen` is the transport/liveness channel; the file is the deterministic parse.

## 5. Interactive pane orchestration with OMC / OMX

The desired transport is a **live, persistent, interactive pane**. The orchestrator may start
the runtime in a pane, but must then converse by prompt injection, not by one-shot exec.

Allowed bootstrap examples:

```text
cmux new-split right --focus false
cmux send --surface <reviewer> -- "omx\n"       # start interactive OMX in that pane
# fallback when OMX is unavailable:
cmux send --surface <reviewer> -- "codex\n"     # start interactive Codex in that pane
```

Allowed prompt injection examples:

```text
cmux set-buffer --name harness "$(cat .agent-harness/prompts/tmp/<id>.txt)"
cmux paste-buffer --name harness --surface <reviewer>
cmux send --surface <reviewer> -- "\n"          # submit to the already-running CLI
cmux read-screen --surface <reviewer> --scrollback --lines 200
```

Forbidden by default for this harness transport because it bypasses the persistent
conversation the user expects:

```text
cmux omx exec ...
omx exec ...
codex exec ...
codex exec review ...
```

Those exec forms are not the ask-family, but they are still **not** the interactive
Socrates/harness transport. Use them only if a human explicitly requests non-interactive exec
for a specific run; v0.1 does not choose them automatically.

## 6. Prompt-via-tempfile

For prompts > ~1500 chars or any multi-line prompt:

1. Write the body to `.agent-harness/prompts/tmp/<loop-id>.txt`.
2. Deliver via cmux only: `set-buffer` → `paste-buffer` into the already-running OMX/Codex pane → Enter.
3. Final transport is always cmux prompt injection. Clean temp files on DONE.

## 7. Safety (see safety-contract.md for the full rule set)

- Never print API keys, full env, or read secret files over the transport.
- Never use dangerous flags by default (`--dangerously-skip-permissions`, `--yolo`,
  `-a never`, `--approval-mode never`).
- The reviewer never edits source files by default.
