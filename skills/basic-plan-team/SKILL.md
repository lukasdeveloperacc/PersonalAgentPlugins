---
name: basic-plan-team
description: Run or resume a planning-only team stage through the installed ralplan harness, or perform an assigned plan-domain review. Use when the user requests basic-plan-team. Not for explaining or editing this skill.
---

# Basic Plan Team

Produce a reviewed plan through the installed planning harness. Planning alone does not authorize implementation.

Read the [team contract](../basic-team/references/team-contract.md) for invocation, ownership, capacity and result requirements. The main/root coordinator also reads [reporting](../basic-team/references/reporting.md); it alone selects and writes the run's reporting backend.

Both root planning and assigned plan-domain review must load and apply [Karpathy guidelines](../karpathy-guidelines/SKILL.md): make assumptions explicit, keep scope minimal and define verifiable acceptance criteria. If the skill is unavailable, report the dependency gap without claiming it was applied.

## Direct invocation or a composed planning stage

The main/root session owns this stage and the harness lifecycle. Complete it before spawning execution teams unless the installed harness has a verified embedded return path. Do not spawn a child Plan lead to impersonate root.

1. Establish scope, non-goals, acceptance criteria and unresolved decisions. Locate and read the installed `ralplan` skill and its actual invocation requirements; if absent, inspect the installed `plan` fallback and disclose the reduced review coverage.
2. Pass the request, relevant repository evidence and applicable Karpathy guidance through the harness's supported context input. Let it own Planner → Architect → Critic and its lifecycle; do not replace its internal role instructions, duplicate the loop or skip required handoff gates. Do not claim every internal agent loaded the skill without evidence.
3. For a planning-only request, use a supported planning-only path. Use standalone advisory only if the installed harness's canonical identity and mode conditions permit it; never use it as a universal execution-team bypass. If the required path is unavailable, return the precise blocker and any usable plan evidence without claiming harness completion.
4. Return the plan, acceptance/test specification, review evidence, unresolved decisions and the harness terminal status. Record the actual invocation and lifecycle owner. Stop here by default.

For a composition that also requests execution, root checks the existing user authorization and the harness's real handoff requirements after planning completes. A plan path or Critic PASS alone is not execution authority. If only the transition is blocked, preserve the usable planning result and identify that transition separately.

## Delegated plan-domain review

For `purpose: review`, inspect the assigned frozen revision against the plan, dependencies, acceptance criteria and scope. Use the domain-review brief in [briefs](../basic-team/references/briefs.md). Remain read-only and return findings to the parent; do not start ralplan, implementation, another Reviewer team or a new reporting run.

Review of a plan you authored is an internal check. Independent approval requires an uninvolved reviewer. If delegated `purpose: plan` requires a root-owned harness, return that requirement to root instead of claiming its lifecycle.

## Return

Use the common result contract, distinguishing plan completion from execution readiness. Include plan/spec paths, actual review verdicts and evidence, unresolved items, checks not run, and any authorized next dependency.
