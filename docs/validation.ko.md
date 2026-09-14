# 실제 실행 검증 보고서

## 2026-09-14–15 재실행 — `20260914-2034`

**새 Azure 환경의 실제 실행, 추가 포털 촬영, 실습 전용 객체 정리를 완료했다.** 본평가 **64응답·64개 서로 다른 실제 trace·완료된 Foundry 평가 run 3개**를 확인했다. 2026-09-15에 지정 계정으로 다시 인증한 뒤 실제 Foundry 포털에서 KB·모델·V1/V2 응답·평가·trace·Monitor·정리 결과를 촬영했다. 이전 영상이나 모의 화면으로 대체하지 않았다.

[이번 실행의 선별 검증 JSON](assets/live-20260914-2034/azure-verification.json) · [실습 순서 통합 영상](assets/live-20260914-2034/foundry-evaluation-guide-order.mp4) · [절차별 전·후 화면](action-captures.ko.md) · [새 환경 준비](environment.ko.md)

### 새 환경과 보존 범위

| 항목 | 실제 상태 |
|---|---|
| 새 그룹 | `rg-foundry-evaluation-20260914-2034`, `swedencentral` |
| 새 Foundry 계정 / 프로젝트 | `fe-20260914-2034` / `learning-loop` |
| 새 Search | `fe-search-20260914-2034`, Basic, semantic/knowledge retrieval `free` |
| 새 관측 | `fe-logs-20260914-2034`, `fe-insights-20260914-2034` |
| 에이전트 | `ll-0914-2034-agent`, baseline version **1**, candidate/holdout version **2** |
| 보조 배포 | `ll-0914-2034-judge`, `gpt-5.4-mini` / `2026-03-17` |
| 기존 그룹 삭제 | **0건**. 이 리포 전용으로 확인된 기존 그룹이 없었음 |
| 기존 공유 환경 | `rg-iq-foundry-lab-56d62b` 및 다른 리포의 두 v2 그룹 보존 |
| 인증 | 지정 계정·tenant·구독과 발급된 ARM 토큰의 주체 대조 |

모든 Azure CLI 조회·변경에 구성된 구독을 명시했으며 `az account set`은 사용하지 않았다. Search가 최초 15분의 로컬 대기 제한을 넘긴 시도를 보존했고, 같은 리소스에서 이후 **`Succeeded` / `running`**을 실제 확인했다. 새 그룹으로 리소스를 재생성하거나 다른 리전·모델로 바꾸지 않았다.

### 실제 결과

네 모델·버전은 기존 계약 그대로다: Sol/Terra/Luna의 `2026-07-09`, Astra의 `2026-09-03`. 각 후보가 dev 6 + dev 6 + holdout 4 = **16개 답변**을 생성했다.

| 단계 | 버전 | 실제 응답 / trace | 업무 검사 | Groundedness 통과 | Relevance 통과 |
|---|---:|---:|---:|---:|---:|
| baseline dev | 1 | 24 / 24 | 0/24 | 24/24 | 21/24 |
| improved dev | 2 | 24 / 24 | 24/24 | 24/24 | 21/24 |
| holdout | 2 | 16 / 16 | 16/16 | 16/16 | 16/16 |

업무 검사는 V2에서 모델별 dev **6/6**, holdout **4/4**다. LLM evaluator는 기존 1–5점 척도와 threshold 4를 유지했다. **업무 검사와 native relevance의 결과는 다르며**, 불합격 native 점수를 합격으로 바꾸지 않았다. 오류·누락 행을 분모에서 빼지 않았다.

| 단계 | Evaluation ID | Run ID |
|---|---|---|
| baseline | `eval_4e52a8af03e94b1d97fccce719cf568b` | `evalrun_28e28fff0a1240e687d216826f1c5075` |
| improved | `eval_276405197d78476abfd5b25377291e95` | `evalrun_022dd0d4fe17441ba7fb469077108050` |
| holdout | `eval_61a0c1526bd54a559385fef1cf788e17` | `evalrun_b6b76d93cc3d46baa5b9505a2be77c51` |

Calibration의 고정 정답/오답 2개, 로컬·원격 smoke 호출은 이 64개 본평가 응답에 포함하지 않았다. 기존 교육용 holdout을 재실행했으므로 **새로운 독립 검증셋이나 일반적인 모델 우월성의 증거가 아니다.** `production_release_approved`는 **false**다.

### 실제 실패 검토와 lineage

`baseline-sol-D01`은 180,000원 한도와 `allowed` 판단은 맞았지만, `TRAVEL-2026` 대신 `"현행 국내 출장비 규정"`이라는 제목을 인용했다. 실제 검색 결과에 `TRAVEL-2026`이 있었으므로, 해당 사례의 실패를 “문서를 찾지 못함”으로 분류하지 않았다.

이 행의 실제 trace `09823f28661586d11629dd328191f997`을 대조한 뒤 고정 dev 정답을 유지한 회귀 데이터를 만들었다. V2 수집이 그 회귀 데이터를 실제로 읽고 원래 trace를 재사용한 lineage를 최종 검증했다. 검토자는 **assistant**이며 실제 재무 담당자의 승인으로 표시하지 않았다.

### 실행 중 확인해 수정한 점

| 관찰 | 처리 |
|---|---|
| `az ad signed-in-user show`가 `--subscription`을 받지 않음 | 기본 계정으로 우회하지 않고, 지정 구독으로 발급된 ARM 토큰에서 tenant·principal을 확인. 토큰은 출력·저장하지 않음 |
| Search 준비가 최초 로컬 대기 제한을 넘김 | 실패한 대기 기록 유지, 동일 서비스 재조회로 실제 준비 완료 확인 |
| 실제 로컬 HTTP JSON 뒤에 azd 확장 업데이트 안내가 붙음 | UTF-8 `Content-Length`와 응답 경계를 엄격히 구분. 확인된 안내만 별도 경고로 기록. 알 수 없는 후행 오류는 거부 |
| azd 부모 종료 직후 잠깐 남은 로컬 포트 | 소유 프로세스·포트가 실제 종료됨을 재확인하고 종료 확인에 제한된 대기 추가. 다른 프로세스는 종료하지 않음 |
| MCP 브라우저 연결 재설정 | 원본 영상 2개와 캡처 보존. 완료 전 이동은 `interrupted`로 기록. 독립 Playwright headless 프로세스로 전환하고 재인증 후 같은 실제 대상을 다시 촬영 |
| 탭 이동 후 버전 선택이 최신 버전으로 복귀 | Playground·Details 이동 뒤 선택 버전과 실제 응답의 `prompt_version`을 다시 확인 |
| Foundry Indexes 목록과 Monitor Tools 목록이 비어 있음 | Search index 부재·도구 미실행으로 해석하지 않음. 실제 Azure Search의 7문서와 native retrieve span으로 별도 확인 |
| 비교 UI가 입력을 양쪽에 동기화 | 두 응답의 실제 `prompt_version`과 서로 다른 trace로 V1/V2를 식별. 화면의 입력 label만으로 버전을 단정하지 않음 |

파서 보완은 CLI 실행기 두 파일에 한정했다. **에이전트 코드·V1/V2 지침·정답/정책 데이터의 원래 hash가 변하지 않았음**을 확인했다. 최초 로컬 응답의 `.http` 원문도 보존했다. 관련 변경 후 필수 unittest 명령의 **39개 테스트**가 통과했다.

### 실제 포털 검증과 추가 호출

Azure Portal의 새 그룹·태그·자원 5개와 Foundry의 모델 5개, 실제 KB/source, Search index의 합성 문서 7개를 확인했다. 검토한 baseline trace를 **ID로 검색해 정확히 1건**을 찾고, 같은 요청의 9개 span·1개 chat·1개 tool call을 native Graph view에서 확인했다. 실제 model span의 `gen_ai.response.model`도 `gpt-5.6-sol-2026-07-09`였다.

포털에서 V1 단독 1회, V1/V2 비교 2회를 추가 호출했다. **이 3응답은 본평가 64응답과 별도**다. 비교 UI가 입력을 동기화해 양쪽 `run_id`가 같았지만 실제 응답은 `prompt_version=v1` / `v2`, 서로 다른 trace ID로 구분됐다. V1은 문서 제목, V2는 `TRAVEL-2026`을 인용했다.

Monitor의 Last Day 화면에는 약 **189.5K 토큰·70 agent runs**가 표시됐고, 별도 tool chart는 71호출을 표시했다. 차트별 집계와 반영 시점은 다르며, 이 수치를 본평가 64행의 분모나 HTTP 실패 건수로 치환하지 않았다. 표시된 추정 비용 `$0`도 전체 Azure 청구액이 아니다. Continuous / scheduled evaluation, 알림, 자동 재학습·자동 운영 배포는 활성화하지 않았다.

### 최종 정리와 남은 비용

인증 대기 중에는 **세션 6개를 중지하고 active 0개**를 확인해 객체를 임시 보존했다. 이후 추가 포털 촬영을 마치고 `cleanup --dry-run` → `cleanup --confirm` → `check-cleanup`을 실제 실행했다.

| 대상 | 최종 확인 |
|---|---|
| 실습 Hosted Agent V1/V2 및 세션 | agent 부재 확인, 포털 Agents 목록도 비어 있음 |
| 네 후보 모델 배포 | 4개 부재 확인, 포털에는 보조 judge만 남음 |
| KB / knowledge source / index | 3개 부재 확인, 같은 Search 연결의 KB 목록도 비어 있음 |
| 실습 런타임 역할 부여 | 3개 부재 확인 |
| 새 Foundry / Search / App Insights / Logs | 보존, 포털의 기반 자원 5개 확인 |
| 고정 보조 judge / 네이티브 평가 이력 | 보존, baseline/improved/holdout/calibration run 확인 |
| 과거 공유 환경·다른 리포의 그룹 | 변경·삭제하지 않음 |

따라서 **실습 실행 자원 정리와 Azure 비용 전체 제거는 다르다.** 보존된 Search Basic 서비스, 로그 보존, 기반 서비스의 비용은 환경 소유자가 관리해야 한다.

### 별도로 남긴 구독 경보·거버넌스 이력

새 그룹의 ARM 배포 이력에 경보/정책 관련 실패 2건도 있어 실제 오류 화면을 확인했다. 이를 agent 배포 성공이나 평가 성공으로 바꾸지 않았다.

- Failure-anomaly alert: `MissingSubscriptionRegistration` — 구독의 `Microsoft.AlertsManagement` 미등록.
- Governance-policy diagnostic setting: `ResourceNotFound` — 정책이 참조한 공유 Log Analytics workspace 부재.

이 항목들은 본 실습의 응답·평가·trace·객체 정리와 별도이며, 경보·거버넌스까지 정상 구성됐다고 주장하지 않는다. **공유 구독 provider·거버넌스 리소스·정책을 임의로 바꾸지 않았다.**

원본은 `.recording/20260914-2034/`, 실제 응답·평가·trace는 그 아래 `workshop/src/agent/.foundry/results/`에 보존한다. 녹화 연결 재설정과 마지막 영상 종료 대기를 포함한 원본도 보존했고, 각 선택 영상은 실제 캡처와 대조했다. 가이드에는 비식별 화면과 선별 검증을 사용한다. 로그인·PIN 화면은 녹화하지 않았다.

---

## 이전 검증 기록 — 2026-09-10

검증일: **2026-09-10**

**요청한 네 모델과 Hosted Agent, Foundry IQ, Foundry Evaluation, Trace, Monitor를 실제 Azure에서 실행했다.** 최종 비교 대상은 **모델 응답 64건, Foundry 평가 64행, 서로 다른 실제 trace 64개**다. 모의 결과를 실제 실행 결과로 사용하지 않았다.

다만 **구성 요소의 실행 검증 완료와 운영 품질 합격은 다르다.** V2의 dev 업무 계약 통과율은 모델별 5/6이며, 필수 인용 100% 조건을 만족하지 못했다. 따라서 운영 승격은 승인하지 않는다.

## 1. 검증 환경과 범위

| 항목 | 실제 사용 |
|---|---|
| Azure 계정 | 사용자가 지정한 계정으로 구독·tenant를 확인하고 실행 |
| 기존 프로젝트 | `iq-foundry-lab-56d62b` |
| 지역 | `swedencentral` |
| Hosted Agent | `frontier-loop-0910`, Python 3.13, Invocations protocol 2.0 |
| 최종 baseline | agent version **5**, prompt **v1** |
| 개선 후보 및 holdout | agent version **6**, prompt **v2** |
| Foundry IQ | `ll-0910-kb`, knowledge source와 semantic index, 합성 문서 7개 |
| 검색 방식 | 실제 `retrieve` API, `extractiveData`, `low` reasoning, query planning 활동 확인 |
| 보조 모델 | 기존 `gpt-5.4-mini` 배포를 planner와 공통 judge로 사용 |
| 모델 추론 | 같은 Foundry 계정의 Azure OpenAI v1 Chat Completions, Entra managed identity |
| 평가 | 새 Foundry Evaluation API의 실제 응답 JSONL 평가 |
| 관측 | 연결된 Application Insights의 실제 요청·모델·retrieval span 조회 |

기본 Azure CLI 구독은 변경하지 않았다. 구독·tenant를 명시하는 자격 증명을 사용했다. 포털 경로는 가이드에 포함했지만, 이번 자동 검증의 증거는 **CLI/SDK/API와 실제 telemetry**이며 포털 화면 클릭 테스트를 수행했다고 주장하지 않는다.

## 2. 네 모델을 실제로 사용했는가

배포 설정만 확인한 것이 아니다. 세 최종 코호트의 `learning_loop.answer`와 `chat` span을 `operation_Id`로 연결해 **반환된 모델 ID**를 조회했다.

| 후보 | 배포 이름 | trace의 실제 `gen_ai.response.model` | 확인한 요청 |
|---|---|---|---:|
| Sol | `ll-0910-sol` | `gpt-5.6-sol-2026-07-09` | 16 |
| Terra | `ll-0910-terra` | `gpt-5.6-terra-2026-07-09` | 16 |
| Luna | `ll-0910-luna` | `gpt-5.6-luna-2026-07-09` | 16 |
| Astra | `ll-0910-astra` | `gpt-6-astra-2026-09-03` | 16 |

각 모델의 16건은 dev baseline 6건 + 개선 dev 6건 + holdout 4건이다. [실측 모델 식별 요약](../artifacts/model-identity.json)에 조회 범위를 남겼다.

## 3. 전후 결과

### 결정적 업무 계약 검사

아래 점수는 **판단 label, 필수 금액, 실제 근거 인용을 모두 통과한 건수**다. 일반적인 모델 지능이나 모든 업무의 정확도를 뜻하지 않는다.

| 모델 | V1 dev | V2 dev | V2 holdout | V2 dev 인용 gate |
|---|---:|---:|---:|---|
| Sol | 0/6 | 5/6 | 4/4 | 미통과: 필수 5건 중 유효 인용 4건 |
| Terra | 0/6 | 5/6 | 4/4 | 미통과: 필수 5건 중 유효 인용 4건 |
| Luna | 0/6 | 5/6 | 4/4 | 미통과: 필수 5건 중 허용 인용 4건 |
| Astra | 0/6 | 5/6 | 4/4 | 미통과: 필수 5건 중 유효 인용 4건 |
| **합계** | **0/24** | **20/24** | **16/16** | **운영 승격 보류** |

V1은 짧은 답변을 위해 내부 문서 식별자를 감추도록 만든 **교육용의 불충분한 초기 지침**이다. 0/24는 “모든 답이 사실상 틀렸다”는 의미가 아니다. 예를 들어 baseline Sol은 판단 label 5/6과 필수 금액 6/6을 맞췄지만, 문서 ID 대신 제목을 인용해 업무 계약을 통과하지 못했다.

### Foundry native evaluator

같은 evaluator 버전·judge 배포·threshold 4를 유지했다. 점수 척도는 1–5다.

| 모델 | V1 groundedness / relevance | V2 groundedness / relevance | Holdout groundedness / relevance |
|---|---|---|---|
| Sol | 5.00 / 3.83 | 5.00 / 4.00 | 5.00 / 4.00 |
| Terra | 4.50 / 3.83 | 5.00 / 4.00 | 5.00 / 4.00 |
| Luna | 4.83 / 3.67 | 5.00 / 4.00 | 5.00 / 4.50 |
| Astra | 4.67 / 3.83 | 4.83 / 4.00 | 5.00 / 4.00 |

핵심 학습은 **groundedness가 높아도 기업의 인용·승인 라우팅 계약까지 만족하는 것은 아니라는 점**이다. 또한 같은 질문·KB를 써도 retrieval context가 달라진 사례가 있으므로 이 표를 순수 모델 성능 순위로 해석하면 안 된다.

## 4. 남아 있는 실패를 숨기지 않았다

| 사례 | 실제 관찰 | 해석 |
|---|---|---|
| `improved-sol-D06`, `improved-terra-D06`, `improved-astra-D06` | 검색 결과의 `source_ids`가 비어 있었고 모델이 정책을 만들지 않고 보류했다. | end-to-end 시스템은 필요한 정책을 찾아 답하지 못했다. 근거 없는 답변을 생성하지 않은 것은 바람직하지만, **검색 문제는 prompt만으로 해결되지 않는다.** 특정 content filter가 원인이라고 단정하지 않았다. |
| `improved-luna-D01` | 답은 맞고 두 인용 모두 실제 문서였다. 다만 추가 승인 조건을 설명하며 `APPROVAL-2026`도 인용했다. | 동결한 rubric은 D01에 `TRAVEL-2026`만 허용하여 실패로 처리했다. **rubric이 지나치게 엄격한지 SME 검토가 필요**하다. 결과를 좋게 만들려고 평가 중 허용 목록을 바꾸지 않았다. |

holdout 4문항에서 모두 통과했어도 위 dev 실패가 사라지는 것은 아니다. 전체 모델의 운영 승격을 보류하는 것이 이번 실습의 정직한 결론이다. 추가 개선은 검색과 평가 기준을 구분한 다음 **새 실험 버전**에서 검증해야 한다.

## 5. learning loop가 실제로 닫혔는가

한 사례의 lineage를 확인했다.

```text
baseline-fulltrace-sol-D01
  source trace: 6fd506db66a6f1f674a98c249f56151d
  citations: ["현행 국내 출장비 규정"]
    -> 검토된 regression JSONL
    -> 같은 동결 질문/기준을 V2에서 실제 재사용
    -> improved-sol-D01
       trace: 56089ae813c34af587b88bcaae01d122
       citations: ["TRAVEL-2026"]
    -> Foundry 재평가와 업무 계약 재검사
```

regression은 저장만 하고 방치하지 않았다. 후보 수집기가 실제로 읽고, 새 응답의 `regression_source_trace_ids`에 이전 trace를 기록했다. 질문·정답·rubric이 동결한 dev 데이터와 다르면 비교를 중단하도록 했다.

자동 검증의 reviewer는 **assistant**로 명시했다. 정책·기준 정답·calibration 문구는 AI 보조로 작성한 합성 초안이며, 실제 재무 담당자의 검토나 생산 환경 승인을 주장하지 않는다. 초기 내부 metadata의 `human-authored` 명명은 작성 주체를 증명하는 값이 아니었으며, 최종 코드·내보낸 자료에서는 고정 참조 데이터라는 표현으로 정리했다. 실제 요청·정답·점수는 변경하지 않았다.

## 6. Foundry run과 관측 증거

| 구분 | Evaluation ID | Run ID | 평가행 / 실제 trace |
|---|---|---|---|
| V1 baseline | `eval_244d17b3f5d440b5955c5509edec0e46` | `evalrun_eb3101add0eb4095923b06480f11c5f8` | 24 / 24 |
| V2 dev | `eval_37890a816f044a4cb0910eb4b639b71a` | `evalrun_9ae8ea6981154448936dcc833854708b` | 24 / 24 |
| V2 holdout | `eval_34e382b33db8488bb830d7f63cdd30f9` | `evalrun_d66cab90d29f4ac7aadbf664f806a58d` | 16 / 16 |

세 run 모두 `completed`, 평가 실행 오류 0건이다. 실제 telemetry는 요청 성공률 100%, sample weight 1로 확인했다. 이는 **HTTP 실행 성공률**이며 위 업무 계약 통과율과 다르다.

별도의 judge calibration 2건도 Foundry에서 실행했다. 명시한 올바른 금액은 통과하고, 근거 없는 금액은 groundedness에서 탈락했다. 이 예제 2건은 본평가의 모델 응답 64건에 포함하지 않았다.

## 7. 120분 설계와 실측 시간

| 최종 코호트 | 응답 생성 구간, KST | 생성 시간 | Foundry 평가 시간 |
|---|---|---:|---:|
| V1 dev 24건 | 20:05:44–20:06:58 | 74초 | 약 70초 |
| V2 dev 24건 | 20:25:53–20:26:51 | 58초 | 약 60초 |
| V2 holdout 16건 | 20:34:08–20:34:48 | 40초 | 약 44초 |

최종 baseline 시작부터 holdout telemetry 확인 파일 저장(20:35:55)까지 약 **30분 11초**였다. 이는 준비된 환경에서 최종 경로를 실행·검토한 구간이다. 참가자 코스는 개념 설명, 코드 확인, 사람의 검토, 포털 확인, 정리와 지연 버퍼까지 포함해 120분으로 설계했다.

**환경 준비·가이드 작성·API/권한 호환성 진단을 포함한 전체 작업은 2시간을 넘었다.** 신규 환경을 처음부터 준비하는 시간까지 2시간 안에 끝났다고 주장하지 않는다. 강사는 사전 준비와 리허설을 완료해야 한다.

응답 생성에 보고된 본평가 토큰은 **입력 75,212 / 출력 7,420**이다. IQ planner, LLM judge, 진단·재시도·local smoke와 인프라 비용은 별도이므로 이 수치가 전체 Azure 요금은 아니다. 작은 표본의 p95는 운영 SLO의 증명이 아니다.

## 8. 실제 실행에서 발견해 반영한 점

| 관찰 | 최종 가이드/코드의 처리 |
|---|---|
| Astra의 프로젝트 Responses `json_schema` 거부 및 최소 Responses 요청 500 | 같은 실제 모델을 유지하고 공통 JSON 텍스트 계약 + Pydantic 검증 사용 |
| 프로젝트 Chat Completions의 hosted identity 권한 오류 지속 | 같은 Foundry 계정 endpoint와 명시적 Entra token scope 사용. 실제 hosted Astra 응답 확인 |
| 시작 시 agent의 `connections/read` 권한 부족 | runtime에 주입된 telemetry 설정 사용. 불필요하게 연결 조회 권한을 요구하지 않음 |
| 기존 App Insights 연결에 `ResourceId` metadata 누락 | target/authType을 유지한 metadata-only 보완 후 실제 Foundry 평가 성공 |
| 기본 rate-limited sampling에서 24개 중 20개 trace만 관측 | 실습 agent만 100% sampling으로 배포하고 최종 baseline을 새로 실행 |
| API가 `"True"` 문자열로 반환한 telemetry boolean | 문자열/boolean을 엄격하게 정규화. 알 수 없는 값은 오류 |
| CLI token 조회의 기본 10초 제한 | 계정·구독을 고정한 상태에서 60초의 제한된 cold-token timeout 사용 |
| azd raw 출력이 HTTP 헤더 포함 | 상태 코드와 JSON body를 분리해 확인 |
| 정리 기록이 가변 소유권 목록을 공유하던 문제 | immutable plan snapshot과 회귀 테스트 추가. 기존 dry-run의 ID를 복원한 후 실제 Azure에서 4개 배포·3개 역할 삭제를 재확인 |

실패한 시도를 성공 데이터로 바꾸거나 성공한 행만 골라 채점하지 않았다. 최종 비교는 별도 label의 완전한 세 코호트만 사용했다.

## 9. 정리 상태

`cleanup --dry-run` → `cleanup --confirm` → **`check-cleanup`의 실제 Azure 재조회**를 수행했다.

| 대상 | 최종 상태 |
|---|---|
| 실습 Hosted Agent와 그 버전·세션 | 삭제 확인 |
| `ll-0910-*` 모델 배포 4개 | 삭제 확인 |
| 실습 KB / knowledge source / index 3개 | 삭제 확인 |
| 실습 중 추가한 역할 부여 3개 | 삭제 확인 |
| 기존 Foundry 프로젝트, Search 서비스, Application Insights | 유지 확인 |
| 기존 보조 모델 `gpt-5.4-mini` | 유지 확인 |
| App Insights의 비파괴 `ResourceId` metadata 보완 | 유지 |
| Foundry evaluation run 및 로컬 검증 결과 | 보존 |

검증용 agent를 삭제했으므로 예전 agent playground URL이 계속 열린다고 보장하지 않는다. 기존 Search/App Insights 등의 가동·보존 비용은 환경 소유자가 관리해야 한다.

## 10. 재현과 파일

- [한국어 가이드](../README.md), [강사 준비](instructor.ko.md), [출처](sources.ko.md)
- [검증 요약 JSON](../artifacts/verification-summary.json), [전후 비교 JSON](../artifacts/comparison.json)
- [실측 모델 ID](../artifacts/model-identity.json), [정리 재확인](../artifacts/cleanup-check.json)
- [개인 실행 환경을 제외한 GitHub 전체 자료 ZIP](https://github.com/junwoojeong100/foundry-evaluation/archive/refs/heads/main.zip)

원래 작업 폴더의 raw 증거는 `src/agent/.foundry/results/`에 있다. 공개 저장소와 GitHub 자료 ZIP에는 배포 가능한 소스·선별한 합성 결과·최종 녹화본을 포함한다. `.env`, `.azure`, `.venv`, 실행 캐시, credential/토큰, 녹화 원본·중간 자료와 환경별 실행 증거 ZIP은 포함하지 않는다. 기존 별도 배포용 ZIP은 `artifacts/foundry-learning-loop-ko.zip`에 로컬 보존한다.

최종 검증에는 **27개 오프라인 테스트**, Python 구문 확인, 실제 Azure 실행, native 평가, 100% trace 확인, 회귀 lineage 검증, 임시 자원 삭제 재확인이 포함됐다. 구성 요소의 성공을 production readiness로 확대 해석하지 않는다.
