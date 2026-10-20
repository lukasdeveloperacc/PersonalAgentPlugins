# Team progress example

These seven JSON blocks are consecutive patches for one run. Root publishes meaningful team tasks; worker results stay in the run's evidence files. Read [reporting.md](reporting.md) for backend selection and resume. `after` means a dependency, never a parent/child relationship.

At startup, root selects Office after callable `report` and `ask` plus a successful initial report. Send each block as the `patch` argument with the same `run_id` and absolute `project_path`. Normal Office runs create no HTML page or full local snapshot. If Office is explicitly absent/disabled at startup, root selects HTML and initializes it once:

```sh
uv run "<skill-dir>/scripts/progress.py" init "<project>/docs/inprogress/import-fix.html" --title "가져오기 상태·검증 개선"
uv run "<skill-dir>/scripts/progress.py" update "<project>/docs/inprogress/import-fix.html" --input "<patch.json>"
```

Resume the selected backend and existing run/page. An enabled but broken Office is NOT READY; unknown configuration is UNKNOWN. Neither is an instruction to create HTML. An Office outage during work leaves reporting explicitly unsynchronized, with bounded diagnosis/retry and terminal summaries; mode stays Office.

Cards show actual team owners, counts, blockers and evidence. A model/effort belongs only to the actual agent represented by that card; do not attribute worker models to a team leader. Evidence notes distinguish `담당자 보고` from `직접 확인`. All paths and revision labels below are illustrative; use actual observations in a real run.

## 1. Publish the plan and team work

```json
{"stage":"구현","summary":"계획 검토가 끝났습니다. Backend가 API 계약을 먼저 확정하고 Frontend와 Docs가 이어서 작업합니다","blockers":"없음","todo":"없음",
 "tasks":[
  {"id":"PLAN","title":"ralplan 계획","owner":"root","lane":"plan","status":"완료","note":"설치된 harness 계획 종료·실행 권한 확인"},
  {"id":"API","title":"가져오기 API 계약 합의","owner":"backend-lead","lane":"build","status":"진행중","after":["PLAN"],"note":"Frontend·Backend 계약 확인 중"},
  {"id":"BE","title":"가져오기 API·검증","owner":"backend-lead","lane":"build","status":"대기중","after":["API"],"note":"0/2 완료 · 계약 합의 대기 · 근거: docs/inprogress/import-fix-backend.md"},
  {"id":"FE","title":"가져오기 UI 상태","owner":"frontend-lead","lane":"build","status":"대기중","after":["API"],"note":"0/2 완료 · API 계약 대기"},
  {"id":"DOC","title":"가져오기 계약 문서","owner":"docs-lead","lane":"build","status":"대기중","after":["API"],"note":"0/1 완료 · API 계약 대기"}],
 "decisions":[{"title":"리뷰 범위","body":"Karpathy·Ponytail 필수, UI 변경으로 Impeccable, API→화면 흐름 변경으로 E2E 포함. 독립 Backend domain review도 필요"}]}
```

## 2. Publish a peer agreement and a team blocker

Workers report to their own leaders; leaders agree on the contract and root records it. The blocked team stays open. Independent work continues.

```json
{"summary":"Backend 계약은 완료됐지만 통합 검증이 막혔습니다. Frontend와 Docs는 확인된 계약으로 진행합니다","blockers":"BE: 테스트 버킷 생성 후 통합 검사 재시도 필요",
 "tasks":[
  {"id":"API","status":"완료","note":"API-1 양측 확인 · 계약 revision c1"},
  {"id":"BE","status":"진행중","note":"1/2 완료 · 막힘: 테스트 버킷 없음 · 다음: 시드 후 검증 · 근거: docs/inprogress/import-fix-backend.md"},
  {"id":"FE","status":"진행중","note":"1/2 완료 · 로딩·실패 상태 구현 · 근거: docs/inprogress/import-fix-frontend.md"},
  {"id":"DOC","status":"진행중","note":"0/1 완료 · 합의한 응답 코드 문서화"}],
 "decisions":[{"title":"API-1","body":"Frontend·Backend 양측 확인: POST /imports, 422 검증 실패, backend가 API 파일 소유. API task 완료로 BE/FE/DOC 착수; 통합 검증은 BE에서 수행. 영향: FE/DOC, 계약 revision c1"}]}
```

## 3. Freeze the revision and dispatch independent reviews

All required review tasks stay open until their evidence supports PASS at the current frozen revision. Domain review is an ordinary `review` task. Only the four external names go in `reviews`.

```json
{"stage":"리뷰 (1라운드)","summary":"팀 작업과 검사가 끝났습니다. r1을 고정하고 외부 리뷰와 독립 도메인 검토를 진행합니다","blockers":"없음",
 "tasks":[
  {"id":"BE","status":"완료","note":"2/2 완료 · 통합 검사 통과 (담당자 보고)"},
  {"id":"FE","status":"완료","note":"2/2 완료 · 상태·접근성 검사 통과 (담당자 보고)"},
  {"id":"DOC","status":"완료","note":"1/1 완료 · 계약 일치 확인 (담당자 보고)"},
  {"id":"R1-D","title":"Backend 독립 도메인 검토 R1","owner":"backend-review-lead","lane":"review","status":"진행중","after":["BE","FE","DOC"],"note":"r1 · 미참여 팀장이 API·권한 검토 중"},
  {"id":"R1-X","title":"외부 필수 리뷰 R1","owner":"reviewer-lead","lane":"review","status":"진행중","after":["BE","FE","DOC"],"note":"r1 · 0/4 PASS · 근거: docs/inprogress/import-fix-reviews.md"}]}
```

## 4. Collect all findings, then assign the fix

A completed review attempt with CHANGES_REQUIRED is not completion of the required review task. Keep that task open; after a new revision, the next round supplies its resolution.

```json
{"stage":"수정 (1라운드)","summary":"모든 1차 리뷰 결과를 모았습니다. 대비 수정 후 새 revision에서 필수 리뷰를 다시 받습니다",
 "tasks":[
  {"id":"R1-D","status":"완료","note":"r1 · PASS · 권한·422 계약 확인 · 근거: docs/inprogress/import-fix-domain.md"},
  {"id":"R1-X","note":"r1 · CHANGES_REQUIRED · 3/4 PASS · 대비 수정과 새 revision 검토 대기"},
  {"id":"FIX","title":"경고 사유 대비 수정","owner":"frontend-lead","lane":"fix","status":"진행중","after":["BE","FE","DOC","R1-D"],"note":"R1 근거 전부 수집 · R1-X finding 수정, 승인 gate는 열린 상태 유지 · 근거: docs/inprogress/import-fix-frontend.md"}],
 "reviews":[
  {"round":1,"reviewer":"Karpathy Agent","verdict":"PASS","note":"r1 · 범위·계약 확인"},
  {"round":1,"reviewer":"Ponytail Agent","verdict":"PASS","note":"r1 · 권고: 중복 문구 정리"},
  {"round":1,"reviewer":"Impeccable Agent","verdict":"CHANGES_REQUIRED","note":"r1 · 경고 사유 대비 부족"},
  {"round":1,"reviewer":"E2E Agent","verdict":"PASS","note":"r1 · required flow 직접 실행"}]}
```

## 5. Dispatch another round on the new revision

`after` names completed prerequisites: the fix follows completed build/domain tasks, and R2 follows the completed fix. R1-X findings trigger the fix after all R1 evidence is collected; that still-open approval gate is not a scheduling prerequisite for its own fix. Old PASS results do not approve r2.

```json
{"stage":"리뷰 (2라운드)","summary":"대비 수정과 검사가 끝났습니다. r2를 고정하고 필수 리뷰 전체를 다시 진행합니다",
 "tasks":[
  {"id":"FIX","status":"완료","note":"대비 4.8:1 · 검사 통과 (담당자 보고)"},
  {"id":"R2-D","title":"Backend 독립 도메인 검토 R2","owner":"backend-review-lead","lane":"review","status":"진행중","after":["FIX"],"note":"r2 · 재검토 중"},
  {"id":"R2-X","title":"외부 필수 리뷰 R2","owner":"reviewer-lead","lane":"review","status":"진행중","after":["FIX"],"note":"r2 · 0/4 PASS"}]}
```

## 6. All required evidence passes; perform final checks

Root checks the required acceptance cells and revision, then resolves the earlier gate. The reducer checks open tasks; it does not independently prove reviewer PASS semantics.

```json
{"stage":"마무리","summary":"r2의 외부 4명과 독립 도메인 검토가 모두 PASS했습니다. 최종 검사와 팀 종료를 확인합니다",
 "tasks":[
  {"id":"R1-X","status":"완료","note":"r1 finding 해소 · 최종 승인 근거는 r2/R2-X"},
  {"id":"R2-D","status":"완료","note":"r2 · PASS · 근거: docs/inprogress/import-fix-domain.md"},
  {"id":"R2-X","status":"완료","note":"r2 · 4/4 PASS · required cell 직접 확인 · 근거: docs/inprogress/import-fix-reviews.md"},
  {"id":"DONE","title":"최종 검사·팀 종료·보고","owner":"root","lane":"finish","status":"진행중","after":["R2-D","R2-X"]}],
 "reviews":[
  {"round":2,"reviewer":"Karpathy Agent","verdict":"PASS","note":"r2"},
  {"round":2,"reviewer":"Ponytail Agent","verdict":"PASS","note":"r2"},
  {"round":2,"reviewer":"Impeccable Agent","verdict":"PASS","note":"r2 · 대비 기준 충족"},
  {"round":2,"reviewer":"E2E Agent","verdict":"PASS","note":"r2 · required flow 직접 실행"}]}
```

## 7. Finish the same run

```json
{"summary":"팀 작업·필수 리뷰·최종 검사 완료, 하위 에이전트 종료 확인. 변경은 작업 트리에 있습니다","todo":"없음","blockers":"없음",
 "tasks":[{"id":"DONE","status":"완료","note":"최종 검사 통과 (직접 확인) · 팀 종료 확인"}]}
```

For a standalone Frontend run, root publishes only its Frontend work and needed review/fix/final tasks; Backend and Docs are not placeholder teams. The same task/review fields and finish gate apply. Root still owns reporting and creates the Frontend and Reviewer leaders as peers.
