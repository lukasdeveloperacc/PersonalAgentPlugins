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

## Basic Team

Codex는 `$basic-team <작업>`, Claude는 `/lukas-plugin:basic-team <작업>`으로 호출합니다. 플러그인 reload 후 새 세션에서 사용할 수 있습니다.

- Planner: `ralplan` 기반 계획, 미설치 시 `plan` 사용. Frontend/Backend 필요 여부와 작업·파일·담당자·연결 규약을 명시
- Executor: Frontend/Backend 담당을 구분한 네이티브 에이전트로 구현. 공용 파일·통합 작업은 단일 담당자를 지정
- Karpathy Agent와 Ponytail Senior Agent: 독립 리뷰 후 둘 다 같은 최종 구현에 `PASS`할 때까지 수정·재검토
- Main Session: `eli5`로 진행 상황·결정 사항을 HTML 그림과 짧은 설명으로 브리핑

역할별 모델·추론 수준은 [basic-team 스킬](skills/basic-team/SKILL.md)에 지정되어 있습니다. 정확한 설정을 선택할 수 없는 환경에서는 대체 모델로 진행하지 않고 제한을 보고합니다. Claude는 2.1.293 이상과 OMC `team`의 네이티브 팀 기능이 필요합니다. Codex는 네이티브 협업 도구를, Claude는 OMC `team`의 네이티브 팀·메시지·종료 절차를 사용합니다. Planner는 ralplan의 계획·검토 방법을 적용하며 별도 OMX/OMC 실행 런타임은 시작하지 않습니다.
