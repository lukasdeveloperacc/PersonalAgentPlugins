---
name: basic-team
description: Coordinate scoped work with native planner, frontend, backend, docs and reviewer subagents in the current session. Use for a basic-team implementation or review request; not for explaining or editing this skill.
---

# Basic Team

The user's current session is main. Keep the goal and completion decision here; delegate concrete work directly to native subagents. Read [team-contract.md](references/team-contract.md) and [reporting.md](references/reporting.md). No separate lead, nested worker tree or Team runtime is required.

## Choose the work

1. Establish the request, acceptance criteria, allowed files, non-goals and verification commands. Reuse the active native Goal without replacing it. Create a new Goal only when the user explicitly requests one, through the host's supported native feature. Plan-only requests end with a plan; they never authorize implementation. If native Goal is unavailable, explain that a single run does not provide automatic continuation.
2. Plan clear tasks here. Call the planner only for unresolved dependencies or design choices; do not require ralplan for ordinary work. Respect a separately requested planning workflow's real lifecycle.
3. Select only needed roles below. Fix cross-file/API contracts and one writer per file before parallel work. Each subagent implements or checks its assignment directly and reports here. Use [briefs.md](references/briefs.md).

| Work | Claude Code agent | Codex agent |
| --- | --- | --- |
| Planning | `lukas-plugin:basic-planner` | `basic_planner` |
| UI | `lukas-plugin:basic-frontend` | `basic_frontend` |
| API/data | `lukas-plugin:basic-backend` | `basic_backend` |
| Documentation | `lukas-plugin:basic-docs` | `basic_docs` |
| Review | `lukas-plugin:basic-reviewer` | `basic_reviewer` |

Check actual native role availability. `agents/openai.yaml` is skill UI metadata, not a native role. Missing roles require the plugin's documented install/reload and a fresh session; never claim a general-purpose spawn loaded the registered role. Model/effort follow user and host settings rather than a mandatory routing table. Subagents inherit parent permissions/MCP; a read-only instruction is not separate sandbox isolation.

## Implement, review and finish

Verify returned files and actual checks, preserving failures and unchecked areas. Apply Karpathy/Ponytail minimum-change guidance without always creating separate persona reviewers. Main may handle a trivial edit directly. For nontrivial implementation, assign one independent reviewer; add UI/connected-flow evidence only where affected behavior and acceptance criteria need it. Supply startup/fixtures and affected states for runtime checks.

Freeze the owned diff, comparison base and revision/hash, including new files; no edits to that content during review. In shared worktrees isolate owned hunks and preserve others' staging/edits. Findings are **required** only for evidenced in-scope defects, regressions, security/data-loss risks or unmet explicit criteria. Taste, adjacent cleanup and speculative features are **advisory**, never automatic fixes. Missing required evidence is BLOCKED, not PASS.

Return required findings to the current file owner. Rerun affected checks and have the reviewer verify the new delta and connected risks. Name applicable previous evidence instead of rerunning every persona; old PASS alone does not approve changed content. Recompute the owned diff before completion. Do not reopen accepted decisions without changed premises or a regression. After three nonconverging rounds, stop adding fixes and report open findings and alternatives for a user decision.

Main owns integration, final checks and the completion decision. Finish only when acceptance criteria and required evidence hold. Report outcome, changed files, actual checks, unresolved items and the reporting link; distinguish product completion from reporting synchronization. Close only this run's settled agents. Never turn a skipped check into success.

For explicit Notion Task tracking, additionally read [notion-tracking.md](references/notion-tracking.md). Otherwise do not load it or write to Notion. This skill does not grant commits, pushes, deployments or shared configuration changes.
