# Safety Contract

Authoritative safety rules for the `cmux-agent-harness-loop` skill. These are hard
constraints; the skill MUST NOT relax them by default.

## 1. Forbidden — the "ask family" (one-shot advisor calls)

```text
/oh-my-claudecode:ask
omc ask
omx ask
provider ask (raw one-shot codex/claude/gemini advisor)
any API-router / one-shot advisor call
```

**Scope of the ban:** it applies to the harness's *transport* choices. The ban targets
one-shot, fire-and-forget advisor calls made outside cmux.

**Explicitly ALLOWED (not the ask family):** launching an interactive runtime inside a cmux
pane, then injecting prompts with `cmux send` / `set-buffer` / `paste-buffer` and observing
with `cmux read-screen`. `cmux omx exec`, `omx exec`, and `codex exec` are not ask-family
commands, but they are forbidden by default for this harness because they bypass the persistent
conversation model. See `cmux-transport-contract.md` §5.

## 2. Forbidden — dangerous flags (never by default)

```text
--dangerously-skip-permissions
--yolo
-a never
--approval-mode never
```

The harness MUST NOT emit these as part of any command it sends to a pane. They may only
ever appear if the human explicitly and durably authorizes them for a specific run, which
v0.1 does not provide a path for.

## 3. Forbidden — secret / environment exposure

- Never print API keys or tokens to a pane or into shared memory.
- Never dump the full environment (`env`, `printenv` with no filter) over the transport.
- Never read secret files (`.env`, `*.pem`, credential stores) and never echo their
  contents into `REVIEW_LOG.md` or any `docs/changes/*.md`.
- Redact env names matching these patterns before writing anything to shared memory:
  `*_API_KEY`, `*_TOKEN`, `*_SECRET`, `*_PASSWORD`.

## 4. Forbidden — reviewer source mutation

The reviewer (OMX/Codex) runs with the instruction to **not modify source files** unless
the orchestrator explicitly tells it to. The reviewer's job is to emit a verdict, not to
edit code. The orchestrator (Claude/OMC) is the only role that mutates source by default.

## 5. Allowed operations

```text
git branch --show-current / git rev-parse --abbrev-ref HEAD
git status --short
git diff --stat   (and --cached)
explicit file reads of non-secret files
cmux pane control (new-split, send, send-key, read-screen, list-panels, respawn-pane, notify, set-buffer, paste-buffer)
interactive OMX/Codex pane bootstrap + prompt injection
writing shared-memory markdown under docs/changes/
writing runtime state under .agent-harness/
```

## 6. setup guard

`setup` MUST refuse to scaffold runtime artifacts (`.agent-harness/`, `docs/changes/`) into
the plugin repository itself. Detection: if the current working directory (or an ancestor)
contains `.claude-plugin/` or a `*/marketplace.json` that names this plugin, refuse and
report — runtime artifacts belong in a *target* project, not in the plugin definition repo.

## 7. Negative tests (enforced by the dry-run suite)

The dry-run suite asserts, over every command the harness would emit and every byte it
would send to a pane:

- Zero occurrences of secret patterns (`*_API_KEY`, tokens, `.env` reads).
- Zero occurrences of the dangerous flags in §2.
- Zero occurrences of the ask-family strings in §1 (`/ask`, `omc ask`, `omx ask`) as
  transport.
- Zero default-use occurrences of non-interactive exec transport (`cmux omx exec`, `omx exec`,
  `codex exec`, `codex exec review`).
