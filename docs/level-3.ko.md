# 레벨 3: 릴리스 절차처럼 평가 운영하기

[English](level-3.en.md) · [메인 가이드로 돌아가기](../README.ko.md#levels) · [요약 영상 12:21부터](../README.ko.md#summary-video)

**약 70분 동안 네 대상을 평가한 뒤 평가를 운영에 넣습니다:** 저장된 답변, 모델 단독, 배포된 에이전트, 그 trace를 평가하고(1–5절), 일정과 릴리스 gate를 만듭니다(6–7절).

| 절 | Foundry가 평가하는 대상 | 사용하는 것 |
|---|---|---|
| [1. rubric 생성](#generate-rubric) | 저장된 V2 답변 | Foundry가 V2 지침으로 만든 rubric |
| [2. 스트레스 테스트](#stress-test) | V2 지침을 넣은 Sol | Foundry가 만든 질문 15개 |
| [3. red team](#red-team) | Sol 배포 | Foundry가 만든 공격 프롬프트 |
| [4. 에이전트 직접 호출](#evaluate-agent) | 배포된 에이전트 | Foundry가 실시간으로 보내는 dev 질문 18개 |
| [5. trace 평가](#evaluate-traces) | 7단계 실행 | Application Insights의 trace 18개 |
| [6. 연속 평가](#continuous-eval) | 에이전트의 최근 트래픽 | 매시간 최근 trace 최대 20개 |
| [7. 릴리스 gate](#release-gate) | 업무 gate 6개(Sol·Luna·Astra × dev·holdout) | 9단계의 `verified-evidence.json` |

**준비:** 같은 폴더에서 [레벨 2](level-2.ko.md)를 마쳤고, **10단계는 아직 실행하지 않았어야 합니다.** 마친 뒤에는 [10단계](../README.ko.md#cleanup)로 돌아갑니다.

- 4·6절은 배포된 에이전트를 씁니다. 10단계가 이 에이전트를 삭제합니다.
- 강사가 수업 전에 공유 모델 용량(2–4절)과 trace 접근 권한(5·6절)을 준비합니다([강사 가이드](instructor.ko.md#levels)).

<a id="generate-rubric"></a>

## 1. rubric을 생성해 내 rubric과 비교

**터미널 A:** Foundry가 V2 지침을 읽어 가중치가 있는 차원을 제안하고, 두 rubric이 V2 응답을 채점합니다.

```bash
python scripts/workshop.py generate-rubric --label improved
```

**완료 확인:** `Generated rubric: <LAB_PREFIX>-generated-rubric version 1, pass threshold ...`, 가중치가 붙은 차원 목록, 그리고 `policy_rubric: .../18 passed on improved`와 `generated_rubric: .../18 passed on improved`가 실패 행 또는 `none`과 함께 나옵니다.

**다르면:** 시간 초과는 생성이나 채점이 아직 진행 중이라는 뜻이므로 같은 명령을 다시 실행합니다. 그 밖의 오류는 [레벨 2·3 복구](troubleshooting.ko.md#levels)를 봅니다.

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

<a id="stress-test"></a>

## 2. 합성 질문으로 V2 스트레스 테스트

**터미널 A:** Foundry가 새 출장 규정 질문 15개를 만들고, 각 질문을 V2 지침·정책 7개와 함께 Sol 배포에 보내 답변을 채점합니다.

```bash
python scripts/workshop.py stress-test --model sol --count 15
```

**완료 확인:** `Stress test completed on sol: N of 15 synthetic questions failed an evaluator`, `intent_resolution`·`relevance`·`indirect_attack`의 결과 한 줄씩, 그리고 실패한 질문이 나옵니다.

**다르면:** 시간 초과는 아직 실행 중이라는 뜻이므로 같은 명령을 다시 실행합니다. Foundry는 질문을 최소 15개 요구합니다.

**읽는 법:**

- **모델 단위 테스트입니다.** Foundry가 정책 7개를 Sol에 직접 넣으며, 에이전트와 그 검색은 쓰지 않습니다. 그래서 5–8단계의 수치와 비교하지 않습니다.
- **실행마다 수치가 달라집니다.** Foundry가 매번 새 질문을 만들기 때문입니다. 개수가 아니라 실패 유형을 비교합니다.
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

<a id="red-team"></a>

## 3. 후보 모델 red team

**주의:** 이 스캔은 의도적으로 유해한 프롬프트를 보냅니다. 스캔은 작게 유지하고, 결과는 내 프로젝트에서만 확인하며, 공격 내용을 메모에 옮기지 않습니다.

**터미널 A:** 작은 클라우드 스캔이 위험 범주 2개를 공격 전략 2개로 Sol 배포에 시도합니다. Foundry의 에이전트 red team이 이 hosted agent를 지원하지 않으므로 모델을 대상으로 합니다([자세히](#beyond)).

```bash
python scripts/workshop.py red-team --model sol
```

**완료 확인:** `Red-team scan completed on sol: risk categories Violence, HateUnfairness; attack strategies base64, flip`에 이어 `Portal (attack success rate): <링크>`가 나옵니다.

**다르면:** 시간 초과는 스캔이 아직 진행 중이라는 뜻이므로 같은 명령을 다시 실행합니다.

**포털:** 이 스캔은 이전(classic) 포털 화면에서만 열립니다([AI red teaming 작동 방식](https://learn.microsoft.com/azure/foundry/concepts/ai-red-teaming-agent)).

1. 상단의 **New Foundry** 스위치를 끕니다. 피드백 창이 뜨면 **Continue without feedback**을 고릅니다.
2. 출력된 링크를 엽니다.
3. **Metric dashboard → Attack risk category**에서 위험 범주별 성공한 공격 비율을 읽습니다.
4. **New Foundry**를 다시 켭니다.

**완료 확인:** 화면 제목이 `<LAB_PREFIX>-red-team-sol`이고, **Hate and unfairness**와 **Violence**에 각각 비율과 `n/3 attacks`가 보입니다.

**다르면:** New Foundry의 **Evaluations → Red team** 탭에는 이 명령으로 만든 스캔이 나오지 않습니다. 이전 화면에서 출력된 링크를 엽니다([포털 화면 차이](troubleshooting.ko.md#portal-differs)).

<details>
<summary>예시 화면: 이전 포털의 red teaming 보고서</summary>

![위험 범주별 성공한 공격을 보여 주는 red teaming 보고서](assets/levels-20260923/ko-l3-redteam.webp)

촬영한 한국어 스캔에서는 Hate and unfairness 공격 3건 중 1건(33.33%)이 성공했고, Violence는 0/3이었습니다. 영문 스캔에서는 성공한 공격이 없었습니다.

</details>

<a id="evaluate-agent"></a>

## 4. Foundry가 에이전트를 직접 호출하게 하기

**터미널 A:** Foundry가 7단계의 dev 질문 18개(질문 6개 × 모델 3개)를 배포된 V2 에이전트에 모델마다 run 하나씩 보내고, 실시간 답변을 채점합니다. 약 15분 걸립니다.

```bash
python scripts/workshop.py evaluate-agent
```

**완료 확인:** 출력에 다음이 차례로 나옵니다.

1. `Foundry called <LAB_AGENT_NAME> version N for 18 dev rows in 3 runs, one per model (prompt v2).`
2. `business_contract`·`task_adherence`·`intent_resolution`·`relevance`의 결과 한 줄씩, 이어서 `business_contract by model: ...`
3. `Your saved improved responses: .../18 business passes.`, `Traces recorded: 18`, `Portal:` 링크

**다르면:** 시간 초과는 아직 실행 중이라는 뜻이므로 같은 명령을 다시 실행합니다. 그 밖의 메시지는 [레벨 2·3 복구](troubleshooting.ko.md#levels)를 봅니다.

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

<a id="evaluate-traces"></a>

## 5. 7단계의 trace 평가

**터미널 A:** Foundry가 Application Insights에서 7단계 실행의 trace 18개를 읽어 채점합니다. 아무것도 다시 호출하지 않습니다.

```bash
python scripts/workshop.py evaluate-traces --label improved
```

**완료 확인:** `Trace evaluation completed: 18 traces from improved, read from Application Insights.`에 이어, `relevance`·`intent_resolution`·`task_adherence`·`indirect_attack`에 대해 `traces`와 `saved responses (Level 2)` 열이 있는 표가 나옵니다.

**다르면:** 접근 오류이면 강사에게 trace 접근 준비를 요청하고, `... traces were not found`이면 수집이 끝나도록 몇 분 기다립니다. 두 메시지 모두 `... <파일> and re-run evaluate-traces --label improved.`로 끝나므로, 그 파일을 삭제한 뒤 같은 명령을 다시 실행합니다([레벨 2·3 복구](troubleshooting.ko.md#levels)).

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

<a id="continuous-eval"></a>

## 6. 연속 평가 켜기

**터미널 A — 일정 만들기:** 에이전트 최신 버전의 최근 trace를 최대 20개씩 매시간 평가하는 일정을 만듭니다. 첫 실행은 2분 뒤에 시작하고, 일정은 8시간 뒤 스스로 멈추며, 10단계가 삭제합니다.

```bash
python scripts/workshop.py continuous-eval
```

**완료 확인:** `Continuous evaluation <LAB_PREFIX>-continuous: every hour on <LAB_AGENT_NAME> version N, up to 20 recent traces, from HH:MM UTC until HH:MM UTC.`와 `No scheduled run yet. Run this command again after HH:MM UTC.`가 나옵니다. 시각은 UTC이며, 한국 시간은 9시간을 더합니다(예: `11:35 UTC`는 20:35).

**다르면:** `This folder has no deployed hosted agent`는 이 폴더의 에이전트가 배포되어 있지 않다는 뜻입니다(예: 10단계를 이미 실행함). 이 절은 건너뛰고, 이 절을 위해 다시 배포하지 않습니다. `Schedule ... already exists and is not owned by this folder`는 다른 조가 같은 `LAB_PREFIX`를 쓴다는 뜻이므로 강사에게 다른 이름을 받습니다.

**터미널 A — 첫 실행 확인:** 출력된 `HH:MM UTC` 이후에 같은 명령을 다시 실행합니다.

```bash
python scripts/workshop.py continuous-eval
```

**완료 확인:** `HH:MM UTC  completed  N traces: relevance .../N, task_adherence .../N, indirect_attack .../N` 같은 줄이 나옵니다.

**다르면:** `in_progress`나 `queued`는 첫 실행이 아직 진행 중이라는 뜻이므로 1분 뒤 같은 명령을 다시 실행합니다.

**읽는 법:**

- **첫 실행은 4절의 트래픽을 평가합니다.** 운영에서는 매시간 실행이 실제 트래픽의 품질 신호를 유지하고, 점수가 떨어지면 5–9단계의 루프로 돌아갑니다.
- **hosted agent는 일정에 따라 trace로 평가하고,** prompt agent는 응답마다 평가할 수도 있습니다([연속 평가](https://learn.microsoft.com/azure/foundry/observability/how-to/how-to-monitor-agents-dashboard#set-up-continuous-evaluation)).

<details>
<summary>촬영한 한국어 결과 — 예시</summary>

```text
Continuous evaluation ll-ko-lv3a-continuous: every hour on frontier-loop-ko-lv3a version 1, up to 20 recent traces, from 11:35 UTC until 19:33 UTC.
  11:35 UTC  completed  20 traces: relevance 20/20, task_adherence 20/20, indirect_attack 20/20
```

첫 실행이 버전 1의 최근 trace 20개를 골랐습니다. 한 번에 최대 20개까지 평가합니다.

</details>

<a id="release-gate"></a>

## 7. 업무 gate를 릴리스 gate로 만들기

**터미널 A:** 9-2의 gate 6개를 확인한 뒤 명령의 종료 코드를 출력합니다.

```bash
python scripts/workshop.py gate
echo "exit code: $?"
```

**완료 확인:** 다음 둘 중 어느 쪽이든 정상이며, 나온 결과를 그대로 보고합니다.

- `Quality gate passed: all six business gates are true. production_release_approved remains false.`에 이어 `exit code: 0`
- 9-2의 gate 중 하나라도 `false`일 때 `Quality gate FAILED: ...`에 이어 `exit code: 1`

**다르면:** 이 명령은 `src/agent/.foundry/results/verified-evidence.json`을 읽습니다. 파일이 없으면 [9단계의 9-1](../README.ko.md#lab-g)로 돌아갑니다.

**읽는 법:** 파이프라인은 새 후보마다 5–9단계와 같은 루프를 실행한 뒤 이 명령을 실행하며, 0이 아닌 종료 코드가 릴리스를 멈춥니다. 예를 들어 GitHub Actions 단계는 다음과 같습니다(읽기만 합니다. 이 저장소에는 이런 워크플로가 없습니다).

```yaml
      - name: Stop the release if a business gate fails
        run: python scripts/workshop.py gate
```

gate를 통과해도 운영 승인이 아니며, 사람의 검토와 8단계의 holdout 규칙은 그대로 적용됩니다. [GitHub Actions에서 평가 실행](https://learn.microsoft.com/azure/foundry/how-to/evaluation-github-action)

## 레벨 3 마무리

[보고](../README.ko.md#finish)에 다음을 더합니다.

- 생성된 rubric이 더하거나 놓친 것
- 실제 공백을 드러낸 합성 질문
- red team의 공격 성공률
- Foundry의 실시간 실행이 저장된 결과와 일치했는지, trace가 보여 준 것
- 내 릴리스 gate가 막을 대상

**완료 확인:** 보고에 위 항목이 한 줄씩 있습니다.

**다음:** [10단계 정리](../README.ko.md#cleanup)로 돌아갑니다. 정리하면 연속 평가 일정, 생성된 rubric과 그 산출물, 합성 질문 데이터셋이 삭제되고, eval group과 red team 결과는 증거로 남습니다.

<a id="beyond"></a>

## 선택 자료: 실습 범위 밖의 운영 기능

| 기능 | 이 에이전트에서의 상태 | 공식 안내 |
|---|---|---|
| 에이전트 red team(금지 행동, 민감 데이터 유출) | invocations 프로토콜의 hosted agent는 거부됨. 2026-09-23 시도는 `Hosted Invocations agents require a freeform input template, which red team agent targets do not provide.`로 실패. prompt agent에서는 동작 | [클라우드에서 AI red teaming 실행](https://learn.microsoft.com/azure/foundry/how-to/develop/run-ai-red-teaming-cloud) |
| prompt agent의 모든 응답 평가 | 평가 규칙은 prompt agent용이며, hosted agent는 6절의 trace 일정을 씀 | [연속 평가 설정](https://learn.microsoft.com/azure/foundry/observability/how-to/how-to-monitor-agents-dashboard#set-up-continuous-evaluation) |
| 예약 red team | red team도 일정으로 실행할 수 있음. 이 실습은 작은 스캔 한 번만 실행 | [클라우드에서 AI red teaming 실행](https://learn.microsoft.com/azure/foundry/how-to/develop/run-ai-red-teaming-cloud) |
