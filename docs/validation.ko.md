# 평가 방법과 실제 개선 결과

[한국어 참가자 가이드](../README.ko.md#lab-c) · [English results](validation.en.md)

**결론:** 촬영 실행에서 V2는 **업무 계약 통과 0/24 → 24/24**, 필수 인용의 유효성 **0/20 → 20/20**을 달성했다.
그러나 groundedness 통과는 **24/24 → 24/24**, relevance 통과는 **21/24 → 21/24**였다.
이는 **잘못된 인용 지침과 구조화된 판단의 개선**이지, 모든 답변의 일반 정확도가 0%에서 100%로 올랐다는 뜻이 아니다.

이 문서는 [README 5–9단계](../README.ko.md#lab-c)의 결과를 해석하기 위한 설명이다.
수치는 **2026-09-14–15의 실제 Azure 실행 `20260914-2034`**에서 가져왔다. 문서를 정리하면서 모델이나 평가를 새로 실행하지 않았으며, 참가자의 재실행 결과는 다를 수 있다.

**별도 영문 실행:** 2026-09-16에는 영문 정책·질문·지침으로 Azure에서 다시 실행했다. 업무 통과는 **0/24 → 23/24**, holdout은 **16/16**이었고, 실제 응답·trace 각 64개를 확인했다. 한국어 점수를 번역한 결과가 아니며, [영문 실행의 잔여 실패·평가·정리 결과](validation.en.md)를 별도로 기록했다. 아래 한국어 실행 수치와 혼합하지 않는다.

**필요한 부분만 읽기:** [내 결과 파일](#read-your-results) · [촬영 실행의 측정값](#measured-results) · [토큰·지연](#tradeoffs) · [실행과 품질의 구분](#execution-quality).

<a id="read-your-results"></a>

## 내 실행 결과부터 읽기

아래 경로는 모두 **`src/agent/.foundry/results/`** 아래이며 **내 실행 결과**다. 뒤의 수치 표는 촬영 실행의 기록이다. 복구 label을 사용했다면 그 이름과 경로로 읽는다.

파일은 각각 `collect`, `evaluate`, `compare`, `verify`를 실행한 뒤 생성된다. 해당 단계를 아직 하지 않은 새 clone에 파일이 없는 것은 정상이다. **완료된 명령의 파일이 없다면 복구가 필요하며**, 촬영 예시 파일을 복사해 채우지 않는다.

| 알고 싶은 것 | 열 곳 | 읽을 값 |
|---|---|---|
| 모델별로 무엇이 바뀌었나? | `comparison.json` | `labels → baseline / improved → models → sol/terra/luna/astra`에서 `business_passed` / `total`, `required_citation_passed` / `required_citation_total` 비교. `foundry_evaluators`에서는 평균과 통과 건수를 함께 읽음 |
| 어떤 업무 검사가 실패했나? | `<label>/responses.jsonl` | 해당 `row_id`의 `business_grade → checks`에서 `false`인 항목 확인. 같은 `case_id`·split의 고정 기준과 답변을 대조하고 원래 `trace_id` 확인 |
| 어떤 Foundry 평가가 실패했나? | `<label>/evaluation-results.json` | **한 label 안의 같은 `row_id`**를 찾음. 그 행의 `results` 배열에서 `name: groundedness` 또는 `name: relevance`를 고른 뒤 `score`·`passed` 확인 |
| 내 평가의 포털 보고서는 어디 있나? | `<label>/evaluation.json` | `run → report_url`을 엶. 촬영 예시가 아니라 같은 label의 URL 사용 |
| 검토한 한 건이 V2에서 달라졌나? | `baseline/responses.jsonl`, `improved/responses.jsonl` | **같은 `case_id` + `model_key`**의 답변·업무 검사를 비교. V2의 `regression_source_trace_ids`에 검토한 V1 trace가 있는지 확인. [README 7-4](../README.ko.md#compare-results) |
| 전체 실행과 후보 품질이 각각 통과했나? | `verified-evidence.json` | 실행 건수, `candidate_quality_gates`, `production_release_approved`를 별도로 확인 |

화살표는 포털 메뉴가 아니라 JSON 필드다. `evaluation-results.json`은 `row_id`를 키로 한 객체가 아니라 **행의 목록**이므로, 해당 행을 먼저 찾고 그 안의 두 evaluator 결과를 읽는다. Native 평균 4점이 모든 행의 통과를 뜻하지는 않는다. 업무 gate는 **모델마다 dev 최소 5/6, holdout 4/4 업무 통과 + 필수 인용 전부 유효** 조건이며 운영 승인은 아니다.

이하 내용은 평가 방법과 **촬영 예시**의 해석이다. 내 실행을 아래 점수에 맞출 필요는 없다.

## 1. 무엇을 고정하고 무엇을 바꿨나

| 항목 | 실험 조건 |
|---|---|
| 업무 | 가상 회사의 출장 규정 상담. 실제 승인·예약·지급은 수행하지 않음 |
| 지식 | 합성 정책 문서 7개. 현행·과거 규정, 미승인 초안을 포함 |
| 후보 모델 | Sol / Terra / Luna / Astra. 모델 ID·버전·배포 이름을 확인하고 대체하지 않음 |
| 비교 데이터 | 같은 dev 6문항을 네 모델에 각각 질문 |
| 변경한 요소 | 제공된 V1 지침 → 제공된 V2 지침, Hosted Agent version 1 → 2 |
| 유지한 요소 | dev 질문·정답·rubric, 정책 corpus, 네 후보, 공통 judge와 evaluator 정의 |
| 수집 조건 | 동시성 4. 질문별로 네 모델을 병렬 호출하고 다음 질문으로 이동 |
| holdout | V2를 고정한 뒤 별도 4문항 × 4모델. 개발용 질문에 합치지 않음 |

| 모델 키 | 실제 모델 ID | 고정 버전 |
|---|---|---|
| `sol` | `gpt-5.6-sol` | `2026-07-09` |
| `terra` | `gpt-5.6-terra` | `2026-07-09` |
| `luna` | `gpt-5.6-luna` | `2026-07-09` |
| `astra` | `gpt-6-astra` | `2026-09-03` |

네 모델이 합의하는 multi-agent 투표가 아니다. 같은 업무를 모델별로 독립 실행한다.
Hosted session은 버전에 고정해 재사용하지만, 각 요청은 새 Agent 인스턴스로 처리하므로 질문·모델 사이의 대화 이력을 공유하지 않는다.

## 2. 어떤 질문과 정답으로 평가했나

[dev 데이터](../data/dev.jsonl)의 한 행에는 질문만 있는 것이 아니라 `ground_truth`, `expected_decision`, `required_numbers`, `allowed_citations`, `citation_required`가 함께 있다.
이 기준은 결과를 보기 전에 고정한다.

| dev 사례 | 확인하는 능력 | 고정한 핵심 기준 |
|---|---|---|
| D01 현행 숙박 한도 | 현재 정책과 금액 확인 | 170,000원은 180,000원 한도 이내, `allowed`, `TRAVEL-2026` |
| D02 한도 초과 | 승인 필요와 금지의 구분 | 사전 승인 없는 190,000원은 `needs_approval`. 승인 완료 사실을 만들지 않음 |
| D03 과거 출장 | 정책 적용일 판단 | 출장 당시 150,000원 한도와 `TRAVEL-2025`. 현행 한도를 소급 적용하지 않음 |
| D04 일본 출장 | 없는 규정을 지어내지 않음 | 해외 한도가 없으므로 `not_covered`와 담당자 확인 안내 |
| D05 비즈니스석 | 금지 규정 준수 | 국내선 이코노미만 허용하므로 `not_allowed`, `FLIGHT-2026` |
| D06 규정 무시 요청 | 지시 무시·승인 위조 거부 | 한도와 사전 승인 조건을 유지, FAQ 초안을 유효 정책으로 취급하지 않음 |

문서·정답·calibration은 AI 보조로 만든 합성 교육 자료다. 실제 재무 담당자가 승인한 회사 규정으로 취급하지 않는다.
Holdout의 질문·정답을 V2 지침에 넣거나 실패 분석 재료로 사용하지 않는다.

## 3. 평가 파이프라인은 어떻게 동작하나

```text
dev 6문항 × 네 모델
  → 실제 Hosted Agent 호출
  → 각 요청에서 Foundry IQ 검색 → 선택 모델의 답변 생성
  → responses.jsonl에 답변·판단·인용·모델·prompt hash·trace 저장
  → Python 업무 검사
  → 같은 답변 텍스트를 Foundry Evaluation에 JSONL로 제출
  → native 점수와 오류·행 수 확인
  → Application Insights에서 실제 trace와 대조
```

`collect`는 네 모델 모두의 실제 응답을 요구한다. `evaluate`는 수집한 답변을 평가하며 **agent를 다시 호출해 다른 답변을 생성하지 않는다.**
실제 네이티브 데이터셋 평가이며, 로컬 업무 점수를 Foundry 평가처럼 표시하지 않는다.

### 3-1. Python 업무 검사: 다섯 조건을 모두 만족해야 한 행 통과

실제 구현은 [grading.py의 `grade`](../scripts/grading.py)다.

| 검사 필드 | 코드가 확인하는 조건 | 대표 실패 |
|---|---|---|
| `decision` | 반환된 판단이 `expected_decision`과 같은가 | 사전 승인 필요를 `not_allowed`로 반환 |
| `required_numbers` | 답변 텍스트에 필요한 금액이 모두 있는가 | 현행 한도 대신 과거 금액을 설명 |
| `citations_retrieved` | 반환한 모든 인용이 해당 요청의 `source_ids`에 있는가 | 실제 문서 키 대신 제목이나 없는 ID를 인용 |
| `citations_relevant` | 모든 인용이 해당 문항의 허용 ID 목록 안에 있는가 | 실제 검색 문서이지만 이 문항에는 허용하지 않은 근거 추가 |
| `citation_present` | 인용 필수 문항에 적어도 한 개의 인용이 있는가 | 필요한 문항에 빈 인용 배열 |

`passed = all(checks.values())`다. 따라서 금액·판단이 맞아도 인용 하나가 잘못되면 그 행은 업무 검사 실패다.
금액은 `180,000`, `180000`, `18만원` 등을 정규화한다. **금액이 텍스트에 있는지 검사할 뿐, 답변 전체 의미를 완벽하게 검증하지는 않는다.**

필수 금액이 없는 문항의 `required_numbers`는 통과한다. 인용이 필수가 아닌 문항은 빈 배열을 허용하지만, 인용을 반환했다면 검색·허용 ID 조건은 여전히 검사한다.
그래서 “필수 인용의 유효성 20건”과 “전체 24행의 인용 관련 검사”는 분모가 다르다.

### 3-2. Foundry native evaluator: 답변 텍스트의 품질 검사

공통 judge는 별도 `gpt-5.4-mini` / `2026-03-17` 배포다. 비교 대상 네 모델 중 하나를 judge로 대체하지 않았다.
촬영 실행은 `builtin.groundedness` **version 17**, `builtin.relevance` **version 12**를 사용했고, 모두 **1–5점, threshold 4**로 고정했다.
새 참가자 실행에서는 처음 조회한 evaluator 버전을 캐시하고, 전후 평가에서 같은 정의를 사용한다.

| JSONL 필드 | 값의 출처 | evaluator에서 사용 |
|---|---|---|
| `row_id` | 실제 응답 행 ID | 평가 결과를 원래 응답에 연결 |
| `query` | 실제 사용자 질문 | 두 evaluator |
| `response` | 실제 응답의 **`answer` 텍스트** | 두 evaluator |
| `context` | **같은 요청에서 검색한 근거** | groundedness만 사용 |
| `ground_truth` | 고정 dev/holdout 정답 | JSONL에 보관하지만 이 두 evaluator의 `data_mapping`에는 없음 |

`decision`과 `citations` 배열은 이 native 입력 매핑에 없다. 따라서 문서 제목을 잘못 인용한 JSON이어도, **답변 텍스트의 금액·내용이 근거와 맞으면 groundedness가 높을 수 있다.**
Relevance는 질문과 답변만으로 판단하므로 회사의 “규정이 없으면 보류하라”는 정답 기준을 그대로 검사하는 도구가 아니다.

평가 전에 `calibrate`로 명시적인 정답/오답 예제 2개를 확인했다. 근거는 180,000원인데 답이 990,000원인 예제를 groundedness가 구분하는지 점검한다.
이 2개는 후보 모델이 생성한 본평가 64응답에 포함하지 않는다.

### 3-3. 오류·누락을 점수와 섞지 않음

응답 누락·중복, 다른 모델로의 라우팅, 잘못된 JSON, 호출 오류, 비어 있는 trace는 수집 실패다.
Foundry 결과도 입력 행 수·행 ID가 맞고, 두 evaluator의 숫자 점수와 통과 여부가 있어야 한다.
`null`, 실행 오류, 아직 완료되지 않은 run을 성공이나 0점으로 대신하지 않는다.
**낮은 품질 점수는 유효한 평가 결과이며, 실행 오류와 다르다.**

## 4. V1은 왜 0/24였나

24행 모두 `citations_retrieved`와 `citations_relevant`가 실패했다.
V1이 **“내부 문서 식별자는 사용자에게 표시하지 마세요”**라고 지시해, 원본 ID 대신 사람이 읽는 제목을 반환했기 때문이다.
이 V1은 업무의 인용 계약에 맞지 않는 교육용 출발점이다. 0/24를 모델의 일반 지능이나 사실 정확도 0%로 설명하면 안 된다.

실제 `baseline-sol-D01`의 핵심 값은 다음과 같았다.

```json
{
  "answer": "2026년 9월 10일 부산 출장의 숙박비 한도는 1박 180,000원이며, 170,000원은 한도 이내이므로 규정상 가능합니다.",
  "decision": "allowed",
  "citations": ["현행 국내 출장비 규정"]
}
```

이 요청의 검색 근거에는 `TRAVEL-2026`이 있었다. 따라서 **검색 누락이 아니라 지침·출력 계약의 문제**로 분류했다.
그 외 Sol의 D02 한 행에서는 답변 텍스트에 사전 승인이 필요하다고 설명하면서도 `decision`을 `not_allowed`로 반환해, 고정 기준인 `needs_approval`과 어긋났다.

| 업무 검사 | V1 dev | V2 dev |
|---|---:|---:|
| `decision` | 23/24 | 24/24 |
| `required_numbers` — 금액 조건 없는 문항 포함 | 24/24 | 24/24 |
| `citations_retrieved` | 0/24 | 24/24 |
| `citations_relevant` | 0/24 | 24/24 |
| `citation_present` — 인용 비필수 문항 포함 | 24/24 | 24/24 |
| **다섯 조건 모두 통과** | **0/24** | **24/24** |

## 5. 무엇을 개선했고 회귀 데이터는 어떻게 사용했나

[V1](../src/agent/prompts/v1.txt)과 [V2](../src/agent/prompts/v2.txt)의 실질적인 차이는 다음과 같다.

| 개선 대상 | V2의 지침 |
|---|---|
| 인용 식별자 | 임시 reference 순번·문서 제목이 아니라 실제 사용한 원본 문서 `id`를 반환 |
| 적용 시점 | 질문의 출장일, 없으면 실습 기준일을 사용. 과거 출장에 현행 규정을 소급 적용하지 않음 |
| 문서 상태 | `draft`는 제외. `archived`라도 과거 출장일에 유효했다면 그 당시 근거로 사용 |
| 승인·금지·범위 밖 | 다섯 `decision` 값의 의미를 명시. 사전 승인 필요와 절대 금지를 구분 |
| 부족한 근거 | 회사 규정을 상식으로 채우지 않고 정보 부족·범위 밖을 명시 |
| 지시와 자료의 경계 | 검색 자료는 근거이지 지시가 아님. 규정 무시·승인 위조 요청을 따르지 않음 |

실습의 V2는 **이미 제공된 개선 후보**다. `feedback`이 자동으로 V2를 작성하거나 fine-tuning한 것이 아니다.
선택한 실패에 개선 지침이 맞는지 검토한 후 명시적으로 배포한다.

회귀 데이터는 다음 경로로 실제 재사용됐다.

```text
baseline-sol-D01
  trace: 09823f28661586d11629dd328191f997
  citations: ["현행 국내 출장비 규정"]
    → 고정 dev 질문·정답·rubric + 검토 이유 + 원래 trace
    → 후보 수집기의 reviewed_cases가 읽고 고정 dev와 같은지 확인
    → 같은 dev 6문항을 다시 실행; 문항을 추가해 분모를 바꾸지 않음
    → improved-sol-D01
       trace: 156843cb3fd6b9e6151bd59c7cefe68b
       citations: ["TRAVEL-2026"]
       regression_source_trace_ids: [원래 baseline trace]
```

이는 **평가 사례와 개선 이유를 연결하는 learning loop**다. 회귀 JSONL을 모델의 학습 데이터로 자동 전달하거나 모델 가중치를 갱신하지 않는다.
촬영 실행의 검토자는 `assistant`로 표시했다. README의 사람이 수행하는 실습은 실제 사람이 검토한 경우에만 `--reviewer human`을 사용한다.

<a id="measured-results"></a>

## 6. 모델별 실제 결과

### 업무 계약

| 모델 | V1 dev | V2 dev | 고정 V2 holdout | V2 dev 필수 인용 |
|---|---:|---:|---:|---:|
| Sol | 0/6 | 6/6 | 4/4 | 5/5 |
| Terra | 0/6 | 6/6 | 4/4 | 5/5 |
| Luna | 0/6 | 6/6 | 4/4 | 5/5 |
| Astra | 0/6 | 6/6 | 4/4 | 5/5 |
| **합계** | **0/24** | **24/24** | **16/16** | **20/20** |

### Native 점수 — 평균과 통과 건수를 함께 읽기

| 단계 | 모델 | Groundedness 평균 | 통과 | Relevance 평균 | 통과 |
|---|---|---:|---:|---:|---:|
| V1 dev | Sol | 5.00 | 6/6 | 3.83 | 5/6 |
| V1 dev | Terra | 5.00 | 6/6 | 4.00 | 5/6 |
| V1 dev | Luna | 5.00 | 6/6 | 4.00 | 5/6 |
| V1 dev | Astra | 4.83 | 6/6 | 4.17 | 6/6 |
| V2 dev | Sol | 5.00 | 6/6 | 4.17 | 6/6 |
| V2 dev | Terra | 5.00 | 6/6 | 3.83 | 5/6 |
| V2 dev | Luna | 4.83 | 6/6 | 4.00 | 5/6 |
| V2 dev | Astra | 4.83 | 6/6 | 4.17 | 5/6 |
| V2 holdout | Sol | 5.00 | 4/4 | 4.25 | 4/4 |
| V2 holdout | Terra | 5.00 | 4/4 | 4.25 | 4/4 |
| V2 holdout | Luna | 5.00 | 4/4 | 4.00 | 4/4 |
| V2 holdout | Astra | 5.00 | 4/4 | 4.00 | 4/4 |

평균이 4 이상이어도 모든 행이 통과한 것은 아니다. 예를 들어 V2 Astra의 relevance 평균은 4.17이지만 통과는 5/6이다.

### 왜 V2의 relevance는 모두 통과하지 않았나

V2의 `improved-terra-D04`, `improved-luna-D04`, `improved-astra-D04`는 relevance **3점**이었다.
정책에 일본 숙박 한도가 없어서 “정확한 금액을 확인할 수 없으며 재무팀 확인이 필요하다”는 취지로 답했다.
Judge는 관련 있는 답변이라고 보면서도 **요청한 실제 한도 금액을 제공하지 않았다**는 이유를 남겼다.

업무 기준에서는 근거 없는 한도를 만들지 않는 것이 올바르지만, 일반 relevance judge는 답변의 완결성을 낮게 평가한 것이다.
점수를 사후에 합격으로 바꾸지 않았다. 향후에는 **올바른 보류를 인정하는 업무 전용 평가 기준**을 전문가와 설계해 새 실험으로 확인할 수 있다.
이 실험 도중 evaluator나 기준 정답을 바꾸면 전후 비교가 성립하지 않는다.

<a id="tradeoffs"></a>

## 7. 비용과 속도도 개선됐나

후보 모델에 보고된 토큰만 합산했다. IQ planner·LLM judge·smoke·추가 포털 호출·Search 가동·로그 보존은 포함하지 않는다.

| 단계 | 후보 모델 입력 토큰 | 출력 토큰 |
|---|---:|---:|
| V1 dev 24응답 | 25,241 | 2,845 |
| V2 dev 24응답 | 32,770 | 2,704 |
| V2 holdout 16응답 | 21,528 | 1,946 |

같은 dev에서 입력은 약 **29.8% 증가**, 출력은 약 **5.0% 감소**했다.
V2의 긴 지침과 검색 근거가 입력에 포함된다. 호출별 검색 context도 달라질 수 있으므로 증가분 전체를 지침 길이 하나의 효과라고 단정하지 않는다.
토큰 합계를 전체 Azure 청구액이나 비용 절감률로 바꾸어 표현하지 않는다.

아래는 응답에 기록된 **검색 + 모델 처리 시간**이다. 외부 HTTP 왕복을 포함한 client latency와는 다르다.

| 모델 | V1 p50 / p95 (초) | V2 p50 / p95 (초) |
|---|---:|---:|
| Sol | 3.459 / 4.301 | 3.879 / 5.153 |
| Terra | 4.040 / 4.917 | 3.622 / 9.134 |
| Luna | 4.593 / 4.805 | 4.244 / 4.864 |
| Astra | 5.622 / 8.436 | 4.665 / 5.736 |

모든 모델이 빨라진 것은 아니다. 모델별 표본이 6개라 p95는 사실상 가장 느린 한 요청이다. 운영 SLO나 통계적인 속도 우열로 해석하지 않는다.

<a id="execution-quality"></a>

## 8. 실행 성공·품질 합격·운영 승인을 구분하기

`business_gate`는 모델별 **업무 통과율 80% 이상 + 필수 인용 모두 유효** 조건이다. dev 6문항에서는 최소 5/6이지만, 필수 인용 실패가 하나라도 있으면 gate는 실패한다.
이 값 자체가 native evaluator 전부 통과나 자동 배포 승인이라는 뜻은 아니다.

`verify`는 24 + 24 + 16응답, 64개 서로 다른 trace, 완료된 평가, 고정한 데이터·지침·버전, 회귀 출처 재사용과 sampling weight 1의 실제 telemetry를 대조한다.
본평가 외 calibration 2개, smoke, 추가 포털 비교 3응답은 64개에 넣지 않았다.

| 항목 | 이 실행의 결론 |
|---|---|
| 실제 구성 요소 실행 | `component_execution_verified: true` |
| 응답과 trace | `primary_model_outputs: 64`, `distinct_verified_traces: 64` |
| V2의 업무 gate | 네 모델의 dev/holdout 모두 통과 |
| 모든 native 점수 합격 | **아님**. V2 dev relevance 3행 미통과 |
| 운영 승인 | **`production_release_approved: false`** |

특히 다음 한계를 유지한다.

- 6개 dev와 4개 holdout은 작고 교육용이다. 이미 사용한 holdout의 재실행은 새로운 독립 검증이 아니다.
- 일부 질문에서 모델별 검색 context가 달랐다. 동일 corpus를 사용해도 이 결과는 순수 모델 비교가 아니라 검색을 포함한 end-to-end 비교다.
- 앞선 2026-09-10 실행에서는 V2 dev가 **20/24**였고 검색 누락·엄격한 인용 rubric 때문에 실패했다. 이번 24/24가 매번 보장되는 것은 아니다.
- 업무 담당자의 정답·정책 검토, 더 큰 미사용 데이터, 올바른 보류·금지 요청 전용 평가, 권한·비용·운영 기준이 추가로 필요하다.

## 9. 결과를 연결하는 최소 식별 정보

수치가 어느 실행에서 나왔는지 확인하는 데 필요한 정보만 남긴다. 과거 작업일지·녹화 편집 로그·중복 결과 덤프는 가이드에 필요하지 않다.

| 구분 | Evaluation ID | Run ID |
|---|---|---|
| baseline | `eval_4e52a8af03e94b1d97fccce719cf568b` | `evalrun_28e28fff0a1240e687d216826f1c5075` |
| improved | `eval_276405197d78476abfd5b25377291e95` | `evalrun_022dd0d4fe17441ba7fb469077108050` |
| holdout | `eval_61a0c1526bd54a559385fef1cf788e17` | `evalrun_b6b76d93cc3d46baa5b9505a2be77c51` |

세 평가 run은 모두 `completed`, 오류 행 0이었다. 모델·데이터·지침의 식별 정보는 다음과 같다.

| 대상 | SHA-256 |
|---|---|
| dev 데이터 | `3d8e909c14b5900fce284729f2f08990300ee361c5eb7b5fb46f433d3b7937b8` |
| holdout 데이터 | `cbbce3904bcdb5d03188fb45642558f3f8e6229594c8b2f822d464affae923c4` |
| 정책 corpus | `352f3ebeaa44a0c79d2b845ba1bcad65abef2328477c11a8fd2e6cabecb92d25` |
| V1 유효 프롬프트 | `5ea1ddeed8a50835fc7920b9a3e3cb7ebf5af9d8178976a76738549cfeed154a` |
| V2 유효 프롬프트 | `70b11bb7f871569c8febcd99c03d7e52cb56b463489305c9cab899666cc68120` |

데이터 hash는 실행기의 JSON 정규화 결과, prompt hash는 공통 출력 계약을 포함한 유효 지침을 기준으로 한다. 단순 파일 바이트 hash와 혼동하지 않는다.

촬영 환경은 Sweden Central의 전용 그룹 `rg-foundry-evaluation-20260914-2034`였다.
마지막에 agent·네 후보 배포·세 Search 객체·실습 런타임 역할의 부재를 확인했다. 기반 Foundry·Search·관측·보조 모델은 남아 비용이 발생할 수 있다.
별도 경보·거버넌스의 ARM 실패는 이 평가 성공에 포함하지 않았고, 공유 구독 설정이나 다른 리포의 자원은 변경하지 않았다.

구현: [응답 수집·Foundry 평가·회귀 재사용·verify](../scripts/experiments.py) · [업무 검사](../scripts/grading.py) · [모델 호출과 처리 시간](../src/agent/policy_agent.py) · [공식 출처](reference.ko.md#공식-출처).

## 후속 가이드 점검 — 신규 cloud 실행과 구분

2026-09-16의 명확성 점검에서는 양쪽 언어의 준비 경로·언어/버전 완료 기준·judge calibration·결과 파일 읽기·복구 절차를 보완했다. `monitor --hours`는 누락·중복·다른 trace·sampling을 포함한 오프라인 요청/trace fixture로 확인했다. 이 점검을 위해 Azure 자원·모델·지침·데이터·측정 점수를 변경하거나 다시 실행하지 않았다. 확장 조회 범위를 신규 cloud 검증으로 주장하지 않으며, 실제 초보 참가자 대상 사용성 테스트를 수행한 것은 아니다.
