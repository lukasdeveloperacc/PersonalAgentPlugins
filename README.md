# PersonalAgentPlugins

한 사람의 AI 코딩 에이전트 환경을 담아 **어느 머신에서든 복원**하는 공개 마켓플레이스다.

자주 쓰는 서드파티 플러그인을 큐레이션하고, 자작 스킬을 함께 배포한다. 새 머신에서 마켓플레이스를 여러 개 등록하는 대신 **하나만** 등록한다.

전체 제품 정의와 유지보수 기준은 [`docs/PRD.html`](docs/PRD.html)에 있다.

## 설치

```sh
# Claude Code
claude plugin marketplace add lukasdeveloperacc/PersonalAgentPlugins
claude plugin install ponytail@personal-agent-plugins

# Codex — 같은 매니페스트를 그대로 읽는다
codex plugin marketplace add https://github.com/lukasdeveloperacc/PersonalAgentPlugins.git
codex plugin add ponytail@personal-agent-plugins

# 마켓플레이스가 없는 런타임 (Hermes 등)
npx skills add lukasdeveloperacc/PersonalAgentPlugins
```

설치 전에 무엇이 들어오는지, 컨텍스트를 얼마나 쓰는지 확인할 수 있다.

```sh
claude plugin details ponytail
```

## 수록 항목

| 항목 | 종류 | 용도 |
|---|---|---|
| `andrej-karpathy-skills` | 큐레이션 | LLM 코딩의 흔한 실수를 줄이는 행동 지침 |
| `ponytail` | 큐레이션 | 가장 단순한 해법 강제. YAGNI, 표준 라이브러리 우선 |
| `authoring` | 자작 | 이 저장소를 유지보수하기 위한 규약 |

큐레이션 항목은 원본 저장소를 가리킨다. 내용을 복사하지 않으므로 원본이 갱신되면 그대로 따라간다(ref 추종). 특정 항목을 멈추려면 그 항목에 `sha`를 추가한다.

## 구조

```
.claude-plugin/marketplace.json   Claude·Codex 공용 진입점
skills/<name>/SKILL.md            자작 스킬 정본 — 모든 런타임이 이 파일을 읽는다
scripts/validate.sh               검증 게이트
```

런타임별 디렉토리를 두지 않는다. 스킬은 한 벌만 존재한다.

## 기여

스킬을 추가하거나 플러그인을 큐레이션할 때는 `authoring` 번들의 `skill-authoring` 스킬을 따른다. 요약하면,

1. `skills/<name>/SKILL.md` — frontmatter `name`은 폴더명과 같아야 한다
2. 부속 파일은 스킬 폴더 안에 둔다
3. `marketplace.json` 번들에 경로를 추가한다 — 빠뜨리면 조용히 배포에서 빠진다
4. `scripts/validate.sh`

커밋 전에 검증한다.

```sh
scripts/validate.sh            # 로컬 검사
scripts/validate.sh --online   # 큐레이션 항목의 ref를 원격에서 확인
```

## 비밀

이 저장소는 공개다. 설정 템플릿에는 값이 아니라 자리표시자(`${ENV_VAR}`)만 들어간다. 토큰·API 키·인증 파일은 어떤 형태로도 커밋하지 않으며, `validate.sh`가 이를 검사한다.

실수로 커밋했다면 히스토리 재작성보다 **즉시 키 회전**이 먼저다.
