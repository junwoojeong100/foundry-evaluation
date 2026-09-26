# 중단한 실습 이어가기: 완료한 작업은 반복하지 않습니다

[참가자 가이드로 돌아가기](../README.ko.md) · [English](troubleshooting.en.md)

**오류 없이 쉬었다면 [다음 미실행 블록부터 재개](#resume)합니다. 오류가 났다면 현재 폴더와 오류 출력을 보존하고 아래에서 고릅니다.**
- **실패 단계:** [오프라인 테스트](#offline-tests) · [로그인](#login) · [검색](#retrieval) · [로컬 실행](#symptom-local) · [배포](#deployment-recovery) · [Hosted Agent](#symptom-hosted) · [calibration](#calibration) · [수집](#collection-retry) · [평가](#evaluation-retry) · [검토 기록](#review-recovery) · [V2 변경](#v2-changed) · [정리](#cleanup-recovery).
- **증거·선택 단계:** [baseline 전부 통과](#no-failures) · [trace](#telemetry) · [포털](#portal-differs) · [완료 판단](#symptom-completion) · [레벨 2·3](#levels).
- **확실하지 않으면:** [증상별 확인](#symptoms)을 먼저 봅니다. label이나 상태 파일이 있으면 [저장 상태로 이어가기](#resume), 환경 준비 실패라면 [환경 소유자 이어가기](#setup-resume)를 봅니다(환경 소유자만).
- 참가자 복구 명령은 기존 실습 폴더의 저장소 루트에서 실행합니다. 환경 소유자 복구는 실행 폴더를 따로 안내합니다.
- 가상환경을 이미 만든 경우 [README 터미널 복원](../README.ko.md#resume-shell)으로 가상환경과 `AZURE_CONFIG_DIR`를 복원합니다.

**명령 오류와 낮은 평가 점수부터 구분하세요.**

| 보이는 결과 | 지금 할 일 |
|---|---|
| 명령이 예외·오류로 끝남, 응답 누락·중복, 또는 평가기 오류 | 다음 단계를 중단하고 [실패한 명령부터 복구](#resume) |
| `collect`가 `business=False`를 출력함 | 업무 검사 실패이지 명령 실패가 아닙니다. 수집이 오류 없이 끝났다면 해당 평가로 진행합니다. |
| 평가 run은 완료됐고 행 오류는 없지만 유효 점수가 낮음 | 기록하고, 완료된 `evaluate`는 반복하지 않습니다. 다음 미실행 작업으로 갑니다: `baseline` [5-4 보고서 확인](../README.ko.md#baseline-report), `improved` [7-3 비교 저장](../README.ko.md#candidate-comparison), `holdout` [8-2 비교 저장·V2 고정 확인](../README.ko.md#holdout-comparison). 이미 마친 블록은 건너뜁니다. |
| trace가 아직 0건이거나 일부만 보임 | [수집 지연·조회 기간·권한 확인](#telemetry). 전체 증거가 확인됐다고 판정하지 않습니다. |
| 녹화 화면만 봄 | 직접 실행 완료가 아니라 관찰로 기록합니다. |

이 문서의 “강사”·“환경 소유자”는 수업에서는 강사, **혼자 실습하면 본인**입니다. 본인이라면 그 행의 확인을 직접 하고, 해결되지 않으면 멈춘 상태와 오류를 기록합니다. 도움을 요청할 때는 실패한 명령, 오류, 단계, 결과 폴더 이름만 전달하며 암호·토큰·`.env` 전체·개인 정보 화면은 공유하지 않습니다.

<a id="resume"></a>

## 멈춘 지점부터 이어가기

**먼저 진행 중인 작업이 없는지 확인합니다.** 원래 터미널·작업이 아직 실행 중이면 기다리며 두 번째 명령을 시작하지 않습니다.

| 중단한 상태 | 지금 할 일 |
|---|---|
| 가상환경이 있고, 오류 없이 쉬었으며 마지막 완료 블록을 메모함 | 기존 폴더에서 [터미널 복원](../README.ko.md#resume-shell) 후 메모한 **다음 블록**부터 진행. 예: 2-3 완료 → 3-1 시작. 완료한 배포·수집·평가를 반복하지 않음 |
| 가상환경 생성 전(1-2 이전)에 중단함 | Bash에서 기존 폴더로 돌아와 마지막 완료 블록의 다음 작업을 진행. `source .../activate`는 아직 실행하지 않음. 1-1을 마쳤다면 [1-2](../README.ko.md#python-setup)로 이동 |
| 오류가 있었거나 완료 여부를 모름 | 아래 실패 단계 표와 저장 상태로 확인. 포털 확인·사람의 검토 완료는 파일 존재만으로 판단하지 않음 |

**오류 복구에서는 코드 블록 전체가 아니라 실패한 명령만 반복합니다.** 예를 들어 `collect`는 성공했고 `evaluate`만 멈췄다면 `collect`부터 다시 실행하지 않습니다. 수집을 새로 해야 할 때만 새 label을 쓰며, 평가·trace 복구는 기존 label을 유지합니다.

| 멈춘 위치 / 메시지 | 이어갈 곳 |
|---|---|
| `azd deploy` 자체 실패 또는 배포 성공 여부 불명확 | [배포 상태 확인](#deployment-recovery). 준비 중인 버전이나 이전 버전을 새 성공으로 간주하지 않음 |
| 배포는 성공했지만 뒤의 `grant-agent-access` 또는 `smoke` 실패 | 원인을 해결하고 **실패한 명령만** 재실행. 재배포해 에이전트 버전을 하나 더 만들지 않음 |
| `collect` 중 오류, `manifest.json`의 `status: failed` | [응답 수집 복구](#collection-retry). 실패한 결과는 보존하고 새 label로 전체 수집 |
| `Evaluation is still running` | [평가 복구](#evaluation-retry). 같은 label의 `evaluate`만 다시 실행 |
| Foundry 평가 실패 또는 결과 검증·다운로드 중단 | [저장 상태별 복구 표](#evaluation-retry)에서 선택. 모든 로컬 오류에 `--retry-failed`를 쓸 수 있는 것은 아님 |
| `Telemetry is incomplete` | 수집 지연·권한과 [기본 2시간 조회 범위](#telemetry)를 확인한 뒤 같은 label의 `monitor`만 재실행 |
| `Hosted prompt does not match`(holdout 수집) 또는 8-2에서 improved·holdout 버전 불일치 | [7-2 뒤 V2가 바뀌었다면](#v2-changed). 결과를 지우거나 고치지 않음 |
| `Label ... already exists` | 상태 파일을 확인합니다. `completed`면 다음 미완료 평가·trace 단계로 갑니다. `failed`면 수집을 복구합니다. `running`이면 원래 프로세스가 실행 중인지 확인하고, 종료 확인 뒤에만 수집을 복구합니다. |
| `feedback`에서 이미 같은 회귀 기록이 존재하거나 다른 행을 저장함 | [검토 기록 확인](#review-recovery). 행 ID·검토 이유·언어·출처 trace가 실제 검토와 일치할 때만 진행. 다른 행 추가 저장은 오저장을 제외하지 않음 |
| 정리 또는 정리 확인 중단 | [정리 복구](#cleanup-recovery). 확인 실패를 해결하려고 성공한 삭제를 반복하지 않음 |
| 레벨 2·3 명령 중단 | [레벨 2·3 복구](#levels). 5–9단계 결과는 바뀌지 않음 |

**저장 파일로 확인할 때:** 아래 표는 **5-2 수집을 시작한 label**에만 적용합니다. 아직 수집 전이면 이 파일들이 없는 것이 정상입니다. 생성·배포 완료 여부가 불명확하고 남은 출력도 없다면 환경 소유자와 상태를 확인하기 전까지 재실행하지 않습니다. 빈 터미널이라는 이유로 새 clone·`init`·`bind`를 실행하지 않습니다.

**`src/agent/.foundry/results/<label>/`**에서 아래 파일을 수정하지 말고 읽습니다.

| 파일 | 완료 확인값 | 확인하는 범위 |
|---|---|---|
| `manifest.json` | `status: completed` | 응답 수집만 |
| `evaluation.json` | `status: completed`, 예상 `run → result_counts → total`, 오류 행 없음 | Foundry 평가 run 상태 |
| `evaluation-results.json` | 모든 응답에 대응하는 행과 각 행의 두 evaluator 결과 | 행별 평가. Trace 확인과는 별개 |
| `telemetry.json` | `complete: true`, 일치하는 `expected_trace_count` / `observed_trace_count` | 해당 label의 trace |

처음 미완료인 파일의 복구 안내를 따릅니다. manifest 하나의 완료는 전체 실습 완료가 아닙니다. 다른 실습이나 언어는 미사용 이름으로 새 폴더에서 시작하며, 소유권·응답·trace를 지워 복구하지 않습니다. Azure 환경 준비가 실패했다면 [환경 준비 복구](#setup-resume)를 따릅니다.

**완료 확인:** 첫 미완료 저장 상태가 실패한 단계 하나와 맞는 복구 섹션 하나를 가리킵니다.

**다르면:** 현재 폴더와 오류 출력을 보존합니다. 오류 메시지로 [증상별 확인](#symptoms)을 찾고, 수업 중이면 단계·label·상태 파일을 강사에게 보여 줍니다.

**다음:** 위의 맞는 섹션을 열거나, 아직 단계가 불명확하면 [증상별 확인](#symptoms)을 사용합니다.

<a id="deployment-recovery"></a>

## 배포 명령 자체가 실패했다면

**4-1 또는 7-2의 `azd deploy`가 실패한 경우입니다.** 단계·마지막 오류·출력에 표시된 에이전트 이름과 버전을 기존 메모에 남깁니다. 원래 명령이 실행 중이면 끝날 때까지 기다립니다. 성공한 배포 뒤 `grant-agent-access`·`smoke`만 실패했다면 배포를 반복하지 말고 [그 명령만 복구](#resume)합니다.

**터미널 — 같은 폴더에서 상태만 조회:**

```bash
azd ai agent show --output json
```

이 명령은 `azure.yaml`과 현재 azd 환경의 이름·버전을 사용합니다. **조회된 버전이 실패한 배포의 대상 버전인지 먼저 대조합니다.** 이전 V1이 `active`인 것은 새 V2 배포 성공이 아닙니다.

| 확인한 상태 | 다음 행동 |
|---|---|
| 대상 버전이 아직 준비 중 | 기다린 뒤 위 상태 조회만 반복. 새 배포를 겹쳐 실행하지 않음 |
| 대상 버전이 `active`로 확인됨 | 첫 배포였다면 [4-2 접근 권한](../README.ko.md#agent-access), V2 배포였다면 [7-2 새 버전 확인](../README.ko.md#candidate-smoke)으로 이동. 응답 확인은 생략하지 않음 |
| 대상 배포의 실패 또는 미생성을 확인했고 원인을 해결함 | 첫 배포는 [4-1](../README.ko.md#deploy-code), V2는 [7-2](../README.ko.md#candidate-deploy)의 `azd deploy --no-prompt`만 한 번 재시도. 이미 성공한 `set-prompt`는 반복하지 않음 |
| 이전 버전만 나옴, 조회 오류, 대상 버전을 모름 | 환경 소유자가 출력·대상 버전·포털의 **Agents → 내 에이전트 → Playground → Log stream**을 대조. 버전이 보인다는 이유만으로 성공 처리하거나 재배포하지 않음 |

**완료 확인:** 실패했던 대상 버전과 현재 상태를 확인했고, 위 표의 다음 행동 하나가 정해졌습니다.

**다르면:** 재시도도 실패하거나 상태를 확인할 수 없다면 멈추고 오류를 보존합니다. [중도 종료 안내](../README.ko.md#stop-early)를 따르며, 정리 전에 생성된 객체와 소유권 기록을 소유자와 대조합니다.

<a id="symptoms"></a>

## 증상별 확인

해당 행의 조치 뒤 실패했던 완료 확인으로 돌아갑니다. 계속 실패하면 오류를 보존하고 연결된 복구 절이나 강사에게 확인합니다.

**환경·로그인**

| 분류 | 증상 | 원인 또는 확인 | 조치 / 정확한 복귀 지점 |
|---|---|---|---|
| 환경 | `.env`가 없거나 필수 값 누락 | 비공개 배포 이름은 추측할 수 없습니다. | 전체 파일을 둔 뒤 [1-1 `.env` 확인](../README.ko.md#workspace-settings)으로 돌아갑니다. |
| 환경 | 오프라인 테스트가 `FAIL`·`ERROR`로 끝남 | Python·가상환경·의존성 오류와 실제 테스트 실패를 구분해야 합니다. | [오프라인 테스트 복구](#offline-tests). `OK` 전에는 Azure 작업을 시작하지 않습니다. |
| 환경 | `read: -p: no coprocess` 또는 경로/activate 파일 오류 | 지금 연 셸이나 폴더가 실습 때 쓰던 위치가 아닐 수 있습니다. | `bash`를 실행하고 [터미널 복원](../README.ko.md#resume-shell)으로 기존 폴더에 돌아갑니다. 새 clone을 만들지 않습니다. |
| 환경 | 언어가 다르거나 language mismatch | 영어는 `LAB_LANGUAGE=en`, 한국어는 `LAB_LANGUAGE=ko`이며 설정이 없으면 한국어입니다. | 원래 언어와 작업 폴더를 유지하고 [1-1 `.env` 확인](../README.ko.md#workspace-settings)으로 돌아갑니다. |
| 환경 | `preflight`의 `missing_models`가 비어 있지 않음 | 세 후보 배포 중 이름·버전·접근 권한·할당량 중 하나가 맞지 않습니다. | `.env`의 `MODEL_*_DEPLOYMENT`가 받은 값 그대로인지 확인한 뒤 환경 소유자에게 배포를 요청합니다(직접 만든 환경이면 [환경 준비 6-1](environment.ko.md#setup-candidates)). 그다음 [preflight](../README.ko.md#project-binding)로 돌아갑니다. |
| 환경 | `The fixed auxiliary planner/judge deployment is missing` | `.env`의 실제 `LAB_AUX_DEPLOYMENT`가 준비되지 않았습니다. | 환경 소유자가 [보조 모델 준비](instructor.ko.md#auxiliary-model) 후 [preflight](../README.ko.md#project-binding)로 돌아갑니다. |
| 환경 | `bind` 또는 `set-prompt`에서 환경/프로젝트 오류 | 이 폴더가 예상 프로젝트·언어에 바인딩되지 않았을 수 있습니다. | 이 폴더의 `bind`를 확인한 뒤 [프로젝트 연결](../README.ko.md#bind-project)로 돌아갑니다. |
| 로그인 | 로그인 안 됨 / tenant 오류 / 다른 계정 | CLI 중 하나가 다른 계정·tenant·subscription을 사용합니다. | 두 로그인을 확인한 뒤 [로그인 확인](../README.ko.md#login-check)으로 돌아갑니다. |
| 로그인 | 새 터미널에서만 로그인이 풀린 것처럼 보임 | 새 셸이 로컬 CLI 프로필 경로를 물려받지 않았습니다. | `AZURE_CONFIG_DIR`를 복원한 뒤 [터미널 복원](../README.ko.md#resume-shell)으로 돌아갑니다. |

**실행·증거**

| 분류 | 증상 | 원인 또는 확인 | 조치 / 정확한 복귀 지점 |
|---|---|---|---|
| <a id="symptom-local"></a>로컬 실행 | 로컬 8088 연결 실패 | 터미널 A가 준비되지 않았거나 포트를 다른 프로세스가 씁니다. | `Connection refused`이면 A의 `Running on ...:8088`을 기다린 뒤 B의 요청 블록만 반복합니다. `Address already in use`이면 내가 켜 둔 다른 실습 서버만 그 창에서 `Ctrl+C`로 종료하고 [3-1](../README.ko.md#local)을 재개합니다. 모르는 프로세스는 종료하지 않습니다. |
| 배포 | `azd deploy` 오류·상태 불명확 | 이전 버전과 이번 대상 버전을 구분해야 합니다. | [배포 상태 확인](#deployment-recovery) 후 해당 미완료 블록으로만 복귀합니다. |
| 검색 | `prepare-iq`에서 역할 부여 거부 | Search identity에 planner 접근 권한이 필요합니다. | [권한](instructor.ko.md#access)을 확인한 뒤 실패한 [2-1 정책 등록](../README.ko.md#knowledge-registration)을 다시 실행합니다. 아직 2-2 검색으로 넘어가지 않습니다. |
| 검색 | `retrieve`가 끝났지만 문서가 없거나 `TRAVEL-2026`이 없음 | 등록 성공과 검색 성공은 별도입니다. | [검색 복구](#retrieval) 후 [정책 검색](../README.ko.md#policy-retrieval)으로 돌아갑니다. |
| <a id="symptom-hosted"></a>Hosted Agent | Search 403 / 역할 부여 실패 | 사용자 권한과 Hosted Agent 인스턴스 ID 권한은 다릅니다. | 두 ID를 확인한 뒤 [에이전트 접근 권한](../README.ko.md#agent-access)으로 돌아갑니다. |
| Hosted Agent | Hosted 424 / cold start | 해당 Hosted 버전이 아직 준비되지 않았을 수 있습니다. | 1–2분 뒤 [원격 응답 확인](../README.ko.md#hosted-smoke)의 `smoke`만 반복합니다. 계속 실패하면 **내 에이전트 → Playground → Log stream**의 오류를 확인합니다. 재배포하지 않습니다. |
| 수집 | 429 / 시간 초과 | 용량 또는 서비스 제한으로 중단됐을 수 있습니다. | 원인과 Retry-After를 보존한 뒤 [수집 복구](#collection-retry)로 돌아갑니다. |
| trace | 시작 시 `connections/read` 거부 | 시작 코드가 연결 메타데이터를 직접 읽고 있을 수 있습니다. | 코드·역할을 바꾸지 말고 [시작 로그 확인·인계](#hosted-telemetry)를 따릅니다. 해결 뒤 원래 단계의 `smoke`만 재개합니다. |
| 평가 | 평가 완료인데 오류 행이나 `null` 점수 | 평가 run 완료와 행별 성공은 다릅니다. | [평가 복구](#evaluation-retry) 후 [baseline](../README.ko.md#baseline-evaluation), [후보](../README.ko.md#candidate-evaluation), [holdout](../README.ko.md#holdout-evaluation)으로 돌아갑니다. |

**완료·정리**

| 분류 | 증상 | 원인 또는 확인 | 조치 / 정확한 복귀 지점 |
|---|---|---|---|
| <a id="symptom-completion"></a>완료 판단 | `verify`는 성공했는데 `candidate_quality_gates`에 `false`가 있음 | 유효한 실행에서 품질 게이트가 실패한 결과입니다. | 보고한 뒤 [완료 판단](../README.ko.md#completion-decision)으로 돌아갑니다. |
| 완료 판단 | `production_release_approved: false` | 업무 게이트를 통과해도 정상입니다. | 값을 그대로 두고 [완료 판단](../README.ko.md#completion-decision)으로 돌아갑니다. |
| 정리 | 정리 대상이 내 이름과 다름 | 소유권 기록과 Azure 상태가 맞지 않을 수 있습니다. | 멈추고 [정리 복구](#cleanup-recovery)를 사용한 뒤 [정리 확인](../README.ko.md#cleanup-check)으로 돌아갑니다. |
<details>
<summary>그 밖의 증상</summary>

| 분류 | 증상 | 원인 또는 확인 | 조치 / 정확한 복귀 지점 |
|---|---|---|---|
| 환경 | 모델 404 | 카탈로그 모델 ID와 실제 배포 이름이 다를 수 있습니다. | `.env`와 azd 값을 대조한 뒤 [preflight](../README.ko.md#project-binding)로 돌아갑니다. |
| 검색 | IQ 400 / schema 오류 | 고정 API 버전, KB schema, 보조 planner 지원이 맞지 않을 수 있습니다. | 세 가지를 확인한 뒤 [정책 검색](../README.ko.md#policy-retrieval)으로 돌아갑니다. |
| 환경 | JSON 뒤의 azd 업데이트 안내 | 제공 실행기는 UTF-8 HTTP 본문과 확인된 안내만 분리합니다. | 수업 중 업그레이드하지 말고 [preflight](../README.ko.md#project-binding)로 돌아갑니다. |
| 로그인 | CLI credential 시간 초과 | 토큰 갱신 지연이 로그인 실패처럼 보일 수 있습니다. | 실제 로그인 실패와 구분한 뒤 [로그인 확인](../README.ko.md#login-check)으로 돌아갑니다. |
| trace | App Insights `ResourceId` 메타데이터 누락 | 실습 전용 App Insights 연결 메타데이터가 불완전할 수 있습니다. | 환경 소유자가 [소유자 전용 관측 복구](instructor.ko.md#observability-repair)를 따른 뒤 [trace 복구](#telemetry)로 돌아갑니다. |

</details>

<a id="offline-tests"></a>

## 오프라인 테스트가 실패했다면

**Azure 로그인·배포 전에 해결합니다.** 첫 `FAIL`·`ERROR`의 테스트 이름과 traceback을 보존합니다. 아래 명령은 테스트를 실행했던 **같은 폴더**에서 사용합니다. 새 환경 준비의 실행 폴더는 원래 clone이 아니라 `RUN_DIR/workshop`입니다.

**터미널 — 기존 가상환경과 의존성 확인:**

```bash
source src/agent/.venv/bin/activate &&
python --version &&
python -c 'import sys; print(sys.executable); print(sys.prefix)' &&
python -m pip check
```

**완료 확인:** Python은 `3.13.x`, 실행 파일과 가상환경 경로는 이 폴더의 `src/agent/.venv` 아래이며, 마지막 줄은 `No broken requirements found.`입니다. 이 확인만으로 테스트가 통과한 것은 아닙니다.

**다르면:** 아래에서 해당 원인만 고칩니다.

| 확인 결과 | 다음 행동 |
|---|---|
| `activate` 파일이 없음 | 원래 설치 위치로 돌아갑니다: [참가자 1-2](../README.ko.md#python-setup), [새 환경 1-6](environment.ko.md#setup-python), [기존 환경 Python 준비](instructor.ko.md#existing-python). 없는 가상환경만 만들며 소스·실행 기록은 보존합니다. |
| Python 버전이나 가상환경 경로가 다름 | 현재 폴더와 [Python 3.13 설치](instructor.ko.md#tools)를 확인합니다. 다른 폴더의 Python을 쓰거나 기존 가상환경을 삭제해 우회하지 않습니다. |
| 원래 오류가 `ModuleNotFoundError`이거나 `pip check`가 의존성 불일치를 보고함 | 위 Python·경로가 맞을 때만 아래 고정 의존성 복구를 실행합니다. |
| 환경 확인은 정상이지만 assertion 등 테스트 실패가 남음 | 테스트 이름·traceback·Python 버전을 수업 담당자에게 전달합니다. 혼자 실습하면 비밀·개인 정보를 제거한 오류로 [저장소 이슈](https://github.com/junwoojeong100/foundry-evaluation/issues)를 확인하거나 보고하고 중단합니다. 테스트·정책·고정 정답을 수정해 `OK`로 만들지 않습니다. |

**터미널 — 누락·불일치 의존성이 확인된 경우에만:**

```bash
python -m pip install -r requirements.lock.txt &&
python -m pip check
```

**완료 확인:** 설치가 오류 없이 끝나고 `No broken requirements found.`가 나옵니다.

**다르면:** 다운로드·의존성 오류를 보존하고 중단합니다. 임의 버전 설치나 전역 설치로 우회하지 않습니다.

**터미널 — 원인을 해결한 뒤 같은 테스트만 다시 실행:**

```bash
python -m unittest discover -s tests -v
```

**완료 확인:** `OK`로 끝납니다. 새 환경의 실행용 복사본은 문서 검사만 생략한 `OK (skipped=1)`도 정상입니다.

**다르면:** 첫 실패 이름·오류를 지원 담당자에게 전달하고 Azure 작업은 계속 보류합니다.

| 테스트를 실행하던 경로 | `OK` 뒤 이어갈 곳 |
|---|---|
| 참가자 README 1-2 | [1-3 로그인](../README.ko.md#login) |
| 새 환경 준비 1-6 | [2-1 로그인](environment.ko.md#setup-identity) |
| 기존 환경 준비 | [1. 설정·로그인](instructor.ko.md#existing-settings) |

<a id="login"></a>

## 로그인 브라우저가 열리지 않는다면

같은 터미널에서 먼저 [README 1-3](../README.ko.md#login)의 **CLI 경로 지정과 tenant·구독 입력 블록**을 실행합니다.

**로그인에 실패한 CLI의 명령만 실행합니다.** 둘 다 필요하면 Azure CLI → azd 순서입니다.

각 명령이 표시한 주소를 브라우저로 열고, **본인 터미널에 표시된 일회용 코드**를 입력해 `.env`의 계정으로 로그인합니다. 코드는 공유하거나 녹화하지 않습니다.

**터미널 — Azure CLI:**

```bash
az login --tenant "$LOGIN_TENANT_ID" --subscription "$LOGIN_SUBSCRIPTION_ID" \
  --use-device-code --output none
```

**완료 확인:** 브라우저 로그인을 마치고 터미널에 오류 없이 프롬프트가 돌아옵니다. 계정 JSON은 출력하지 않습니다.

**다르면:** 오류를 보존합니다. 조직 정책으로 차단됐다면 우회하지 말고 승인된 로그인 환경을 사용합니다.

**터미널 — azd:**

```bash
azd auth login --tenant-id "$LOGIN_TENANT_ID" --use-device-code
```

**완료 확인:** 브라우저 로그인을 마치고 터미널에 오류 없이 프롬프트가 돌아옵니다.

**다르면:** 오류를 보존합니다. 조직 정책으로 차단됐다면 우회하지 말고 승인된 로그인 환경을 사용합니다.

<a id="login-return"></a>

**Azure CLI만 복구했고 azd 로그인은 아직 안 했다면, azd 로그인부터 마칩니다.** azd만 실패했고 Azure CLI는 이미 성공했다면 바로 두 로그인 확인으로 갑니다. 폴더를 바꾸거나 성공한 로그인을 반복하지 않습니다.

**이 문서로 오기 직전의 경로**에서 아래 한 행을 따릅니다. 두 로그인을 모두 마쳐야 확인 블록을 실행합니다.

| 로그인하던 경로 | azd 로그인이 아직이면 | 두 로그인 완료 후 확인 | 확인 뒤 이어갈 곳 |
|---|---|---|---|
| 참가자 README 1-3 | [README 3번 azd 로그인](../README.ko.md#azd-login) | [README 두 로그인 확인](../README.ko.md#login-check) | README 1-4 프로젝트 확인 |
| 새 환경 준비 2-1 | [환경 준비 azd 로그인](environment.ko.md#azd-login) | [환경 준비 두 로그인 확인](environment.ko.md#login-check) | 같은 문서 2-2 계정·보존·용량 확인 |
| 기존 환경 준비 1 | [기존 환경 azd 로그인](instructor.ko.md#azd-login) | [기존 환경 두 로그인 확인](instructor.ko.md#login-check) | 같은 문서의 후보 배포 이름 지정 → 2 보조 배포 준비 |

**새 환경 준비 중에는 아직 서비스가 없으므로 README의 `preflight`·`bind`로 넘어가지 않습니다.**

**완료 확인:** 선택한 확인 블록에서 Azure CLI와 azd의 계정, tenant, subscription이 그 폴더의 `.env`와 일치합니다.

**다르면:** 정확한 로그인 오류를 보존하고 승인된 로그인 경로를 강사에게 요청합니다. 계정이나 tenant를 바꾸지 않습니다.

<details>
<summary>참고 링크</summary>

[Azure CLI 대화형 로그인](https://learn.microsoft.com/cli/azure/authenticate-azure-cli-interactively) · [CLI 설정 경로](https://learn.microsoft.com/cli/azure/azure-cli-configuration#cli-configuration-file)

</details>

**다음:** 위 표에서 선택한 문서의 확인 블록 아래부터 이어갑니다. 준비 경로를 바꾸지 않습니다.

<a id="hosted-telemetry"></a>

## 시작 로그에 `connections/read`가 있다면

**참가자:** 원래 단계에서 멈춥니다. **내 에이전트 → Playground → Log stream**에서 해당 오류를 확인하고, 실패한 단계·`LAB_AGENT_NAME`·확인 가능한 배포 버전·오류 부분만 환경 소유자에게 전달합니다. 연결 문자열·토큰·`.env` 전체는 공유하지 않으며, 해결하려고 에이전트에 Owner를 주거나 소스를 바꾸지 않습니다.

**환경 소유자:** 배포에 사용한 소스와 `azure.yaml`을 편집기로 확인합니다. 제공된 `src/agent/main.py`의 `telemetry_connection`은 `APPLICATIONINSIGHTS_CONNECTION_STRING` 또는 `OTEL_EXPORTER_OTLP_ENDPOINT`가 주입되면 프로젝트 연결을 조회하지 않습니다. 제공된 `azure.yaml`의 hosted 서비스 `env`에는 `LAB_AUTH_MODE=cli`를 전달하지 않습니다. 배포본이 이 조건과 다르거나 런타임의 주입 설정을 확인할 수 없으면 오류와 버전을 소스 유지 관리자·플랫폼 지원에 전달합니다. 확인 없이 연결 문자열을 복사하거나 재배포하지 않습니다.

**완료 확인:** 원인을 해결한 뒤 원래 단계의 `smoke`만 실행했을 때 시작 오류가 없고 해당 단계의 언어·지침·숫자 버전 조건을 만족합니다.

**다르면:** 오류와 현재 버전을 보존하고 중단합니다. 수정 과정에서 7-2 뒤에 재배포했다면 [V2 변경 복구](#v2-changed)로 비교 기준을 다시 맞춥니다.

<a id="retrieval"></a>

## 정책을 등록했는데 검색 근거가 없다면

2단계의 질문에서 `document_ids`에 **`TRAVEL-2026`이 없거나 `activity`가 비어 있다면** 여기서 확인합니다. `retrieve`가 오류 없이 끝났다는 사실만으로 필요한 정책을 찾았다고 판단하지 않습니다.

**원인:** 등록은 성공했지만 인덱스가 아직 검색 가능하지 않거나 KB/source/인덱스 연결이 다를 수 있습니다.

1. `prepare-iq`가 **`Foundry IQ ready: ...; 7 synthetic documents.`**로 끝났는지 확인합니다. 검색 출력의 `knowledge_base`도 내 `LAB_PREFIX` + `-kb`여야 합니다. 등록 자체가 실패했다면 그 오류부터 해결합니다.
2. `retrieve` 출력의 **`saved` 경로**를 편집기로 열어 `documents`, `references`, `activity`를 확인합니다. 등록 직후라면 1–2분 기다린 뒤 **[2단계의 같은 `retrieve` 명령만](../README.ko.md#policy-retrieval)** 다시 실행합니다. 검색 확인을 위해 `prepare-iq`, 배포, 응답 수집까지 반복하지 않습니다.
3. 여전히 근거가 없으면 환경 소유자와 KB·source·인덱스 연결을 대조합니다. 내 실습의 **`LAB_PREFIX-kb` → `LAB_PREFIX-source` → `LAB_PREFIX-policies`**여야 하며, `LAB_PREFIX`는 `.env`의 실제 값으로 읽습니다.

결과 파일과 KB 이름은 보존합니다. 정책·질문을 바꾸어 통과시키거나 다른 조의 KB를 사용하지 않습니다.

**완료 확인:** 저장 파일의 `knowledge_base`가 내 KB이고, `documents` 목록 안에 `"id": "TRAVEL-2026"`이 있으며 `activity`가 비어 있지 않습니다. **`document_ids`는 터미널 요약에만 나오는 필드**입니다.

**다르면:** 저장 경로와 KB/source/인덱스 이름을 환경 소유자에게 전달합니다. 정책·질문이나 다른 조의 KB를 바꾸지 않습니다.

**다음:** [2단계 완료 기준과 포털 확인](../README.ko.md#policy-retrieval)을 마친 뒤 3단계로 진행합니다.

<a id="calibration"></a>

## Judge calibration을 통과하지 못했다면

파일이 있다면 **`src/agent/.foundry/results/judge-calibration/evaluation.json`**을 확인합니다. 평가가 **아직 실행 중**이거나 생성·다운로드 오류를 해결했다면 아래로 재개합니다.

**터미널 — 기존 calibration 재개:** 원래 명령이 끝난 뒤 실행합니다. 채점 중에는 1–3분쯤 출력이 없을 수 있습니다.

```bash
python scripts/workshop.py calibrate
```

**완료 확인:** 마지막 줄에 `Judge calibration passed; ...`가 나옵니다. 아래 재시도 블록은 건너뜁니다.

**다르면:** `Evaluation is still running`이면 같은 명령으로 이어갑니다. 실패·오류 run이 기록됐을 때만 아래 블록을 고릅니다. 정상 완료된 낮은 점수는 재시도하지 않습니다.

**터미널 — 실패한 calibration만 재시도:** 저장된 `status`가 **`failed` / `canceled` / `cancelled`**이거나 **`run → result_counts → errored`가 0보다 클 때만** 사용합니다. 원인을 먼저 해결하며 실패한 작업은 보존됩니다.

```bash
python scripts/workshop.py calibrate --retry-failed
```

실패·오류 실행이 기록되지 않은 결과 형식 오류·누락은 이 calibration 폴더의 상태·원문 결과를 보존하고 환경 소유자에게 확인합니다. 재시도를 강행하지 않습니다. Calibration은 본평가 48응답과 별개입니다.

**완료 확인:** 마지막 줄에 `Judge calibration passed; ...`가 나오고, 같은 폴더의 `calibration.json`에 `passed: true`가 있습니다.

**다르면:** calibration 폴더와 원문 출력을 보존하고 환경 소유자에게 확인합니다. 예제·threshold를 바꾸거나 유효한 낮은 점수를 반복 실행하지 않습니다.

<a id="calibration-return"></a>

**다음:** `Judge calibration passed`가 나오면 원래 진행하던 경로로 돌아갑니다. calibration은 이미 끝났으므로 다시 실행하거나 준비 경로를 바꾸지 않습니다.

| calibration이 멈췄던 곳 | 다음 미실행 단계 |
|---|---|
| 참가자 README 5-1 | [5-2 baseline 수집](../README.ko.md#baseline-collection) |
| 새 환경 준비 6-2 | [6-3 전달 경로](environment.ko.md#handoff) |
| 기존 환경 준비 3 | [리허설 또는 개인 실습 선택](instructor.ko.md#after-calibration) |

<a id="telemetry"></a>

## 쉬었다가 이어 하니 trace가 없다면

포털이 Last Day를 보여도 `monitor`의 기본 조회는 **최근 2시간**입니다. 최근 24시간 안의 실행이라면 **같은 label**을 유지하고 기간만 늘립니다.

**터미널 — 기존 trace 조회 기간 늘리기:**

```bash
python scripts/workshop.py monitor --label baseline --hours 24
```

실패한 모니터링이 다른 단계라면 `baseline`을 실제 `improved` 또는 `holdout`으로 바꿉니다. `--hours`는 **1–168 사이 정수 시간**이며 원래 수집 시점을 포함하도록 선택합니다. 이미 보존 기간이 끝났거나 삭제된 telemetry를 되살리는 옵션은 아닙니다.

**완료 확인:** `telemetry.json`의 `complete`가 `true`이고 같은 label의 `expected_trace_count`와 `observed_trace_count`가 일치합니다.

**다르면:** label, 수집 시각, 조회 기간, telemetry 오류를 환경 소유자에게 전달합니다. 응답을 다시 수집하거나 `telemetry.json`을 편집하지 않습니다.

<details>
<summary>그래도 실패할 수 있는 이유</summary>

에이전트와 run 필터는 그대로이며 trace 누락·중복·다른 trace·sampling은 여전히 검사에서 실패합니다. 방금 실행했다면 반영을 기다린 뒤 이 명령만 반복합니다. 계속 누락되면 환경 소유자와 권한·보존 기간·연결된 App Insights를 확인합니다. 응답을 다시 수집하거나 `telemetry.json`을 편집해 완료 상태를 만들지 않습니다.

</details>

**다음:** 복구한 명령을 반복하지 말고 해당 trace의 완료 확인 아래부터 이어갑니다: [baseline trace](../README.ko.md#baseline-traces), [후보 trace](../README.ko.md#candidate-traces), [holdout trace](../README.ko.md#holdout-traces). 이미 정리까지 했다면 저장된 증거만 읽습니다. 새 실험은 새 작업 폴더와 새 이름으로 시작합니다.

<a id="collection-retry"></a>

## 응답 수집에 실패했다면

다음 조건에서만 사용합니다:

- 원래 수집기가 종료됐을 때만 사용합니다. 종료란 원래 터미널이 프롬프트로 돌아왔거나, 터미널을 닫았다면 그 프로세스가 끝난 것을 확인한 상태입니다. 확실하지 않으면 기다리며, 두 번째 수집 명령을 시작하지 않습니다.
- 실패한 label의 상태와 원문은 보존합니다.
- 같은 단계만 미사용 retry label 하나로 한 번 다시 수집합니다.
- 모델·split·질문·지침·에이전트 버전·완료된 label·검토 출처는 바꾸지 않습니다. [7-2 뒤 V2가 바뀐 경우](#v2-changed)만 현재 V2 버전으로 수집합니다.
- 첫 retry도 실패하면 멈추고 오류를 보존합니다.

| 실패한 경우 | 이동할 곳 |
|---|---|
| 비교 전 baseline 실패 | [처음 baseline 실패](#collection-retry-baseline) |
| baseline 완료 뒤 V2 dev 실패 | [V2 dev 수집 실패](#collection-retry-improved) |
| holdout 실패 | [Holdout 수집 실패](#collection-retry-holdout) |

<a id="run-values"></a>

### 복구 뒤 사용할 실행값

**복구 수집이 성공하면 본문으로 돌아가기 전에 기존 메모의 아래 값만 갱신합니다.** 복구하지 않은 label은 원래 값을 유지합니다. 아직 수집하지 않은 단계는 기본값을 적고, 나중에 복구할 때만 바꿉니다.

| 메모할 값 | 최초 기본값 | 복구 후 사용할 값과 위치 |
|---|---|---|
| V1 dev label | `baseline` | V1 복구 성공 시 `baseline-retry`. 이후 `feedback`·`compare`·`summary`·`monitor`와 `verify --baseline`의 값 |
| V2 dev label | `improved` | V2 복구 성공 시 `improved-retry`. 이후 비교·조회·trace와 `verify --candidate`의 값 |
| V2 holdout label | `holdout` | holdout 복구 성공 시 `holdout-retry`. 이후 비교·조회·trace와 `verify --holdout`의 값 |
| 수집 동시성 `concurrency` | `4` | **완료한 V1 baseline**의 `src/agent/.foundry/results/<실제 label>/manifest.json`에서 읽음. `2`이면 이후 V2 dev·holdout `collect`에도 `--concurrency 2` 적용 |

**바꿀 것은 값이지 옵션 이름이 아닙니다.** `--label`·`--labels`·`--baseline`·`--candidate`·`--holdout` 뒤의 label 값, 읽을 결과 경로와 출력 설명에 실제 이름을 적용합니다. **`--split dev`·`--split holdout`은 바꾸지 않습니다.** `row_id`는 그 label의 실제 출력에서 복사합니다. 기존 폴더·파일·row ID·manifest를 이름 변경하거나 편집하지 않습니다.

예를 들어 **V2 dev만** 복구했다면 최종 검증은 `python scripts/workshop.py verify --baseline baseline --candidate improved-retry --holdout holdout`입니다. 다른 단계도 복구했다면 그 값도 메모대로 바꿉니다. 이 메모는 [9-3 보고서](../README.ko.md#finish)에도 옮깁니다.

**복구를 아직 실행하지 않았다면:** 위 첫 표에서 실패한 단계 하나를 고르고, 해당 하위 절의 명령만 실행합니다. 이 절은 재수집 허용 조건을 바꾸지 않습니다.

<a id="collection-retry-baseline"></a>

### 처음 baseline 실패

**터미널 — V1 재수집:** 429 또는 시간 초과에서 낮은 동시성이 복구 방법일 때 사용합니다.

```bash
python scripts/workshop.py collect --split dev --label baseline-retry --concurrency 2
```

**완료 확인:** 오류 없이 `18/18`로 끝납니다. 완료한 것은 **V1 수집뿐**이며, 평가·포털·trace 확인은 아직 남아 있습니다.

**다르면:** 새 label을 또 만들지 말고 오류와 원래 실패 기록을 보존합니다.

**다음:** [실행값 메모](#run-values)를 `V1 dev=baseline-retry`, `concurrency=2`로 갱신하고 [5-3의 평가 명령](../README.ko.md#baseline-evaluation)부터 이어갑니다. 이후 V2 dev·holdout 수집에도 `--concurrency 2`를 적용하며, 예시 `baseline-sol-D01`은 `baseline-retry-sol-D01`로 읽습니다. 완료한 수집은 반복하지 않습니다.

<a id="collection-retry-improved"></a>

### V2 dev 수집 실패

README 7-4에서 검토 기록이 연결되지 않았거나(`source trace carried: no`) [7-2 뒤 V2가 바뀐](#v2-changed) 경우에도 이 명령으로 새 label을 수집합니다.

**터미널 — V2 dev 재수집:** 완료한 baseline의 `manifest.json`에서 `concurrency`를 확인합니다. `2`이면 아래 `--concurrency 4`를 `--concurrency 2`로 바꿉니다.

```bash
python scripts/workshop.py collect --split dev --label improved-retry --concurrency 4
```

**완료 확인:** 오류 없이 `18/18`로 끝납니다.

**다르면:** 멈추고 오류를 보존합니다. 완료된 baseline·검토 기록은 바꾸지 않습니다.

**다음:** [실행값 메모](#run-values)의 V2 dev label을 `improved-retry`로 갱신하고 [7단계의 평가·비교](../README.ko.md#candidate-evaluation)부터 이어갑니다. 이후 명령·경로에서도 이 값을 유지합니다.

<a id="collection-retry-holdout"></a>

### Holdout 수집 실패

**터미널 — holdout 재수집:** 완료한 baseline의 `manifest.json`에서 `concurrency`를 확인합니다. `2`이면 아래 `--concurrency 4`를 `--concurrency 2`로 바꿉니다.

```bash
python scripts/workshop.py collect --split holdout --label holdout-retry --concurrency 4
```

**완료 확인:** 오류 없이 `12/12`로 끝납니다.

**다르면:** 멈추고 오류를 보존합니다. 고정한 지침은 바꾸지 않습니다.

**다음:** [실행값 메모](#run-values)의 V2 holdout label을 `holdout-retry`로 갱신하고 [8단계의 평가](../README.ko.md#holdout-evaluation)부터 이어갑니다. `--split holdout`은 그대로입니다.

<a id="evaluation-retry"></a>

## Foundry 평가 run만 실패했다면

응답 수집이 온전히 완료됐는지 먼저 확인합니다. **`src/agent/.foundry/results/<label>/evaluation.json`**이 있다면 읽고 아래에서 하나를 선택합니다.

| 저장된 상태 / 오류 | 다음 행동 |
|---|---|
| Foundry 평가 run 생성 전 중단, 로컬 대기 시간 초과, 결과 다운로드 중단 | 원인을 해결한 뒤 **A**. 저장된 run을 재사용하며, 아직 run이 없을 때만 생성 |
| `status: failed / canceled / cancelled` 또는 `run → result_counts → errored`가 0보다 큼 | 원인을 해결한 뒤 **B**. 실패한 시도를 보존하고 재시도 실행 생성 |
| 오류 행 없이 평가 run은 완료됐지만 ID 누락·중복, `null` 점수, 결과 형식 검증에서 실패 | 중단하고 `evaluation.json`과, 있다면 `evaluation-output-raw.json`을 보존. 환경 소유자에게 결과 형식 확인을 요청하며 **B 강행·상태/점수 편집 금지** |
| 평가 run과 각 행은 정상 완료됐지만 유효한 점수가 낮음 | 재시도하지 않습니다. 보고서와 포털 확인을 마치고 실습을 계속합니다. |

아래 명령의 `baseline`을 **실제로 실패한 label**로 바꿉니다(`improved-retry` 같은 복구 label도 포함). 원래 명령이 끝난 뒤 하나만 실행합니다. 채점 중에는 1–3분쯤 출력이 없을 수 있습니다.

**터미널 — A. 같은 입력의 평가 시작 또는 재개:**

```bash
python scripts/workshop.py evaluate --label baseline
```

**완료 확인:** `Foundry evaluation completed: ... (18 rows)` 또는 holdout의 `(12 rows)`와 보고서 URL이 나옵니다. 아래 B는 건너뜁니다.

**다르면:** 위 저장 상태 표에서 다시 고릅니다. 대기 시간 초과이면 A로 이어가고, 실패·오류 run이 기록됐을 때만 B를 씁니다.

**터미널 — B. 실패·오류 run이 기록된 경우에만 재시도:**

```bash
python scripts/workshop.py evaluate --label baseline --retry-failed
```

평가 오류 때문에 `collect`를 반복하지 않습니다.

**완료 확인:** `evaluation.json`의 `status`가 `completed`이고, `run → result_counts → total`이 예상 개수이며 `errored`가 `0`입니다. `evaluation-results.json`에는 응답마다 유효한 행이 하나씩 있습니다.

**다르면:** `evaluation.json`과 원문 출력을 보존하고 위 저장 상태 표에서 고릅니다. 상태·점수를 편집하거나 수집을 반복하지 않습니다.

**다음:** 중단했던 완료 확인으로 돌아갑니다: [baseline 평가](../README.ko.md#baseline-evaluation), [후보 평가](../README.ko.md#candidate-evaluation), [holdout 평가](../README.ko.md#holdout-evaluation).

<a id="no-failures"></a>

## baseline이 전부 통과했다면

실패가 없다는 것도 결과입니다. 실패를 만들거나 답변·정답을 수정하지 않습니다.

1. [README 6-2](../README.ko.md#review-case)의 `show` 블록에 `baseline-sol-D01`(또는 다른 baseline 행)을 넣어 저장된 응답과 고정 정답을 봅니다. `row_id`와 `trace_id`를 메모합니다.
2. 6-2처럼 응답을 고정 dev 정답과 비교하고, 포털에서 그 trace를 확인합니다.
3. “업무 검사는 전부 통과했고 무엇을 확인했는지”와 **제공 V2에서도 유지할 동작**을 한 줄로 설명합니다. 실패나 품질 개선을 미리 주장하지 않습니다.
4. [6-3 검토 기록 저장](../README.ko.md#save-review)으로 돌아갑니다. `feedback`은 통과한 dev 응답도 기록할 수 있습니다. 저장 후 7단계에서 V2의 타당성을 검토합니다.

최종 `verify`는 후보 결과가 저장된 baseline trace ID를 보관하는지만 확인합니다. baseline trace를 후보 trace 증거로 재사용하지 않습니다.
holdout을 열어 실패를 찾거나 개선 재료로 사용하는 것은 금지합니다.

**완료 확인:** 저장한 검토 기록에 baseline `row_id`, `trace_id`, 확인한 내용, V2가 유지해야 할 동작이 있습니다.

**다르면:** 선택한 baseline 응답과 고정 dev 정답으로 돌아갑니다. holdout을 쓰거나 실패를 만들지 않습니다.

**다음:** [V2 배포와 후보 평가](../README.ko.md#lab-e)를 계속합니다.

<a id="review-recovery"></a>

## 검토 기록이 이미 있거나 잘못 저장됐다면

**V2 수집 전에 확인합니다.** `src/agent/.foundry/datasets/regression-*.jsonl`은 다음 dev 수집에서 모두 읽습니다. 올바른 행을 추가 저장하거나 보고할 행을 바꾸는 것만으로 오저장 기록이 제외되지 않습니다.

1. **편집기:** 기존 파일의 `lineage`에서 `source_row_id`·`source_trace_id`·`review_reason`·`language`를 읽습니다. [6-2](../README.ko.md#review-case)에서 그 행의 저장된 응답·고정 정답·trace를 실제로 대조합니다.
2. 이미 실제 검토와 일치하는 기록이면 그대로 둡니다. 실수로 다른 행을 저장했지만 이제 그 행도 검토했고 저장된 이유가 근거와 일치한다면, 기존 메모에 **오저장 경위와 나중에 추가 검토한 사실**을 적습니다.
3. 이유·출처·정답이 맞지 않거나, 오저장 상태로 V2 수집까지 했다면 멈춥니다. 파일과 오류를 보존하고 행 ID·trace ID·오저장 사유를 강사 또는 저장소 담당자에게 전달합니다. 파일 삭제·편집·추가 저장만으로 복구 완료를 만들지 않습니다.

**완료 확인:** 남아 있는 모든 검토 기록이 실제 검토한 행·근거와 일치하고, 오저장이 있었다면 경위가 메모에 남아 있습니다.

**다르면:** V2 수집을 시작하지 않습니다. 확인할 수 없는 검토를 정상 결과로 보고하거나 원래 증거를 수정하지 않습니다.

**다음:** [6-3의 저장된 기록 확인](../README.ko.md#read-review)만 마친 뒤 7단계로 갑니다. 기존 행의 `feedback`은 반복하지 않습니다.

<a id="v2-changed"></a>

## 7-2 뒤 V2가 바뀌었다면

holdout은 7-3에서 평가한 **그 V2 버전**으로만 수집합니다. 8-1 수집이 `Hosted prompt does not match`로 멈췄거나, 8-2에서 improved와 holdout의 `agent_version`·`prompt_hash`가 다르면 여기서 고릅니다. 결과 파일은 지우거나 고치지 않습니다.

| 7-2 뒤에 한 일 | 할 일 |
|---|---|
| `set-prompt` 실행, `.env`·prompt 파일 수정만 함(`azd deploy`는 안 함) | 아래 **A**로 선택을 되돌린 뒤 8-1로 돌아갑니다. |
| `azd deploy`를 다시 함 | 에이전트 버전이 바뀌어 기존 `improved`와 짝이 맞지 않습니다. 아래 **B**를 따릅니다. |

prompt 파일을 고쳤다면 수정 내용을 별도 메모에 보관한 뒤 **제공된 원본**으로 복원합니다. `.env`의 다른 값도 바꿨다면 7-2 때의 값으로 되돌립니다.

| 실습 폴더 | 원본 지침 복원 방법 |
|---|---|
| 참가자의 Git clone | **터미널:** 이 폴더에서 `git restore -- src/agent/prompts`를 실행합니다. |
| 자습용 `$RUN_DIR/workshop` 복사본 | **편집기:** 원래 clone의 수정하지 않은 `src/agent/prompts/` 파일들을 실습 복사본의 같은 경로로 복사합니다. 복사본에는 `.git`이 없으므로 위 Git 명령을 쓰지 않습니다. |
| 압축을 푼 ZIP 폴더 | **편집기:** 처음 받은 ZIP의 `src/agent/prompts/` 원본 파일들로 복원합니다. |

**터미널 — A. V2 선택 되돌리기(재배포 없음):**

```bash
python scripts/workshop.py set-prompt v2 &&
python scripts/workshop.py smoke
```

**완료 확인:** `prompt_version: v2`이고 `agent_version`이 메모한 **V2 버전**(7-2)과 같습니다. 이후 추가 변경이 없다면 A를 반복하지 않습니다. holdout 수집을 시작한 적이 없으면 [8-1 수집 블록](../README.ko.md#holdout-collection)으로 갑니다. 이미 `holdout/manifest.json`이 있으면 기존 기록을 보존하고 [holdout 재수집](#collection-retry-holdout)으로 갑니다.

**다르면:** 원본 지침과 설정을 복원한 뒤에도 버전이 다르거나 `Hosted prompt does not match`가 계속되면 기존 V2와 같은 조건이 아닙니다. **B**를 따릅니다.

**B — 현재 V2 버전으로 dev부터 다시:**

1. **터미널:** A의 **명령 블록**으로 현재 버전을 확인합니다(방금 실행했다면 그 출력 사용). `Hosted prompt does not match`이면 `azd deploy --no-prompt`를 **한 번만** 실행한 뒤 A의 명령 블록을 다시 실행합니다. `prompt_version: v2`가 나오면 새 `agent_version`을 메모합니다.
2. [V2 dev 수집 복구](#collection-retry-improved)로 `improved-retry`를 수집합니다. README 7-3 평가·비교와 7-4 요약까지 그 label로 마칩니다.
3. 새 버전을 메모의 V2 기준으로 삼고, 이후 추가 변경이 없으면 [8-1 수집 블록](../README.ko.md#holdout-collection)으로 갑니다. 이미 `holdout/manifest.json`이 있으면 [holdout 재수집](#collection-retry-holdout)의 `holdout-retry`를 씁니다. 이후 명령·파일 경로·`verify`에도 바뀐 label을 씁니다.

이미 holdout을 봤다면 보고서에 `V2 변경 복구로 holdout 재사용`을 적습니다. 결과를 보고 지침을 튜닝하거나 이를 새로운 미사용 검증으로 보고하지 않습니다.

**완료 확인:** 8-2 확인에서 새 improved label과 holdout label의 `agent_version`·`prompt_hash`가 같습니다.

**다르면:** 멈추고 오류와 label 이름을 기록합니다. 기존 결과를 지우거나 버전을 맞추려고 반복 배포하지 않습니다.

**다음:** 아직 하지 않은 [8-1 수집](../README.ko.md#holdout-collection) 또는 [8-2 확인](../README.ko.md#holdout-comparison)으로 돌아갑니다. 완료한 수집·평가는 반복하지 않습니다.

<a id="portal-differs"></a>

## 포털 화면이 예시 화면과 다르면

예시 화면의 계정·프로젝트·이름·버전·시간 범위가 아니라 **본인 값**을 확인합니다.

| 차이 | 확인할 것 | 하지 말 것 |
|---|---|---|
| report URL을 잃어버렸거나 다른 보고서가 열림 | 편집기에서 `src/agent/.foundry/results/<실제 label>/evaluation.json`의 **`run → report_url`**을 복사해 엽니다. | URL을 다시 받으려고 `collect`·`evaluate`를 반복하지 않습니다. |
| 탭 이동 뒤 에이전트 버전이 달라 보임 | 의도한 버전을 다시 고르고 저장된 `prompt_version`과 대조합니다. | 저장된 응답 확인 없이 현재 탭만 믿지 않습니다. |
| 프로젝트 전역 **Evaluations**와 에이전트 상세 **Evaluation**이 다름 | README 단계가 지시한 목록을 엽니다. | 두 목록을 같은 것으로 보지 않습니다. |
| 버전 비교 위치를 찾기 어려움 | **Version 선택 상자 → Compare versions**에서 서로 다른 두 버전을 고르고 **Send**를 한 번만 누릅니다. | 에이전트의 **More** 메뉴를 쓰거나 양쪽 창을 따로 호출하지 않습니다. |
| Foundry **Indexes**가 비어 있음 | **Knowledge bases**의 source와 Azure Search index를 따로 확인합니다. | Foundry index 목록만 보고 검색 실패로 판단하지 않습니다. |
| **Monitor → Tools**가 비어 있음 | trace span을 엽니다. 코드 내부 IQ span은 보일 수 있습니다. | 포털 도구 목록으로 trace 증거를 대신하지 않습니다. |
| 오래된 trace가 보이지 않음 | 시간 범위를 넓힌 뒤 실제 trace ID로 찾습니다. | 임의 ID, 다른 에이전트 trace, 다른 언어 실행, 녹화나 예시 화면을 한국어 실행 증거로 대신하지 않습니다. |
| 구독 경보·정책 ARM 오류가 보임 | 모델 평가와 구분해 강사에게 확인합니다. | 예시 화면과 맞추려고 공유 구독 설정을 바꾸지 않습니다. |

배경 설명이 필요할 때만 [참고 설명](reference.ko.md), 권한·모델 준비가 필요할 때만 [강사 가이드](instructor.ko.md)를 봅니다.

**완료 확인:** 포털 화면이 내 실제 계정, 프로젝트, 에이전트 버전, 시간 범위, 저장된 `prompt_version` 또는 trace ID와 일치합니다.

**다르면:** 화면과 저장 결과 파일 경로를 보존해 강사에게 전달합니다. 공유 구독 설정을 바꾸지 않습니다.

**다음:** 중단했던 포털 확인으로 돌아가거나, 진행 중인 단계가 holdout이면 [holdout 결과 읽기](../README.ko.md#holdout-results)를 계속합니다.

<a id="levels"></a>

## 레벨 2·3 명령이 중단됐다면

먼저 원래 명령이 끝났는지 확인합니다.
평가 run 상태는 **`src/agent/.foundry/results/suite/`** 또는 **`src/agent/.foundry/results/level3/`**에 있습니다.
아래에서 정확한 메시지를 고릅니다.
이 복구는 5–9단계 증거와 소유권 기록을 바꾸지 않습니다. 별도 실험은 새 폴더에서 시작합니다.
낮은 유효 점수·공격 성공·`Quality gate FAILED`·`Composite gate FAILED`는 재시도 사유가 아닙니다. 같은 오류가 재발하면 강사에게 전달합니다.

가장 흔한 실패는 아래 표에서 바로 고릅니다.

| 메시지 또는 상황 | 다음 행동 |
|---|---|
| `... still running`, `... still generating`, `... still in progress`로 종료됨 | 같은 인자·label로 명령을 다시 실행해 저장된 run을 이어갑니다. `--retry-failed`나 파일 삭제는 필요 없습니다. |
| 터미널 닫힘·네트워크 시간 초과 | 원래 프로세스의 종료와 저장된 run 유무를 확인합니다. 기록이 있으면 같은 명령으로 상태를 조회·재개합니다. 기록이 없다면 중복 생성 여부를 강사와 확인하며 성공으로 간주하지 않습니다. |
| `... evaluator results failed, for example because the judge hit its rate limit` | `suite/<label>-output.json`의 실제 오류를 확인합니다. 속도 제한은 가능한 원인일 뿐입니다. 원인 해결 후 메시지의 `--retry-failed` 명령을 실행합니다. 실패한 run은 `suite.json`의 `attempts`에 남습니다. |
| `Suite run for ... ended as failed` | 원인을 해결한 뒤 같은 명령을 `--retry-failed`와 함께 실행합니다. |

위 표에 정확한 메시지가 없으면 아래 목록을 열고 같은 메시지의 행만 따릅니다.

<details>
<summary>그 밖의 레벨 2·3 메시지(위에 없는 정확한 메시지일 때만 열기)</summary>

행이 실패 출력의 명령을 따르라고 하면, 출력에 나온 `python scripts/workshop.py ...` 명령과 인자를 그대로 복사합니다. 인자를 새로 만들지 않습니다.

**Suite와 평가기 준비**

| 메시지 또는 상황 | 다음 행동 |
|---|---|
| `Run register-evaluators before evaluate-suite.` 또는 `Run evaluate-suite --labels ... first.` | 메시지가 가리키는 명령을 먼저 실행한 뒤 다시 실행합니다. |
| `Evaluator ... already exists and is not owned by this folder` | 내 소유로 기록되지 않은 평가기입니다. 강사와 충돌을 확인하며 지금 폴더의 `LAB_PREFIX` 변경·다른 평가기 삭제로 우회하지 않습니다. |
| `... was registered with a different definition` 또는 `The suite's evaluators changed ...` | 강사와 등록 당시 정의·현재 코드를 비교합니다. 확인된 원본에서만 복구하고, 등록된 평가기를 고쳐 맞추지 않습니다. |
| `Saved ... responses changed after their suite run was created` | 변경 파일과 검증된 원본을 강사와 대조합니다. 원본이 없으면 중단하며, 재수집·hash 편집으로 맞추지 않습니다. |
| `... rubric results failed`, `... stress-test results failed`, `... red-team results failed`, `The red-team scan returned incomplete results ...` | 원인을 해결한 뒤 [상태 파일 복구](#level-state-recovery)를 따릅니다. 낮은 점수와 실행 오류를 구분합니다. |
| `Comparison insight failed` 또는 `Cluster insight failed` | 1분 기다린 뒤 같은 명령을 실행합니다. 실패한 인사이트만 다시 만들고, 실패한 인사이트는 `insights.json`의 `failed_attempts`에 남습니다. |

**레벨 3 실행과 trace 평가**

| 메시지 또는 상황 | 다음 행동 |
|---|---|
| `Rubric generation ended as ...`, `The run ended as ...` | 실패 상태·오류를 강사와 확인합니다. 원인이 해결되고 메시지가 파일 삭제를 명시한 경우에만 [상태 파일 복구](#level-state-recovery)를 따릅니다. |
| `... already compares the rubrics on ...` 또는 `... already holds a ...-question run` | 저장된 run과 인자가 다릅니다. 메시지에 나온 기존 값으로 재개합니다. 다른 조건의 새 실험은 별도로 계획하며 기존 기록을 지우지 않습니다. |
| HTTP `429`(Too Many Requests) 오류 | `Retry-After`가 있으면 그만큼, 없으면 1분 기다립니다. 저장된 run 상태에 맞게 재개/실패 재시도를 고릅니다. `--count`는 늘리지 않습니다. |
| `This folder has no deployed hosted agent` | 강사와 원인을 확인합니다. 이미 정리했다면 4·6절은 **완료가 아닌 생략**으로 기록하고 재배포하지 않습니다. 실행하지 않은 절을 레벨 3 완료로 표시하지 않습니다. |
| `... agent calls or evaluator results failed` | 저장된 실제 오류가 있으면 해결한 뒤(오류 없이 한 평가기의 결과만 빠진 run도 있음) `python scripts/workshop.py evaluate-agent --split dev --retry-failed`를 실행합니다. 실패한 모델 run만 교체되고, 이전 run은 `attempts`에 남습니다. |
| `The <model> run ended as failed: ... Error code: 500` | 서비스 내부 오류입니다. 1분 기다린 뒤 `python scripts/workshop.py evaluate-agent --retry-failed`를 실행합니다. |
| `The <model> run ended as failed: ... Error code: 401 ... PermissionDenied` | 4절은 내 권한으로 Foundry 계정의 평가 API를 호출하므로 Foundry 계정 범위의 **Foundry User**가 필요합니다. 프로젝트 범위 할당만으로는 부족합니다([레벨 2·3 준비](instructor.ko.md#levels)). 환경 소유자가 역할을 부여하고 적용되면(최대 1시간) `python scripts/workshop.py evaluate-agent --split dev --retry-failed`를 실행합니다. |
| `evaluate-traces`가 `ApplicationInsightsAccessDenied` 같은 접근 오류로 끝남 | 강사가 [trace 접근 준비](instructor.ko.md#levels)를 마친 뒤 [상태 파일 복구](#level-state-recovery)를 따릅니다. |
| `... traces were not found ... evaluator results failed` | 누락 trace 수가 0보다 크면 반영·권한을 확인합니다. 누락 0건인데 평가 오류가 있으면 judge 오류를 확인합니다. 원인 해결 뒤 [상태 파일 복구](#level-state-recovery)를 따릅니다. |

**연속 평가와 포털 확인**

| 메시지 또는 상황 | 다음 행동 |
|---|---|
| `Schedule ... already exists and is not owned by this folder` | 내 소유로 기록되지 않은 일정입니다. 강사와 충돌을 확인하며 지금 `LAB_PREFIX`를 바꾸거나 그 일정을 삭제하지 않습니다. |
| `No scheduled run yet` | 연속 평가의 첫 실행은 출력된 시각에 시작합니다. 그 뒤에 `continuous-eval`을 다시 실행합니다. |
| 연속 평가가 `queued`·`in_progress`이거나, 실패했거나, trace가 0건임 | 대기 상태는 1분 뒤 같은 명령으로 조회합니다. 실패·0 trace는 미완료로 기록하고 트래픽·권한을 강사와 확인합니다. 일정 생성만으로 완료 처리하지 않습니다. |
| 연속 평가가 `completed`지만 평가 오류·빈 결과가 있음 | [행별 완료 기준](level-3.ko.md#continuous-eval)을 아직 충족하지 못했습니다. 미완료로 기록하고 원인을 확인합니다. 유효한 `passed: false`와 구분합니다. |
| 포털에서 `red-team` 스캔을 찾기 어려움 | New Foundry에서 **Evaluations → Red team** 탭을 열고 `<LAB_PREFIX>-red-team-sol`을 고릅니다. 비율은 **Overall metric results**에서 읽습니다. 목록의 **Issues in last run** 열은 성공한 공격 수가 아닙니다. |

</details>

**완료 확인:** 레벨 2·3 명령이 완료되거나 `suite/` 또는 `level3/` 아래에 정확한 실패 상태가 저장되어 있습니다.

**다르면:** 반복 실행을 멈추고 저장 상태와 원문 오류를 강사에게 전달합니다.

**다음:** 중단했던 레벨 2 또는 레벨 3 완료 확인으로 돌아가거나, 선택 과제를 마쳤다면 [10단계 정리](../README.ko.md#cleanup)로 진행합니다.



<a id="level-state-recovery"></a>

### 레벨 3에서 오류가 상태 파일 삭제를 명시한 경우에만

**대기·낮은 점수·label/질문 수 변경에는 사용하지 않습니다.** 실행 오류의 원인을 해결한 뒤, 오류 메시지가 삭제할 상태 파일을 명시했을 때만 사용합니다. 증거를 지우는 대신 그 파일을 보관 폴더로 옮겨 재시도를 가능하게 합니다.

**터미널 — 기존 실습 폴더의 저장소 루트:** 원래 명령이 끝났는지 확인합니다. 입력에는 **오류에 나온 파일 경로만** 붙여넣고, `Delete`·`and re-run` 같은 문구나 따옴표는 넣지 않습니다. 출력된 절대 경로와 `src/agent/...` 상대 경로 모두 됩니다. 블록은 **이 폴더의** `level3/` 안 rubric·stress·red-team·trace 상태 파일만 허용합니다. 에이전트·연속 평가 상태, 원문 출력, 다른 실습 폴더는 허용하지 않습니다.

```bash
read -r -p "State file named in the error: " STATE_FILE &&
python - "$STATE_FILE" <<'PY'
from pathlib import Path
import re
import shutil
import sys
import tempfile

root = Path("src/agent/.foundry/results/level3").resolve()
entered = Path(sys.argv[1])
state = entered.resolve()
allowed = r"(rubric-compare|(?:stress|red-team)-(?:sol|luna|astra)|traces-[a-z][a-z0-9-]{0,39})\.json"
if (entered.is_symlink() or state.parent != root or not state.is_file()
        or not re.fullmatch(allowed, state.name) or state.name.endswith("-output.json")):
    raise SystemExit("Stop: not an eligible state file in this workshop's level3 folder.")
raw = state.with_name(state.stem + "-output.json")
if raw.is_symlink() or (raw.exists() and not raw.is_file()):
    raise SystemExit("Stop: unexpected raw-output path; state was not moved.")
archive = Path(tempfile.mkdtemp(prefix="failed-attempt-", dir=root))
if raw.is_file():
    shutil.copy2(raw, archive / raw.name)
state.rename(archive / state.name)
print("Archived failed state:", archive / state.name)
PY
```

**완료 확인:** `Archived failed state:` 뒤에 새 경로가 나옵니다. 편집기에서 열어 실패한 run/job ID가 보존됐는지 확인합니다. 짝이 되는 원문 출력도 있다면 함께 복사됐습니다. 원래 상태 파일 하나만 이동했고 소유권·5–9단계 증거는 그대로입니다. 보관 폴더는 실습 폴더 안에 고유 이름으로 만들어져 다른 시도나 언어의 백업을 덮어쓰지 않습니다.

**다르면:** `Stop:`이면 정확한 오류의 경로와 지금 실습 폴더를 대조합니다. 복사·이동 오류이면 환경 소유자와 오류 및 남아 있는 파일을 확인합니다. 실패 상태가 안전하게 보관되기 전에는 파일을 지우거나 다음으로 진행하지 않습니다.

**다음:** 같은 명령·인자로 한 번만 재시도합니다. 새 호출에는 비용이 들 수 있습니다. 성공하면 해당 레벨 3 완료 확인으로 돌아가 다음 절을 이어갑니다. 같은 오류가 반복되거나 선택 실습을 중단하면 보관 파일을 유지하고 미완료 절을 기록한 뒤 [10단계 정리](../README.ko.md#cleanup)로 갑니다. 기존 소유권 기록은 그대로 쓰며, 이미 성공한 정리는 반복하지 않습니다.

<a id="cleanup-recovery"></a>

## 정리 또는 정리 확인이 중단됐다면

같은 폴더·계정·이름을 유지하고 원래 정리 프로세스가 종료됐는지 확인합니다. 정리 계획·결과는 `src/agent/.foundry/results/`, 소유권 기록은 `src/agent/.foundry/local-state.json`에 있습니다. 이 파일은 수정하지 않습니다.

| 어디까지 끝났나 | 다음 행동 |
|---|---|
| `cleanup --confirm` 성공, `cleanup.json`에 `completed: true`가 있지만 `check-cleanup` 실패 | **A: 확인만 재시도**. 성공한 삭제는 반복하지 않습니다. |
| 일부 삭제 뒤 실패했고 소유자가 원래 대상 전부와 남은 소유권 기록을 Azure 상태와 대조할 수 있음 | **B: 대조·승인된 나머지 삭제**. 재시도 전에 원래 계획을 보관합니다. |
| 소유권·대상·공유 의존성·삭제 결과가 불명확함 | 자동 삭제 중단. 오류·계획·소유권 기록을 소유자에게 전달합니다. 완료 파일을 만들려고 기록을 고치거나 B를 실행하지 않습니다. |

**A — 삭제 명령은 성공했고 확인만 실패:** 완료 파일과 `plan`을 보존하고 접근·반영 지연 문제를 해결한 뒤 아래 확인만 실행합니다.

```bash
python scripts/workshop.py check-cleanup
```

[10-3의 완료 기준](../README.ko.md#cleanup-check)을 확인합니다. 대상이 남아 있거나 보존할 서비스가 없다면 보고하며 완료로 처리하지 않습니다. `cleanup --confirm`을 반복하면 원래 삭제를 검증하는 대신 **남은 소유 대상 기준으로 계획이 교체**됩니다. B로 넘어가 이 확인을 우회하지 않습니다.

<a id="partial-cleanup"></a>

**B — 소유자가 대조·승인한 부분 삭제 이어가기**

1. **편집기:** `results/` 아래 아직 쓰지 않은 보관 폴더에 원래 `cleanup-plan.json`, 위 위치의 `local-state.json`, 있다면 `cleanup.json`·`cleanup-check.json`을 복사합니다. 오류·보관 경로도 기록합니다. 활성 파일을 옮기거나 편집하거나 이전 보관본을 덮어쓰지 않습니다.
2. **환경 소유자:** 원래 계획의 모든 대상이 Azure에서 이미 삭제됐는지 아직 남았는지 기록합니다. 남은 소유권 기록과 일치해야 합니다. 삭제된 대상이 소유 기록에 남거나, 공유 Search/planner 역할·다른 소유자·불명확한 결과가 있으면 멈춥니다. 기록을 고쳐 맞추지 않습니다.
3. **터미널 — 남은 계획만 확인:**

```bash
python scripts/workshop.py cleanup --dry-run
```

**완료 확인:** 원래 보관 계획에 있던, 아직 남아 있는 본인 전용 대상만 나옵니다. 새 대상·공유 의존성이 없고 소유자가 이 나머지 계획을 승인했습니다. 빈 목록만으로 원래 대상의 삭제를 증명하지는 못합니다.

**다르면:** 추가 삭제를 멈추고 소유자에게 차이를 전달합니다.

**터미널 — 위 대조·별도 승인을 마친 경우에만:**

```bash
python scripts/workshop.py cleanup --confirm
```

**완료 확인:** `Owned workshop resources removed; shared infrastructure and evidence preserved.`로 끝납니다.

**다르면:** 두 시도의 기록을 모두 보존하고 멈춥니다. 자동 반복하지 않습니다.

**터미널 — 나머지 삭제가 성공한 뒤:**

```bash
python scripts/workshop.py check-cleanup
```

**완료 확인:** [10-3의 값](../README.ko.md#cleanup-check)은 **재개한 계획**과 맞고, 앞선 시도에서 삭제한 대상도 모두 없음을 소유자가 확인했습니다. 마지막 확인은 최신 계획만 검사하므로 줄어든 개수를 원래 전체 계획의 검증으로 보고하지 않습니다. 두 시도의 증거를 보고서와 함께 보관합니다.

**다르면:** 확인 결과와 원래 계획을 소유자에게 전달하며 추가 삭제하지 않습니다.

**다음:** A 또는 B의 확인을 마치면 기본 정리는 끝났습니다. 본인 전용 환경을 종료하려면 [생성 기록과 삭제 범위 확인](environment.ko.md#final-cleanup)을 따릅니다. 별도 승인으로 그룹 전체를 삭제한 뒤에는 `check-cleanup`이 아니라 [기반 환경의 최종 확인](environment.ko.md#final-cleanup-check)을 사용합니다. 공유 그룹 삭제로 우회하지 않습니다.

<a id="setup-resume"></a>
<a id="환경-소유자-터미널을-닫은-뒤-준비-이어가기"></a>

## 환경 소유자: 미완료 준비 이어가기

**참가자는 환경 준비 중이 아니었다면 여기서 멈춥니다.** 원래 clone과 `RUN_DIR`를 유지하고, 새 `RUN_ID` 생성·이미 완료한 `init` 반복·스냅샷 덮어쓰기는 하지 않습니다.

**터미널 — 기존 경로 확인:** `bash`를 실행하고 원래 clone 경로와 기존 `RUN_DIR`를 따옴표 없이 입력합니다.

```bash
read -r -p "환경 준비에 사용한 원래 clone의 절대 경로: " REPO_ROOT &&
cd "$REPO_ROOT" &&
read -r -p "기존 RUN_DIR의 절대 경로: " RUN_DIR &&
printf 'RUN_DIR=%s\n' "$RUN_DIR"
```

**완료 확인:** 원래 clone으로 이동했고 출력 경로가 메모한 `RUN_DIR`와 같습니다. 편집기에서 아래 표에 맞는 파일 상태를 고릅니다. `config.json`이 있다면 `workspace`가 이 `RUN_DIR` 아래의 `workshop`인지 먼저 확인합니다.

**다르면:** 메모한 두 경로를 다시 확인합니다. 경로가 불명확하거나 다른 실행이면 기록을 새로 만들거나 덮어쓰지 않습니다.

| 남아 있는 파일 / 완료한 작업 | 다음 행동 |
|---|---|
| `init`가 입력 검증에서 실패했고 `RUN_DIR` 자체가 없음 | [초기 설정 수정 후 같은 `init`만 재시도](#setup-init-retry)합니다. 새 실행 ID는 만들지 않습니다. |
| `RUN_DIR`는 있지만 `config.json`이 없음 | 부분 생성 상태입니다. 폴더·오류를 보존해 준비 담당자에게 전달합니다. `init` 재시도 대상이 아닙니다. |
| `config.json`만 있고 `workshop/` 없음 | 원래 clone에서 `source src/agent/.venv/bin/activate`를 실행합니다. 이 `RUN_DIR`로 [`prepare` 명령만](environment.ko.md#setup-snapshot) 실행한 뒤 Python 준비로 갑니다. |
| `workshop/`은 있고 `source-manifest.json` 없음 | 소스 복사가 중단됐습니다. 폴더와 오류를 보존하고, 폴더를 지우거나 manifest를 만들지 않습니다. |
| 스냅샷·manifest는 있고 Python·테스트 미완료 | `"$RUN_DIR/workshop"`에서 [독립 Python 준비](environment.ko.md#setup-python)를 이어가고, 로그인 전에 `OK`를 확인합니다. |
| 스냅샷·Python·테스트 완료 | 아래에서 실행 폴더를 복원한 뒤 중단한 Azure 단계를 고릅니다. |

**터미널 — 스냅샷과 Python 테스트가 완료된 경우에만:**

```bash
cd "$RUN_DIR/workshop" &&
source src/agent/.venv/bin/activate &&
export AZURE_CONFIG_DIR="$PWD/.azure-cli"
```

**완료 확인:** 가상환경과 CLI 프로필이 기존 실행 폴더를 가리키며 새 소스·Azure 환경을 만들지 않았습니다.

**다르면:** 경로 오류이면 위 `config.json`의 `workspace`와 대조합니다. 가상환경이 없다면 위 표의 Python·테스트 미완료 행을 따릅니다.

**여러 명령이 `&&`로 연결된 블록이 실패했나요?** 실패한 명령 뒤의 명령들은 실행되지 않았습니다. 원인을 해결한 뒤 **실패한 줄부터 블록 끝까지** 순서대로 이어갑니다. 한 줄씩 실행할 때는 줄 끝의 `&&`를 뺍니다. 이미 성공한 앞부분은 반복하지 않습니다.

| 중단한 준비 단계 | 이어갈 위치 |
|---|---|
| 로그인 | [환경 준비 2-1](environment.ko.md#setup-identity)의 미완료 로그인부터 이어갑니다. 이미 성공한 로그인은 반복하지 않습니다. |
| 환경 준비 2–5단계 서비스 생성 | `cd "$REPO_ROOT"`, `AZURE_CONFIG_DIR` 유지, [중단한 단계](environment.ko.md#setup-route)의 실패한 명령과 그 뒤 미실행 명령을 같은 `--run-dir "$RUN_DIR"`로 실행 |
| 환경 준비 6단계 후보 모델 준비 | `"$RUN_DIR/workshop"`에서 [6단계](environment.ko.md#setup-candidates)의 실패 명령부터 재개 |
| 후보 준비 완료, calibration만 미완료 | 같은 실행 폴더에서 [judge 점검](environment.ko.md#setup-calibration)부터 재개. `prepare-models`는 반복하지 않음 |
| 환경 준비 완료 | [전달 경로](environment.ko.md#handoff)를 선택. 준비를 반복하지 않음 |

로그인이 만료됐다면 설정된 계정으로 복구하며 다른 계정·새 이름·소유권 삭제로 우회하지 않습니다.

**완료 확인:** 원래 실행 폴더, `RUN_DIR`, 가상환경, `AZURE_CONFIG_DIR`가 복원됐고 중단한 단계만 선택했습니다.

**다르면:** `config.json`, `RUN_DIR`, 마지막 오류를 보존합니다. 혼자라면 본인이 환경 소유자이므로 `config.json`의 `subscription`·`run_id`가 이번 실행과 같은지 대조한 뒤 같은 `RUN_DIR`로만 재개합니다. 새 `RUN_ID`를 만들거나 스냅샷을 덮어쓰지 않습니다.

**다음:** 위 표의 해당 환경 준비 단계로 돌아가거나, 전달까지 끝났다면 [README bind](../README.ko.md#bind-project)로 진행합니다.

<a id="setup-init-retry"></a>

## `init`가 기록 생성 전에 실패했다면

**이 분기는 초기 입력 검증 실패로 기록한 `RUN_DIR` 자체가 아직 없을 때만 씁니다.** 먼저 [기존 경로 확인](#setup-resume)으로 `REPO_ROOT`·`RUN_DIR`를 복원합니다. 원래 clone의 `.env`에서 [초기 다섯 설정](environment.ko.md#initial-settings)을 수정·저장합니다. 시각으로 새 `RUN_ID`를 만드는 전체 블록은 반복하지 않습니다.

**터미널 — 원래 clone (`$REPO_ROOT`), 같은 `RUN_DIR`:**

```bash
if [ -e "$RUN_DIR" ] || [ -L "$RUN_DIR" ]; then
  printf '%s\n' 'Stop: RUN_DIR already exists; preserve it and use saved-state recovery.' >&2
  false
else
  source src/agent/.venv/bin/activate &&
  python scripts/prepare_environment.py init --run-dir "$RUN_DIR" --language ko
fi
```

**완료 확인:** 출력 JSON이 `language: ko`이고 같은 `RUN_DIR`에 `config.json`이 생겼습니다. 이제 [1-5 소스 복사](environment.ko.md#setup-snapshot)로 갑니다.

**다르면:** 오류와 경로를 보존합니다. 폴더가 이미 있으면 [저장 상태별 표](#setup-resume)로 돌아가며, 없는 파일을 직접 만들거나 폴더를 삭제하지 않습니다.
