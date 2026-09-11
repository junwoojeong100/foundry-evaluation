# 강사 준비: 120분 실습의 시작 조건

이 문서는 참가자 120분에 포함하지 않는 **환경 준비**다. 빈 Azure 구독에서의 전체 소요 시간은 모델 접근 승인·할당량·권한 전파에 따라 달라진다.

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
| 인증 | `az`와 `azd`가 의도한 계정으로 로그인되어 있음 |
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

## 설정과 안전한 준비

1. `.env.example`을 `.env`로 복사하고 **실습 환경의 값**을 채운다.
2. 기본 Azure CLI 구독을 바꾸는 대신 지정 구독으로 조회·인증한다.
3. `python scripts/workshop.py preflight --allow-missing-models`로 환경과 네 모델의 지역별 지원·할당량을 읽기 전용 확인한다.
4. 모델이 없다면 `python scripts/workshop.py prepare-models`로 **고유 접두사**를 가진 네 배포만 만든다.
5. `python scripts/workshop.py preflight`를 다시 통과시킨다.
6. `prepare-iq`와 실제 retrieval을 실행한다.
7. azd를 아래 절차로 바인딩하고 로컬·원격 smoke test를 완료한다.
8. `python scripts/workshop.py calibrate`로 명시적으로 정의한 정답/오답 예제 2건을 Foundry에서 평가한다. 실제 네 모델 응답과 섞지 않는 judge 점검이며, groundedness가 근거 없는 금액을 구분하는지 확인한다.

평가가 `AppInsights connection is missing ResourceId metadata`로 실패하면 `python scripts/workshop.py repair-observability --confirm`으로 기존 연결에 **실제 Application Insights ARM ID 메타데이터만** 추가한다. target/credential은 변경하지 않는다. 이 비파괴 연결 보완은 cleanup 후에도 유지된다. 이후 `calibrate --retry-failed`로 실패 run을 보존한 채 새 run을 만든다.

모델은 `GlobalStandard` 사용량 기반 배포를 사용한다. PTU를 예약하거나 할당량 증설을 자동 신청하지 않는다. 실제 모델/SKU/할당량 검사를 통과하지 못하면 강사가 먼저 해결한다.

## azd 초기화

이 저장소에는 실습 전용 `azure.yaml`과 소스가 제공된다. 기존 프로젝트를 사용할 때는 **기존 프로젝트의 ARM ID**와 실제 보조 모델 deployment name을 사용한다.

```bash
python scripts/workshop.py bind
```

`azure.yaml`이 없을 때는 공식 `azd ai agent init --src ... --project-id ...` 경로를 사용한다. 제공된 `azure.yaml`이 있으면 다시 init하여 `-2` agent를 만드는 대신 로컬 azd environment를 만들거나 재사용한다. service key와 agent name을 조별 이름으로 맞춘다. 구독·프로젝트 충돌이 있으면 중단한다. `src/agent` 경로, `invocations` protocol, Python 3.13 code deployment도 확인한다.

기존 Foundry 프로젝트 전체를 재프로비저닝하지 않는다. 기존 모델 배포·지식 객체·에이전트를 임의로 수정하지 않는다. 새로 만든 것의 정확한 이름과 ID는 `.foundry` 상태에 기록한다.

로컬 서버는 신뢰할 수 있는 개발 환경에서만 잠깐 실행하고 즉시 종료한다. 공개망에 노출하지 않는다. 로컬 테스트 서버와 Azure 플랫폼이 인증을 처리하는 hosted endpoint는 서로 다른 보안 경계다.

## 설치와 실행

```bash
python3.13 -m venv src/agent/.venv
source src/agent/.venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/workshop.py preflight
```

프레임워크와 Foundry SDK의 버전 상한이 다를 수 있다. Agent Framework Foundry 1.11.0, core 1.16.0, OpenAI adapter 1.14.1, Azure AI Projects 2.3.0, Agent Server Invocations 1.1.0을 고정했다. 무조건 모든 패키지를 최신 버전으로 올리지 않는다. `requirements.lock.txt`는 검증 환경의 전체 의존성 스냅샷이다. 같은 Python 환경을 재현할 때 `python -m pip install -r requirements.lock.txt`를 사용할 수 있다.

## 실습 시간 리허설

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
