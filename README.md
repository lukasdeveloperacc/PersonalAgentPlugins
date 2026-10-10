# Custom Plugin

- 개인 특화 Harness 관리용 Plugin 원격 개발 저장소 입니다.
- 자세한 정보는 @AGENTS.md 를 읽어주세요

---

# Setup

```
PLUGIN_NAME="lukas-plugin"
mkdir -p plugins
ln -sfn .. "plugins/${PLUGIN_NAME}"
```

# Enroll Plugin

```bash
./scripts/plugin.sh codex install
./scripts/plugin.sh codex remove
./scripts/plugin.sh codex reload

./scripts/plugin.sh claude install
./scripts/plugin.sh claude remove
./scripts/plugin.sh claude reload
```

- `install` : 이 원격저장소의 plugin 설치
  - CodeGraph 공식 npm CLI를 전역 설치. MCP는 기본 OFF이며 `mcp-setup`으로 활성화
  - Node.js 20 이상과 npm 필요. npm 전역 설치 경로가 `PATH`에 있어야 합니다.
  - Claude: OMC 플러그인을 의존성으로 설치하고, `omc`가 없으면 공식 npm 패키지 설치 후 `omc setup --quiet` 실행. Basic Team용 Agent Teams 환경 변수도 Claude 사용자 설정에 설정
  - Codex: `omx`가 없으면 공식 npm 패키지 설치 후 사용자 범위의 plugin 모드로 setup. 사용자 `AGENTS.md`가 있으면 병합하고, 없으면 생성
  - 설치 후 새 세션에서 `omc` 또는 `omx`로 harness 실행 가능
  - Claude/Codex의 마켓플레이스 명령으로 플러그인만 설치하면 npm 설치·setup은 실행되지 않으므로 위 스크립트를 사용해야 합니다.
- `remove` : plugin 제거
  - CodeGraph MCP 등록을 제거하고 npm CLI를 삭제. 다른 도구에서 CodeGraph MCP가 켜져 있으면 CLI는 유지. 프로젝트의 `.codegraph/` 인덱스는 보존
  - Agent Teams 값은 설치 스크립트가 설정했고 값이 그대로인 경우에만 이전 값으로 복구
  - 별도로 사용할 수 있는 OMC/OMX npm 패키지와 사용자 설정·실행 기록은 보존
  - 이미 없는 플러그인은 건너뛰며, 다른 도구에서 사용 중인 GlitchTip 터널은 유지
- `reload` : CLI·harness·의존 플러그인 업데이트 후 plugin 재설치
  - CodeGraph npm CLI를 최신 버전으로 갱신. MCP 활성화 상태는 유지
  - Claude Agent Teams 설정을 다시 적용
  - 업데이트 후 codex, claude 세션 모두 재실행 필요
  - Codex: `codex update`, OMX npm 최신 안정 버전 설치, Ponytail·ELI5 마켓플레이스 갱신 및 재설치, Impeccable 최신 CLI로 스킬 강제 갱신
  - Claude: `claude update`, OMC npm 최신 안정 버전 설치, Ponytail·ELI5·Impeccable·OMC 마켓플레이스 및 플러그인 업데이트
  - 마지막에 OMC/OMX setup을 다시 실행. 명령이 실패하면 종료하고 다음 단계는 실행하지 않음

Harness setup은 사용자 전역 설정을 갱신합니다. OMC는 `~/.claude/CLAUDE.md`의 사용자 내용을 병합하고, OMX는 사용자 범위의 `AGENTS.md`를 병합하며 프로젝트의 `AGENTS.md`는 변경하지 않습니다. `reload`는 harness를 npm의 `@latest`로 업데이트한 뒤 기존 사용자 범위의 setup 정책을 적용합니다.

MCP 관리 스크립트는 `skills/mcp-setup/scripts/mcp.sh`에 있습니다. 이전 경로 `scripts/mcp.sh`도 새 스크립트로 전달하므로 기존 호출은 계속 동작합니다.

## Basic Team

Codex는 `$basic-team <작업>`, Claude는 `/lukas-plugin:basic-team <작업>`으로 호출합니다. 플러그인 reload 후 새 세션에서 사용할 수 있습니다.

- Planner: `ralplan` 기반 계획, 미설치 시 `plan` 사용. Frontend/Backend 각각의 병렬 작업을 찾아 작업·파일·담당자·의존성·연결 규약을 명시. Frontend 계획에는 `impeccable`의 UX·디자인 기준을 참고
- Executor: Frontend/Backend 각각 여러 네이티브 에이전트가 독립 작업을 병렬 구현. 준비된 작업부터 가용 슬롯에 배정하고 공용 파일·통합 작업은 단일 담당자를 지정
- Karpathy Agent와 Ponytail Senior Agent: 독립 리뷰 후 둘 다 같은 최종 구현에 `PASS`할 때까지 수정·재검토
  - Frontend·Backend에서 외부 라이브러리 API·버전 의존 동작·의존성 버전이 바뀌면 Context7으로 실제 사용 버전에 맞는 문서를 확인. MCP나 해당 버전 문서가 없으면 공식 문서·upstream 소스로 대체하고 확인 근거·남은 불확실성을 보고
- Impeccable reviewer: Frontend 디자인·UX 평가가 필요할 때만 생성해 `impeccable`로 평가. 생성된 경우 이 리뷰어의 최종 `PASS`도 필요하며 기존 Reviewer 모델·추론 설정 사용
- E2E reviewer: 여러 화면·Frontend/Backend/저장소·인증·서비스가 연결되는 동작을 변경하거나 E2E 검증을 요청하면 독립 에이전트로 전체 흐름·관련 실패 경로를 검증. 기존 Reviewer 모델·추론 설정을 사용하며 같은 최종 구현의 `PASS`가 필요
  - 브라우저 검증은 Orca 환경에서 Orca browser 우선. Orca 환경이 없으면 `mcp-setup`으로 `chrome-devtools` 상태를 확인해 필요할 때만 켜고, 실제 도구 연결 후 검증. 브라우저 검증·재검토 종료 또는 취소·종료 blocker 시 원래 켜져 있었더라도 해당 MCP를 끄고 확인. 다른 MCP는 유지하며 Impeccable의 브라우저 검증에도 같은 정책 적용
  - MCP 설정 변경은 현재 세션의 연결·토큰 사용에 즉시 반영되지 않을 수 있음. 도구가 없는 Codex 세션에서는 새 세션으로 같은 진행판·검토 대상을 이어가며, 연결 전에는 E2E 성공으로 표시하지 않음
- Main Session: 실행 프로젝트의 `docs/inprogress/<작업명>-<시작시각>-progress.html`에 `eli5`로 하나의 HTML 진행판을 유지. 같은 작업의 추가 요청·세션 재개는 기존 파일을 갱신하고, 별도 작업은 새 파일 생성. 모든 브리핑에 진행판 링크·절대 경로·확인된 저장 시각을 표시. 계획 / 에이전트별 진행 / 리뷰·검증 / 결정·막힌 일 탭으로 나누고 짧게 브리핑
- 진행판 저장: `uv run`으로 실행하는 [업데이트 스크립트](skills/basic-team/scripts/progress.py)로 부분 JSON을 병합하고 안전하게 저장. Main은 회신 수신 → 저장 성공 확인 → 다음 배정·브리핑 순서를 지키며, 실패한 업데이트는 미처리로 유지. 세션 재개 시 기존 경로·체크포인트·미저장 보고를 이어감. [저장·재개·테스트 명령](skills/basic-team/references/progress-updates.md)
- 진행판 훅: 기본 비활성. Codex·Claude에서 basic-team Main이 기존 진행판을 확인하고 현재 작업 구간을 명시적으로 등록한 경우에만 안내. 새 입력·재개·compaction 때 등록을 초기화하고, 계속하는 Main이 다시 등록. 일반 작업·자식·식별 불가 이벤트는 안내 없이 종료. 플러그인 전용 상태만 관리하며 진행판·OMX/OMC 상태를 수정하거나 작업을 차단하지 않음. [활성화·해제 규칙](skills/basic-team/references/progress-updates.md#scoped-nonblocking-host-reminders)
- 진행판 디자인: [공통 HTML 템플릿](skills/basic-team/assets/progress-template.html)을 사용. 반응형 에이전트 그래프·보고 요약 툴팁·노드 클릭 상세 모달·진행 파일 절대 경로와 복사 버튼을 제공. 실제 선행 관계만 연결선으로 표시하고 모델·상태는 노드에서 바로 확인하며, 시작·완료 브리핑에도 파일 링크와 경로를 명시
- 협업: 반복 상태 조회 대신 네이티브 회신·완료 알림으로 후속 작업을 진행. 할 일이 없으면 이벤트 대기하고, 필요한 변경 사항만 전달하여 토큰 낭비를 줄임
- 막힌 작업: 코드·설정·오류 근거·공식 문서를 먼저 조사해 합리적인 해결책을 적용. 중요한 모호함이나 사용자 결정이 남으면 Main Session이 조사 결과·추천안과 함께 질문하고, 영향 없는 작업은 계속 진행

역할별 모델·추론 수준은 [basic-team 스킬](skills/basic-team/SKILL.md)에 지정되어 있습니다. 정확한 설정을 선택할 수 없는 환경에서는 대체 모델로 진행하지 않고 제한을 보고합니다. Claude는 2.1.293 이상과 OMC `team`의 네이티브 팀 기능이 필요합니다. Codex는 네이티브 협업 도구를, Claude는 OMC `team`의 네이티브 팀·메시지·종료 절차를 사용합니다. Planner는 ralplan의 계획·검토 방법을 적용하며 별도 OMX/OMC 실행 런타임은 시작하지 않습니다.
