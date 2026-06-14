# Fixture: captured `cmux list-panels` frame

A canned output the dry-run transport shim returns for `cmux list-panels`, so the OBSERVE /
pane-liveness logic can be tested with no live cmux session.

## Scenario A — reviewer pane alive

```text
SURFACE      WINDOW   ROLE          TITLE                      ALIVE
surface:1    win:1    orchestrator  claude                     yes
surface:2    win:1    reviewer      cmux omx exec (codex)      yes
```

Expected: `panes.json.surfaces.reviewer == "surface:2"` is reused (liveness probe succeeds).

## Scenario B — reviewer pane dead / absent

```text
SURFACE      WINDOW   ROLE          TITLE                      ALIVE
surface:1    win:1    orchestrator  claude                     yes
```

Expected: stored `surface:2` is absent from the list → treated as dead → `new-split right`
creates a fresh reviewer surface, `panes.json` updated.
