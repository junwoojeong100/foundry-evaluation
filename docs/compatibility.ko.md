# 호환성·지원 범위·출처 검토

[English](compatibility.en.md) · [메인 가이드](../README.ko.md) · [평가 설계](evaluation-design.ko.md) · [가이드 유지보수](maintaining.ko.md)

**출처 검토일: 2026-09-26.** “현재 공식 문서를 확인했다”, “오프라인 검사가 통과했다”, “실제 Azure 실행을 마쳤다”는 서로 다른 주장입니다. 이 문서는 이를 분리하며 모든 GitHub 저장소 중 객관적으로 1위라고 주장하지 않습니다.

## 목적에 맞는 실습 경로

| 경로 | 하는 일 | 남는 증거 | Azure 사용 |
|---|---|---|---|
| [레벨 0](offline.ko.md) · 15분 | 작성된 답변을 채점하고 회귀·검사 사각지대 발견 | 합성임을 명시한 로컬 보고서 | 없음 |
| [레벨 1](../README.ko.md#start-here) · 환경 준비 후 120분 | 배포·수집·평가·검토·개선·holdout·정리 | 실제 48응답, trace, 평가, 검토 이력 | 유료 |
| [레벨 2](level-2.ko.md) · 40분 | 기본·코드·도메인 rubric 판정 비교 | 평가 항목 9개, 판정 불일치·실패 분석 | judge·서비스 추가 호출 |
| [레벨 3](level-3.ko.md) · 약 70분 | rubric 생성·스트레스 테스트·모델/에이전트/trace 평가·일정·게이트 | 대상별 별도 증거와 명시적 게이트 판단 | 추가 호출·임시 일정 |

레벨 2는 레벨 1의 9단계 뒤, 레벨 3은 레벨 2 뒤에 합니다. 둘 다 **정리 전에** 진행합니다. 준비·서비스 대기·지역별 기능 제공·권한 확보 시간까지 보장하는 예상 시간은 아닙니다.

## 재현 가능한 실행 환경과 최신 SDK 구분

기록된 실행의 환경을 의도적으로 고정합니다. **한 수업 도중 `pip install --upgrade`로 의존성을 바꾸지 않습니다.** 기본 로컬 설치와 오프라인 CI는 `requirements.lock.txt`를 사용합니다. 전체 패키지 버전 스냅샷이며 암호학적 해시까지 고정한 패키지 잠금 파일은 아닙니다.

| 구성 요소 | 저장소의 계약 | 확인할 곳 |
|---|---|---|
| 클라우드 실습 Python | 3.13, Bash, macOS/Linux 또는 WSL | [도구 준비](instructor.ko.md#tools), `azure.yaml` |
| 오프라인 입문 Python | 3.10 이상, 표준 라이브러리만 사용, 기본 Windows 지원 | `scripts/offline_lab.py`, 자격 증명 없는 CI 작업 |
| Foundry 프로젝트 SDK | `azure-ai-projects==2.3.0` | `src/agent/requirements.txt`, `requirements.lock.txt` |
| Agent Framework | Foundry 1.11.0, core 1.16.0, OpenAI adapter 1.14.1 | `src/agent/requirements.txt` |
| Agent Server | Invocations 1.1.0, core 2.1.0 | `src/agent/requirements.txt` |
| OpenAI client | 전체 스냅샷의 2.54.0 | `requirements.lock.txt` |
| Search 지식 검색 | `2026-05-01-preview` | `src/agent/knowledge.py` |
| 모델 식별 | 세 모델·버전 쌍 고정. 실제 배포 이름은 환경별로 다름 | [모델 계약](reference.ko.md#model-names), `preflight` |
| Judge·평가기 버전 | 한 실험 안에서 judge 배포와 처음 조회한 평가기 정의 고정 | [평가 방법](validation.ko.md#business-checks) |
| CLI·포털 증거 | 버전을 남긴 과거 실행. 현재의 모든 조합을 보증하지 않음 | [기록된 도구](instructor.ko.md#tools), [기록된 결과](validation.ko.md) |

### 현재 SDK와의 중요한 차이

검토일 기준 [PyPI의 `azure-ai-projects` 최신 버전은 2.7.0](https://pypi.org/project/azure-ai-projects/2.7.0/)이며 2026-09-18에 게시됐습니다. **2.3.0은 실습의 고정 버전이지 최신 버전이 아닙니다.** 현재 Learn 예제를 이 환경에 그대로 붙여 넣으면 모두 동작하는 것이 아닙니다.

[공식 SDK 변경 이력](https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/ai/azure-ai-projects/CHANGELOG.md)에는 다음 차이가 있습니다.

| 변경 | 무검토 업그레이드가 위험한 이유 |
|---|---|
| 2.4: 생성 작업이 `begin_create_generation_job`과 장기 실행 poller를 사용 | 2.3 실습은 job ID를 직접 저장하고 조회하므로 호출·반환 계약이 다름 |
| 2.5: OpenAI 의존성이 `openai>=3.0.0`·`httpx2`로 바뀜 | Foundry SDK만 올리면 고정한 프레임워크·클라이언트 조합과 충돌할 수 있음 |
| 2.7: beta 데이터 생성 옵션의 생성자 변경 | import가 성공해도 실제 실행 동작은 달라질 수 있음 |

**2.7 마이그레이션을 완료했다고 주장하거나 자동 수행하지 않습니다.** 마이그레이션은 별도 환경에서 의존성과 관련 코드를 함께 바꾸고 polling·재개·오류·정리 동작을 보존해야 합니다. 오프라인 검사 후 승인을 받아 두 언어와 영향을 받는 실제 레벨을 리허설하고 새 증거를 별도로 남깁니다. [유지보수 절차](maintaining.ko.md#upgrades)를 따릅니다.

## New Foundry와 classic

이 실습에는 `/azure/foundry/`의 **새 Microsoft Foundry** 문서를 사용합니다. `/azure/foundry-classic/`의 classic 평가 예제는 SDK·프로젝트 유형·입력 매핑·출력 형태가 다른 경우가 많습니다.

| 주제 | 현재 공식 출처 | 이 저장소에서의 해석 |
|---|---|---|
| 평가 단위·클라이언트 준비 | [클라우드 평가 개요](https://learn.microsoft.com/azure/foundry/observability/how-to/cloud-evaluation) | 저장된 답변·새로 생성하는 대상·전체 대화 구분 |
| 기존 답변 데이터 | [데이터셋 평가](https://learn.microsoft.com/azure/foundry/observability/how-to/cloud-evaluation-datasets) | 레벨 1은 에이전트를 다시 호출하지 않고 저장된 답변 채점 |
| 모델·에이전트 호출 | [대상 평가](https://learn.microsoft.com/azure/foundry/observability/how-to/cloud-evaluation-targets) | 레벨 3의 새 관측값은 기존 48개에 더하지 않음 |
| 업무별 에이전트 기준 | [에이전트 평가](https://learn.microsoft.com/azure/foundry/observability/how-to/evaluate-agent) | rubric을 검토하고 안전 신호 추가. 새 생성 예제는 새 SDK 필요 |
| 점수·조회·지연·비용 | [평가 결과](https://learn.microsoft.com/azure/foundry/observability/how-to/cloud-evaluation-results) | 누락·오류를 보존하고 대상 추정 비용과 청구액 구분 |
| 지역·한도·네트워크·저장소 | [평가 제공 범위](https://learn.microsoft.com/azure/foundry/concepts/evaluation-regions-limits-virtual-network) | 모델이 제공돼도 모든 평가기·red team을 지원하는 것은 아님 |
| Classic 경계 | [Classic 연속 평가](https://learn.microsoft.com/azure/foundry-classic/how-to/continuous-evaluation-agents) | 새 포털 실습과 교환해서 사용하지 않음 |

역할 이름은 전환 중 **Foundry User/Owner** 또는 이전 **Azure AI User/Owner**로 보일 수 있으며 이름 변경으로 역할 ID가 달라지지는 않습니다. 익숙한 표시 이름만 보지 말고 [정확한 범위별 역할 표](instructor.ko.md#access)를 확인합니다. 문제를 우회하려고 Owner로 넓히지 않습니다.

이 저장소의 native 품질 합격선 **4**는 의도한 선택입니다. Learn 예제의 기본 합격선과 다를 수 있으므로 플랫폼 전체의 기본값을 추정하지 말고 고정한 평가기 정의와 저장된 결과를 확인합니다.

## GitHub에서 비교한 자료

다음은 **2026-09-26에 확인한 대표 공개 자료의 진입 문서**입니다. 전수 조사·기능 부재 감사·실제 실행 비교가 아닙니다. 링크는 검토한 README revision을 고정합니다. 별점이나 업데이트 날짜를 품질 점수로 사용하지 않았습니다.

| 공개 자료 | 확인한 진입 문서의 강점 | 이 가이드가 보완하는 방향 |
|---|---|---|
| [Microsoft AI Tour LTG151](https://github.com/microsoft/aitour26-LTG151-build-trustworthy-ai-with-systematic-evaluations-in-microsoft-foundry/blob/8610367547fbdcf703d13a234e61e267bf5379da/README.md) | Foundry 관측·평가·모니터링·최적화 세션과 공식 SDK 예제 연결 | 완료 확인·복구·통제 비교·증거 경계를 갖춘 한영 실습 절차 |
| [Azure-Samples/Agentic-Evaluations](https://github.com/Azure-Samples/Agentic-Evaluations/blob/2d205f321b2e6b54ba62b5ee26c6cd79d492ab70/README.md) | 설정 기반 파이프라인·사용자 지정 judge·에이전트 지표·시각화 | 고정된 교육 실험과 사례별 업무 계약. 범용 프레임워크를 대체하지 않음 |
| [microsoft/FrontierWeekHack](https://github.com/microsoft/FrontierWeekHack/blob/7cdcc35df535d655cdf0900ccbc71d8108a05c67/README.md) | 시나리오 기반 에이전트 제작 → 관측 → 평가 → 워크플로 | Holdout·rubric 분석·trace·릴리스 게이트까지 평가에 집중 |
| [한국어 Evaluation Engineering 데모](https://github.com/devkimchi/foundry-evaluation-engineering-demo/blob/ea0c07122a85f6256fbf17bc382190676b885b95/README.md) | 포털 중심 V1/V2 비교와 상충하는 평가 판정 해석 | 코드·참조 판정의 불일치를 드러내는 로컬 실습과 hosted 경로 |

추가된 설명과 교육 데이터는 새로 작성했습니다. 연결한 저장소의 예제와 라이선스는 해당 저장소가 원본입니다.

## 증거와 알려진 한계

| 주장 | 뒷받침하는 것 | 입증하지 않는 것 |
|---|---|---|
| 자격 증명 없이 입문 실습 가능 | 네트워크·외부 프로세스 호출을 막은 표준 라이브러리 실행 테스트 | 실제 모델 품질 |
| 명령과 가이드의 일치 유지 | 파서 인수·Bash 문법·로컬 링크·한영 명령·예제 검사 | 현재 외부 포털 화면·Azure 가용성 |
| 짝 비교로 회귀 확인 | 행 순서·누락·중복·모델 분리·실행 간 context 변화 테스트 | 인과관계나 운영 릴리스 정책 |
| 실제 실행 기록이 있음 | 날짜가 있는 [영문](validation.en.md)·[한국어](validation.ko.md) 결과와 영상 | 문서를 수정할 때마다 새 Azure 실행 완료 |
| 공개 CI에 Azure 자격 증명이 불필요 | `.github/workflows/validate.yml`, 읽기 권한, Azure 로그인 없음 | 실제 평가·프로비저닝·Azure 정리 |

**알려진 한계:** 실제 경로는 고정한 세 모델 배포와 적합한 리전이 필요하며, 임의 모델 하나로 바로 시작하는 범용 예제가 아닙니다. 교육 데이터는 의도적으로 작습니다. 운영 네트워크 강화, 범용 멀티턴·멀티모달 평가, 교차 공급자 벤치마크, fine-tuning, 자동 운영 승격은 범위 밖입니다. 기록된 원본 클라우드 결과는 배포하지 않습니다. 새 clone을 완료된 실행처럼 보이게 하려고 대체 증거를 만들지 않습니다.

출처나 포털이 달라지면 정확한 절과 민감정보를 제거한 증상을 [기여 절차](maintaining.ko.md)로 전달합니다. 출처 검토일과 새 실제 리허설 날짜를 구분합니다.
