# 강사 준비: 120분 실습의 시작 조건

[한국어 실습](../README.ko.md) · [English](instructor.en.md)

새 그룹부터 준비하는 명령과 화면은 [새 Azure 환경 가이드](environment.ko.md)에 있다. 수업에서 결과를 설명할 때는 [평가 방법과 개선 결과](validation.ko.md)를 사용한다.

이 문서는 참가자 120분에 포함하지 않는 **환경 준비**다. 빈 Azure 구독에서의 전체 소요 시간은 모델 접근 승인·할당량·권한 전파에 따라 달라진다.

**혼자 실습한다면:** 여기서 “강사”는 환경 소유자를 뜻하며 본인이 맡아도 된다. 준비를 한 번 마친 뒤 참가자 경로로 진행한다. 다만 승인된 구독·모델 접근·용량·아래 권한이 필요하며 문서가 이를 대신 부여하지는 않는다.

**준비 순서:** [도구](#tools) → [권한](#access) → 아래 환경 경로 선택 → [분리된 리허설](#rehearsal-workspace) → [조별 전달](#handoff).

| Azure 기반 서비스 | 준비 경로 |
|---|---|
| Foundry·Search·연결된 관측 서비스가 준비되지 않음 | [전용 새 환경 생성](environment.ko.md). 두 준비 경로를 모두 실행하지 않는다. |
| 위 서비스는 있고 모델·권한 점검이 필요함 | [기존 환경으로 준비](#existing-foundation) |

<a id="tools"></a>

## 로컬 도구 설치와 확인

**여기는 직접 실행할 때도 필요한 기본 환경이다.** GHCP에 환경 생성·실습 실행을 맡기는 추가 도구와 설정은 [별도 GHCP 안내](copilot.ko.md)를 따른다. GHCP·Node.js·Playwright를 기본 실습의 필수 도구로 혼동하지 않는다.

| 도구 | 설치 안내 / 확인 조건 |
|---|---|
| Git | [Git 설치](https://git-scm.com/downloads) |
| Python | [Python 설치](https://www.python.org/downloads/)에서 **3.13.x** 선택. 실습 터미널에서 `python3.13` 실행 가능 |
| Azure CLI | [Azure CLI 설치](https://learn.microsoft.com/cli/azure/install-azure-cli) |
| azd | [Azure Developer CLI 설치](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd) |
| Bash | macOS 기본 제공. Linux/WSL에서는 배포판 패키지로 설치하며 아래 Ubuntu 예시 참고. [GNU Bash](https://www.gnu.org/software/bash/) |
| curl | macOS 기본 제공. Linux/WSL에서 없으면 아래 예시 또는 [배포판별 curl 다운로드](https://curl.se/download.html) 참고 |
| 편집기 | [VS Code 설치](https://code.visualstudio.com/download) 또는 기존 텍스트 편집기. `.env`·JSON을 열 수 있으면 됨 |
| 브라우저 | [Edge 설치](https://www.microsoft.com/edge/download) 또는 [Chrome 설치](https://www.google.com/chrome/). 로그인·Foundry 포털 확인에 사용 |
| Windows 터미널 | [WSL 설치](https://learn.microsoft.com/windows/wsl/install). Windows에만 설치하지 말고 **WSL 안에 Linux용 도구도 설치** |

macOS/Linux는 Bash(`bash`), Windows는 WSL의 Bash를 사용한다. 수동 포털 확인용 브라우저와 편집기는 Windows 쪽 앱을 사용해도 된다. CLI 도구는 실습을 실행할 WSL 안에서 확인한다.

먼저 Bash와 curl을 확인한다.

```bash
bash --version &&
curl --version
```

Ubuntu/WSL에서 명령이 없다면 `sudo apt-get update` 후 **없는 도구의 행만** 실행한다. 설치 승인은 사용자 터미널에서 처리하고 암호를 채팅에 전달하지 않는다.

| 없는 도구 | 설치 명령 |
|---|---|
| Bash | `sudo apt-get install bash` |
| curl | `sudo apt-get install curl` |

macOS에서 기본 명령을 찾지 못하면 `/bin/bash`, `/usr/bin/curl`과 PATH를 먼저 확인한다. 다른 Linux 배포판은 해당 배포판의 패키지 관리자를 사용한다. 설치 후 위 버전 확인을 반복한다.

그다음 나머지 CLI 도구를 확인한다. Python 패키지 설치는 [README 1-2](../README.ko.md#1-2-가상환경과-로컬-테스트)에서 수행한다.

```bash
git --version &&
python3.13 --version &&
az version &&
azd version &&
azd extension list
```

없는 명령이 있으면 해당 도구를 설치하고 다시 확인한다. `microsoft.foundry`에 **설치된 버전이 없을 때만** 한 번 설치한다.

```bash
azd extension install microsoft.foundry
```

이어서 agent 명령이 제공되는지 확인한다.

```bash
azd ai agent --help
```

명령 목록에 `run`, `invoke`가 있어야 한다. 업데이트 안내 자체를 현재 명령의 실패로 보지 않으며, 실험 중 “모두 업데이트”나 임의 다운그레이드를 하지 않는다. 설치된 명령이 실패하면 호환되는 azd/확장 조합을 먼저 해결한다.

**도구 확인을 마쳤다면 맞는 경로 하나로 이동한다.** 아래 강사 준비 전체를 모든 참가자가 수행할 필요는 없다.

| 진행 방식 | 다음으로 갈 곳 |
|---|---|
| 준비된 환경에서 직접 실습 | [README 1단계](../README.ko.md#start) |
| GHCP에 실행을 맡김 | [GHCP 설치·시작 안내](copilot.ko.md#install). 기본 도구 설치는 반복하지 않음 |
| 환경 소유자가 직접 Azure 준비 | [권한](#access) 확인 후 새 환경 / 기존 환경 경로 선택 |

<a id="handoff"></a>

## 참가자에게 전달할 것

**리허설을 마친 뒤** 이 체크리스트로 전달한다. 참가자는 [README의 1–10단계](../README.ko.md#start)만 따라간다. 녹화 제작이나 Azure 인프라 생성 절차를 참가자의 선행 과제로 섞지 않는다.

| 전달 항목 | 강사가 확인할 내용 |
|---|---|
| 실행 가능한 계정 | 참가자 계정의 조회·배포 권한. 실제 CLI 로그인은 참가자가 README 1-3에서 수행 |
| 조별 `.env` | `.env.example`의 모든 값을 채움. 한국어는 `LAB_LANGUAGE=ko`, 영어는 `en`. 암호·API key·token은 없음 |
| 준비된 서비스 | Foundry 프로젝트, Search, 연결된 App Insights, 네 후보와 별도 planner/judge |
| 고유한 이름 | 참가자가 아직 사용하지 않은 `LAB_PREFIX`, `LAB_AGENT_NAME` |
| 준비된 도구 | [기본 도구 설치·확인](#tools) 통과. GHCP 사용 시 [추가 준비](copilot.ko.md)는 별도 수행 |
| 도움받을 담당자 | `grant-agent-access` 역할 부여·403·quota 오류를 처리할 담당자 |

**중요:** `.env`만 전달한 새 clone에는 로컬 azd 환경이 없다. 참가자는 README 1단계의 **`bind`를 자기 폴더에서 실행**한다. 강사 PC에서 바인딩했다는 이유로 이 단계를 생략하지 않는다.

<a id="rehearsal-workspace"></a>
<a id="리허설과-참가자-실행을-분리"></a>

## 모델 준비·리허설·참가자 실행을 분리

**수업용 모델의 소유권은 준비 폴더에 남긴다.** 그 폴더에서 전체 실습을 리허설하면 10단계 cleanup이 참가자에게 공유할 모델까지 삭제할 수 있다.

모델 준비가 끝나면 별도 리허설 clone을 만든다. 아래 폴더가 이미 있으면 다른 미사용 이름을 쓰며 기존 폴더를 지우지 않는다.

```bash
git clone https://github.com/junwoojeong100/foundry-evaluation.git foundry-evaluation-rehearsal-ko &&
cd foundry-evaluation-rehearsal-ko
```

편집기로 **완성된 `.env`만** 이 clone에 복사한다. `LAB_LANGUAGE=ko`와 실제 프로젝트·endpoint·모델 배포 이름은 유지하고, **`LAB_PREFIX`와 `LAB_AGENT_NAME`만 미사용 리허설 이름**으로 바꾼다. 이후 [README 1–10단계](../README.ko.md#start)를 따르되 이미 clone했으므로 clone 블록은 건너뛴다.

참가자 이름은 또 별도로 예약한다. 참가자의 접두사로 KB·source·index·agent를 미리 만들면 새 폴더의 소유권 검사에서 덮어쓰기를 거부할 수 있다.

준비된 모델을 공유하는 경우 `.env`의 `MODEL_*_DEPLOYMENT`에는 그 **실제 배포 이름**을 유지한다. 바꾸는 것은 조별 지식 객체·agent 이름이며, 모델을 임의로 교체하지 않는다.
다른 사람의 `.azure`, `.foundry` 소유권 파일, 실행 결과나 인증 저장소를 복사해서 오류를 우회하지 않는다.
언어별 실습도 폴더·접두사·agent 이름을 분리한다. 영어 자료는 `data/en/`과 `src/agent/prompts/en/`에 있으며, 실행기는 다른 언어의 소유권·응답·평가·회귀 데이터를 섞는 것을 거부한다.

참가자의 `cleanup`은 **그 폴더에 생성 기록이 있는 대상만** 정리한다. 강사가 미리 준비한 모델·기반 서비스의 최종 비용과 정리는 강사가 따로 관리한다.

**리허설 정리 후, 전달 전에:** 모델 준비 폴더와 그 CLI 프로필로 돌아와 `python scripts/workshop.py preflight`를 실행한다. 네 배포와 `missing_models: []`를 확인하며, 모델이 없으면 전달을 멈추고 준비부터 복구한다. 참가자가 사용 중인 준비 폴더의 모델은 정리하지 않는다.

아래 [리허설 시간표](#rehearsal)를 사용한다. **이후 참가자가 없는 일회성 개인 실습**이라면 준비 폴더를 계속 사용해도 되며, 그 경우 소유한 모델의 정리는 의도된 동작이다.

## 사전 준비

| 항목 | 준비 상태 |
|---|---|
| Azure 구독 | 실습용 구독과 tenant를 명시적으로 선택 |
| Foundry | `Microsoft.CognitiveServices/accounts/projects` 유형의 프로젝트 |
| 지역 | Hosted Agent와 네 모델을 실제로 사용할 수 있는 지역 |
| 모델 | Sol/Terra/Luna/Astra의 실제 배포 + 고정된 보조 planner/judge |
| Search | semantic/agentic retrieval 지원, system-assigned identity, Entra RBAC |
| 관측 | 프로젝트에 연결된 Application Insights와 Logs 조회 권한 |
| 로컬 | Python 3.13, Azure CLI, azd, `microsoft.foundry` 확장 |
| 인증 | 참가자가 README 1-3에서 두 CLI에 로그인하고 MFA를 완료할 수 있음 |
| 데이터 | 합성 문서만 사용, 실습 접두사는 조마다 다름 |

도구 설치는 [azd 설치](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd), [Hosted Agent quickstart](https://learn.microsoft.com/azure/foundry/agents/quickstarts/quickstart-hosted-agent)를 따른다. agent hosting과 SDK 패키지의 GA/preview 상태를 혼동하지 않는다.

<a id="access"></a>

## 권한

환경 소유자는 새 그룹·자원을 만들고 아래 역할을 해당 범위에 부여할 수 있어야 한다. **Contributor만으로는 역할 부여 권한**(`Microsoft.Authorization/roleAssignments/write`)이 생기지 않으므로 승인된 접근 관리자가 권한을 준비하거나 해당 작업을 수행해야 한다. 이를 해결하려고 agent에 관리자/Owner 권한을 주지 않는다. 역할 부여 권한이 없는 참가자는 `prepare-iq`, `grant-agent-access`에서 환경 소유자의 지원이 필요하다.

| 주체 | 최소 업무 권한 | 범위 |
|---|---|---|
| 참가자 | Foundry User + 필요한 개발/배포 권한 | 실습 Foundry 프로젝트/계정 |
| 준비 담당자 | 모델 배포·Search schema 생성 권한 | 실습 리소스 |
| 문서 적재 담당자 | Search Service Contributor, Search Index Data Contributor | 실습 Search |
| Search managed identity | Cognitive Services User | planner 모델이 있는 Foundry 계정 |
| Agent instance identity | Search Index Data Reader, Cognitive Services OpenAI User | 실습 Search, 네 후보 모델이 있는 Foundry 계정 |
| 관측 담당자 | Log Analytics Reader 등 필요한 Logs 권한 | App Insights/연결 workspace |

Foundry 역할의 이전 이름인 Azure AI User 등이 UI에 남아 있을 수 있다. 역할의 이름만 보고 Owner를 일괄 부여하지 않는다. 기존 역할이 충분하면 추가하지 않는다.

이 실습은 조 전체가 볼 수 있는 합성 문서를 공유한다. 실제 다중 사용자 제품은 문서별 권한, tenant 격리, on-behalf-of/호출자 신원 전달을 별도로 구현해야 한다. Search 읽기 역할만으로 사용자별 문서 필터링이 자동 완성되지는 않는다.

최종 계정 endpoint 추론 경로는 agent에 프로젝트의 `Foundry User`나 Owner를 부여하지 않는다. 사용자/준비 담당자의 Foundry 역할과 agent identity의 두 데이터 접근 역할을 구분한다. 진단 중 시험한 추가 역할은 검증 환경 정리 시 함께 제거한다.

<a id="existing-foundation"></a>

## 로컬 설치와 테스트

기반 서비스가 이미 있는 경우의 준비 경로다. 새 환경 가이드를 완료했다면 그 문서의 전달 안내를 따르며 이 준비를 반복하지 않는다.

미사용 clone을 **모델 준비 폴더**로 쓴다. 필요하면 [README 1-1의 clone 블록](../README.ko.md#source-setup)만 실행하고 돌아온다. 이 폴더의 루트에서 실행하며, **마지막에 `OK`가 나온 뒤에만** 아래 Azure 준비로 넘어간다.

```bash
python3.13 -m venv src/agent/.venv &&
source src/agent/.venv/bin/activate &&
python -m pip install -r requirements.txt &&
python -m unittest discover -s tests -v
```

프레임워크와 Foundry SDK의 버전 상한이 다를 수 있다. Agent Framework Foundry 1.11.0, core 1.16.0, OpenAI adapter 1.14.1, Azure AI Projects 2.3.0, Agent Server Invocations 1.1.0을 고정했다. 무조건 모든 패키지를 최신 버전으로 올리지 않는다. `requirements.lock.txt`는 검증 환경의 전체 의존성 스냅샷이다. 같은 Python 환경을 재현할 때 `python -m pip install -r requirements.lock.txt`를 사용할 수 있다.

## 설정과 안전한 준비

1. `.env.example`을 참고해 이 폴더의 `.env`에 **`LAB_LANGUAGE=ko`, 미사용 준비용 이름, 실제 자원·모델 배포 값**을 채운다. 기존 파일은 덮어쓰지 않는다.
2. 테스트가 `OK`인 같은 폴더에서 [README 1-3 로그인](../README.ko.md#login)을 실행한다. 실습용 CLI 경로를 지정하고 두 CLI에 로그인한 뒤, 계정·tenant·구독·인증 상태를 대조한다. 다른 작업의 기본 CLI 구독은 바꾸지 않는다.
3. `python scripts/workshop.py preflight --allow-missing-models`로 환경과 네 모델의 지역별 지원·할당량을 읽기 전용 확인한다.
4. 모델이 없다면 `python scripts/workshop.py prepare-models`로 **고유 접두사**를 가진 네 배포만 만든다.
5. `python scripts/workshop.py preflight`를 다시 실행해 `language: ko`, `missing_models: []`를 확인한다.
6. `python scripts/workshop.py calibrate`의 **`Judge calibration passed`**를 확인한다. 참가자 README 5단계에서도 점검하며, 같은 입력의 완료된 calibration은 재사용한다. 예제 2건은 네 모델의 본평가 64응답에 포함하지 않는다.
7. 수업 준비라면 [별도 리허설 폴더](#rehearsal-workspace)를 거쳐 참가자에게 전달한다. 일회성 개인 실습이라면 이 폴더에서 [README 1-4](../README.ko.md#project-binding)로 이어간다. 순서는 bind → IQ 검색 → 로컬 smoke → 배포·권한 부여 → 원격 smoke다. 두 경로를 모두 실행하지 않는다.

평가가 `AppInsights connection is missing ResourceId metadata`로 실패하면 강사가 연결의 소유권과 범위를 먼저 확인한다. **공유 연결은 참가자가 직접 변경하지 않는다.** 수정이 허용된 실습 전용 연결에만 `python scripts/workshop.py repair-observability --confirm`으로 실제 Application Insights ARM ID 메타데이터를 추가한다. target/credential은 변경하지 않으며 보완 기록은 cleanup 후에도 유지된다. 이후 `calibrate --retry-failed`로 실패 run을 보존한 채 새 run을 만든다.

모델은 `GlobalStandard` 사용량 기반 배포를 사용한다. PTU를 예약하거나 할당량 증설을 자동 신청하지 않는다. 실제 모델/SKU/할당량 검사를 통과하지 못하면 강사가 먼저 해결한다.

<a id="azd-초기화"></a>

<details>
<summary>bind가 하는 일 — 추가로 실행할 단계가 아닌 참고 설명</summary>

이 저장소에는 실습 전용 `azure.yaml`과 소스가 제공된다. `bind`는 기존 프로젝트의 ARM ID와 실제 보조 모델 deployment name을 사용해 지금 폴더의 azd 환경을 만들거나 재사용한다.

제공된 `azure.yaml`을 다시 init하여 `-2` agent를 만들지 않는다. `bind`가 service key와 agent name을 조별 이름으로 맞추며, 구독·프로젝트 충돌이 있으면 중단한다. `src/agent` 경로, `invocations` protocol, Python 3.13 code deployment도 확인한다.

기존 Foundry 프로젝트 전체를 재프로비저닝하지 않는다. 기존 모델 배포·지식 객체·에이전트를 임의로 수정하지 않는다. 새로 만든 것의 정확한 이름과 ID는 `.foundry` 상태에 기록한다.

로컬 서버는 신뢰할 수 있는 개발 환경에서만 잠깐 실행하고 즉시 종료한다. 공개망에 노출하지 않는다. 로컬 테스트 서버와 Azure 플랫폼이 인증을 처리하는 hosted endpoint는 서로 다른 보안 경계다.

</details>

<a id="rehearsal"></a>

## 실습 시간 리허설

| 시간 | 참가자 단계 | 확인할 결과 |
|---|---|---|
| 00–10분 | 1. 시작 준비 | 테스트·두 CLI 로그인·계정 확인·preflight·bind |
| 10–25분 | 2. 지식 검색 | 실제 IQ 문서 ID와 activity |
| 25–40분 | 3–4. 로컬·배포 | 로컬과 원격의 실제 응답 |
| 40–55분 | 5. Baseline | dev 24행과 Foundry 평가 |
| 55–70분 | 6. 사례 검토 | 실제 trace와 검토된 회귀 데이터 |
| 70–85분 | 7. V2 재평가 | 새 버전·같은 dev 24행 |
| 85–100분 | 8. Holdout | 고정 후보의 16행 |
| 100–110분 | 9. 운영·검증 | 64응답·64trace·lineage |
| 110–115분 | 10. 정리 | 소유 대상만 정리 |
| 115–120분 | 버퍼 | 비동기 평가·telemetry 반영 |

한 조의 전체 실행을 사전 리허설한다. 특히 다음 대기 시간을 측정한다.

- 모델·agent 배포 및 첫 호출의 cold start.
- Search index 반영과 RBAC 전파.
- dev 24행 생성과 Foundry evaluator 완료.
- Application Insights에 trace가 실제 조회되기까지의 지연.

기준 시간표를 넘으면 **참가자 시작 전에** 모델 용량·동시성·준비 상태를 조정한다. 실습 중 지식 검색·평가·네 모델 중 일부를 빼고 완료로 처리하지 않는다.

## 운영 확장 범위

2시간 뒤에 확장할 수 있는 주제는 continuous evaluation, 알림, CI/CD quality gate, prompt optimizer, fine-tuning/RL, 여러 공급자의 모델, 사용자별 문서 권한이다. 이번 실습의 “사람이 검토한 회귀 데이터 → 개선 후보 → holdout” 통제 구조를 유지하면서 추가한다.

## 정리 원칙

공유 resource group 전체를 삭제하지 않는다. `cleanup --dry-run`으로 소유권 기록과 정확한 이름을 먼저 보고 `--confirm`으로 실습 자원만 정리한다. 기존 Search 서비스와 Foundry 프로젝트는 계속 비용이 발생할 수 있으므로 환경 소유자가 별도로 관리한다.

## 실습 파일을 수정할 때

Foundry 에이전트를 수정하거나 설명하기 전에 `microsoft-foundry` 스킬의 지침을 확인한다.
합성 데이터만 사용하며 공유 Azure 자원과 기본 CLI 구독은 변경하지 않는다. Azure 명령에는 구성된 구독을 명시한다.
모델·지침·데이터셋·trace의 연결 관계를 보존하고, 다른 모델로 대체하거나 누락·오류 행을 성공으로 집계하지 않는다.
문서의 명령은 실제 코드와 일치해야 하며, Azure 실행 전에 [로컬 테스트](#로컬-설치와-테스트)를 통과시킨다.
실제 cloud 실행 결과는 [평가 방법과 개선 결과](validation.ko.md)에 별도로 구분한다.
