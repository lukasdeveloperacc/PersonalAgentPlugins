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