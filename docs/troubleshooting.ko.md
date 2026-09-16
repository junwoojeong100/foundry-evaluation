# 막혔을 때: 멈추고, 원인을 확인하고, 같은 기준으로 재시도

[참가자 가이드로 돌아가기](../README.ko.md) · [English](troubleshooting.en.md)

**명령 오류와 낮은 평가 점수부터 구분하세요.**

| 보이는 결과 | 지금 할 일 |
|---|---|
| 명령이 예외·오류로 끝남, 응답 누락·중복·실행 오류 | 다음 단계를 중단하고 아래에서 원인을 해결 |
| `collect`가 `business=False`를 출력함 | 업무 검사 미통과 표시이지 실행 오류가 아님. 수집이 오류 없이 끝나면 해당 단계의 평가로 진행 |
| 평가 job은 완료됐지만 업무/native 점수가 낮음 | 점수는 그대로 기록하고 해당 단계의 완료·포털 확인을 마침. `baseline`은 [6단계 검토](../README.ko.md#lab-d), `improved`는 [7-4 비교](../README.ko.md#compare-results), `holdout`은 [9단계 검증](../README.ko.md#lab-g)으로 진행 |
| trace가 아직 0건이거나 일부만 보임 | 정상 운영으로 판정하지 않고 수집 지연·필터·권한 확인 |
| 녹화 화면만 봄 | 직접 실행 완료가 아니라 관찰로 기록 |

강사에게는 **실패한 명령, 오류 문구, 현재 단계, 결과 폴더 이름**을 전달합니다.
암호·토큰·`.env` 전체·개인 정보가 있는 화면을 공유 채팅이나 공개 이슈에 올리지 않습니다.

<a id="resume"></a>

## 실패한 명령부터 이어가기

**코드 블록 전체를 반복하지 않습니다.** 예를 들어 `collect`는 성공했고 `evaluate`만 멈췄다면 `collect`부터 다시 실행하면 안 됩니다.
아래에서 멈춘 위치를 고르고, 같은 결과 폴더와 label을 유지합니다.

| 멈춘 위치 / 메시지 | 이어갈 곳 |
|---|---|
| `collect` 중 오류, `manifest.json`의 `status: failed` | [응답 수집 복구](#collection-retry). 실패한 결과는 보존하고 새 label로 전체 수집 |
| `Evaluation is still running` | [평가 복구](#evaluation-retry). 같은 label의 `evaluate`만 다시 실행 |
| Foundry run이 failed/canceled이거나 오류 행이 있음 | 원인을 해결한 뒤 [평가 복구](#evaluation-retry)의 `--retry-failed` 사용 |
| `Telemetry is incomplete` | 수집 지연·권한과 [기본 2시간 조회 범위](#telemetry)를 확인한 뒤 같은 label의 `monitor`만 재실행 |
| `Label ... already exists` | 기존 `manifest.json`을 읽기만 해서 상태 확인. `completed`면 평가 단계부터, `failed`면 수집 복구. `running`이면 기존 실행의 진행·중단 여부를 강사와 확인 |
| `feedback`에서 이미 같은 회귀 기록이 존재 | 기존 행 ID·검토 이유·출처가 이번에 검토한 내용과 일치할 때만 다음 단계 진행. 다르면 중단하고 확인하며 파일을 지워 우회하지 않음 |

**터미널을 다시 열었나요?** 새 clone이 아니라 **기존 실습 폴더**를 열고 [터미널 복원 블록](../README.ko.md#resume-shell)을 따릅니다. 빈 터미널이라는 이유로 `init`·`bind`·배포·수집을 반복하지 않습니다.

**`src/agent/.foundry/results/<label>/`**의 `manifest.json`은 **수집 상태만** 나타냅니다. 평가는 `evaluation.json`, trace 수집은 `telemetry.json`을 확인합니다. 수집 완료가 평가 완료를 뜻하지는 않습니다.

다른 실습이나 언어를 시작할 때만 미사용 이름을 받아 새 폴더를 사용합니다. 소유권·응답·trace를 지워 오류를 우회하지 않습니다. 응답 수집이 아니라 Azure 환경을 만들다가 중단했다면 [환경 준비 복구](#setup-resume)를 따릅니다.

## 증상별 확인

| 증상 | 확인 / 조치 |
|---|---|
| `.env`가 없거나 필수 값 누락 | 저장소 루트에 강사가 준 파일을 둡니다. 다른 조의 이름·배포를 추측해 채우지 않습니다. |
| 언어가 다르거나 language mismatch | 한국어는 `LAB_LANGUAGE=ko`, 영어는 `en`인 별도 작업 폴더를 사용합니다. 기존 실행의 언어·소유권·결과를 바꾸어 표시하지 않습니다. |
| `read: -p: no coprocess` 또는 경로/activate 파일 오류 | 먼저 `bash`를 실행했는지, 터미널 A의 `pwd` 경로로 이동했는지 확인합니다. 로그인 파일이 없다고 다른 계정으로 바꾸지 않습니다. |
| `preflight`의 `missing_models`가 비어 있지 않음 | 강사에게 네 지정 배포의 접근·할당량·준비 상태 확인을 요청합니다. 다른 모델로 대체하지 않습니다. |
| 로그인 안 됨 / tenant 오류 / 다른 계정 | [README 1-3](../README.ko.md#login)에서 두 CLI에 로그인하고 `user`·`email`·`tenant`·`subscription`을 `.env`와 대조합니다. `az account set`으로 기본 구독을 바꾸지 않습니다. |
| 새 터미널에서만 로그인이 풀린 것처럼 보임 | 같은 실습 폴더에서 `export AZURE_CONFIG_DIR="$PWD/.azure-cli"`를 다시 지정합니다. 이전 터미널의 경로 설정은 새 터미널에 자동으로 전달되지 않습니다. |
| `bind` 또는 `set-prompt`에서 환경/프로젝트 오류 | 새 작업 폴더에서 `bind`를 먼저 실행했는지 확인합니다. 다른 프로젝트의 `.azure`나 소유권 파일을 복사하지 않습니다. |
| 로컬 8088 연결 실패 | 터미널 A의 ready 로그를 확인합니다. 기존 프로세스를 임의 종료하지 않습니다. 포트가 이미 사용 중이면 강사와 실습 환경을 분리합니다. |
| `prepare-iq`에서 역할 부여 거부 | Search identity의 planner 접근 권한을 환경 소유자에게 요청합니다. 소유권 검사를 우회하거나 agent에 Owner 권한을 주지 않습니다. |
| 모델 404 | 카탈로그 모델 ID와 실제 배포 이름을 구분합니다. `.env`와 azd가 같은 프로젝트·배포를 가리키는지 확인합니다. |
| 429 / timeout | 원인을 보존한 뒤 용량·Retry-After·출력 한도를 확인합니다. 필요하면 수집 동시성을 낮추되 전후 비교에 같은 값을 사용합니다. |
| Search 403 / 역할 부여 실패 | 사용자와 agent instance identity의 역할을 각각 확인합니다. 로컬 성공이 hosted 권한 성공은 아닙니다. 강사가 필요한 범위만 처리합니다. |
| IQ 400 / schema 오류 | 고정한 API 버전, KB schema, 보조 planner 지원을 확인합니다. 일반 Search 결과를 IQ 성공으로 대신하지 않습니다. |
| Hosted 424 / cold start | 실제 배포 상태와 해당 session 로그를 확인하고 준비 뒤 같은 버전으로 재시도합니다. |
| 시작 시 `connections/read` 거부 | 플랫폼이 주입한 telemetry 설정을 사용하는지 확인합니다. 무작정 넓은 연결 조회 권한을 주지 않습니다. |
| 평가 완료인데 오류 행이나 `null` 점수 | job 상태와 각 행을 함께 확인합니다. 오류를 0점·합격으로 변환하지 않습니다. |
| `verify`는 성공했는데 `candidate_quality_gates`에 `false`가 있음 | 유효한 실행의 품질 미통과 결과입니다. [완료 후 판단](../README.ko.md#completion-decision)에 따라 그대로 보고하고 정리하며, 점수를 높이려고 재실행하지 않습니다. |
| `production_release_approved: false` | 업무 gate를 통과해도 정상입니다. 권한 오류나 편집할 값이 아닙니다. [세 결과의 다음 행동](../README.ko.md#completion-decision)을 확인합니다. |
| JSON 뒤의 azd 업데이트 안내 | 제공 실행기는 UTF-8 HTTP 본문과 확인된 안내만 분리합니다. 확장/SDK를 수업 중 무조건 업그레이드하지 않습니다. |
| CLI credential 시간 초과 | 실제 로그인 실패와 토큰 갱신 지연을 구분합니다. 제공 코드의 60초 제한을 무한 대기로 바꾸지 않습니다. |
| `ResourceId metadata` 평가 오류 | 강사에게 실습 전용 App Insights 연결 metadata 확인을 요청합니다. 참가자가 공유 연결을 직접 변경하지 않습니다. |
| 정리 대상이 내 이름과 다름 | 즉시 중단합니다. `.foundry` 소유권 기록을 지우거나 편집해서 삭제를 강행하지 않습니다. |

<a id="login"></a>

## 로그인 브라우저가 열리지 않는다면

[README 1-3](../README.ko.md#login)의 **CLI 경로 지정과 tenant·구독 입력 블록을 먼저 실행한 같은 터미널**에서 아래를 사용합니다.
각 명령이 표시한 주소를 브라우저로 열고, **본인 터미널에 표시된 일회용 코드**를 입력해 `.env`의 계정으로 로그인합니다.

```bash
az login --tenant "$LOGIN_TENANT_ID" --subscription "$LOGIN_SUBSCRIPTION_ID" \
  --use-device-code --output none &&
azd auth login --tenant-id "$LOGIN_TENANT_ID" --use-device-code
```

두 명령이 끝나면 README 1-3의 [두 로그인 결과 확인](../README.ko.md#login-check) 블록으로 돌아갑니다. 로그인 명령을 다시 실행할 필요는 없습니다. 코드는 채팅·문서·녹화에 공유하지 않습니다.
조직 정책이 device-code 로그인을 막으면 우회하지 말고 강사에게 승인된 로그인 환경을 요청합니다.
공식 설명: [Azure CLI 대화형 로그인](https://learn.microsoft.com/cli/azure/authenticate-azure-cli-interactively) · [CLI 설정 경로](https://learn.microsoft.com/cli/azure/azure-cli-configuration#cli-configuration-file).

<a id="calibration"></a>

## Judge calibration이 통과하지 않는다면

평가가 **아직 실행 중**이면 아래 명령만 반복합니다.

```bash
python scripts/workshop.py calibrate
```

Native job이 실패·취소됐거나 오류 행이 있다면 원인을 먼저 해결한 뒤, 실패 job을 보존하고 재시도합니다.

```bash
python scripts/workshop.py calibrate --retry-failed
```

Job은 완료됐지만 judge가 제공된 근거 있는 금액과 근거 없는 금액을 **구분하지 못했다면** 중단하고 환경 소유자와 judge·설정을 검토합니다. 예제·threshold를 바꾸거나 정상적으로 나온 낮은 점수를 통과할 때까지 반복하지 않습니다. Calibration은 agent의 본평가 64응답과 별개입니다.

<a id="telemetry"></a>

## 쉬었다가 이어 하니 trace가 없다면

포털이 Last Day를 보여도 `monitor`의 기본 조회는 **최근 2시간**입니다. 최근 24시간 안의 실행이라면 **같은 label**을 유지하고 기간만 늘립니다.

```bash
python scripts/workshop.py monitor --label baseline --hours 24
```

실패한 모니터링이 다른 단계라면 `baseline`을 실제 `improved` 또는 `holdout`으로 바꿉니다. `--hours`는 **1–168 사이 정수 시간**이며 원래 수집 시점을 포함하도록 선택합니다. 이미 보존 기간이 끝났거나 삭제된 telemetry를 되살리는 옵션은 아닙니다.

Agent와 run 필터는 그대로이며 trace 누락·중복·다른 trace·sampling은 여전히 검사에서 실패합니다. 방금 실행했다면 반영을 기다린 뒤 이 명령만 반복합니다. 계속 누락되면 환경 소유자와 권한·보존 기간·연결된 App Insights를 확인합니다. 응답을 다시 수집하거나 `telemetry.json`을 편집해 완료 상태를 만들지 않습니다.

복구 후 중단했던 완료 확인으로 돌아갑니다. 이미 cleanup까지 했다면 저장된 증거를 읽습니다. 새 실험은 새 폴더·이름으로 시작합니다.

<a id="collection-retry"></a>

## 응답 수집에 실패했다면

`collect`가 실패한 label의 `failure.json`, manifest, 원문 응답을 **그대로 보존**합니다.
해당 label에 다시 쓰거나 성공한 행만 추려서 평가하지 않습니다.

**실패한 단계만 복구합니다.** 해당 단계의 모델·정책·질문·지침·agent 버전은 유지합니다. 원인을 해결한 뒤 새 label로 그 단계의 전체 질문을 다시 수집합니다.

| 실패한 단계 | 아래 예시의 새 label | 이후 적용할 곳 |
|---|---|---|
| 첫 V1 baseline | `baseline-retry` | Feedback과 `verify --baseline baseline-retry` |
| V2 dev 후보 | `improved-retry` | 비교와 `verify --candidate improved-retry` |
| 고정 V2 holdout | `holdout-retry` | 비교와 `verify --holdout holdout-retry` |

**새 label**로 평가·monitor를 실행하고, 이후 명령 **및 파일 경로**에도 적용합니다. 예시의 재시도 label이 이미 있다면 다른 미사용 label로 모두 바꿉니다. 다른 완료된 label과 검토 출처는 유지합니다.

**완료된 비교가 없는 첫 baseline 실패:** 원인 해결을 위해 동시성을 2로 낮추는 경우의 예시입니다.

```bash
python scripts/workshop.py collect --split dev --label baseline-retry --concurrency 2 &&
python scripts/workshop.py evaluate --label baseline-retry &&
python scripts/workshop.py compare --labels baseline-retry &&
python scripts/workshop.py monitor --label baseline-retry
```

이 경우 이후 `feedback`, `compare`, `verify --baseline`도 **같은 `baseline-retry`**를 사용합니다.
improved/holdout 수집에도 `--concurrency 2`를 유지합니다. label 일부만 바꾸면 비교 대상이 섞입니다.
위 네 명령이 모두 끝나면 **새 평가의 report URL로 5단계 포털 확인**을 마치고 [6-2 사례 선택](../README.ko.md#review-case)부터 이 label로 이어갑니다. 완료한 수집·평가·monitor는 반복하지 않습니다.

**Baseline 완료 후 V2 dev나 holdout 실패:** baseline의 `manifest.json`에 기록된 `concurrency`를 유지합니다. 아래는 **4**인 경우이며, 다르면 실제 값으로 바꿉니다. 실패한 단계의 명령 **하나만** 선택합니다.

```bash
python scripts/workshop.py collect --split dev --label improved-retry --concurrency 4
```

```bash
python scripts/workshop.py collect --split holdout --label holdout-retry --concurrency 4
```

V2 dev가 **24/24**로 끝나면 바로 [7단계 평가·비교](../README.ko.md#candidate-evaluation)부터 `improved`를 `improved-retry`로 바꾸어 이어갑니다. Holdout이 **16/16**으로 끝나면 바로 [8단계 평가](../README.ko.md#holdout-evaluation)부터 `holdout`을 `holdout-retry`로 바꾸어 이어갑니다. 해당 단계 처음의 배포·수집은 반복하지 않습니다.

재배포하거나, holdout을 보고 지침을 바꾸거나, 완료된 baseline과 회귀 검토를 다시 만들지 않습니다. Holdout 실행 오류를 복구한 결과는 **새 미사용 검증셋이 아닙니다.** Baseline 완료 후 동시성까지 바꿔야 한다면 별도로 통제한 새 실험을 시작하며 원래 증거는 지우지 않습니다.

<a id="evaluation-retry"></a>

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
복구를 마치면 중단했던 README 단계의 **완료 확인**을 마친 뒤 다음 단계로 진행합니다.

<a id="no-failures"></a>

## Baseline이 전부 통과했다면

실패가 없다는 것도 결과입니다. 실패를 만들거나 답변·정답을 수정하지 않습니다.

1. `src/agent/.foundry/results/baseline/responses.jsonl`에서 검토할 **dev 응답 하나**를 고릅니다. `row_id`·`case_id`·`model_key`·`trace_id`를 적어 둡니다.
2. [README 6-2의 2–4번](../README.ko.md#review-case)처럼 같은 응답·고정 dev 기준·trace를 대조합니다.
3. “업무 검사는 전부 통과했고 무엇을 추가로 검토했는지”와 제공 V2를 비교할 이유를 설명합니다. 실패나 품질 개선을 미리 주장하지 않습니다.
4. [6-3 검토 기록 저장](../README.ko.md#save-review)으로 돌아갑니다. `feedback`은 통과한 dev 응답도 기록할 수 있습니다. 저장 후 7단계에서 V2의 타당성을 검토합니다.

최종 `verify`는 **검토된 baseline trace가 후보 실행에서 재사용됐는지** 확인합니다.
holdout을 열어 실패를 찾거나 개선 재료로 사용하는 것은 금지합니다.

## 포털 화면이 영상과 다르면

- 화면의 계정·이름·버전·날짜가 아니라 **본인 값**을 확인합니다.
- 탭 이동 후 agent 버전 선택이 최신 버전으로 바뀔 수 있습니다. 실제 응답의 `prompt_version`도 대조합니다.
- 프로젝트 전역 **Evaluations**와 agent 상세의 **Evaluation**은 같은 목록이 아닙니다.
- 버전 비교는 agent의 More가 아니라 **Version 선택 상자 → Compare versions**에서 엽니다. 서로 다른 두 버전을 고르고 Send는 한 번만 누릅니다. 양쪽이 함께 호출됩니다.
- Foundry **Indexes**가 비어 있어도 실제 Search index는 존재할 수 있습니다. **Knowledge bases의 source**와 Azure Search의 index를 따로 확인합니다.
- **Monitor → Tools**가 비어 있어도 코드 내부의 IQ 호출은 trace에 있을 수 있습니다.
- 오래된 trace는 시간 범위를 넓힌 뒤 실제 ID로 찾습니다. 임의 ID나 다른 agent의 trace를 성공 증거로 대신하지 않습니다.
- 구독 경보·정책의 ARM 오류는 모델 평가와 구분해 강사에게 확인합니다. 공유 구독 설정을 바꿔서 영상과 화면을 맞추지 않습니다.

원인별 설계 배경은 [참고 설명](reference.ko.md), 권한·모델 준비는 [강사 가이드](instructor.ko.md)를 확인합니다.

<a id="setup-resume"></a>

## 환경 소유자: 터미널을 닫은 뒤 준비 이어가기

[환경 준비 1단계](environment.ko.md)에서 소스 스냅샷과 Python 환경을 완성한 경우에만 사용합니다. 새 `RUN_ID`를 만들거나 `init` / `prepare`를 반복하지 않습니다.

`bash`를 실행한 뒤, **원래 clone 경로**와 **준비 중 출력된 기존 `RUN_DIR` 경로**를 따옴표 없이 입력합니다.

```bash
read -r -p "원래 환경 준비 clone의 절대 경로: " REPO_ROOT &&
cd "$REPO_ROOT" &&
read -r -p "기존 RUN_DIR의 절대 경로: " RUN_DIR &&
ls "$RUN_DIR/config.json" "$RUN_DIR/source-manifest.json" &&
cd "$RUN_DIR/workshop" &&
source src/agent/.venv/bin/activate &&
export AZURE_CONFIG_DIR="$PWD/.azure-cli"
```

**완료 확인:** 두 기록 파일이 있고, 가상환경이 활성화되며, CLI 프로필은 기존 실행 폴더를 가리킵니다. 파일이 없으면 중단하고 환경 소유자와 미완성 상태를 확인합니다. Manifest를 임의로 만들어 채우지 않습니다.

| 중단한 준비 단계 | 이어갈 위치 |
|---|---|
| 로그인 | 지금 폴더에서 [README 1-3](../README.ko.md#login)을 수행한 뒤 환경 준비 2단계로 복귀 |
| 환경 준비 2–5단계의 서비스 생성 | `cd "$REPO_ROOT"`로 이동. `AZURE_CONFIG_DIR`는 유지하고 같은 `--run-dir "$RUN_DIR"`로 실패한 명령만 실행 |
| 환경 준비 6단계의 후보 모델 준비 | 지금 `"$RUN_DIR/workshop"` 폴더에서 실패한 명령부터 재개 |
| 환경 준비는 이미 완료됨 | [개인 실습 또는 수업 전달 경로](environment.ko.md#handoff)를 선택. 준비를 반복하지 않음 |

로그인이 만료됐다면 설정된 계정으로 복구합니다. 다른 계정·새 자원 이름·소유권 기록 삭제로 오류를 우회하지 않습니다.
