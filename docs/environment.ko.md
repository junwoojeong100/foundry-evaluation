# 새 Azure 환경 준비하기 — 강사 또는 개인 실습

[한국어 실습](../README.ko.md) · [English](environment.en.md)

**목표:** **Sweden Central**에 새 유료 한국어 실습 환경을 만듭니다. Foundry·Search·관측 서비스·세 후보·planner/judge와 바로 쓸 수 있는 `.env`를 준비합니다. 이 준비는 120분 참가자 실습 밖에서 먼저 끝내는 작업입니다.

**새 기반 서비스(Foundry 계정·프로젝트, Search, 관측 서비스, 모델 배포)가 필요할 때만 이 문서를 씁니다.** 완성된 `.env`를 이미 받았다면 이 문서를 건너뛰고 [README 1단계](../README.ko.md#start)에서 시작합니다. 서비스는 있지만 준비가 덜 됐다면 [기존 환경 준비](instructor.ko.md#existing-foundation)로 갑니다. 두 경로를 함께 실행하지 않습니다.

여기서 새 환경을 만들면 수업 준비, 리허설, 개인 실습 모두 1–6단계를 끝낸 뒤 calibration 후 [전달 경로](#handoff)를 하나 고릅니다.

**시작 전:** Bash/WSL 터미널 하나에서 한 블록씩 실행합니다. 터미널을 닫았다면 아래 재개 지시를 따릅니다.

- 도구: `git`, `python3.13`, `az`, `azd`, Bash/WSL, curl, 편집기, 브라우저.
- 권한: 로그인할 소유자가 나열된 자원과 범위 지정 RBAC 역할을 만들 수 있어야 합니다.

1단계에서 미사용 Git clone을 만들거나 그 루트로 들어갑니다.

<details>
<summary>시작 조건 상세 확인</summary>

확실하지 않으면 강사용 [도구](instructor.ko.md#tools)와 [권한](instructor.ko.md#access) 확인을 봅니다.

</details>

<a id="setup-route"></a>

**순서:** [1. 실행 폴더](#setup-workspace) → [2. 계정·용량](#setup-identity) → [3. 서비스](#setup-foundation) → [4. 권한·연결](#setup-access) → [5. 보조 모델](#setup-auxiliary) → [6. 후보·calibration 확인](#setup-candidates) → [전달](#handoff).

> 새 서비스에는 비용이 발생합니다. 합성 데이터만 사용합니다.
>
> 공유/영어 자원을 보존합니다. 다른 흐름의 기본 Azure CLI 구독을 바꾸지 않습니다. Sweden Central은 리소스 그룹 위치일 뿐이며, GlobalStandard 모델 추론이 Sweden에만 머문다는 보장은 아닙니다.

<details>
<summary>선택: Copilot CLI에 이 준비 맡기기</summary>

[Copilot CLI 설치·시작 안내](copilot.ko.md)를 먼저 따릅니다. 그 문서에서 초기 설정만 하러 왔다면 1단계 표를 채운 뒤 [계획 확인](copilot.ko.md#plan-review)으로 돌아갑니다. 양쪽에서 환경 준비를 중복 실행하지 않습니다.

</details>

<a id="setup-workspace"></a>

## 1. 격리된 한국어 소스 작업 폴더 만들기

이 도구는 Git commit으로 소스 버전을 확인하므로 ZIP이 아니라 **아직 실습하지 않은 Git clone**에서 실행합니다.

**명령을 직접 실행하는 위치는 `REPO_ROOT`와 `RUN_DIR/workshop` 두 곳뿐이며, `RUN_DIR`는 기록 경로로만 씁니다.**

| 경로 | 역할 | 명령을 실행하는 단계 |
|---|---|---|
| `REPO_ROOT` | 원래 clone·가이드·준비 도구 | 초기 준비와 2–5단계 서비스 생성 |
| `RUN_DIR` | 이번 실행의 설정·생성 기록 | `--run-dir` 인자로만 전달. **여기서 명령을 실행하지 않음** |
| `RUN_DIR/workshop` | 독립 소스와 생성된 `.env` | Python 테스트·로그인·6단계·이후 참가자 실습 |

### 1-1. Git clone 준비

아직 쓰지 않은 Git clone 루트에 있지 않다면 먼저 실행합니다.

**터미널 — 새 clone을 만들 상위 폴더에서:**

```bash
git clone https://github.com/junwoojeong100/foundry-evaluation.git foundry-evaluation-setup-ko &&
cd foundry-evaluation-setup-ko
```

**완료 확인:** 현재 폴더에 `README.ko.md`가 있습니다.

**다르면:** 중단하고 미사용 clone 루트로 이동한 뒤 계속합니다. ZIP이나 이전 실습 폴더에서 실행하지 않습니다.

<a id="initial-settings"></a>

### 1-2. 초기 `.env` 작성

**편집기 — 현재 clone 루트(곧 `$REPO_ROOT`로 저장할 폴더):**

1. 이 clone 루트에서 `.env.example`을 `.env`로 복사합니다.
2. 아래 행만 채우고 나머지 템플릿 값은 그대로 둡니다.

- 기존 `.env`를 덮어쓰거나 `.env.txt`를 만들지 않습니다.
- 암호, API key, 토큰은 넣지 않습니다.
- 구독 ID는 [Azure Portal](https://portal.azure.com/) **Subscriptions → 해당 구독 → Overview**, tenant ID는 **Microsoft Entra ID → Overview**에서 확인합니다. 포털 로그인은 `az`/`azd` 로그인과 별개입니다.

| 필드 | 값 |
|---|---|
| `AZURE_SUBSCRIPTION_ID` | 강사가 승인한 실습 구독 |
| `AZURE_TENANT_ID` | 그 구독의 tenant |
| `AZURE_EXPECTED_USERNAME` | 직접 로그인할 계정 |
| `AZURE_RESOURCE_GROUP` | 조사할 이전 그룹 이름. 없으면 **`AZURE_RESOURCE_GROUP=`**로 둠 |
| `LAB_LANGUAGE` | `ko` |

새 서비스 이름·엔드포인트·모델 배포 이름은 도구가 별도 폴더의 `.env`에 생성합니다.

**완료 확인:** `.env`가 현재 clone 루트에 저장되어 있고, `AZURE_SUBSCRIPTION_ID`, `AZURE_TENANT_ID`, `AZURE_EXPECTED_USERNAME`, `LAB_LANGUAGE=ko`를 채웠으며 `AZURE_RESOURCE_GROUP`은 이전 그룹 이름이거나 의도적으로 `AZURE_RESOURCE_GROUP=`로 비워 두었습니다.

**다르면:** 도구를 설치하기 전에 `.env`를 고칩니다. placeholder나 비밀 값을 넣은 채 계속하지 않습니다.

### 1-3. 준비 도구 설치

**터미널 — 현재 clone 루트(아래에서 `$REPO_ROOT`로 저장):**

```bash
python3.13 -m venv src/agent/.venv &&
source src/agent/.venv/bin/activate &&
python -m pip install -r requirements.lock.txt
```

**완료 확인:** `pip`가 오류 없이 끝납니다.

**다르면:** `RUN_DIR`를 만들기 전에 Python 또는 패키지 오류를 해결합니다. 일부만 설치된 가상환경으로 계속하지 않습니다.

### 1-4. `RUN_DIR` 생성

실행 ID는 한 번만 새로 정합니다. 예시 ID나 기존 `RUN_DIR`를 재사용하지 말고, 출력된 경로를 이후 모든 블록에서 사용합니다.

**터미널 — 현재 clone 루트(여기서 `$REPO_ROOT`로 저장):**

```bash
REPO_ROOT="$(pwd)" &&
RUN_ID="ko-$(date -u +%Y%m%d-%H%M%S)" &&
RUN_DIR="$REPO_ROOT/.workshop/$RUN_ID" &&
printf 'RUN_DIR=%s\n' "$RUN_DIR" &&
python scripts/prepare_environment.py init --run-dir "$RUN_DIR" --language ko
```

출력된 `RUN_DIR`의 절대 경로를 지금 보관합니다.

**완료 확인:** `init`이 끝나고 **`$RUN_DIR/config.json`**이 생깁니다. 새 이름을 기록한 것이며, 아직 소스 복사나 Azure 자원 생성은 하지 않았습니다.

**다르면:** 출력과 같은 `RUN_DIR`를 보존하고 [환경 준비 복구](troubleshooting.ko.md#setup-resume)를 따릅니다. 새 실행 ID로 처음부터 반복하지 않습니다.

<details>
<summary>새 터미널에서 재개할 때</summary>

```bash
read -r -p "이 clone의 절대 경로(REPO_ROOT): " REPO_ROOT &&
read -r -p "출력된 RUN_DIR 경로: " RUN_DIR &&
cd "$REPO_ROOT" &&
source src/agent/.venv/bin/activate
```

2단계 로그인 명령이 `AZURE_CONFIG_DIR`를 설정합니다. 이미 2단계를 지났다면 `export AZURE_CONFIG_DIR="$RUN_DIR/workshop/.azure-cli"`도 실행합니다.

</details>

<a id="setup-snapshot"></a>

### 1-5. 소스 스냅샷 복사

이어서 실제 실행할 소스 스냅샷을 만듭니다.

**터미널 — 원래 clone (`$REPO_ROOT`):**

```bash
python scripts/prepare_environment.py prepare --run-dir "$RUN_DIR"
```

**완료 확인:** **`$RUN_DIR/source-manifest.json`**과 **`$RUN_DIR/workshop/.env`**가 있고, 생성된 이 `.env`가 이후 실행 설정입니다.

**다르면:** [환경 준비 복구](troubleshooting.ko.md#setup-resume)에서 소스 복사 상태를 확인합니다. `init`을 반복하거나 기존 폴더를 덮어쓰지 않습니다.

원래 clone의 `.env`를 수정해도 생성된 복사본은 바뀌지 않습니다. 재개할 때는 저장된 설정과 소유권 기록을 유지합니다.

<a id="setup-python"></a>

### 1-6. 독립 소스 설치와 테스트

**터미널 — 실행 폴더 (`$RUN_DIR/workshop`):**

```bash
cd "$RUN_DIR/workshop" &&
python3.13 -m venv src/agent/.venv &&
source src/agent/.venv/bin/activate &&
python -m pip install -r requirements.lock.txt &&
python -m unittest discover -s tests -v
```

**완료 확인:** 테스트가 `OK`입니다. **`$RUN_DIR/source-manifest.json`**에 소스 commit과 SHA-256 해시가 있고 **`$RUN_DIR/workshop/.env`**에 `LAB_LANGUAGE=ko`와 새 이름이 있습니다. 이전 `.azure`·`.foundry`·가상환경을 재사용하지 않았습니다.

**다르면:** Azure 작업으로 넘어가지 않고 [Python 준비 복구](troubleshooting.ko.md#setup-resume)를 따릅니다. 이미 만들어진 가상환경·소스를 새로 만들지 않습니다.

2단계는 **`$RUN_DIR/workshop`**에서 시작하고, 2-2에서 서비스 준비를 위해 **`$REPO_ROOT`**로 돌아갑니다.

<a id="setup-identity"></a>

## 2. 로그인·소유권·용량 확인

### 2-1. Azure CLI와 azd 로그인

**`$RUN_DIR/workshop`**에서 로그인합니다. 그래야 이후 한국어 실습 명령이 이 폴더의 격리된 CLI 프로필을 씁니다. 아직 기반 서비스가 없으므로 README의 `preflight`·`bind`는 실행하지 않습니다.

**터미널 — 실행 폴더 (`$RUN_DIR/workshop`):** ID를 입력합니다. 이 로그인은 이 폴더의 `.azure-cli/`에만 보관합니다(공유·커밋 금지).

```bash
export AZURE_CONFIG_DIR="$PWD/.azure-cli" &&
read -r -p ".env의 AZURE_TENANT_ID 값: " LOGIN_TENANT_ID &&
read -r -p ".env의 AZURE_SUBSCRIPTION_ID 값: " LOGIN_SUBSCRIPTION_ID
```

**터미널 — 실행 폴더 (`$RUN_DIR/workshop`):** Azure CLI에 로그인합니다. 구독을 물으면 `.env`의 구독을 고릅니다.

```bash
az login --tenant "$LOGIN_TENANT_ID" --subscription "$LOGIN_SUBSCRIPTION_ID" --output none
```

**터미널 — 실행 폴더 (`$RUN_DIR/workshop`):** 같은 계정으로 azd에 로그인합니다.

```bash
azd auth login --tenant-id "$LOGIN_TENANT_ID"
```

**터미널 — 실행 폴더 (`$RUN_DIR/workshop`):** 두 로그인을 확인합니다.

```bash
az account show --subscription "$LOGIN_SUBSCRIPTION_ID" \
  --query "{user:user.name,tenant:tenantId,subscription:id,state:state}" --output json &&
azd auth status --output json
```

**완료 확인:** CLI의 `user`와 azd의 `email`이 `AZURE_EXPECTED_USERNAME`과 같고, `tenant`·`subscription`이 `.env`의 두 ID와 같으며, `state: Enabled`, `status: authenticated`입니다.

**다르면:** 지정한 계정으로 다시 로그인합니다. 브라우저가 열리지 않으면 [로그인 문제 해결](troubleshooting.ko.md#login)을 봅니다.

### 2-2. 계정·보존·용량 확인

2-1에서 로그인한 같은 터미널을 계속 씁니다. 터미널을 다시 열었다면 먼저 1-4의 **새 터미널에서 재개할 때**를 실행해 `AZURE_CONFIG_DIR`가 `$RUN_DIR/workshop/.azure-cli`를 가리키게 합니다.

**터미널 — 원래 clone (`$REPO_ROOT`):**

```bash
cd "$REPO_ROOT" &&
python scripts/provision_environment.py identity --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py ownership --run-dir "$RUN_DIR" --preserve-existing &&
python scripts/provision_environment.py model-capacity --run-dir "$RUN_DIR"
```

**완료 확인:** 각 명령의 마지막 JSON에서 아래 필드만 확인합니다.

- `identity` 출력: `requested_account_matches: true`, `configured_subscription_matches: true`, `configured_tenant_matches: true`, `subscription_state: Enabled`, `default_subscription_changed: false`
- `ownership` 출력: `existing_groups_explicitly_preserved: true`
- `model-capacity` 출력: `gpt-6-sol`·`gpt-6-luna`·`gpt-6-astra`와 보조 모델 `gpt-5.4-mini`의 GlobalStandard 레코드

**다르면:** 자원을 생성하지 않습니다. 계정 불일치는 위 로그인 확인, 권한·용량 오류는 환경 소유자와 확인한 뒤 [실패한 준비 명령만 복구](troubleshooting.ko.md#setup-resume)합니다. 구독·모델·리전을 임의로 바꾸지 않습니다.

<a id="setup-foundation"></a>

## 3. 새 전용 그룹과 서비스 생성

**`$RUN_DIR/config.json`**에 생성된 새 이름을 확인한 뒤 실행합니다.

**터미널 — 원래 clone (`$REPO_ROOT`):**

```bash
python scripts/provision_environment.py group --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py foundry --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py project --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py logs --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py insights --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py search --run-dir "$RUN_DIR"
```

**포털 — Azure Portal → Resource groups → 이번 실행 그룹:** 새 그룹을 엽니다.

**완료 확인:** 새 리소스 그룹이 아래 구조와 같습니다.

```text
Subscription
└─ 이번 실행의 리소스 그룹(`run=$RUN_ID`, Sweden Central)
   ├─ Foundry 계정·프로젝트
   ├─ Search
   ├─ Application Insights
   └─ Log Analytics
```

**Resources**에는 이번 실행이 만든 이름만 있고, 이전·공유 그룹의 자원은 없습니다. **Tags**에는 `workshop=foundry-evaluation`, `cleanup-scope=exclusive`, `purpose=synthetic-data-only`, `run=$RUN_ID`가 있습니다.

- Search는 Basic 1 replica / 1 partition입니다. `semanticSearch`와 `knowledgeRetrieval`의 `free` 설정이 **Search 가동·모델 호출까지 무료라는 뜻은 아닙니다.**
- Portal의 ARM **Deployments** 목록은 Foundry 모델 배포 목록과 다릅니다.

**다르면:** 출력의 실패한 명령과 [기존 생성 기록을 확인](troubleshooting.ko.md#setup-resume)합니다. 성공한 생성 명령부터 반복하거나 새 그룹을 만들지 않습니다. Search의 대기 시간 초과만 발생했다면 바로 아래 복구를 사용합니다.

<details>
<summary>Search 대기 시간만 초과했다면 — 같은 자원 확인</summary>

실패한 대기 기록을 보존하고, 자원을 재생성하거나 리전을 바꾸지 않습니다.

**터미널 — 원래 clone (`$REPO_ROOT`):**

```bash
python scripts/provision_environment.py search-status --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py wait-search --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py search-status --run-dir "$RUN_DIR"
```

**완료 확인:** 같은 Search 자원의 `provisioning_state`가 `Succeeded`이고 `status`가 `running`입니다. 4단계로 진행합니다.

**다르면:** 같은 `RUN_DIR`의 출력과 상태를 보존하고 환경 준비 복구로 돌아갑니다.

</details>

<a id="setup-access"></a>

## 4. 필요한 권한과 연결 준비

이 단계는 이번 실행의 새 자원에만 필요한 권한과 연결을 만듭니다.

- `user-*` 명령 4개는 **2단계에서 검증한 사용자 한 명**에게만 새 프로젝트·계정·Search 범위의 역할을 부여합니다. 다른 참가자는 [강사의 권한 체크리스트](instructor.ko.md#access)에 따라 별도로 준비합니다.
- `project-monitor`는 프로젝트 ID에 원격 분석 조회 권한을 줍니다.
- 두 연결 명령은 keyless Microsoft Entra(`AAD`) Search 연결과, metadata에 실제 `ResourceId`를 기록한 App Insights 연결을 만듭니다.
- 에이전트 인스턴스 ID는 나중에 생깁니다. [README 4단계](../README.ko.md#deploy)의 `grant-agent-access`로 Search/model 권한을 부여하며, 넓은 Owner 권한은 주지 않습니다.

**터미널 — 원래 clone (`$REPO_ROOT`):**

```bash
python scripts/provision_environment.py user-foundry --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py user-model --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py user-search-service --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py user-search-data --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py project-monitor --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py insights-connection --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py search-connection --run-dir "$RUN_DIR"
```

**완료 확인:** 명령이 오류 없이 끝납니다. 모든 역할 출력에 `created: true` 또는 `already_assigned: true`가 있고, `scope_resource`는 내 사용자에 대해 `project`·`foundry`·`search`, 프로젝트 ID에 대해 `insights`·`logs`입니다. 연결 출력에는 `resource: insights-connection`과 `resource: search-connection`이 있습니다.

**다르면:** 환경 소유자가 오류에 나온 주체와 범위를 확인한 뒤 [실패한 권한·연결 명령만 복구](troubleshooting.ko.md#setup-resume)합니다. 넓은 Owner 권한이나 공유 연결 변경으로 우회하지 않습니다.

<a id="setup-auxiliary"></a>

## 5. 보조 모델과 실제 엔드포인트 확인

planner/judge를 배포하고 Azure가 반환한 실제 엔드포인트를 새 실행 폴더에 반영합니다.

**터미널 — 원래 clone (`$REPO_ROOT`):**

```bash
python scripts/provision_environment.py auxiliary --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py ready --run-dir "$RUN_DIR"
```

**완료 확인:** **`$RUN_DIR/workshop/.env`**에 새 환경의 Project 엔드포인트와 Azure OpenAI 엔드포인트가 들어 있습니다. 두 엔드포인트는 서로 다르고, 이전 실행의 엔드포인트와도 달라야 합니다. 보조 모델은 `gpt-5.4-mini` / `2026-03-17`이며 planner/judge이지 세 후보 모델 중 하나를 대신하지 않습니다.

**다르면:** [같은 실행의 준비 상태](troubleshooting.ko.md#setup-resume)를 확인합니다. `auxiliary`가 성공하고 `ready`만 실패했다면 `ready`만 복구하며, 엔드포인트를 추측해 입력하지 않습니다.

<a id="setup-candidates"></a>

<a id="6-네-후보-준비-후-참가자에게-전달"></a>

## 6. 후보 준비, calibration 확인, 다음 전달 선택

### 6-1. 후보 준비

실행 폴더에서 후보 배포 상태를 맞춘 뒤 judge calibration을 확인하고 전달합니다.

**터미널 — 실행 폴더 (`$RUN_DIR/workshop`):** 실행 폴더로 이동: 5단계까지 완료한 같은 터미널을 사용합니다.

```bash
cd "$RUN_DIR/workshop" &&
source src/agent/.venv/bin/activate
```

**터미널 — 실행 폴더 (`$RUN_DIR/workshop`):** 후보 모델을 준비합니다. 아래 명령은 **사전 검사 → 없는 후보만 유료 배포 → 최종 검사**까지 합니다. 별도 `preflight`를 앞뒤로 반복하지 않습니다.

```bash
python scripts/workshop.py prepare-models
```

**완료 확인:** 오류 없이 종료됩니다. **마지막 JSON**에서 확인합니다.

- `language: ko`
- 세 후보 모두 `deployed: true`
- `missing_models: []`
- 고정 모델·버전: `gpt-6-sol` / `2026-09-22`, `gpt-6-luna` / `2026-09-22`, `gpt-6-astra` / `2026-09-03`

첫 JSON의 `missing_models`는 생성 전 상태일 수 있습니다.

<details>
<summary>선택 예시: 기록된 준비 상태 필드</summary>

기록된 화면에서 확인할 필드는 `language: ko`, `missing_models: []`, 후보마다 `deployed: true`입니다. `prepare-models`가 이미 실행하는 준비 점검의 출력이므로 따로 실행하지 않습니다. 내 환경의 배포 이름은 예시 화면과 다를 수 있습니다.

![기록된 한국어 준비 상태 필드 — 세 후보 배포 준비 완료](assets/live-ko-20260923b/screenshots/S1-02-preflight-after.webp)

</details>

**다르면:** 모델 접근·할당량·배포 오류를 해결한 뒤 [같은 폴더에서 실패한 준비만 복구](troubleshooting.ko.md#setup-resume)합니다.

<a id="setup-calibration"></a>

### 6-2. judge 확인

**터미널 — 실행 폴더 (`$RUN_DIR/workshop`):** judge calibration 확인: 후보 준비를 마친 뒤 실행합니다.

```bash
python scripts/workshop.py calibrate
```

**완료 확인:** **`Judge calibration passed`**. 예제 2개는 본평가 48개 응답에 포함하지 않습니다.

**다르면:** [calibration만 복구](troubleshooting.ko.md#calibration)합니다. 후보 준비가 끝났다면 `prepare-models`부터 반복하지 않습니다.

<a id="handoff"></a>

### 6-3. 전달 경로 선택

**다음 경로를 하나만 선택합니다.**

| 이어서 실행할 사람 | 사용할 폴더와 다음 행동 |
|---|---|
| 본인이 개인 실습을 이어서 할 때 | **`$RUN_DIR/workshop`**에서 [README의 `bind` 명령](../README.ko.md#bind-project)을 실행합니다. 6단계 `prepare-models`에서 준비 상태를 이미 확인했습니다. 별도 README `preflight`, clone, 설치, 로그인은 반복하지 않습니다. |
| 강사가 수업 리허설을 할 때 | 이 폴더에는 모델 소유권을 남깁니다. 새 실행 이름을 쓰는 [별도 리허설 clone](instructor.ko.md#rehearsal-workspace)에서 실습해, 리허설 cleanup이 공유 모델을 지우지 않게 합니다. |
| 새 참가자에게 전달할 때 | **미사용 조별 이름**과 **실제 준비된 모델 배포 이름**이 들어 있는 완성된 `.env`를 전달합니다. `.azure`, `.foundry`, 소유권 파일, 인증 캐시, 결과는 보내지 않습니다. 전달 전 [강사 체크리스트](instructor.ko.md#handoff)를 확인합니다. 참가자는 새 폴더에 `.env`를 저장하고 [README 1단계](../README.ko.md#start)부터 진행합니다. |

**완료 확인:** 전달 경로를 하나만 골랐고, 그 행에 적힌 폴더 또는 완성된 `.env`가 준비되었습니다.

**다르면:** README 1단계를 시작하지 말고 선택한 전달 행을 먼저 완료합니다.

- `LAB_LANGUAGE`를 바꾸거나 기존 지식 객체를 덮어쓰지 않습니다. 참가자 `cleanup`은 그 폴더의 소유 객체만 정리합니다.
- 환경 소유자는 기반 서비스·Search·로그·보조 모델 비용과 [한국어 결과 범위 질문](validation.ko.md)을 관리합니다.

<details>
<summary>참고: 준비 확인이 필요한 이유</summary>

- `--preserve-existing`은 영어 실습을 포함한 기존 그룹을 모두 보존합니다. 옵션 없이 실행하면 이전 실행의 후보 배포나 그룹을 발견했을 때 소유권 확인을 위해 중단할 수 있습니다.
- 각 Azure CLI 요청에는 설정한 구독이 명시됩니다. 용량 가용성과 구독 할당량은 별도 확인이며, 할당량은 6단계 모델 준비에서 다시 확인합니다.
- 도구는 태그뿐 아니라 이번 실행의 실제 생성 기록도 요구합니다. 태그만으로 다른 자원을 수정할 권한이 생기지 않습니다.

</details>

여기서 멈춥니다. 개인 전용 기반을 소유하고 README 정리까지 끝낸 경우에만 아래 선택 절차를 엽니다.

<details>
<summary>선택: README 10단계 후 개인 전용 기반 그룹 삭제</summary>

<a id="final-cleanup"></a>

**개인 전용 기반 환경까지 최종 정리하기 — 별도 선택**

**README 10단계의 `cleanup`·`check-cleanup`을 끝낸 환경 소유자만 진행합니다.** 개인 실습의 기반 서비스 삭제는 별도 선택이며, 참가자 정리나 Copilot CLI 실행 요청이 그룹 전체 삭제의 승인은 아닙니다.

| 환경 | 선택할 경로 |
|---|---|
| 기존·공유 환경 또는 다음 참가자/수업이 사용할 그룹 | **기반 서비스와 보조 배포를 보존합니다.** 담당자가 잔여 비용·보존 기간·최종 종료일을 관리합니다. 아래 그룹 삭제는 하지 않습니다. |
| 이 문서의 도구로 새로 만든 **본인 전용 그룹**, 다른 사용자·후속 실습 없음 | 아래 소유권 확인 후 **그 그룹만** 최종 삭제할 수 있습니다. |
| 생성 기록이 없거나 소유권·사용자가 불명확함 | 중단하고 환경 소유자에게 확인합니다. 이름·태그만으로 삭제하지 않습니다. |

<a id="final-cleanup-check"></a>

<details>
<summary>소유자 전용 삭제 절차: 확인, 삭제, 완료 확인</summary>

**1. 증거를 보관하고 삭제 범위 확인**

필요한 로컬 응답·평가·회귀 기록과 `verified-evidence.json`, `cleanup-check.json`을 보관합니다. 그룹 삭제 후 Foundry 보고서 URL과 Azure trace를 다시 열 수 있다고 가정하지 않습니다. 인증 캐시·암호·토큰은 공유하거나 커밋하지 않습니다.

**편집기 — 기록된 실행 폴더 (`$RUN_DIR`):** 준비 때 보관한 **같은 `RUN_DIR`**의 `config.json`과 `infrastructure-state.json`을 엽니다. 새 run을 만들지 않습니다.

| 확인할 것 | 일치해야 하는 값 |
|---|---|
| 실행 | `config.json → run_id`와 `infrastructure-state.json → run` |
| 삭제할 그룹 | `config.json → resource_group`. **`old_resource_group`는 보존 대상** |
| 구독·Resource ID | `config.json → subscription`과 `infrastructure-state.json → group_id`의 구독·그룹 |
| 생성된 서비스 | `infrastructure-state.json → resources`에 기록된 Resource ID |

**포털:** [Azure Portal](https://portal.azure.com/)에서 설정한 계정·tenant·구독을 확인하고 **Resource groups → 위 그룹**을 엽니다. 다음을 확인합니다.

- **Resource ID**가 기록된 `group_id`와 같습니다.
- **위치**가 Sweden Central(`swedencentral`)입니다.
- **Tags**가 `workshop=foundry-evaluation`, `cleanup-scope=exclusive`, `purpose=synthetic-data-only`, `run=내 실행 ID`와 일치합니다.
- **Resources**에는 이번 실행의 생성 기록에 있는 Foundry 계정·프로젝트·Search·App Insights·Log Analytics·보조 배포만 있어야 합니다.
- 현재 사용 현황에는 다른 사용자나 후속 수업 의존성이 없어야 합니다.

기록에 없는 자원, 다른 그룹과의 불명확한 종속성, 후속 수업 계획이 있으면 삭제하지 않습니다. 태그나 소유권 파일을 고쳐 조건을 맞추지 않습니다.

**2. 검토한 그룹만 삭제**

**그룹 전체와 남은 서비스가 삭제되며 그룹 자체는 복구할 수 없습니다.** 위 범위와 영향을 확인한 소유자가 삭제를 결정한 뒤에만 실행합니다. Copilot CLI에 맡긴다면 **정확한 구독·그룹·삭제 영향에 대해 이 작업을 별도로 승인**합니다.

**포털:** 같은 그룹 화면에서 **Delete resource group**을 선택하고, 확인란에 **검토한 그룹 이름**을 입력해 삭제를 확정합니다. 다른 그룹이나 공유 환경으로 범위를 넓히지 않습니다. [공식 그룹 삭제 절차](https://learn.microsoft.com/azure/azure-resource-manager/management/delete-resource-group#delete-resource-group)를 따릅니다.

**3. 삭제 완료와 남은 비용 확인**

**포털:** **삭제 완료 알림**을 기다린 뒤, 같은 구독의 Resource groups 목록을 새로 고쳐 정확한 그룹 이름이 사라졌는지 확인합니다. 삭제 요청 제출만으로 완료로 기록하지 않습니다. 잠금·권한·종속성 오류가 나면 오류를 보존하고 담당자에게 확인하며 보호 설정을 임의 해제하지 않습니다.

**이후 `check-cleanup`을 다시 실행하지 않습니다.** 그 명령은 기반 서비스가 보존된 README 10단계를 검사하므로, 전체 그룹 삭제 확인은 위 포털 결과로 합니다. 이미 발생한 사용료와 지연 반영 비용은 남을 수 있습니다. 구독의 **Cost Management → Cost analysis**에서 확인하며, 삭제 성공을 청구액 0으로 해석하지 않습니다.

참고 자료: [공식 Foundry 기본 인프라 예제](https://github.com/Azure-Samples/azd-ai-starter-basic/tree/main/infra) · [Search knowledge retrieval 과금 설정](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-enable-disable).


</details>
</details>
