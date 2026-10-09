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
  - Node.js 20 이상과 npm 필요. npm 전역 설치 경로가 `PATH`에 있어야 합니다.
  - Claude: OMC 플러그인을 의존성으로 설치하고, `omc`가 없으면 공식 npm 패키지 설치 후 `omc setup --quiet` 실행
  - Codex: `omx`가 없으면 공식 npm 패키지 설치 후 사용자 범위의 plugin 모드로 setup. 사용자 `AGENTS.md`가 있으면 병합하고, 없으면 생성
  - 설치 후 새 세션에서 `omc` 또는 `omx`로 harness 실행 가능
  - Claude/Codex의 마켓플레이스 명령으로 플러그인만 설치하면 npm 설치·setup은 실행되지 않으므로 위 스크립트를 사용해야 합니다.
- `remove` : plugin 제거
  - 별도로 사용할 수 있는 OMC/OMX npm 패키지와 사용자 설정·실행 기록은 보존
  - 이미 없는 플러그인은 건너뛰며, 다른 도구에서 사용 중인 GlitchTip 터널은 유지
- `reload` : plugin 업데이트
  - 업데이트 후 codex, claude 세션 모두 재실행 필요
  - `eli5` 의존성도 각 마켓플레이스에서 갱신 후 재설치
  - OMC/OMX setup도 다시 실행. 이미 있는 CLI는 자동 업그레이드하지 않음

Harness setup은 사용자 전역 설정을 갱신합니다. OMC는 `~/.claude/CLAUDE.md`의 사용자 내용을 병합하고, OMX는 사용자 범위의 `AGENTS.md`를 병합하며 프로젝트의 `AGENTS.md`는 변경하지 않습니다. OMC 업데이트는 `omc update`, OMX 업데이트는 `omx update`로 관리합니다.
