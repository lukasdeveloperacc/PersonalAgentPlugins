# Security Policy

The v0.1 plugins are skill-only. They do not include MCP servers, hooks, automatic shell execution, or deployment automation.

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

## Permission Model

Claude Developer can implement and verify within a TASK_SPEC.

Codex PM can run PM workshops, draft SDD/TASK_SPEC/handoff documents, and propose GitHub state changes.

Codex Reviewer can review PRs/diffs and recommend review decisions.

The human lead is the only final merge and release authority.

PM GitHub behavior defaults to `propose-only`. Any future write mode requires an explicit configuration and must keep destructive operations forbidden.

## Future MCP Additions

Add MCP servers only after v0.1 skill workflows are stable. Prefer read-only or staging-scoped integrations first.

Recommended future order:

1. GitHub MCP
2. Context7
3. Playwright or Chrome DevTools MCP
4. Figma MCP
5. Sentry MCP
6. Supabase/PostgreSQL read-only MCP
