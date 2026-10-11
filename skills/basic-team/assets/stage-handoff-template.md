# Stage handoff

- Run / round / observation policy:
- Source -> target stage:
- Outcome: ready | BLOCKED | cancelled
- Approved plan path / revision:
- Implementation baseline / final content or diff identity:
- Progress page absolute path / confirmed saved_at / checkpoint:

## Required artifacts

Use the transition row in references/workflow-contracts.md. List every required artifact with its saved path and revision; the HTML page cannot replace another artifact.

| Artifact | Saved path / revision | Verified result or gap |
| --- | --- | --- |

## Tasks and settings

| Task / agent | Owner / owned files | Prerequisites / observed status | Requested model + effort | Invocation | Host/pane observed model + effort / evidence | Specific user exception, if any |
| --- | --- | --- | --- | --- | --- | --- |

## Changes, reviews, and validation

- Changed files / delivered behavior:
- Required reviewers / round / reviewed revision / verdicts:

| Check / scenario | Command or verified action | Checked revision / environment | Exit code / expected vs observed | Result / evidence / unchecked scope |
| --- | --- | --- | --- | --- |

- Superseded results after later edits:
- Hook: arm request accepted / registration confirmed / disarm requested / disarm confirmed; run_id and evidence, or unavailable/manual fallback:
- Shutdown / inactive state / browser-MCP cleanup evidence (completion):
- Blockers / missing input / recovery / owner:
- Next actions and tasks to release:
- Pending progress patches / outstanding task or question IDs (resume):

## Transition completion checklist

Check only with evidence above. Mark inapplicable items with a reason; record any explicit user exception. A required unchecked item means BLOCKED for this transition.

- [ ] Every artifact in this transition's row exists and was read.
- [ ] Task ownership, prerequisites, and acceptance criteria are recorded.
- [ ] Settings satisfy the recorded observation policy; accepted invocation is distinguished from actual observation, and no known mismatch remains.
- [ ] Validation covers the latest relevant edit and states unchecked scope.
- [ ] Required reviews are complete for the same frozen revision, or this earlier transition records their pending status.
- [ ] Tool failures are recorded as BLOCKED without inferring a product defect.
- [ ] Progress save receipt is confirmed; ELI5 briefing includes its link, absolute path, saved time, and separate hook request/confirmation states.
- [ ] Completion only: all required PASS verdicts, validation, shutdown/state, cleanup, and final save succeeded; no pending writes/updates remain.
