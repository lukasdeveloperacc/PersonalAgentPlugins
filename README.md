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
  - MCP 서버(notion, glitchtip, gcloud 등)는 기본 OFF라 `/mcp` 목록에 보이지 않음. 설치가 끝나면 서버별 on/off 목록이 출력되고, `mcp-setup` 스킬("notion MCP 켜줘")로 필요한 것만 켬. Claude Code는 플러그인 MCP를 '목록에 보이되 꺼진 상태'로 둘 수 없기 때문
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

# Team Skills

팀장은 동급으로 협의하고, 각 팀의 worker는 자기 팀장에게만 보고합니다. 사용자는 팀별 진행·막힘·리뷰 결과를 확인합니다.

| 스킬 | 사용 목적 |
| --- | --- |
| `$basic-team` | 필요한 팀을 골라 계획·구현·리뷰·통합을 조율 |
| `$basic-plan-team` | Karpathy 지침을 기본 적용하고 기존 ralplan harness로 계획 작성·검토; 계획만 요청하면 구현 없이 종료 |
| `$basic-frontend-team` | UI·상태·접근성·API 사용 작업 또는 도메인 리뷰 |
| `$basic-backend-team` | API·권한·데이터 계약 작업 또는 도메인 리뷰 |
| `$basic-docs-team` | 근거에 맞춘 문서 작업 또는 문서 리뷰 |
| `$basic-reviewer-team` | Karpathy·Ponytail, 필요한 Impeccable·E2E 리뷰; 제품 수정은 원 담당 팀에 반환 |
| `$thegame-basic-team` | basic-team의 공개 작업을 한 Notion Task의 체크리스트로 동기화 |

예: `$basic-frontend-team 로그인 폼의 오류 상태를 개선해줘`, `$basic-team 가져오기 API와 UI를 함께 수정해줘`.
Frontend·Backend 팀장과 구현 worker는 Karpathy·Ponytail 지침을 기본 적용하고, 별도의 독립 외부 리뷰도 유지합니다. 단독 구현 팀도 필요한 외부 리뷰를 거칩니다. 팀 계층·peer 통신 지원은 실행 호스트에서 확인하며, 미지원이면 구체적 제약을 보고합니다.

진행 보고는 root가 시작할 때 한 번 선택합니다. Office `report`·`ask`가 사용 가능하고 초기 보고가 성공하면 Office를 사용하며 HTML을 만들지 않습니다. Office가 명시적으로 없거나 꺼져 있으면 기존 progress HTML을 사용합니다. 활성화됐지만 연결이 깨진 경우와 설정이 불명확한 경우는 별도로 진단하며, 실행 중 장애가 나도 자동으로 다른 보고 방식으로 바꾸지 않습니다. 재개 시에도 같은 run과 보고 방식을 유지합니다.
