# Security Policy

The v0.1 plugins are skill-only. They do not include MCP servers, hooks, automatic shell execution, or deployment automation.

## Prohibited By Default

- Secrets, tokens, API keys, or `.env` edits.
- Production database writes.
- Production deployment or release automation.
- Automatic merge approval.
- Broad file edits outside TASK_SPEC scope.
- Hidden shell hooks.

## Permission Model

Claude Developer can implement and verify within a TASK_SPEC.

Codex PM/Reviewer can scope and review.

The human lead is the only final merge and release authority.

## Future MCP Additions

Add MCP servers only after v0.1 skill workflows are stable. Prefer read-only or staging-scoped integrations first.

Recommended future order:

1. GitHub MCP
2. Context7
3. Playwright or Chrome DevTools MCP
4. Figma MCP
5. Sentry MCP
6. Supabase/PostgreSQL read-only MCP
