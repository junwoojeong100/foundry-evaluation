# 막혔을 때: 멈추고, 원인을 확인하고, 같은 기준으로 재시도

[참가자 가이드로 돌아가기](../README.md)

**명령 오류와 낮은 평가 점수부터 구분하세요.**

| 보이는 결과 | 지금 할 일 |
|---|---|
| 명령이 예외·오류로 끝남, 응답 누락·중복·실행 오류 | 다음 단계를 중단하고 아래에서 원인을 해결 |
| 평가 job은 완료됐지만 업무/native 점수가 낮음 | 점수를 고치지 않고 [실패 검토](../README.md#lab-d) 진행 |
| trace가 아직 0건이거나 일부만 보임 | 정상 운영으로 판정하지 않고 수집 지연·필터·권한 확인 |
| 녹화 화면만 봄 | 직접 실행 완료가 아니라 관찰로 기록 |

강사에게는 **실패한 명령, 오류 문구, 현재 단계, 결과 폴더 이름**을 전달합니다.
암호·토큰·`.env` 전체·개인 정보가 있는 화면을 공유 채팅이나 공개 이슈에 올리지 않습니다.

## 증상별 확인

| 증상 | 확인 / 조치 |
|---|---|
| `.env`가 없거나 필수 값 누락 | 저장소 루트에 강사가 준 파일을 둡니다. 다른 조의 이름·배포를 추측해 채우지 않습니다. |
| `preflight`의 `missing_models`가 비어 있지 않음 | 강사에게 네 지정 배포의 접근·할당량·준비 상태 확인을 요청합니다. 다른 모델로 대체하지 않습니다. |
| 로그인 안 됨 / tenant 오류 / 다른 계정 | [README 1-3](../README.md#login)에서 두 CLI에 로그인하고 `user`·`email`·`tenant`·`subscription`을 `.env`와 대조합니다. `az account set`으로 기본 구독을 바꾸지 않습니다. |
| 새 터미널에서만 로그인이 풀린 것처럼 보임 | 같은 실습 폴더에서 `export AZURE_CONFIG_DIR="$PWD/.azure-cli"`를 다시 지정합니다. 이전 터미널의 경로 설정은 새 터미널에 자동으로 전달되지 않습니다. |
| `bind` 또는 `set-prompt`에서 환경/프로젝트 오류 | 새 작업 폴더에서 `bind`를 먼저 실행했는지 확인합니다. 다른 프로젝트의 `.azure`나 소유권 파일을 복사하지 않습니다. |
| 로컬 8088 연결 실패 | 터미널 A의 ready 로그를 확인합니다. 기존 프로세스를 임의 종료하지 않습니다. 포트가 이미 사용 중이면 강사와 실습 환경을 분리합니다. |
| 모델 404 | 카탈로그 모델 ID와 실제 배포 이름을 구분합니다. `.env`와 azd가 같은 프로젝트·배포를 가리키는지 확인합니다. |
| 429 / timeout | 원인을 보존한 뒤 용량·Retry-After·출력 한도를 확인합니다. 필요하면 수집 동시성을 낮추되 전후 비교에 같은 값을 사용합니다. |
| Search 403 / 역할 부여 실패 | 사용자와 agent instance identity의 역할을 각각 확인합니다. 로컬 성공이 hosted 권한 성공은 아닙니다. 강사가 필요한 범위만 처리합니다. |
| IQ 400 / schema 오류 | 고정한 API 버전, KB schema, 보조 planner 지원을 확인합니다. 일반 Search 결과를 IQ 성공으로 대신하지 않습니다. |
| Hosted 424 / cold start | 실제 배포 상태와 해당 session 로그를 확인하고 준비 뒤 같은 버전으로 재시도합니다. |
| 시작 시 `connections/read` 거부 | 플랫폼이 주입한 telemetry 설정을 사용하는지 확인합니다. 무작정 넓은 연결 조회 권한을 주지 않습니다. |
| 평가 완료인데 오류 행이나 `null` 점수 | job 상태와 각 행을 함께 확인합니다. 오류를 0점·합격으로 변환하지 않습니다. |
| JSON 뒤의 azd 업데이트 안내 | 제공 실행기는 UTF-8 HTTP 본문과 확인된 안내만 분리합니다. 확장/SDK를 수업 중 무조건 업그레이드하지 않습니다. |
| CLI credential 시간 초과 | 실제 로그인 실패와 토큰 갱신 지연을 구분합니다. 제공 코드의 60초 제한을 무한 대기로 바꾸지 않습니다. |
| `ResourceId metadata` 평가 오류 | 강사에게 실습 전용 App Insights 연결 metadata 확인을 요청합니다. 참가자가 공유 연결을 직접 변경하지 않습니다. |
| 정리 대상이 내 이름과 다름 | 즉시 중단합니다. `.foundry` 소유권 기록을 지우거나 편집해서 삭제를 강행하지 않습니다. |

<a id="login"></a>

## 로그인 브라우저가 열리지 않는다면

[README 1-3](../README.md#login)의 **CLI 경로 지정과 tenant·구독 입력 블록을 먼저 실행한 같은 터미널**에서 아래를 사용합니다.
각 명령이 표시한 주소를 브라우저로 열고, **본인 터미널에 표시된 일회용 코드**를 입력해 `.env`의 계정으로 로그인합니다.

```bash
az login --tenant "$LOGIN_TENANT_ID" --subscription "$LOGIN_SUBSCRIPTION_ID" \
  --use-device-code --output none &&
azd auth login --tenant-id "$LOGIN_TENANT_ID" --use-device-code
```

두 명령이 끝나면 README 1-3의 **두 로그인 결과 확인** 블록으로 돌아갑니다. 코드는 채팅·문서·녹화에 공유하지 않습니다.
조직 정책이 device-code 로그인을 막으면 우회하지 말고 강사에게 승인된 로그인 환경을 요청합니다.
공식 설명: [Azure CLI 대화형 로그인](https://learn.microsoft.com/cli/azure/authenticate-azure-cli-interactively) · [CLI 설정 경로](https://learn.microsoft.com/cli/azure/azure-cli-configuration#cli-configuration-file).

## 응답 수집에 실패했다면

`collect`가 실패한 label의 `failure.json`, manifest, 원문 응답을 **그대로 보존**합니다.
해당 label에 다시 쓰거나 성공한 행만 추려서 평가하지 않습니다.

강사와 원인을 해결한 뒤 새 label로 전체 질문을 다시 수집합니다. 예를 들어 **실패한 첫 baseline을 다시 수집**할 때는:

```bash
python scripts/workshop.py collect --split dev --label baseline-retry --concurrency 2 &&
python scripts/workshop.py evaluate --label baseline-retry &&
python scripts/workshop.py compare --labels baseline-retry &&
python scripts/workshop.py monitor --label baseline-retry
```

이 경우 이후 `feedback`, `compare`, `verify --baseline`도 **같은 `baseline-retry`**를 사용합니다.
improved/holdout 수집에도 `--concurrency 2`를 유지합니다. label 일부만 바꾸면 비교 대상이 섞입니다.

이미 완료된 baseline과 회귀 검토가 있다면 baseline을 다시 만들지 말고 **실패한 단계부터** 복구합니다.
새 실험이 필요하면 강사와 새 폴더·고유 접두사를 준비합니다. 과거 결과·회귀 trace를 지워 출발점을 꾸미지 않습니다.

## Foundry 평가만 실패했다면

응답 수집이 온전히 완료됐는지 먼저 확인합니다. **아직 실행 중인 평가와 실제 실패한 평가의 복구 명령은 다릅니다.**

`Evaluation is still running`으로 로컬 대기만 끝났다면 **같은 label**로 다시 조회합니다. 기존 평가 run을 이어서 기다리며 새 run을 만들지 않습니다.

```bash
python scripts/workshop.py evaluate --label baseline
```

반면 상태가 `failed` / `canceled` / `cancelled`이거나 오류 행이 기록됐다면, 원인을 해결한 뒤 아래를 실행합니다. 실패한 시도는 보존하고 새 평가 run을 만듭니다.

```bash
python scripts/workshop.py evaluate --label baseline --retry-failed
```

`--retry-failed`는 낮은 점수를 숨기는 옵션이 아닙니다. **실행 오류를 해결한 경우에만** 사용합니다.
label이 다르면 위 예시도 실제 label로 바꿉니다.

<a id="no-failures"></a>

## Baseline이 전부 통과했다면

실패가 없다는 것도 결과입니다. 실패를 만들거나 답변·정답을 수정하지 않습니다.

1. `src/agent/.foundry/results/baseline/responses.jsonl`에서 가장 불확실한 **dev 행** 하나를 고릅니다.
2. 같은 `trace_id`의 근거와 응답을 확인하고, “전부 통과했으며 무엇을 추가로 검토했는지”를 기록합니다.
3. 제공 V2를 비교할 이유가 타당한지 강사와 판단합니다. 비교하더라도 품질 개선을 미리 주장하지 않습니다.
4. `feedback`의 실제 `row_id`와 검토 이유를 사용합니다. 이 명령은 통과한 dev 행도 검토 기록으로 남길 수 있습니다.

최종 `verify`는 **검토된 baseline trace가 후보 실행에서 재사용됐는지** 확인합니다.
holdout을 열어 실패를 찾거나 개선 재료로 사용하는 것은 금지합니다.

## 포털 화면이 영상과 다르면

- 화면의 계정·이름·버전·날짜가 아니라 **본인 값**을 확인합니다.
- 탭 이동 후 agent 버전 선택이 최신 버전으로 바뀔 수 있습니다. 실제 응답의 `prompt_version`도 대조합니다.
- 프로젝트 전역 **Evaluations**와 agent 상세의 **Evaluation**은 같은 목록이 아닙니다.
- Foundry **Indexes**가 비어 있어도 실제 Search index는 존재할 수 있습니다. **Knowledge bases의 source**와 Azure Search의 index를 따로 확인합니다.
- **Monitor → Tools**가 비어 있어도 코드 내부의 IQ 호출은 trace에 있을 수 있습니다.
- 오래된 trace는 시간 범위를 넓힌 뒤 실제 ID로 찾습니다. 임의 ID나 다른 agent의 trace를 성공 증거로 대신하지 않습니다.
- 구독 경보·정책의 ARM 오류는 모델 평가와 구분해 강사에게 확인합니다. 공유 구독 설정을 바꿔서 영상과 화면을 맞추지 않습니다.

원인별 설계 배경은 [참고 설명](reference.ko.md), 권한·모델 준비는 [강사 가이드](instructor.ko.md)를 확인합니다.
