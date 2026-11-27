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
  - macOS + Homebrew 환경에서 Node.js와 Obsidian 앱을 먼저 설치·갱신. 실행 중인 Obsidian은 정상 종료를 요청하고 갱신 후 다시 실행하며, 정상 종료가 되지 않으면 앱 교체를 중단
  - CodeGraph 공식 npm CLI를 전역 설치. MCP는 기본 OFF이며 `mcp-setup`으로 활성화
  - Obsidian: Claude는 `obsidian@obsidian-skills`를 의존 플러그인으로 설치. Codex는 upstream의 `skills` CLI로 Markdown·Bases·Canvas·CLI 스킬 4개를 `~/.agents/skills`에 설치
  - [Slack 공식 플러그인](https://github.com/slackapi/slack-skills-plugin) `slack@slack`은 두 도구에서 설치·갱신·제거를 관리. Claude는 Slack MCP를 최초 사용 시 OAuth로 연결하며, Codex의 공식 플러그인은 Slack 개발 스킬을 제공하고 워크스페이스 연동은 기존 Slack 앱에서 사용
  - MCP 서버(notion, glitchtip, radar, gcloud 등)는 기본 OFF라 `/mcp` 목록에 보이지 않음. 설치가 끝나면 서버별 on/off 목록이 출력되고, `mcp-setup` 스킬("notion MCP 켜줘")로 필요한 것만 켬. Claude Code는 플러그인 MCP를 '목록에 보이되 꺼진 상태'로 둘 수 없기 때문
  - Homebrew의 `node` 최신 안정 버전을 사용하고 Node.js 22.20 이상인지 검증(`skills` CLI 요구사항). 갱신된 Node 경로를 설치 스크립트와 하위 npm/npx 명령에 적용하며 사용자 셸 설정은 변경하지 않음
  - Claude: OMC 플러그인을 의존성으로 설치하고, `omc`가 없으면 공식 npm 패키지 설치 후 `omc setup --quiet` 실행. office 결재 대기용 `MCP_TOOL_TIMEOUT=325000`도 Claude 사용자 설정에 설정
  - Codex: `omx`가 없으면 공식 npm 패키지 설치 후 사용자 범위의 plugin 모드로 setup. 사용자 `AGENTS.md`가 있으면 병합하고, 없으면 생성
  - 설치 후 새 세션에서 `omc` 또는 `omx`로 harness 실행 가능
  - Claude/Codex의 마켓플레이스 명령으로 플러그인만 설치하면 npm 설치·setup은 실행되지 않으므로 위 스크립트를 사용해야 합니다.
- `remove` : plugin 제거
  - CodeGraph MCP 등록을 제거하고 npm CLI를 삭제. 다른 도구에서 CodeGraph MCP가 켜져 있으면 CLI는 유지. 프로젝트의 `.codegraph/` 인덱스는 보존
  - 해당 도구의 Obsidian 의존 플러그인/스킬을 제거. 다른 에이전트도 쓰는 Codex 공유 스킬은 `skills` CLI가 보존할 수 있음. Obsidian 앱과 vault는 보존
  - Agent Teams·`MCP_TOOL_TIMEOUT` 값은 설치 스크립트가 설정한 경로와 현재 값이 확인되는 경우에만 이전 값으로 복구. 대상 경로가 없는 옛 기록은 설정과 함께 보존하고 진단 메시지를 출력
  - 별도로 사용할 수 있는 OMC/OMX npm 패키지와 사용자 설정·실행 기록은 보존
  - 이미 없는 플러그인은 건너뛰며, 다른 도구에서 사용 중인 GlitchTip 및 Radar 터널은 유지
- `reload` : CLI·harness·의존 플러그인 업데이트 후 plugin 재설치
  - `install`과 동일하게 Node.js·Obsidian 앱을 먼저 갱신. 이 단계가 실패하면 플러그인 갱신을 진행하지 않음
  - CodeGraph npm CLI를 최신 버전으로 갱신. MCP 활성화 상태는 유지
  - Claude `MCP_TOOL_TIMEOUT` 설정을 다시 적용하고, 대상 경로가 확인되는 과거 Agent Teams 관리 값만 사용자 변경을 보존하며 복구
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

# TheGame Notion 업무 추적

새 작업을 요청했을 때 소속이 불분명하면 에이전트가 “이번 작업을 TheGame 업무로 기록할까요?”라고 묻습니다. “응”이면 같은 응답에서 Task를 오늘 내 Daily의 **🎯 오늘 할 일**에 체크박스로 연결합니다. Daily를 다시 읽고 Task와 Daily 링크를 보여준 뒤 작업을 시작합니다. Daily 기록이 보류되면 그 이유를 알려줍니다. “아니”면 기록 없이 작업합니다. 다음 날 같은 작업을 이어가면 기존 Task를 그날의 내 Daily에도 연결합니다. 그날의 Daily가 없으면 새로 만들고, 어제 Daily와의 연결도 보존합니다.

`$thegame-work-task 정산 CSV 환불 누락 수정 시작해줘. 관련 Slack은 <스레드 URL>이야`처럼 TheGame 업무 추적을 요청하면 TaskBoard에 업무를 등록하고 오늘 내 Daily Scrum TODO와 연결합니다. 이 업무의 PR을 만들 때는 Task와 Slack 원문을 PR에 넣고, PR 링크도 Task에 기록합니다. 완료 기준을 충족하면 Task에 결과와 확인 근거를 요약하고 상태를 DONE으로 바꿉니다. 연결된 Daily의 해당 체크박스까지 다시 읽어 확인한 뒤 두 링크를 보고합니다. 한쪽만 성공하면 남은 항목을 알려주고 재개 시 복구합니다.

Notion MCP 연결이 필요합니다. 같은 Git 워크트리에서 새 세션을 열면 SessionStart 훅이 진행 중인 Task 링크를 에이전트에 전달합니다. [thegame-work-task 스킬](skills/thegame-work-task/SKILL.md)

# Basic work and native agents

사용자가 지시하는 현재 Claude Code/Codex 세션이 메인입니다. `$basic-team`은 필요한 역할을 직접 호출하고 결과·검증을 통합하는 유일한 basic 계열 스킬입니다. 각 subagent는 맡은 일을 직접 수행하고 메인으로 반환합니다.

| 역할 | Claude Code | Codex |
| --- | --- | --- |
| 계획(필요할 때만) | `lukas-plugin:basic-planner` | `basic_planner` |
| 프런트엔드 | `lukas-plugin:basic-frontend` | `basic_frontend` |
| 백엔드 | `lukas-plugin:basic-backend` | `basic_backend` |
| 문서 | `lukas-plugin:basic-docs` | `basic_docs` |
| 독립 리뷰 | `lukas-plugin:basic-reviewer` | `basic_reviewer` |

```text
Codex: basic_backend에게 이 API 오류 수정과 관련 테스트를 맡겨줘
Claude: lukas-plugin:basic-frontend subagent로 로그인 오류 상태를 수정해줘
복합 작업: basic-team으로 가져오기 API와 UI를 함께 수정해줘
선택 추적: basic-team으로 작업하고 TheGame Notion Task에도 진행 상황을 남겨줘
```

역할 원본은 `agents/basic-*.md`에서 수정합니다. Claude는 플러그인의 agents를 로드합니다. Codex는 설치 스크립트가 같은 원본을 `${CODEX_HOME:-$HOME/.codex}/agents/basic_*.toml`에 생성합니다. 생성물은 직접 수정하지 않습니다. `install/reload/remove`는 관리 파일만 처리하며 동명의 사용자 파일과 수정본을 보존합니다. Codex 마켓플레이스 설치만으로 native 역할 배포가 완료되지는 않으므로 위 설치 스크립트를 사용합니다. 갱신 후 새 세션에서 실제 역할 등록을 확인합니다. `skills/*/agents/openai.yaml`은 스킬 UI 설정입니다.

모델·effort는 사용자/호스트 설정을 따릅니다. 각 도구의 native `/goal`에 최종 완료 조건을 설정할 수 있으며 이미 활성인 목표를 재사용합니다. 스킬 호출만으로 새 Goal을 만들거나, 계획 요청을 구현으로 전환하지 않습니다. Agent Teams 활성화나 중첩 작업자 계층은 필요하지 않습니다.

비단순 구현은 기본 독립 reviewer 1명이 검토합니다. 필요한 UI·연결 흐름 검증을 추가하되, 필수 결함만 수정하고 취향·인접 정리는 권고로 남깁니다. 수정 후 변경분과 영향받은 검사를 확인합니다. 기존 개별 역할 스킬 5개는 위 native 역할 호출로, `thegame-basic-team`은 `basic-team`의 선택 Notion 추적으로 대체됩니다. 옛 명령은 더 이상 제공하지 않으며 진행 중인 기존 run은 강제 이관하지 않습니다.

진행 보고는 현재 세션만 기록합니다. Office가 준비되면 기존 run을 사용하고, 명시적으로 없거나 꺼져 있으면 HTML을 선택합니다. 설정 불명/연결 장애는 성공이나 부재로 간주하지 않으며 독립 작업을 계속하면서 미동기화를 표시합니다. 재개 시 같은 run과 보고 방식을 유지합니다. Notion은 요청한 경우에만 한 Task에 체크리스트를 동기화합니다.
