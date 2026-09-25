# 강사 준비: 120분 실습의 시작 조건

[한국어 실습](../README.ko.md) · [English](instructor.en.md)

**완료 후 남길 것:** 준비된 Azure 서비스와 모델 배포, 완성된 조별 `.env`, 리허설까지 검증된 참가자 진행 경로. 모두 **참가자 120분 실습 시간 외에** 준비한다.

**대상:** 개인 실습 학습자를 포함한 환경 소유자다. 혼자 실습하면 “강사”는 본인을 뜻한다. 완성된 환경을 받은 참가자는 [README 1단계](../README.ko.md#start)로 간다.

**필요한 것:** 승인된 구독, 모델 접근과 용량, [아래 권한](#access), 예산. 준비와 리허설은 유료 Azure 리소스(모델 배포, Search, 로깅)를 만들고 호출한다. [예산 계획표](#budget)의 기록된 한 조 기준 토큰 비용은 기본 실습 약 $0.60, 레벨 2·3 포함 최대 약 $25.49이며, hosted 에이전트 컴퓨팅과 공유 비용은 별도다.

**진행 순서:**

1. **도구와 권한:** [로컬 도구를 설치](#tools)한 뒤 [권한](#access)을 확인한다.
2. **기반 환경:** Foundry·Search·telemetry 중 하나라도 없으면 [전용 새 환경 생성](environment.ko.md)을 마치고, 셋 다 있으면 [기존 환경으로 준비](#existing-foundation)한다.
3. <a id="after-calibration"></a>**judge calibration을 통과하면 운영 경로를 하나 고른다:**
   - **수업 운영:** [리허설 clone](#rehearsal-workspace)에서 README 1–9단계를 끝낸다. 레벨 2·3을 가르치면 [레벨 2·3](#levels)을 리허설한다. 리허설 clone에서 README 10단계를 실행한 뒤 [전달 전 최종 모델 확인](#final-model-check) → [시간표](#rehearsal) → [조별 전달](#handoff)로 간다. 수업 후 [정리](#정리-원칙)를 한다.
   - **개인 실습:** 같은 폴더에서 README [`bind` 명령](../README.ko.md#bind-project)으로 돌아간다.

**시작:** [로컬 도구 설치와 확인](#tools)

<a id="budget"></a>

<details>
<summary>예산 계획표: 조별 호출량과 비용 예시</summary>

가격은 지역과 시점에 따라 다르므로 아래 호출량을 [Azure 가격 계산기](https://azure.microsoft.com/pricing/calculator/)로 계산하고, [Cost Management](https://learn.microsoft.com/azure/cost-management-billing/costs/tutorial-acm-create-budgets)에서 리소스 그룹에 예산 알림을 설정한 뒤, 리허설 후 실제 비용과 비교한다.

| 조별 | 기본 실습 | 레벨 2 | 레벨 3 |
|---|---|---|---|
| 에이전트 답변(답변마다 Foundry IQ 검색 1회와 후보 모델 호출 1회) | 평가 48 + smoke 3 | 없음 | 18(4절) |
| Sol 직접 호출 | 없음 | 없음 | 스트레스 테스트 답변 15 + red team 공격 6 |
| 보조 배포의 LLM judge 결과 | 96 + calibration 4 | 252 + 실패 클러스터링 작업 1회 | rubric 36 + 스트레스 30 + 에이전트 54 + trace 54 + 연속 평가 최대 320, 그리고 rubric·질문 생성 |
| 안전 평가기 결과 | 없음 | 36 | 스트레스 15 + red team 6 + trace 18 + 연속 평가 최대 160 |
| 조가 만드는 유료 객체 | hosted 에이전트: 4단계부터 10단계 정리까지 | 없음 | 연속 평가 일정: 최대 8시간 또는 10단계까지 |

한국어 기본 실습의 기록에서는 에이전트 대시보드에 에이전트 run 54건, 약 145.8K tokens가 표시됐다([기록된 결과](validation.ko.md#dashboard)). Search, 모델 배포, 로깅은 공유 자원이라 조별 정리 뒤에도 비용이 계속 발생한다([정리와 유지 관리](#정리-원칙)).

**기록된 한국어 실행 기준 비용 예시:** [Azure Retail Prices API](https://learn.microsoft.com/rest/api/cost-management/retail-prices/azure-retail-prices)에서 2026년 9월 25일에 조회한 Sweden Central 정가다. GlobalStandard 기준이며 세금과 할인은 반영하지 않았다. 예산을 승인하기 전에 자신의 가격으로 바꾼다.

| 조별 | 기본 실습 | 레벨 2 | 레벨 3 |
|---|---|---|---|
| 모델·평가 토큰 | 약 $0.60 | 약 $2.80 | 약 $4.16, 연속 평가에 최대 $17.93 추가 |
| hosted 에이전트 컴퓨팅 | 활성 세션 1시간당 $0.135 | 없음 | 4절 에이전트 실행에 같은 요금 |

- 1M 토큰당 입력/출력 요금: Sol $2/$10, Luna $0.10/$0.50, Astra $10/$50, `gpt-5.4-mini` $0.75/$4.50. 안전 평가 결과는 AI evaluations 미터의 $20/$60으로 계산했다.
- 토큰 행은 답변, 평가 결과, 레벨 2 실패 클러스터링 작업마다 저장된 토큰 사용량을 합한 값이며, 연속 평가는 최대치인 trace 160개로 계산했다. red team 스캔과 rubric·질문 생성 작업은 저장된 결과에 토큰이 없어 포함하지 않았다.
- hosted 세션은 유휴 제한 시간(기본 15분)이 끝날 때까지 vCPU 1개와 2 GiB로 과금된다.
- 공유 비용은 계속 발생한다: Search Basic은 시간당 $0.101(월 약 $74), Log Analytics 수집은 무료 한도를 넘으면 GB당 $2.99다.

</details>

<a id="tools"></a>

## 로컬 도구 설치와 확인

**기본 도구부터 확인한다.** 직접 실행에는 Copilot CLI·Node.js·Playwright가 필요 없다. Copilot CLI를 쓸 때도 이 확인을 마친 뒤 [별도 Copilot CLI 안내](copilot.ko.md)를 진행한다.

| 도구 | 설치 안내 / 확인 조건 |
|---|---|
| Git | [Git 설치](https://git-scm.com/downloads) |
| Python | [Python 설치](https://www.python.org/downloads/)에서 **3.13.x** 선택. 실습 터미널에서 `python3.13` 실행 가능 |
| Azure CLI | [Azure CLI 설치](https://learn.microsoft.com/cli/azure/install-azure-cli) |
| azd | [Azure Developer CLI 설치](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd) |
| Bash | 필요한 셸. [GNU Bash](https://www.gnu.org/software/bash/) |
| curl | 필요한 전송 도구. [배포판별 curl 다운로드](https://curl.se/download.html) |
| 편집기 | [VS Code 설치](https://code.visualstudio.com/download) 또는 기존 텍스트 편집기. `.env`·JSON을 열 수 있으면 됨 |
| 브라우저 | [Edge 설치](https://www.microsoft.com/edge/download) 또는 [Chrome 설치](https://www.google.com/chrome/). 로그인·Foundry 포털 확인에 사용 |
| Windows만: WSL 터미널 | [WSL 설치](https://learn.microsoft.com/windows/wsl/install) |

실습 명령은 Bash에서 실행한다. macOS/Linux는 로컬 터미널을 사용하고, Windows는 WSL 안에 Linux 도구를 설치해 WSL Bash를 사용한다. 수동 확인용 편집기와 브라우저는 Windows 앱을 사용해도 된다.

**편집기 — Windows/WSL 사용자:** Windows의 VS Code에 [WSL 확장](https://code.visualstudio.com/docs/remote/wsl)을 설치한다. 이후 실습 폴더를 만들면 **F1 → WSL: Connect to WSL**로 연결한 뒤 **File → Open Folder**에서 연다. 왼쪽 아래에 **WSL** 표시가 있어야 뒤의 Linux 경로와 터미널을 그대로 쓸 수 있다.

**터미널 — CLI 도구 확인:** 처음으로 찾지 못한 명령에서 멈추므로 해당 도구만 설치한 뒤 다시 확인한다.

```bash
bash --version &&
curl --version &&
git --version &&
python3.13 --version &&
az version &&
azd version &&
azd extension list
```

**완료 확인:** 모든 명령이 버전이나 JSON 결과를 출력하고 `azd extension list`가 오류 없이 끝난다.

**다르면:** 빠진 도구만 설치하거나 복구한 뒤 같은 블록을 다시 실행한다. Ubuntu/WSL에서는 `sudo apt-get update`를 한 번 실행한다. Bash가 없으면 `sudo apt-get install bash`, curl이 없으면 `sudo apt-get install curl`만 실행한다.

설치 승인은 사용자 터미널에서 처리하고 암호를 채팅에 전달하지 않는다.

<details>
<summary>빠진 도구가 계속 보일 때의 플랫폼 참고</summary>

macOS에서는 `/bin/bash`, `/usr/bin/curl`, PATH를 먼저 확인한다. 다른 Linux 배포판은 해당 패키지 관리자를 사용한다.

</details>

**터미널 — 어느 폴더에서든, `microsoft.foundry` 설치 버전이 없을 때만 설치:** 위 `azd extension list`에 이미 보이면 이 블록을 건너뛴다.

```bash
azd extension install microsoft.foundry &&
azd extension list
```

**완료 확인:** 새로 설치했거나 이미 있던 `microsoft.foundry` 버전이 `azd extension list`에 보인다.

**다르면:** azd 설치를 복구한 뒤 이 명령만 다시 실행한다.

**터미널 — 에이전트 명령 확인:**

```bash
azd ai agent --help
```

**완료 확인:** 명령 목록에 `run`, `invoke`가 있다.

**다르면:** azd와 `microsoft.foundry` 확장 버전을 맞춘 뒤 다시 확인한다. 업데이트 안내 자체를 실패로 보지 않으며, 실험 중 “모두 업데이트”나 임의 다운그레이드를 하지 않는다.

Azure를 직접 준비하지 않는다면 여기서 멈추고 [README 1단계](../README.ko.md#start)나 [Copilot CLI 안내](copilot.ko.md)로 돌아간다. 직접 준비한다면 [권한](#access)으로 계속 진행한다. **혼자 실습한다면** 권한을 확인한 뒤 [새 전용 환경 만들기](environment.ko.md)로 간다. Python 패키지는 선택한 경로의 가상환경 설치 단계에서 설치하며, 지금 전역으로 설치하지 않는다.

<details>
<summary>참고: 준비할 Azure 서비스와 조건</summary>

| 항목 | 준비 상태 |
|---|---|
| Azure 구독 | 실습용 구독과 tenant를 명시적으로 선택 |
| Foundry | `Microsoft.CognitiveServices/accounts/projects` 유형의 프로젝트 |
| 지역 | Hosted Agent와 세 모델을 실제로 사용할 수 있는 지역 |
| 모델 | Sol/Luna/Astra(`gpt-6-sol`·`gpt-6-luna`·`gpt-6-astra`)의 실제 배포 + IQ 계획과 judge에 함께 쓰는 고정 보조 배포 |
| Search | semantic/agentic retrieval 지원, system-assigned identity, Entra RBAC |
| 관측 | 프로젝트에 연결된 Application Insights와 Logs 조회 권한 |
| 로컬 | Python 3.13, Azure CLI, azd, `microsoft.foundry` 확장 |
| 인증 | 참가자가 README 1-3에서 두 CLI에 로그인하고 MFA를 완료할 수 있음 |
| 데이터 | 합성 문서만 사용, 실습 접두사는 조마다 다름 |

Agent hosting과 SDK 패키지의 GA/preview 상태는 서로 다를 수 있으므로 혼동하지 않는다.

</details>

<a id="사전-준비"></a>

<a id="access"></a>

## 권한

환경 소유자는 필요한 리소스 그룹·리소스를 만들거나 사용할 수 있고, 아래 역할을 해당 범위에 부여할 수 있어야 한다. **Contributor에는 역할 부여 권한**(`Microsoft.Authorization/roleAssignments/write`)이 없다. 혼자 실습하면 먼저 아래에서 **구독 Owner**를 확인한다. 새 자원의 역할은 환경 준비 명령과 README 2-1·4-2가 부여하므로 아래 역할 표는 참고용이다.

**포털 — 혼자 실습할 때 Owner 확인:** [Azure Portal](https://portal.azure.com/)의 **Subscriptions → 사용할 구독 → Access control (IAM) → Check access → View my access**에서 본인의 역할을 확인한다. `View my access` 대신 역할 목록이 바로 보이면 그 목록을 본다([공식 확인 절차](https://learn.microsoft.com/azure/role-based-access-control/check-access)).

**완료 확인:** 해당 구독에 본인의 활성 **Owner** 역할이 있다. 아직 만들지 않은 Search·에이전트의 역할을 여기서 수동으로 추가할 필요는 없다. [새 전용 환경 만들기](environment.ko.md)로 진행한다.

**다르면:** 계정과 구독을 다시 확인한다. 역할이 활성화 대상(`Eligible`)이면 [역할 활성화](https://learn.microsoft.com/azure/role-based-access-control/role-assignments-eligible-activate)를 먼저 마친다. Contributor만 있으면 아래처럼 접근 관리자의 지원이 필요하다.

승인된 접근 관리자가 권한을 준비하거나 해당 작업을 수행해야 한다. 관리자·Owner 권한을 에이전트에 우회로로 주지 않는다. 역할 부여 권한이 없는 참가자는 `prepare-iq`와 `grant-agent-access`에서 환경 소유자의 지원이 필요하다.

각 행마다 대상 범위의 **Access control (IAM) → Check access**에서 확인하거나 접근 관리자의 확인을 받는다. managed identity와 범위를 서로 바꾸지 않는다.

| 주체 | 최소 업무 권한 | 범위 |
|---|---|---|
| 참가자 | Foundry 접근과 필요한 개발·배포 작업 | 승인된 프로젝트/계정 |
| 준비 담당자 | 모델 배포·Search 스키마 생성 권한 | 실습 리소스 |
| 문서 적재 담당자 | Search Service Contributor, Search Index Data Contributor | 실습 Search |
| Search managed identity | Cognitive Services User | planner 모델이 있는 Foundry 계정 |
| 에이전트 인스턴스의 managed identity | Search Index Data Reader, Cognitive Services OpenAI User | 실습 Search, 세 후보 모델이 있는 Foundry 계정 |
| 관측 담당자 / project identity | 연결된 telemetry 읽기 | Application Insights / Logs |

로컬 성공이 hosted 에이전트 권한을 보장하지 않는다. 위 표의 역할만 부여한다. 포털에 이전 역할 이름(Azure AI User 등)이 보여도 Owner를 주지 않고, 기존 역할이 충분하면 추가하지 않는다. 에이전트는 계정 endpoint로 모델을 호출하므로 그 managed identity에는 프로젝트의 `Foundry User`나 Owner가 필요 없다. 진단 중 추가한 역할은 검증 환경을 정리할 때 제거한다.

**완료 확인:** 모든 행에 주체, 정확한 역할, 정확한 범위가 정해져 있고, 환경 소유자가 그 역할을 직접 부여할 수 있거나 승인된 접근 관리자가 부여하기로 했다.

**다르면:** 승인된 접근 관리자가 역할을 부여하거나 대신 할당할 때까지 준비를 멈춘다. Contributor 권한만으로 진행하지 않는다.

<details>
<summary>프로덕션 경계와 지원 환경</summary>

이 실습은 조 전체가 볼 수 있는 합성 문서를 공유한다. 실제 다중 사용자 제품은 문서별 권한, tenant 격리, on-behalf-of/호출자 신원 전달을 별도로 구현해야 한다. Search 읽기 역할만으로 사용자별 문서 필터링이 자동으로 적용되지는 않는다.

지원되는 hosted 에이전트 환경은 [Hosted Agent quickstart](https://learn.microsoft.com/azure/foundry/agents/quickstarts/quickstart-hosted-agent)를 참고한다.

</details>

**다음:** 기존 기반 환경을 쓰면 [기존 기반 환경으로 준비](#existing-foundation)로 간다. 새 서비스를 만들면 [전용 새 환경 생성](environment.ko.md)으로 돌아간다.

<a id="existing-foundation"></a>

<a id="로컬-설치와-테스트"></a>

## 기존 기반 환경으로 준비

기반 서비스가 이미 있는 경우의 준비 경로다. 새 환경 가이드를 완료했다면 그 문서의 전달 안내를 따르며 이 준비를 반복하지 않는다.

**이 경로의 순서:** 아래에서 범위를 확인하고 로컬 테스트를 통과한 뒤 [1. 설정·로그인](#existing-settings) → [2. 보조 배포](#auxiliary-model) → [3. 후보 모델과 calibration](#check-candidates) → 리허설 또는 개인 실습 복귀 순으로 진행한다.

**먼저 범위를 확인한다.** Foundry 계정·프로젝트, Search, 연결된 Application Insights는 **`AZURE_RESOURCE_GROUP`의 같은 그룹**에 있어야 한다. 후보·보조 모델은 같은 Foundry 계정의 배포여야 한다. 다른 그룹이나 계정이면 멈추고 환경 소유자와 범위를 맞춘다. 예시에 맞추려고 공유 리소스를 옮기지 않는다.

미사용 clone을 **모델 준비 폴더**로 쓴다.

**터미널 — clone을 만들 상위 폴더:** 모델 준비용 clone을 만든다. 이미 미사용 clone이 있으면 이 블록을 건너뛰고 그 루트로 `cd`한다.

**실행 전:** `foundry-evaluation-model-prep-ko`가 이미 있으면 블록의 두 폴더 이름을 같은 미사용 이름으로 바꾼다. 기존 폴더는 지우지 않는다.

```bash
git clone https://github.com/junwoojeong100/foundry-evaluation.git foundry-evaluation-model-prep-ko &&
cd foundry-evaluation-model-prep-ko
```

**완료 확인:** 터미널이 새 모델 준비 clone의 루트에 있고, 그 폴더에 `README.md`와 `scripts/`가 있다.

**다르면:** 미사용 폴더 이름 하나로 블록을 다시 실행하거나, 이미 있는 미사용 clone의 루트로 `cd`한다.

**터미널 — 모델 준비 폴더:**

```bash
python3.13 -m venv src/agent/.venv &&
source src/agent/.venv/bin/activate &&
python -m pip install -r requirements.txt &&
python -m unittest discover -s tests -v
```

**완료 확인:** 테스트가 **`OK`**로 끝난다. 테스트는 두 언어와 고정된 정책 ID, 금액 규칙, 동결된 사례 계약을 확인한다.

**다르면:** Azure 작업을 시작하지 말고 실패한 오프라인 테스트를 먼저 고친다. `requirements.lock.txt`의 고정 의존성은 유지한다.

<details>
<summary>고정 패키지 버전</summary>

프레임워크와 Foundry SDK의 버전 상한이 다를 수 있어 Agent Framework Foundry 1.11.0, core 1.16.0, OpenAI adapter 1.14.1, Azure AI Projects 2.3.0, Agent Server Invocations 1.1.0을 고정했다. 실습 중에 프레임워크·확장·SDK를 무조건 최신으로 올리지 않는다. `requirements.lock.txt`는 검증 환경의 전체 의존성 스냅샷이며, 같은 Python 환경을 재현할 때 `python -m pip install -r requirements.lock.txt`를 사용할 수 있다.

</details>

**다음:** [실제 설정값 복사, 로그인, 후보 배포 이름 정하기](#existing-settings)로 간다.

<a id="existing-settings"></a>
<a id="1-설정과-로그인"></a>

### 1. 실제 설정값 복사, 로그인, 후보 배포 이름 정하기

**편집기 — 모델 준비 폴더:**

- 완성된 `.env`를 받았다면 교체하지 말고 아래 표의 필드를 확인한다.
- 없으면 `.env.example`을 **지금 clone 루트의 `.env`**로 복사한 뒤 아래 필드만 채운다.

화면에 표시된 이름·엔드포인트만 복사하며, API key, 브라우저 URL, `/openai/v1/`, 전체 Resource ID는 넣지 않는다.

| `.env` 필드 | 값을 확인할 곳 |
|---|---|
| `AZURE_SUBSCRIPTION_ID` / `AZURE_TENANT_ID` | Azure Portal의 **Subscriptions → 해당 구독 → Overview**에서 구독 ID, **Microsoft Entra ID → Overview**에서 그 구독 디렉터리의 tenant ID |
| `AZURE_EXPECTED_USERNAME` | 승인된 계정의 로그인 이름(UPN). 표시 이름이 아님 |
| `AZURE_RESOURCE_GROUP` | 기존 실습 서비스가 있는 Azure Portal의 **리소스 그룹 이름** |
| `AZURE_AI_ACCOUNT_NAME` / `AZURE_AI_PROJECT_NAME` | Foundry에서 선택한 프로젝트의 **리소스 이름 / 프로젝트 이름**. 리소스는 프로젝트의 상위 계정이며 프로젝트 자체가 아님 |
| `FOUNDRY_PROJECT_ENDPOINT` | Foundry의 해당 프로젝트 **Overview → project endpoint**. `/api/projects/<project>`로 끝나는 값 |
| `AZURE_OPENAI_ENDPOINT` | Azure Portal의 **같은 Foundry 계정 → Keys and Endpoint**에서 `.openai.azure.com`으로 끝나는 Azure OpenAI 기본 엔드포인트 |
| `AZURE_SEARCH_NAME` / `AZURE_SEARCH_ENDPOINT` | 사용할 **Search 서비스 → Overview**의 이름과 **URL**. URL은 `.search.windows.net`으로 끝남 |
| `AZURE_APPLICATION_INSIGHTS_NAME` | 같은 그룹에서 **이 프로젝트에 연결된 Application Insights 리소스 이름**. Log Analytics workspace 이름이 아님 |
| `MODEL_*_DEPLOYMENT` | Foundry **Build → Models**에서 실제 후보 배포 이름이 있으면 복사한다. 없는 후보의 이름은 아래 후보 표로 정한다. |

나머지는 `LAB_LANGUAGE=ko`, `LAB_PROMPT_VERSION=v1`, `LAB_AUTH_MODE=cli`를 유지한다. `LAB_PREFIX`와 `LAB_AGENT_NAME`은 미사용 값으로 정한다. `LAB_AUX_DEPLOYMENT`는 나중에 [2단계](#auxiliary-model)에서 기록한다. `FOUNDRY_PROJECT_ENDPOINT` 값을 `AZURE_OPENAI_ENDPOINT`에 넣지 않는다.

**완료 확인:** 표의 필드가 포털의 이름·엔드포인트 값으로 채워졌고 `LAB_LANGUAGE=ko`, `LAB_PROMPT_VERSION=v1`, `LAB_AUTH_MODE=cli`가 그대로다.

**다르면:** 로그인 전에 `.env`만 고친다.

<details>
<summary>Copilot CLI에서 온 경우</summary>

Copilot CLI 페이지에서 설정값만 준비하러 왔다면 여기서 [계획 확인](copilot.ko.md#plan-review)으로 돌아간다. CLI 로그인은 이후 실행 단계에서 한다.

</details>

로컬 테스트가 `OK`이면 **모델 준비 폴더**에서 로그인한다. 이 폴더만의 격리된 CLI 프로필을 쓰기 위해서다. 아래 로그인 블록 네 개만 실행한다. [README 1-3](../README.ko.md#login)과 같은 로그인이지만, 보조 모델이 아직 준비되지 않았으므로 README의 `preflight`·`bind`는 실행하지 않는다.

**터미널 A — 1. ID 입력:** 이 로그인은 이 폴더의 `.azure-cli/`에만 보관한다(공유·커밋 금지).

```bash
export AZURE_CONFIG_DIR="$PWD/.azure-cli" &&
read -r -p ".env의 AZURE_TENANT_ID 값: " LOGIN_TENANT_ID &&
read -r -p ".env의 AZURE_SUBSCRIPTION_ID 값: " LOGIN_SUBSCRIPTION_ID
```

**완료 확인:** 두 프롬프트에 `.env`의 tenant ID와 subscription ID를 입력했고, 터미널은 모델 준비 폴더에 있다.

**다르면:** 로그인하지 말고 이 ID 입력 블록만 다시 실행한다.

**터미널 A — 2. Azure CLI 로그인:** 구독을 물으면 `.env`의 구독을 고른다.

```bash
az login --tenant "$LOGIN_TENANT_ID" --subscription "$LOGIN_SUBSCRIPTION_ID" --output none
```

**완료 확인:** Azure CLI 로그인이 오류 없이 끝나고 프롬프트로 돌아온다.

**다르면:** 이 블록만 지정 tenant·subscription으로 다시 실행하고, 계속 실패하면 [로그인 문제 해결](troubleshooting.ko.md#login)을 본다.

**터미널 A — 3. azd 로그인:** 같은 계정을 쓴다.

```bash
azd auth login --tenant-id "$LOGIN_TENANT_ID"
```

**완료 확인:** azd 로그인이 같은 계정으로 끝난다.

**다르면:** azd 로그인 블록만 다시 실행한다.

<a id="login-check"></a>

**터미널 A — 4. 두 로그인 확인:**

```bash
az account show --subscription "$LOGIN_SUBSCRIPTION_ID" \
  --query "{user:user.name,tenant:tenantId,subscription:id,state:state}" --output json &&
azd auth status --output json
```

**완료 확인:** CLI의 `user`와 azd의 `email`이 `AZURE_EXPECTED_USERNAME`과 같고, `tenant`·`subscription`이 `.env`의 두 ID와 같으며, `state: Enabled`, `status: authenticated`다.

**다르면:** 지정한 계정으로 다시 로그인한다. 브라우저가 열리지 않으면 [로그인 문제 해결](troubleshooting.ko.md#login)을 따른다.

**편집기 — preflight 전에 후보 배포 이름 정하기:** 아래 표에 따라 `.env`의 세 `MODEL_*_DEPLOYMENT` 값을 수정한다.

| 후보 상태 | 해당 `MODEL_*_DEPLOYMENT`에 넣을 값 |
|---|---|
| 지정 모델·버전이 이미 배포됨 | **실제 배포 이름**을 복사. 새 접두사와 같을 필요는 없음 |
| 후보가 아직 배포되지 않음 | 실제 `LAB_PREFIX` 뒤에 `-sol`, `-luna`, `-astra`를 붙인 미사용 이름을 예약. 아래 3번에서 없는 배포를 생성 |

**완료 확인:** 세 값은 실제 기존 배포 이름이거나 아직 쓰지 않은 `<LAB_PREFIX>-sol` / `-luna` / `-astra` 이름이다.

**다르면:** preflight를 실행하지 말고 세 값만 고친다.

템플릿의 `ll-team01-sol` 같은 이름이 실제 배포의 존재를 뜻하지는 않는다. 고정 [모델 ID·버전](reference.ko.md#model-names)은 유지하며 보조 배포는 아래에서 별도로 준비한다.

<a id="auxiliary-model"></a>

### 2. 보조 배포를 먼저 준비

**실습 전에 환경 소유자가 `gpt-5.4-mini` 보조 배포 하나를 준비한다.** Foundry IQ 계획과 LLM judge가 이 배포를 함께 쓴다. `prepare-models`는 이 배포를 만들지 않으며, `--allow-missing-models`는 **후보 모델 누락만** 허용하므로 이 배포가 없으면 명령이 중단된다. 기존 배포 확인 → 맞는 배포가 없을 때만 생성 → 실제 배포 이름을 `.env`에 기록하는 순서로 진행한다.

**포털 — 기존 보조 배포 확인:**

1. [Foundry](https://ai.azure.com/)에 `.env`의 계정으로 로그인한다.
2. **New Foundry**에서 `AZURE_AI_ACCOUNT_NAME`과 `AZURE_AI_PROJECT_NAME`이 맞는 프로젝트를 연다.
3. **Build → Models**에서 기존 배포를 열어 아래 조건을 확인한다.

| 확인 항목 | 이 실습의 고정 조건 |
|---|---|
| 배포 위치 | `.env`에 지정한 **같은 Foundry 계정** |
| 모델 ID / 버전 | `gpt-5.4-mini` / `2026-03-17` |
| 배포 유형 | **Global Standard** (`GlobalStandard`). PTU 예약이 아님 |
| 버전 유지 | 자동 버전 업그레이드 없음 (`NoAutoUpgrade`) |
| 배포 상태 | **`Succeeded`** |

**Build → Models**의 열이 헷갈릴 때만 아래 예시 화면을 연다. 모델, 버전, 상태, 배포 유형만 대조한다.

<details>
<summary>선택 예시 화면: Build → Models 필드 위치를 찾을 때만 열기</summary>

기록된 한국어 예시 실행의 **Build → Models → Deployments** 목록이다. 세 후보 배포와 `gpt-5.4-mini`가 모두 `Succeeded`, `Global Standard`다. 실제 이름·접두사·시각은 달라진다.

![기록된 Foundry 배포 예시](assets/live-ko-20260923b/screenshots/S1-P01-models-after.webp)

</details>

모든 행이 맞는 배포만 재사용한다.

**포털 — 맞는 배포가 없을 때만 생성:** **Discover → Models → `gpt-5.4-mini` → Deploy → Custom settings**에서 `<LAB_PREFIX>-judge`, **Global Standard**, 버전 `2026-03-17`, `NoAutoUpgrade`, 승인된 용량으로 만든다. 모델 접근·버전/유형·할당량이 맞지 않으면 중단한다. 다른 모델로 대체하거나 공유 배포를 수정하지 않는다.

**완료 확인:** 기존 또는 새 보조 배포가 위 조건을 모두 만족하고 `Succeeded` 상태다.

**다르면:** `.env`를 고치기 전에 모델 접근, 버전·유형, 할당량, 배포 상태를 먼저 해결한다.

**편집기 — 보조 배포 값 기록:** 지금 폴더의 `.env`에 기록하고, 배포의 Resource ID는 참가자 정리가 건드리지 않는 곳에 따로 보관한다.

| 키 | 기록할 값 |
|---|---|
| `LAB_AUX_DEPLOYMENT` | **Build → Models에서 복사한 실제 배포 이름** |
| `LAB_AUX_MODEL` | `gpt-5.4-mini` |

**완료 확인:** 배포가 `.env`의 Foundry 계정·프로젝트에 있고 위 조건을 만족하며, `.env`의 두 값이 **각각 실제 배포 이름과 모델 ID**에 맞는다. 이 배포 하나를 IQ planner와 평가 judge가 함께 사용하며, Resource ID는 참가자 정리 대상 밖에 보관되어 있다.

**다르면:** 여기서 멈추고 보조 배포나 `.env`의 두 값을 먼저 고친다. 공유 배포를 고치거나 다른 모델로 대체하지 않는다.

<a id="check-candidates"></a>

### 3. 세 후보 모델 점검과 judge calibration

**터미널 — 현재 모델 확인:** 같은 모델 준비 폴더에서 실행한다. 보조 모델은 위에서 준비되어 있어야 한다.

```bash
python scripts/workshop.py preflight --allow-missing-models
```

**완료 확인:** 오류 없이 끝나고 `language: ko`와 `missing_models` 목록이 나온다. 목록이 **`[]`이면 후보 준비는 완료**이므로 생성 명령을 건너뛰고 [judge 점검](#candidate-calibration)으로 간다.

**다르면:** 보조 모델 오류는 [앞 단계](#auxiliary-model), 나머지는 [증상별 확인](troubleshooting.ko.md#symptoms)에서 원인을 해결한다. 오류가 난 상태로 모델 생성에 넘어가지 않는다.

**터미널 — `missing_models`에 후보가 있을 때만 생성:** 없는 배포만 고유 접두사로 만들고 마지막에 `preflight`까지 수행한다. 새 배포는 `GlobalStandard` 용량 50, `NoAutoUpgrade`이며 기존 배포는 유지한다.

```bash
python scripts/workshop.py prepare-models
```

**완료 확인:** 오류 없이 끝나고 **마지막 JSON**에 `language: ko`, 세 후보의 `deployed: true`, `missing_models: []`가 나온다. 별도 `preflight`를 다시 실행하지 않는다.

**다르면:** 모델 접근·할당량·배포 오류를 해결한 뒤 같은 폴더에서 실패한 명령만 복구한다. 이름·모델을 바꾸거나 새 기반 환경으로 우회하지 않는다([증상별 확인](troubleshooting.ko.md#symptoms)).

<a id="candidate-calibration"></a>

**터미널 — judge 점검(두 경로 공통):**

```bash
python scripts/workshop.py calibrate
```

**완료 확인:** **`Judge calibration passed`**. 참가자 README 5단계에서도 점검하며, 같은 입력의 완료된 calibration은 재사용한다. 예제 2건은 본 평가의 48개 후보 응답에 포함하지 않는다.

**다르면:** [calibration만 복구](troubleshooting.ko.md#calibration)한다. 끝난 모델 준비부터 반복하지 않는다.

<a id="azd-초기화"></a>
<a id="observability-repair"></a>

평가가 Application Insights `ResourceId` metadata 누락을 보고하면 재시도 전에 아래 소유자 전용 복구를 연다.

<details>
<summary>소유자 전용 관측 복구</summary>

[관측 증상 행](troubleshooting.ko.md#symptoms)을 따른다. 승인된 강사만 전용 실습 연결을 복구할 수 있으며, 예시를 맞추려고 공유 연결을 수정하지 않는다.

`python scripts/workshop.py repair-observability --confirm`은 이 연결이 실습 전용임을 확인한 뒤에만 사용한다.

원인을 해결한 뒤 저장된 run 상태에 따라 [calibration 복구](troubleshooting.ko.md#calibration) 또는 [평가 복구](troubleshooting.ko.md#evaluation-retry)를 선택한다. 로컬 오류만으로 `--retry-failed`를 사용하거나 낮은 점수를 통과할 때까지 반복하지 않는다.

</details>

**다음:** 수업 준비라면 [별도 리허설 폴더](#rehearsal-workspace)로 간다. 개인 실습이라면 같은 폴더에서 README [`bind` 명령](../README.ko.md#bind-project)으로 돌아간다. 완료한 clone·설치·로그인·preflight는 반복하지 않는다.

<a id="rehearsal-workspace"></a>
<a id="리허설과-참가자-실행을-분리"></a>

## 모델 준비·리허설·참가자 실행을 분리

**수업용 모델의 소유권은 준비 폴더에 남긴다.** 그 폴더에서 전체 실습을 리허설하면 10단계 정리가 참가자에게 공유할 모델까지 삭제할 수 있다.

```text
모델 준비 폴더 (공유 모델의 소유권 유지)
  -> .env만 복사, LAB_PREFIX/LAB_AGENT_NAME 변경 -> 리허설 clone: 1-9단계 -> 선택 레벨 2·3 -> 10단계
  -> .env만 복사, LAB_PREFIX/LAB_AGENT_NAME 변경 -> 각 조의 clone: 같은 경로
```

**터미널 — 모델 준비 clone 밖, 리허설 clone을 만들 상위 폴더:** 모델 준비가 끝나면 기본 리허설 clone을 만든다.

**실행 전:** `foundry-evaluation-rehearsal-ko`가 이미 있으면 블록의 두 폴더 이름을 같은 미사용 이름으로 바꾼다. 기존 폴더는 지우지 않는다.

```bash
git clone https://github.com/junwoojeong100/foundry-evaluation.git foundry-evaluation-rehearsal-ko &&
cd foundry-evaluation-rehearsal-ko
```

**완료 확인:** 터미널이 새 리허설 clone의 루트에 있고, 그 폴더에 `README.md`와 `scripts/`가 있다.

**다르면:** 미사용 폴더 이름 하나로 블록을 다시 실행하거나, 이미 있는 미사용 clone의 루트로 `cd`한다.

**편집기 — 리허설 clone의 `.env`:** 모델 준비 폴더의 완성된 `.env` 파일만 이 clone의 루트로 복사한다. `LAB_LANGUAGE=ko`, 프로젝트, 엔드포인트, 모델 배포 이름은 그대로 둔다. **`LAB_PREFIX`와 `LAB_AGENT_NAME`만** 미사용 리허설 이름으로 바꾼다.

**완료 확인:** 리허설 clone의 `.env`에 `LAB_LANGUAGE=ko`, 실제 엔드포인트·배포 이름, 미사용 `LAB_PREFIX`/`LAB_AGENT_NAME`이 있다.

**다르면:** 리허설 clone의 `.env`만 고친다. `.azure`, `.foundry`, 인증 저장소, 실행 결과는 복사하지 않는다.

**README — 리허설 clone:** 이 clone에서 [README 1-1](../README.ko.md#source-setup)의 clone 블록 다음부터 시작해, 방금 복사한 `.env`로 README 1–9단계를 순서대로 진행한 뒤 이 문서로 돌아온다.

**완료 확인:** 이 clone에서 README 9-1 `verify`가 `component_execution_verified: true`, `primary_model_outputs: 48`, `distinct_verified_traces: 48`을 보여 주고, 9-2 대시보드에 데이터가 보인다.

**다르면:** 실패한 README 단계에서만 복구한다. 레벨이나 정리로 넘어가지 않는다.

<details>
<summary>bind와 로컬 서버 참고</summary>

`bind`는 제공된 `azure.yaml`로 지금 폴더의 azd 환경을 만들거나 재사용하고 조별 서비스·에이전트 이름을 맞춘다. Foundry 프로젝트를 다시 프로비저닝하지 않는다. `azd ai agent init`을 다시 실행하거나 다른 폴더의 상태를 복사하지 않는다.

로컬 서버는 신뢰할 수 있는 개발 환경에서만 잠깐 실행하고 즉시 종료한다. 공개망에 노출하지 않는다. 로컬 테스트 서버와 Azure 플랫폼이 인증을 처리하는 hosted 엔드포인트는 서로 다른 보안 경계다.

</details>

**다음:** 레벨 2·3을 가르친다면 [레벨 2·3 준비](#levels)로 간다. 아니면 이 clone에서 [README 10단계](../README.ko.md#cleanup)를 실행한 뒤 [전달 전 최종 모델 확인](#final-model-check)으로 간다.

<a id="levels"></a>

## 레벨 2·3 준비

가르칠 레벨([레벨 2](level-2.ko.md), [레벨 3](level-3.ko.md))만 리허설 clone의 README 9단계 뒤, 10단계 전에 리허설한다. 참가자는 자기 폴더에서 9단계와 10단계 사이에 진행한다. 팀이 시작하기 전에 trace 접근, judge·Sol 용량, 3절을 가르친다면 red team 승인, 정리 범위를 확인한다. 레벨 3의 4절은 참가자 권한으로 Foundry 계정의 평가 API를 호출하므로, 참가자에게 Foundry 계정 범위의 **Foundry User**가 필요하다. [전용 새 환경 생성](environment.ko.md)의 `user-foundry`가 만드는 프로젝트 범위 할당만으로는 부족하다.

**터미널 — 기존 기반 환경의 trace 접근 준비:** 공유 기반 환경의 모델 준비 폴더에서 한 번 실행한다. 성공한 뒤에는 리허설 폴더와 조별 폴더에서 반복하지 않는다. [전용 새 환경 생성](environment.ko.md) 경로로 만든 새 환경에는 이미 이 역할이 있다.

```bash
python scripts/workshop.py prepare-trace-access
```

**완료 확인:** 오류 없이 끝나고 `Trace access is ready. This shared preparation is not recorded as team-owned, so team cleanup keeps it.`가 출력된다. `Log Analytics Reader is already assigned...` 또는 `Assigned Log Analytics Reader...`가 함께 나올 수 있다.

**다르면:** 레벨 2·3 준비를 멈추고 환경 소유자가 보고된 managed identity, workspace, RBAC 문제를 해결한다. 해결 전에는 trace 평가를 시작하지 않는다.

레벨 3 red team을 가르치려면 유해 프롬프트 테스트에 대한 조직 승인을 먼저 받는다. 승인되지 않으면 레벨 3의 3절을 건너뛴다. 실습에는 합성 데이터만 쓰고 실제 직원 데이터는 연결하지 않는다.

<details>
<summary>레벨 2·3 리허설 체크리스트</summary>

레벨 2·3을 가르치면 judge/Sol 용량, trace 접근, red team 승인, 정리 범위를 리허설한다.

| 확인 | 이유 |
|---|---|
| judge 용량 | 속도 제한 위험 → 조별 시작을 나누거나 승인된 judge 용량을 늘린다. |
| Sol 배포 | 공유 Sol 부하 → `stress-test`와 `red-team`에 필요한 용량을 확인한다. |
| 에이전트 실제 호출 | hosted 에이전트 부하 → 조별로 병렬 run 3개에서 Foundry 호출 18회를 리허설한다. |
| trace 접근 | 위 `prepare-trace-access` 명령으로 준비한다. |
| 연속 평가 | 예약된 judge 사용량 → 조별로 8시간 동안 매시간 trace 최대 20개를 확인한다. |
| preview API | preview API 변경 위험 → 사용자 지정/생성 평가기, 인사이트, 합성 데이터, red team을 수업 직전에 리허설한다. |
| 소유권 | 정리 범위 → 팀이 만든 사용자 지정 평가기와 생성 데이터셋만 삭제되고 eval group, 인사이트, red team 스캔은 남는다. |

**trace 내용:** 에이전트의 모델 span에는 모델 입력 전체(질문과 검색된 정책)와 답변이 기록되며, trace 평가는 이 내용을 읽는다.

**지원되지 않는 것:** 이 hosted 에이전트 프로토콜은 에이전트 대상 red team을 지원하지 않는다. 그래서 레벨 3에서는 모델 배포를 대상으로 red team을 수행한다. [실습 범위 밖의 운영 기능](level-3.ko.md#beyond)을 본다.

</details>

**다음:** 리허설 clone에서 [README 10단계](../README.ko.md#cleanup)를 실행한 뒤 [전달 전 최종 모델 확인](#final-model-check)으로 간다.

<a id="final-model-check"></a>

## 전달 전 최종 모델 확인

**터미널 — 모델 준비 폴더:** 실행 환경을 복원하고 전달 전에 모델을 확인한다.

```bash
source src/agent/.venv/bin/activate &&
export AZURE_CONFIG_DIR="$PWD/.azure-cli" &&
python scripts/workshop.py preflight
```

**완료 확인:** 오류 없이 끝나고 세 후보 배포와 `missing_models: []`가 보인다.

**다르면:** 전달을 멈추고 이 폴더에서 [3. 세 후보 모델 점검](#check-candidates)으로 돌아간다. 참가자가 사용 중인 모델은 정리하지 않는다.

**다음:** [리허설 시간표](#rehearsal)로 간다.

<a id="rehearsal"></a>

## 실습 시간 리허설

120분은 준비된 환경을 전제로 한다. 지식 검색·평가·세 모델 중 일부를 빼고 완료로 처리하지 않는다. 시간이 넘으면 모델 배포, 에이전트 배포, 초기 기동(cold start), RBAC 전파, 평가 완료, telemetry 반영 중 어디서 지연됐는지 측정한다.

| 시간 | 참가자 단계 | 확인할 결과 |
|---|---|---|
| 00–10분 | 1. 시작 준비 | 테스트·두 CLI 로그인·계정 확인·preflight·bind |
| 10–25분 | 2. 지식 검색 | 실제 한국어 문서 ID와 IQ activity |
| 25–40분 | 3–4. 로컬·배포 | 로컬과 원격의 실제 응답 |
| 40–55분 | 5. Baseline | 국문 dev 응답 18개와 Foundry 평가 완료 |
| 55–70분 | 6. 사례 검토 | 실제 trace와 검토된 회귀 데이터 |
| 70–85분 | 7. V2 재평가 | 새 버전·같은 dev 6문항 × 3모델 = 18응답 |
| 85–100분 | 8. Holdout | 고정 후보의 holdout 응답 12개 |
| 100–110분 | 9. 운영·검증 | 응답 48개, trace 48개, 전체 lineage |
| 110–115분 | 10. 정리 | 소유 대상만 정리 |
| 115–120분 | 버퍼 | 비동기 평가·telemetry 반영 |

**완료 확인:** 리허설이 지식 검색, 세 모델, 평가, 정리를 빼지 않고 120분 안에 끝난다.

**다르면:** 참가자 시작 전에 용량, 동시성, 준비 상태를 조정한다.

수업 중 한 조가 환경 문제로 10분 이상 지연되면 그 폴더의 설정과 권한을 조와 함께 복구한다. 다른 환경이 필요하면 새 폴더와 이름으로 별도 실행하고, 이전 응답이나 소유권 기록을 옮겨 이어 붙이지 않는다.

**다음:** [참가자에게 전달할 것](#handoff)으로 간다.

<a id="handoff"></a>

## 참가자에게 전달할 것

이 체크리스트는 리허설 정리, [전달 전 최종 모델 확인](#final-model-check), [시간표](#rehearsal) 확인이 모두 끝난 뒤에만 쓴다. 참가자는 [README 1–10단계](../README.ko.md#start)를 따르고, 레벨 2·3은 9단계 뒤, 정리 전에 진행한다.

**편집기:** 조마다 완성된 `.env`, README 1단계 링크, 지원 담당자를 한 번에 전달할 수 있게 준비한다.

| 전달 항목 | 강사가 확인할 내용 |
|---|---|
| 계정 접근 | 의도한 구독, tenant, 프로젝트, 모델 배포 접근을 확인한다. 참가자는 README 1-3에서 로그인하고 MFA를 완료한다. |
| 조별 `.env` | `.env.example`의 모든 값을 채우고 **`LAB_LANGUAGE=ko`**로 설정한다. 암호·API key·token은 넣지 않는다. 참가자는 자기 폴더에서 `bind`를 실행한다. 강사 PC에서 바인딩한 복사본은 대신할 수 없다. |
| 준비된 서비스 | Foundry 프로젝트, Search, 연결된 Application Insights, 세 후보 모델, 별도 보조 배포를 확인한다. `MODEL_*_DEPLOYMENT`의 공유 배포 이름은 바꾸지 않는다. 모델과 기반 서비스 비용은 강사가 관리한다. |
| 고유한 이름 | 조마다 미사용 `LAB_PREFIX`, `LAB_AGENT_NAME`을 정한다. 영문·국문 실행은 폴더를 나눈다. 이름만 예약하고 KB, source, index, 에이전트는 미리 만들지 않는다. |
| 준비된 도구 | [기본 도구 설치·확인](#tools) 통과. Copilot CLI 사용 시 [추가 준비](copilot.ko.md)는 별도 수행 |
| 도움받을 담당자 | `grant-agent-access` 역할 부여·403·quota 오류를 처리할 담당자 |
| 레벨 2·3 | 가르친다면 모든 조를 감당할 judge·Sol 용량([레벨 2·3 준비](#levels)) |

**완료 확인:** 표의 모든 행을 확인했고, 조별 전달물에 고유 `LAB_PREFIX`·`LAB_AGENT_NAME`이 든 완성된 `.env`, README 1단계 링크, 지원 담당자가 들어 있다. 그러면 전달물과 [README 1단계](../README.ko.md#start)를 보낸다.

**다르면:** 전달을 보류하고 누락된 계정, 설정, 서비스, 이름, 도구, 지원 담당자를 참가자 시작 전에 고친다.

<a id="정리-원칙"></a>

## 정리와 유지 관리

**README — 각 조의 실습 폴더:** [README 10단계 dry run](../README.ko.md#cleanup)을 먼저 확인한다. 표시된 이름이 그 폴더의 소유 객체와 일치할 때만 정리를 확정한다. 공유 리소스 그룹 전체를 삭제하거나 공유 리소스에서 `azd down`을 실행하지 않는다. 공유 Search, 모델 배포, 로깅은 조별 정리 뒤에도 비용이 발생하므로 환경 소유자가 Cost Management에서 계속 확인한다.

본인만 쓰는 개인 실습 리소스 그룹은 README 10단계 후 [전용 기반 환경의 최종 정리](environment.ko.md#final-cleanup)를 사용한다.

**완료 확인:** README 10단계 dry run 목록이 그 폴더가 소유한 객체와만 일치한다.

**다르면:** 삭제를 확정하지 말고 소유권이나 환경 불일치를 먼저 해결한다.

**다음:** 준비와 정리가 끝났다. 아래 maintainer 확인은 가이드를 수정할 때만 따른다.

<a id="documentation-checks"></a>

<details>
<summary>가이드 수정 시 maintainer 확인</summary>

## 가이드를 수정할 때

Foundry 에이전트를 수정하거나 설명하기 전에 `microsoft-foundry` 스킬의 지침을 확인한다. 합성 데이터만 사용하며 공유 Azure 리소스와 기본 CLI 구독은 변경하지 않는다. Azure 명령에는 구성된 구독을 명시한다. 모델·지침·데이터셋·trace의 연결 관계를 보존하고, 다른 모델로 대체하거나 누락·오류 행을 성공으로 집계하지 않는다. 문서의 명령은 실제 코드와 일치해야 하며, Azure 실행 전에 로컬 테스트를 통과시킨다.

영문·국문 실행 경로를 함께 유지한다. 결과와 시작 조건부터 쓰고, **새 실습·기존 실행 복구**를 먼저 구분한다. 지침(V1·V2), 질문 묶음(split), 결과 이름(label)은 따로 설명한다. 환경 준비·도구 위임 같은 다른 경로와 배경 설명은 접어 두되, **사례 검토와 결과 해석에 필요한 설명은 본문에 보이게 둔다.**

실행 단계마다 **작업 위치·명령·완료 증거·복구 경로**를 명시한다. 수집·평가·집계·trace 조회·증거 검증뿐 아니라 **후보 준비와 calibration도 명령 하나와 완료 확인 하나씩** 배치한다. 복구 페이지에 뒤의 실습 명령을 묶어 복제하지 말고, 실패한 작업을 복구한 뒤 **메인 가이드의 다음 미실행 명령**으로 돌려보낸다. 내부에서 이미 수행하는 검사를 별도 명령으로 반복하지 않는다.

접힌 예시 화면은 그것이 보여 주는 완료 확인 바로 뒤에 둔다. 환경 준비 문서의 복귀 링크는 아직 실행하지 않은 명령을 가리킨다. 최종 보고는 증거·포털 확인 뒤에 두며, **출처 연결·실행 완료·품질 통과**를 구분한다. 촬영 예시의 답변·점수를 독자의 목표 결과로 쓰지 않는다. 실제 cloud 실행 결과는 [국문 결과](validation.ko.md)와 [영문 결과](validation.en.md)에 따로 두며, 번역한 질문은 새로운 독립 holdout 사례가 아니다.

가상환경을 활성화한 **원래 clone**에서 실행한다.

```bash
python -m unittest discover -s tests -p 'test_docs.py' -v
```

로컬 링크·앵커·첨부 파일, 코드 블록 구조, Bash·JSON 문법, 실제 파서와 Python 명령 인자의 일치, 한영 명령 순서를 확인한다. 개요 표의 **18 + 18 + 12응답이 실제 질문·모델 수와 맞는지**, 필수 결과 해석이 접혀 있지 않은지도 검사한다. 기본·후보 준비·수집 복구 경로의 독립된 완료 확인, 참가자·환경 준비 가이드의 **다르면** 안내, 복구 링크의 다음 명령, **대시보드 → 보고 → 정리** 순서도 검사한다. 예시 명령을 실행하거나 Azure에 접속하지 않으며, 과거 cloud 점수를 재검증하는 테스트가 아니다. 가이드가 없는 실행용 소스 스냅샷에서는 문서 검사를 건너뛴다.

추가로 참가자·환경 소유자·재개 사용자 입장에서 [시작 안내](../README.ko.md#start-here)를 따라 읽는다. **지금 할 일·완료 표시·다음 위치**를 추측 없이 찾을 수 있는지 확인한다. 자동 검사가 처음 읽는 사람의 이해도까지 입증하지는 않는다.

</details>
