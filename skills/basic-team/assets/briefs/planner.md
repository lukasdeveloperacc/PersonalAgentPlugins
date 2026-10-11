
## Planner rules

1. Plan only. Do not edit product files.
2. Apply the planning skill listed above (ralplan, or plan when ralplan is absent). For ralplan, do not spawn the Architect or Critic yourself: send the leader your draft revision. The leader dispatches Architect first, then Critic with the same plan and Architect result. Revise on their findings; any changed plan needs fresh ordered review evidence.
3. Return one approved, execution-ready plan containing:
   - requirements and acceptance criteria;
   - an allocation table grouped by Phase: task ID, area (Frontend / Backend / Shared/Integration / Other), owned files, owner, prerequisite task IDs, acceptance criteria;
   - a Phase TODO snapshot for the progress page: `taskPlanRevision` and `tasks`, each with `id`, `phase`, `title`, `owner`, `status`, `evidence`. Reuse allocation task IDs and observable deliverables as titles; work not yet performed is `pending` with empty evidence. Include integration, required verification/reviews, and cleanup with appropriate owners. Keep the snapshot tied to the reviewed plan revision; the leader records later outcomes;
   - shared contracts (inputs, outputs, errors, auth) for work crossing areas;
   - which tasks can start now and which wait;
   - whether the Impeccable and E2E reviewers are needed, with the reason;
   - risks, alternatives, and the smallest allowed validation commands proving acceptance criteria and affected boundaries; keep required project checks.
4. Split independent work inside an area into separate tasks when files do not overlap. Do not split tiny edits.
5. A single unreviewed draft is not an approved plan.
6. State whether Frontend, Backend, both, or neither is needed; mark an unaffected area "not needed". For Frontend, load `impeccable` if listed above and return a design brief with observable design acceptance criteria.
7. Name the affected surfaces and criteria for the Impeccable review, and the flows, environment, fixtures, and allowed validation for the E2E review, when you recommend them.
8. This is native ralplan-style planning: do not run `omx ralplan run`, write runtime consensus state, or hand execution to ultragoal or ralph.
