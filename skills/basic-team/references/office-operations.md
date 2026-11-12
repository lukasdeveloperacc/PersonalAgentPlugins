# Office connection and display checks

Main is the only writer. Follow [reporting.md](reporting.md) for identity, schema, checks and completion. Use this reference for a concrete transport, actor placement or readback problem; routine status changes do not require a browser/full-state audit.

## Connection

Use supported discovery/reconnection first. A configured entry, HTTP homepage or one connection failure does not establish report/ask availability. If supported, direct configured MCP HTTP transport uses initialize → initialized notification → tools/list → tools/call with negotiated headers/authentication and advertised schemas. Inspect tool isError and returned run identity; HTTP 200 alone is insufficient. Do not guess REST writes, install clients, restart shared services or alter global settings.

Keep saved mode/run ID during outages. Retry only with new evidence; continue independent product work with explicit unsynchronized summaries. A stale session catalog may differ from the live server; use only callable supported transports and disclose limits. Never create another run to refresh tools.

## Actor identity and placement

Native IDs identify actual actors, while Office owner is a display key. Prefer deployed `get_office_rules` departments/owners/plan_lane_precedence. Main uses `leader`; examples for real actors are `frontend-ui`, `backend-api`, `docs-contract`, `reviewer-basic`. Lane plan may take precedence. Generic reviewer verdict/evidence belongs in an ordinary review task note, not an invented external reviews enum. Use exact external persona labels only when that review actually ran.

Read actual model/effort for each new actor once from supported runtime metadata per [team-contract.md](team-contract.md). Reuse for that instance, never requested/default settings as observation. Placement/rank/status is not runtime liveness or proof of model configuration. A missing value remains unverified; answer an actual Office check factually rather than fabricating settings.

After first actor publication or owner/model correction, check affected stored fields and advertised placements using report response or targeted get_run. Unexpected fallback/unassigned needs a rules/identity check; do not alias actors merely to force display. Aggregate gates have no actor/model. Keep task IDs stable and send only changed fields. Routine status patches need no repeated full readback, but every response's checks must be processed.

## Visible behavior and completion

Claim visible placement/text only after a supported browser check. API data success proves saved fields, not rendering. Report any browser limit separately. Do not create fake tasks or reopen completed tasks to change animation/title display.

`진행중` means actual work. A finished review attempt may be complete with CHANGES_REQUIRED while a required approval gate waits for fixes. Keep unresolved gates open; do not close them for visual effect. Final completion requires real evidence plus the reporting contract's full task/TODO/question/check audit, not a quiet room.
