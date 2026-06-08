# Security Policy

The v0.x plugins are conservative. PM includes Chrome DevTools MCP for public read-only site investigation. Claude Developer includes Chrome DevTools MCP for local/app runtime inspection. Claude Designer includes Figma MCP for design inspection and approved draft writes. The plugins do not include hooks, automatic deployment automation, production write automation, or direct Claude execution/control.

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
- Silent Figma writes to official/source-of-truth files.
- Figma deletions of frames, pages, components, assets, shared tokens, variables, libraries, or published components without explicit task approval.

## Permission Model

Claude Developer can implement and verify within a TASK_SPEC.

Claude Developer may use Chrome DevTools MCP for local app verification, console/network/DOM inspection, screenshots, and approved public runtime debugging. Authenticated sessions and state-changing browser actions still require explicit human approval.

Claude Developer may use OMC in-session skills and shell CLI harnesses according to `docs/developer-omc-harness-contract.md`. Developer must not use OMC to bypass TASK_SPEC scope, DESIGN_SPEC gates, secret restrictions, production restrictions, merge approval, or release approval.

Claude Designer can create DESIGN_SPEC artifacts and may use Figma MCP for approved draft, duplicate, branch, sandbox, or approved official targets.

Codex PM can run PM workshops, draft SDD/TASK_SPEC/handoff documents, and propose GitHub state changes.

Codex PM may use Chrome DevTools MCP for user-provided site investigation. Default usage is public, read-only browsing in a separate browser context. `--autoConnect`, `--browser-url`, or other active authenticated session modes require explicit human approval.

Codex Reviewer can review PRs/diffs and recommend review decisions.

Codex Reviewer can review DESIGN_SPEC artifacts, Figma write scope, visual QA evidence, and approved Figma sources. Codex Reviewer must not create, modify, delete, rename, publish, or reorganize Figma objects.

The human lead is the only final merge and release authority.

PM GitHub behavior defaults to `propose-only`. Any future write mode requires an explicit configuration and must keep destructive operations forbidden.

## MCP Additions

Current MCP:

1. Chrome DevTools MCP for PM site investigation.
2. Chrome DevTools MCP for Claude Developer browser/runtime debugging and verification.
3. Figma MCP for Claude Designer through the local desktop server at `http://127.0.0.1:3845/mcp`.
4. Figma MCP for Codex Reviewer through the same local desktop server, for read/review evidence only.

Figma MCP write usage requires an explicit target and approval. Prefer draft, duplicate, branch, or sandbox files. Markdown DESIGN_SPEC remains the durable handoff source of truth.

Codex Reviewer Figma usage is read/review only even if the underlying MCP server exposes write-capable tools.

Claude Developer Figma usage is not configured. Developer consumes Markdown DESIGN_SPEC and Figma source references but must not mutate Figma.

Add future MCP servers only after current skill workflows are stable. Prefer read-only or staging-scoped integrations first.

Recommended future order:

1. GitHub MCP
2. Context7
3. Playwright MCP
4. Sentry MCP
5. Supabase/PostgreSQL read-only MCP
