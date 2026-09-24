# 출장 규정 에이전트를 실행하고, 평가하고, 개선하기

[English guide](README.md)

**120분 동안 실제 응답 48개를 모아, 지침을 바꾼 전후의 차이를 설명합니다.** 에이전트 코드와 V1·V2 지침은 모두 제공되므로 직접 작성하지 않습니다. 마지막에는 **검토한 사례, V1 → V2 비교, holdout 판단** 세 항목을 보고합니다. 목표는 만점이나 운영 승인이 아닙니다.

<a id="start-here"></a>
<a id="other-starts"></a>
<a id="다른-상황"></a>
<a id="내-상황에-맞는-시작점"></a>

## 여기서 시작하세요

**새 실습:** 아래 준비물이 있으면 [1단계](#start)부터 **1–10단계만 순서대로** 진행합니다. 참고 문서·영상·레벨 2·3을 먼저 읽을 필요는 없습니다.

**이전 실행을 이어간다면:** 새로 시작하지 말고 [같은 폴더에서 복구](docs/troubleshooting.ko.md#resume)합니다.

**1단계 전에 필요한 것:**

- **환경:** 준비된 Azure 환경(**유료** 서비스)과 완성된 조별 `.env`.
- **로컬 도구:** Git, Python 3.13, Bash, curl, 편집기, 브라우저. Windows는 WSL을 씁니다.
- **Azure 도구:** Azure CLI와 azd(`microsoft.foundry` 확장). [도구 설치·확인](docs/instructor.ko.md#tools)

도구 설치·Azure 환경 준비는 120분에 포함하지 않습니다. **로컬 실행도 유료 Azure 모델과 Search를 호출합니다.**

<details>
<summary>환경 준비가 필요하거나 Copilot에 실행을 맡기려는 경우</summary>

| 현재 상태 | 시작할 곳 |
|---|---|
| Azure 서비스는 있지만 설정·모델·권한 준비가 필요함 | 환경 소유자가 [기존 환경 준비](docs/instructor.ko.md#existing-foundation) 진행 |
| 준비된 Azure 환경이 없음 | [새 전용 환경 준비](docs/environment.ko.md)를 마치고 그 문서가 지정한 단계로 복귀 |
| Copilot CLI(GHCP)에 실행을 맡기고 싶음 | [선택 Copilot 가이드](docs/copilot.ko.md) 사용. 수동 실행과 동시에 진행하지 않음. 직접 실행에는 Copilot·Playwright가 필요 없음 |

혼자 실습하면 본인이 환경 소유자입니다. **환경 준비 경로는 하나만 선택합니다.**

</details>

<a id="실습-개요"></a>

## 10단계 실습 경로

에이전트는 출장 규정 질문에 **답변·판단(decision)·근거 문서 ID**로 답합니다. 지침 두 버전을 후보 모델 세 개로 비교합니다.

- **후보 모델:** Sol·Luna·Astra(`gpt-6-sol`·`gpt-6-luna`·`gpt-6-astra`)가 같은 질문에 각각 독립적으로 답합니다.
- **보조 모델:** `gpt-5.4-mini`는 검색 계획과 채점만 맡으며 후보가 아닙니다.
- **V1/V2**는 모델이 아니라 지침 버전입니다.

```text
질문 → Python agent → Foundry IQ로 정책 검색 → 선택한 모델 → 답변
V1: 18응답 → trace 하나 검토 → V2: 18응답 → 후보 고정 → holdout: 12응답
```

<a id="evaluation-runs"></a>

**dev**는 V1·V2 비교에 쓰는 6문항, **holdout**은 V2를 고정한 뒤 확인하는 별도 4문항입니다. `--split`은 이 질문 묶음을 고르고, `--label`은 결과 폴더에 이름을 붙입니다. **`improved`는 V2 결과의 이름이지, 개선됐다는 판정이 아닙니다.**

| 단계 | 다음으로 넘어가는 기준 |
|---|---|
| [1. 시작 준비](#start) | 테스트·두 로그인·preflight·프로젝트 연결 완료 |
| [2. 정책 검색](#lab-a) | 내 지식베이스가 `TRAVEL-2026`을 반환 |
| [3. 로컬 실행](#local) | `HTTP 200`과 실제 V1 답변 |
| [4. 배포](#deploy) | 원격 답변에 숫자 agent 버전이 있음 |
| [5. V1 평가](#lab-c) | `baseline`: `dev` 6문항 × 3모델 = V1 18응답 평가 완료 |
| [6. 한 사례 검토](#lab-d) | 원래 trace와 함께 검토 기록 저장 |
| [7. V2 평가](#lab-e) | `improved`: **같은 `dev` 6문항** × 3모델 = V2 18응답 평가 완료 |
| [8. Holdout 평가](#lab-f) | `holdout`: 따로 남겨 둔 4문항 × 3모델 = 바꾸지 않은 V2의 12응답 평가 완료 |
| [9. 증거 확인·보고](#lab-g) | 48응답·48 trace·검토 이력 검증과 세 항목 보고 |
| [10. 정리](#cleanup) | 내 소유 객체만 삭제 |

**시간:** 1–2단계 25분 · 3–4단계 15분 · 5–6단계 30분 · 7–8단계 30분 · 9–10단계 15분 · 여유 5분. **9단계 보고 → 10단계 정리** 순서입니다. 선택 실습인 [레벨 2·3](#levels)은 그 사이에 하며, 정리 뒤에는 시작하지 않습니다.

**진행 방법**

- **작업 위치:** **터미널 A**, **터미널 B**(3단계만), **편집기**, **포털** 중 블록 앞의 굵은 라벨이 가리키는 곳입니다. 포털은 **New Foundry·영어 메뉴** 기준이며 “내 agent”는 `LAB_AGENT_NAME`입니다.
- **명령:** `$` 없이 **한 블록씩**, 저장소 루트에서 실행합니다. 입력 프롬프트가 돌아올 때까지 기다립니다(3단계의 로컬 서버만 예외).
- **확인:** 블록마다 **완료 확인**을 봅니다. 다르면 출력을 보존하고 **다르면**을 따라 [그 명령만 복구](docs/troubleshooting.ko.md#resume)합니다. 점수를 높이려고 끝난 단계를 다시 실행하지 않습니다.
- **메모:** 버전 번호·검토·비교 결과를 **메모 하나**에 모아 9단계 보고에 씁니다.
- **예시:** 접힌 **예시 화면·참고 설명**은 필요할 때만 엽니다. 예시와 점수가 달라도 명령이 정상 완료됐다면 계속 진행합니다.
- **holdout:** **`data/holdout.jsonl`은 8단계 전까지 열지 않습니다.**

<a id="배경-learning-loop와-frontier-ecosystems"></a>
<a id="이-실습에서는-무엇으로-연결하나요"></a>

**선택 자료:** [Learning loop 배경](docs/reference.ko.md#background) · [용어 설명](docs/reference.ko.md#terms) · [요약 영상](#summary-video)

**이제 [1단계](#start)로 갑니다.**

<a id="start"></a>
<a id="4-시작-전-준비"></a>

## 1. 시작 준비

**목표:** 새 한국어 실습 폴더에서 로그인과 프로젝트 연결을 마칩니다.

<a id="source-setup"></a>

### 1-1. 코드와 `.env` 준비

**터미널 A — 폴더 받기:** Bash를 실행한 뒤(이미 Bash라면 첫 블록은 건너뜀) 새 폴더로 clone합니다. **사용하지 않은 clone이나 압축을 푼 ZIP 폴더**가 이미 있다면 clone 대신 그 루트로 이동합니다.

```bash
bash
```

```bash
git clone https://github.com/junwoojeong100/foundry-evaluation.git &&
cd foundry-evaluation
```

<a id="workspace-settings"></a>

**편집기 — `.env` 추가:** 강사가 준 `.env`를 이 폴더의 `README.ko.md` 옆에 저장합니다. 이미 `.env`가 있으면 덮어쓰지 말고 강사에게 확인합니다. 숨김 파일이므로 **파일 열기**로 열어 아래를 확인합니다.

- **파일:** `.env`(`.env.txt`가 아님).
- **내 값:** `LAB_LANGUAGE=ko`, `LAB_PROMPT_VERSION=v1`, 그리고 다른 참가자가 쓰지 않는 조별 이름의 `LAB_PREFIX`·`LAB_AGENT_NAME`(영문 소문자로 시작하는 3–50자의 소문자·숫자·하이픈).
- **강사 값:** `MODEL_*_DEPLOYMENT`와 `LAB_AUX_DEPLOYMENT`에 강사가 준비한 배포 이름.
- **금지:** 빈 값, `<...>` 표시, 암호, key, token.

**완료 확인:** 이 폴더에 `azure.yaml`, `scripts/`, `src/`와 위 조건을 모두 만족하는 `.env`가 있습니다. `.env`는 Python이 읽으므로 실행하거나 `source`하지 않습니다.

**다르면:** 빠진 값은 강사에게 받습니다. 추측해서 채우지 않습니다.

<details>
<summary>이 값들이 중요한 이유</summary>

- 이어서 하는 실행이라면 `LAB_LANGUAGE`와 `LAB_PROMPT_VERSION`을 바꾸지 않습니다. 결과와 소유권이 언어에 묶여 있습니다.
- `MODEL_*` 값을 바꿔도 모델이 생기지 않습니다. 조별 이름을 바꿔도 강사의 배포 이름은 유지합니다([이름 구분](docs/reference.ko.md#model-names)).

</details>

### 1-2. 가상환경과 로컬 테스트

**터미널 A — 설치:**

```bash
python3.13 -m venv src/agent/.venv &&
source src/agent/.venv/bin/activate &&
python -m pip install -r requirements.txt
```

**터미널 A — 테스트:**

```bash
python -m unittest discover -s tests -v
```

**완료 확인:** 테스트 출력이 **`OK`**로 끝납니다.

**다르면:** [증상별 확인](docs/troubleshooting.ko.md#symptoms)을 본 뒤 실패 출력을 강사와 공유합니다.

<a id="login"></a>

### 1-3. Azure CLI와 azd 로그인

**터미널 A:** 아래 네 블록을 순서대로 실행합니다. 시작 전에 확인합니다.

- `.env`에서 `=` 오른쪽 값만 붙여넣습니다.
- 암호·로그인 코드는 넣지 않습니다.
- 브라우저에서는 `AZURE_EXPECTED_USERNAME` 계정으로 로그인합니다(다른 계정이 보이면 **다른 계정 사용**).

**터미널 A — 1. ID 입력:** 이 로그인은 이 폴더의 `.azure-cli/`에만 보관합니다(공유·커밋 금지).

```bash
export AZURE_CONFIG_DIR="$PWD/.azure-cli" &&
read -r -p ".env의 AZURE_TENANT_ID 값: " LOGIN_TENANT_ID &&
read -r -p ".env의 AZURE_SUBSCRIPTION_ID 값: " LOGIN_SUBSCRIPTION_ID
```

**터미널 A — 2. Azure CLI 로그인:** 구독을 물으면 `.env`의 구독을 고릅니다.

```bash
az login --tenant "$LOGIN_TENANT_ID" --subscription "$LOGIN_SUBSCRIPTION_ID" --output none
```

**터미널 A — 3. azd 로그인:** 같은 계정을 씁니다.

```bash
azd auth login --tenant-id "$LOGIN_TENANT_ID"
```

<a id="login-check"></a>

**터미널 A — 4. 두 로그인 확인:**

```bash
az account show --subscription "$LOGIN_SUBSCRIPTION_ID" \
  --query "{user:user.name,tenant:tenantId,subscription:id,state:state}" --output json &&
azd auth status --output json
```

**완료 확인:** CLI의 `user`와 azd의 `email`이 `AZURE_EXPECTED_USERNAME`과 같고, `tenant`·`subscription`이 `.env`의 두 ID와 같으며, `state: Enabled`, `status: authenticated`입니다.

**다르면:** 지정한 계정으로 다시 로그인합니다. 브라우저가 열리지 않으면 [로그인 문제 해결](docs/troubleshooting.ko.md#login)을 따릅니다.

<a id="project-binding"></a>

### 1-4. 프로젝트 확인과 연결

**터미널 A — 프로젝트 확인:**

```bash
python scripts/workshop.py preflight
```

**완료 확인:** `language: ko`, `missing_models: []`, 그리고 `gpt-6-sol`·`gpt-6-luna`·`gpt-6-astra`의 `deployed: true`.

**다르면:** `language: en`이면 아직 쓰지 않은 폴더일 때만 `.env`를 고칩니다. `missing_models`가 비어 있지 않으면 강사에게 해당 배포 준비를 요청합니다.

<details>
<summary>예시 화면: preflight 완료와 Build → Models</summary>

세 모델의 `deployed: true`, 빈 `missing_models`, `language: ko`를 확인합니다.

![로그인 후 세 모델과 프로젝트 준비 상태 확인](docs/assets/live-ko-20260923b/screenshots/S1-02-preflight-after.webp)

같은 배포는 포털 **Build → Models**에서도 볼 수 있습니다. 이름은 강사가 준비한 실제 배포 이름이며, 모델 ID·버전이 고정 값과 같아야 합니다.

![Build → Models의 세 후보와 judge 배포](docs/assets/live-ko-20260923b/screenshots/S1-P01-models-after.webp)

</details>

<a id="bind-project"></a>

**터미널 A — 연결:** 같은 폴더에서 위 preflight 완료 기준을 확인했을 때만 연결합니다. 환경 준비 문서에서 여기로 왔다면 clone·설치·로그인을 반복하지 않습니다.

```bash
python scripts/workshop.py bind
```

**완료 확인:** `Bound <내 agent> to /subscriptions/.../projects/<내 프로젝트>`.

**다르면:** [증상별 확인](docs/troubleshooting.ko.md#symptoms)을 봅니다.

<a id="resume-shell"></a>

<details>
<summary>나중에 새 터미널을 열었다면 먼저 복원합니다</summary>

`bash`를 실행하고 이 폴더로 돌아와 아래 블록을 실행합니다. 저장된 로그인은 그대로 유효합니다.

```bash
source src/agent/.venv/bin/activate &&
export AZURE_CONFIG_DIR="$PWD/.azure-cli"
```

`az account set`은 쓰지 않으며, 실행을 시작한 뒤에는 `LAB_LANGUAGE`를 바꾸지 않습니다.

</details>

**다음:** [2. 조직의 지식 넣고 검색하기](#lab-a)

<a id="lab-a"></a>
<a id="5-실습-a--조직의-기억을-foundry-iq에-넣기"></a>
<a id="2-조직의-지식-넣기--실습-a"></a>

## 2. 조직의 지식 넣고 검색하기

**목표:** 합성 정책 7개로 만든 **지식베이스(KB)**가 맞는 정책을 찾습니다.

### 2-1. 정책 등록

**편집기:** `data/policies.json`을 열어 `TRAVEL-2026`의 적용일·상태·숙박 한도를 확인합니다. 파일은 수정하지 않습니다.

**터미널 A:**

```bash
python scripts/workshop.py prepare-iq
```

**완료 확인:** `Foundry IQ ready: <내 KB>; 7 synthetic documents.` 내 KB 이름은 `LAB_PREFIX` + `-kb`입니다.

**다르면:** 역할 부여 오류는 환경 소유자가 처리합니다. [증상별 확인](docs/troubleshooting.ko.md#symptoms)을 봅니다.

<a id="policy-retrieval"></a>

### 2-2. 검색 확인

**터미널 A:**

```bash
python scripts/workshop.py retrieve --query "2026년 9월 국내 출장 숙박비 한도는 얼마인가요?"
```

**완료 확인:** `knowledge_base`가 내 KB이고, `document_ids`에 **`TRAVEL-2026`**이 있으며, `activity`가 비어 있지 않습니다. 과거 규정이 함께 나올 수도 있습니다.

**다르면:** [검색 복구](docs/troubleshooting.ko.md#retrieval)를 따릅니다.

### 2-3. 포털에서 KB 확인

**포털:** 같은 계정으로 [Microsoft Foundry](https://ai.azure.com/)에 로그인한 뒤 차례로 엽니다.

1. 리소스 `AZURE_AI_ACCOUNT_NAME`과 프로젝트 `AZURE_AI_PROJECT_NAME`
2. **Knowledge → Knowledge bases → 내 KB**

**완료 확인:** source(`LAB_PREFIX` + `-source`)가 **Active**이고 **Retrieval instructions**가 채워져 있습니다.

**다르면:** [포털 화면 차이](docs/troubleshooting.ko.md#portal-differs)를 봅니다.

<details>
<summary>예시 화면: KB·검색 지침·source</summary>

![실제 KB·검색 지침과 source](docs/assets/live-ko-20260923b/screenshots/S2-P01-knowledge-after.webp)

</details>

**다음:** [3. 로컬에서 한 번 실행하기](#local)

<a id="local"></a>
<a id="6-실습-b--python-에이전트를-hosted-agent로-배포"></a>
<a id="3-로컬에서-한-번-실행하기--실습-b"></a>

## 3. 로컬에서 한 번 실행하기

**목표:** 내 PC에서 실행한 agent가 실제 V1 한국어 답변을 반환합니다.

### 3-1. 서버 시작

**터미널 A — 경로 복사:** 이 폴더의 경로를 출력해 복사합니다. 3-2에서 터미널 B에 붙여넣습니다.

```bash
pwd
```

**터미널 A — 서버 시작:** V1을 선택하고 서버를 시작합니다. 3-3까지 그대로 둡니다.

```bash
python scripts/workshop.py set-prompt v1 &&
azd ai agent run --no-client
```

**완료 확인:** traceback 없이 `Running on http://0.0.0.0:8088`이 나오고, 입력 프롬프트로 돌아오지 않습니다.

**다르면:** [증상별 확인](docs/troubleshooting.ko.md#symptoms)의 8088 포트 항목을 봅니다.

### 3-2. 터미널 B에서 요청 보내기

**터미널 B — Bash 시작:** 새 터미널 창을 열고, 이미 Bash가 아니라면 실행합니다.

```bash
bash
```

**터미널 B — 요청 보내기:** `터미널 A에서 확인한 실습 폴더 경로:`가 나오면 3-1에서 복사한 경로를 따옴표 없이 붙여넣습니다. 이 블록은 같은 폴더의 환경을 복원하고, readiness를 확인한 뒤 요청 하나를 보냅니다.

```bash
read -r -p "터미널 A에서 확인한 실습 폴더 경로: " WORKSHOP_DIR &&
cd "$WORKSHOP_DIR" &&
source src/agent/.venv/bin/activate &&
export AZURE_CONFIG_DIR="$PWD/.azure-cli" &&
curl --fail --show-error --write-out '\nHTTP %{http_code}\n' http://127.0.0.1:8088/readiness &&
python scripts/workshop.py smoke --local
```

**완료 확인:** **`HTTP 200`**에 이어, 비어 있지 않은 한국어 `answer`와 `model_key: sol`, `language: ko`, `prompt_version: v1`이 담긴 JSON이 나옵니다.

**다르면:** 터미널 A가 아직 실행 중인지 확인한 뒤 [증상별 확인](docs/troubleshooting.ko.md#symptoms)을 봅니다.

<details>
<summary>예시 화면: 실제 로컬 응답</summary>

![실제 로컬 응답](docs/assets/live-ko-20260923b/screenshots/S3-04-local-smoke-after.webp)

</details>

### 3-3. 서버 종료

**터미널 A:** **`Ctrl+C`**를 누른 뒤 터미널 B를 닫습니다.

**완료 확인:** 터미널 A에 입력 프롬프트가 돌아옵니다. 이후 명령은 모두 터미널 A에서 실행합니다.

**다르면:** `Ctrl+C`를 한 번 더 누르고 기다립니다.

**다음:** [4. Hosted Agent로 배포하기](#deploy)

<a id="deploy"></a>
<a id="4-hosted-agent로-배포하기--실습-b"></a>

## 4. Hosted Agent로 배포하기

**목표:** 같은 코드가 Azure에서 번호가 붙은 agent 버전으로 답합니다. 로컬 Docker는 필요 없습니다.

### 4-1. 코드 배포

**터미널 A:**

```bash
azd deploy --no-prompt
```

**완료 확인:** `SUCCESS: Your application was deployed ...`가 나오고 입력 프롬프트가 돌아옵니다.

**다르면:** 오류 출력을 보존하고 [실패한 명령만 복구](docs/troubleshooting.ko.md#resume)합니다.

<a id="agent-access"></a>

### 4-2. Agent 접근 권한 부여

**터미널 A:**

```bash
python scripts/workshop.py grant-agent-access
```

**완료 확인:** `Search read and Foundry model inference access configured for <내 agent>.`

**다르면:** **이 agent의 instance identity**에 필요한 역할을 강사에게 요청합니다. Owner 권한은 추가하지 않습니다.

<a id="hosted-smoke"></a>

### 4-3. 원격 응답 확인

**터미널 A:** 원격 agent에 요청 하나를 보내고, 출력된 `agent_version`을 메모에 `V1 버전: N`으로 적어 둡니다.

```bash
python scripts/workshop.py smoke
```

**완료 확인:** 비어 있지 않은 한국어 `answer`, `prompt_version: v1`, `trace_id`(이 요청의 실행 기록 ID), **숫자로 된 `agent_version`**이 담긴 JSON. 버전은 `1`이 아닐 수도 있으며, 7-2에서는 다른 번호가 나와야 합니다.

**다르면:** 원인을 고친 뒤 `smoke`만 다시 실행합니다. 재배포하지 않습니다([복구 안내](docs/troubleshooting.ko.md#resume)).

### 4-4. 포털에서 버전 확인

**포털:** **Agents → 내 agent → Playground**를 열고 4-3의 버전을 선택합니다.

**완료 확인:** Playground의 버전 선택 상자에 4-3의 숫자 `agent_version`이 선택되어 있습니다.

**다르면:** [포털 화면 차이](docs/troubleshooting.ko.md#portal-differs)를 봅니다.

<details>
<summary>예시 화면: 실제 원격 응답과 Playground</summary>

![실제 원격 응답](docs/assets/live-ko-20260923b/screenshots/S4-03-smoke-after.webp)

Playground에서 호출한 V1 답변입니다. 금액·판단은 맞지만 `citations`에 문서 ID 대신 제목이 들어 있으며, 이런 추가 호출은 48응답에 포함하지 않습니다.

![Playground에서 호출한 V1 응답](docs/assets/live-ko-20260923b/screenshots/S4-P01-playground-after.webp)

</details>

**다음:** [5. 세 모델의 baseline 평가하기](#lab-c)

<a id="lab-c"></a>
<a id="7-실습-c--네-모델-baseline과-foundry-evaluation"></a>
<a id="5-네-모델의-baseline-평가하기--실습-c"></a>
<a id="5-세-모델의-baseline-평가하기"></a>

## 5. 세 모델의 baseline 평가하기

**목표:** V1 응답 18개(dev 6문항 × 3모델)를 `baseline`으로 모아 평가합니다.

| 명령 | 하는 일 |
|---|---|
| `collect` | 에이전트를 호출해 답변을 만들고, 판단·금액·인용을 Python 업무 검사로 확인 |
| `evaluate` | **저장된 답변**을 Foundry judge로 채점. 새 답변은 만들지 않으며 groundedness(근거성)·relevance(관련성)는 5점 중 4점 이상이면 통과 |
| `compare` / `summary` | 저장된 결과를 로컬에서 집계·요약. 모델 호출 없음 |

9단계의 품질 gate(통과 기준)는 **업무 검사**로 정합니다. Foundry 점수는 별도 품질 신호이며 업무 검사를 대신하지 않습니다([평가기 입력](#무엇을-평가하나요)).

### 5-1. Judge 확인

**터미널 A:** 채점 모델(judge)이 근거 있는 답과 틀린 답을 구분하는지 예제 두 개로 점검합니다. 이것이 calibration이며, 본평가 48응답에는 포함하지 않습니다.

```bash
python scripts/workshop.py calibrate
```

**완료 확인:** `Judge calibration passed`.

**다르면:** [calibration부터 복구](docs/troubleshooting.ko.md#calibration)합니다.

### 5-2. Baseline 18응답 수집

**터미널 A:**

```bash
python scripts/workshop.py collect --split dev --label baseline
```

**완료 확인:** 진행 표시가 오류 없이 `18/18`에 도달합니다. `business=False`는 검토할 결과이지 명령 오류가 아닙니다.

**다르면:** [수집 복구](docs/troubleshooting.ko.md#collection-retry)를 따릅니다.

<a id="baseline-evaluation"></a>

### 5-3. 저장된 응답 평가

**터미널 A:**

```bash
python scripts/workshop.py evaluate --label baseline
```

**완료 확인:** `Foundry evaluation completed: ... (18 rows)`와 그 아래 report URL. 점수가 낮아도 유효한 결과입니다.

**다르면:** [평가 복구](docs/troubleshooting.ko.md#evaluation-retry)를 따릅니다. 수집은 반복하지 않습니다.

### 5-4. 평가 보고서 열기

**포털:** `evaluate`가 출력한 report URL을 엽니다.

**완료 확인:** 평가 run이 **Completed**이고 groundedness·relevance 결과가 18행 있습니다.

**다르면:** agent의 Evaluation 탭이 아니라 프로젝트 전체의 **Evaluations** 목록에서 찾고, [포털 화면 차이](docs/troubleshooting.ko.md#portal-differs)를 봅니다.

<a id="무엇을-평가하나요"></a>

<details>
<summary>참고용(진행에는 필요 없음): 질문 묶음과 평가기 입력</summary>

- `data/dev.jsonl`은 **현행 한도, 사전 승인, 과거 규정, 정책 밖 질문, 금지 항목, 규정 무시 요청**을 다룹니다.
- 질문 묶음과 결과 이름은 [처음의 비교표](#evaluation-runs)를 그대로 사용합니다.
- Judge인 `gpt-5.4-mini`는 후보가 아니며, calibration 예제 2건은 48응답에 포함하지 않습니다.
- Foundry의 groundedness·relevance 평가기는 답변 텍스트만 보고 `decision`·`citations` 필드는 받지 않으므로, **높은 groundedness만으로 판단이나 인용 ID가 맞았다고 볼 수 없습니다**([평가기별 입력](docs/validation.ko.md#business-checks)).

</details>

<details>
<summary>예시 화면: baseline 평가 보고서</summary>

![실제 baseline 평가](docs/assets/live-ko-20260923b/screenshots/S5-P01-baseline-report-after.webp)

</details>

**다음:** [6. 한 사례를 검토하고 이유 남기기](#lab-d)

<a id="lab-d"></a>
<a id="8-실습-d--점수가-아니라-실패를-학습-자산으로"></a>
<a id="6-실패-한-건을-찾아-이유-남기기--실습-d"></a>

## 6. 한 사례를 검토하고 이유 남기기

**목표:** 실제 응답 하나를 고정 기준과 **trace**(그 요청의 검색·모델 호출 기록)로 설명하고, V2 수집이 다시 쓰는 **회귀 사례**로 저장합니다.

### 6-1. 결과 집계와 검토 대상 찾기

**터미널 A — 결과 집계:** `summary`가 읽을 `comparison.json`을 만듭니다.

```bash
python scripts/workshop.py compare --labels baseline
```

**완료 확인:** 비교 JSON의 `labels → baseline → models`에 `sol`·`luna`·`astra`가 있습니다.

**다르면:** 5단계 수집·평가가 완료됐는지 확인하고 [실패한 명령만 복구](docs/troubleshooting.ko.md#resume)합니다.

**터미널 A — trace 확인:**

```bash
python scripts/workshop.py monitor --label baseline
```

**완료 확인:** 오류 없이 끝나고 `complete: true`, `expected_trace_count: 18`, `observed_trace_count: 18`이 나옵니다.

**다르면:** [모니터링 복구](docs/troubleshooting.ko.md#telemetry)를 따릅니다. 응답을 다시 수집하지 않습니다.

**터미널 A — 검토할 행 찾기:**

```bash
python scripts/workshop.py summary --labels baseline
```

**완료 확인:** 모델별 요약 표와 `baseline business-check failures:`가 나옵니다. 요약은 저장된 결과를 읽을 뿐, 다시 평가하지 않습니다.

**다르면:** 오류에 나온 파일·label을 확인하고 `summary`만 다시 실행합니다.

<a id="review-case"></a>

### 6-2. 한 사례를 골라 원인 설명

**고르기:** 6-1 요약의 `baseline business-check failures:`에 나온 **첫 `row_id`**와 괄호 안의 실패 검사를 사용합니다. `none`이면 아래 응답 파일의 첫 행을 골라 **통과한 이유**를 검토합니다. 실패를 만들 필요는 없습니다.

**응답 → 정답 → trace 순서로 확인합니다.** `.jsonl`은 한 줄에 JSON 객체 하나를 담은 파일입니다. 편집기에서 찾기(`Ctrl+F`, macOS는 `Cmd+F`)로 **줄 번호가 아닌 ID**를 찾습니다. 경로는 저장소 루트 기준이며, 파일은 수정하지 않습니다.

| 순서 | 열 곳과 찾는 값 | 확인할 것 |
|---|---|---|
| 1. 실제 응답 | `src/agent/.foundry/results/baseline/responses.jsonl`에서 `row_id` 검색 | `answer`·`decision`·`citations`를 읽고 검색 근거인 `source_ids`와 대조. 같은 행의 `case_id`·`trace_id`로 아래를 찾음 |
| 2. 고정 정답 | `data/dev.jsonl`에서 위 `case_id` 검색 | `ground_truth`·`expected_decision`·`required_numbers`·`allowed_citations`와 응답의 차이 확인 |
| 3. 실행 기록 | 포털 **내 agent → Traces → Graph view**에서 전체 `trace_id` 검색 | `foundry_iq.retrieve`와 `chat` span을 열어 검색된 근거와 모델 답변 확인 |

**메모할 것은 세 가지뿐입니다:** `row_id`, `trace_id`, 그리고 `관찰: ...; 근거: ...; 바꿀 점: ...` 한 줄. 나머지 JSON 필드는 옮겨 적지 않습니다. 모두 통과했다면 바꿀 점 대신 **제공 V2로도 유지할 동작**을 적습니다([통과 사례 검토](docs/troubleshooting.ko.md#no-failures)).

**완료 확인:** 같은 사례의 응답·고정 정답·두 span을 대조했고, 근거가 있는 한 줄 검토를 적었습니다.

**다르면:** 파일·행이 없으면 다른 label을 연 것은 아닌지 확인합니다. trace가 보이지 않으면 기간을 넓히고 전체 `trace_id`로 검색합니다([포털 화면 차이](docs/troubleshooting.ko.md#portal-differs)).

<details>
<summary>예시 화면: 검토한 요청의 span graph</summary>

![실제 실패 요청의 span graph](docs/assets/live-ko-20260923b/screenshots/S6-P01-trace-after.webp)

</details>

<details>
<summary>표에 나오는 용어</summary>

- `row_id`는 응답 하나, `case_id`는 질문, `trace_id`는 그 응답의 실행 기록입니다.
- `citations`는 답변이 인용한 ID, `source_ids`는 그 요청에서 검색된 문서입니다.
- **span**은 한 요청 안의 개별 작업입니다.
- `false`인 검사는 [다섯 업무 검사](docs/validation.ko.md#business-checks) 중 하나입니다. 올바른 `decision`([판단값](docs/reference.ko.md#decision-values)), 필수 금액 모두 포함, 모든 인용이 검색 문서에 있음, 모든 인용이 허용 목록에 있음, 필요한 인용의 존재입니다.

</details>

<a id="실제-예시-금액은-맞는데-왜-실패했나요"></a>

<details>
<summary>예시: 검색 문제와 지침 문제를 어떻게 구분하나요?</summary>

2026-09-23 촬영 실행의 `baseline-sol-D01`(`gpt-6-sol`)은 **170,000원 숙박비가 180,000원 한도 이내**라는 답과 `allowed` 판단을 맞혔습니다.
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

<a id="save-review"></a>

### 6-3. 내 검토 기록 저장

**터미널 A:** 첫 질문에는 검토한 `row_id`를, 두 번째 질문에는 6-2의 한 줄 검토(10자 이상, 예시 복사 금지)를 붙여넣습니다.

```bash
read -r -p "검토한 row_id: " ROW_ID &&
read -r -p "관찰·근거·바꾸거나 유지할 점 (10자 이상): " REVIEW_REASON &&
python scripts/workshop.py feedback --label baseline --row-id "$ROW_ID" \
  --reason "$REVIEW_REASON" --reviewer human
```

**완료 확인:** `Reviewed trace-to-dataset record saved:` 뒤에 `src/agent/.foundry/datasets/regression-<내 row_id>.jsonl`의 실제 경로가 나옵니다.

**다르면:** 이 행의 검토 기록이 이미 있을 수 있습니다. [복구 안내](docs/troubleshooting.ko.md#resume)대로 확인하고 덮어쓰지 않습니다.

**편집기:** 방금 출력된 **실제 경로의 파일**을 엽니다. `<내 row_id>`를 그대로 입력하거나 파일을 새로 만들지 않습니다. 기존 파일은 수정하지 않습니다.

**완료 확인:** `lineage → source_row_id`와 `source_trace_id`가 검토한 행·trace와 같고, `ground_truth`가 6-2에서 본 고정 정답과 같습니다(모델 답변이 아님).

**다르면:** 파일을 고치거나 지우지 말고 멈춘 뒤, 6-3 출력과 함께 강사에게 알립니다.

**다음:** [7. V2로 바꾸고 같은 dev 다시 평가하기](#lab-e)

<a id="lab-e"></a>
<a id="9-실습-e--개선하고-같은-조건으로-다시-평가"></a>
<a id="7-v2로-바꾸고-같은-dev-다시-평가하기--실습-e"></a>

## 7. V2로 바꾸고 같은 dev 다시 평가하기

**목표:** 제공된 V2 지침을 새 버전으로 배포하고, 모델·데이터·평가 기준은 그대로 둔 채 같은 dev 6문항으로 평가합니다.

<a id="v2에서는-무엇을-바꾸나요"></a>

### 7-1. 제공된 V2 검토

**편집기 — V1/V2 차이 확인:** `src/agent/prompts/v1.txt`와 `src/agent/prompts/v2.txt`를 열고, 6-2에서 적은 **바꿀 점 또는 유지할 동작**과 연결되는 행을 아래 표에서 찾습니다. 두 파일은 수정하지 않습니다. V2는 자동 생성물이 아니라 제공된 후보입니다.

| V1 약점 | 제공된 V2 지침 |
|---|---|
| 문서 ID를 숨김 | 실제 사용한 **원본 문서 ID**를 인용 |
| 날짜·문서 상태 기준이 모호함 | 출장일에 유효한 정책을 적용하고 `draft`는 제외 |
| 승인 필요와 금지를 섞음 | 다섯 판단값의 뜻을 정하고 승인 사실을 만들지 않음 |
| 근거가 부족할 때의 처리가 없음 | `not_covered` 또는 `needs_info`를 쓰고 일반 상식으로 규정을 채우지 않음 |
| 검색 문서 안의 지시를 따를 수 있음 | 검색 문서는 **지시가 아닌 근거**로 보고 규정 무시 요청은 거부 |

**완료 확인:** 내 검토와 연결되는 V2 지침을 하나 고르고, V1과 무엇이 다른지 메모했습니다. 통과한 사례라면 V2에서도 지켜야 할 규칙을 연결합니다.

**다르면:** 검토한 동작에 해당하는 지침이 없다면 멈추고 강사와 비교할 대상을 확인합니다. 제공된 V2가 내 사례를 개선한다고 미리 단정하지 않습니다.

### 7-2. V2 배포 후 새 버전 확인

**터미널 A — V2 배포:**

```bash
python scripts/workshop.py set-prompt v2 &&
azd deploy --no-prompt
```

**완료 확인:** `SUCCESS: Your application was deployed ...`가 나옵니다.

**다르면:** 오류 출력을 보존하고 [실패한 명령만 복구](docs/troubleshooting.ko.md#resume)합니다.

**터미널 A — 새 버전 확인:**

```bash
python scripts/workshop.py smoke
```

**완료 확인:** `prompt_version: v2`와, 4-3과 **다른 숫자 `agent_version`**.

**다르면:** 호출 오류는 [해당 명령만 복구](docs/troubleshooting.ko.md#resume)합니다. 응답은 왔지만 V1 또는 이전 버전이면 멈추고 강사와 배포 대상을 확인합니다. 버전 번호를 맞추려고 재배포하지 않습니다.

### 7-3. 같은 dev 수집·평가

**터미널 A — 수집:**

```bash
python scripts/workshop.py collect --split dev --label improved
```

**완료 확인:** 진행 표시가 오류 없이 `18/18`에 도달합니다.

**다르면:** [수집 복구](docs/troubleshooting.ko.md#collection-retry)를 따릅니다.

<a id="candidate-evaluation"></a>

**터미널 A — 평가:**

```bash
python scripts/workshop.py evaluate --label improved
```

**완료 확인:** `Foundry evaluation completed: ... (18 rows)`와 report URL.

**다르면:** [평가 복구](docs/troubleshooting.ko.md#evaluation-retry)를 따릅니다.

**터미널 A — 비교 저장:**

```bash
python scripts/workshop.py compare --labels baseline improved
```

**완료 확인:** 출력된 비교 JSON에 `labels → baseline`, `labels → improved`, `comparison_notes`가 있습니다.

**다르면:** 오류에 나온 label과 7-3의 평가 완료를 확인하고 [실패한 명령만 복구](docs/troubleshooting.ko.md#resume)합니다. 수집부터 반복하지 않습니다.

<a id="compare-results"></a>

### 7-4. 내 전후 결과 비교

**터미널 A:** 저장된 결과를 읽기만 하는 요약을 출력하고, 메모에 복사합니다.

```bash
python scripts/workshop.py summary --labels baseline improved
```

**완료 확인:** 출력에 다음이 차례로 나옵니다.

1. `Reviewed case ... source trace carried: yes`: 내 V1 검토가 V2 결과에 연결됨
2. `sol`·`luna`·`astra` 표: 각 값은 V1 `->` V2([열의 뜻](#metric-fields))
3. `improved business-check failures:`와 `improved Foundry-score failures:`: row ID 또는 `none`

**다르면:** 비교 파일·label이 없다는 오류이면 7-3의 평가 완료를 확인한 뒤 `compare`와 `summary`만 다시 실행합니다. `Reviewed case`가 없거나 `source trace carried: no`이면 검토 연결이 확인되지 않은 것이므로 멈추고 강사와 6-3의 기록을 확인합니다. 수집·검토를 새로 만들어 덮지 않습니다.

**검토한 사례부터 읽습니다:** `source trace carried: yes`는 **검토 출처가 연결됐다는 뜻**이지 개선 판정이 아닙니다. 같은 줄의 `business passed` 또는 `business failed (...)`로 그 사례의 V2 업무 검사 결과를 확인하고 메모합니다.

**그다음 세 모델 표를 읽습니다:** `business`·`required citations`로 업무 규칙 준수를 먼저 봅니다. 그다음 `groundedness`·`relevance`로 답변 품질, `tokens in/out`·`p50/p95 s`로 자원 사용량과 처리 시간을 봅니다. 각 칸은 **V1 → V2**이며, 나빠진 값도 그대로 보고합니다. 기준을 낮추거나 모델을 바꾸거나 V2를 자동 채택하지 않습니다.

<a id="metric-fields"></a>
<a id="실제-실행에서는-무엇이-좋아졌나요"></a>

<details>
<summary>요약 표의 열</summary>

요약은 `src/agent/.foundry/results/comparison.json`(`labels → baseline / improved → models`)과 label별 `evaluation-results.json`을 읽습니다.

| 열 | 필드 | 뜻 |
|---|---|---|
| `business` | `business_passed` / `total` | 다섯 업무 검사를 모두 통과한 응답 수 |
| `required citations` | `required_citation_passed` / `required_citation_total` | 인용이 필요한 응답 중 유효하게 인용한 응답 수 |
| `groundedness`, `relevance` | `foundry_evaluators → native_passed` / `total` | **4점 이상**을 받은 행 수. 평균 4점이 전부 통과를 뜻하지 않음 |
| `tokens in/out` | `input_tokens`, `output_tokens` | 해당 모델의 **같은 dev 6응답 합계**. planner·judge 등은 빠지므로 Azure 청구액이 아님 |
| `p50/p95 s` | `latency_p50_seconds`, `latency_p95_seconds` | 검색 + 모델 처리 시간(**초**). 모델당 6응답이라 p95는 가장 느린 한 응답이며 운영 보장이 아님([측정 범위](docs/validation.ko.md#tradeoffs)) |

실행마다 검색 근거가 다를 수 있어(`comparison_notes`) 모델 순위가 아닌 end-to-end 비교입니다. 미통과 행을 자세히 보려면 [미통과 행 확인](docs/validation.ko.md#native-failures)을 봅니다. 촬영 실행의 기록(내 목표 점수가 아닌 예시)은 [모델별 실제 결과](docs/validation.ko.md#measured-results)에 있습니다. 업무 통과 0/18 → 18/18은 답변 정확도 0% → 100%가 아니라 인용 규칙 준수의 변화입니다.

</details>

<a id="portal-comparison"></a>

<details>
<summary>선택, 시간이 남을 때만: 포털에서 V1과 V2 비교(추가 모델 호출, 48응답에 포함하지 않음)</summary>

**내 agent → Playground → Version 선택 상자 → Compare versions**를 엽니다. 양쪽이 같은 버전으로 열릴 수 있으므로 왼쪽은 V1, 오른쪽은 V2의 실제 버전 번호를 선택합니다. 어느 쪽 입력창이든 아래 dev 질문을 붙여넣습니다.

```json
{
  "query": "2026년 9월 10일 부산 출장에서 1박 숙박비 170000원은 규정상 가능한가요? 한도도 알려주세요.",
  "model_key": "sol",
  "case_id": "D01",
  "run_id": "portal-ko-comparison"
}
```

**Send는 한 번만** 누릅니다. 비교 화면이 양쪽 버전을 함께 호출합니다. 각 응답의 `language`, `prompt_version`, `citations`, 서로 다른 `trace_id`를 확인합니다. 추가 시연 호출이며 수집한 18 + 18응답을 대체하거나 통계에 더하지 않습니다.

**아래는 촬영 예시입니다:** 왼쪽 V1은 문서 제목, 오른쪽 V2는 `TRAVEL-2026`을 인용했습니다. 내 응답의 판단·인용은 다를 수 있습니다. 실제 차이를 읽고, 예시와 맞추려고 다시 호출하지 않습니다.

![실제 V1/V2 응답 비교](docs/assets/live-ko-20260923b/screenshots/S7-P02-compare-citations-after.webp)

</details>

**다음:** [8. 후보를 고정하고 holdout 평가하기](#lab-f)

<a id="lab-f"></a>
<a id="10-실습-f--holdout과-frontier-ecosystem-테스트"></a>
<a id="8-후보를-고정하고-holdout-평가하기--실습-f"></a>

## 8. 후보를 고정하고 holdout 평가하기

**목표:** 바꾸지 않은 V2로 응답 12개(holdout 4문항 × 3모델)를 수집·평가합니다.

### 8-1. Holdout 응답 수집

**주의:** 7-2에서 배포한 V2를 바꾸지 않고 그대로 씁니다. 별도 `freeze` 명령은 없습니다. 7-2 이후 아래 중 하나라도 했다면 **수집하지 말고 먼저 강사에게 알립니다.**

- `set-prompt` 또는 `azd deploy` 실행
- `.env` 또는 prompt 파일 수정

**터미널 A:**

```bash
python scripts/workshop.py collect --split holdout --label holdout
```

**완료 확인:** 진행 표시가 오류 없이 `12/12`에 도달합니다.

**다르면:** [수집 복구](docs/troubleshooting.ko.md#collection-retry)를 따릅니다.

<a id="holdout-evaluation"></a>

### 8-2. Holdout 평가와 비교

**터미널 A — 평가:**

```bash
python scripts/workshop.py evaluate --label holdout
```

**완료 확인:** `Foundry evaluation completed: ... (12 rows)`와 report URL.

**다르면:** [평가 복구](docs/troubleshooting.ko.md#evaluation-retry)를 따릅니다. 수집은 반복하지 않습니다.

**터미널 A — 고정한 V2인지 확인:**

```bash
python scripts/workshop.py compare --labels baseline improved holdout
```

**완료 확인:** 출력된 비교 JSON의 `labels → improved`와 `labels → holdout`에서 `agent_version`과 `prompt_hash`가 같습니다.

**다르면:** 명령 오류는 [실패한 명령만 복구](docs/troubleshooting.ko.md#resume)합니다. 버전이나 hash가 다르면 **비교 조건이 달라진 것**이므로 멈추고 강사와 확인합니다. 재평가·파일 편집으로 일치시키지 않습니다.

### 8-3. Holdout 보고서 열기

**포털:** dev 보고서가 아니라 이번 holdout `evaluate`가 출력한 report URL을 엽니다.

**완료 확인:** 평가 run이 **Completed**이고 12행을 보여 줍니다.

**다르면:** [포털 화면 차이](docs/troubleshooting.ko.md#portal-differs)를 봅니다.

**주의:** 결과를 본 뒤 prompt를 고쳐 같은 holdout을 다시 “미사용 검증”으로 제출하지 않습니다. 이 4문항은 교육용이며 독립 벤치마크가 아닙니다([촬영 실행의 점수와 한계](docs/validation.ko.md#measured-results)).

<details>
<summary>예시 화면: holdout 평가 보고서</summary>

![실제 holdout 평가](docs/assets/live-ko-20260923b/screenshots/S8-P01-holdout-report-after.webp)

</details>

**다음:** [9. 운영 신호와 전체 증거 확인하기](#lab-g)

<a id="lab-g"></a>
<a id="11-실습-g--trace와-monitor의-차이"></a>
<a id="9-운영-신호와-전체-증거-확인하기--실습-g"></a>

## 9. 운영 신호와 전체 증거 확인하기

**목표:** 전체 증거 검증 → 운영 대시보드 확인 → 최종 보고 순서로 마칩니다. 보고에 필요한 값을 모두 확인한 뒤 보고를 한 번에 작성합니다.

### 9-1. 전체 응답·평가·trace 검증

**터미널 A — V2 dev trace:**

```bash
python scripts/workshop.py monitor --label improved
```

**완료 확인:** 오류 없이 끝나고 `complete: true`, `expected_trace_count: 18`, `observed_trace_count: 18`.

**다르면:** `monitor`는 최근 2시간만 보므로, 오래된 실행은 [조회 기간을 늘립니다](docs/troubleshooting.ko.md#telemetry). 응답은 다시 수집하지 않습니다.

**터미널 A — holdout trace:**

```bash
python scripts/workshop.py monitor --label holdout
```

**완료 확인:** 오류 없이 끝나고 `complete: true`, `expected_trace_count: 12`, `observed_trace_count: 12`.

**다르면:** 같은 label의 [모니터링 복구](docs/troubleshooting.ko.md#telemetry)를 따릅니다.

**터미널 A — 전체 증거 검증:**

```bash
python scripts/workshop.py verify --baseline baseline --candidate improved --holdout holdout
```

**완료 확인:** `language: ko`, `component_execution_verified: true`, `primary_model_outputs: 48`, `distinct_verified_traces: 48`.

**다르면:** [실패한 단계 복구](docs/troubleshooting.ko.md#resume)를 따릅니다. 증거 파일을 고치지 않습니다.

<details>
<summary>예시 화면: 전체 실행 증거 확인</summary>

![실제 응답·trace·평가·lineage 검증](docs/assets/live-ko-20260923b/screenshots/S9-03-verify-after.webp)

</details>

<a id="operational-dashboard"></a>
<a id="9-3-운영-대시보드-확인"></a>

### 9-2. 운영 대시보드 확인

**포털:** **내 agent → Monitor → Last Day**를 엽니다.

**완료 확인:** Last Day 그래프에 내 실행 시간대의 요청·토큰·지연이 보입니다. **오류 수를 메모합니다.** smoke·포털 호출도 포함되므로 합계가 48과 달라도 됩니다.

**다르면:** [포털 화면 차이](docs/troubleshooting.ko.md#portal-differs)를 봅니다.

<details>
<summary>예시 화면: Foundry Monitor 대시보드</summary>

촬영 실행에서는 48응답에 smoke·Playground 호출이 더해져 agent run이 54건이었습니다.

![실제 Foundry Monitor 대시보드](docs/assets/live-ko-20260923b/screenshots/S9-P01-monitor-after.webp)

</details>

<a id="completion-decision"></a>
<a id="9-2-보고할-내용-정하기"></a>
<a id="9-2-내-결과를-세-가지로-보고하기"></a>
<a id="finish"></a>
<a id="마무리-세-가지-보고"></a>

### 9-3. 내 결과를 세 가지로 보고하기

**편집기:** `src/agent/.foundry/results/verified-evidence.json`을 열고 `candidate_quality_gates`를 찾습니다. 9-1에서 저장한 결과이므로 명령을 다시 실행하지 않습니다. **gate는 품질 통과 기준**이며, 모델마다 `dev`·`holdout` 두 값이 있습니다.

| gate | `true`의 뜻(모델별) |
|---|---|
| `dev` | 6응답 중 **5응답 이상이 모든 업무 검사 통과** + 필수 인용 전부 유효 |
| `holdout` | 4응답 **모두 업무 검사 통과** + 필수 인용 전부 유효 |

**내 메모:** 지금까지 모은 결과를 아래 세 항목에 넣습니다. **명령이 아니라 보고 양식**입니다. `...`에는 촬영 예시가 아닌 내 값을 씁니다.

```text
검토: row_id=...; trace_id=...; 관찰·근거·바꿀 점(또는 유지할 동작)=...
변화: ... (7-4 summary의 세 모델 표와 미통과 행을 붙여넣기)
판단: sol(dev=..., holdout=...); luna(dev=..., holdout=...); astra(dev=..., holdout=...); 남은 한계=...; production_release_approved=false
```

**판단하는 법:**

- `false`인 gate는 그대로 보고합니다. **실행 미완료가 아니라 유효한 품질 결과입니다.**
- 모두 `true`여도 Foundry 점수의 미통과와 한계를 남깁니다. 9-2의 오류 수가 0이 아니면 **남은 한계**에 넣습니다.
- `summary`의 토큰·처리 시간도 보고하며, 나빠진 값도 숨기지 않습니다.
- **`production_release_approved: false`가 정상**입니다. gate를 모두 통과해도 운영 승인이나 모델의 통계적 우월성을 주장하지 않습니다.

**완료 확인:** 검토·전후 비교·gate 6개가 모두 내 결과이며, 남은 한계와 `production_release_approved=false`를 적었습니다. 점수를 높이려고 재실행하지 않습니다.

**다르면:** gate 값이 없다면 9-1로 돌아갑니다. 메모만 빠졌다면 [6단계 검토 기록](#save-review)과 [7-4 요약](#compare-results)의 **저장 결과를 읽어** 채웁니다. 검토·수집을 다시 실행하지 않습니다.

**다음:** [10. 내 실습 자원만 정리하기](#cleanup)로 갑니다. 레벨 2·3을 추가하려면 정리 전에 아래 선택 항목을 엽니다.

<a id="levels"></a>

<details>
<summary>선택: 시간이 더 있으면 정리 전에 레벨 2·3 추가</summary>

같은 폴더에서 진행합니다. **10단계 뒤에는 에이전트가 삭제되므로 추가 실습을 시작하지 않습니다.** 모델·judge 호출 비용이 추가됩니다.

| 선택 | 더하는 내용 | 추가 시간 | 경로 |
|---|---|---|---|
| 레벨 1만 | 여기까지의 평가 루프 | 없음 | [10단계 정리](#cleanup) |
| 레벨 2 | 업무 규칙을 Foundry 평가기로 채점하고 run·실패 원인 비교 | 약 40분 | [레벨 2](docs/level-2.ko.md) → 10단계 |
| 레벨 2·3 | 생성 평가 기준, 모델·agent·trace 평가, 연속 평가, 릴리스 gate | 약 110분 | [레벨 2](docs/level-2.ko.md) → [레벨 3](docs/level-3.ko.md) → 10단계 |

</details>

<a id="cleanup"></a>
<a id="12-마무리와-비용-정리"></a>

## 10. 내 실습 자원만 정리하기

**목표:** 이 폴더가 만들어 소유한 객체를 지우고, 로컬 증거와 공유 서비스는 남깁니다. 개인 실습에서는 직접 만든 후보 모델 배포도 삭제 대상일 수 있습니다.

**주의:** 정리 전에 확인합니다.

- 포털 확인을 모두 마칩니다. 정리하면 live agent가 삭제됩니다.
- `azd down`이나 공유 resource group 삭제는 실행하지 않습니다.
- Search, 로그, 기반 서비스, 보조 모델의 비용은 환경 소유자만 관리합니다.

### 10-1. 삭제 계획만 확인

**터미널 A:**

```bash
python scripts/workshop.py cleanup --dry-run
```

**완료 확인:** 모든 대상이 이 폴더의 소유권 기록에 속합니다.

| 계획 필드 | 있어야 할 대상 |
|---|---|
| `agent`, `search_objects`, `role_assignments` | 내 `LAB_AGENT_NAME`, `LAB_PREFIX` 지식 객체, 이 폴더에서 만든 역할 |
| `models` | **공유 배포를 쓰는 참가자는 빈 목록.** 모델 준비 폴더에서 개인 실습을 했다면 `prepare-models`로 만든 후보가 포함될 수 있으며, 다른 사용자가 필요로 하지 않을 때만 삭제 |
| `schedules`, `custom_evaluators`, `generated_datasets` | 레벨 2·3을 하지 않았다면 빈 목록. 했다면 이 폴더의 일정·평가기·생성 데이터셋만 포함 |

기반 서비스와 보조 planner/judge는 보존합니다. `.env`에 모델 이름이 있다는 것만으로 소유권이 생기지는 않습니다.

**다르면:** 멈추고 강사에게 알립니다. 아무것도 삭제하지 않습니다.

### 10-2. 검토한 계획만 실행

**터미널 A:**

```bash
python scripts/workshop.py cleanup --confirm
```

**완료 확인:** 출력이 `Owned workshop resources removed; shared infrastructure and evidence preserved.`로 끝납니다.

**다르면:** [정리 복구](docs/troubleshooting.ko.md#cleanup-recovery)를 따릅니다.

<a id="cleanup-check"></a>

### 10-3. 삭제 여부를 별도로 확인

**터미널 A:**

```bash
python scripts/workshop.py check-cleanup
```

**완료 확인:** 출력된 JSON(`src/agent/.foundry/results/cleanup-check.json`에도 저장)에 `temporary_hosted_agent_absent: true`, `existing_foundry_project_preserved: true`, `existing_search_service_preserved: true`가 있고, 삭제 건수가 예시 화면이 아니라 **내 계획**과 같습니다.

**다르면:** 이 확인만 실패했다면 [확인 명령부터 복구](docs/troubleshooting.ko.md#cleanup-recovery)합니다. 성공한 `cleanup --confirm`을 다시 실행하면 저장된 계획이 바뀌므로 반복하지 않습니다.

<details>
<summary>예시 화면: 정리 완료 확인</summary>

![실제 Azure 정리 재확인](docs/assets/live-ko-20260923b/screenshots/S10-03-check-after.webp)

</details>

**기본 실습 완료:** [9-3의 보고](#finish)와 삭제 확인 결과를 보관합니다. 로컬 증거 파일은 지우지 않습니다. 직접 만든 **본인 전용 개인 실습 환경**이라면 [기반 서비스 최종 정리](docs/environment.ko.md#final-cleanup)를 별도로 선택할 수 있으며, 공유 그룹은 삭제하지 않습니다.

<details>
<summary>저장된 증거의 위치</summary>

| 위치 | 내용 |
|---|---|
| `src/agent/.foundry/results/baseline/` | V1의 18응답과 평가 |
| `src/agent/.foundry/results/improved/` | V2의 18응답과 평가 |
| `src/agent/.foundry/results/holdout/` | 고정 후보의 12응답과 평가 |
| `src/agent/.foundry/results/comparison.json` | 세 모델의 전후 지표와 미통과 사례 |
| `src/agent/.foundry/datasets/regression-*.jsonl` | 검토 이유·고정 정답·원래 trace |
| `src/agent/.foundry/results/verified-evidence.json` | 전체 실행·lineage 검증 |
| `src/agent/.foundry/results/cleanup-check.json` | 삭제 확인 결과. 확인한 계획은 같은 폴더의 `cleanup.json` |

뒤의 실습 명령이 이 파일들을 읽습니다. 지우거나 예시 결과로 바꾸지 않습니다.

</details>

## 참고 문서

- **결과와 한계:** [평가 방법과 개선 결과](docs/validation.ko.md)
- **설계와 용어:** [설계·모델·공식 출처](docs/reference.ko.md)
- **레벨 2·3:** [Foundry custom 평가기와 인사이트](docs/level-2.ko.md) · [생성 rubric·스트레스 테스트·red team·에이전트 직접 호출·trace·연속 평가·릴리스 gate](docs/level-3.ko.md)
- **오류:** [문제 해결](docs/troubleshooting.ko.md)
- **강사:** [강사 준비](docs/instructor.ko.md) · [새 Azure 환경 생성](docs/environment.ko.md)
- **선택:** [GHCP로 진행](docs/copilot.ko.md)

<a id="summary-video"></a>

## 선택: 14분 요약 영상

<details>
<summary>한국어 실습 요약 영상 — 14분 35초</summary>

[한국어 실습 요약 영상 (MP4, 17.2 MiB)](videos/foundry-evaluation-gpt6-ko-20260923b.mp4)

2026-09-23 한국어 재실행(`ko-20260923b`)의 실제 CLI와 Foundry 포털을 Playwright headless로 녹화해 본문 순서로 편집했습니다. 레벨 2·3 장은 같은 날 레벨 리허설에서 저장한 실제 CLI 출력을 렌더한 화면이며, red team 장은 현재 `red-team` 명령으로 다시 실행한 출력입니다. 소리는 없고, 대기 구간은 줄였으며, 로그인·MFA와 계정·구독 식별자는 제외했습니다. 영상과 본문이 다르면 본문을 따릅니다.

| 단계 | 영상 위치 | 단계 | 영상 위치 |
|---|---|---|---|
| 1. 시작 준비 | 00:07 | 2. 지식 넣고 검색 | 01:07 |
| 3. 로컬 실행 | 02:08 | 4. Hosted Agent 배포 | 02:49 |
| 5. baseline 평가 | 04:18 | 6. 사례 검토 | 05:27 |
| 7. V2 평가 | 06:49 | 8. holdout 평가 | 09:32 |
| 9. 운영 신호·증거 | 10:35 | 레벨 2 | 11:59 |
| 레벨 3 | 12:21 | 10. 정리 | 13:07 |

영문 실행의 요약 영상은 [영문 가이드](README.md#summary-video)에 있습니다.

</details>
