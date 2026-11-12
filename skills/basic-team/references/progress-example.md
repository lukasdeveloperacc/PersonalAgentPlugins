# Main-owned progress example

Main alone sends these patches, in order, to the selected Office run or existing HTML page. IDs are stable; after means dependency. Native role models below are omitted deliberately: in a real Office run publish actual observed actor values once, or leave them unverified and answer returned checks. With advertised kind support mark APPROVAL aggregate; omit kind in this portable HTML example.

Generic reviewer verdicts live in normal review task notes. They are not the external persona reviews enum. Each required defect must be verified before closing APPROVAL; completed review attempts may carry CHANGES_REQUIRED. Main retains revision/owned patch evidence outside the tracker.

```json
{
 "stage": "구현",
 "summary": "현재 세션이 API 수정 범위와 검사를 정했습니다",
 "tasks": [
  {
   "id": "BE",
   "title": "API 오류 수정",
   "owner": "backend-api",
   "lane": "build",
   "status": "진행중",
   "note": "담당 API 수정과 대상 테스트 진행 중",
   "todos": [
    {
     "id": "BE-1",
     "text": "오류 수정·대상 테스트",
     "phase": "구현"
    }
   ]
  }
 ]
}
```

```json
{
 "stage": "리뷰",
 "tasks": [
  {
   "id": "BE",
   "status": "완료",
   "note": "대상 테스트 통과",
   "todos": [
    {
     "id": "BE-1",
     "done": true
    }
   ]
  },
  {
   "id": "R1",
   "title": "독립 검토",
   "owner": "reviewer-basic",
   "lane": "review",
   "status": "진행중",
   "after": [
    "BE"
   ],
   "note": "owned diff r1 확인 중"
  }
 ]
}
```

```json
{
 "stage": "수정 (1라운드)",
 "tasks": [
  {
   "id": "R1",
   "status": "완료",
   "note": "r1 · CHANGES_REQUIRED · 빈 입력에서 500 재현 · evidence/review.md"
  },
  {
   "id": "APPROVAL",
   "title": "필수 결함 해소",
   "owner": "",
   "lane": "review",
   "status": "대기중",
   "note": "r1 필수 결함 수정 후 변경분 검토 대기",
   "todos": [
    {
     "id": "APPROVAL-1",
     "text": "빈 입력 오류 해소 확인"
    }
   ]
  },
  {
   "id": "FIX",
   "title": "빈 입력 오류 수정",
   "owner": "backend-api",
   "lane": "fix",
   "status": "진행중",
   "after": [
    "BE",
    "R1"
   ],
   "note": "담당 파일 수정 중"
  }
 ]
}
```

```json
{
 "stage": "리뷰",
 "tasks": [
  {
   "id": "FIX",
   "status": "완료",
   "note": "빈 입력 회귀 테스트 통과"
  },
  {
   "id": "R2",
   "title": "수정 변경분 검토",
   "owner": "reviewer-basic",
   "lane": "review",
   "status": "진행중",
   "after": [
    "FIX"
   ],
   "note": "r2 delta 및 연결 위험 확인"
  }
 ]
}
```

```json
{
 "stage": "마무리",
 "tasks": [
  {
   "id": "R2",
   "status": "완료",
   "note": "r2 · PASS · 빈 입력·정상 입력 확인 · evidence/review.md"
  },
  {
   "id": "APPROVAL",
   "status": "완료",
   "note": "r2의 필수 결함 해소 근거 확인",
   "todos": [
    {
     "id": "APPROVAL-1",
     "done": true
    }
   ]
  },
  {
   "id": "DONE",
   "title": "최종 검사·보고",
   "owner": "leader",
   "lane": "finish",
   "status": "진행중",
   "after": [
    "R2",
    "APPROVAL"
   ],
   "note": "최종 diff와 검사 근거 대조 중"
  }
 ]
}
```

```json
{
 "summary": "최종 내용·검증 확인 완료",
 "tasks": [
  {
   "id": "DONE",
   "status": "완료",
   "note": "최종 diff r2와 대상 검사 일치"
  }
 ]
}
```

When Office supports todos use the same merge-by-ID payload. Otherwise publish done/total and the current item in note. Never tick work merely to satisfy closure. User asks/check replies are top-level report arguments, not patch fields; read the advertised schemas and reporting contract.
