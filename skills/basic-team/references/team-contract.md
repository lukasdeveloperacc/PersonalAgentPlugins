# Main and native subagent contract

The user's current session is main and the sole coordinator. It owns the goal, scope, file ownership, dependencies, integration, reporting and final completion. Native planner/frontend/backend/docs/reviewer agents are direct children doing scoped work. They do not spawn agents, message peers or users, invoke basic-team recursively, or write Office/HTML/Notion.

## Inputs and results

Give each assignment its purpose, absolute workdir, goal/acceptance criteria, allowed files and non-goals, necessary context/dependencies and concrete verification commands. Review adds a comparison base, exact owned patch/revision/hash including new files, relevant existing check evidence and any fix delta. Use [briefs.md](briefs.md).

Each result returns status, changed files, actual check commands/results, required/advisory findings, unchecked items and next dependencies. Separate observed facts from inference. Save large logs in the task's existing evidence location; return the useful summary and path. Never claim a check from intent or a partial assertion.

Agents are not alone in the worktree. One current writer owns each file; main records handovers and prerequisite order. Preserve unrelated edits and staging. Report an ownership conflict or scope expansion here before changing that work. Continue independent tasks while a dependent task waits. Implement only the assignment and necessary callers/tests, using existing patterns and installed Karpathy/Ponytail guidance where applicable.

## Host and capacity

Use the host's actual native agent tools and registered names from [basic-team](../SKILL.md). Confirm role availability, return routing and available slots. Budget main and live agents together; start only ready work and reuse the same owner for follow-ups. No nested spawn or Agent Teams/tmux capability gate is needed. If native agents are unavailable, report that limitation without pretending the requested role ran.

Do not override user models/effort or permissions to enforce an old policy table. Claude role Markdown and generated Codex TOML are native definitions; skill UI YAML is not. Parent sandbox/approval/MCP settings apply; role instructions do not create a security boundary.

## Actor evidence

For each newly spawned actor's first report, main reads its actual model/effort from supported runtime metadata. Record canonical/native identity and reporting owner in existing task evidence, not a new registry. Reuse confirmed settings for the same instance; recheck only for a setting change or concrete mismatch. Requested settings are not observed settings. If metadata is unavailable, record the missing evidence and leave actual values unverified; never scan unrelated sessions or fill defaults to silence a warning.

Subagents notify main of actual start, completion, failure or blocked waiting. Main publishes meaningful transitions, not raw messages. Main validates their evidence and handles Office checks directly with the actor. A completed attempt is not an approval: independent reviewer findings and final checks govern completion. See [reporting.md](reporting.md).
