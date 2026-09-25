# 레벨 2: 내 업무 규칙을 Foundry로 평가하기

[English](level-2.en.md) · [메인 가이드로 돌아가기](../README.ko.md#levels) · [요약 영상 12:26부터](../README.ko.md#summary-video)

**약 40분 뒤에는:** 저장된 같은 V1·V2 응답 36개를 비교한 표와, **업무 검사와 LLM 점수를 구분한 해석**이 남습니다.

**순서:** [1. 평가기 두 개 등록](#register-evaluators) → [2. 저장된 응답 채점](#evaluate-suite) → [3. judge 확인](#judge-agreement) → [4. 실행 결과와 실패 원인 비교](#insights) → [보고](#finish-level-2).

| 시작 전 확인 | 필요한 상태 |
|---|---|
| 기본 실습 | 같은 폴더에서 1–9단계 완료. **10단계 정리는 아직 실행하지 않음** |
| 입력 | 저장된 `baseline`·`improved` 각 18응답. `holdout`은 사용하지 않음 |
| 비용 | judge 추가 호출. **새 에이전트 응답은 만들지 않음** |
| 마친 뒤 | [레벨 3](level-3.ko.md) 또는 [10단계 정리](../README.ko.md#cleanup). 10단계 정리는 여기서 만든 사용자 지정 평가기도 삭제합니다 |

**실행 위치:** 기존 **터미널 A**에서 **저장소 루트**로 실행합니다. 새 터미널이면 [환경만 복원](../README.ko.md#resume-shell)합니다. `.env`의 이름과 V2 지침은 바꾸지 않습니다. 복구 때 다른 label을 썼다면 아래 `baseline`·`improved`를 실제 label로 바꿉니다.

**2절에서는 통과 건수, 3절에서는 judge 일치도, 4절에서는 평균 점수와 실패 원인을 읽습니다.** 셋 다 보고에 넣습니다. 예시 점수와 선택 포털 화면은 필수 단계가 아닙니다.

<a id="register-evaluators"></a>

## 1. 사용자 지정 평가기 두 개 등록

**터미널 A:**

```bash
python scripts/workshop.py register-evaluators
```

**완료 확인:** `Registered <LAB_PREFIX>-business-contract version 1 (code)`와 `Registered <LAB_PREFIX>-policy-rubric version 1 (rubric)` 두 줄이 나옵니다. 다시 실행하면 `Reusing ...`이 나오고 아무것도 새로 만들지 않습니다.

**다르면:** `already exists and is not owned by this folder`이면 멈추고 강사와 소유권 충돌을 확인합니다. 지금 `.env`의 `LAB_PREFIX`를 바꾸거나 다른 조의 평가기를 삭제하지 않습니다. [레벨 2·3 복구](troubleshooting.ko.md#levels)

**읽는 법:** 이제 프로젝트에 재사용 가능한 평가기 두 개가 있습니다. 다섯 업무 검사를 그대로 실행하는 코드 평가기와, LLM judge가 정책 품질을 채점하는 rubric 평가기입니다.

<details>
<summary>두 평가기의 내용</summary>

| 평가기 | 유형 | 채점 내용 | 통과 기준 |
|---|---|---|---|
| `<LAB_PREFIX>-business-contract` | 코드(Foundry에서 Python 실행) | `scripts/grading.py`와 같은 다섯 검사: 판단값, 필수 금액, 검색된 인용, 허용된 인용, 필요한 인용의 존재 | 통과한 검사의 비율이 점수이며, 1.0일 때만 통과 |
| `<LAB_PREFIX>-policy-rubric` | Rubric(LLM judge) | 가중치가 있는 다섯 차원: 유효한 정책 적용, 정책에 맞는 판단, 문서 ID 인용, 범위 밖이면 보류, 규정 우회 거부 | 차원별 1–5점을 가중 정규화해 0.7 이상이면 통과 |

두 평가기는 프로젝트의 evaluator catalog에 `LAB_PREFIX`를 붙여 만들어지고, 정리할 수 있도록 이 폴더의 소유권 기록에 남습니다. 정의는 `scripts/foundry_eval.py`에 있습니다.

</details>

**다음:** [2. 저장된 V1·V2 평가](#evaluate-suite)

<a id="evaluate-suite"></a>
<a id="2-평가기-9개로-v1v2-평가"></a>

## 2. 평가 항목 9개로 V1·V2 채점

**필요한 등록은 이미 끝났습니다.** 이 suite는 **평가 항목 9개**를 채점합니다. 1절의 사용자 지정 평가기 2개, 기본 제공 평가기 6개, 같은 rubric을 검색 근거 없이 실행하는 `policy_rubric_no_evidence`입니다.

**터미널 A:** 저장된 `baseline`·`improved` 응답을 한 eval group으로 평가합니다. 몇 분 걸립니다.

```bash
python scripts/workshop.py evaluate-suite --labels baseline improved
```

**완료 확인:** `Suite evaluation completed: ... (baseline, improved)`, 9행짜리 표, `Portal:` 링크가 나옵니다. `business_contract` 행은 7-4 요약의 업무 통과 수와 같습니다.

**다르면:** `The suite is still running`으로 명령이 끝났다면 같은 명령으로 저장된 run을 이어갑니다. 아직 터미널에서 실행 중이면 기다립니다. 그 밖의 오류는 [레벨 2·3 복구](troubleshooting.ko.md#levels)를 봅니다.

<details>
<summary>실패한 run 재시도 — 실패·오류 행이 확인된 경우에만</summary>

결과가 실패했다면 저장된 오류부터 확인합니다. 속도 제한은 가능한 원인 중 하나일 뿐입니다. 429라면 `Retry-After`만큼 기다린 뒤 실행합니다.

```bash
python scripts/workshop.py evaluate-suite --labels baseline improved --retry-failed
```

실패한 run만 교체하며 이전 시도는 남습니다. 낮은 유효 점수에는 쓰지 않습니다. 같은 오류가 반복되면 멈추고 강사에게 전달합니다.

</details>

**내 표에서 읽을 순서:**

1. **`business_contract`부터 봅니다.** V1 → V2 통과 건수를 적고 7-4의 로컬 업무 검사와 같은지 확인합니다.
2. **`policy_rubric`과 `policy_rubric_no_evidence`를 비교합니다.** `policy_rubric`은 질문과 검색된 정책 본문을 받고, `policy_rubric_no_evidence`는 질문만 받습니다. 같은 rubric이라도 judge에게 근거를 주었을 때와 안 주었을 때 통과 건수가 달랐는지 적습니다.
3. **기본 제공 품질·에이전트·RAG·안전 평가기의 변화 하나를 적습니다**(없으면 `none`). 이 점수들은 판단·금액·인용을 보는 업무 검사를 대신하지 않습니다.

<details>
<summary>기록된 예시 실행(2026-09-23 한국어 응답) — 내 목표 점수가 아닌 예시</summary>

```text
criterion                  kind     baseline  improved
business_contract          code     0/18      18/18
policy_rubric              rubric   10/18     18/18
policy_rubric_no_evidence  rubric   0/18      9/18
groundedness               RAG      18/18     18/18
relevance                  RAG      16/18     15/18
response_completeness      quality  18/18     18/18
task_adherence             agent    16/18     16/18
intent_resolution          agent    16/18     16/18
indirect_attack            safety   18/18     18/18
```

`business_contract`는 기록된 예시 실행의 로컬 결과(0/18 → 18/18)와 같습니다. LLM 판정 항목은 같은 저장 응답을 다시 평가해도 1–3행 달라질 수 있습니다. 실패 행을 직접 확인하고, 결정적인 업무 검사와 LLM rubric을 함께 봅니다. 작은 실행 한 번만으로 개선을 단정하지 않습니다.

</details>

<details>
<summary>평가 항목 9개와 각각이 받는 입력</summary>

| 항목 | 유형 | 받는 입력 | 기본 통과 기준 |
|---|---|---|---|
| `business_contract` | 사용자 지정 코드 | 행의 모든 필드: 판단값, 금액, 인용, 검색된 ID, 허용 ID | 다섯 검사 모두 통과 |
| `policy_rubric` | 사용자 지정 rubric | 질문 **+ 검색된 근거**, 답변·판단·인용 | 0.7 |
| `policy_rubric_no_evidence` | 사용자 지정 rubric | 질문만, 답변·판단·인용 | 0.7 |
| `groundedness` | 기본 제공 RAG | 질문, 답변 텍스트, 검색된 근거 | 5점 중 4점 |
| `relevance` | 기본 제공 RAG | 질문, 답변 텍스트 | 5점 중 4점 |
| `response_completeness` | 기본 제공 품질 | 답변 텍스트, 고정 정답 | 5점 중 3점 |
| `task_adherence` | 기본 제공 에이전트 | 질문, 답변 텍스트 | 통과/실패 |
| `intent_resolution` | 기본 제공 에이전트 | 질문, 답변 텍스트 | 5점 중 3점 |
| `indirect_attack` | 기본 제공 안전 | 질문, 답변 텍스트 | 조작된 내용 없음 |

자세히: [기본 제공 평가기](https://learn.microsoft.com/azure/foundry/concepts/built-in-evaluators) · [사용자 지정 평가기](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/custom-evaluators) · [rubric 평가기](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/rubric-evaluators)

</details>

**다음:** [3. judge와 업무 검사 결과 비교](#judge-agreement)

<a id="judge-agreement"></a>

## 3. judge와 업무 검사 결과 비교

**터미널 A:** 2절의 모든 LLM judge를 정확한 업무 검사인 `business_contract`와 같은 실제 응답 36개에서 비교합니다. 5-1에서는 직접 작성한 예제 2개로만 judge를 확인했습니다. 이 명령은 저장된 결과만 읽고 새 호출은 하지 않습니다.

```bash
python scripts/workshop.py judge-agreement --labels baseline improved
```

**완료 확인:** `Judge agreement with business_contract on 36 saved rows (baseline, improved); no new calls.`, judge 일곱 행의 표가 나오고, 이어서 row ID 또는 `none`이 붙은 `Business passes that a judge failed`가 나옵니다.

**다르면:** `Run evaluate-suite ... first`, `No saved suite output`, `has no valid ... result`이면 먼저 2절을 끝냅니다([레벨 2·3 복구](troubleshooting.ko.md#levels)).

**읽는 법:**

- **`judge pass + business fail`:** 업무 검사에서 실패한 답변을 judge가 통과시켰습니다. 이 수가 많은 judge는 업무 검사를 대신할 수 없습니다.
- **`judge fail + business pass`:** 올바른 답변을 judge가 떨어뜨렸습니다. 그 judge로 릴리스를 막기 전에, 2절 포털 run에서 목록의 행마다 답변과 judge의 이유를 읽습니다. 올바른 보류가 relevance에서 낮게 나온 것은 judge의 한계이지 에이전트 실패가 아닙니다.
- **judge를 결과에 맞추지 않습니다.** 기준값, rubric, 기준 정답은 그대로 두고, 릴리스를 막을 judge와 진단용으로만 쓸 judge를 메모합니다.

<details>
<summary>기록된 예시 실행의 결과 — 예시</summary>

```text
Judge agreement with business_contract on 36 saved rows (baseline, improved); no new calls.
criterion                  kind     agree  judge pass + business fail  judge fail + business pass
policy_rubric              rubric   26/36  10                          0
policy_rubric_no_evidence  rubric   27/36  0                           9
groundedness               RAG      18/36  18                          0
relevance                  RAG      17/36  16                          3
response_completeness      quality  18/36  18                          0
task_adherence             agent    18/36  16                          2
intent_resolution          agent    18/36  16                          2
Business passes that a judge failed (review each):
  policy_rubric_no_evidence: improved-sol-D01, improved-sol-D02, improved-luna-D02, improved-sol-D03, improved-luna-D03, improved-astra-D03, improved-astra-D04, improved-luna-D05, improved-astra-D05
  relevance: improved-luna-D04, improved-sol-D04, improved-astra-D04
  task_adherence: improved-luna-D05, improved-sol-D05
  intent_resolution: improved-sol-D06, improved-astra-D06
```

업무 실패 18건은 모두 V1 행입니다. 기본 제공 judge 다섯 개는 그중 16–18건을 통과시켰으므로 어느 것도 업무 검사를 대신할 수 없습니다. `policy_rubric`은 올바른 답변을 하나도 떨어뜨리지 않았지만 업무 실패 10건을 통과시켰습니다. 근거가 없으면 같은 rubric이 올바른 V2 답변 9건을 떨어뜨렸고, relevance는 올바르게 보류한 V2 D04 세 행을 모두 떨어뜨렸습니다.

</details>

**다음:** [4. 실행 결과와 실패 클러스터 비교](#insights)

<a id="insights"></a>

## 4. 실행 결과와 실패 클러스터 비교

**터미널 A:** Foundry가 2절의 `baseline`·`improved` run을 비교하고, `improved` run의 실패를 클러스터로 묶습니다.

```bash
python scripts/workshop.py insights --baseline baseline --candidate improved
```

**완료 확인:** 출력에 다음이 차례로 나옵니다.

1. 아홉 항목의 `delta`·`p`·`effect`가 담긴 `Comparison (candidate vs baseline):` 표
2. `Failure clusters in the candidate run [evaluator that failed each sample]:` 목록 또는 `none`

**다르면:** `Run evaluate-suite ... first`이면 2절의 완료 확인으로 돌아갑니다. `Insights are still generating`으로 종료됐다면 같은 명령으로 이어갑니다. `... insight failed`이면 [오류별 복구](troubleshooting.ko.md#levels)를 따릅니다.

**읽는 법:**

- **2절은 통과 건수, 이 절은 평균 점수입니다.** `delta`는 candidate − baseline입니다. `business_contract` 평균 `0.60`은 일부 검사가 맞았다는 뜻이지, 응답의 60%가 통과했다는 뜻이 아닙니다.
- **`Changed`는 차이이지 개선 판정이 아닙니다.** `delta`, 평가기의 좋은 방향, 18행이라는 작은 표본을 함께 봅니다([통계 비교 범례](https://learn.microsoft.com/azure/foundry/how-to/evaluate-results#compare-the-evaluation-results)).
- **클러스터는 실패한 평가기부터 봅니다.** `policy_rubric_no_evidence` 실패가 많으면 judge가 근거를 못 봤을 수 있습니다. `business_contract` 실패는 어떤 업무 검사가 틀렸는지 확인합니다.

<details>
<summary>기록된 예시 실행의 인사이트 — 예시</summary>

```text
criterion                  baseline  candidate  delta  p      effect
business_contract          0.60      1.00       +0.40  0.000  Changed
policy_rubric              0.70      0.91       +0.22  0.000  Changed
policy_rubric_no_evidence  0.21      0.59       +0.37  0.000  Changed
groundedness               5.00      4.94       -0.06  0.324  Inconclusive
relevance                  3.94      4.11       +0.17  0.380  Inconclusive
```

V2에서 클러스터로 묶인 16개 샘플 중 9개가 `policy_rubric_no_evidence`에서 나왔습니다. 예를 들어 `unsupported_policy_assertions` 클러스터는 어떤 정책이 유효한지 judge가 볼 수 없었기 때문에 생겼습니다.

</details>

**다음:** [레벨 2 마무리](#finish-level-2). 선택 사항으로, 정리 전에 [포털에서 run 비교](#선택-포털에서-run-비교)로 한 번 더 확인할 수 있습니다.

<a id="finish-level-2"></a>

## 레벨 2 마무리

**보고 메모:** 아래 형식을 [9-3의 보고](../README.ko.md#finish)에 복사하고 **내 결과**로 채웁니다. 명령이 아닙니다.

```text
업무 검사: .../18 → .../18; 근거 있는 rubric: .../18 → .../18
릴리스를 막을 judge: ...; 진단용 judge: ... (judge 일치도)
범용·안전 평가기로 알게 된 점: ...
비교/클러스터: 평가기=...; delta/effect=...; 확인한 실패 원인 또는 실패 없음=...
```

**완료 확인:** 1–4절이 끝났고, 메모에는 통과 건수와 평균 점수를 구분한 내 결과·해석이 있습니다. 낮은 점수는 미완료가 아니지만 명령 오류로 빠진 결과는 미완료로 기록합니다.

**다르면:** 끝나지 않은 첫 절로 돌아가 그 명령만 이어갑니다. 끝난 명령은 반복하지 않습니다([레벨 2·3 복구](troubleshooting.ko.md#levels)).

**다음:** [레벨 3](level-3.ko.md)으로 가거나 [10단계 정리](../README.ko.md#cleanup)로 돌아갑니다. 정리하면 이 레벨의 사용자 지정 평가기도 삭제되고, eval group과 결과는 증거로 남습니다.

<a id="선택-포털에서-run-비교"></a>

<details>
<summary>선택: 포털에서 run 비교 — 추가 확인이 필요할 때만</summary>

**포털:** 2절의 `Portal:` 링크를 엽니다. eval group에 `baseline-...`과 `improved-...` run이 평가 항목별 열과 함께 보입니다.

**예시 화면:** eval group에서 두 run을 선택한 모습입니다. 선택한 위 두 run이 2절의 기록 표와 같은 결과이고, 아래 두 행은 judge 속도 제한으로 일부 결과가 빠진 이전 시도입니다.

![baseline과 improved run을 선택한 eval group](assets/levels-20260923/ko-l2-runs.webp)

**완료 확인:** 두 run이 `Completed`이고, `business_contract` 열이 2절의 CLI 표와 같습니다.

**다르면:** CLI 표를 사용하고 [포털 화면 차이](troubleshooting.ko.md#portal-differs)를 봅니다.

통계 비교 화면은 두 run을 선택한 뒤 **Compare runs**를 누르고, **Baseline**으로 `baseline-...` run을 고릅니다([공식 안내](https://learn.microsoft.com/azure/foundry/how-to/evaluate-results#compare-the-evaluation-results)). retry 시도가 보이면 CLI 표와 일치하는 최신 `Completed` `baseline-...`·`improved-...` run 두 개를 선택합니다.

</details>
