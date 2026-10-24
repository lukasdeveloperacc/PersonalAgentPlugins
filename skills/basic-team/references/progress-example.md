# Team progress example

The first seven JSON blocks are consecutive portable patches for one run; the final example is Office-only. Root publishes meaningful team tasks; worker results stay in the run's evidence files. Read [reporting.md](reporting.md) for backend selection and resume. `after` means a dependency, never a parent/child relationship.

At startup, root selects Office after discovering `report` and `ask` schemas through a supported MCP transport and a successful initial report; actual question/answer execution remains unverified until a real decision. Send each block as the `patch` argument with the same `run_id` and absolute `project_path`. Normal Office runs create no HTML page or full local snapshot. If Office is explicitly absent/disabled at startup, root selects HTML and initializes it once:

```sh
uv run "<skill-dir>/scripts/progress.py" init "<project>/docs/inprogress/import-fix.html" --title "가져오기 상태·검증 개선"
uv run "<skill-dir>/scripts/progress.py" update "<project>/docs/inprogress/import-fix.html" --input "<patch.json>"
```

Resume the selected backend and existing run/page. An enabled but broken Office is NOT READY; unknown configuration is UNKNOWN. Neither is an instruction to create HTML. An Office outage during work leaves reporting explicitly unsynchronized, with bounded diagnosis/retry and terminal summaries; mode stays Office.

Cards show actual team owners, counts, blockers and evidence. A model/effort belongs only to the actual agent represented by that card; do not attribute worker models to a team leader. Evidence notes distinguish `담당자 보고` from `직접 확인`. All paths and revision labels below are illustrative; use actual observations in a real run.

The lead settings below illustrate observed values, not defaults to copy. Keep each lead/leaf's canonical ID, parent, native ID, display owner and observation source in the existing evidence artifact. `backend_lead` may be a native ID while `backend-lead` is its Office owner; canonical root uses display owner `leader`. The observed registry has no dedicated Reviewer lead seat, so the aggregate gate (`R1-X`) has an empty owner and each external reviewer gets its own card owned by its exact label; never rename the Reviewer lead to root's `leader` to force placement. See [office-operations.md](office-operations.md) for display checks.

## 1. Publish the plan and team work

```json
{"stage":"구현","summary":"계획 검토가 끝났습니다. Backend가 API 계약을 먼저 확정하고 Frontend와 Docs가 이어서 작업합니다","blockers":"없음","todo":"없음",
 "tasks":[
  {"id":"PLAN","title":"ralplan 계획","owner":"leader","lane":"plan","status":"완료","note":"설치된 harness 계획 종료·실행 권한 확인"},
  {"id":"API","title":"가져오기 API 계약 합의","owner":"backend-lead","model":"gpt-6.1-sol","effort":"medium","lane":"build","status":"진행중","after":["PLAN"],"note":"Frontend·Backend 계약 확인 중 · 팀장 설정 직접 확인 · 근거: docs/inprogress/import-fix-backend.md"},
  {"id":"BE","title":"가져오기 API·검증","owner":"backend-lead","model":"gpt-6.1-sol","effort":"medium","lane":"build","status":"대기중","after":["API"],"note":"0/2 완료 · 계약 합의 대기 · 팀장 설정 직접 확인 · 근거: docs/inprogress/import-fix-backend.md"},
  {"id":"FE","title":"가져오기 UI 상태","owner":"frontend-lead","model":"gpt-6.1-sol","effort":"medium","lane":"build","status":"대기중","after":["API"],"note":"API 계약 대기\n근거: docs/inprogress/import-fix-frontend.md",
   "todos":[{"id":"FE-a","phase":"준비","text":"작업자 분배·acceptance matrix 공유"},{"id":"FE-b","phase":"검증","text":"작업자 결과·호출부 확인"},{"id":"FE-c","phase":"보고","text":"root에 요약"}]},
  {"id":"FE-1","title":"로딩·실패 상태 UI","owner":"frontend-state","model":"gpt-6-luna","effort":"max","lane":"build","status":"대기중","after":["API"],"note":"API 계약 대기",
   "todos":[{"id":"FE-1a","phase":"구현","text":"로딩 상태"},{"id":"FE-1b","phase":"구현","text":"422 실패 메시지"},{"id":"FE-1c","phase":"검증","text":"상태별 테스트","detail":"npx vitest run src/import"}]},
  {"id":"DOC","title":"가져오기 계약 문서","owner":"docs-lead","model":"gpt-6.1-sol","effort":"medium","lane":"build","status":"대기중","after":["API"],"note":"0/1 완료 · API 계약 대기 · 팀장 설정 직접 확인 · 근거: docs/inprogress/import-fix-docs.md"}],
 "decisions":[{"title":"리뷰 범위","body":"Karpathy·Ponytail 필수, UI 변경으로 Impeccable, API→화면 흐름 변경으로 E2E 포함. 독립 Backend domain review도 필요"}]}
```

## 2. Publish a peer agreement and a team blocker

Workers report to their own leaders; leaders agree on the contract and root records it. The blocked team stays open. Independent work continues.

```json
{"summary":"Backend 계약은 완료됐지만 통합 검증이 막혔습니다. Frontend와 Docs는 확인된 계약으로 진행합니다","blockers":"BE: 테스트 버킷 생성 후 통합 검사 재시도 필요",
 "tasks":[
  {"id":"API","status":"완료","note":"API-1 양측 확인 · 계약 revision c1"},
  {"id":"BE","status":"진행중","note":"1/2 완료 · 막힘: 테스트 버킷 없음 · 다음: 시드 후 검증 · 근거: docs/inprogress/import-fix-backend.md"},
  {"id":"FE","status":"진행중","note":"FE-1 진행 중","todos":[{"id":"FE-a","done":true}]},
  {"id":"FE-1","status":"진행중","note":"실패 메시지 작업 중","todos":[{"id":"FE-1a","done":true}]},
  {"id":"DOC","status":"진행중","note":"0/1 완료 · 합의한 응답 코드 문서화"}],
 "decisions":[{"title":"API-1","body":"Frontend·Backend 양측 확인: POST /imports, 422 검증 실패, backend가 API 파일 소유. API task 완료로 BE/FE/DOC 착수; 통합 검증은 BE에서 수행. 영향: FE/DOC, 계약 revision c1"}]}
```

Office only, when the schema advertises it: if this response's `checks` holds a pending check for `BE` (30 minutes unchanged), root asks backend-lead and sends the answer (a reporting backend-lead answers it itself) beside the next patch as a top-level argument, never inside `patch`: `"check_replies":[{"check_id":"<checks[].id>","answer":"<backend-lead가 확인한 실제 상태·막힘·남은 todo·다음 단계>"}]`. Actor cards below without observed settings (`R1-D`, `R2-D`) get a missing-settings check; answer with the missing-record reason instead of filling values. The portable patches below omit `kind`; for Office supporting it, add `kind: "aggregate"` to `R1-X`/`R2-X` at first publication as shown in the Office-only example. Without that schema support, omit the field and explain any aggregate missing-settings check as before.

## 3. Freeze the revision and dispatch independent reviews

Required approval gates stay open until their evidence supports PASS at the current frozen revision. `진행중` means someone is actively reviewing; a gate awaiting fixes is `대기중`. Domain review is an ordinary `review` task. Only the four external names go in `reviews`.

```json
{"stage":"리뷰 (1라운드)","summary":"팀 작업과 검사가 끝났습니다. r1을 고정하고 외부 리뷰와 독립 도메인 검토를 진행합니다","blockers":"없음",
 "tasks":[
  {"id":"BE","status":"완료","note":"2/2 완료 · 통합 검사 통과 (담당자 보고)"},
  {"id":"FE","status":"완료","note":"상태·접근성 검사 통과 (담당자 보고)","todos":[{"id":"FE-b","done":true},{"id":"FE-c","done":true}]},
  {"id":"FE-1","status":"완료","note":"vitest 통과 (담당자 보고)","todos":[{"id":"FE-1b","done":true},{"id":"FE-1c","done":true}]},
  {"id":"DOC","status":"완료","note":"1/1 완료 · 계약 일치 확인 (담당자 보고)"},
  {"id":"R1-D","title":"Backend 독립 도메인 검토 R1","owner":"backend-review-lead","lane":"review","status":"진행중","after":["BE","FE","DOC"],"note":"r1 · 미참여 팀장이 API·권한 검토 중 · 실제 model/effort 미확인 · 근거: docs/inprogress/import-fix-domain.md"},
  {"id":"R1-X","title":"외부 필수 리뷰 R1","owner":"","lane":"review","status":"진행중","after":["BE","FE","DOC"],"note":"r1 · 0/4 PASS · reviewer-lead 전용 좌석 없음 · 근거: docs/inprogress/import-fix-reviews.md"},
  {"id":"R1-K","title":"Karpathy 리뷰 R1","owner":"Karpathy Agent","model":"gpt-6.1-sol","effort":"medium","lane":"review","status":"진행중","after":["BE","FE","DOC"],"note":"r1 · 요구사항·계약 검토 중"},
  {"id":"R1-P","title":"Ponytail 리뷰 R1","owner":"Ponytail Agent","model":"gpt-6.1-sol","effort":"medium","lane":"review","status":"진행중","after":["BE","FE","DOC"],"note":"r1 · 구현·호출부 검토 중"},
  {"id":"R1-I","title":"Impeccable 리뷰 R1","owner":"Impeccable Agent","model":"gpt-6.1-sol","effort":"medium","lane":"review","status":"진행중","after":["BE","FE","DOC"],"note":"r1 · 화면 8칸 캡처 검토 중"},
  {"id":"R1-E","title":"E2E 리뷰 R1","owner":"E2E Agent","model":"gpt-6.1-sol","effort":"medium","lane":"review","status":"진행중","after":["BE","FE","DOC"],"note":"r1 · API→화면 흐름 실행 중"}]}
```

## 4. Collect all findings, then assign the fix

A completed review attempt with CHANGES_REQUIRED is not approval. If it has its own execution card, close that attempt with its verdict preserved. Keep the aggregate approval gate open as `대기중`, not `진행중`: reviewers have stopped working while the file owner fixes the finding. After a new revision, the next round supplies the gate's resolution. A fix must not depend on the still-open gate that its own finding is blocking.

```json
{"stage":"수정 (1라운드)","summary":"모든 1차 리뷰 결과를 모았습니다. 대비 수정 후 새 revision에서 필수 리뷰를 다시 받습니다",
 "tasks":[
  {"id":"R1-D","status":"완료","note":"r1 · PASS · 권한·422 계약 확인 · 근거: docs/inprogress/import-fix-domain.md"},
  {"id":"R1-K","status":"완료","note":"r1 · PASS"},
  {"id":"R1-P","status":"완료","note":"r1 · PASS · 권고 1건"},
  {"id":"R1-I","status":"완료","note":"r1 · CHANGES_REQUIRED · 경고 사유 대비 부족"},
  {"id":"R1-E","status":"완료","note":"r1 · PASS"},
  {"id":"R1-X","status":"대기중","note":"r1 검토 수행 종료 · CHANGES_REQUIRED · 3/4 PASS · 승인 gate 미해결 · 대비 수정과 새 revision 검토 대기"},
  {"id":"FIX","title":"경고 사유 대비 수정","owner":"frontend-lead","model":"gpt-6.1-sol","effort":"medium","lane":"fix","status":"진행중","after":["BE","FE","DOC","R1-D"],"note":"R1 근거 전부 수집 · R1-X finding 수정, 승인 gate는 열린 상태 유지 · 근거: docs/inprogress/import-fix-frontend.md"}],
 "reviews":[
  {"round":1,"reviewer":"Karpathy Agent","verdict":"PASS","note":"r1 · 합의한 범위·API 계약 확인, 필수 결함 없음 · 범위 밖 미검증 · 근거: docs/inprogress/import-fix-reviews.md"},
  {"round":1,"reviewer":"Ponytail Agent","verdict":"PASS","note":"r1 · 호출부·실패 처리 확인, 필수 결함 없음 · 권고: 중복 문구 정리 · 범위 밖 미검증 · 근거: docs/inprogress/import-fix-reviews.md"},
  {"round":1,"reviewer":"Impeccable Agent","verdict":"CHANGES_REQUIRED","note":"r1 · 경고 사유 텍스트 대비가 기준 미달: 필수 수정 · 화면 8칸 확인, 그 외 범위 미검증 · 근거: docs/inprogress/import-fix-reviews.md"},
  {"round":1,"reviewer":"E2E Agent","verdict":"PASS","note":"r1 · 필수 API→화면 흐름 직접 실행, 필수 결함 없음 · 범위 밖 미검증 · 근거: docs/inprogress/import-fix-reviews.md"}]}
```

## 5. Dispatch another round on the new revision

`after` names completed prerequisites: the fix follows completed build/domain tasks, and R2 follows the completed fix. R1-X findings trigger the fix after all R1 evidence is collected; that still-open approval gate is not a scheduling prerequisite for its own fix. Old PASS results do not approve r2.

```json
{"stage":"리뷰 (2라운드)","summary":"대비 수정과 검사가 끝났습니다. r2를 고정하고 필수 리뷰 전체를 다시 진행합니다",
 "tasks":[
  {"id":"FIX","status":"완료","note":"대비 4.8:1 · 검사 통과 (담당자 보고)"},
  {"id":"R2-D","title":"Backend 독립 도메인 검토 R2","owner":"backend-review-lead","lane":"review","status":"진행중","after":["FIX"],"note":"r2 · 재검토 중 · 실제 model/effort 미확인 · 근거: docs/inprogress/import-fix-domain.md"},
  {"id":"R2-X","title":"외부 필수 리뷰 R2","owner":"","lane":"review","status":"진행중","after":["FIX"],"note":"r2 · 0/4 PASS · 근거: docs/inprogress/import-fix-reviews.md"},
  {"id":"R2-K","title":"Karpathy 리뷰 R2","owner":"Karpathy Agent","model":"gpt-6.1-sol","effort":"medium","lane":"review","status":"진행중","after":["FIX"],"note":"r2 · 재검토 중"},
  {"id":"R2-P","title":"Ponytail 리뷰 R2","owner":"Ponytail Agent","model":"gpt-6.1-sol","effort":"medium","lane":"review","status":"진행중","after":["FIX"],"note":"r2 · 재검토 중"},
  {"id":"R2-I","title":"Impeccable 리뷰 R2","owner":"Impeccable Agent","model":"gpt-6.1-sol","effort":"medium","lane":"review","status":"진행중","after":["FIX"],"note":"r2 · 대비 수정 재검토 중"},
  {"id":"R2-E","title":"E2E 리뷰 R2","owner":"E2E Agent","model":"gpt-6.1-sol","effort":"medium","lane":"review","status":"진행중","after":["FIX"],"note":"r2 · 흐름 재실행 중"}]}
```

## 6. All required evidence passes; perform final checks

Root checks the required acceptance cells and revision, then resolves the earlier gate. The reducer checks open tasks; it does not independently prove reviewer PASS semantics.

```json
{"stage":"마무리","summary":"r2의 외부 4명과 독립 도메인 검토가 모두 PASS했습니다. 최종 검사와 팀 종료를 확인합니다",
 "tasks":[
  {"id":"R1-X","status":"완료","note":"r1 finding 해소 · 최종 승인 근거는 r2/R2-X"},
  {"id":"R2-D","status":"완료","note":"r2 · PASS · 근거: docs/inprogress/import-fix-domain.md"},
  {"id":"R2-K","status":"완료","note":"r2 · PASS"},
  {"id":"R2-P","status":"완료","note":"r2 · PASS"},
  {"id":"R2-I","status":"완료","note":"r2 · PASS"},
  {"id":"R2-E","status":"완료","note":"r2 · PASS"},
  {"id":"R2-X","status":"완료","note":"r2 · 4/4 PASS · required cell 직접 확인 · 근거: docs/inprogress/import-fix-reviews.md"},
  {"id":"DONE","title":"최종 검사·팀 종료·보고","owner":"leader","model":"gpt-6.1-sol","effort":"medium","lane":"finish","status":"진행중","after":["R2-D","R2-X"]}],
 "reviews":[
  {"round":2,"reviewer":"Karpathy Agent","verdict":"PASS","note":"r2 · 합의한 API·UI 요구사항과 계약 확인, 필수 결함 없음 · 범위 밖 미검증 · 근거: docs/inprogress/import-fix-reviews.md"},
  {"round":2,"reviewer":"Ponytail Agent","verdict":"PASS","note":"r2 · 호출부·실패 처리 확인, 필수 결함 없음 · R1 중복 문구 권고는 선택 사항 · 범위 밖 미검증 · 근거: docs/inprogress/import-fix-reviews.md"},
  {"round":2,"reviewer":"Impeccable Agent","verdict":"PASS","note":"r2 · 화면 8칸에서 수정된 대비 4.8:1 확인, 필수 결함 없음 · 범위 밖 미검증 · 근거: docs/inprogress/import-fix-reviews.md"},
  {"round":2,"reviewer":"E2E Agent","verdict":"PASS","note":"r2 · 필수 API→화면 흐름과 422 실패 시나리오 직접 실행, 필수 결함 없음 · 범위 밖 미검증 · 근거: docs/inprogress/import-fix-reviews.md"}]}
```

## 7. Finish the same run

```json
{"summary":"팀 작업·필수 리뷰·최종 검사 완료, 하위 에이전트 종료 확인. 변경은 작업 트리에 있습니다","todo":"없음","blockers":"없음",
 "tasks":[{"id":"DONE","status":"완료","note":"최종 검사 통과 (직접 확인) · 팀 종료 확인"}]}
```

For a standalone Frontend run, root publishes only its Frontend work and needed review/fix/final tasks; Backend and Docs are not placeholder teams. The same task/review fields and finish gate apply. Root still owns reporting and creates the Frontend and Reviewer leaders as peers.

## Office-only actor and aggregate cards

Only when the advertised `report` input schema includes `patch.tasks[].kind`, use this additional example as `patch` with the saved run ID. Do not send `kind` to an older Office or the HTML helper. The model/effort below illustrate observed root values; replace them with this run's actual observations. Canonical `/root` remains in evidence; `leader` is only its Office display key. The gate has no single executor and no model/effort, while each actual reviewer still has its own actor card and verified settings.

```json
{"tasks":[
  {"id":"MOTION","title":"모션 구현","kind":"actor","owner":"leader","model":"gpt-6.1-sol","effort":"medium","lane":"build","status":"진행중","note":"실제 root 설정 직접 확인 · canonical /root는 실행 근거에 보존"},
  {"id":"REVIEW","title":"필수 리뷰 승인 집계","kind":"aggregate","owner":"","lane":"review","status":"진행중","note":"실제 리뷰 진행 중 · 개별 reviewer 카드의 같은 revision 결과 취합",
   "todos":[{"id":"REVIEW-1","phase":"검증","text":"필수 reviewer의 같은 revision 근거 확인"}]}]}
```

The aggregate's model/effort exemption does not skip TODO/staleness checks or approval/completion evidence. If reviewers finish with required findings, put this gate in `대기중` and preserve its unfinished TODO until fixes and same-revision approval are verified.
