# OMC Harness Contract

This contract defines how Claude Developer uses installed OMC surfaces during implementation, debugging, verification, and long-running work.

## Installed Evidence

This contract targets OMC / oh-my-claudecode `4.14.1`.

OMC exposes two different surfaces:

- In-session Claude skills: `/oh-my-claudecode:<skill>` or the short slash alias when available.
- Terminal CLI commands: `omc ...` from a shell.

Do not confuse the two surfaces. There is no supported `omc autopilot`, `omc ralph`, or `omc ultrawork` terminal subcommand in this OMC version.

## Primary Loop Authority

Use only one primary loop authority per task:

- Direct Developer loop for small, PR-sized work.
- `/oh-my-claudecode:ralph` for single-owner verified completion.
- `/oh-my-claudecode:team` for parallel staged execution inside Claude.
- `omc team ...` for tmux CLI workers outside the current Claude conversation.
- `/oh-my-claudecode:ultraqa` for repeated quality-gate diagnose/fix cycles.
- `omc ultragoal` for durable multi-story goal artifacts and Claude `/goal` handoff.

Do not start a second primary loop when one is active. If conflict exists, adopt the active loop, use artifact-only Ultragoal notes, or report the conflict as a blocker.

## Harness Selection Matrix

| Situation | Use | Reason |
| --- | --- | --- |
| TASK_SPEC is missing scope, acceptance criteria, allowed files, or design gates | `BLOCKED_BY_SPEC` | Developer must not invent PM scope. |
| Small scoped implementation with clear checks | Direct Developer loop | Lowest overhead. |
| Must finish fully with fresh verification and review pressure | `/oh-my-claudecode:ralph` | Persistent PRD-driven verify/fix loop. |
| Broad work spans independent files/modules or needs specialist coordination | `/oh-my-claudecode:team` | Canonical staged team pipeline. |
| Need external Codex/Gemini/Claude advisor artifact | `/oh-my-claudecode:ask` or `omc ask` | Captures `.omc/artifacts/ask/` evidence. |
| Need tmux CLI workers, especially Codex/Gemini panes | `omc team N:<provider> "..."` | Shell-side worker panes. |
| Tests/build/lint/typecheck are failing or need repeated cycling | `/oh-my-claudecode:ultraqa --tests|--build|--lint|--typecheck` | Bounded QA fix loop. |
| Need final confidence evidence without a fix loop | `/oh-my-claudecode:verify` | Evidence-first verification. |
| Browser UI/runtime issue | Chrome DevTools MCP plus `/oh-my-claudecode:visual-verdict` when visual references exist | Console/network/DOM/screenshot evidence. |
| Multi-story overnight work must survive session restart | `omc ultragoal create-goals` then `omc ultragoal complete-goals` | Durable `.omc/ultragoal/` ledger and Claude `/goal` handoff. |
| OMC itself behaves unexpectedly | `/oh-my-claudecode:debug` | Inspect state, trace, logs, and runtime evidence. |

## Developer Boundaries

- Developer may use Chrome DevTools MCP for local or approved public runtime inspection.
- Developer must not submit forms, change account settings, place orders, bypass access controls, or inspect authenticated sessions unless explicitly approved.
- Developer may read DESIGN_SPEC and Figma source URLs, but must not mutate Figma. Figma writes belong to Designer.
- Developer must not call raw `codex`, `claude`, or `gemini` provider CLIs when OMC `/ask` or `omc ask` is the intended advisor route.
- Developer must not approve merge, release, or production writes.

## Required Harness Decision Output

Every non-trivial Developer run must report:

- Selected harness: direct, ralph, team, omc-team, ultraqa, verify, visual-verdict, ultragoal, ask, or blocked.
- Why it was selected.
- Whether the harness was executed or only recommended.
- Evidence produced: command output, screenshots, ask artifact paths, `.omc/ultragoal/` status, test names, or blocker notes.
- Active loop conflict, if any.

## Resume Contract

When resuming:

1. Read TASK_SPEC, DESIGN_SPEC when relevant, and this OMC contract.
2. Inspect `git status`, changed files, prior verification output, and `.omc/ultragoal/` or `.omc/state/` when present.
3. Identify the active loop authority before doing more work.
4. Continue the next incomplete acceptance criterion or OMC story.
5. Re-run the smallest verification that proves the resumed claim.
