# Office transport and display checks

Use this reference when configured Office tools are missing, actor settings are being published, or a successful report looks wrong. Root remains the only reporter; the reporting contract owns backend selection and recovery limits.

## Configured but tools are unavailable

First use the host's supported tool discovery/reconnection. An enabled entry and an HTTP 200 homepage prove neither callable `report`/`ask` nor successful reporting. Keep NOT READY until a real initial report succeeds; preserve an existing run ID on resume.

If the host supports direct MCP HTTP requests to the already configured endpoint, the observed recovery path is JSON-RPC `initialize` → initialized notification → `tools/list` → `tools/call`. Use the configured URL, authentication, negotiated protocol/session headers and advertised input schemas. Do not guess REST write endpoints or bypass a host restriction. Read the MCP envelope, tool `isError` and returned `run_id`; HTTP 200 alone is insufficient. Discovery of both schemas plus a successful `report` permits Office selection under the reporting contract, with question/answer execution still unverified. Call `ask` only for a real user decision, retaining a pending `ask_id` as usual.

If this path is unsupported, expose the missing connection and continue independent work with unsynchronized terminal summaries. Do not install a second client, change shared configuration or restart Office merely to recover reporting. Registration changes in Codex take effect in a new session.

## Actor identity is not an Office owner

Native names route agents; canonical IDs establish which actor and parent produced evidence. Office `owner` is a display key, not execution hierarchy. Check the deployed role registry when placement matters; do not infer it from an agent path or `after` edges.

The interviewed deployment's `web/src/roles.json` maps:

| Office owner | Display department |
| --- | --- |
| `backend-*` / `frontend-*` / `docs-*` | Backend / Frontend / Docs |
| `Planner`, `Architect`, `Critic`, `plan-*` (newer Office; also `lane: plan`) | Meeting room |
| `Karpathy Agent`, `Ponytail Agent`, `reviewer-*` (newer Office) | Audit |
| `Impeccable Agent` / `E2E Agent` | Design / QA |
| `leader` | Root's manager seat |

For example, canonical `/root/backend_lead/db_core` can have display owner `backend-core`; preserve the canonical ID and parent in its evidence/note. Use one stable display key per actor and do not assign multiple actors the same owner. Newer Office maps `reviewer-*` to Audit and `plan-*` to the meeting room, so the aggregate review gate can use owner `reviewer-lead`. Older registries lack these and seat `reviewer-lead` temporarily; there give the gate an empty owner (`""`): the card still shows, and no character is seated. Never alias another lead to `leader`. These are version-dependent display rules, not a promise of team/worker seats.

`reviews[]` alone already seats each reviewer in Audit/Design/QA, but a `#/run/<id>` link opens visitor mode, which draws only the room you are in: enter that room before calling reviewers missing. Still create one execution card per external reviewer per round (`R1-K`, `R1-P`, `R1-I`, `R1-E`) when it starts, so its working status and model/effort show. Use the exact `reviews[].reviewer` label as its owner, including across rounds for the same reporting role. Record the actual per-round agent IDs in evidence. An internal owner such as `karpathy_agent` plus a review label `Karpathy Agent` can render two characters for one reviewing role; do not create alternate spellings to organize rounds.

Rank is currently inferred from the model string (`luna`/`haiku` → 신입사원, `sol`/`sonnet` → 대리, `opus` → 과장), independently of execution role. A lead shown as 대리 does not establish the wrong model or hierarchy. Preserve observed settings and explain this product limitation instead of changing model data to force a rank.

The observed UI takes settings from active task cards. If one actor has several real tasks, carry its same applicable confirmed settings onto each active card rather than relying on another waiting/completed card. Unknown settings remain unverified. Corrections merge by task ID: omitting an earlier incorrect model/effort does not erase it. Use the deployed contract's supported clearing value (the observed string fields accept `""`) with an unverified note and check readback; do not leave requested values looking confirmed.

## Verify the report at the right level

1. Check patch fields: allowed stage prefix, lane/status, exact external reviewer labels, `decisions[].body` and top-level `close_ask_ids`. Reuse examples rather than inventing nested fields.
2. Publish observed actor model/effort on that actor's existing deliverable card, including leads. On Claude Code root reads these directly per the team contract. Elsewhere, put requested values and missing-observation explanations in the note/evidence; never present a requested value as confirmed. A missing value stays unverified, not borrowed from another actor. A zero missing-field count does not establish runtime verification; do not populate fields merely to make that count zero.
3. After the first actor publication or an owner/model/payload correction, compare the affected fields using the report response's `state` or `get_run` (older Office: the read-only `/api/state` with only the exact project/run). Do not dump or save the global snapshot. Routine status patches need no repeated full readback.
4. If claiming visible placement or text, verify the affected Office screen with the supported browser. Stored keys and a successful response do not prove rendering. Report data verification and screen verification separately when a browser is unavailable.

Fix malformed decision text using the same decision title with `body`; keep task IDs stable when correcting owner/model fields. Do not create duplicate runs or synthetic build tasks to compensate for a display limitation. Document a required Office product change separately from a skill correction.

## Finished work and waiting approval

The observed UI derives typing from `status: 진행중`. Update finished work at the next reporting checkpoint, preserving its result; do not keep it active while waiting for fixes, user input or another reviewer. An execution-only review card can be `완료` with CHANGES_REQUIRED while its required approval gate stays open. A combined or aggregate card is `대기중` when none of the represented reviewers are working, and remains `진행중` while any still work. Explain execution ended but approval is unresolved. Required missing evidence still blocks approval; waiting or unavailable work is not a PASS.

Check all cards belonging to that owner across rounds: an old `진행중` card can keep the character typing even when a later card is complete. Do not close a real outstanding gate just to make the room look finished. Verify stored status and visible animation separately; an inaccessible browser only limits the screen claim.
