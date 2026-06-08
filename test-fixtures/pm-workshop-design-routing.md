# Fixture: PM Workshop Design Routing

Use with:

```text
$pm-plugin:brainstorm
```

## Prompt

SmartStoreToolkit의 상품 수집 시작 화면을 새로 만들고 싶다.

사용자는 스마트스토어 운영자이고, 도매사 URL이나 상품 소스를 넣으면 수집 가능성을 점검하고 다음 단계로 넘어가는 흐름이 필요하다.

이 작업은 UI/UX 품질이 중요하다. 바로 TASK_SPEC를 만들지 말고, PM으로서 기존 README/docs를 조사하고 DESIGN_REQUIRED 여부를 판단한 뒤 Workflow Decision Gate를 먼저 제안해라.

## Expected Behavior

- Classify as `UI_UX_DESIGN` or `FEATURE_SHAPING` with `DESIGN_REQUIRED`.
- Include design materiality in the Discovery Dossier.
- Do not jump directly to TASK_SPEC or Developer handoff.
- Recommend Claude Designer routing:
  - `/designer-plugin:design-intent`
  - `/designer-plugin:screen-spec`
  - `/designer-plugin:figma-draft` only if Figma draft write is approved
- Require Codex `reviewer-plugin:design-review` before Developer handoff.
- Require `visual_qa_required: true` or explain why it is waived.
- If TASK_SPEC candidates are drafted, include conditional design fields.
