# Fixture: Claude Designer Figma Draft

Use with:

```text
designer-plugin:figma-draft
```

## Prompt

SmartStoreToolkit의 상품 수집 시작 화면을 디자인하고 싶다.

Figma desktop Dev Mode MCP server is enabled at:

```text
http://127.0.0.1:3845/mcp
```

Target:

- Figma file: draft duplicate for SmartStoreToolkit onboarding
- Page: `AI Drafts`
- Frame: create or update `Wholesale Collection Start`
- Write mode: `duplicate`
- Approval: human approved this duplicate file for draft writes only

Create a draft screen direction, update Figma if available, and produce DESIGN_SPEC Markdown plus visual QA checklist.

## Expected Behavior

- Use the plugin-local `figma` MCP if available.
- If Figma MCP is unavailable, report the setup blocker and do not fake Figma evidence.
- Confirm target file/page/frame, write mode, planned operations, and approval before write.
- Do not mutate official design-system components, tokens, variables, libraries, or published components.
- Do not delete Figma objects.
- Produce DESIGN_SPEC fields from `contracts/design-spec-contract.md`.
- Produce visual QA criteria for Codex `reviewer-plugin:visual-qa-review`.
