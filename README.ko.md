# 출장 규정 에이전트를 실행하고, 평가하고, 개선하기

[English guide](README.md)

**출장비 질문에 규정을 찾아 답하는 AI 에이전트를 실행하고, 지침을 바꾸면 답변이 나아지는지 확인합니다.** 에이전트 코드와 두 지침 버전(V1·V2)이 모두 제공되므로 코드를 작성하지 않습니다.

**기본 실습은 120분입니다.** 실제 응답 48개를 모아 **한 사례를 검토하고, V1 → V2를 비교하고, 새 질문에서도 V2가 통하는지 보고**합니다. 낮은 점수도 실습 결과입니다. 목표는 만점이나 운영 승인이 아닙니다.

<a id="start-here"></a>
<a id="other-starts"></a>
<a id="다른-상황"></a>
<a id="내-상황에-맞는-시작점"></a>

## 여기서 시작하세요

**내 상황에 맞는 시작점 하나만 따릅니다.** 아래 문서를 모두 읽을 필요는 없습니다.

| 내 상황 | 시작할 곳 |
|---|---|
| 수업에서 강사에게 완성된 조별 `.env`를 받음 | [1단계](#start)부터 **1–10단계를 순서대로** 진행 |
| `.env` 준비가 덜 됐고, 사용할 Foundry·Search·관측 서비스가 모두 있음 | 환경 소유자가 [기존 환경 준비](docs/instructor.ko.md#existing-foundation)를 마침 → 그 문서의 전달 안내를 따름 |
| 필요한 기반 서비스가 없어 **새 전용 환경**이 필요함 | [새 환경 준비](docs/environment.ko.md)의 시작 전 확인과 1–6단계를 마침 → 그 문서의 안내대로 [1-4 연결](#bind-project)부터 진행 |
| 이전 실행을 이어감 | [같은 폴더에서 재개](docs/troubleshooting.ko.md#resume). 정상 중단이면 다음 미실행 블록, 오류·상태 불명이면 해당 명령 복구 |

**`.env`가 없다는 이유만으로 새 서비스를 만들지 않습니다.** 환경 준비 경로는 하나만 선택합니다. 혼자 실습하면 환경 소유자는 본인입니다.

**필요한 도구:** Git, Python 3.13, Bash, curl, Azure CLI, azd(`microsoft.foundry` 확장), 편집기(VS Code 권장), 브라우저. Windows는 WSL을 씁니다([설치·확인](docs/instructor.ko.md#tools)). 도구 설치·Azure 환경 준비는 120분에 포함하지 않습니다.

**비용:** 로컬 실행도 유료 Azure 모델과 Search를 호출합니다. 혼자 만든 환경은 10단계 뒤 [본인 전용 리소스 그룹 삭제](docs/environment.ko.md#final-cleanup)까지 해야 기반 서비스 비용이 멈춥니다.

<details>
<summary>선택: Copilot CLI에 실행을 맡기고 싶다면</summary>

[Copilot 가이드](docs/copilot.ko.md)를 따르고, 수동 실행을 동시에 하지 않습니다. 직접 실행에는 Copilot·Playwright가 필요 없습니다.

</details>

<a id="실습-개요"></a>

## 10단계 실습 경로

**Microsoft Foundry**는 AI 에이전트를 배포·평가·관찰하는 Azure 플랫폼입니다. 이 실습에서는 세 모델에 같은 질문을 하고, 제공된 지침만 V1에서 V2로 바꿔 비교합니다.

```text
질문 → Python 에이전트 → Foundry IQ로 정책 검색 → 후보 모델 → 답변
```

| 단계 | 다음으로 넘어가는 기준 |
|---|---|
| [1. 시작 준비](#start) | 테스트·두 로그인·preflight·프로젝트 연결 완료 |
| [2. 정책 검색](#lab-a) | 내 지식베이스가 `TRAVEL-2026`을 반환 |
| [3. 로컬 실행](#local) | `HTTP 200`과 실제 V1 답변 |
| [4. 배포](#deploy) | 원격 답변에 숫자 에이전트 버전이 있음 |
| [5. V1 평가](#lab-c) | 6문항 × 3모델 = V1 18응답 평가 완료 |
| [6. 한 사례 검토](#lab-d) | 원래 trace와 함께 검토 기록 저장 |
| [7. V2 평가](#lab-e) | **같은 6문항** × 3모델 = V2 18응답 평가·전후 비교 완료 |
| [8. 새 질문으로 확인](#lab-f) | 별도 4문항 × 3모델 = 바꾸지 않은 V2의 12응답 평가 완료 |
| [9. 증거 확인·보고](#lab-g) | 48응답·48 trace·검토 이력 검증과 세 항목 보고 |
| [10. 정리](#cleanup) | 내 소유 객체만 삭제 |

**시간:** 1–2단계 25분 · 3–4단계 15분 · 5–6단계 30분 · 7–8단계 30분 · 9–10단계 15분 · 여유 5분. **9단계 보고 → 10단계 정리** 순서이며, 선택 [레벨 2·3](#levels)은 그 사이에 합니다.

<a id="how-to-follow"></a>

### 진행 방법

- **수업 실행자:** 조별 `.env` 하나당 **한 명이 자기 계정·PC·실습 폴더 하나로** 명령을 실행하고, 나머지는 그 화면을 보며 함께 검토합니다. 같은 `.env`를 여러 PC에서 실행하면 같은 이름의 자원을 서로 소유하려 하므로 중단됩니다. 각자 실행하려면 시작 전에 강사에게 실행자별 다른 `LAB_PREFIX`·`LAB_AGENT_NAME`이 든 `.env`를 받습니다.
- **작업 위치:** 블록 앞의 굵은 라벨(**터미널 A**, **터미널 B**(3단계만), **편집기**, **포털**)을 따릅니다. “내 에이전트”는 `LAB_AGENT_NAME`입니다.
- **한 블록씩:** **작업 위치 → 명령 실행 → 완료 확인 → 다음 블록** 순서입니다. 입력 프롬프트(다음 명령을 입력할 수 있는 줄)가 돌아올 때까지 기다립니다. 3단계 서버만 예외입니다. 입력 요청이 나오면 값만 붙여넣고 Enter를 누릅니다.
- **멈출 때:** 오류가 나거나 **완료 확인**의 필수 값이 없으면 바로 아래 **다르면**을 따라 [그 명령만 복구](docs/troubleshooting.ko.md#resume)합니다. 실행이 끝난 뒤의 낮은 유효 점수는 **기록하고 계속**합니다. 좋은 점수를 얻으려고 다시 실행하지 않습니다. 오늘 끝내거나 나중에 이어 하려면 [중도 종료 안내](#stop-early)를 따릅니다.
- **새 터미널:** Bash를 열고 메모한 경로로 [복원 블록](#resume-shell)을 실행합니다(3단계 터미널 B 블록에는 포함됨).
- **기록:** 편집기에 텍스트 문서 **하나**를 열고, 각 단계에서 요청한 값을 적습니다. 쉬기 전에는 `마지막 완료 블록 / 다음 블록 / 실습 폴더`도 저장합니다. 9-3에서 **같은 문서**를 [보고서 양식](#finish)에 맞춰 정리합니다.

**`data/holdout.jsonl`은 8단계 전까지 열지 않습니다.** 용어는 사용하는 단계에서 설명합니다([전체 용어](docs/reference.ko.md#terms)). 접힌 참고·예시와 영상은 필요할 때만 봅니다.

<details>
<summary>터미널·파일·출력 읽기가 익숙하지 않다면</summary>

| 보이는 표현 | 이렇게 읽으세요 |
|---|---|
| 저장소 루트 / “이 폴더” | 명령을 실행할 코드의 맨 위 폴더. 수업은 1-1의 clone, 새 환경을 만들었다면 준비 문서 6-3의 `/workshop` 폴더 |
| 코드 블록 | 블록 안의 명령만 복사합니다. 앞에 `$`를 덧붙이지 않습니다. 수집을 복구했다면 [실제 label·동시성](docs/troubleshooting.ko.md#run-values)을 먼저 적용합니다 |
| `&&` | 앞 명령이 성공해야 다음 명령을 실행합니다 |
| `$PWD`, `"$ROW_ID"` 같은 코드 | 터미널이 값으로 바꿉니다. `$`나 따옴표를 지우거나 직접 치환하지 않습니다 |
| 출력 설명의 `<내 에이전트>` | 실제 출력에는 내 `LAB_AGENT_NAME` 값이 나옵니다. 이 문구를 입력하지 않습니다 |
| `language: ko` | JSON에서는 `"language": "ko"`로 보입니다. `true`는 참, `false`는 거짓, `[]`는 빈 목록입니다 |

JSON이나 쿼리가 길게 나와도 정상입니다. **완료 확인**의 값은 대개 출력 **맨 아래**에 있습니다. 출력 끝의 `Next:` 제안 명령과 `Update available` 안내 대신 **이 가이드의 다음 블록**을 따릅니다.

`.env`(설정 파일)와 `src/agent/.foundry/`(결과 폴더)는 점(.)으로 시작하는 숨김 파일·폴더입니다. VS Code의 **File → Open Folder**로 실습 폴더를 열면 탐색기에서 볼 수 있습니다. 파일을 수정한 뒤에는 **Ctrl+S(macOS: Cmd+S)**로 저장합니다. `.env`는 실행하거나 `source`하지 않습니다.

도움이 필요하면 실패한 명령·오류·단계만 전달하고, 암호·토큰·`.env` 전체는 공유하지 않습니다. “강사”·“환경 소유자”는 수업에서는 강사, 혼자 실습하면 본인입니다.

</details>

<a id="배경-learning-loop와-frontier-ecosystems"></a>
<a id="이-실습에서는-무엇으로-연결하나요"></a>

<a id="start"></a>
<a id="4-시작-전-준비"></a>

## 1. 시작 준비

**목표:** 새 한국어 실습용 폴더에서 로그인과 프로젝트 연결을 마칩니다. **혼자 만든 환경에서 왔다면**([새 전용 환경](docs/environment.ko.md) 6단계 완료) 1-1~1-3과 preflight를 건너뛰고 [연결](#bind-project)만 실행합니다.

<a id="source-setup"></a>

### 1-1. 코드와 `.env` 준비

**터미널 A — Bash 실행:** 터미널을 열고 아래를 실행합니다(이미 Bash여도 괜찮습니다. macOS 기본은 zsh, Windows는 WSL 터미널 사용).

```bash
bash
```

**완료 확인:** 새 입력 프롬프트가 나옵니다. 창이 새로 열리거나 성공 문구가 나오지 않아도 정상입니다.

**다르면:** `command not found`이면 [Bash/WSL 설치](docs/instructor.ko.md#tools)를 확인합니다.

**터미널 A — 새 폴더로 clone:** 실습 결과가 없는 **clone이나 압축을 푼 ZIP 폴더**가 이미 있으면 이 블록을 건너뛰고, 그 폴더 루트로 이동해 `ls README.ko.md && pwd`만 실행합니다.

```bash
git clone https://github.com/junwoojeong100/foundry-evaluation.git foundry-evaluation-ko &&
cd foundry-evaluation-ko &&
ls README.ko.md &&
pwd
```

**완료 확인:** `README.ko.md`와 이 폴더의 절대 경로가 출력됩니다. 터미널 A가 저장소 루트(이하 “이 폴더”)에 있다는 뜻입니다. 경로를 메모해 두면 새 터미널에서 돌아올 때 씁니다.

**다르면:** `already exists`이면 명령의 `foundry-evaluation-ko` 두 곳을 새 이름(예: `foundry-evaluation-ko-2`)으로 바꿔 실행합니다. 이전 결과가 있는 폴더는 다시 쓰지 않습니다.

<a id="workspace-settings"></a>

**편집기 — `.env` 추가(수업 참가자):** VS Code의 **File → Open Folder**로 이 폴더를 엽니다. 강사가 준 `.env`를 탐색기의 `README.ko.md` 옆(폴더 맨 위)에 넣고 열어 아래를 확인합니다. 이미 `.env`가 있으면 덮어쓰지 말고 강사에게 확인합니다.

- **파일:** `.env`(`.env.txt`가 아님).
- **로그인할 사람:** `AZURE_EXPECTED_USERNAME`이 실행자 **본인의 Azure 로그인 이름/이메일**이어야 합니다. `.env`는 설정표이지 계정·암호나 접근 권한이 아닙니다. 강사가 이 계정의 접근을 준비하고, 실행자가 자기 로그인·MFA를 완료합니다.
- **역할 부여 지원:** 직접 역할을 부여할 권한이 없다면 강사와 **2-1 `prepare-iq`·4-2 `grant-agent-access`의 지원 담당자·가능 시간**을 정합니다([권한 확인](docs/instructor.ko.md#access)). 관리자는 자기 세션에서 필요한 할당만 수행하며, 실행자는 본인 계정·폴더를 유지합니다.
- **내 값:** `LAB_LANGUAGE=ko`, `LAB_PROMPT_VERSION=v1`, 그리고 조별로 겹치지 않는 `LAB_PREFIX`·`LAB_AGENT_NAME`.
- **강사 값:** `MODEL_*_DEPLOYMENT`와 `LAB_AUX_DEPLOYMENT`에 강사가 준비한 배포 이름.
- **금지:** 빈 값, `<...>` 표시, 암호, key, token.

**터미널 A — 파일 이름과 두 값 확인:**

```bash
ls -a .env &&
grep -E '^LAB_(LANGUAGE|PROMPT_VERSION)=' .env
```

**완료 확인:** `.env`, 그리고 `LAB_LANGUAGE=ko`와 `LAB_PROMPT_VERSION=v1` 두 줄이 출력되고, 편집기에서 위 조건도 모두 확인했습니다. `.env`는 Python이 읽으므로 실행하거나 `source`하지 않습니다.

**다르면:** `No such file`이면 파일이 `.env.txt`나 `env` 같은 이름으로 저장됐는지 보고 정확히 `.env`로 바꿉니다. 빠진 값이나 실행자와 다른 `AZURE_EXPECTED_USERNAME`은 강사에게 확인하고, 그 계정의 접근이 준비된 `.env`를 받은 뒤 진행합니다. 다른 사람의 계정·암호를 빌리거나 설정값을 추측하지 않습니다.

<details>
<summary>이 값들이 중요한 이유</summary>

- 이어서 하는 실행이라면 `LAB_LANGUAGE`와 `LAB_PROMPT_VERSION`을 바꾸지 않습니다. 결과와 소유권이 언어에 묶여 있습니다.
- `LAB_PREFIX`·`LAB_AGENT_NAME`은 영문 소문자로 시작하는 3–50자의 소문자·숫자·하이픈입니다.
- `MODEL_*` 값을 바꿔도 모델이 생기지 않습니다. 조별 이름을 바꿔도 강사의 배포 이름은 유지합니다([이름 구분](docs/reference.ko.md#model-names)).

</details>

<a id="python-setup"></a>

### 1-2. 가상환경과 로컬 테스트

**터미널 A — 설치:**

```bash
python3.13 -m venv src/agent/.venv &&
source src/agent/.venv/bin/activate &&
python -m pip install -r requirements.txt
```

**완료 확인:** 설치 로그가 끝나고 `(.venv)`가 붙은 프롬프트로 돌아옵니다. `Requirement already satisfied`도 정상입니다.

**다르면:** `python3.13`을 찾지 못하면 [도구 설치](docs/instructor.ko.md#tools)를 확인합니다. 패키지 다운로드 오류이면 네트워크를 확인한 뒤 이 설치 블록만 다시 실행합니다. 아직 테스트로 넘어가지 않습니다.

**터미널 A — 테스트:**

```bash
python -m unittest discover -s tests -v
```

**완료 확인:** 테스트 출력이 **`OK`**로 끝납니다.

**다르면:** 다음 단계로 가지 않습니다. 설치 문제는 위 설치 블록의 안내를 따르고, 테스트의 `FAIL`·`ERROR`는 [오프라인 테스트 복구](docs/troubleshooting.ko.md#offline-tests)에서 원인을 구분합니다. 테스트나 정답을 고쳐 통과시키지 않습니다.

<a id="login"></a>

### 1-3. Azure CLI와 azd 로그인

**터미널 A:** 같은 터미널에서 1–4번 블록을 순서대로 실행합니다. 4번이 두 로그인을 한 번에 확인합니다.

- 1번에서 입력한 ID는 2–4번에서 그대로 씁니다. `.env`의 `=` 오른쪽 값만 붙여넣고, 암호·로그인 코드는 넣지 않습니다.
- 2·3번 뒤에는 브라우저에서 `AZURE_EXPECTED_USERNAME` 계정으로 로그인하고(다른 계정이 보이면 **다른 계정 사용**) 프롬프트가 돌아올 때까지 기다립니다.
- 2·3번에서 오류가 나면 거기서 멈추고 다음 블록으로 가지 않습니다.

**터미널 A — 1. ID 입력:** 이 로그인은 이 폴더의 `.azure-cli/`에만 보관합니다(공유·커밋 금지).

```bash
export AZURE_CONFIG_DIR="$PWD/.azure-cli" &&
read -r -p ".env의 AZURE_TENANT_ID 값: " LOGIN_TENANT_ID &&
read -r -p ".env의 AZURE_SUBSCRIPTION_ID 값: " LOGIN_SUBSCRIPTION_ID
```

**완료 확인:** 두 ID를 입력한 뒤 프롬프트가 돌아옵니다. 아직 로그인은 시작하지 않았습니다.

**다르면:** 잘못 입력했다면 이 블록만 다시 실행합니다. `read: -p: no coprocess`이면 `bash`를 실행한 뒤 다시 입력합니다.

**터미널 A — 2. Azure CLI 로그인:** 구독을 물으면 `.env`의 구독을 고릅니다.

```bash
az login --tenant "$LOGIN_TENANT_ID" --subscription "$LOGIN_SUBSCRIPTION_ID" --output none
```

**완료 확인:** 브라우저 로그인을 마치고 터미널에 오류 없이 프롬프트가 돌아옵니다. `--output none`이므로 계정 JSON은 출력하지 않습니다.

**다르면:** [로그인 복구](docs/troubleshooting.ko.md#login)에서 Azure CLI만 복구한 뒤 3번으로 진행합니다.

<a id="azd-login"></a>

**터미널 A — 3. azd 로그인:** 같은 계정을 씁니다.

```bash
azd auth login --tenant-id "$LOGIN_TENANT_ID"
```

**완료 확인:** 브라우저 로그인을 마치고 터미널에 오류 없이 프롬프트가 돌아옵니다. 실제 계정 일치는 다음 블록에서 확인합니다.

**다르면:** [로그인 복구](docs/troubleshooting.ko.md#login)에서 azd만 복구합니다. 성공한 Azure CLI 로그인은 반복하지 않습니다.

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

**터미널 A — 프로젝트 확인:** 첫 출력까지 30초 안팎 걸릴 수 있습니다.

```bash
python scripts/workshop.py preflight
```

**완료 확인:** 출력 맨 아래에 `missing_models: []`와 `language: ko`가 있고, 그 위 `gpt-6-sol`·`gpt-6-luna`·`gpt-6-astra`가 모두 `deployed: true`입니다.

**다르면:** `language: en`이면 아직 쓰지 않은 폴더일 때만 `.env`의 `LAB_LANGUAGE`를 `ko`로 고칩니다. `missing_models`가 비어 있지 않으면 `.env`의 `MODEL_*_DEPLOYMENT` 값이 받은 그대로인지 먼저 확인합니다. 그대로라면 모델 배포가 준비되지 않은 것이므로 환경 소유자에게 요청합니다(직접 만든 환경이면 [환경 준비 6-1](docs/environment.ko.md#setup-candidates)을 그 폴더에서 다시 확인).

<details>
<summary>예시 화면: preflight 완료와 Build → Models</summary>

세 모델의 `deployed: true`, 빈 `missing_models`, `language: ko`를 확인합니다.

![로그인 후 세 모델과 프로젝트 준비 상태 확인](docs/assets/live-ko-20260923b/screenshots/S1-02-preflight-after.webp)

같은 배포는 포털 **Build → Models**에서도 볼 수 있습니다. 이름은 강사가 준비한 실제 배포 이름이며, 모델 ID·버전이 고정 값과 같아야 합니다.

![Build → Models의 세 후보와 judge 배포](docs/assets/live-ko-20260923b/screenshots/S1-P01-models-after.webp)

</details>

<a id="bind-project"></a>

**터미널 A — 연결:** 위 preflight 완료 확인을 통과한 뒤 실행합니다. **환경 준비 문서(6단계)에서 왔다면** 그 문서의 `prepare-models`가 preflight까지 마쳤으므로, 그 문서 6-3의 “실습 폴더 열기” 블록으로 연 폴더에서 이 블록만 실행합니다.

```bash
python scripts/workshop.py bind
```

**완료 확인:** `Bound <내 에이전트> to /subscriptions/.../projects/<내 프로젝트>`.

**다르면:** [증상별 확인](docs/troubleshooting.ko.md#symptoms)의 `bind` 항목을 봅니다.

<a id="resume-shell"></a>

<details>
<summary>나중에 새 터미널을 열었다면: 이 폴더의 실행 환경 복원</summary>

새 터미널에서 `bash`를 실행한 뒤 아래 블록을 실행하고, 입력 요청에 메모한 이 폴더의 절대 경로를 붙여넣습니다. 기존 로그인 캐시를 다시 사용합니다. 3단계 터미널 B 블록에는 이미 포함돼 있습니다. **가상환경 생성 전이라면** 복원 대신 기존 폴더에서 메모한 다음 작업을 진행합니다. 1-1을 마쳤다면 [1-2](#python-setup)입니다.

```bash
read -r -p "실습 폴더의 절대 경로: " WORKSHOP_DIR &&
cd "$WORKSHOP_DIR" &&
source src/agent/.venv/bin/activate &&
export AZURE_CONFIG_DIR="$PWD/.azure-cli"
```

**완료 확인:** 프롬프트에 `(.venv)`가 표시되고 오류가 없습니다. `az account set`은 쓰지 않으며, 실행을 시작한 뒤에는 `LAB_LANGUAGE`를 바꾸지 않습니다.

**다르면:** `No such file or directory`이면 `/`로 시작하는 전체 경로를 따옴표 없이 다시 붙여넣습니다(`~`는 쓰지 않음). 경로를 잊었다면 실습 폴더를 연 VS Code 창에서 **Terminal → New Terminal**을 열고 `pwd`로 확인합니다.

**복원 뒤:** 메모한 다음 미실행 블록으로 돌아갑니다. 아래 “다음: 2단계”는 처음 1단계를 마친 사람의 경로입니다. 로그인 만료 오류가 실제로 나면 [로그인 복구](docs/troubleshooting.ko.md#login)를 따릅니다.

</details>

**다음:** [2. 조직의 지식 넣고 검색하기](#lab-a)

<a id="lab-a"></a>
<a id="5-실습-a--조직의-기억을-foundry-iq에-넣기"></a>
<a id="2-조직의-지식-넣기--실습-a"></a>

## 2. 조직의 지식 넣고 검색하기

**목표:** 합성 정책 7개로 만든 **지식베이스(KB)**가 맞는 정책을 찾습니다.

<a id="knowledge-registration"></a>

### 2-1. 정책 등록

**편집기:** `data/policies.json`을 열어 `TRAVEL-2026`의 적용일·상태·숙박 한도를 확인합니다. 파일은 수정하지 않습니다.

**터미널 A:**

```bash
python scripts/workshop.py prepare-iq
```

**완료 확인:** `Created: ...` 줄들 뒤에 `Foundry IQ ready: <내 KB>; 7 synthetic documents.`가 나옵니다. 내 KB 이름은 `LAB_PREFIX` + `-kb`입니다.

**다르면:** `AuthorizationFailed`나 `roleAssignments/write`이면 2-2 전에 멈춥니다. 접근 관리자가 [역할 부여 복구](docs/instructor.ko.md#role-recovery)의 `prepare-iq` 행대로 **Search identity의 planner 접근을 실제로 부여·확인한 뒤**, 실행자가 같은 계정·폴더에서 이 명령만 다시 실행합니다. 관리자 계정으로 바꿔 로그인하지 않습니다. 그 밖의 오류는 [증상별 확인](docs/troubleshooting.ko.md#symptoms)을 봅니다.

<a id="policy-retrieval"></a>

### 2-2. 검색 확인

**터미널 A:**

```bash
python scripts/workshop.py retrieve --query "2026년 9월 국내 출장 숙박비 한도는 얼마인가요?"
```

**완료 확인:** `knowledge_base`가 내 KB이고, `document_ids`에 **`TRAVEL-2026`**이 있으며, `activity`가 비어 있지 않습니다. 과거 규정이 함께 나올 수도 있습니다.

**다르면:** [검색 복구](docs/troubleshooting.ko.md#retrieval)를 따릅니다.

### 2-3. 포털에서 KB 확인

**포털:** 브라우저에서 [Microsoft Foundry](https://ai.azure.com/)를 열고 같은 계정으로 로그인합니다. 포털 단계는 모두 영어 메뉴 기준입니다.

1. 화면 오른쪽 위 **New Foundry** 스위치를 켭니다.
2. 왼쪽 위 프로젝트 이름을 눌러 `.env`의 `AZURE_AI_PROJECT_NAME`(리소스 `AZURE_AI_ACCOUNT_NAME`)을 고릅니다.
3. 위쪽 **Build** → 왼쪽 **Knowledge** → **Knowledge bases** → 내 KB(`LAB_PREFIX` + `-kb`)를 엽니다.

**완료 확인:** 아래쪽 **Knowledge sources**의 지식 소스(`LAB_PREFIX` + `-source`)가 **Active**이고 **Retrieval instructions**가 채워져 있습니다.

**다르면:** [포털 화면 차이](docs/troubleshooting.ko.md#portal-differs)를 봅니다.

**예시 화면:** KB·검색 지침·지식 소스(내 이름은 다름)

![실제 KB·검색 지침과 source](docs/assets/live-ko-20260923b/screenshots/S2-P01-knowledge-after.webp)

**다음:** [3. 로컬에서 한 번 실행하기](#local)

<a id="local"></a>
<a id="6-실습-b--python-에이전트를-hosted-agent로-배포"></a>
<a id="3-로컬에서-한-번-실행하기--실습-b"></a>

## 3. 로컬에서 한 번 실행하기

**목표:** 내 PC에서 실행한 에이전트가 실제 V1 한국어 답변을 반환합니다.

### 3-1. 서버 시작

**터미널 A — 경로 복사:** 이 폴더의 경로를 출력해 복사합니다. 3-2에서 터미널 B에 붙여넣습니다.

```bash
pwd
```

**완료 확인:** `/`로 시작하는 실습 폴더 경로를 복사했습니다.

**다르면:** 경로가 1단계에서 메모한 폴더와 다르면 [터미널 복원](#resume-shell) 후 다시 확인합니다.

**터미널 A — 서버 시작:** V1을 선택하고 서버를 시작합니다. 3-3까지 그대로 둡니다. `Selected v1; run azd deploy ...` 안내의 배포는 4단계에서 하며, 처음에는 의존성 설치로 30초쯤 걸립니다.

```bash
python scripts/workshop.py set-prompt v1 &&
azd ai agent run --no-client
```

**완료 확인:** `Starting agent on http://localhost:8088` 뒤로 로그가 이어지다가 traceback 없이 `Running on http://0.0.0.0:8088`이 나오고, 입력 프롬프트로 돌아오지 않습니다.

**다르면:** [증상별 확인](docs/troubleshooting.ko.md#symptoms)의 8088 포트 항목을 봅니다.

### 3-2. 터미널 B에서 요청 보내기

**터미널 B — Bash 시작:** 터미널 A는 그대로 두고 새 터미널 창(또는 탭)을 열어 실행합니다. 이미 Bash여도 됩니다.

```bash
bash
```

**완료 확인:** 터미널 B에 새 입력 프롬프트가 나오고 터미널 A의 서버는 계속 실행 중입니다.

**다르면:** A의 서버를 종료했다면 3-1에서 다시 시작합니다. B에는 서버 시작 명령을 붙여넣지 않습니다.

**터미널 B — 요청 보내기:** 입력 요청이 나오면 3-1에서 복사한 절대 경로를 붙여넣고 Enter를 누릅니다. 블록이 경로를 알아서 따옴표로 감싸고, 환경을 복원하고, readiness를 확인한 뒤 요청 하나를 보냅니다.

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

**목표:** 같은 코드가 Azure에서 번호가 붙은 에이전트 버전으로 답합니다. 로컬 Docker는 필요 없습니다.

<a id="deploy-code"></a>

### 4-1. 코드 배포

**터미널 A:** 보통 1–3분 걸리며, `Polling agent status (1/30)`처럼 상태 줄이 이어지는 것은 정상입니다.

```bash
azd deploy --no-prompt
```

**완료 확인:** `SUCCESS: Your application was deployed ...`가 나오고 입력 프롬프트가 돌아옵니다. 그 앞뒤의 `Next:` 제안 명령과 `Update available` 안내는 실행하지 않습니다.

**다르면:** 오류 출력을 보존하고 [배포 자체 실패·상태 확인](docs/troubleshooting.ko.md#deployment-recovery)을 따릅니다. 성공 여부를 모른 채 재배포하거나 4-2로 넘어가지 않습니다.

<a id="agent-access"></a>

### 4-2. 에이전트 접근 권한 부여

**터미널 A:**

```bash
python scripts/workshop.py grant-agent-access
```

**완료 확인:** `Search read and Foundry model inference access configured for <내 에이전트>.`

**다르면:** 역할 부여 권한 오류이면 [역할 부여 복구](docs/instructor.ko.md#role-recovery)의 `grant-agent-access` 행에서 에이전트 principal과 역할·범위를 확인합니다. 관리자가 자기 세션에서 할당을 마친 뒤 실행자가 같은 계정·폴더에서 이 명령만 다시 실행합니다. 재배포하거나 Owner 권한을 추가하지 않습니다. 그 밖의 오류는 [Hosted Agent 증상](docs/troubleshooting.ko.md#symptom-hosted)을 봅니다.

<a id="hosted-smoke"></a>

### 4-3. 원격 응답 확인

**터미널 A:** 원격 에이전트에 요청 하나를 보내고, 출력된 `agent_version`을 메모에 `V1 버전: N`으로 적어 둡니다. 첫 호출은 30초쯤 걸릴 수 있습니다.

```bash
python scripts/workshop.py smoke
```

**완료 확인:** 비어 있지 않은 한국어 `answer`, `prompt_version: v1`, `trace_id`(이 요청의 실행 기록 ID), **숫자로 된 `agent_version`**이 담긴 JSON. 버전은 `1`이 아닐 수도 있으며, 7-2에서는 다른 번호가 나와야 합니다.

**다르면:** `424`나 시간 초과이면 에이전트가 아직 시작 중일 수 있으니 1–2분 뒤 `smoke`만 다시 실행합니다. 권한 오류(`403`)이면 4-2가 성공했는지 확인하고, 역할 반영에 몇 분 걸릴 수 있으니 5분쯤 뒤 다시 실행합니다. 재배포하지 않습니다([Hosted Agent 증상](docs/troubleshooting.ko.md#symptom-hosted)).

### 4-4. 포털에서 버전 확인

**포털:** 왼쪽 **Agents** → 내 에이전트(`LAB_AGENT_NAME`) → **Playground** 탭을 열고, 화면 오른쪽 위 **Version** 상자에서 4-3의 번호를 고릅니다.

**완료 확인:** 오른쪽 위 **Version**에 4-3의 숫자 `agent_version`이 선택되어 있습니다.

**다르면:** 먼저 선택한 버전이 4-3 출력의 `agent_version`과 같은지 확인하고, 그래도 다르면 [포털 화면 차이](docs/troubleshooting.ko.md#portal-differs)를 봅니다.

<details>
<summary>예시 화면(포털이 다르게 보이면 열기): 실제 원격 응답과 Playground</summary>

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

<a id="evaluation-runs"></a>

**아래 세 label은 첫 실행의 기본값입니다.** 수집을 복구했다면 [실제 label·동시성 메모](docs/troubleshooting.ko.md#run-values)를 이후 명령·경로·출력 설명에 적용합니다. 같은 에이전트(`LAB_AGENT_NAME`)가 질문을 세 후보 모델에 보내 각각 답변 하나씩 받습니다. `model_key`의 `sol`·`luna`·`astra`는 각각 `gpt-6-sol`·`gpt-6-luna`·`gpt-6-astra`를 고르는 키이며, 에이전트 이름이나 Azure 배포 이름이 아닙니다.

**V1·V2는 모델이 아니라 지침(prompt)의 버전**, **split은 질문 묶음**, **label은 결과 폴더 이름**입니다. `dev`는 개선에 쓰고, `holdout`은 V2를 고정한 뒤 마지막에만 여는 새 질문입니다.

| 결과 이름(label) | 지침 | 질문 묶음(split) | 응답 수 | 확인할 것 |
|---|---|---|---|---|
| `baseline` | V1 | `dev` 6문항 | 18 | 바꾸기 전 답변 |
| `improved` | V2 | 같은 `dev` 6문항 | 18 | 지침을 바꾼 전후 차이 |
| `holdout` | 고정한 V2 | 새 `holdout` 4문항 | 12 | 새 질문에서도 통하는지 |

**지금은 첫 행 `baseline`만 실행합니다.** 7단계에서 `improved`, 8단계에서 `holdout`을 실행해 **18 + 18 + 12 = 48응답**을 모읍니다. 준비 확인용 호출과 채점 모델(judge)의 점수는 이 수에 더하지 않습니다. `improved`는 이름일 뿐 개선 판정이 아니며, dev와 holdout은 서로 다른 질문이라 전후 비교하지 않습니다.

**응답을 만드는 명령과 채점하는 명령은 다릅니다.** 아래 두 종류의 검사는 서로 대신할 수 없습니다.

| 명령 | 하는 일 | 확인하는 것 |
|---|---|---|
| `collect` | 에이전트의 **새 응답 18개**를 저장하고 Python 업무 검사를 실행 | 판단값·금액·인용이 정해진 규칙과 맞는가 |
| `evaluate` | **저장된 18개 응답**을 judge로 채점. 에이전트 응답을 새로 만들지 않음 | 근거에 맞는가(`groundedness`), 질문에 관련 있는가(`relevance`) |

세부 입력은 [평가기별 설명](#무엇을-평가하나요)에서 볼 수 있습니다.

### 5-1. Judge 확인

**터미널 A:** 채점 모델(judge)이 근거 있는 답과 틀린 답을 구분하는지 예제 두 개로 점검합니다. 이것이 calibration이며, 본평가 48응답에는 포함하지 않습니다. 출력 없이 1분쯤 기다릴 수 있습니다.

```bash
python scripts/workshop.py calibrate
```

**완료 확인:** 평가 완료 줄과 URL 뒤 마지막 줄이 `Judge calibration passed; ...`입니다.

**다르면:** [calibration부터 복구](docs/troubleshooting.ko.md#calibration)합니다.

<a id="baseline-collection"></a>

### 5-2. Baseline 18응답 수집

**터미널 A:** `--split dev`는 6문항 묶음을 고르고, `--label baseline`은 결과 폴더 이름을 정합니다. 준비 점검 JSON이 먼저 길게 나온 뒤 `01/18 ...` 줄이 하나씩 늘어납니다(보통 1–3분).

```bash
python scripts/workshop.py collect --split dev --label baseline
```

**완료 확인:** 진행 표시가 오류 없이 `18/18`에 도달하고 `Session ... retained ...` 줄로 끝납니다. `business=False`는 검토할 결과이지 명령 오류가 아닙니다.

**다르면:** [수집 복구](docs/troubleshooting.ko.md#collection-retry)를 따릅니다.

<a id="baseline-evaluation"></a>

### 5-3. 저장된 응답 평가

**터미널 A:** 수집 복구에서 돌아왔다면 `--label` 뒤에 [실제 V1 label](docs/troubleshooting.ko.md#run-values)을 씁니다. Foundry가 채점하는 동안 1–3분쯤 출력이 없을 수 있습니다.

```bash
python scripts/workshop.py evaluate --label baseline
```

**완료 확인:** `Foundry evaluation completed: ... (18 rows)`와 그 아래 report URL. 점수가 낮아도 유효한 결과입니다.

**다르면:** [평가 복구](docs/troubleshooting.ko.md#evaluation-retry)를 따릅니다. 수집은 반복하지 않습니다.

<a id="baseline-report"></a>

### 5-4. 평가 보고서 열기

**포털:** `evaluate`가 출력한 report URL을 복사해 브라우저에서 엽니다.

**완료 확인:** **Status**가 **Completed**이고, **Overall metric results**의 groundedness·relevance 아래 분모가 **18**(예: `18 / 18`, `15 / 18`)입니다. 아래 표는 한 페이지에 10행씩 보이므로 **Next**로 넘깁니다.

**다르면:** 에이전트의 Evaluation 탭이 아니라 프로젝트 전체의 **Evaluations** 목록에서 찾고, [포털 화면 차이](docs/troubleshooting.ko.md#portal-differs)를 봅니다.

<details>
<summary>예시 화면: baseline 평가 보고서(내 이름은 다름)</summary>

![실제 baseline 평가](docs/assets/live-ko-20260923b/screenshots/S5-P01-baseline-report-after.webp)

</details>

<a id="무엇을-평가하나요"></a>

<details>
<summary>참고: 질문 묶음과 평가기 입력</summary>

- `data/dev.jsonl`은 **현행 한도, 사전 승인, 과거 규정, 정책 밖 질문, 금지 항목, 규정 무시 요청**을 다룹니다.
- 질문 묶음과 결과 이름은 [이 단계의 평가 계획표](#evaluation-runs)를 그대로 사용합니다.
- Judge인 `gpt-5.4-mini`는 후보가 아니며, calibration 예제 2건은 48응답에 포함하지 않습니다.
- groundedness(근거성)·relevance(관련성)는 **5점 중 4점 이상**이면 통과입니다. `compare`·`summary`는 저장된 결과만 읽으며 모델을 호출하지 않습니다.
- Foundry의 groundedness·relevance 평가기는 답변 텍스트만 보고 `decision`·`citations` 필드는 받지 않으므로, **높은 groundedness만으로 판단이나 인용 ID가 맞았다고 볼 수 없습니다**([평가기별 입력](docs/validation.ko.md#business-checks)).
- 9단계 게이트(실습의 품질 통과 기준)는 업무 검사로 판단하고, Foundry 점수는 별도 품질 신호로 봅니다.

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

**완료 확인:** 오류 없이 긴 비교 JSON이 나오고 끝에 `comparison_notes`가 있습니다. JSON 안 `baseline → models`에 `sol`·`luna`·`astra`가 있습니다.

**다르면:** 5단계 수집·평가가 완료됐는지 확인하고 [실패한 명령만 복구](docs/troubleshooting.ko.md#resume)합니다.

<a id="baseline-traces"></a>

**터미널 A — trace 확인:** 긴 KQL 쿼리가 먼저 나오고, 그 아래에 결과 JSON이 나옵니다.

```bash
python scripts/workshop.py monitor --label baseline
```

**완료 확인:** 오류 없이 끝나고 결과 JSON에 `complete: true`, `expected_trace_count: 18`, `observed_trace_count: 18`이 있습니다.

**다르면:** `Telemetry is incomplete`이면 trace가 아직 반영 중일 수 있습니다. 2–3분 뒤 이 명령만 다시 실행하고, 계속되면 [모니터링 복구](docs/troubleshooting.ko.md#telemetry)를 따릅니다. 수집은 반복하지 않습니다.

**터미널 A — 검토할 행 찾기:**

```bash
python scripts/workshop.py summary --labels baseline
```

**완료 확인:** 모델별 요약 표와 `baseline business-check failures:` 줄이 나옵니다. 그 줄에는 쉼표로 구분된 row ID 목록이나 `none`이 있습니다. 요약은 저장된 결과를 읽을 뿐, 다시 평가하지 않습니다.

**다르면:** 오류에 나온 파일·label을 확인하고 `summary`만 다시 실행합니다.

<a id="review-case"></a>

### 6-2. 한 사례를 골라 원인 설명

**고르기:** 6-1의 `baseline business-check failures:` 뒤 **첫 `row_id`**(예: `baseline-luna-D01`)를 괄호 앞까지 복사합니다. 괄호 안은 실패한 검사입니다. `none`이면 `baseline-sol-D01`을 골라 **통과한 이유**를 검토합니다.

**터미널 A — 한 행 보기:** 복사한 `row_id`를 붙여넣습니다. 저장된 응답과 고정 정답을 나란히 보여 주며, 파일을 바꾸거나 모델을 호출하지 않습니다.

```bash
read -r -p "검토할 row_id: " ROW_ID &&
python scripts/workshop.py show --label baseline --row-id "$ROW_ID"
```

**완료 확인:** JSON에 `case_id`, `trace_id`, `saved_response`(저장된 응답), `business_checks`(다섯 업무 검사), `fixed_reference`(`data/dev.jsonl`의 고정 정답)가 있습니다. `row_id`와 `trace_id`를 메모합니다.

**다르면:** `Unknown row ID`이면 괄호·쉼표 없이 `baseline-`으로 시작하는 ID만 다시 붙여넣습니다.

**먼저 터미널 A에서 질문(`query`)을 읽습니다.** `saved_response` → `answer`를 `fixed_reference` → `ground_truth`와 비교한 뒤, 아래 표로 `business_checks`의 각 `false`를 설명합니다. `saved_response`는 에이전트가 한 답, `fixed_reference`는 미리 정해 둔 정답입니다.

| `business_checks`의 검사 | 같은 출력에서 대조할 값 |
|---|---|
| `decision` | `saved_response` → `decision`이 `fixed_reference` → `expected_decision`과 같아야 함([판단값의 뜻](docs/reference.ko.md#decision-values)) |
| `required_numbers` | `saved_response` → `answer`에 `fixed_reference` → `required_numbers`의 금액이 모두 있어야 함 |
| `citations_retrieved` | `saved_response` → `citations`의 모든 ID가 `saved_response` → `source_ids`에 있어야 함 |
| `citations_relevant` | 인용한 모든 ID가 `fixed_reference` → `allowed_citations`에도 있어야 함 |
| `citation_present` | `fixed_reference` → `citation_required`가 `true`이면 `citations`가 비어 있으면 안 됨. `false`이면 `[]`도 허용 |

문서를 찾은 것(`source_ids`)과 인용한 것(`citations`)은 다릅니다. 인용이 비면 “모든 ID”를 확인하는 두 검사는 통과해도 `citation_present`는 실패할 수 있습니다. 다섯 검사가 모두 `true`라면 통과한 이유를 설명합니다. JSON 전체를 해석할 필요는 없습니다.

**이어서 포털에서 같은 요청의 기록을 확인합니다.** `row_id`는 응답 이름이고, `trace_id`는 포털에서 찾을 실행 기록 ID입니다.

1. 왼쪽 **Agents** → 내 에이전트 → **Traces → Trace view**를 엽니다. 표 위 왼쪽 검색창에 전체 `trace_id`를 붙여넣고, 검색된 행의 **Trace ID** 링크를 누릅니다. 보이지 않으면 **Date range → 7D**로 넓힙니다.
2. 열린 창의 **Graph view**에서 `foundry_iq.retrieve`(검색)와 `chat`으로 시작하는 상자(모델 호출)를 열어 **이름과 실행 상태**를 확인합니다. 각 상자가 작업 하나의 기록인 **span**입니다. 메모에 `검색 span=이름/상태; 모델 span=이름/상태`를 덧붙입니다. 내부 JSON 전체를 해석할 필요는 없습니다. **Success**는 실행 성공일 뿐 답변 품질이나 원인을 증명하지 않으므로, 원인 설명은 앞서 `show`로 대조한 근거를 사용합니다.

**그다음 한 줄로 메모합니다:** `row_id=...; trace_id=...; 관찰: ...; 근거: ...; 바꿀 점: ...`. `관찰`에는 무엇이 맞거나 틀렸는지, `근거`에는 위에서 대조한 필드·문서 ID, `바꿀 점`에는 필요한 지침을 적습니다. 통과한 사례라면 **V2에서도 유지할 동작**을 적습니다([통과 사례](docs/troubleshooting.ko.md#no-failures), [원인 구분 예시](#실제-예시-금액은-맞는데-왜-실패했나요)).

**완료 확인:** 포털 창 위쪽 `ID:`가 내 `trace_id`와 같고, 두 span의 이름·상태와 `row_id=...; trace_id=...; 관찰: ...; 근거: ...; 바꿀 점(또는 유지할 동작): ...` 메모가 있습니다.

**다르면:** trace가 보이지 않으면 기간을 넓히고 전체 `trace_id`로 다시 찾습니다([포털 화면 차이](docs/troubleshooting.ko.md#portal-differs)). 필요한 span이 없으면 확인 완료로 기록하지 말고 [trace 복구](docs/troubleshooting.ko.md#telemetry)를 따릅니다. 파일은 수정하지 않습니다.

**예시 화면:** `foundry_iq.retrieve`와 `chat` span이 보이는 **Graph view**(내 ID·이름은 다름)

![실제 요청의 span graph](docs/assets/live-ko-20260923b/screenshots/S6-P01-trace-after.webp)

<details>
<summary>참고: 원본 파일과 다섯 업무 검사</summary>

- `show`는 `src/agent/.foundry/results/baseline/responses.jsonl`(저장된 응답)과 `data/dev.jsonl`(고정 정답)을 읽습니다. `.jsonl`은 한 줄에 JSON 객체 하나를 담은 파일입니다.
- `false`인 검사는 [다섯 업무 검사](docs/validation.ko.md#business-checks) 중 하나입니다. 올바른 `decision`([판단값](docs/reference.ko.md#decision-values)), 필수 금액 모두 포함, 모든 인용이 검색 문서에 있음, 모든 인용이 허용 목록에 있음, 필요한 인용의 존재입니다.

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

**다르면:** `already exists`이면 이 행의 검토 기록이 이미 있습니다. [복구 안내](docs/troubleshooting.ko.md#resume)의 `feedback` 행대로 확인하고 덮어쓰지 않습니다.

<a id="read-review"></a>

**터미널 A — 저장된 기록 확인:** 같은 터미널에서 방금 저장한 파일을 읽기 좋게 출력합니다. 파일은 수정하지 않습니다. **9-3에서 왔다면 위 `feedback`은 실행하지 않습니다.** `ROW_ID`를 잃었다면 편집기에서 `src/agent/.foundry/datasets/`의 기존 `regression-*.jsonl`을 열어 아래 필드를 읽습니다.

```bash
python -m json.tool --no-ensure-ascii "src/agent/.foundry/datasets/regression-$ROW_ID.jsonl"
```

**완료 확인:** `lineage → source_row_id`·`source_trace_id`·`review_reason`이 실제 검토한 행·trace·이유와 같고, 맨 위 `ground_truth`가 6-2 `fixed_reference`의 `ground_truth`와 같습니다(모델 답변이 아님).

**다르면:** `No such file`이면 새 터미널이라 `ROW_ID`가 비었을 수 있으니 위 출력의 경로를 따옴표 안에 직접 붙여넣습니다. 검토하지 않은 행이나 맞지 않는 이유가 저장됐다면 **V2 수집 전에 멈추고 [검토 기록 확인](docs/troubleshooting.ko.md#review-recovery)**을 따릅니다. 올바른 행을 추가 저장해도 오저장 기록은 제외되지 않습니다.

<a id="실제-예시-금액은-맞는데-왜-실패했나요"></a>

<details>
<summary>예시: 검색 문제와 지침 문제를 어떻게 구분하나요?</summary>

2026-09-23 기록된 예시 실행의 `baseline-sol-D01`(`gpt-6-sol`)은 **170,000원 숙박비가 180,000원 한도 이내**라는 답과 `allowed` 판단을 맞혔습니다.
하지만 `citations`에 문서 키 `TRAVEL-2026` 대신 **`"현행 국내 출장비 규정"`이라는 제목**을 넣었습니다.

| 확인 항목 | 실제 관찰 | 원인 판단 |
|---|---|---|
| 답변·판단·금액 | 맞음 | 모든 답변이 사실상 틀린 사례는 아님 |
| 검색 `source_ids` | `TRAVEL-2026`이 실제로 있음 | 검색 누락을 원인으로 분류하지 않음 |
| `citations_retrieved`, `citations_relevant` | 둘 다 `false` | 검색 문서 키와 인용 값이 일치하지 않음 |
| V1 지침 | “내부 문서 식별자는 사용자에게 표시하지 마세요” | 업무 검사와 충돌하는 지침을 개선 대상으로 선택 |

이 설명을 쓰기 전에 내 행도 같은 상황인지 먼저 확인합니다. `feedback`은 이 사례의 **고정 dev 정답과 원래 trace**를 회귀 데이터로 연결합니다.
모델의 답을 새 정답으로 복사하거나 모델 가중치를 학습시키는 명령이 아닙니다. V2 수집기는 이 데이터를 실제로 읽어 같은 사례를 다시 확인합니다.

</details>

**다음:** [7. V2로 바꾸고 같은 dev 다시 평가하기](#lab-e)

<a id="lab-e"></a>
<a id="9-실습-e--개선하고-같은-조건으로-다시-평가"></a>
<a id="7-v2로-바꾸고-같은-dev-다시-평가하기--실습-e"></a>

## 7. V2로 바꾸고 같은 dev 다시 평가하기

**목표:** 제공된 V2 지침을 새 버전으로 배포하고, 모델·데이터·평가 기준은 그대로 둔 채 같은 dev 6문항으로 평가합니다.

<a id="v2에서는-무엇을-바꾸나요"></a>

### 7-1. 제공된 V2 검토

**편집기 — V1/V2 차이 확인:** `src/agent/prompts/v1.txt`와 `src/agent/prompts/v2.txt`를 열고, 6-2의 **바꿀 점 또는 유지할 동작**과 연결되는 행을 아래 표에서 고릅니다. 두 파일은 수정하지 않습니다. V2는 제공된 후보입니다.

| V1 약점 | 제공된 V2 지침 |
|---|---|
| 문서 ID를 숨김 | 실제 사용한 **원본 문서 ID**를 인용 |
| 날짜·문서 상태 기준이 모호함 | 출장일에 유효한 정책을 적용하고 `draft`는 제외 |
| 승인 필요와 금지를 섞음 | 다섯 판단값의 뜻을 정하고 승인 사실을 만들지 않음 |
| 근거가 부족할 때의 처리가 없음 | `not_covered` 또는 `needs_info`를 쓰고 일반 상식으로 규정을 채우지 않음 |
| 검색 문서 안의 지시를 따를 수 있음 | 검색 문서는 **지시가 아닌 근거**로 보고 규정 무시 요청은 거부 |

**완료 확인:** 내 검토와 연결되는 V2 지침과 V1과의 차이, 또는 `직접 대응하는 V2 지침 없음`을 메모했습니다. 통과한 사례라면 V2에서도 지켜야 할 규칙을 연결합니다.

**다르면:** 직접 연결되는 지침이 없으면 `직접 대응하는 V2 지침 없음`으로 메모하고 진행합니다. 억지로 연결하거나 제공된 V2가 내 사례를 개선한다고 미리 단정하지 않습니다.

<a id="candidate-deploy"></a>

### 7-2. V2 배포 후 새 버전 확인

**터미널 A — V2 선택 후 배포:** 4-1처럼 1–3분 걸립니다.

```bash
python scripts/workshop.py set-prompt v2 &&
azd deploy --no-prompt
```

**완료 확인:** `Selected v2; ...`에 이어 `SUCCESS: Your application was deployed ...`가 나옵니다.

**다르면:** `Selected v2; ...`가 없으면 [설정 오류](docs/troubleshooting.ko.md#symptoms)를, 그 뒤 배포가 실패했다면 [배포 상태 확인](docs/troubleshooting.ko.md#deployment-recovery)을 따릅니다. 성공한 `set-prompt`까지 반복하지 않습니다.

<a id="candidate-smoke"></a>

**터미널 A — 새 버전 확인:** 출력된 `agent_version`을 메모에 `V2 버전: N`으로 적습니다.

```bash
python scripts/workshop.py smoke
```

**완료 확인:** `prompt_version: v2`와, 4-3과 **다른 숫자 `agent_version`**.

**다르면:** `Hosted prompt does not match` 오류가 나거나 `agent_version`이 4-3과 같으면 V2가 배포되지 않은 것입니다. `.env`에 `LAB_PROMPT_VERSION=v2`가 있는지 확인하고 위 V2 선택·배포 블록을 **한 번만** 다시 실행한 뒤 이 확인을 반복합니다. 그 밖의 호출 오류는 [해당 명령만 복구](docs/troubleshooting.ko.md#resume)합니다.

<a id="candidate-collection"></a>

### 7-3. 같은 dev 수집·평가

**수집 복구를 거쳤다면:** [실행값 메모](docs/troubleshooting.ko.md#run-values)의 실제 label을 사용합니다. 완료한 baseline의 `manifest.json`에서 `concurrency`가 `2`이면 아래 수집 명령 끝에 **`--concurrency 2`**를 붙입니다. V2 dev·holdout 모두 baseline과 같아야 합니다.

**터미널 A — 수집:** 5-2처럼 준비 점검 JSON 뒤에 `01/18 ...` 줄이 늘어납니다(보통 1–3분).

```bash
python scripts/workshop.py collect --split dev --label improved
```

**완료 확인:** 진행 표시가 오류 없이 `18/18`에 도달합니다.

**다르면:** [수집 복구](docs/troubleshooting.ko.md#collection-retry)를 따릅니다.

<a id="candidate-evaluation"></a>

**터미널 A — 평가:** 수집 복구에서 돌아왔다면 `--label` 뒤에 [실제 V2 dev label](docs/troubleshooting.ko.md#run-values)을 씁니다. 5-3처럼 1–3분쯤 출력이 없을 수 있습니다.

```bash
python scripts/workshop.py evaluate --label improved
```

**완료 확인:** `Foundry evaluation completed: ... (18 rows)`와 report URL.

**다르면:** [평가 복구](docs/troubleshooting.ko.md#evaluation-retry)를 따릅니다.

<a id="candidate-comparison"></a>

**터미널 A — 비교 저장:** 복구했다면 두 label을 [실행값 메모](docs/troubleshooting.ko.md#run-values)와 대조합니다. 이후 `summary`·`show`에서도 같은 값을 씁니다.

```bash
python scripts/workshop.py compare --labels baseline improved
```

**완료 확인:** 오류 없이 긴 비교 JSON이 나오고, JSON 안에 `baseline`과 `improved`, 끝에 `comparison_notes`가 있습니다.

**다르면:** 오류에 나온 label과 7-3의 평가 완료를 확인하고 [실패한 명령만 복구](docs/troubleshooting.ko.md#resume)합니다.

<a id="compare-results"></a>

### 7-4. 내 전후 결과 비교

**터미널 A:** 저장된 결과를 읽기만 하는 요약을 출력합니다. 나온 결과를 그대로 두고, 기준을 낮추거나 모델을 바꾸거나 V2를 자동 채택하지 않습니다.

```bash
python scripts/workshop.py summary --labels baseline improved
```

**완료 확인:** 출력에 아래 세 부분이 차례로 나오며, 이를 메모에 복사합니다.

1. `Reviewed case ...` 줄: `source trace carried: yes`(개선이 아니라 출처 연결)와 V2 결과 `business passed` 또는 `business failed (...)`
2. `sol`·`luna`·`astra`의 V1 `->` V2 표([열의 뜻](#metric-fields)). V2에서 늘어난 토큰·지연은 9-3의 남은 한계에 적도록 표시합니다.
3. `improved business-check failures:`와 `improved Foundry-score failures:`: row ID 또는 `none`

**다르면:** 파일·label이 없다는 오류이면 7-3의 평가가 끝났는지 확인한 뒤 `compare`와 `summary`만 다시 실행합니다. `Reviewed case` 줄이 없거나 `source trace carried: no`이면 V2 수집이 6-3의 검토 기록을 읽지 못한 것입니다(보통 6-3 전에 7-3을 실행한 경우). 6-3을 아직 안 했다면 먼저 하고, [V2 dev 수집 복구](docs/troubleshooting.ko.md#collection-retry-improved)로 `improved-retry`를 새로 수집해 이후 `improved` 대신 씁니다. 기존 결과는 지우지 않습니다.

<a id="metric-fields"></a>
<a id="실제-실행에서는-무엇이-좋아졌나요"></a>

**표 읽는 순서:** `->` 왼쪽이 V1, 오른쪽이 V2입니다. 먼저 **업무 통과**, 다음 **judge 통과**, 마지막 **토큰·시간의 증가 여부**를 봅니다. 한 열만 좋아졌다고 전체가 개선됐다고 결론 내리지 않습니다.

| 열 | 읽는 법 |
|---|---|
| `business` | 다섯 업무 검사를 **모두** 통과한 응답 수 / 전체 수. `5/6`이면 6개 중 5개 통과 |
| `required citations` | 인용이 필요한 응답 중 유효하게 인용한 수 / 인용이 필요한 수 |
| `groundedness`, `relevance` | 각각 근거성·관련성에서 **5점 중 4점 이상을 받은 응답 수 / 전체 수**. `5/6`은 점수가 아니라 통과 건수 |
| `tokens in/out` | 모델이 읽은 입력 / 만든 출력의 양(토큰). 해당 모델의 **dev 6응답 합계**이며, Azure 청구액이 아님 |
| `p50/p95 s` | 검색 + 모델 처리 시간(**초**). 6응답을 빠른 순으로 놓으면 p50은 세 번째, p95는 마지막 시간. 작을수록 빠름 |

**메모의 해석:** `업무 통과는 늘어남/같음/줄어듦; judge 미통과는 ...; 토큰·시간은 ...`처럼 내 값으로 적습니다. 변화가 없거나 나빠졌어도 그대로 씁니다.

**터미널 A — 검토한 사례의 저장된 V2 답변 확인:** 위 `Reviewed case ...` 줄에서 **`->` 뒤, `:` 앞의 V2 row ID**를 복사합니다. V1 row가 6-3에서 검토한 행과 같은 줄을 고르며, 새 Playground 응답을 대신 쓰지 않습니다.

```bash
read -r -p "Reviewed case 줄의 V2 row_id: " V2_ROW_ID &&
python scripts/workshop.py show --label improved --row-id "$V2_ROW_ID"
```

**완료 확인:** `case_id`·`model_key`는 6-2의 사례와 같고 `trace_id`는 다릅니다. 원래 trace를 V2 증거로 복사한 것이 아니라 새 응답입니다. `saved_response`의 `answer`·`decision`·`citations`를 6-2 및 바뀌지 않은 `fixed_reference`와 비교합니다. V2 `row_id`와 실제 바뀐 점(또는 같음)을 메모하며, 업무 통과·실패가 그대로여도 답변은 대조합니다.

**다르면:** `Unknown row ID`이면 `:`과 뒤의 설명 없이 오른쪽 ID만 복사하고, 복구 label을 썼다면 그 실제 이름을 사용합니다. V1 출력을 잃었다면 [6-2의 저장된 행](#review-case)을 다시 엽니다. 수집·평가는 반복하지 않습니다.

<details>
<summary>참고: 집계 원본과 비교의 한계</summary>

요약은 `src/agent/.foundry/results/comparison.json`(`labels → baseline / improved → models`)과 label별 `evaluation-results.json`을 읽습니다. 집계 필드는 [결과 읽기](docs/validation.ko.md#read-your-results)를 참고합니다.

토큰에는 planner·judge 등이 빠지고, 응답 6개의 지연 통계는 운영 성능을 보장하지 않습니다([측정 범위](docs/validation.ko.md#tradeoffs)). 검색 근거도 실행마다 달라질 수 있으므로(`comparison_notes`) 이 표는 모델만의 순위가 아니라 **검색을 포함한 에이전트 전체** 비교입니다.

미통과 행은 [미통과 행 확인](docs/validation.ko.md#native-failures)에서 봅니다. 기록된 예시 실행은 [모델별 실제 결과](docs/validation.ko.md#measured-results)에 있으며 내 목표 점수가 아닙니다.

</details>

<a id="portal-comparison"></a>

<details>
<summary>선택, 7-4 뒤 시간이 남을 때만: 포털에서 V1과 V2 비교(추가 호출·비용 발생, 48응답에 포함하지 않음)</summary>

**내 에이전트 → Playground → Version 선택 상자 → Compare versions**를 엽니다. 왼쪽은 V1, 오른쪽은 V2의 실제 버전 번호로 맞춥니다(처음에는 같은 버전이 두 번 선택될 수 있음). 입력창 하나에 아래 dev 질문을 붙여넣습니다.

```json
{
  "query": "2026년 9월 10일 부산 출장에서 1박 숙박비 170000원은 규정상 가능한가요? 한도도 알려주세요.",
  "model_key": "sol",
  "case_id": "D01",
  "run_id": "portal-ko-comparison"
}
```

**Send는 한 번만** 누릅니다. 비교 화면이 양쪽 버전을 함께 호출합니다. 각 응답의 `language`, `prompt_version`, `citations`, 서로 다른 `trace_id`를 확인합니다. 추가 시연 호출이며 수집한 18 + 18응답을 대체하거나 통계에 더하지 않습니다.

**아래는 기록된 예시 화면입니다:** 왼쪽 V1은 문서 제목, 오른쪽 V2는 `TRAVEL-2026`을 인용했습니다. 내 응답의 판단·인용은 다를 수 있습니다. 실제 차이를 읽고, 예시와 맞추려고 다시 호출하지 않습니다.

![실제 V1/V2 응답 비교](docs/assets/live-ko-20260923b/screenshots/S7-P02-compare-citations-after.webp)

</details>

**다음:** [8. V2를 바꾸지 않고 holdout 평가하기](#lab-f)

<a id="lab-f"></a>
<a id="10-실습-f--holdout과-frontier-ecosystem-테스트"></a>
<a id="8-후보를-고정하고-holdout-평가하기--실습-f"></a>

## 8. V2를 바꾸지 않고 holdout 평가하기

**목표:** 바꾸지 않은 V2로 응답 12개(holdout 4문항 × 3모델)를 수집·평가합니다.

### 8-1. Holdout 응답 수집

**주의:** 7-2에서 배포한 V2를 바꾸지 않고 그대로 씁니다. 별도 `freeze` 명령은 없습니다. 7-2 이후 아래 작업을 했고 **그 변경의 복구를 아직 마치지 않았다면**, 수집 전에 [V2가 바뀌었을 때 복구](docs/troubleshooting.ko.md#v2-changed)를 따릅니다.

- `set-prompt` 또는 `azd deploy` 실행
- `.env` 또는 prompt 파일 수정

**복구를 마쳤다면:** **원래 V2 버전을 다시 확인했거나, 새 V2로 dev 수집·평가·7-4 확인을 마쳤고** 이후 변경이 없다면 복구를 반복하지 않습니다. 새 버전으로 진행했다면 그 번호를 메모의 V2 기준으로 삼습니다. 이미 holdout 기록이 있다면 복구 문서의 retry label을 쓰며, 8-2의 버전·해시 대조는 생략하지 않습니다.

<a id="holdout-collection"></a>

**수집 복구를 거쳤다면:** [실행값 메모](docs/troubleshooting.ko.md#run-values)의 실제 label을 사용합니다. 완료한 baseline의 `manifest.json`에서 `concurrency`가 `2`이면 아래 수집 명령 끝에 **`--concurrency 2`**를 붙입니다. `--split holdout`은 바꾸지 않습니다.

**터미널 A:** 준비 점검 JSON 뒤에 `01/12 ...` 줄이 늘어납니다(보통 1–3분).

```bash
python scripts/workshop.py collect --split holdout --label holdout
```

**완료 확인:** 진행 표시가 오류 없이 `12/12`에 도달합니다.

**다르면:** `Hosted prompt does not match` 오류이면 [V2가 바뀌었을 때 복구](docs/troubleshooting.ko.md#v2-changed)를, 그 밖의 오류는 [수집 복구](docs/troubleshooting.ko.md#collection-retry)를 따릅니다.

<a id="holdout-evaluation"></a>

### 8-2. Holdout 평가와 V2 고정 확인

**터미널 A — 평가:** 수집 복구에서 돌아왔다면 `--label` 뒤에 [실제 holdout label](docs/troubleshooting.ko.md#run-values)을 씁니다. 1–3분쯤 출력이 없을 수 있습니다.

```bash
python scripts/workshop.py evaluate --label holdout
```

**완료 확인:** `Foundry evaluation completed: ... (12 rows)`와 report URL.

**다르면:** [평가 복구](docs/troubleshooting.ko.md#evaluation-retry)를 따릅니다.

<a id="holdout-comparison"></a>

**터미널 A — 비교 저장:** 복구했다면 세 label을 [실행값 메모](docs/troubleshooting.ko.md#run-values)와 대조합니다. 이후 출력 설명의 `baseline`·`improved`·`holdout`도 실제 label로 읽습니다.

```bash
python scripts/workshop.py compare --labels baseline improved holdout
```

**완료 확인:** 오류 없이 긴 비교 JSON이 나오고 끝에 `comparison_notes`가 있습니다.

**다르면:** 오류에 나온 label과 위 평가 완료를 확인하고 [실패한 명령만 복구](docs/troubleshooting.ko.md#resume)합니다.

**터미널 A — 고정한 V2인지 확인:** 방금 저장한 비교 파일에서 label별 에이전트 버전과 지침 해시(내용을 식별하는 값, 앞 12자리)만 한 줄씩 출력합니다.

```bash
python -c 'import json; labels = json.load(open("src/agent/.foundry/results/comparison.json"))["labels"]; [print(name, "agent_version=" + str(item["agent_version"]), "prompt_hash=" + item["prompt_hash"][:12]) for name, item in labels.items()]'
```

**완료 확인:** `improved`와 `holdout` 줄의 `agent_version`·`prompt_hash`가 같고, 그 `agent_version`이 메모한 **V2 버전**입니다. `baseline` 줄은 V1이라 다릅니다.

**다르면:** 값이 다르면 **비교 조건이 달라진 것**입니다. 재평가·파일 편집으로 맞추지 말고 [V2가 바뀌었을 때 복구](docs/troubleshooting.ko.md#v2-changed)를 따릅니다.

<a id="holdout-results"></a>

### 8-3. Holdout 결과 읽기

**터미널 A:** 8-2에서 V2가 고정된 것을 확인한 뒤, 저장된 holdout의 읽기 전용 요약을 출력합니다(모델 호출 없음). holdout은 dev와 다른 질문이므로 그 통과율로 V1 → V2 개선을 주장하지 않습니다.

```bash
python scripts/workshop.py summary --labels holdout
```

**완료 확인:** `sol`·`luna`·`astra` 표의 `business`·`groundedness`·`relevance`가 각각 **`.../4`**로 나오고, 아래 두 목록에 row ID 또는 `none`이 있습니다. 두 목록은 메모에 따로 복사합니다(업무 검사가 `4/4`여도 Foundry 점수는 미통과일 수 있음).

- `holdout business-check failures:`
- `holdout Foundry-score failures:`

**다르면:** 비교 파일·label이 없으면 8-2의 `compare`부터 이어갑니다. 평가 결과가 `n/a`이거나 Foundry 미통과 목록이 없으면 [평가 복구](docs/troubleshooting.ko.md#evaluation-retry)를 따릅니다. 미통과 행은 [미통과 행 확인](docs/validation.ko.md#native-failures)에서 봅니다.

### 8-4. Holdout 보고서 열기

**포털:** dev 보고서가 아니라 이번 holdout `evaluate`가 출력한 report URL을 엽니다.

**완료 확인:** **Status**가 **Completed**이고, **Overall metric results**의 분모가 **12**(예: `12 / 12`)입니다.

**다르면:** [포털 화면 차이](docs/troubleshooting.ko.md#portal-differs)를 봅니다.

**주의:** 이 결과를 보고 prompt를 고친 뒤 같은 holdout을 “미사용 검증”으로 다시 제출하지 않습니다. 이 4문항은 교육용이며 독립 벤치마크가 아닙니다.

<details>
<summary>예시 화면: holdout 평가 보고서(내 이름은 다름)</summary>

![실제 holdout 평가](docs/assets/live-ko-20260923b/screenshots/S8-P01-holdout-report-after.webp)

</details>

**다음:** [9. 운영 지표와 전체 증거 확인하기](#lab-g)

<a id="lab-g"></a>
<a id="11-실습-g--trace와-monitor의-차이"></a>
<a id="9-운영-신호와-전체-증거-확인하기--실습-g"></a>

## 9. 운영 지표와 전체 증거 확인하기

**목표:** 전체 증거 검증 → 운영 대시보드 확인 → 최종 보고 순서로 마칩니다. 보고에 필요한 값을 모두 확인한 뒤 보고를 한 번에 작성합니다.

### 9-1. 전체 응답·평가·trace 검증

<a id="candidate-traces"></a>

**터미널 A — V2 dev trace:** 복구했다면 `--label` 뒤에 [실제 V2 dev label](docs/troubleshooting.ko.md#run-values)을 씁니다.

```bash
python scripts/workshop.py monitor --label improved
```

**완료 확인:** 오류 없이 끝나고 결과 JSON에 `complete: true`, `expected_trace_count: 18`, `observed_trace_count: 18`이 있습니다.

**다르면:** `monitor`는 최근 2시간만 봅니다. V2 수집 뒤 2시간이 지났다면 [조회 기간을 늘리고](docs/troubleshooting.ko.md#telemetry), 방금 수집했다면 2–3분 뒤 이 명령만 다시 실행합니다.

<a id="holdout-traces"></a>

**터미널 A — holdout trace:** 복구했다면 `--label` 뒤에 [실제 holdout label](docs/troubleshooting.ko.md#run-values)을 씁니다.

```bash
python scripts/workshop.py monitor --label holdout
```

**완료 확인:** 오류 없이 끝나고 결과 JSON에 `complete: true`, `expected_trace_count: 12`, `observed_trace_count: 12`가 있습니다.

**다르면:** `Telemetry is incomplete`이면 2–3분 뒤 이 명령만 다시 실행하고, 계속되면 같은 label의 [모니터링 복구](docs/troubleshooting.ko.md#telemetry)를 따릅니다.

**터미널 A — 전체 증거 검증:** [실행값 메모](docs/troubleshooting.ko.md#run-values)와 세 label **값**을 대조합니다. 복구했다면 값만 바꾸고 `--baseline`·`--candidate`·`--holdout` 옵션 이름은 그대로 둡니다. 긴 비교 JSON 뒤에 검증 결과 JSON이 나옵니다.

```bash
python scripts/workshop.py verify --baseline baseline --candidate improved --holdout holdout
```

**완료 확인:** 맨 아래 JSON에 `language: ko`, `component_execution_verified: true`, `primary_model_outputs: 48`, `distinct_verified_traces: 48`이 있습니다.

**다르면:** 오류 메시지가 가리키는 단계를 [실패한 단계 복구](docs/troubleshooting.ko.md#resume)에서 찾습니다. 증거 파일을 고치지 않습니다.

<details>
<summary>예시 화면: 전체 실행 증거 확인</summary>

![실제 응답·trace·평가·lineage 검증](docs/assets/live-ko-20260923b/screenshots/S9-03-verify-after.webp)

</details>

<a id="operational-dashboard"></a>
<a id="9-3-운영-대시보드-확인"></a>

### 9-2. 운영 대시보드 확인

**포털:** 왼쪽 **Agents** → 내 에이전트 → **Monitor** 탭 → **Overview**에서 기간을 **Last Day**로 둡니다.

**완료 확인:** **Agent runs**와 **Runs and token metrics** 그래프에 내 실행 시간대의 값이 있습니다. 메모에 **Agent runs** 범례의 상태별 수(예: `completed: 54`)와 `Total tokens`를 적습니다. `completed` 외의 상태도 이름·수를 그대로 적고, 없으면 `completed 외 상태 없음`으로 적습니다. 진행 중인 실행까지 오류로 세지 않습니다. smoke·포털 호출도 포함되므로 합계가 48과 달라도 됩니다.

**다르면:** 2–3분 뒤 새로 고칩니다. 이전 날짜에 실행했다면 **7D**로 넓히고, 계속 비어 있으면 [포털 화면 차이](docs/troubleshooting.ko.md#portal-differs)를 봅니다.

`Estimated cost: $0`도 무료라는 뜻은 아니므로 10단계 정리는 반드시 합니다.

<details>
<summary>예시 화면(포털이 다르게 보이면 열기): Foundry Monitor 대시보드</summary>

기록된 예시 실행에서는 48응답에 smoke·Playground 호출이 더해져 agent run이 54건이었습니다.

![실제 Foundry Monitor 대시보드](docs/assets/live-ko-20260923b/screenshots/S9-P01-monitor-after.webp)

</details>

<a id="completion-decision"></a>
<a id="9-2-보고할-내용-정하기"></a>
<a id="9-2-내-결과를-세-가지로-보고하기"></a>
<a id="finish"></a>
<a id="마무리-세-가지-보고"></a>

### 9-3. 내 결과를 세 가지로 보고하기

**터미널 A:** 9-1에서 저장한 증거 파일을 다시 출력합니다(다시 검증하지 않음). `candidate_quality_gates`에서 모델마다 `dev`·`holdout` 값을 메모로 옮깁니다. `dev=true`는 6응답 중 **5개 이상**이 업무 검사를 통과하고 필수 인용이 모두 유효하다는 뜻입니다. `holdout=true`는 4응답 **모두** 통과했다는 뜻입니다.

```bash
python -m json.tool --no-ensure-ascii src/agent/.foundry/results/verified-evidence.json
```

**완료 확인:** `candidate_quality_gates`에 `sol`·`luna`·`astra`의 `dev`·`holdout` 값 여섯 개가 있습니다. `false`도 기록할 정상 결과입니다.

**다르면:** 파일이 없으면 [9-1의 검증](#lab-g) 완료 여부를 확인합니다. 파일을 직접 만들거나 값을 채워 넣지 않습니다.

**편집기 — 메모를 보고서로 저장:** 지금까지 메모한 **같은 문서**를 아래 양식(명령 아님)으로 정리합니다. VS Code의 **File → Save As**에서 실습 폴더의 `src/agent/.foundry/results/workshop-report.txt`로 저장합니다. `...`를 남기지 않고 빈 목록은 `none`으로 적습니다. `production_release_approved=false`는 바꾸지 않습니다.

실제 label은 사용한 결과 폴더 이름이며, 동시성은 그 폴더의 `manifest.json` → `concurrency`에서 읽습니다. 복구하지 않았어도 이 값과 `복구 이력: none`을 적습니다.

```text
1. 검토(6-2의 한 줄): ...
   연결한 V2 지침(7-1): ...
2. 변화(7-4):
   V1 버전(4-3)=...; V2 버전(7-2)=...
   검토한 V2 row와 실제 답변·판단·인용의 변화(또는 같음): ...
   V1 -> V2 표: 여기에 표 붙여넣기
   해석(업무 통과·judge 미통과·토큰·시간): ...
   improved 미통과: 업무=...; Foundry=...
3. 판단(verified-evidence.json의 게이트):
   실제 label: V1 dev=...; V2 dev=...; V2 holdout=...
   수집 동시성(concurrency)=...
   복구 이력(없으면 none): ...
   holdout 사용 이력(최초 사용 또는 재사용과 그 사유): ...
   sol: dev=..., holdout=...
   luna: dev=..., holdout=...
   astra: dev=..., holdout=...
   holdout 미통과(8-3): 업무=...; Foundry=...
   Monitor(9-2): Agent runs 상태별 수=...; Total tokens=...
   남은 한계(토큰·지연 증가, completed 외 실행 상태 등): ...
   production_release_approved=false
```

**그대로 보고할 것:** `false`인 게이트, Foundry 점수 미통과, 나빠진 값도 유효한 결과입니다. 게이트 통과는 운영 승인이 아닙니다. V2 변경 복구로 holdout을 재사용했다면 **새로운 미사용 검증이 아님**을 적습니다. 버전·해시 일치만으로 최초 사용이 증명되지는 않습니다.

**완료 확인:** 보고서 파일을 저장했고, `...`가 남아 있지 않으며, 7-4의 표·실제 label·동시성·복구 및 holdout 사용 이력과 `production_release_approved=false`가 있습니다. 점수를 높이려고 재실행하지 않습니다.

**다르면:** 게이트 값이 없으면 9-1로 돌아갑니다. 메모가 빠졌다면 **저장된** [검토 기록](#read-review)·[dev 요약](#compare-results)·[holdout 요약](#holdout-results)을 읽어 채웁니다. 검토·수집·평가를 다시 실행하지 않습니다.

**다음:** 레벨 2·3을 추가하려면 정리 **전에** 아래 선택 항목을 엽니다. 추가하지 않으면 [10. 내 실습 자원만 정리하기](#cleanup)로 갑니다.

<a id="levels"></a>

<details>
<summary>선택: 시간이 더 있으면 정리 전에 레벨 2·3 추가</summary>

같은 폴더에서 진행합니다. **10단계 뒤에는 에이전트가 삭제되므로 추가 실습을 시작하지 않습니다.** 모델·judge 호출 비용이 추가됩니다.

| 선택 | 더하는 내용 | 추가 시간 | 경로 |
|---|---|---|---|
| 레벨 2 | 업무 규칙을 Foundry 평가기로 채점하고 실행 결과·실패 원인 비교 | 약 40분 | [레벨 2](docs/level-2.ko.md) → 10단계 |
| 레벨 2·3 | 생성 평가 기준, 모델·에이전트·trace 평가, 연속 평가, 릴리스 게이트 | 약 110분 | [레벨 2](docs/level-2.ko.md) → [레벨 3](docs/level-3.ko.md) → 10단계 |

</details>

<a id="cleanup"></a>
<a id="12-마무리와-비용-정리"></a>

## 10. 내 실습 자원만 정리하기

**목표:** 이 폴더가 만들어 소유한 객체를 지우고, 로컬 증거와 공유 서비스는 남깁니다. 개인 실습에서는 직접 만든 후보 모델 배포도 삭제 대상일 수 있습니다.

<a id="stop-early"></a>

<details>
<summary>중도 종료하거나 나중에 이어 하려면</summary>

| 선택 | 할 일 |
|---|---|
| 나중에 이어 하기 | 진행 중인 작업이 끝나면 같은 메모에 `마지막 완료 블록 / 다음 블록 / 실습 폴더`와 사용 중인 label을 저장합니다. 같은 폴더·설정·증거를 보존하고 [정상 중단 또는 오류에 맞게 재개](docs/troubleshooting.ko.md#resume)합니다. **터미널을 닫아도 Azure 자원 비용은 계속될 수 있습니다.** |
| 이번 실행 끝내기 | 진행 중인 수집·배포·평가가 끝났는지 확인하고, 완료한 단계·오류·현재 증거만 기존 메모에 저장합니다. 미완료 단계의 결과를 만들지 말고 아래 [10-1 삭제 계획](#cleanup-plan)부터 진행합니다. |

로컬 서버가 켜져 있다면 그 터미널에서 `Ctrl+C`로 종료합니다. 클라우드 작업 상태가 불명확하거나 배포·역할 부여 중 실패했다면, **생성된 객체가 소유권 계획에 모두 기록됐는지** 환경 소유자와 [정리 복구](docs/troubleshooting.ko.md#cleanup-recovery)에서 먼저 확인합니다. 기록 누락을 빈 계획으로 간주해 정리 완료로 보고하지 않습니다.

아직 환경 준비 중이라 이 폴더의 `cleanup`을 실행할 수 없다면 환경 소유자의 [전용 환경 종료](docs/environment.ko.md#final-cleanup)를 따릅니다. 공유 그룹은 삭제하지 않습니다. 1–9단계를 끝내지 않았다면 **실습 미완료**와 실제 정리 상태를 따로 기록합니다.

</details>

**주의:** 정리 전에 확인합니다.

- 실습을 완료하는 경로에서는 포털 확인을 모두 마칩니다. 중도 종료는 위 안내를 따릅니다. 정리하면 실행 중인 에이전트가 삭제됩니다.
- `azd down`이나 공유 resource group 삭제는 실행하지 않습니다.
- Search, 로그, 기반 서비스, 보조 모델은 이 단계 뒤에도 남아 비용이 계속 발생합니다. 수업이면 환경 소유자가 관리하고, **혼자 만든 환경이면 10-3 뒤 [리소스 그룹 삭제](docs/environment.ko.md#final-cleanup)로 멈춥니다.**

<a id="cleanup-plan"></a>

### 10-1. 삭제 계획만 확인

**터미널 A:**

```bash
python scripts/workshop.py cleanup --dry-run
```

**완료 확인:** 출력 JSON의 모든 대상이 이 폴더의 소유권 기록에 속합니다. 완료 경로에서는 `agent`가 내 `LAB_AGENT_NAME`이고 `search_objects`의 세 이름(`...-kb`, `...-source`, `...-policies`)에 모두 내 `LAB_PREFIX`가 들어 있습니다. **중도 종료는 실제 생성한 대상만 있어야 합니다.** 만들지 않은 에이전트의 `agent: null`이나 빈 목록은 정상이며, 생성한 대상이 계획에서 빠졌다면 삭제 전에 위 정리 복구로 확인합니다.

**대조 방법:** 편집기에서 `src/agent/.foundry/local-state.json`을 읽고, 출력 계획과 아래를 대조합니다. 파일을 고쳐 맞추지 않습니다.

| 계획 필드 | 소유권 기록 필드 |
|---|---|
| `agent` | `agent_owned`(미생성이면 둘 다 없음/`null`) |
| `search_objects` | `owned_search_paths`의 같은 경로들(순서는 달라도 됨) |
| `role_assignments` | `owned_roles`의 같은 전체 ID들 |
| `models` | `owned_models`의 같은 이름·ID·모델·버전 |

| 계획 필드 | 있어야 할 대상 |
|---|---|
| `agent`, `search_objects`, `role_assignments` | 내 `LAB_AGENT_NAME`, 내 `LAB_PREFIX` 지식 객체 3개, 이 폴더에서 만든 역할(긴 ID, 보통 2개). 공유 수업에서는 [공유 Search의 planner 역할](docs/instructor.ko.md#shared-search-access)이 목록에 없는지 소유자와 확인하며, 있으면 10-2 전에 멈춥니다. 본인 전용 개인 실습은 이 역할도 폴더 소유일 수 있습니다. |
| `models` | **공유 배포를 쓰는 참가자는 빈 목록입니다.** 개인 실습에서 `prepare-models`로 만든 후보만 포함될 수 있으며, 다른 사용자가 쓰지 않을 때만 삭제합니다 |
| `schedules`, `custom_evaluators`, `generated_datasets` | 레벨 2·3을 하지 않았다면 빈 목록. 했다면 이 폴더의 일정·평가기·생성 데이터셋만 포함 |
| `preserved` | 기존 Foundry 프로젝트·Search·App Insights·평가 증거(삭제하지 않음) |

기반 서비스와 보조 모델(planner/judge)은 보존합니다. `.env`에 모델 이름이 있다는 것만으로 소유권이 생기지는 않습니다. **확인한 JSON 출력을 기존 메모에 복사합니다.** `--dry-run`은 계획 파일을 저장하지 않으며, 기록 대조는 위의 공유 의존성 확인을 대신하지 않습니다.

**다르면:** 10-2를 실행하지 않고 [정리 복구](docs/troubleshooting.ko.md#cleanup-recovery)의 “소유권·대상이 다름” 행을 따릅니다. 아무것도 삭제하지 않습니다.

### 10-2. 검토한 계획만 실행

**터미널 A:**

```bash
python scripts/workshop.py cleanup --confirm
```

**완료 확인:** 출력이 `Owned workshop resources removed; shared infrastructure and evidence preserved.`로 끝납니다.

**다르면:** [정리 복구](docs/troubleshooting.ko.md#cleanup-recovery)를 따릅니다.

<a id="cleanup-check"></a>

### 10-3. 삭제 여부를 별도로 확인

**대조할 계획:** 편집기에서 `src/agent/.foundry/results/cleanup.json`의 `plan`을 엽니다. 10-2가 실제 사용한 계획이며, 10-1에서 메모한 대상과 같아야 합니다. 아래 개수는 이 `plan`과 대조합니다. 원래 계획을 얻으려고 삭제나 dry-run을 반복하지 않습니다.

**터미널 A:**

```bash
python scripts/workshop.py check-cleanup
```

**완료 확인:** 출력된 JSON(`src/agent/.foundry/results/cleanup-check.json`에도 저장)에 `temporary_hosted_agent_absent: true`, `existing_foundry_project_preserved: true`, `existing_search_service_preserved: true`가 있습니다. `*_absent` 숫자는 삭제를 확인한 개수이며, `temporary_search_objects_absent`·`temporary_role_assignments_absent`·`temporary_model_deployments_absent`가 10-1 계획의 `search_objects`·`role_assignments`·`models` 개수와 같습니다.

**다르면:** 이 확인만 실패했다면 [확인 명령부터 복구](docs/troubleshooting.ko.md#cleanup-recovery)합니다. 성공한 `cleanup --confirm`을 다시 실행하면 저장된 계획이 바뀌므로 반복하지 않습니다.

<details>
<summary>예시 화면: 정리 완료 확인</summary>

![실제 Azure 정리 재확인](docs/assets/live-ko-20260923b/screenshots/S10-03-check-after.webp)

</details>

**1–9단계도 마쳤다면 기본 실습 완료입니다.** [9-3의 보고](#finish), 삭제 확인 결과, 로컬 증거 파일을 보관합니다. 중도 종료라면 실습 미완료 상태와 현재 증거만 보관합니다. **혼자 만든 환경이라면** 더 쓰지 않을 때 [리소스 그룹 삭제](docs/environment.ko.md#final-cleanup)까지 해야 Search·로그 같은 기반 서비스 비용이 멈춥니다. 수업·공유 환경의 그룹은 삭제하지 않습니다.

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
| `src/agent/.foundry/results/workshop-report.txt` | 9-3에서 저장한 세 항목 보고 |
| `src/agent/.foundry/results/cleanup-check.json` | 삭제 확인 결과. 확인한 계획은 같은 폴더의 `cleanup.json` |

보고와 복구에 쓰므로 지우거나 예시 결과로 바꾸지 않습니다.

</details>

## 참고 문서

아래는 모두 선택 자료입니다. 10단계 실습은 여기서 끝납니다.

- **결과와 한계:** [평가 방법과 개선 결과](docs/validation.ko.md)
- **설계와 용어:** [Learning loop 배경](docs/reference.ko.md#background) · [용어 설명](docs/reference.ko.md#terms) · [설계·모델·공식 출처](docs/reference.ko.md)
- **레벨 2·3:** [Foundry 사용자 지정 평가기와 인사이트](docs/level-2.ko.md) · [생성 rubric·스트레스 테스트·red team·에이전트 직접 호출·trace·연속 평가·릴리스 게이트](docs/level-3.ko.md)
- **오류:** [문제 해결](docs/troubleshooting.ko.md)
- **강사·혼자 실습 준비:** [강사 준비](docs/instructor.ko.md) · [새 Azure 환경 생성](docs/environment.ko.md)
- **선택:** [Copilot CLI로 진행](docs/copilot.ko.md)

<a id="summary-video"></a>

## 선택: 15분 요약 영상

<details>
<summary>한국어 실습 요약 영상 — 15분 2초</summary>

[한국어 실습 요약 영상 (MP4, 17.5 MiB)](videos/foundry-evaluation-gpt6-ko-20260923b.mp4)

2026-09-23 한국어 재실행(`ko-20260923b`)을 본문 순서로 편집한 영상입니다. 영상과 본문이 다르면 본문을 따릅니다.

- 실제 CLI와 Foundry 포털을 Playwright headless로 녹화했습니다.
- 6-1·7-4·8-3의 `summary` 표는 녹화 뒤에 저장된 결과를 현재 읽기 전용 `summary` 명령으로 다시 읽어 렌더했고, 포털 V1/V2 비교는 본문처럼 7-4 뒤 선택 확인으로 옮겼습니다.
- 레벨 2·3 장은 같은 날 레벨 리허설에서 저장한 실제 CLI 출력을 렌더한 화면이며, red team 장은 현재 `red-team` 명령으로 다시 실행한 출력입니다.
- 소리는 없고, 대기 구간은 줄였으며, 로그인·MFA와 계정·구독 식별자는 제외했습니다.

| 단계 | 영상 위치 | 단계 | 영상 위치 |
|---|---|---|---|
| 1. 시작 준비 | 00:07 | 2. 지식 넣고 검색 | 01:07 |
| 3. 로컬 실행 | 02:08 | 4. Hosted Agent 배포 | 02:49 |
| 5. baseline 평가 | 04:18 | 6. 사례 검토 | 05:27 |
| 7. V2 평가 | 06:58 | 8. holdout 평가 | 09:51 |
| 9. 운영 신호·증거 | 11:02 | 레벨 2 | 12:26 |
| 레벨 3 | 12:48 | 10. 정리 | 13:34 |

영문 실행의 요약 영상은 [영문 가이드](README.md#summary-video)에 있습니다.

</details>
