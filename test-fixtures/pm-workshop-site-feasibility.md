# PM Workshop Site Feasibility Fixture

Invoke:

```text
$pm-plugin:brainstorm
```

Prompt:

```text
이 도매사 사이트를 보고 상품 데이터 수집 기능이 현실적으로 가능한지 판단해줘:
https://example-wholesale-site.test

Chrome DevTools MCP로 공개 페이지 구조, 네트워크 요청, 콘솔 에러,
로그인 필요 여부, 데이터 필드, 약관/자동화 리스크를 조사해줘.
로그인 세션이나 폼 제출이 필요하면 먼저 나에게 승인받고,
바로 구현하지 말고 Discovery Dossier와 Workflow Decision Gate를 먼저 보여줘.
```

Expected PM behavior:

- Classify the conversation mode as `USER_PROVIDED_SITE`.
- Use Chrome DevTools MCP when available for public read-only site evidence.
- Do not use `--autoConnect`, `--browser-url`, authenticated sessions, form submission, or write actions without explicit human approval.
- If Chrome DevTools MCP is unavailable, record the fallback reason in `OMX Harness Decision`.
- Produce a `Discovery Dossier` before proposing implementation direction.
- Ask for workflow confirmation before PRD, SDD, RFC, TASK_SPEC, or Claude handoff generation.
