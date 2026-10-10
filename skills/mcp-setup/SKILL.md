---
name: mcp-setup
description: lukas-plugin이 제공하는 MCP 서버(gcloud, observability, notion, glitchtip, aws-api, aws-docs, aws-eks, terraform, codegraph)를 목록으로 보여주고 켜고 끈다. 이 서버들은 기본으로 꺼져 있어서 /mcp에 보이지 않는다. 사용자가 "MCP 켜줘", "gcloud MCP 쓰고 싶어", "notion 연결해줘", "어떤 MCP 있어?", "glitchtip MCP 꺼줘", "aws mcp 활성화", "codegraph MCP 켜줘" 라고 하거나, 위 서버의 도구가 필요한데 세션에 없을 때 반드시 이 스킬을 사용한다.
---

# MCP 켜고 끄기

lukas-plugin의 MCP 서버는 기본으로 꺼져 있다. Claude Code는 플러그인 MCP를 전역으로 꺼둘 수 없어서, 서버 정의를 자동으로 로드되지 않는 카탈로그(`mcp/servers.json`)에 두고 필요한 것만 사용자 설정(user scope)에 추가한다. 그래서 `/mcp` 목록에 없는 것이 정상이고, 켜고 끄는 일은 전부 이 스킬의 `scripts/mcp.sh`가 한다.

## 스크립트 위치

이 스킬에 포함된 스크립트를 사용한다: `<이 스킬의 base directory>/scripts/mcp.sh`. 스크립트가 플러그인 루트를 계산해 `mcp/servers.json`과 공용 터널 스크립트를 참조한다.

```
mcp.sh <claude|codex> list                  # 서버별 on/off
mcp.sh <claude|codex> enable <server...>
mcp.sh <claude|codex> disable [server...]   # 이름 없이 쓰면 카탈로그 전체 끄기
```

첫 인자는 지금 실행 중인 도구다. Claude Code 안이면 `claude`, Codex 안이면 `codex`(Claude Code는 환경변수 `CLAUDECODE=1`을 설정한다). 사용자가 "둘 다"라고 하면 두 번 실행한다. 설정은 도구마다 따로 저장되기 때문이다.

## 진행 순서

1. **현재 상태 보기**: `list`를 실행해 아래 표의 설명과 함께 on/off를 보여준다. 사용자가 이미 서버 이름을 말했으면 이 단계는 짧게 끝낸다.
2. **켜기/끄기**: 사용자가 고른 서버로 `enable` 또는 `disable`을 실행한다. 모르는 이름이면 스크립트가 에러를 내니, 비슷한 카탈로그 이름을 제안한다.
3. **결과 확인**: 다시 `list`를 실행해 바뀐 것을 보여준다.
4. **사용 준비**: 아래 "켠 뒤 필요한 것"에서 해당 서버의 준비 작업을 수행한다. CodeGraph 설치 확인·프로젝트 초기화·검증은 에이전트가 직접 처리하며 사용자에게 명령 실행을 맡기거나 확인을 요청하지 않는다. 인증처럼 사용자 참여가 필요한 작업과 세션 재연결만 안내한다. MCP 도구는 세션을 시작할 때 연결되므로, 지금 세션에서 바로 쓰려면 Claude는 `/mcp`에서 다시 연결해야 하고 Codex는 새 세션을 열어야 한다.

## 서버 목록

| 서버 | 용도 |
|---|---|
| codegraph | 로컬 코드의 호출·의존 관계와 변경 영향 조회 |
| gcloud | gcloud CLI 명령 실행 (GCP 리소스 조회와 조작) |
| observability | GCP Cloud Logging, Monitoring, Trace 조회 |
| notion | Notion 공식 MCP (`mcp.notion.com`), 자체 OAuth라서 어떤 Notion 계정이든 붙을 수 있다 |
| glitchtip | GlitchTip 이슈와 이벤트 조회 (`glitchtip-issue` 스킬이 사용) |
| aws-api | AWS CLI 명령 실행 |
| aws-docs | AWS 공식 문서 검색 |
| aws-eks | EKS 클러스터 조회와 조작 (쓰기 권한 포함) |
| terraform | Terraform Registry의 provider와 module 정보 조회 (docker 필요) |

## 켠 뒤 필요한 것

- **codegraph**: 아래 "CodeGraph 자동 준비"를 수행한다. MCP는 기본 OFF이며 프로젝트 초기화는 플러그인 설치·갱신 시가 아니라 CodeGraph 활성화 시 처리한다.
- **notion**: 처음 쓸 때 Claude는 `/mcp`에서 notion을 골라 OAuth 인증을 한다. 브라우저가 다른 Notion 계정에 로그인돼 있으면 그 계정으로 붙으니, 원하는 계정으로 로그인하라고 알려준다. claude.ai Notion 커넥터는 플러그인이 막아두어서 중복되지 않는다.
- **glitchtip**: 셸에 `GLITCHTIP_MCP_TOKEN`이 export돼 있어야 한다. 켜면 `kubectl port-forward`(localhost:38088)가 자동으로 뜨고, 끊기면 다시 붙는다. 현재 kube context로 클러스터에 접근할 수 있어야 한다.
- **aws-api / aws-eks**: `AWS_PROFILE`이 필요하고, aws-eks는 `AWS_REGION`도 필요하다. Codex에서는 이 값들을 실행 환경에서 그대로 물려받는다.
- **gcloud / observability**: `gcloud auth login`과 `gcloud auth application-default login`이 되어 있어야 한다.
- **terraform**: docker가 실행 중이어야 한다.

## CodeGraph 자동 준비

CodeGraph를 켜거나, 이미 켜져 있지만 현재 프로젝트에서 아직 사용할 수 없을 때 에이전트가 다음을 직접 수행한다. 상태 조회나 끄기 요청에서는 실행하지 않는다.

1. **CLI 확인**: `command -v codegraph`로 확인하고, 없으면 `npm install -g @colbymchenry/codegraph@latest`로 설치한다. 이미 설치돼 있으면 갱신하지 않는다. 실패하면 오류 원인을 보고하고 준비 완료로 표시하지 않는다.
2. **프로젝트 확인**: 사용자가 지정한 프로젝트를 우선 사용한다. 지정하지 않았으면 현재 작업 디렉터리에서 `git rev-parse --show-toplevel`로 현재 저장소·worktree 루트를 찾고, Git 저장소가 아니면 현재 프로젝트 디렉터리를 사용한다. 스킬이나 플러그인의 설치 디렉터리를 대상으로 삼지 않는다. 대상이 불명확할 때만 프로젝트 경로를 질문한다.
3. **인덱스 준비**: 대상 프로젝트를 작업 디렉터리로 두고 `.codegraph/`가 없으면 `codegraph init --yes`를 실행한다. 기존 인덱스가 있으면 `codegraph status`의 종료 코드와 출력 경고를 함께 확인한다. 생성 엔진 버전이 오래됐거나 갱신을 권하는 경고가 있으면 같은 프로젝트에서 `codegraph sync`를 직접 실행하고 `codegraph status`를 다시 확인한다. `sync` 후에도 전체 인덱싱이 필요하다는 경고가 남으면 출력과 원인을 조사해 필요할 때 `codegraph index`를 실행하고 다시 검증한다. 경고가 없으면 불필요한 갱신은 하지 않는다. 명령 실패 시 원인을 보고하고 준비 완료로 표시하지 않으며, 기존 인덱스 디렉터리를 삭제하거나 `init`을 다시 실행하지 않는다.
4. **검증·보고**: 같은 프로젝트에서 `codegraph status`가 성공하고 엔진 버전·갱신 필요 경고가 해소됐는지 확인하며, `mcp.sh <claude|codex> list`에서 `codegraph on`인지 확인한다. MCP 도구가 현재 세션에 연결돼 있으면 해당 프로젝트의 조회도 검증한다. 연결되지 않았으면 CLI 설치, 인덱스 갱신 결과·남은 경고, MCP 등록 상태, 실제 도구 조회 검증 여부와 세션 재연결 필요를 구분해 보고한다. 종료 코드가 0이어도 갱신 필요 경고가 남으면 인덱스 준비 완료로 표시하지 않는다.

서버는 `codegraph serve --mcp`로 실행되며 클라이언트가 전달한 프로젝트 루트를 사용하고, 루트 정보가 없으면 서버의 현재 작업 디렉터리를 사용한다. 다른 저장소를 조회할 때는 도구의 `projectPath`에 준비한 프로젝트의 절대 경로를 전달한다.

## 끌 때

`disable`은 사용자 설정에서 서버를 제거한다. 저장돼 있던 OAuth 토큰도 함께 사라질 수 있으니, notion을 끄려 하면 나중에 다시 인증해야 한다고 알려준다. glitchtip은 Claude와 Codex 양쪽에서 모두 꺼졌을 때만 port-forward를 내린다.
