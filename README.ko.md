# 출장 규정 에이전트를 실행하고, 평가하고, 개선하기

[English guide](README.md) · [1단계로 바로 이동](#start)

**Microsoft Foundry + Agent Framework Python · 한국어 · 준비된 환경에서 120분**

**완료하면:** 제공된 에이전트를 실행하고 실제 응답을 검토해 **64개 응답**으로 V1/V2를 비교합니다. 앱 작성은 필요 없습니다. 목표는 근거로 개선을 설명하는 것이지, **만점이나 운영 승인**이 아닙니다.

## 여기서 시작하세요

| 현재 상태 | 시작할 곳 |
|---|---|
| Azure 서비스·권한·완성된 조별 `.env`를 받음 | [1단계: 시작 준비](#start) |
| 기반 서비스는 있지만 모델·권한 준비가 필요함 | 환경 소유자가 [기존 환경 준비](docs/instructor.ko.md#existing-foundation)를 진행 |
| 준비된 Azure 환경이 없음 | [새 환경 준비](docs/environment.ko.md)를 마치고 그 문서가 지정하는 단계로 복귀. 혼자 실습하면 본인이 환경 소유자를 맡습니다. |
| 이전 실행을 이어가는 중 | **같은 폴더**에서 [복구 안내](docs/troubleshooting.ko.md#resume)를 따름. 다시 clone하지 않습니다. |

**기본 도구:** Git, Python 3.13, Azure CLI, azd + `microsoft.foundry`, Bash·curl, 편집기·브라우저. Windows의 CLI 도구는 **WSL 안에 설치**합니다. [기본 도구 설치·확인](docs/instructor.ko.md#tools)을 먼저 마칩니다.

**GHCP에 실행을 맡길 때만:** [추가 도구 설치·연결·실습 요청 방법](docs/copilot.ko.md)을 따릅니다. 직접 실행에는 GHCP나 Playwright가 필요하지 않습니다.

**비용과 언어:** **유료 Azure 서비스**가 필요하며 환경 준비는 120분에 포함하지 않습니다. `.env` 복사만으로 자원·권한이 생기지 않습니다. `LAB_LANGUAGE=ko`를 사용하고, 언어별 **폴더·미사용 `LAB_PREFIX` / `LAB_AGENT_NAME`**을 분리합니다. 기존 실행의 언어는 바꾸지 않습니다.

<a id="실습-개요"></a>

## 10단계 실습 경로

예를 들어 2026년 9월 출장의 1박 170,000원 숙박 가능 여부를 물어 **답변·판단·문서 ID**를 받습니다. Sol·Terra·Luna·Astra가 독립적으로 답하며 투표하지 않습니다. **V1/V2는 모델이 아닌 지침입니다.**

```text
질문 → Python agent → Foundry IQ로 정책 검색 → 선택한 모델 → 답변
V1(24응답) → trace 검토 → V2(24응답) → 후보 고정 → holdout(16응답)
```

| 단계 | 다음으로 넘어가는 기준 |
|---|---|
| [1. 시작 준비](#start) | 테스트·두 CLI 로그인·preflight·프로젝트 연결 완료 |
| [2. 정책 검색](#lab-a) | 내 지식베이스에서 문서 ID와 검색 activity 반환 |
| [3. 로컬 실행](#local) | `HTTP 200` **그리고** 실제 V1 답변 확인 |
| [4. 배포](#deploy) | 원격 응답의 숫자 agent 버전과 trace 확인 |
| [5. V1 평가](#lab-c) | Calibration 통과, 24응답 수집·평가 완료 |
| [6. 한 사례 검토](#lab-d) | 원래 trace와 고정 정답을 유지한 검토 기록 저장 |
| [7. V2 평가](#lab-e) | 새 버전으로 **같은 dev 6문항**에 대한 24응답을 수집·평가하고 비교 |
| [8. Holdout 평가](#lab-f) | 고정 V2의 별도 16응답 수집·평가 완료 |
| [9. 전체 증거 확인](#lab-g) | 64응답·64trace·평가·검토 이력 연결 확인 |
| [10. 정리](#cleanup) | 내 소유 객체 정리, 남는 서비스 비용 확인 |

> **처음부터 지킬 것:** 합성 데이터와 지정한 네 모델만 사용합니다. `data/holdout.jsonl`은 **8단계 전까지 열지 않습니다.** 실패한 기록은 보존하고 누락·오류 행을 성공으로 세지 않습니다.

<a id="배경-learning-loop와-frontier-ecosystems"></a>
<a id="이-실습에서는-무엇으로-연결하나요"></a>

**선택 자료:** [Learning loop 배경](docs/reference.ko.md#background) · [용어 설명](docs/reference.ko.md#terms) · [요약 영상](#summary-video). 1단계 전에 읽거나 시청할 필요는 없습니다.

**필수:** 번호가 있는 단계·완료 확인·**포털 확인**. **선택:** 접힌 예시·참고 자료. 명령은 본문에서 복사하고 계정·이름·버전·결과는 본인 값을 씁니다. 화면은 2026-09-14–15의 예시이며 로그인·MFA는 촬영하지 않았습니다.

<a id="start"></a>
<a id="4-시작-전-준비"></a>

## 1. 시작 준비

**할 일:** 새 실습 폴더를 열고, 내 계정·모델·프로젝트가 맞는지 확인합니다.

실습 명령을 입력할 창을 **터미널 A**라고 부릅니다. 먼저 아래 한 줄을 실행합니다.

```bash
bash
```

`$` 없이 **한 블록씩** 복사합니다. `&&`는 앞 명령이 성공해야 이어서 실행한다는 뜻입니다.
입력 프롬프트와 완료 기준을 확인한 뒤 진행하며, **3단계 서버만 계속 실행해 둡니다.** 배포·평가는 몇 분 걸려도 중복 실행하지 않습니다. 오류가 나면 [실패한 명령만 복구](docs/troubleshooting.ko.md#resume)합니다.

<a id="source-setup"></a>

### 1-1. 코드와 설정 파일 준비

미사용 clone이나 ZIP이 있다면 그 폴더로 이동해 이 블록을 건너뜁니다. 기존 결과·`.azure`·`.foundry`를 지워 새 실습처럼 만들지 않으며, 이어가는 실행은 [복구 안내](docs/troubleshooting.ko.md#resume)를 따릅니다.

```bash
git clone https://github.com/junwoojeong100/foundry-evaluation.git &&
cd foundry-evaluation
```

<a id="workspace-settings"></a>

강사가 준 `.env`를 **`README.ko.md`와 같은 위치**에 둡니다. 기존 `.env`를 덮어쓰지 않습니다.
구독·tenant, 프로젝트·Search, 모델 배포 이름, 조별 `LAB_PREFIX`와 `LAB_AGENT_NAME`이 들어 있어야 합니다.
`LAB_PREFIX`와 `LAB_AGENT_NAME`은 이번 조가 아직 사용하지 않은 이름이어야 합니다. 암호·API key·access token은 넣지 않습니다.

**저장소 루트**에는 `azure.yaml`, `scripts/`, `src/`, `.env`가 있습니다. 숨김 파일 `.env`는 편집기의 **파일 열기**로 열며 `.env.txt`로 저장하지 않습니다. Python이 읽으므로 **실행하거나 `source .env`하지 않습니다.** `<subscription-id>` 같은 표시는 꺾쇠까지 실제 값으로 바꿉니다. 모르는 값은 추측하지 말고 준비부터 마칩니다.

### 1-2. 가상환경과 로컬 테스트

```bash
python3.13 -m venv src/agent/.venv &&
source src/agent/.venv/bin/activate &&
python -m pip install -r requirements.txt &&
python -m unittest discover -s tests -v
```

테스트 마지막에 **`OK`가 나온 뒤**, 같은 터미널에서 **1-3 로그인 → 1-4 프로젝트 연결** 순서로 진행합니다.

<a id="login"></a>

### 1-3. 지금 Azure CLI와 azd에 로그인

**로그인은 여기서 합니다. 아직 `preflight`나 `bind`를 실행하지 않습니다.**
`.env`를 열고 아래 질문에 `AZURE_TENANT_ID`와 `AZURE_SUBSCRIPTION_ID`의 **`=` 오른쪽 값만** 붙여넣습니다.
브라우저에서 선택할 계정은 같은 파일의 **`AZURE_EXPECTED_USERNAME`**입니다.

```bash
export AZURE_CONFIG_DIR="$PWD/.azure-cli" &&
read -r -p ".env의 AZURE_TENANT_ID 값: " LOGIN_TENANT_ID &&
read -r -p ".env의 AZURE_SUBSCRIPTION_ID 값: " LOGIN_SUBSCRIPTION_ID
```

첫 줄은 **Azure CLI의 실습용 로그인·구독 설정을 이 폴더에 분리**합니다. 다른 작업에서 쓰던 기본 CLI 구독은 바꾸지 않습니다.
`.azure-cli/`에는 로그인 캐시가 생기므로 공유하거나 커밋하지 않습니다.

**먼저 Azure CLI에 로그인합니다.**

```bash
az login --tenant "$LOGIN_TENANT_ID" --subscription "$LOGIN_SUBSCRIPTION_ID" --output none
```

열린 브라우저에서 `.env`의 계정을 선택하고 MFA를 완료합니다. 다른 계정이 보이면 **다른 계정 사용**을 선택합니다.
터미널에 구독 선택이 나오면 `.env`의 구독 ID와 같은 항목을 선택합니다. 오류 없이 터미널 A의 입력 프롬프트가 돌아올 때까지 기다립니다.

**이어서 azd에 별도로 로그인합니다.** Azure CLI 로그인만으로 이 단계가 완료되지는 않습니다.

```bash
azd auth login --tenant-id "$LOGIN_TENANT_ID"
```

브라우저가 열리면 **같은 계정**을 선택하고 인증을 마칩니다. 암호·MFA·로그인 코드는 터미널 명령이나 녹화에 넣지 않습니다.
로그인이 완료되지 않았는데 브라우저도 열리지 않으면 [로그인 문제 해결](docs/troubleshooting.ko.md#login)을 따릅니다.

**두 로그인 결과를 확인합니다.**

```bash
az account show --subscription "$LOGIN_SUBSCRIPTION_ID" \
  --query "{user:user.name,tenant:tenantId,subscription:id,state:state}" --output json &&
azd auth status --output json
```

`user`와 `email`은 `.env`의 `AZURE_EXPECTED_USERNAME`, `tenant`와 `subscription`은 입력한 `.env`의 두 ID와 일치해야 합니다.
또한 `state`는 **`Enabled`**, azd의 `status`는 **`authenticated`**여야 합니다. 하나라도 다르면 1-4로 넘어가지 말고 1-3에서 올바른 계정으로 다시 로그인합니다.

<a id="project-binding"></a>

### 1-4. 로그인 확인 후 프로젝트 연결

```bash
python scripts/workshop.py preflight
```

**연결 전 확인:** `language: ko`, `missing_models: []`, 네 후보의 `deployed: true`를 확인합니다. 명령이 성공했어도 `language: en`이면 한국어 실습이 아닙니다. 아직 사용하지 않은 폴더의 설정만 바로잡고, 기존 실행의 언어를 바꾸어 표시하지 않습니다.

위 값이 맞을 때만 연결합니다.

```bash
python scripts/workshop.py bind
```

**완료 확인:** 내 agent와 프로젝트에 대해 `Bound ...`가 출력됩니다. `bind`는 **지금 사용하는 폴더의 azd 설정**을 연결하므로 강사가 다른 PC에서 실행했더라도 필요합니다.

<a id="resume-shell"></a>

**터미널 사용 규칙:** 이후 명령은 **저장소 루트의 터미널 A**에서 실행하며, 3단계에서만 두 번째 터미널을 사용합니다.
**새 터미널을 열 때마다** `bash`를 실행하고 같은 폴더로 돌아와 아래 두 줄을 적용합니다. 로그인 캐시가 유효하면 재로그인은 필요 없습니다.

```bash
source src/agent/.venv/bin/activate &&
export AZURE_CONFIG_DIR="$PWD/.azure-cli"
```

명령이 오류로 끝나면 다음 단계로 넘어가지 말고 [문제 해결](docs/troubleshooting.ko.md)을 확인합니다.
기본 Azure CLI 구독을 바꾸는 `az account set`은 사용하지 않습니다.

<details>
<summary>예시: preflight 완료 화면</summary>

네 모델의 `deployed: true`와 빈 `missing_models`를 확인합니다. 현재 코드의 `language: ko`는 과거 캡처에 없을 수 있습니다.

![로그인 후 네 모델과 프로젝트 준비 상태 확인](docs/assets/live-20260914-2034/screenshots/00-30-ready-after.webp)

</details>

<a id="lab-a"></a>
<a id="5-실습-a--조직의-기억을-foundry-iq에-넣기"></a>
<a id="2-조직의-지식-넣기--실습-a"></a>

## 2. 조직의 지식 넣고 검색하기

**할 일:** 정책을 검색할 **지식베이스(KB)**를 만들고 근거를 조회합니다. 먼저 `data/policies.json`에서 적용일·문서 상태·숙박 한도를 읽습니다.
비교 중에는 정책 파일을 **수정하지 않습니다.**

```bash
python scripts/workshop.py prepare-iq &&
python scripts/workshop.py retrieve --query "2026년 9월 국내 출장 숙박비 한도는 얼마인가요?"
```

**완료 확인:** 내 접두사의 KB가 생성되고 검색 결과에 `knowledge_base`, `document_ids`, `activity`가 있습니다.
현재·과거 문서가 함께 나오면 적용일을 비교합니다. 다른 조의 객체를 덮어쓰지 않습니다.

**포털 확인:** [Foundry](https://ai.azure.com/)에 `AZURE_EXPECTED_USERNAME` 계정으로 별도 로그인합니다. 리소스 `AZURE_AI_ACCOUNT_NAME`과 프로젝트 `AZURE_AI_PROJECT_NAME`을 대조한 뒤 **Knowledge → Knowledge bases**를 엽니다.

이후 **New Foundry·영어 메뉴**를 사용합니다. “내 agent”는 `LAB_AGENT_NAME`, KB와 source는 `LAB_PREFIX` 뒤에 각각 `-kb`, `-source`를 붙인 이름입니다. 예시가 아닌 내 이름을 확인합니다.

![실제 KB와 source](docs/assets/live-20260914-2034/screenshots/A-P01-knowledge-after.webp)

<a id="local"></a>
<a id="6-실습-b--python-에이전트를-hosted-agent로-배포"></a>
<a id="3-로컬에서-한-번-실행하기--실습-b"></a>

## 3. 로컬에서 한 번 실행하기

**할 일:** V1 지침으로 서버를 띄우고, 실제 검색과 모델 응답을 확인합니다.

### 3-1. 터미널 A에서 서버 시작

**터미널 A**의 절대 경로를 복사합니다. 터미널 B에서 같은 폴더로 이동할 때 씁니다.

```bash
pwd
```

이어서 터미널 A에서 서버를 시작하고 **그대로 실행해 둡니다.**

```bash
python scripts/workshop.py set-prompt v1 &&
azd ai agent run --no-client
```

오류 traceback 없이 서버가 **8088 포트에서 수신을 시작할 때까지** 기다립니다. 터미널 A는 입력 프롬프트로 돌아오지 않고 **계속 실행 중**이어야 합니다.

### 3-2. 터미널 B에서 요청 보내기

터미널 A는 실행해 둡니다. 새 창 **터미널 B**에서 Bash를 실행합니다.

```bash
bash
```

터미널 A의 **절대 경로를 따옴표 없이** 입력합니다. 이 블록이 같은 폴더·Python 환경·CLI 프로필을 터미널 B에 복원합니다.

```bash
read -r -p "터미널 A에서 확인한 실습 폴더 경로: " WORKSHOP_DIR &&
cd "$WORKSHOP_DIR" &&
source src/agent/.venv/bin/activate &&
export AZURE_CONFIG_DIR="$PWD/.azure-cli" &&
curl --fail --show-error --write-out '\nHTTP %{http_code}\n' http://127.0.0.1:8088/readiness &&
python scripts/workshop.py smoke --local
```

**완료 확인:** 터미널 B의 **`HTTP 200`**, 실제 한국어 답변, `model_key: sol`, `language: ko`, `prompt_version: v1`을 확인합니다.
Readiness만으로 추론 성공을 판단하지 않습니다. `smoke`는 호출·모델 연결 확인이지 **품질 만점 검사**가 아닙니다. V1 인용 문제는 5–6단계에서 검토합니다.

<details>
<summary>예시: 실제 로컬 응답</summary>

Readiness뿐 아니라 실제 답변·인용·`model_key`·`prompt_version`을 확인합니다.

![실제 로컬 응답](docs/assets/live-20260914-2034/screenshots/B06-local-smoke-retry-after.webp)

</details>

### 3-3. 서버를 멈추고 터미널 A로 복귀

**터미널 A에서 `Ctrl+C`**를 누릅니다. 입력 프롬프트가 돌아온 뒤에만 4단계로 진행합니다. 터미널 B는 닫아도 되며, 이후 명령은 모두 터미널 A에서 실행합니다.

<a id="deploy"></a>
<a id="4-hosted-agent로-배포하기--실습-b"></a>

## 4. Hosted Agent로 배포하기

**할 일:** 같은 코드를 Azure에 배포하고, 원격에서 실제로 호출합니다. 로컬 Docker는 필요 없습니다.

```bash
azd deploy --no-prompt &&
python scripts/workshop.py grant-agent-access &&
python scripts/workshop.py smoke
```

**완료 확인:** 실제 한국어 답변과 `trace_id`, `language: ko`, `prompt_version: v1`, **숫자로 된 `agent_version`**이 있습니다.
버전 번호를 따로 적어 둡니다. 반드시 `1`이라고 가정하지 않습니다.

`grant-agent-access`에서 권한 오류가 나면 **이번 agent의 instance identity에 필요한 역할 부여를 강사에게 요청**합니다.
다른 계정으로 바꾸거나 Owner 권한을 임의로 추가하지 않습니다.

**포털 확인:** **Agents → 내 agent → Playground**에서 같은 버전을 선택합니다. 탭 이동 후에도 버전을 다시 확인합니다.

<details>
<summary>예시: 실제 원격 응답</summary>

원격 응답의 숫자 `agent_version`과 `trace_id`를 확인합니다. 로컬 성공과 원격 성공은 별개입니다.

![실제 원격 응답](docs/assets/live-20260914-2034/screenshots/B10-remote-smoke-after.webp)

</details>

<a id="lab-c"></a>
<a id="7-실습-c--네-모델-baseline과-foundry-evaluation"></a>
<a id="5-네-모델의-baseline-평가하기--실습-c"></a>

## 5. 네 모델의 baseline 평가하기

**할 일:** **dev**(비교용 질문) 6문항을 네 모델에 보내 V1 기준 결과를 `baseline`으로 저장합니다. `--label`은 결과 폴더 이름이며 이후 `improved`, `holdout`을 그대로 사용합니다.

**Judge**는 답변 텍스트를 채점하는 별도 보조 모델이며, 네 후보 중 하나가 아닙니다.

### 5-1. 지금 폴더에서 judge 확인

```bash
python scripts/workshop.py calibrate
```

**`Judge calibration passed`**를 확인합니다. 고정 정답·오답 예제 2건은 64응답에서 제외하며, 같은 입력의 완료된 calibration은 재사용합니다. 실패하면 [calibration부터 복구](docs/troubleshooting.ko.md#calibration)합니다.

### 5-2. Baseline 24응답 수집

```bash
python scripts/workshop.py collect --split dev --label baseline
```

오류 없이 **`24/24`**로 끝나는지 확인합니다. `src/agent/.foundry/results/baseline/business-summary.json`의 네 모델이 각각 `total: 6`이어야 합니다.

<a id="baseline-evaluation"></a>

### 5-3. 저장된 응답 평가

```bash
python scripts/workshop.py evaluate --label baseline
```

**완료 확인:** **`Foundry evaluation completed: ... (24 rows)`**가 출력됩니다.

**다음 행동:** 실행 오류 없이 24행 평가가 끝났다면 **점수가 낮아도** 아래 포털 확인을 마치고 6단계로 진행합니다. 누락·중복·오류·`null` 점수는 [평가 복구](docs/troubleshooting.ko.md#evaluation-retry)가 필요합니다. 완료된 수집을 반복하지 않습니다.

**두 검사 구분:** Python은 판단·금액·인용 ID를 검사합니다. Foundry는 답변 텍스트의 **groundedness(근거성)·relevance(관련성)**를 1–5점으로 평가하며 4점 이상 통과입니다. 한쪽의 통과가 다른 쪽의 통과를 뜻하지는 않습니다.

<a id="무엇을-평가하나요"></a>

<details>
<summary>평가 원리: 입력·기준·필드 매핑</summary>

`data/dev.jsonl`은 **현행 한도, 사전 승인, 과거 규정, 정책 밖 질문, 금지 항목, 규정 무시 요청**을 다룹니다.
각 질문에 네 모델이 각각 답하므로 **6문항 × 4모델 = 24응답**입니다. 정답을 모델 대신 입력하거나 녹화의 답을 재사용하지 않습니다.

| 검사 | 실제 입력과 기준 | 무엇을 알 수 있나요? |
|---|---|---|
| 업무 검사 — Python | `decision`, `answer`의 필수 금액, `citations`를 고정 dev 기준과 비교 | 회사가 정한 판단·금액·문서 ID 계약을 지켰는가 |
| Foundry `groundedness` | 질문 + **답변 텍스트** + 그 호출의 검색 근거. 1–5점, **4점 이상 통과** | 답변의 주장이 제공된 근거로 뒷받침되는가 |
| Foundry `relevance` | 질문 + **답변 텍스트**. 1–5점, **4점 이상 통과** | 질문에 관련 있고 충분한 답을 했는가 |

`collect`는 실제 Hosted Agent를 호출하고 업무 검사를 수행합니다. `evaluate`는 **이미 수집한 같은 응답**을 Foundry에 제출합니다. 평가 때 agent를 다시 호출하지 않습니다.
JSONL에 정답도 보관하지만, 이 두 native evaluator의 입력 매핑에는 `ground_truth`·`decision`·`citations`가 없습니다. **높은 groundedness만으로 업무 정답이나 인용 ID까지 합격했다고 판단하면 안 됩니다.**

</details>

**포털 확인:** `evaluate`가 출력한 report URL을 열면 **내 평가 run으로 바로 이동**합니다. 같은 주소는 `src/agent/.foundry/results/` 아래 **`baseline/evaluation.json → run → report_url`**에도 저장됩니다. 직접 찾을 때는 왼쪽 전역 **Evaluations**를 사용하며 agent 상세의 Evaluation 탭과 구분합니다.

**화면에서 볼 것:** 평가 run의 완료 상태, 행 수, 두 evaluator의 결과입니다. 업무 검사 결과는 별도의 `business-summary.json`에서 읽습니다.

![실제 baseline 평가](docs/assets/live-20260914-2034/screenshots/C-P02-baseline-report-after.webp)

<a id="lab-d"></a>
<a id="8-실습-d--점수가-아니라-실패를-학습-자산으로"></a>
<a id="6-실패-한-건을-찾아-이유-남기기--실습-d"></a>

## 6. 한 사례를 검토하고 이유 남기기

**할 일:** 실제 응답 하나와 **trace**(검색·모델 호출 기록)를 확인합니다. 검토한 질문·고정 정답·원래 trace를 연결한 **회귀 사례**를 남깁니다.

### 6-1. 보고서와 trace 준비

```bash
python scripts/workshop.py compare --labels baseline &&
python scripts/workshop.py monitor --label baseline
```

**완료 확인:** `monitor`의 `complete: true`, `expected_trace_count: 24`, `observed_trace_count: 24`입니다. 다르면 feedback 전에 [모니터링 복구](docs/troubleshooting.ko.md#telemetry)를 마칩니다.

### 6-2. 한 사례를 골라 원인 설명

`compare`는 보고서를 출력하고 **`src/agent/.foundry/results/comparison.json`**에도 저장합니다. 이 파일을 편집기로 엽니다. 아래 화살표는 포털 메뉴가 아니라 **JSON 필드의 위치**입니다.

1. **`labels → baseline → business_failures`**에서 한 행을 고릅니다. `row_id`, `trace_id`, false인 `checks`를 읽습니다.
2. 편집기로 `src/agent/.foundry/results/baseline/responses.jsonl`을 엽니다. 한 줄이 JSON 객체 하나이며, **줄 번호가 아닌 `row_id`**를 찾습니다(`Ctrl+F`, macOS는 `⌘F`). **`answer`·`decision`·`citations`·`source_ids`**를 대조합니다. 화면 자동 줄바꿈만 켜고 파일은 수정하지 않습니다.
3. 포털 **내 agent → Traces**에서 해당 `trace_id`로 검색합니다. 기간을 맞추고 Graph view의 검색·모델 span을 확인합니다.
4. 이 행의 근거로 **원인과 바꿀 점**을 설명합니다.

`business_failures`가 비어 있으면 실패를 꾸미지 않습니다. [전부 통과했을 때의 검토 방법](docs/troubleshooting.ko.md#no-failures)을 따릅니다.

<a id="실제-예시-금액은-맞는데-왜-실패했나요"></a>

<details>
<summary>예시: 검색 문제와 지침 문제를 어떻게 구분하나요?</summary>

촬영 실행의 `baseline-sol-D01`은 **170,000원 숙박비가 180,000원 한도 이내**라는 답과 `allowed` 판단을 맞혔습니다.
하지만 `citations`에 문서 키 `TRAVEL-2026` 대신 **`"현행 국내 출장비 규정"`이라는 제목**을 넣었습니다.

| 확인 항목 | 실제 관찰 | 원인 판단 |
|---|---|---|
| 답변·판단·금액 | 맞음 | 모든 답변이 사실상 틀린 사례는 아님 |
| 검색 `source_ids` | `TRAVEL-2026`이 실제로 있음 | 검색 누락을 원인으로 분류하지 않음 |
| `citations_retrieved`, `citations_relevant` | 둘 다 `false` | 검색 문서 키와 인용 값이 일치하지 않음 |
| V1 지침 | “내부 문서 식별자는 사용자에게 표시하지 마세요” | 업무 검사와 충돌하는 지침을 개선 대상으로 선택 |

`feedback`은 이 사례의 **고정 dev 정답과 원래 trace**를 회귀 데이터로 연결합니다.
모델의 답을 새 정답으로 복사하거나 모델 가중치를 학습시키는 명령이 아닙니다. V2 수집기는 이 데이터를 실제로 읽어 같은 사례를 다시 확인합니다.

</details>

### 6-3. 내 검토 기록 저장

**검토한 `row_id`와 10자 이상의 이유**를 입력합니다. “관찰 → 근거 → 바꿀 점” 순서로 쓰며, 예시 ID·설명을 그대로 복사하지 않습니다.

```bash
read -r -p "검토한 row_id: " ROW_ID &&
read -r -p "확인한 실패 원인과 근거: " REVIEW_REASON &&
python scripts/workshop.py feedback --label baseline --row-id "$ROW_ID" \
  --reason "$REVIEW_REASON" --reviewer human
```

**완료 확인:** `src/agent/.foundry/datasets/regression-*.jsonl`이 저장되고 원래 trace가 연결됩니다.
기준 정답은 바꾸지 않습니다. 자동 실행에서는 `--reviewer assistant`로 표시하며 사람의 승인으로 기록하지 않습니다.

**화면에서 볼 것:** 선택한 **같은 trace** 안의 검색 span과 모델 span입니다. 다른 요청의 검색 결과를 원인 분석에 섞지 않습니다.

![실제 실패 요청의 span graph](docs/assets/live-20260914-2034/screenshots/D-P04-graph-after.webp)

<a id="lab-e"></a>
<a id="9-실습-e--개선하고-같은-조건으로-다시-평가"></a>
<a id="7-v2로-바꾸고-같은-dev-다시-평가하기--실습-e"></a>

## 7. V2로 바꾸고 같은 dev 다시 평가하기

**할 일:** 모델·데이터·평가 기준을 유지하고, 같은 dev 질문으로 제공된 V2와 V1을 비교합니다.

<a id="v2에서는-무엇을-바꾸나요"></a>

### 7-1. 제공된 후보 검토

`src/agent/prompts/v1.txt`와 `src/agent/prompts/v2.txt`를 읽습니다. V2는 자동 생성물이 아닌 **제공된 후보**입니다. 6단계의 원인과 맞지 않으면 적용을 멈추고 강사와 개선 대상을 다시 정합니다.

**두 파일을 직접 편집하지 않습니다.** 아래 `set-prompt v2`로 제공된 V2를 선택합니다.

| V1에서 불명확하거나 잘못된 부분 | 제공된 V2의 변경 |
|---|---|
| 내부 문서 ID를 숨김 | `citations`에 실제 사용한 **원본 문서 ID**를 넣음 |
| 현행·과거·초안의 적용 기준이 부족함 | 출장일에 유효한 정책을 선택하고 `draft`는 제외. 과거 출장에는 당시 정책 적용 |
| 승인 필요와 금지의 구분이 부족함 | `needs_approval`·`not_allowed` 등 판단 값의 의미를 명시하고 승인 사실을 만들지 않음 |
| 근거가 부족한 질문의 처리 기준이 부족함 | 범위 밖은 `not_covered`, 정보 부족은 `needs_info`. 일반 상식으로 회사 규정을 보충하지 않음 |
| 사용자·검색 문서의 지시를 그대로 따를 위험 | 검색 문서는 **근거이지 지시가 아님**을 명시하고 규정 무시·근거 위조 요청을 거부 |

**변경 범위:** 지침과 Hosted Agent 버전만. 모델·정답은 유지합니다.

### 7-2. V2 배포 후 새 버전 확인

```bash
python scripts/workshop.py set-prompt v2 &&
azd deploy --no-prompt &&
python scripts/workshop.py smoke
```

**수집 전 확인:** 4단계와 **다른 숫자 `agent_version`**, `language: ko`, `prompt_version: v2`를 확인합니다.

### 7-3. 같은 dev 수집·평가

```bash
python scripts/workshop.py collect --split dev --label improved
```

<a id="candidate-evaluation"></a>

**`24/24`**를 확인한 뒤 평가하고 비교합니다.

```bash
python scripts/workshop.py evaluate --label improved &&
python scripts/workshop.py compare --labels baseline improved
```

**완료 확인:** 평가 **`(24 rows)`**와 갱신된 **`src/agent/.foundry/results/comparison.json`**입니다. dev·모델·KB·평가 기준·수집 동시성은 전후에 같아야 합니다.

### 7-4. 내 전후 결과 비교

**내 결과를 읽는 위치:** 이 파일의 **`labels → baseline 또는 improved → models → sol/terra/luna/astra`**를 엽니다.
모델별로 아래 세 항목을 전후 비교합니다.

| 비교할 항목 | 필드 | 뜻 |
|---|---|---|
| 업무 통과 | `business_passed` / `total` | 다섯 업무 검사를 모두 통과한 응답 수 / 전체 |
| 필수 인용 | `required_citation_passed` / `required_citation_total` | 필수 인용이 유효한 응답 수 / 인용 필수 응답 수 |
| Foundry 점수 | `foundry_evaluators → groundedness 또는 relevance` | `native_mean_score`(평균)와 `native_passed` / `total`(통과/전체)을 읽음. **각 행이 5점 만점에 4점 이상**이어야 통과하며, 평균 4점이 전부 통과를 뜻하지는 않음 |

**판단:** 좋아지지 않았거나 악화됐다면 그대로 기록합니다. V2를 자동 채택하거나 평가 기준을 낮추지 않습니다. 8단계는 이 후보를 평가하는 것이지 **운영 도입을 결정하는 단계가 아닙니다.**

<a id="실제-실행에서는-무엇이-좋아졌나요"></a>

<details>
<summary>촬영한 한국어 실행 결과 — 내 목표 점수가 아닌 예시</summary>

아래는 **촬영 실행의 같은 dev 24응답 전후 비교**입니다. 본인 실행에서도 동일하게 나온다고 보장하지 않습니다.

| 지표 | V1 | V2 | 해석 |
|---|---:|---:|---|
| 모든 업무 검사를 통과한 응답 | 0/24 | 24/24 | 이 실행의 업무 계약 준수가 개선됨 |
| 올바른 `decision` | 23/24 | 24/24 | Sol의 D02가 `not_allowed`에서 `needs_approval`로 교정됨 |
| 필수 인용이 유효한 응답 | 0/20 | 20/20 | 제목 대신 실제 검색 문서 ID를 사용 |
| Groundedness 통과 | 24/24 | 24/24 | 이미 높았고 통과 건수는 개선되지 않음 |
| Relevance 통과 | 21/24 | 21/24 | **전체 통과 건수는 그대로임** |

**0/24 → 24/24를 일반적인 답변 정확도 0% → 100%로 해석하지 않습니다.** V1은 인용 규칙이 잘못된 교육용 출발점이며, 24행 모두 인용 검사에서 실패했습니다.
V2도 정책에 없는 해외 한도를 올바르게 보류한 D04에서 Terra·Luna·Astra의 relevance가 **3점**이었습니다. 업무 기준과 일반 judge의 “충분한 답변” 기준이 다를 수 있으므로 점수를 합격으로 고치지 않습니다.

</details>

<a id="portal-comparison"></a>

<details>
<summary>선택: 포털에서 두 버전 비교 — 추가 모델 호출</summary>

**내 agent → Playground → Version 선택 상자 → Compare versions**를 엽니다. 양쪽이 같은 버전으로 열릴 수 있으므로 왼쪽은 V1, 오른쪽은 V2의 실제 버전 번호를 선택합니다. 어느 쪽 입력창이든 아래 dev 질문을 붙여넣습니다.

```json
{
  "query": "2026년 9월 10일 부산 출장에서 1박 숙박비 170000원은 규정상 가능한가요? 한도도 알려주세요.",
  "model_key": "sol",
  "case_id": "D01",
  "run_id": "portal-ko-comparison"
}
```

**Send는 한 번만** 누릅니다. 비교 화면이 양쪽 버전을 함께 호출합니다. 각 응답의 `language`, `prompt_version`, `citations`, 서로 다른 `trace_id`를 확인합니다. 추가 시연 호출이며 수집한 24 + 24응답을 대체하거나 통계에 더하지 않습니다.

**화면에서 볼 것:** 왼쪽 V1은 문서 제목, 오른쪽 V2는 `TRAVEL-2026`을 인용합니다.

![실제 V1/V2 응답 비교](docs/assets/live-20260914-2034/screenshots/E-P03-compare-results-after.webp)

</details>

**다음 필수 단계:** [8. 후보 고정 후 holdout 평가](#lab-f).

<a id="lab-f"></a>
<a id="10-실습-f--holdout과-frontier-ecosystem-테스트"></a>
<a id="8-후보를-고정하고-holdout-평가하기--실습-f"></a>

## 8. 후보를 고정하고 holdout 평가하기

**할 일:** 이제부터 V2의 지침·모델·검색 설정을 바꾸지 않습니다. **Holdout**은 이 시점까지 열지 않은 별도 검증 질문입니다. 4문항을 네 모델로 평가합니다.

```bash
python scripts/workshop.py collect --split holdout --label holdout
```

<a id="holdout-evaluation"></a>

**`16/16`**을 확인한 뒤 평가합니다.

```bash
python scripts/workshop.py evaluate --label holdout &&
python scripts/workshop.py compare --labels baseline improved holdout
```

**완료 확인:** 수집 **`16/16`**, 평가 완료 메시지의 **`(16 rows)`**, 7단계와 **같은 `agent_version` 및 `prompt_version: v2`**를 확인합니다.
`comparison.json`의 **`labels → improved`**와 **`labels → holdout`**에서 `agent_version`과 `prompt_hash`를 대조합니다. 포털은 이전 dev 보고서가 아니라 holdout의 `evaluate`가 출력한 report URL로 엽니다.
결과를 본 뒤 prompt를 고치고 같은 holdout을 다시 “미사용 검증”으로 제출하지 않습니다.
이 저장소의 4문항은 교육용이며, 재실행 결과가 새로운 독립 검증셋이나 운영 품질을 보장하지 않습니다.

촬영 실행의 점수와 한계는 [한국어 평가 결과](docs/validation.ko.md#measured-results)에서 별도로 확인합니다. 본인의 점수를 예시에 맞추지 않습니다.

**화면에서 볼 것:** dev의 24행이 아니라 **holdout 16행**인지 확인합니다.

![실제 holdout 평가](docs/assets/live-20260914-2034/screenshots/F-P01-holdout-report-after.webp)

<a id="lab-g"></a>
<a id="11-실습-g--trace와-monitor의-차이"></a>
<a id="9-운영-신호와-전체-증거-확인하기--실습-g"></a>

## 9. 운영 신호와 전체 증거 확인하기

**할 일:** Trace는 **한 요청의 원인**, Monitor는 **여러 요청의 지연·실패·토큰 추이**를 확인하는 데 사용합니다.

### 9-1. 전체 응답·평가·trace 검증

`monitor`는 해당 label의 trace를 검증하고 batch session을 중지합니다. 기본 범위는 **최근 2시간**입니다. 오래된 실행은 [조회 기간을 늘리며](docs/troubleshooting.ko.md#telemetry), trace를 찾으려고 응답을 재수집하지 않습니다.

```bash
python scripts/workshop.py monitor --label improved &&
python scripts/workshop.py monitor --label holdout &&
python scripts/workshop.py verify --baseline baseline --candidate improved --holdout holdout
```

**완료 확인:** `language: ko`, `component_execution_verified: true`, `primary_model_outputs: 64`, `distinct_verified_traces: 64`입니다.
총 응답은 **24 + 24 + 16 = 64**이며, 개선 실행이 6단계의 회귀 데이터를 실제로 재사용해야 합니다.

<a id="completion-decision"></a>

**`src/agent/.foundry/results/verified-evidence.json`을 열고 다음 행동을 결정합니다.**

| 결과 | 뜻 | 다음 행동 |
|---|---|---|
| 오류·파일 누락·완료 기준 불일치 | 실행 미완료 또는 다른 실행 | [실패한 단계 복구](docs/troubleshooting.ko.md#resume). 증거 파일을 고쳐 완료로 만들지 않음 |
| 완료 기준 일치, `candidate_quality_gates`에 `false`가 있음 | 실행 완료, 업무 gate 미통과 | 그대로 보고 → 포털 9-2 → 정리 10. 점수를 높이려 재실행하지 않음 |
| 완료 기준 일치, `candidate_quality_gates`가 모두 `true` | 업무 gate 통과. **Native 미통과는 남을 수 있음** | Native 미통과·한계도 보고 → 포털 9-2 → 정리 10 |

Gate 위치는 **`candidate_quality_gates → sol/terra/luna/astra → dev / holdout`**입니다. 모델마다 **dev 최소 5/6, holdout 4/4 업무 통과 + 각 split의 필수 인용 전부 유효**가 필요합니다.

**`production_release_approved: false`는 정상입니다.** 두 완료 경로 모두 운영 승인이 아니므로 값을 바꾸지 않습니다.

<details>
<summary>예시: 전체 실행 증거 확인</summary>

![실제 응답·trace·평가·lineage 검증](docs/assets/live-20260914-2034/screenshots/G03-verify-after.webp)

</details>

### 9-2. 운영 대시보드 확인

**포털 확인:** **내 agent → Monitor → Last Day**에서 내 실행 시간대의 요청·토큰·지연·오류를 봅니다.

대시보드에는 smoke·추가 포털 호출도 포함되므로 합계가 64와 달라도 됩니다. 실제 오류는 원인을 확인하며, batch 성공만으로 전체 환경의 오류가 0이라고 기록하지 않습니다. 해석이 필요하면 [평가 방법·비용·한계](docs/validation.ko.md)를 참고합니다.

<a id="cleanup"></a>
<a id="12-마무리와-비용-정리"></a>

## 10. 내 실습 자원만 정리하기

**할 일:** trace·포털 검토와 9단계 결과 저장을 마친 뒤 정리합니다. 정리하면 live agent와 지식 객체는 없어지지만 로컬 응답·평가 파일은 남습니다. 먼저 **삭제 계획만** 확인합니다.

### 10-1. 삭제 계획만 확인

```bash
python scripts/workshop.py cleanup --dry-run
```

계획의 agent·모델·KB·역할이 **이번 실습에서 만든 대상인지** 확인합니다.
모르는 이름이나 다른 조의 자원이 있으면 중단합니다. 공유 프로젝트에서 `azd down`이나 resource group 전체 삭제를 실행하지 않습니다.

### 10-2. 검토한 계획만 실행

```bash
python scripts/workshop.py cleanup --confirm &&
python scripts/workshop.py check-cleanup
```

**완료 확인:** `temporary_hosted_agent_absent: true`, `existing_foundry_project_preserved: true`, `existing_search_service_preserved: true`입니다. 삭제 건수는 예시 화면이 아닌 **내 계획**과 대조합니다. 강사가 준비한 모델은 임의로 삭제하지 않습니다.
Search 가동·로그 보존·기반 서비스·보조 모델의 비용은 남을 수 있으며, 환경 소유자가 최종 정리를 별도로 관리합니다.

<details>
<summary>예시: 정리 완료 확인</summary>

![실제 Azure 정리 재확인](docs/assets/live-20260914-2034/screenshots/H03-cleanup-check-after.webp)

</details>

## 끝나면 남는 것

| 위치 | 내용 |
|---|---|
| `src/agent/.foundry/results/baseline/` | V1의 24응답과 평가 |
| `src/agent/.foundry/results/improved/` | V2의 24응답과 평가 |
| `src/agent/.foundry/results/holdout/` | 고정 후보의 16응답과 평가 |
| `src/agent/.foundry/datasets/regression-*.jsonl` | 검토 이유·고정 정답·원래 trace |
| `src/agent/.foundry/results/verified-evidence.json` | 전체 실행·lineage 검증 |

이 파일들은 뒤 단계의 입력이므로 실습이 끝나기 전에 지우거나 예시 결과로 바꾸지 않습니다.

**촬영 점수가 아닌 내 저장 결과로 세 가지를 설명합니다.**

- **검토:** `row_id`·원래 trace·관찰한 문제와 근거.
- **변화:** 네 모델 각각의 업무 통과·필수 인용·native 평균과 통과 건수의 전후 차이.
- **판단:** Holdout 결과·품질 gate·남은 한계. 운영 승인이나 모델의 통계적 우월성으로 확대 해석하지 않습니다.

<a id="summary-video"></a>

## 전체 흐름을 영상으로 다시 보기 — 선택 사항

<details>
<summary>한국어 실습 요약 영상 보기 — 21분 55초</summary>

[전체 실습 요약 영상 1개 — 21분 55초, 클릭해서 재생](https://github.com/user-attachments/assets/98446bdb-072d-44a5-95d7-4965ccf1c010)

영상은 온라인으로 재생합니다. 저장소에는 동일한 MP4 복사본을 포함하지 않습니다.
영상은 환경 준비 중 calibration을 확인했으며, 현재 본문은 baseline 평가 직전에도 이를 명시합니다. 과거 영상과 명령 묶음이 다르면 현재 본문의 완료 기준을 따릅니다. 촬영 당시 경로·이름을 복사하지 않습니다.

</details>

## 필요한 참고 문서

[평가 방법과 개선 결과](docs/validation.ko.md) · [설계·모델·공식 출처](docs/reference.ko.md) · [문제 해결](docs/troubleshooting.ko.md) · [강사 준비](docs/instructor.ko.md) · [새 Azure 환경 생성](docs/environment.ko.md) · [GHCP로 진행 — 선택](docs/copilot.ko.md)
