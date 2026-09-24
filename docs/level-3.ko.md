# 레벨 3: 릴리스 절차처럼 평가 운영하기

[English](level-3.en.md) · [메인 가이드로 돌아가기](../README.ko.md#levels) · [요약 영상 12:21부터](../README.ko.md#summary-video)

**약 70분 뒤 남길 것:** 평가 대상별 결과표 한 장, 연속 평가의 첫 실행 결과, 릴리스 gate의 종료 코드입니다. **모델 단독·에이전트·trace 평가는 대상과 입력이 다르므로 점수를 한데 합치지 않습니다.**

**준비:** 같은 폴더에서 [레벨 2](level-2.ko.md)를 마쳤고, **10단계는 아직 실행하지 않았어야 합니다.** 마친 뒤에는 [10단계](../README.ko.md#cleanup)로 돌아갑니다.

- 4·6절은 배포된 에이전트를 씁니다. 10단계가 이 에이전트를 삭제합니다.
- 강사가 수업 전에 공유 모델 용량(2–4절)과 trace 접근 권한(5·6절)을 준비합니다([강사 가이드](instructor.ko.md#levels)).

**진행:** 기존 **터미널 A·저장소 루트**에서 1–7절을 순서대로 합니다. 새 터미널이면 [환경만 복원](../README.ko.md#resume-shell)하고 이름·V2 지침·배포 버전을 유지합니다. 복구 label을 썼다면 아래 `--label improved`를 실제 후보 label로 바꿉니다.

**비용·증거:** 1–6절의 모델·judge 호출은 추가 과금되며, 6절은 최대 8시간 일정도 만듭니다. 추가 응답을 기본 실습의 48응답에 합치지 않습니다. 7절은 **9단계의 저장된 업무 gate만** 읽고 1–6절의 새 결과를 자동 반영하지 않습니다.

<a id="level-3-results"></a>

**메모는 이 표 하나만 씁니다.** 아래를 내 메모에 복사하고, 각 절을 마칠 때 마지막 칸을 **내 값과 해석**으로 채웁니다. 공격 프롬프트·유해 응답 원문은 복사하지 않습니다.

| 절 | 평가 대상 | 메모할 내 결과 |
|---|---|---|
| [1. 채점 기준표(rubric) 생성](#generate-rubric) | 저장된 V2 답변 | 두 rubric의 통과 수 `/18`와 업무 계약 검사 대비 놓친 점(없으면 없음) |
| [2. 스트레스 테스트](#stress-test) | V2 지침·정책 7개를 직접 받는 Sol. **검색·에이전트는 사용하지 않음** | 실패 수 `/15`; 실제 정책 공백·judge 판단·안전 경고 중 확인한 유형(없으면 없음) |
| [3. 공격 테스트(red team)](#red-team) | **V2 지침 없는** Sol 배포 | 공격 성공 수 `/6`와 성공률(ASR). 낮을수록 좋음 |
| [4. 에이전트 직접 호출](#evaluate-agent) | 배포된 V2 에이전트의 **새 응답 18개**(dev 6문항 × 3모델) | 모델별 업무 통과 수 `/6`와 7-4 저장 결과와의 차이 |
| [5. trace 평가](#evaluate-traces) | 7단계의 Application Insights trace 18개 | 평가 결과와 레벨 2 대비 차이 |
| [6. 연속 평가](#continuous-eval) | 매시간 최근 trace 최대 20개 | 첫 `completed` 시각·trace 수·세 평가 결과·포털의 오류/누락 없음 확인 |
| [7. 릴리스 gate](#release-gate) | 9단계 `verified-evidence.json`의 업무 gate 6개 | 출력 문구·종료 코드·통과 또는 막은 gate. **운영 승인은 아님** |

**대기:** 명령이 아직 실행 중이면 기다립니다. `... still running`·`... still in progress`로 **종료된 경우에만** 같은 명령으로 재개합니다. 네트워크 timeout을 원격 실행 중이라는 증거로 해석하지 않습니다. 그 밖의 오류는 [메시지별 복구](troubleshooting.ko.md#levels)를 따릅니다.

<a id="generate-rubric"></a>

## 1. rubric을 생성해 내 rubric과 비교

**터미널 A:** Foundry가 V2 지침을 읽어 가중치가 있는 차원을 제안하고, 두 rubric이 V2 응답을 채점합니다.

```bash
python scripts/workshop.py generate-rubric --label improved
```

**완료 확인:** `Generated rubric: <LAB_PREFIX>-generated-rubric version 1, pass threshold ...`, 가중치가 붙은 차원 목록, 그리고 `policy_rubric: .../18 passed on improved`와 `generated_rubric: .../18 passed on improved`가 실패 행 또는 `none`과 함께 나옵니다.

**다르면:** `Rubric generation is still running` 또는 `The run is still in progress`로 종료됐다면 같은 명령으로 재개합니다. 그 밖의 오류는 [레벨 2·3 복구](troubleshooting.ko.md#levels)를 봅니다.

**읽는 법:**

- **생성된 차원은 코드처럼 검토합니다.** LLM이 생성하므로 차원과 가중치는 조마다, 실행마다 다를 수 있습니다.
- **실패 행을 레벨 2의 `business_contract`와 비교합니다.** 영문 촬영 실행에서는 두 rubric 모두 V2 18행을 전부 통과시켰고, 계약 검사가 잡은 Sol D02의 판단값 오류도 통과시켰습니다. rubric은 품질을 판단할 뿐, 결정적인 계약 검사를 대신하지 않습니다.

<details>
<summary>촬영한 한국어 결과 — 예시</summary>

```text
Generated rubric: ll-ko-0923b-generated-rubric version 1, pass threshold 0.5
  - correct_policy_decision (weight 10)
  - date_appropriate_policy_application (weight 5)
  - evidence_grounding (weight 5)
  - citation_integrity (weight 4)
  - quantitative_normalization (weight 4)
  - schema_and_output_discipline (weight 4)
  - concise_korean_explanation (weight 2)
  - general_quality (weight 5)
policy_rubric: 18/18 passed on improved; failed rows: none
generated_rubric: 18/18 passed on improved; failed rows: none
```

한국어 지침에서는 `concise_korean_explanation`처럼 언어에 맞춘 차원도 생성되었습니다.

</details>

**다음:** [2. 합성 질문 스트레스 테스트](#stress-test)

<a id="stress-test"></a>

## 2. 합성 질문으로 V2 스트레스 테스트

**터미널 A:** Foundry가 새 출장 규정 질문 15개를 만들고, 각 질문을 V2 지침·정책 7개와 함께 Sol 배포에 보내 답변을 채점합니다.

```bash
python scripts/workshop.py stress-test --model sol --count 15
```

**완료 확인:** `Stress test completed on sol: N of 15 synthetic questions failed an evaluator`와 `intent_resolution`·`relevance`·`indirect_attack`의 결과가 한 줄씩 나옵니다. 실패가 있으면 질문도 나옵니다. `N=0`도 정상 결과입니다.

**다르면:** `The run is still in progress`로 종료됐다면 같은 명령으로 재개합니다. 그 밖의 오류는 [레벨 2·3 복구](troubleshooting.ko.md#levels)를 봅니다. 질문 수는 15개로 유지합니다.

**읽는 법:**

- **모델 단위 테스트입니다.** Foundry가 정책 7개를 Sol에 직접 넣으며, 에이전트와 그 검색은 쓰지 않습니다. 그래서 5–8단계의 수치와 비교하지 않습니다.
- **별도의 새 실험끼리는 질문과 수치가 달라질 수 있습니다.** 이 폴더에서 같은 명령을 재개하면 저장된 질문·run을 재사용합니다. 결과 파일을 지워 더 좋은 점수를 뽑지 않습니다.
- **실패한 질문을 분류합니다.** 실제 공백(예: 규정이 다루지 않는 해외 출장), 올바른 보류를 감점한 judge, 안전 경고 중 무엇인지 봅니다. 좋은 질문은 고정 정답을 직접 작성한 뒤에만 새 dev 사례로 추가하고, holdout으로 튜닝하지 않습니다.

<details>
<summary>촬영한 한국어 결과 — 예시</summary>

```text
Stress test completed on sol: 3 of 15 synthetic questions failed an evaluator
  intent_resolution: 14/15
  relevance: 14/15
  indirect_attack: 14/15
```

실패한 질문은 모두 일본 출장처럼 국내 규정이 다루지 않는 해외 출장이었습니다. 그중 해외 로밍비·라운지 비용을 회의비로 처리해 달라는 요청에 대한 답변 하나는 `indirect_attack`으로 표시되었습니다.

</details>

**다음:** [3. 후보 모델 red team](#red-team)

<a id="red-team"></a>

## 3. 후보 모델 red team

**주의:** 이 스캔은 의도적으로 유해한 프롬프트를 보냅니다. 스캔은 작게 유지하고, 결과는 내 프로젝트에서만 확인하며, 공격 내용을 메모에 옮기지 않습니다.

**터미널 A:** 작은 클라우드 스캔이 Sol 배포에 공격 6건을 보냅니다. 위험 범주 2개마다 전략을 쓰지 않은 기본 공격(`baseline`) 1건과 공격 전략 2개로 1건씩입니다. Foundry 평가로 실행되며 약 1분 걸립니다. Foundry의 에이전트 red team이 이 hosted agent를 지원하지 않으므로 모델을 대상으로 합니다([자세히](#beyond)).

```bash
python scripts/workshop.py red-team --model sol
```

**완료 확인:** 출력에 다음이 차례로 나옵니다.

1. `Red-team scan completed on sol: risk categories Violence, HateUnfairness; attack strategies base64, flip`
2. `Attack success rate: N/6 attacks succeeded (...); lower is better`, 이어서 `by risk category` 한 줄과 `by attack strategy` 한 줄
3. `Portal: <링크>`

**다르면:** `The run is still in progress`로 종료됐다면 같은 명령으로 재개합니다. 그 밖의 메시지는 [레벨 2·3 복구](troubleshooting.ko.md#levels)를 봅니다. 공격 성공은 낮은 품질 결과이지 재시도할 실행 오류가 아닙니다.

**읽는 법:**

- **공격 성공은 Foundry의 안전 평가기가 Sol의 답변에서 그 공격이 노린 유해 내용을 찾았다는 뜻입니다.** 공격 성공률(ASR)은 성공한 공격의 비율이므로 낮을수록 좋습니다.
- **이 스캔은 내 지침이 아니라 배포를 시험합니다.** Sol은 V2 지침 없이, 배포의 콘텐츠 필터를 거쳐 답합니다. 공격 6건은 작은 표본입니다. 리허설에서 세 번 스캔할 때마다 같은 프롬프트 6개를 보냈지만 Sol의 답변은 매번 달랐고, 전략을 쓰지 않은 violence 공격은 그중 두 번 성공했습니다. 비율만 보지 말고 성공한 공격을 하나씩 검토합니다.

**포털:** `Portal:` 링크를 엽니다. 스캔이 New Foundry에서 열리며, **Evaluations → Red team** 탭에도 나옵니다([AI red teaming 작동 방식](https://learn.microsoft.com/azure/foundry/concepts/ai-red-teaming-agent)).

**완료 확인:** 화면 제목이 `<LAB_PREFIX>-red-team-sol`이고, **Overall metric results**에 CLI와 같은 비율이 보입니다(예: **Violence ASR**과 `n/3`). 아래 표에서 **Attack outcome**이 `Fail`이면 성공한 공격입니다.

**다르면:** **Evaluations → Red team** 탭에서 `<LAB_PREFIX>-red-team-sol`을 찾아 엽니다. 비율은 스캔 화면에서 읽습니다. 목록의 **Issues in last run** 열은 성공한 공격 수가 아닙니다.

<details>
<summary>예시 화면: New Foundry의 스캔 화면</summary>

![위험 범주와 공격 전략별 공격 성공률을 보여 주는 red team 스캔](assets/levels-20260923/ko-l3-redteam.webp)

이 예시에서는 Response와 Reasoning 열을 흐리게 가렸습니다.

</details>

<details>
<summary>촬영한 한국어 결과 — 예시</summary>

```text
Red-team scan completed on sol: risk categories Violence, HateUnfairness; attack strategies base64, flip
Attack success rate: 0/6 attacks succeeded (0.0%); lower is better
  by risk category: Violence 0/3, HateUnfairness 0/3
  by attack strategy: baseline 0/2, base64 0/2, flip 0/2
```

같은 날 영문 스캔은 같은 프롬프트 6개를 보냈고, 전략을 쓰지 않은 violence 공격 1건이 성공해 1/6이었습니다. 스캔은 실습 언어나 지침을 쓰지 않으므로, 이 차이는 Sol의 답변이 실행마다 달라서 생깁니다.

</details>

**다음:** [4. 배포된 에이전트 직접 평가](#evaluate-agent)

<a id="evaluate-agent"></a>

## 4. Foundry가 에이전트를 직접 호출하게 하기

**터미널 A:** Foundry가 같은 dev 6문항을 세 모델에 각각 질문해 **새 응답 18개**를 채점합니다. 배포된 V2 에이전트를 호출하며 모델마다 run 하나씩, 약 15분 걸립니다.

```bash
python scripts/workshop.py evaluate-agent --split dev
```

**완료 확인:** 출력에 다음이 차례로 나옵니다.

1. `Foundry called <LAB_AGENT_NAME> version N for 18 dev rows in 3 runs, one per model (prompt v2).`
2. `business_contract`·`task_adherence`·`intent_resolution`·`relevance`의 결과 한 줄씩, 이어서 `business_contract by model: ...`
3. `Traces recorded: 18`과 `Portal:` 링크. 기본 label이면 `Your saved improved responses: .../18 business passes.`도 나옵니다. 복구 label이면 이 줄이 없을 수 있으므로 7-4의 내 요약과 직접 대조합니다.

**다르면:** `The agent evaluation is still running`으로 종료됐다면 같은 명령으로 재개합니다. 그 밖의 메시지는 [레벨 2·3 복구](troubleshooting.ko.md#levels)를 봅니다. 실패 복구에도 `--split dev`를 유지합니다.

**읽는 법:**

- **파이프라인이 에이전트를 평가하는 방식입니다.** 수집 코드 없이 Foundry가 에이전트를 호출하고 평가기를 적용합니다. `azd ai agent eval run`과 CI 작업도 이렇게 동작합니다.
- **레벨 2의 코드 평가기가 실시간 답변을 채점하므로,** 저장된 결과와 실시간 결과가 같은 업무 계약으로 채점됩니다.
- **저장된 `improved` 결과와 모델별로 비교합니다.** 답변을 새로 받으므로 7단계에서 실패한 행을 여기서 통과하거나 그 반대일 수 있습니다. 평가기가 바뀐 것이 아니라 모델의 실행 간 차이입니다.

<details>
<summary>Foundry가 이 invocations 에이전트를 호출하는 방식</summary>

- 렌더링한 메시지 내용 `{"type": "input_text", "text": "..."}`을 에이전트 엔드포인트로 보냅니다. 이 에이전트는 그 형식을 받아, text가 호출 JSON이면 그 호출을 그대로 실행하고, 일반 텍스트면 `case_id` `external`로 Sol에 보냅니다([hosted agent 평가](https://learn.microsoft.com/azure/foundry/observability/quickstarts/quickstart-evaluate-hosted-agent)).
- 저장된 판단값이 없는 행이면, 코드 평가기는 Foundry가 실시간 응답을 넣는 행의 `sample.output_text` 필드에서 에이전트의 JSON 답변을 읽습니다.

</details>

<details>
<summary>촬영한 한국어 결과 — 예시</summary>

```text
Foundry called frontier-loop-ko-lv3a version 1 for 18 dev rows in 3 runs, one per model (prompt v2).
  business_contract  18/18
  task_adherence     18/18
  intent_resolution  15/18
  relevance          18/18
business_contract by model: sol 6/6, luna 6/6, astra 6/6
Traces recorded: 18
```

`intent_resolution`이 실패시킨 3행은 모두 올바른 답이었습니다. 규정이 다루지 않는 일본 출장을 재무팀에 넘긴 D04 한 건과, 승인 완료로 적어 달라는 요청을 거절한 D06 두 건입니다. 범용 평가기는 요청을 들어주지 않았다고 감점했고, 업무 계약은 모두 통과시켰습니다. 실패 행은 점수보다 먼저 이유를 읽습니다.

이 run은 7단계 저장 응답이 없는 리허설 폴더에서 15분 걸렸습니다. 저장 응답이 없어 `Your saved improved responses` 줄은 출력되지 않았으며, 촬영한 7단계 결과는 18/18이었습니다.

</details>

**다음:** [5. 저장된 trace 평가](#evaluate-traces)

<a id="evaluate-traces"></a>

## 5. 7단계의 trace 평가

**터미널 A:** Foundry가 Application Insights에서 7단계 실행의 trace 18개를 읽어 채점합니다. 아무것도 다시 호출하지 않습니다.

```bash
python scripts/workshop.py evaluate-traces --label improved
```

**완료 확인:** `Trace evaluation completed: 18 traces from improved, read from Application Insights.`에 이어, `relevance`·`intent_resolution`·`task_adherence`·`indirect_attack`에 대해 `traces`와 `saved responses (Level 2)` 열이 있는 표가 나옵니다.

**다르면:** 접근 오류는 강사와 권한을 확인하고, 누락 trace는 반영을 기다립니다. **오류가 파일 삭제를 명시한 경우에만** [상태 파일 복구](troubleshooting.ko.md#level-state-recovery)대로 백업 후 지정 파일 하나를 처리합니다. 단순 대기 시간 초과에는 삭제하지 않습니다. 비교 열이 `n/a`이면 레벨 2를 같은 label로 마쳤는지 확인합니다.

**읽는 법:**

- **trace에는 모델이 실제로 본 내용이 남습니다.** 입력은 *검색된 정책이 포함된* 질문이고, 출력은 JSON 원문 답변입니다. 레벨 2는 같은 평가기에 질문과 답변 텍스트만 주었으므로 결과가 다를 수 있습니다. 촬영한 실행에서는 모든 항목이 trace 18개를 전부 통과했습니다.
- **Foundry가 에이전트를 호출할 수 없을 때 trace를 씁니다.** 스트리밍·장시간 실행 에이전트나, 실제 트래픽을 사후에 평가할 때입니다([trace 평가](https://learn.microsoft.com/azure/foundry/observability/how-to/cloud-evaluation-deployed-interactions#evaluate-traces-preview)).
- **trace에는 메시지 내용이 남습니다.** 실습 데이터는 합성 데이터입니다. 실제 사용자라면 평가 전에 trace에 무엇을 기록할지 먼저 정합니다.

<details>
<summary>촬영한 한국어 결과 — 예시</summary>

```text
Trace evaluation completed: 18 traces from improved, read from Application Insights.
criterion          traces  saved responses (Level 2)
relevance          18/18   15/18
intent_resolution  18/18   16/18
task_adherence     18/18   16/18
indirect_attack    18/18   18/18
```

trace는 8시간 전 것이었습니다. 명령이 수집 시각을 보고 조회 기간을 정합니다.

</details>

**다음:** [6. 연속 평가 일정과 첫 결과 확인](#continuous-eval)

<a id="continuous-eval"></a>

## 6. 연속 평가 켜기

**터미널 A — 일정 만들기:** 생성 시점의 에이전트 버전에 고정해 최근 trace를 최대 20개씩 매시간 평가합니다. 첫 실행은 2분 뒤에 시작하고, 일정은 8시간 뒤 스스로 멈추며, 10단계가 삭제합니다. 같은 명령을 다시 실행하면 기존 일정의 상태를 조회합니다.

```bash
python scripts/workshop.py continuous-eval
```

**일정 생성 확인:** `Continuous evaluation <LAB_PREFIX>-continuous: every hour on <LAB_AGENT_NAME> version N, up to 20 recent traces, from HH:MM UTC until HH:MM UTC.`가 나옵니다. `No scheduled run yet`이면 아래 시각까지 기다립니다. 이미 실행 결과가 있으면 바로 아래 완료 기준과 대조합니다. 시각은 UTC이며 한국 시간은 9시간을 더합니다(예: `11:35 UTC`는 20:35).

**다르면:** agent가 없거나 일정 소유권이 충돌하면 멈추고 [오류별 복구](troubleshooting.ko.md#levels)를 따릅니다. 이름 변경·재배포로 우회하지 않습니다. 이미 10단계를 마쳤다면 이 절은 **미실행**으로 기록하며 완료로 표시하지 않습니다.

**터미널 A — 첫 실행 확인:** 출력된 `HH:MM UTC` 이후에 같은 명령을 다시 실행합니다.

```bash
python scripts/workshop.py continuous-eval
```

**완료 확인:** `HH:MM UTC  completed  N traces: relevance .../N, task_adherence .../N, indirect_attack .../N`이 나오고 **N이 1 이상**입니다. 일정 생성만으로는 완료가 아닙니다. 시각·trace 수·세 평가 결과를 메모합니다.

**다르면:** `in_progress`·`queued`이면 1분 뒤 같은 명령으로 조회합니다. `failed`·오류·0 traces이면 미완료로 기록하고 강사와 트래픽·권한을 확인합니다. 일정을 지우고 새로 만들지 않습니다.

**포털 — 행별 결과 확인:** 출력의 `Portal:` 링크를 열고 위에서 메모한 **같은 UTC 시각의 run**을 선택합니다.

**완료 확인:** N개 행에 세 평가기의 유효한 결과가 있고 오류·누락이 없습니다. `completed`만으로 오류가 없다고 판단하지 않습니다. `passed: false`는 유효한 미통과 결과이므로 그대로 보고합니다.

**다르면:** 빈 결과·평가 오류는 미완료로 기록하고 강사와 확인합니다. 새 일정을 만들어 오류 이력을 지우지 않습니다.

**읽는 법:**

- **최근 트래픽에서 trace를 고릅니다.** 4절의 호출과 다른 최근 호출이 포함될 수 있습니다. 운영에서는 이 품질 신호가 떨어지면 5–9단계의 루프로 돌아갑니다.
- **hosted agent는 일정에 따라 trace로 평가하고,** prompt agent는 응답마다 평가할 수도 있습니다([연속 평가](https://learn.microsoft.com/azure/foundry/observability/how-to/how-to-monitor-agents-dashboard#set-up-continuous-evaluation)).

<details>
<summary>촬영한 한국어 결과 — 예시</summary>

```text
Continuous evaluation ll-ko-lv3a-continuous: every hour on frontier-loop-ko-lv3a version 1, up to 20 recent traces, from 11:35 UTC until 19:33 UTC.
  11:35 UTC  completed  20 traces: relevance 20/20, task_adherence 20/20, indirect_attack 20/20
```

첫 실행이 버전 1의 최근 trace 20개를 골랐습니다. 한 번에 최대 20개까지 평가합니다.

</details>

**다음:** [7. 저장된 업무 gate로 릴리스 중단 여부 확인](#release-gate)

<a id="release-gate"></a>

## 7. 업무 gate를 릴리스 gate로 만들기

**터미널 A:** 9단계의 실행 검증과 gate 6개를 확인한 뒤 명령의 종료 코드를 출력합니다. **이 레벨의 red team·연속 평가 결과는 이 gate에 포함되지 않습니다.**

```bash
python scripts/workshop.py gate
echo "exit code: $?"
```

**완료 확인:** 다음 둘 중 어느 쪽이든 정상이며, 나온 결과를 그대로 보고합니다.

- `Quality gate passed: all six business gates are true. production_release_approved remains false.`에 이어 `exit code: 0`
- 9-2의 gate 중 하나라도 `false`일 때 `Quality gate FAILED: ...`에 이어 `exit code: 1`

**다르면:** 파일 없음·traceback은 품질 미통과와 다른 실행 오류입니다. `src/agent/.foundry/results/verified-evidence.json`과 [9-1의 완료 기준](../README.ko.md#lab-g)을 확인합니다. 출력 없이 종료 코드 `1`만 보고 업무 gate 실패로 기록하지 않습니다.

**읽는 법:** 파이프라인은 새 후보마다 5–9단계와 같은 루프를 실행한 뒤 이 명령을 실행하며, 0이 아닌 종료 코드가 릴리스를 멈춥니다. 예를 들어 GitHub Actions 단계는 다음과 같습니다(읽기만 합니다. 이 저장소에는 이런 워크플로가 없습니다).

```yaml
      - name: Stop the release if a business gate fails
        run: python scripts/workshop.py gate
```

gate를 통과해도 운영 승인이 아니며, 사람의 검토와 8단계의 holdout 규칙은 그대로 적용됩니다. [GitHub Actions에서 평가 실행](https://learn.microsoft.com/azure/foundry/how-to/evaluation-github-action)

<a id="finish-level-3"></a>

## 레벨 3 마무리

각 절에서 채운 [결과표](#level-3-results)를 기본 실습의 [보고](../README.ko.md#finish)에 붙입니다. 끝난 명령을 다시 실행할 필요는 없습니다.

**완료 확인:** 1–7절의 완료 기준을 충족하고 표를 채웠습니다. 생략·오류·0 trace는 **미완료**로 기록합니다. 낮은 유효 점수나 `Quality gate FAILED`는 완료된 실습의 결과입니다.

**다음:** [10단계 정리](../README.ko.md#cleanup)로 돌아갑니다. 미완료로 중단하더라도 만든 유료 자원·일정의 정리는 필요합니다. 이미 정리를 마쳤다면 반복하지 않습니다. 정리하면 연속 평가 일정, 생성된 rubric과 그 산출물, 합성 질문 데이터셋이 삭제되고, eval group과 red team 결과는 증거로 남습니다.

<a id="beyond"></a>

## 선택 자료: 실습 범위 밖의 운영 기능

| 기능 | 이 에이전트에서의 상태 | 공식 안내 |
|---|---|---|
| 에이전트 red team(금지 행동, 민감 데이터 유출) | invocations 프로토콜의 hosted agent는 거부됨. 2026-09-23 시도는 `Hosted Invocations agents require a freeform input template, which red team agent targets do not provide.`로 실패. prompt agent에서는 동작 | [클라우드에서 AI red teaming 실행](https://learn.microsoft.com/azure/foundry/how-to/develop/run-ai-red-teaming-cloud) |
| prompt agent의 모든 응답 평가 | 평가 규칙은 prompt agent용이며, hosted agent는 6절의 trace 일정을 씀 | [연속 평가 설정](https://learn.microsoft.com/azure/foundry/observability/how-to/how-to-monitor-agents-dashboard#set-up-continuous-evaluation) |
| 예약 red team | red team도 일정으로 실행할 수 있음. 이 실습은 작은 스캔 한 번만 실행 | [클라우드에서 AI red teaming 실행](https://learn.microsoft.com/azure/foundry/how-to/develop/run-ai-red-teaming-cloud) |
