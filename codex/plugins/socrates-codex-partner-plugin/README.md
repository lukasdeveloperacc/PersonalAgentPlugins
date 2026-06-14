# socrates-codex-partner-plugin

Codex companion plugin for the Claude `cmux-agent-harness-loop-plugin`.

It gives the Codex/OMX pane predictable roles for the video-style Socrates workflow:

- `socrates-partner` — Korean PM/critic reflection during idea discovery.
- `socrates-document-specialist` — Korean PRD/brief/handoff writer.
- `harness-reviewer` — file-authoritative STOP/GO reviewer for the cmux loop.

## Install from this repository

From the repository root:

```sh
codex plugin marketplace add ./codex
codex plugin add socrates-codex-partner-plugin@personal-agent-plugins-codex
```

## Claude ↔ Codex flow

1. Claude `/cmux-agent-harness-loop-plugin:socrates` hosts the user conversation.
2. Claude starts/reuses an interactive `omx` pane and injects a prompt through `cmux send` or
   buffer paste.
3. Codex uses `socrates-partner` to critique the idea in Korean.
4. When the user chooses `이대로 진행`, Codex can use `socrates-document-specialist` to write planning docs.
5. Later, `harness-reviewer` writes deterministic review verdict files for implementation loops.

No `/ask`, `omc ask`, `omx ask`, `omx exec`, `codex exec`, dangerous flags, or source edits by
default.
