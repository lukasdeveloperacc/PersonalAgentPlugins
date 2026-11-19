# GlitchTip MCP와 Loki 포트포워딩 복구

조사에 필요한 조회가 실패하면 해당 서비스만 복구하고 같은 조회를 다시 실행한다. 로컬 주소의 연결 거절·타임아웃은 터널을 확인할 신호다. HTTP 401/403은 인증·권한을, 정상 응답에 결과가 0건이면 검색 조건을 확인한다.

## EKS 연결에서 AWS SSO 세션 만료가 보고될 때

- 대상 kubeconfig의 exec 설정과 실행 환경에서 사용하는 AWS 프로필을 확인한다. 아래 `$profile`에는 그 프로필을 사용한다. `aws sts get-caller-identity --profile "$profile"`로 확인해 대상 계정·역할이면 중단된 Kubernetes 조회를 재시도한다. 같은 사용자 홈과 SSO 세션을 쓰는 다른 터미널의 유효한 로그인 캐시도 재사용된다.
- SSO 로그인이 필요하면 `aws sso login --profile "$profile"`을 실행해 브라우저 인증을 시작한다. 브라우저가 없는 터미널에서는 `aws sso login --profile "$profile" --use-device-code --no-browser`를 실행하고, 현재 사용자와의 비공개 대화에서 CLI가 표시한 인증 주소와 일회용 코드를 전달해 휴대폰 브라우저로 승인해 달라고 요청한다. 승인 또는 코드 만료까지 로그인 프로세스를 유지한다. 사용자에게 필요한 작업은 브라우저 로그인·승인이며, 조직에서 요구하면 MFA도 완료한다. 기기 코드는 회사 Issue 스레드나 조사 보고서에 남기지 않는다. [AWS CLI 인증 안내](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sso.html)
- CLI가 로그인 성공을 반환하면 같은 프로필의 STS 신원, 실패했던 Kubernetes 요청, 포트포워딩을 통한 원래 조회 순으로 재확인한다. STS 신원이 맞는데 Kubernetes가 `Forbidden`을 반환하면 해당 namespace의 Service 조회나 `pods/portforward` 권한을 확인한다. 로그인을 반복하지 않는다.

## GlitchTip MCP

1. 현재 호스트의 MCP 설정에서 GlitchTip 등록 여부와 URL을 확인한다. 이 플러그인의 기본 주소는 `http://localhost:38088/mcp`다. 사용자 지정 주소는 해당 환경의 연결 지침을 따른다.
2. 기본 주소로 등록돼 있고 로컬 연결이 끊겼으면 `kubectl config current-context`가 사건 대상 클러스터인지 확인한다. 일치하면 **설치된 플러그인 루트**의 [scripts/glitchtip-forward.sh](../../../scripts/glitchtip-forward.sh)를 `start` 인자로 실행한다. 기존 감독 프로세스가 있으면 그 프로세스가 재연결을 맡는다.
3. 준비 시간을 짧게 두고 대상 이슈의 `get_issue`를 다시 호출한다. 세션 시작 시 연결에 실패해 도구가 목록에서 빠졌다면 호스트가 지원하는 MCP 재연결 후 도구를 다시 찾는다. 복구 여부는 실제 MCP 조회 결과로 판단한다.
4. 계속 실패하면 `${XDG_STATE_HOME:-$HOME/.local/state}/lukas-plugin/glitchtip-forward.log`의 최근 오류에서 포트 충돌, Kubernetes 접근 거부, Service·pod 부재를 확인한다. 다른 프로세스가 포트를 사용 중이면 보존한다. MCP가 미등록이거나 복구가 막히면 제공된 이벤트 JSON 또는 로그인된 GlitchTip UI에서 대상 이벤트를 읽는다. 원본을 확보할 수 없을 때만 사용자에게 요청한다.

## Loki

1. 설정된 Loki 주소로 사건 시간대의 label 조회를 시도한다. 정상 응답이면 기존 연결을 쓴다. 로컬 포워딩이 필요하면 저장소 배포 설정 또는 대상 클러스터의 Service 목록에서 **로그 조회를 받는 Service**, namespace, Service port를 확인한다. 예를 들어 gateway 또는 read Service가 될 수 있다. 클러스터와 테넌트는 사건 환경에 맞춘다.
2. 확인한 값으로 아래 명령을 별도 터미널 세션에서 실행한다. 로컬 포트를 자동 배정하므로 기존 포워딩과 충돌하지 않는다. `Forwarding from 127.0.0.1:<포트>`가 출력되면 그 포트를 이번 조회 주소로 사용한다.

   ```sh
   kubectl --context "$ctx" -n "$ns" port-forward --address 127.0.0.1 "svc/$svc" ":$service_port"
   ```

3. `logcli --addr="http://127.0.0.1:<포트>"`로 같은 조회를 다시 실행한다. CLI가 없으면 같은 주소의 `/loki/api/v1/labels`로 Loki 성공 응답을 확인한 뒤 `/loki/api/v1/query_range`로 사건 로그를 조회한다. 게이트웨이의 인증·테넌트 설정은 기존 조회 환경을 따른다.
4. 조사 중 터널이 끊기면 포워딩 세션의 오류를 확인한다. pod 교체처럼 일시적인 원인이면 같은 Service로 다시 열고 새 로컬 주소에서 중단된 조회를 재시도한다. 권한·대상 오류가 지속되면 막힌 지점을 기록하고 확보한 증거로 진행한다. 조사 종료 시 이번 조사에서 직접 연 임시 포워딩 세션만 종료한다.
