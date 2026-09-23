# 레벨 2: Foundry가 업무 계약을 평가하게 만들기

[English](level-2.en.md) · [메인 가이드로 돌아가기](../README.ko.md#levels) · [요약 영상 11:59부터](../README.ko.md#summary-video)

**약 40분 동안 하는 일:**

1. 다섯 업무 검사를 **Foundry custom 코드 평가기**로, 정책 기준을 **rubric 평가기**로 등록합니다.
2. 저장된 V1·V2 응답을 **평가기 9개로 한 eval group에서** 평가합니다.
3. Foundry의 **run 비교(통계 검정)**와 **실패 클러스터**를 읽습니다.

**준비:** 같은 폴더에서 [메인 가이드](../README.ko.md)의 1–9단계를 마쳤고, **10단계는 아직 실행하지 않았어야 합니다.** 정리 단계에서 여기서 만든 평가기도 삭제됩니다. 새 에이전트 응답은 수집하지 않고 judge 모델만 호출합니다.

**이 레벨이 필요한 이유:** 촬영 실행의 7단계에서 업무 통과는 0/18 → 18/18로 바뀌었지만 Foundry groundedness는 18/18 그대로였습니다. 업무 결과는 로컬 Python이 계산했습니다. 여기서는 Foundry가 그 계약을 직접 측정하게 하고, 다른 평가기 유형과 나란히 비교합니다.

<a id="register-evaluators"></a>

## 1. custom 평가기 두 개 등록

**터미널 A:**

```bash
python scripts/workshop.py register-evaluators
```

**완료 확인:** `Registered <LAB_PREFIX>-business-contract version 1 (code)`와 `Registered <LAB_PREFIX>-policy-rubric version 1 (rubric)` 두 줄이 나옵니다. 다시 실행하면 `Reusing ...`이 나오고 아무것도 새로 만들지 않습니다.
**다르면:** `already exists and is not owned by this folder`는 다른 조가 같은 `LAB_PREFIX`를 쓴다는 뜻이므로 강사에게 다른 이름을 받습니다. 그 밖의 오류는 [레벨 2·3 복구](troubleshooting.ko.md#levels)를 봅니다.

<details>
<summary>두 평가기의 내용</summary>

| 평가기 | 유형 | 채점 내용 | 통과 기준 |
|---|---|---|---|
| `<LAB_PREFIX>-business-contract` | 코드(Foundry에서 Python 실행) | `scripts/grading.py`와 같은 다섯 검사: 판단값, 필수 금액, 검색된 인용, 허용된 인용, 필요한 인용의 존재 | 통과한 검사의 비율이 점수이며, 1.0일 때만 통과 |
| `<LAB_PREFIX>-policy-rubric` | Rubric(LLM judge) | 가중치가 있는 다섯 차원: 유효한 정책 적용, 정책에 맞는 판단, 문서 ID 인용, 범위 밖이면 보류, 규정 우회 거부 | 차원별 1–5점을 가중 정규화해 0.7 이상이면 통과 |

두 평가기는 프로젝트의 평가기 카탈로그에 `LAB_PREFIX`를 붙여 만들어지고, 정리할 수 있도록 이 폴더의 소유권 기록에 남습니다. 정의는 `scripts/foundry_eval.py`에 있습니다.

</details>

<a id="evaluate-suite"></a>

## 2. 평가기 9개로 V1·V2 평가

**터미널 A:** 저장된 `baseline`·`improved` 응답을 읽어 한 eval group에서 차례로 실행합니다. 몇 분 걸립니다.

```bash
python scripts/workshop.py evaluate-suite --labels baseline improved
```

**완료 확인:** `Suite evaluation completed: ... (baseline, improved)`, 9행짜리 표, `Portal:` 링크가 나옵니다. `business_contract` 행은 7-4 요약의 업무 통과 수와 같습니다.
**다르면:** `evaluator results failed, for example because the judge hit its rate limit`는 공유 judge가 바빴다는 뜻이므로 같은 명령에 `--retry-failed`를 붙여 다시 실행합니다. 시간 초과 메시지는 아직 실행 중이라는 뜻이므로 같은 명령을 다시 실행해 이어 갑니다.

**표는 세 부분으로 읽습니다.**

- **내 계약(`business_contract`)**은 로컬 업무 검사를 Foundry 안에서 그대로 재현합니다.
- **같은 rubric이라도 근거가 있고 없음에 따라** 다릅니다. `policy_rubric`은 질문과 검색된 정책 본문을 받고, `policy_rubric_no_evidence`는 질문만 받습니다. judge는 매핑해 준 것만 봅니다.
- **범용 평가기**(`groundedness`, `relevance`, `response_completeness`, `task_adherence`, `intent_resolution`, 안전 평가기 `indirect_attack`)는 거의 움직이지 않습니다. 내 계약을 모르기 때문입니다.

<details>
<summary>촬영한 한국어 응답(2026-09-23)의 결과 — 내 목표 점수가 아닌 예시</summary>

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

`business_contract`는 촬영 실행의 로컬 결과(0/18 → 18/18)와 같습니다. 영문 응답을 같은 입력으로 한 번 더 평가했을 때 `business_contract`는 그대로였고, LLM이 판정하는 항목은 1–3행 달라졌습니다(예: baseline의 `policy_rubric` 7/18 → 10/18). LLM 판정 항목은 한 행이 아니라 방향으로 비교합니다. 영문 실행에서는 V2의 Sol D02 판단값 오류를 `business_contract`만 잡고 `policy_rubric`은 통과시켰습니다. 결정적인 계약 검사와 LLM rubric이 서로를 보완하는 이유입니다.

</details>

<details>
<summary>평가기 9개와 각각이 받는 입력</summary>

| 항목 | 유형 | 받는 입력 | 기본 통과 기준 |
|---|---|---|---|
| `business_contract` | custom 코드 | 행의 모든 필드: 판단값, 금액, 인용, 검색된 ID, 허용 ID | 다섯 검사 모두 통과 |
| `policy_rubric` | custom rubric | 질문 **+ 검색된 근거**, 답변·판단·인용 | 0.7 |
| `policy_rubric_no_evidence` | custom rubric | 질문만, 답변·판단·인용 | 0.7 |
| `groundedness` | 기본 제공 RAG | 질문, 답변 텍스트, 검색된 근거 | 5점 중 4점 |
| `relevance` | 기본 제공 RAG | 질문, 답변 텍스트 | 5점 중 4점 |
| `response_completeness` | 기본 제공 품질 | 답변 텍스트, 고정 정답 | 5점 중 3점 |
| `task_adherence` | 기본 제공 agent | 질문, 답변 텍스트 | 통과/실패 |
| `intent_resolution` | 기본 제공 agent | 질문, 답변 텍스트 | 5점 중 3점 |
| `indirect_attack` | 기본 제공 안전 | 질문, 답변 텍스트 | 조작된 내용 없음 |

자세히: [기본 제공 평가기](https://learn.microsoft.com/azure/foundry/concepts/built-in-evaluators) · [custom 평가기](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/custom-evaluators) · [rubric 평가기](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/rubric-evaluators)

</details>

<a id="insights"></a>

## 3. run 비교와 실패 클러스터

**터미널 A:**

```bash
python scripts/workshop.py insights --baseline baseline --candidate improved
```

**완료 확인:** 아홉 항목의 `delta`·`p`·`effect`가 담긴 `Comparison (candidate vs baseline):` 표에 이어, `Failure clusters in the candidate run [evaluator that failed each sample]:` 목록 또는 `none`이 나옵니다.
**다르면:** `Run evaluate-suite ... first`는 2절이 아직 끝나지 않았다는 뜻입니다. 시간 초과는 인사이트를 아직 만드는 중이라는 뜻이고, `... insight failed`는 인사이트 하나를 만들지 못했다는 뜻입니다. 두 경우 모두 같은 명령을 다시 실행합니다.

**읽는 법:**

- **`effect`**는 두 run에 대한 Foundry의 통계 검정입니다. `Changed`는 유의한 차이(p가 0.05 이하), `Inconclusive`는 행이 너무 적거나 p가 0.05 이상이라는 뜻입니다. run당 18행이라 큰 변화만 유의하게 나옵니다.
- **각 클러스터에는 그 실패를 낸 평가기가 표시됩니다.** 샘플 대부분이 `policy_rubric_no_evidence`에서 왔다면, 그 클러스터는 에이전트의 실제 문제가 아니라 근거 없이 채점한 judge의 문제를 묘사한 것입니다. 제안을 따르기 전에 출처부터 확인합니다.

<details>
<summary>촬영한 한국어 인사이트 — 예시</summary>

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

## 4. 선택: 포털에서 run 비교

**포털:** 2절의 `Portal:` 링크를 열고 `baseline-...`과 `improved-...` run을 선택한 뒤 **Compare**를 누릅니다. 비교 화면은 같은 통계 검정을 쓰며 셀마다 효과를 색으로 표시합니다([공식 안내](https://learn.microsoft.com/azure/foundry/how-to/evaluate-results#compare-the-evaluation-results)).

**완료 확인:** 평가기마다 두 run이 나란히 보이고, custom 평가기는 `LAB_PREFIX`가 붙은 이름으로 보입니다.
**다르면:** 3절의 CLI 표를 사용하고 [포털 화면 차이](troubleshooting.ko.md#portal-differs)를 봅니다.

## 레벨 2 마무리

보고에 **어떤 평가기가 어떤 질문에 답하는지** 한 문장을 더합니다. 예를 들어, 통과 여부는 계약 검사가 정하고, 근거가 있는 rubric은 품질을 설명하며, 범용 평가기와 안전 평가기는 각자 설계된 회귀를 감시합니다.

**다음:** [레벨 3](level-3.ko.md)으로 가거나 [10단계 정리](../README.ko.md#cleanup)로 돌아갑니다. 정리하면 이 레벨의 custom 평가기도 삭제되고, eval group과 결과는 증거로 남습니다.
