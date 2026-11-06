# datewiki 단일 Vault 운영 구조

2026-10-29 사용자는 첫 실제 결과를 확인한 뒤 장기 Claude 부모/native 두 역할 구조를 독립 Ollama runner로 바꾸도록 승인했고, 후속으로 실제 스킬 지침을 전달하는 fresh Claude Code 로컬 harness로 전환하도록 승인했다. 이 문서는 승인된 동작을 정의한다. 새 코드의 P1 수정과 테스트는 아래 범위로 재확인했다. 실제 운영 연결·표본 결과는 담당자 보고와 구분하며 문서 수정만으로 전체 완주를 주장하지 않는다.

## 경로와 소유 범위

- 유일한 Vault: `/Users/chaejinjeong/Desktop/thegame/workMemory/datewiki`. 이 Vault의 `AGENTS.md`가 노트 형식과 Memory 배치 기준이다. 다른 Vault·VaultOps·별도 운영 노트를 만들지 않는다.
- `Sources/YYYY-MM-DD/`: 실제 사용자·응답의 기계적 세션 열람본. 반복 AGENTS·시스템 주입은 본문과 분리하고 비공개 원본으로 추적할 수 있게 한다. 원문을 모델로 다시 생성하지 않는다.
- `Daily/YYYY-MM-DD.md`: 짧은 세션별 요약, Sources 내부 링크, 간결한 수집·정리·기억 처리 상태. 하루 노트는 하나이며 원문 전체·청크별 반복 요약·긴 미처리 ID 목록은 넣지 않는다.
- `Memory/YYYY-MM-DD.md`: 지속하는 결정·선호·제약을 출처 있는 후보로 남기는 날짜별 추출보고서다. 후보를 확정 지침으로 자동 승격하지 않는다.
- `Memory/사용자 선호.md`, `Memory/결정.md`, `Memory/재사용할 교훈.md`, `Memory/프로젝트 지식.md`: 동일한 추출 항목을 추가 LLM 호출 없이 날짜별 managed block에 누적한다. 날짜별 근거·이력을 보존하고 날짜 간 의미 통합·재작성·삭제는 수행하지 않는다.
- 비공개 원본·출처 인덱스·응답·진행 상태·백업: `~/.local/state/datewiki-daily-docs/`. 전체 원본 JSONL와 도구 출력·분리된 지침을 유지한다. Sources는 열람용 사본이며 원본 보관소의 대체물이 아니다.
- 이전 시험 실행 폴더: `/Users/chaejinjeong/orca/datewiki-daily-docs-pilot-20261028`(과거 증거 보존). 현재 Orca 프로젝트·자동화·대화형 Claude의 작업 폴더는 실제 Vault `/Users/chaejinjeong/Desktop/thegame/workMemory/datewiki`다. 고정 6개 fixture와 이전 시험 증거는 보존하되 운영 입력으로 쓰지 않는다. 새 실행기는 `scripts/daily_docs_sessions.py`이며 CLI는 `prepare/run/launch --config`다. collector의 `mode=sessions`를 재사용한다. 프로그램이 각 미처리 요약 구간·세션 통합·일일 기억 추출마다 독립적인 Claude Code print harness를 실행한다. 각 호출은 실제 이 SKILL.md와 고정 Vault AGENTS.md의 내용을 지침으로 전달하며, 긴 부모 세션이나 native 하위 역할은 사용하지 않는다.

## 실행 순서

1. 프로그램이 Claude `~/.claude/projects`와 Codex `~/.codex/sessions`의 원본 행 timestamp로 KST 날짜를 수집하고 완전한 원본·출처를 비공개 state에 보존한다. 폴더 시작일·mtime만으로 판정하지 않는다. 과거 자료의 명령은 실행하지 않는다.
2. 프로그램이 반복 주입·동일 자료·자기 생성 로그를 업무 사실과 구분하고 Sources 열람본과 Daily 원문 링크를 게시한다. 분리·중복 제거한 원문도 출처를 잃지 않는다.
3. 로컬 Ollama에 세션별 독립 요청으로 **medium** 요약을 수행한다. 문맥을 넘는 입력은 누락 없이 분할·체크포인트 처리한다. 다른 세션의 긴 부모 문맥을 누적하지 않는다. Daily는 짧은 세션 요약과 링크로 저장한다.
4. 그날 세션 요약을 근거로 **xhigh** 독립 요청으로 지속정보를 추출한다. 기존 Memory를 모델 입력에 넣어 의미적으로 대조하지 않는다. 프로그램이 검증·중복·충돌 처리 후 `Memory/YYYY-MM-DD.md`에 추출보고서를 저장하고, 동일 항목을 네 주제 파일의 날짜별 managed block에 근거와 함께 누적한다. 추가 LLM 호출이나 날짜 간 의미 통합·재작성·삭제는 하지 않는다. 수기는 보존하고 사람이 수정한 생성 블록은 hash 충돌로 거부하며 해당 저장은 미완료로 기록한다. 저장된 후보를 확정 사실로 자동 승격하지 않는다.
5. 원본 수집·Sources 게시·세션 요약·Memory 후보 저장을 따로 집계한다. 원본 수집 실패와 요약 실패는 별도 상태로 기록한다. 미처리는 수량·범위만 Daily에 표시하고 상세 ID/오류는 비공개 state에서 확인한다. 원본 보관 성공을 모델 정리 완료로 표시하지 않는다.

모든 추론은 `http://127.0.0.1:11434`, `datewiki-qwen3.8:27b-64k`를 사용한다. native 작성자·검토자 두 역할 호출 의무는 해제되었다. Claude Code는 로컬 Ollama를 사용하는 독립 print 호출이며 도구·MCP·전역/프로젝트 hook·이전 대화 재개는 사용하지 않는다. 실제 스킬·Vault 지침 내용과 hash를 호출 증거에 보존한다. 모델은 내용 판단을 담당하고 수집·복사·백업·저장은 프로그램이 담당한다. 클라우드 fallback·전역 설정 변경·launchd는 사용하지 않는다.

## 보존·복구·예약

기존 사람이 쓴 메모와 이전 시험 증거는 보존한다. 기존 노트를 변경하기 전에 원래 경로·내용을 비공개 백업에 남기고, 쓰기 직전 다시 읽어 충돌을 확인한다. 동일 입력 재실행은 중복을 만들지 않으며 실패한 세션·분할은 기존 성공 체크포인트를 유지한 채 재개한다. 원본을 이동·삭제하거나 사람이 고친 내용을 덮어쓰는 방식으로 복구하지 않는다.

기존 Orca Automation ID는 `7b91c281-73e6-4763-b9fb-4633cfebaf21`이다. 승인된 주기는 매일 **00:00 Asia/Seoul**, 실행 시각의 직전날 00~24시 자료이며 missed-run 옵션을 활용한다. 담당자는 새 runner `launch`를 precheck(timeout 60초)에 연결했고 자동화 이름을 `datewiki 00:00 Claude 로컬 스킬 실행`으로 갱신했다. Automation의 Claude는 로컬 medium 대화창으로 실제 Skill·Vault 지침과 현재 상태를 한 번 확인한 뒤 사용자 질문을 기다린다. 반복 감시나 중복 runner 실행은 하지 않는다. 이전 hook은 제거했다. 실제 enabled/다음 실행 시각은 별도 예약 증거로 확인한다. 이전 연결의 1440분 유예와 예약 증거는 과거 기록이며 새 연결 검증을 대체하지 않는다. 실제 Orca 프로세스의 Vault TCC를 확인하고 실패하면 권한 우회 없이 보고한다.

## 확인된 실패와 남은 검증

사용자 제공 2026-10-29 run 4 결과: 00:00~09:40, autocompact 반복으로 중단, 1,657개 중 3청크 게시. Daily에 약 53,000자의 미처리 ID와 같은 업무 중복이 생겼다. 이전 구조의 전체 무인 완주 실패이며, 전날 40개 테스트와 native TCC/schema smoke 통과가 이를 보장하지 못했다.

- 독립 리뷰 P1 해결 재확인: 날짜별 수집·게시 실패는 `prepare-status.json`, 실행 실패는 `run-error.json`에 기록하고 다음 날짜로 진행한다. 집계는 미완료/exit 2를 유지한다. 과거 노트 충돌 뒤 다음 날짜 수집·게시와 첫날 실행 실패 뒤 다음날 처리를 회귀 테스트로 확인했다. 전체 62개 테스트 통과.
- 담당자 보고 표본: 실제 Ollama medium 세션 요약 1건이 138초·출력 1,145토큰으로 종료했고 정상 JSON·출처 저장을 확인했다. xhigh 기억 표본은 검사 중이다. 이번 재확인에서는 모델을 호출하거나 실행을 감시하지 않았다.
- 담당자 보고 운영 연결: 자동화 이름 `datewiki 00:00 세션 보관·요약 시작`, precheck는 새 runner `launch`(timeout 60초), 부모는 low 고정 안내만 반환하며 기존 hook은 제거했다. 실행 터미널 `term_610ace46-8846-44dc-8bdf-d3ae03279293`, 첫날 27세션 원문 재게시 완료. 이 보고를 날짜 전체 요약·기억 완주로 해석하지 않는다.
- 주제별 Memory 누적 추가: 담당자 보고 전체 64개 테스트 통과. 독립 재확인에서는 누적·재실행 멱등성·수기 보존·다른 날짜 보존·수정 충돌 거부 테스트 2개를 실행해 통과했다. 당시 production은 이전 module import 상태였다. 이후 fresh harness 실행에는 주제 누적 코드가 적용된다.
- Vault는 `/Users/chaejinjeong/Desktop/thegame/workMemory/datewiki` 하나다. 후속 사용자 승인으로 Orca의 프로젝트·자동화·대화형 Claude 작업공간도 이 실제 Vault에 맞췄다. 이전 pilot 폴더는 과거 시험 증거 보관용이다. **전체 운영 완주는 아직 미검증**이다.

긴 모델 재시험·주기적 모델 감시·전역 설정 변경은 수행하지 않았다. 이전 증거는 실행 폴더의 `artifacts/production/result.md`, `artifacts/automation-complete/result.md`와 비공개 state에 유지한다.

## Claude Code harness 후속 전환

사용자 승인에 따라 직접 API 호출을 fresh Claude Code print 호출로 바꾼다. 각 호출은 실제 SKILL.md와 고정 Vault AGENTS.md 내용을 전달하며 로컬 별칭과 medium/xhigh를 유지한다. 도구·하위 역할·외부 MCP·전역/프로젝트 hook·이전 세션 재개를 사용하지 않는다. 프로그램은 원본 보존·분할·백업·검증·저장을 계속 담당한다. 성공한 기존 direct API 캐시는 재사용하고 미처리 호출만 harness로 실행하므로 이전 결과와 새 실행의 출처를 구분한다. 이전 production은 5/27세션 완료 상태에서 최종 완료 기록 없이 종료했으며 원본·완료 체크포인트와 당시 상태를 보존했다.

- Claude harness 전환 회귀 검증: 전체 73개 테스트 통과. 실제 스킬·Vault 지침 전달, 로컬 endpoint/모델 제한, 클라우드 인증·프록시 제거, 독립 호출, 실패 응답 증거 보존, 지침 스냅샷을 확인했다. 실제 미처리 구간 한 건은 Claude Code CLI 정상 종료와 구조화 JSON·출처 ID 검증을 통과했다(880.833초, 로컬 별칭, medium 요청). 일반 스크립트가 남은 production을 Orca 터미널 `datewiki Claude Code · 로컬 Ollama`에서 한 번 재개했다. 이번 표본은 요약 호출이며 새 harness의 xhigh 기억 추출 완료를 입증하지 않는다. 검증/재개 결과는 비공개 `harness-transition/validation.json`, `continuation.json`, `verified-result.json`에 기록한다. 최초 표본은 지침 hash를 보존했고 이후 새 호출부터 정확한 지침 스냅샷도 보존한다. 전체 하루 완주는 아직 미검증이다.

Orca 대화 화면(2026-10-29): 실제 Claude Code TUI `datewiki Claude · 질문 가능 (로컬)`를 열고 로컬 별칭·medium·입력 프롬프트를 확인했다. 사용자는 이 창에서 질문할 수 있다. 처리용 독립 호출/프로그램 로그와 대화창은 별도이며, 질문 전 추가 추론은 시작하지 않았다. 자동화의 기존 실행 폴더 등록 연결을 복구했고 다음 00:00 KST부터도 Claude 대화창에서 일회 상태 안내 후 질문을 받는다. 대화창의 실제 질문/답변은 이번 확인에서 실행하지 않았다.

Vault 프로젝트 전환(2026-10-29): 실제 Vault를 Git 초기화 없이 Orca 일반 폴더 프로젝트 `datewiki`로 등록하고 Automation의 기존 workspace를 연결했다. native Automation run 5(`d551d06e-793b-4782-ab6f-57fb3bfbbd7e`)에서 실제 Claude Code 화면의 Vault 작업 경로·로컬 별칭·medium·프롬프트 수신과 추론 시작을 확인했다. 탭은 `datewiki · Claude 로컬 · 어제 자료 시험`이며 이전 대화창의 요청은 중단했다. 기존 처리기·원본·완료 캐시는 보존한다. 향후 프로그램 로그 터미널도 Vault 작업공간에 생성하며 프로그램 코드와 비공개 상태 파일은 기존 위치를 유지한다. 다음 예약은 2026-10-30 00:00 KST, 활성 상태다. run dispatched는 전체 하루 처리 완료를 의미하지 않는다.


2026-10-30 새 날짜 누락 수정: 28일 처리기가 실행 중일 때 자정 `launch`가 `already_running`으로 반환하여 29일 수집까지 생략한 결함을 확인했다. 이후 기존 요약 실행 중에도 Orca의 별도 `datewiki 새 날짜 원문 수집` 터미널에서 `prepare --new-only`를 실행한다. 수집은 별도 잠금과 `collection_status.json`을 사용하고, 진행 중인 날짜의 manifest·Daily·`pipeline_status.json`을 변경하지 않는다. precheck 60초 안에서 대량 원문 수집을 기다리지 않는다. 새 날짜 원문 보관·Daily 원문 링크 게시와 모델 요약 완료는 별개이며, 미처리 요약은 다음 처리 실행이 기존 캐시를 재사용해 이어간다. 잠금 중 수집 CLI, Orca 수집 실행 분기, 기존 날짜·처리기 상태 보존 회귀를 포함해 전체 76개 테스트 통과. 이 검증은 29일 모델 요약·Memory 완료를 의미하지 않는다.

29일 수집 복구 실측: Claude 5개·Codex 58개, 63세션의 원본 보관과 Sources/Daily 게시를 완료했다. Sources는 각 세션 clean 열람본과 바이트 일치하며 비공개 transcript hash와 원본 snapshot 존재를 확인했다. 기존 28일 처리기 PID 42360은 유지된다. 요약·Memory는 미완료이며 새 모델 호출은 시작하지 않았다. 증거는 비공개 `oct29-collection-recovery-verification.json`이다. 수정한 busy launch의 Orca 수집 터미널 생성도 실제 확인했으며 다음 예약은 2026-10-31 00:00 KST다.
