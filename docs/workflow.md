# PM / Developer Workflow

This repository defines a paired AI-native workflow:

- Codex has separate PM and Reviewer plugins.
- Claude acts as Designer and Developer.
- The human lead approves final merge and release.

## Standard Flow

1. Codex PM starts with `pm-plugin:brainstorm` as the conversational entry point for first-project onboarding, feature shaping, user-provided site investigation, refactor discovery, bug themes, or docs/handoff planning.
2. Codex PM researches current external best practices first when upstream behavior, standards, or version-aware guidance matters.
3. Codex PM produces a `Discovery Dossier` from available docs/code/schema/backlog evidence and the research pass.
4. Codex PM presents a `Workflow Decision Gate` and asks the human to confirm whether to interview more, research first, plan first, create a full bundle, create a standard bundle, or produce TASK_SPEC only.
5. Codex PM ranks and grooms backlog with `pm-plugin:roadmap-rank`, `pm-plugin:backlog-groom`, or `pm-plugin:pm-sync` when needed.
6. If UI/UX is material, Claude Designer creates design intent, DESIGN_SPEC, SCREEN_SPEC, component specs, Figma drafts, and visual QA briefs with `designer-plugin`.
7. Codex Reviewer gates design artifacts with `reviewer-plugin:design-review` before Developer handoff.
8. Codex Reviewer gates PM artifacts with `reviewer-plugin:spec-review` when the work is large, ambiguous, technical, or long-running.
9. Codex PM creates a TASK_SPEC and Claude handoff with `pm-plugin:task-spec`.
10. Codex Reviewer checks Developer readiness with `reviewer-plugin:task-spec-review`, `reviewer-plugin:handoff-review`, and `reviewer-plugin:db-contract-review` when data surfaces are affected.
11. Claude Developer runs `developer-plugin:intake-task` for long-running or high-risk work to confirm TASK_SPEC, DESIGN_SPEC, scope, testability, and OMC harness readiness.
12. Claude Developer implements the TASK_SPEC and approved DESIGN_SPEC with `developer-plugin:implement-task` or `developer-plugin:omc-execute`.
13. Claude Developer uses direct execution, `/oh-my-claudecode:ralph`, `/oh-my-claudecode:team`, `omc team`, `/oh-my-claudecode:ultraqa`, `omc ultragoal`, `/oh-my-claudecode:verify`, `/oh-my-claudecode:ask`, or `browser-debug` according to the Developer OMC harness contract.
14. Claude runs verification with `developer-plugin:verify-app`.
15. Codex Reviewer runs `reviewer-plugin:visual-qa-review` for UI/UX work and `reviewer-plugin:pr-review` for the diff or PR.
16. The human lead decides whether to merge or release.

## Role Boundaries

Codex PM:

- Defines scope, non-goals, acceptance criteria, and reviewer checklist.
- Uses `brainstorm` as the first PM conversation before turning uncertainty into documents or TASK_SPECs.
- Investigates available project evidence before drafting final artifacts.
- Uses Chrome DevTools MCP for public read-only site investigation when the user provides a URL.
- Uses external research when current best practices or upstream behavior matter.
- Asks the human to confirm the workflow path before producing final document bundles.
- Produces PM workshop, SDD, backlog, TASK_SPEC, and Claude handoff drafts.
- Uses GitHub as state/tracking and Markdown as decision/spec/handoff SoT.
- Does not implement code.
- Does not run Claude directly.
- Does not perform final PR review.

Claude Developer:

- Implements inside the TASK_SPEC and approved DESIGN_SPEC when UI/UX is material.
- Uses the OMC harness contract to choose direct execution, Ralph, Team, UltraQA, Ultragoal, Verify, Ask, or browser debugging.
- Uses only one primary OMC loop authority per task.
- Uses Chrome DevTools MCP for approved local/public runtime inspection.
- Produces verification evidence.
- Does not approve merge or release.
- Does not mutate Figma or use unsupported shell subcommands such as `omc ralph`, `omc autopilot`, or `omc ultrawork`.

Claude Designer:

- Turns user intent and PM context into design direction, DESIGN_SPEC, SCREEN_SPEC, component specs, Figma drafts, and visual QA briefs.
- Uses Figma MCP through the local desktop Dev Mode server when available.
- May create or modify Figma only in explicitly approved draft, duplicate, branch, sandbox, or approved official targets.
- Keeps Markdown DESIGN_SPEC as the durable handoff source of truth.
- Does not implement code, approve merge, or approve release.

Codex Reviewer:

- Reviews PM artifacts and Claude handoffs before implementation starts.
- Reviews design artifacts and visual QA evidence before Developer handoff or PR review.
- Reviews changes and recommends `APPROVE`, `REQUEST_CHANGES`, or `COMMENT_ONLY`.
- Does not create the PM TASK_SPEC.
- Does not run Claude directly.
- Does not perform final merge or release approval.

Human lead:

- Owns final merge and release decisions.
- Owns ambiguous product/technical decisions that the PM workshop cannot safely resolve.

## Versioning

Use `0.x` releases while the plugin schemas and TASK_SPEC contract are still stabilizing.

Any backward-incompatible TASK_SPEC contract change must update both the Codex and Claude skills in the same release.

Any backward-incompatible DESIGN_SPEC contract change must update Claude Designer, Claude Developer, and Codex Reviewer skills in the same release.

Any backward-incompatible OMC harness contract change must update Claude Developer skills and root `docs/developer-omc-harness-contract.md` in the same release.
