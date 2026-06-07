# Security Policy

The v0.x plugins are conservative. PM includes Chrome DevTools MCP for public read-only site investigation. They do not include hooks, automatic deployment automation, production write automation, or direct Claude execution/control.

## Prohibited By Default

- Secrets, tokens, API keys, or `.env` edits.
- Production database writes.
- Production deployment or release automation.
- Automatic merge approval.
- Broad file edits outside TASK_SPEC scope.
- Hidden shell hooks.
- Direct Claude execution/control from PM skills.
- GitHub writes by default from PM skills.
- DB migrations or production schema changes from PM skills.
- Authenticated browser session inspection unless the human explicitly approves that site/session.
- Browser actions that submit forms, place orders, change account settings, bypass access controls, or collect private data.

## Permission Model

Claude Developer can implement and verify within a TASK_SPEC.

Codex PM can run PM workshops, draft SDD/TASK_SPEC/handoff documents, and propose GitHub state changes.

Codex PM may use Chrome DevTools MCP for user-provided site investigation. Default usage is public, read-only browsing in a separate browser context. `--autoConnect`, `--browser-url`, or other active authenticated session modes require explicit human approval.

Codex Reviewer can review PRs/diffs and recommend review decisions.

The human lead is the only final merge and release authority.

PM GitHub behavior defaults to `propose-only`. Any future write mode requires an explicit configuration and must keep destructive operations forbidden.

## MCP Additions

Current MCP:

1. Chrome DevTools MCP for PM site investigation.

Add future MCP servers only after current skill workflows are stable. Prefer read-only or staging-scoped integrations first.

Recommended future order:

1. GitHub MCP
2. Context7
3. Playwright MCP
4. Figma MCP
5. Sentry MCP
6. Supabase/PostgreSQL read-only MCP
