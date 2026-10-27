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
  - macOS + Homebrew 환경에서 Node.js와 Obsidian 앱을 먼저 설치·갱신. Obsidian이 실행 중이면 앱 교체 전에 중단하며 강제 종료하지 않음
  - CodeGraph 공식 npm CLI를 전역 설치. MCP는 기본 OFF이며 `mcp-setup`으로 활성화
  - Obsidian: Claude는 `obsidian@obsidian-skills`를 의존 플러그인으로 설치. Codex는 upstream의 `skills` CLI로 Markdown·Bases·Canvas·CLI 스킬 4개를 `~/.agents/skills`에 설치
  - MCP 서버(notion, glitchtip, gcloud 등)는 기본 OFF라 `/mcp` 목록에 보이지 않음. 설치가 끝나면 서버별 on/off 목록이 출력되고, `mcp-setup` 스킬("notion MCP 켜줘")로 필요한 것만 켬. Claude Code는 플러그인 MCP를 '목록에 보이되 꺼진 상태'로 둘 수 없기 때문
  - Homebrew의 `node` 최신 안정 버전을 사용하고 Node.js 22.20 이상인지 검증(`skills` CLI 요구사항). 갱신된 Node 경로를 설치 스크립트와 하위 npm/npx 명령에 적용하며 사용자 셸 설정은 변경하지 않음
  - Claude: OMC 플러그인을 의존성으로 설치하고, `omc`가 없으면 공식 npm 패키지 설치 후 `omc setup --quiet` 실행. Basic Team용 Agent Teams 환경 변수와 office 결재 대기용 `MCP_TOOL_TIMEOUT=325000`도 Claude 사용자 설정에 설정
  - Codex: `omx`가 없으면 공식 npm 패키지 설치 후 사용자 범위의 plugin 모드로 setup. 사용자 `AGENTS.md`가 있으면 병합하고, 없으면 생성
  - 설치 후 새 세션에서 `omc` 또는 `omx`로 harness 실행 가능
  - Claude/Codex의 마켓플레이스 명령으로 플러그인만 설치하면 npm 설치·setup은 실행되지 않으므로 위 스크립트를 사용해야 합니다.
- `remove` : plugin 제거
  - CodeGraph MCP 등록을 제거하고 npm CLI를 삭제. 다른 도구에서 CodeGraph MCP가 켜져 있으면 CLI는 유지. 프로젝트의 `.codegraph/` 인덱스는 보존
  - 해당 도구의 Obsidian 의존 플러그인/스킬을 제거. 다른 에이전트도 쓰는 Codex 공유 스킬은 `skills` CLI가 보존할 수 있음. Obsidian 앱과 vault는 보존
  - Agent Teams·`MCP_TOOL_TIMEOUT` 값은 설치 스크립트가 설정했고 값이 그대로인 경우에만 이전 값으로 복구
  - 별도로 사용할 수 있는 OMC/OMX npm 패키지와 사용자 설정·실행 기록은 보존
  - 이미 없는 플러그인은 건너뛰며, 다른 도구에서 사용 중인 GlitchTip 터널은 유지
- `reload` : CLI·harness·의존 플러그인 업데이트 후 plugin 재설치
  - `install`과 동일하게 Node.js·Obsidian 앱을 먼저 갱신. 이 단계가 실패하면 플러그인 갱신을 진행하지 않음
  - CodeGraph npm CLI를 최신 버전으로 갱신. MCP 활성화 상태는 유지
  - Claude Agent Teams·`MCP_TOOL_TIMEOUT` 설정을 다시 적용
  - 업데이트 후 codex, claude 세션 모두 재실행 필요
  - Codex: `codex update`, OMX npm 최신 안정 버전 설치, Ponytail·ELI5 마켓플레이스 갱신 및 재설치, Impeccable 최신 CLI로 스킬 강제 갱신, Obsidian 스킬을 원본에서 다시 설치해 갱신
  - Claude: `claude update`, OMC npm 최신 안정 버전 설치, Ponytail·ELI5·Impeccable·OMC·Obsidian 마켓플레이스 및 플러그인 업데이트
  - 마지막에 OMC/OMX setup을 다시 실행. 명령이 실패하면 종료하고 다음 단계는 실행하지 않음

# Decision Skills

| 스킬 | 사용 목적 |
| --- | --- |
| `$llm-council` | 중요한 결정을 다섯 관점의 독립 분석·익명 상호 검토로 검증하고 최종 권고 제시 |

예: `$llm-council 지금 자동화를 만들지, 수작업으로 수요를 먼저 검증할지 검토해줘`.
Claude Code와 Codex의 네이티브 서브에이전트를 사용합니다. 여러 모델을 호출하는 방식은 아니며, 서브에이전트 미지원 시 제약을 밝힙니다.

# Obsidian

이 저장소는 도구와 업무 절차를 배포하며, 실제 기록은 사용자가 지정한 별도 Obsidian vault에 저장합니다.
[kepano/obsidian-skills](https://github.com/kepano/obsidian-skills)의 문법·앱 조작 지식을 재사용하고, `$obsidian-work`는 업무 시작·종료와 ingest/query/lint 절차를 담당합니다. 두 호스트 모두 기존 manifest의 `./skills/`에서 이 공통 스킬을 발견합니다.

- Claude: upstream 플러그인 전체를 설치합니다. Markdown·Bases·Canvas·CLI 외에 Defuddle·Knap 스킬도 포함되지만, 해당 실행 도구를 별도로 설치하지는 않습니다.
- Codex: `npx skills add`의 `--global --agent codex --copy`로 필요한 4개만 설치합니다. 목적지는 `$CODEX_HOME`과 별개인 `~/.agents/skills`이며 `install`·`reload`는 동명의 설치본을 원본으로 갱신하므로 직접 수정하지 않습니다.
- [Homebrew](https://docs.brew.sh/Manpage)로 `node`와 [Obsidian cask](https://formulae.brew.sh/cask/obsidian)를 설치·갱신합니다. 수동 설치된 기존 Obsidian 앱도 최신 앱으로 교체해 Homebrew 관리로 전환합니다. 자체 업데이트 앱도 갱신하도록 `--greedy`를 사용하며, `remove`는 Node.js·Obsidian 앱·vault를 보존합니다.
- [공식 Obsidian CLI](https://obsidian.md/help/cli)는 현재 cask의 바이너리 링크로 PATH에 등록됩니다. 앱에서 필요한 CLI 설정은 Settings → General → Command line interface에서 확인합니다. 설치 스크립트는 PATH 등록 여부만 알리고 앱 실행·연결은 검사하지 않습니다. CLI가 없어도 일반 Markdown 조회·기록은 가능합니다.
- Obsidian MCP와 자동 기록 훅은 추가하지 않습니다. vault 생성·스키마 변경·Git 커밋·푸시도 설치 과정에서 실행하지 않습니다.

사용 예:

```text
Codex: $obsidian-work /절대경로/업무-vault에서 오늘 업무 시작해줘
Claude: /lukas-plugin:obsidian-work /절대경로/업무-vault에 이번 세션 결정사항과 후속 작업 기록해줘
```

이후 같은 vault에서 `이 자료를 ingest해줘`, `기록을 근거로 답해줘`, `링크 lint해줘`처럼 요청할 수 있습니다. 스킬은 vault의 기존 규칙과 폴더 구조를 따릅니다. 배포 소스를 갱신한 뒤에는 위 `reload` 명령으로 설치본을 갱신하고 새 세션을 시작합니다.

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
