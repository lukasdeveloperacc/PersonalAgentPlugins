# Progress page example

A real-shaped run, saved at the moments SKILL.md asks for. Each block is one `update` patch; send only what changed. The page draws the graph from `lane`, `status` and `after`, so keeping those three right is what matters.

Conventions used here:
- Agent tasks carry the full model ID and effort (not the spawn alias), so the card shows exactly which model version ran each task.
- One card per piece of work, including each review per round (`R1-K`, `R2-K`) and each fix, so the graph shows the loop.
- `note` carries the one-line result a person needs (a verdict, a count, why it is blocked).
- A blocked task stays `진행중` with the reason in `note`, and `blockers` says the same at the top.
- `summary` says what is happening now and what comes next, in plain Korean.

```sh
uv run "<skill-dir>/scripts/progress.py" init "<project>/docs/inprogress/external-stt-import-20261012-1150.html" --title "외부 STT 가져오기 끊김 해결 + 외부 작업 판정 통일"
```

## 1. Plan approved, tasks split (end of step 2)

```json
{"stage": "구현", "summary": "ralplan 계획이 승인되어 계약(C-1)부터 구현을 시작했습니다", "blockers": "없음",
 "tasks": [
  {"id": "PLAN", "title": "ralplan 계획", "owner": "leader", "lane": "plan", "status": "완료", "note": "plan-r4 승인"},
  {"id": "C-1", "title": "OpenAPI 계약 갱신 + 타입 재생성", "owner": "backend-1", "model": "claude-haiku-5-5", "effort": "max", "lane": "build", "status": "진행중", "after": ["PLAN"]},
  {"id": "BE-1", "title": "가져오기 안에서 음성 검증까지 처리", "owner": "backend-1", "model": "claude-haiku-5-5", "effort": "max", "lane": "build", "status": "대기중", "after": ["C-1"]},
  {"id": "BE-2", "title": "외부 작업에 교정 구간 복사·제출 규칙", "owner": "backend-2", "model": "claude-haiku-5-5", "effort": "max", "lane": "build", "status": "대기중", "after": ["C-1"]},
  {"id": "FE-1", "title": "3단계 표시·로딩·잠금, 공개 대기 라벨", "owner": "frontend-1", "model": "claude-haiku-5-5", "effort": "max", "lane": "build", "status": "대기중", "after": ["C-1"]},
  {"id": "FE-2", "title": "외부 작업 상세를 엑셀 판정 UI로 통일", "owner": "frontend-2", "model": "claude-haiku-5-5", "effort": "max", "lane": "build", "status": "대기중", "after": ["C-1"]},
  {"id": "CHECK", "title": "전체 테스트·빌드", "owner": "backend-1", "model": "claude-haiku-5-5", "effort": "max", "lane": "build", "status": "대기중", "after": ["BE-1", "BE-2", "FE-1", "FE-2"]}],
 "decisions": [
  {"title": "Impeccable 리뷰 필요", "body": "3단계 표시, 목록 라벨, 판정 화면 등 보이는 UI가 바뀜"},
  {"title": "E2E 리뷰 필요", "body": "가져오기 → 이어하기 → 공개 → 판정 → 제출이 화면·서버·DB를 가로지름"},
  {"title": "Notion 동기화 제외", "body": "사용자 확인: 이번 범위에서 빼기로 함"}]}
```

## 2. A blocker during build

```json
{"blockers": "BE-1: 로컬 MinIO 버킷이 없어 통합 테스트 실패 — 시드 스크립트로 생성 후 재시도 중",
 "tasks": [
  {"id": "C-1", "status": "완료"}, {"id": "BE-2", "status": "진행중"}, {"id": "FE-1", "status": "진행중"}, {"id": "FE-2", "status": "진행중"},
  {"id": "BE-1", "status": "진행중", "note": "막힘: 테스트 버킷 없음"}]}
```

## 3. Build done, first review round finished (end of step 4)

Publish the round only after all reviewers returned.

```json
{"stage": "수정 (1라운드)", "summary": "1차 리뷰에서 Impeccable이 필수 수정 1건을 냈습니다. 담당자가 고친 뒤 4명이 새 revision을 다시 리뷰합니다", "blockers": "없음",
 "tasks": [
  {"id": "BE-1", "status": "완료", "note": ""}, {"id": "BE-2", "status": "완료"}, {"id": "FE-1", "status": "완료"}, {"id": "FE-2", "status": "완료"},
  {"id": "CHECK", "status": "완료", "note": "백엔드 392 · 통합 339 · 프론트 1435 통과"},
  {"id": "R1-K", "title": "Karpathy 리뷰 R1", "owner": "Karpathy Agent", "model": "claude-sonnet-5-5", "effort": "high", "lane": "review", "status": "완료", "after": ["CHECK"], "note": "PASS"},
  {"id": "R1-P", "title": "Ponytail 리뷰 R1", "owner": "Ponytail Agent", "model": "claude-sonnet-5-5", "effort": "high", "lane": "review", "status": "완료", "after": ["CHECK"], "note": "PASS · 권고 2건"},
  {"id": "R1-I", "title": "Impeccable 리뷰 R1", "owner": "Impeccable Agent", "model": "claude-sonnet-5-5", "effort": "high", "lane": "review", "status": "완료", "after": ["CHECK"], "note": "수정 필요: 경고 사유 색 대비"},
  {"id": "R1-E", "title": "E2E 리뷰 R1", "owner": "E2E Agent", "model": "claude-sonnet-5-5", "effort": "high", "lane": "review", "status": "완료", "after": ["CHECK"], "note": "PASS · 5개 시나리오"},
  {"id": "FIX-1", "title": "경고 사유 색·대비 수정", "owner": "frontend-1", "model": "claude-haiku-5-5", "effort": "max", "lane": "fix", "status": "진행중", "after": ["R1-I"]}],
 "reviews": [
  {"round": 1, "reviewer": "Karpathy Agent", "verdict": "PASS", "note": "요구사항·계약 범위 이상 없음"},
  {"round": 1, "reviewer": "Ponytail Agent", "verdict": "PASS", "note": "권고: 중복 표시 정리, 재시도 경로 테스트 보강"},
  {"round": 1, "reviewer": "Impeccable Agent", "verdict": "CHANGES_REQUIRED", "note": "경고 사유 텍스트 대비 3.1:1 → 4.5:1 이상 필요"},
  {"round": 1, "reviewer": "E2E Agent", "verdict": "PASS", "note": "가져오기→이어하기→공개→판정→제출 실제 브라우저 확인"}]}
```

## 4. Fix done, second round passed (end of step 5)

```json
{"stage": "마무리", "summary": "2차 리뷰에서 4명 모두 PASS했습니다. 최종 검사 후 에이전트를 종료하고 보고합니다",
 "tasks": [
  {"id": "FIX-1", "status": "완료", "note": "대비 4.8:1, 프론트 테스트 통과"},
  {"id": "R2-K", "title": "Karpathy 리뷰 R2", "owner": "Karpathy Agent", "model": "claude-sonnet-5-5", "effort": "high", "lane": "fix", "status": "완료", "after": ["FIX-1"], "note": "PASS"},
  {"id": "R2-P", "title": "Ponytail 리뷰 R2", "owner": "Ponytail Agent", "model": "claude-sonnet-5-5", "effort": "high", "lane": "fix", "status": "완료", "after": ["FIX-1"], "note": "PASS"},
  {"id": "R2-I", "title": "Impeccable 리뷰 R2", "owner": "Impeccable Agent", "model": "claude-sonnet-5-5", "effort": "high", "lane": "fix", "status": "완료", "after": ["FIX-1"], "note": "PASS"},
  {"id": "R2-E", "title": "E2E 리뷰 R2", "owner": "E2E Agent", "model": "claude-sonnet-5-5", "effort": "high", "lane": "fix", "status": "완료", "after": ["FIX-1"], "note": "PASS"},
  {"id": "DONE", "title": "최종 검사 · 에이전트 종료 · 보고", "owner": "leader", "lane": "finish", "status": "진행중", "after": ["R2-K", "R2-P", "R2-I", "R2-E"]}],
 "reviews": [
  {"round": 2, "reviewer": "Karpathy Agent", "verdict": "PASS"}, {"round": 2, "reviewer": "Ponytail Agent", "verdict": "PASS"},
  {"round": 2, "reviewer": "Impeccable Agent", "verdict": "PASS", "note": "대비 기준 충족"}, {"round": 2, "reviewer": "E2E Agent", "verdict": "PASS"}]}
```

## 5. Finished (end of step 6)

```json
{"stage": "완료", "summary": "모든 리뷰 PASS, 최종 검사 통과, 에이전트 종료. 남은 확인: PR CI 결과",
 "tasks": [{"id": "DONE", "status": "완료", "note": "테스트 통과 · 에이전트 6명 종료"}]}
```
