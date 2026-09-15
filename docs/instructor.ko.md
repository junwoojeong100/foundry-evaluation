# 강사 준비: 120분 실습의 시작 조건

새 그룹부터 준비하는 실제 명령과 화면은 [새 Azure 환경 가이드](environment.ko.md)에 있다. [이번 재촬영의 실행 범위와 검증 한계](validation.ko.md)는 과거 검증과 구분한다.

이 문서는 참가자 120분에 포함하지 않는 **환경 준비**다. 빈 Azure 구독에서의 전체 소요 시간은 모델 접근 승인·할당량·권한 전파에 따라 달라진다.

## 참가자에게 전달할 것

참가자는 [README의 1–10단계](../README.md#start)만 따라간다. 녹화 제작이나 Azure 인프라 생성 절차를 참가자의 선행 과제로 섞지 않는다.

| 전달 항목 | 강사가 확인할 내용 |
|---|---|
| 실행 가능한 계정 | 참가자 계정의 조회·배포 권한. 실제 CLI 로그인은 참가자가 README 1-3에서 수행 |
| 조별 `.env` | `.env.example`의 모든 값을 채움. 암호·API key·token은 없음 |
| 준비된 서비스 | Foundry 프로젝트, Search, 연결된 App Insights, 네 후보와 별도 planner/judge |
| 고유한 이름 | 참가자가 아직 사용하지 않은 `LAB_PREFIX`, `LAB_AGENT_NAME` |
| 준비된 도구 | Python 3.13, Azure CLI, azd 확장, Bash 또는 WSL |
| 도움받을 담당자 | `grant-agent-access` 역할 부여·403·quota 오류를 처리할 담당자 |

**중요:** `.env`만 전달한 새 clone에는 로컬 azd 환경이 없다. 참가자는 README 1단계의 **`bind`를 자기 폴더에서 실행**한다. 강사 PC에서 바인딩했다는 이유로 이 단계를 생략하지 않는다.

## 리허설과 참가자 실행을 분리

리허설은 **별도 폴더와 별도 `LAB_PREFIX` / `LAB_AGENT_NAME`**으로 수행한다. 참가자의 접두사로 KB·source·index·agent를 미리 만들면, 새 참가자 폴더의 소유권 검사에서 덮어쓰기를 거부할 수 있다.

준비된 모델을 공유하는 경우 `.env`의 `MODEL_*_DEPLOYMENT`에는 그 **실제 배포 이름**을 유지한다. 바꾸는 것은 조별 지식 객체·agent 이름이며, 모델을 임의로 교체하지 않는다.
다른 사람의 `.azure`, `.foundry` 소유권 파일, 실행 결과나 인증 저장소를 복사해서 오류를 우회하지 않는다.

참가자의 `cleanup`은 **그 폴더에 생성 기록이 있는 대상만** 정리한다. 강사가 미리 준비한 모델·기반 서비스의 최종 비용과 정리는 강사가 따로 관리한다.

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

## 권한

| 주체 | 최소 업무 권한 | 범위 |
|---|---|---|
| 참가자 | Foundry User + 필요한 개발/배포 권한 | 실습 Foundry 프로젝트/계정 |
| 준비 담당자 | 모델 배포·Search schema 생성 권한 | 실습 리소스 |
| 문서 적재 담당자 | Search Service Contributor, Search Index Data Contributor | 실습 Search |
| Search managed identity | Cognitive Services User | planner 모델이 있는 Foundry 계정 |
| Hosted Agent identity | Search Index Data Reader | 실습 Search |
| Hosted Agent instance identity | Cognitive Services OpenAI User | 네 후보 모델이 있는 Foundry 계정 |
| 관측 담당자 | Log Analytics Reader 등 필요한 Logs 권한 | App Insights/연결 workspace |

Foundry 역할의 이전 이름인 Azure AI User 등이 UI에 남아 있을 수 있다. 역할의 이름만 보고 Owner를 일괄 부여하지 않는다. 기존 역할이 충분하면 추가하지 않는다.

이 실습은 조 전체가 볼 수 있는 합성 문서를 공유한다. 실제 다중 사용자 제품은 문서별 권한, tenant 격리, on-behalf-of/호출자 신원 전달을 별도로 구현해야 한다. Search 읽기 역할만으로 사용자별 문서 필터링이 자동 완성되지는 않는다.

최종 계정 endpoint 추론 경로는 agent에 프로젝트의 `Foundry User`나 Owner를 부여하지 않는다. 사용자/준비 담당자의 Foundry 역할과 agent identity의 두 데이터 접근 역할을 구분한다. 진단 중 시험한 추가 역할은 검증 환경 정리 시 함께 제거한다.

## 로컬 설치와 테스트

리허설용 저장소 루트에서 실행한다. **마지막에 `OK`가 나온 뒤에만** 아래 Azure 준비로 넘어간다.

```bash
python3.13 -m venv src/agent/.venv &&
source src/agent/.venv/bin/activate &&
python -m pip install -r requirements.txt &&
python -m unittest discover -s tests -v
```

프레임워크와 Foundry SDK의 버전 상한이 다를 수 있다. Agent Framework Foundry 1.11.0, core 1.16.0, OpenAI adapter 1.14.1, Azure AI Projects 2.3.0, Agent Server Invocations 1.1.0을 고정했다. 무조건 모든 패키지를 최신 버전으로 올리지 않는다. `requirements.lock.txt`는 검증 환경의 전체 의존성 스냅샷이다. 같은 Python 환경을 재현할 때 `python -m pip install -r requirements.lock.txt`를 사용할 수 있다.

## 설정과 안전한 준비

1. `.env.example`을 참고해 `.env`에 **실습 환경의 값**을 채운다. 기존 파일은 덮어쓰지 않는다.
2. 테스트가 `OK`인 같은 폴더에서 [README 1-3 로그인](../README.md#login)을 실행한다. 실습용 CLI 경로를 지정하고 두 CLI에 로그인한 뒤, 계정·tenant·구독·인증 상태를 대조한다. 다른 작업의 기본 CLI 구독은 바꾸지 않는다.
3. `python scripts/workshop.py preflight --allow-missing-models`로 환경과 네 모델의 지역별 지원·할당량을 읽기 전용 확인한다.
4. 모델이 없다면 `python scripts/workshop.py prepare-models`로 **고유 접두사**를 가진 네 배포만 만든다.
5. `python scripts/workshop.py preflight`를 다시 통과시킨다.
6. `prepare-iq`와 실제 retrieval을 실행한다.
7. azd를 아래 절차로 바인딩하고 로컬·원격 smoke test를 완료한다.
8. `python scripts/workshop.py calibrate`로 명시적으로 정의한 정답/오답 예제 2건을 Foundry에서 평가한다. 실제 네 모델 응답과 섞지 않는 judge 점검이며, groundedness가 근거 없는 금액을 구분하는지 확인한다.

평가가 `AppInsights connection is missing ResourceId metadata`로 실패하면 강사가 연결의 소유권과 범위를 먼저 확인한다. **공유 연결은 참가자가 직접 변경하지 않는다.** 수정이 허용된 실습 전용 연결에만 `python scripts/workshop.py repair-observability --confirm`으로 실제 Application Insights ARM ID 메타데이터를 추가한다. target/credential은 변경하지 않으며 보완 기록은 cleanup 후에도 유지된다. 이후 `calibrate --retry-failed`로 실패 run을 보존한 채 새 run을 만든다.

모델은 `GlobalStandard` 사용량 기반 배포를 사용한다. PTU를 예약하거나 할당량 증설을 자동 신청하지 않는다. 실제 모델/SKU/할당량 검사를 통과하지 못하면 강사가 먼저 해결한다.

## azd 초기화

이 저장소에는 실습 전용 `azure.yaml`과 소스가 제공된다. 기존 프로젝트를 사용할 때는 **기존 프로젝트의 ARM ID**와 실제 보조 모델 deployment name을 사용한다.

```bash
python scripts/workshop.py bind
```

`azure.yaml`이 없을 때는 공식 `azd ai agent init --src ... --project-id ...` 경로를 사용한다. 제공된 `azure.yaml`이 있으면 다시 init하여 `-2` agent를 만드는 대신 로컬 azd environment를 만들거나 재사용한다. service key와 agent name을 조별 이름으로 맞춘다. 구독·프로젝트 충돌이 있으면 중단한다. `src/agent` 경로, `invocations` protocol, Python 3.13 code deployment도 확인한다.

기존 Foundry 프로젝트 전체를 재프로비저닝하지 않는다. 기존 모델 배포·지식 객체·에이전트를 임의로 수정하지 않는다. 새로 만든 것의 정확한 이름과 ID는 `.foundry` 상태에 기록한다.

로컬 서버는 신뢰할 수 있는 개발 환경에서만 잠깐 실행하고 즉시 종료한다. 공개망에 노출하지 않는다. 로컬 테스트 서버와 Azure 플랫폼이 인증을 처리하는 hosted endpoint는 서로 다른 보안 경계다.

## 실습 시간 리허설

| 시간 | 참가자 단계 | 확인할 결과 |
|---|---|---|
| 00–10분 | 1. 시작 준비 | 테스트·두 CLI 로그인·계정 확인·preflight·bind |
| 10–25분 | 2. 지식 검색 A | 실제 IQ 문서 ID와 activity |
| 25–40분 | 3–4. 로컬·배포 B | 로컬과 원격의 실제 응답 |
| 40–55분 | 5. baseline C | dev 24행과 Foundry 평가 |
| 55–70분 | 6. 실패 검토 D | 실제 trace와 검토된 회귀 데이터 |
| 70–85분 | 7. V2 재평가 E | 새 버전·같은 dev 24행 |
| 85–100분 | 8. holdout F | 고정 후보의 16행 |
| 100–110분 | 9. 운영·검증 G | 64응답·64trace·lineage |
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

## 가이드 수정 시 확인

원래 저장소 루트의 가상환경에서 아래를 실행한다. 문서 검사는 명령을 실제 파서로 확인하되 **Azure 호출 전에 중단**하며, 순서·링크·복사 블록의 오류 중단을 확인한다.
문서가 없는 실행용 소스 스냅샷에서도 핵심 테스트가 동작하도록 `tests_docs`를 `tests`와 분리했다.

```bash
python -m unittest discover -s tests_docs -v
```
