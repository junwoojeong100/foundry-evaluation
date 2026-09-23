# 레벨 3: 릴리스 절차처럼 평가 운영하기

[English](level-3.en.md) · [메인 가이드로 돌아가기](../README.ko.md#levels)

**약 40분 동안 하는 일:**

1. Foundry가 V2 지침으로 **rubric을 생성**하게 하고, 내가 만든 rubric과 비교합니다.
2. Foundry가 만든 질문으로 V2 지침을 **스트레스 테스트**합니다.
3. 공격 전략으로 후보 모델을 **red team**합니다.
4. 업무 gate 6개를 CI 파이프라인이 강제할 수 있는 **릴리스 gate**로 만듭니다.

**준비:** 같은 폴더에서 [레벨 2](level-2.ko.md)를 마쳤고, **10단계는 아직 실행하지 않았어야 합니다.** 2·3절은 공유 Sol 배포와 judge를 호출하므로 강사가 수업 전에 용량을 확인합니다.

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

- **모델 단위 테스트입니다.** 에이전트의 검색을 거치지 않으므로 5–8단계의 수치와 비교하지 않습니다.
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

**터미널 A:** 작은 클라우드 스캔이 위험 범주 2개를 공격 전략 2개로 Sol 배포에 시도합니다.

```bash
python scripts/workshop.py red-team --model sol
```

**완료 확인:** `Red-team scan completed on sol: risk categories Violence, HateUnfairness; attack strategies base64, flip`에 이어 `Portal (attack success rate): <링크>`가 나옵니다.
**다르면:** 시간 초과는 스캔이 아직 진행 중이라는 뜻이므로 같은 명령을 다시 실행합니다.

**포털:** 출력된 링크를 열어 위험 범주와 공격 전략별 **공격 성공률(ASR)**을 읽습니다([AI red teaming 작동 방식](https://learn.microsoft.com/azure/foundry/concepts/ai-red-teaming-agent)).

**완료 확인:** 이 스캔의 red teaming 화면이 열리고 공격 성공률이 보입니다.
**다르면:** [포털 화면 차이](troubleshooting.ko.md#portal-differs)를 봅니다.

**주의:** red team은 의도적으로 유해한 프롬프트를 만듭니다. 스캔은 작게 유지하고, 결과는 내 프로젝트에서만 확인하며, 공격 내용을 실습 메모에 옮기지 않습니다.

<a id="release-gate"></a>

## 4. 업무 gate를 릴리스 gate로 만들기

**터미널 A:**

```bash
python scripts/workshop.py gate
```

**완료 확인:** `Quality gate passed: all six business gates are true. production_release_approved remains false.`와 종료 코드 0. 9-2의 gate 중 하나라도 `false`이면 `Quality gate FAILED: ...`를 출력하고 종료 코드 1로 끝납니다.
**다르면:** 이 명령은 `src/agent/.foundry/results/verified-evidence.json`을 읽습니다. 파일이 없으면 [9-1](../README.ko.md#lab-g)로 돌아갑니다.

파이프라인은 새 후보에 대해 5–9단계와 같은 루프를 실행한 뒤 이 명령을 실행하며, 0이 아닌 종료 코드가 릴리스를 멈춥니다.

```yaml
      - name: Stop the release if a business gate fails
        run: python scripts/workshop.py gate
```

이 저장소의 워크플로가 아니라 예시 단계입니다. gate를 통과해도 운영 승인이 아니며, 사람의 검토와 8단계의 holdout 규칙은 그대로 적용됩니다. [GitHub Actions에서 평가 실행](https://learn.microsoft.com/azure/foundry/how-to/evaluation-github-action)

## 레벨 3 마무리

보고에 다음을 더합니다: 생성된 rubric이 더하거나 놓친 것, 실제 공백을 드러낸 합성 질문, red team의 ASR, 그리고 내 릴리스 gate가 막을 대상.

**다음:** [10단계 정리](../README.ko.md#cleanup)로 돌아갑니다. 정리하면 생성된 rubric과 그 산출물, 합성 질문 데이터셋이 삭제되고, eval group과 red team 결과는 증거로 남습니다.

<a id="beyond"></a>

## 실습 범위 밖의 운영 기능

다음 기능은 실행 중인 에이전트나 강사 수준의 준비가 필요해 실습 경로에 넣지 않았습니다.

| 기능 | 필요한 것 | 공식 안내 |
|---|---|---|
| Foundry가 배포된 에이전트를 사례마다 직접 호출 | 배포된 에이전트. responses 또는 invocations 프로토콜의 hosted agent도 지원 | [hosted agent 평가](https://learn.microsoft.com/azure/foundry/observability/quickstarts/quickstart-evaluate-hosted-agent) |
| 운영 trace 평가 | 프로젝트 managed identity의 연결된 Application Insights 읽기 권한, 메시지 내용을 기록하는 trace. 이 실습의 에이전트는 기본적으로 메시지 내용 없이 trace를 기록합니다. | [trace 평가](https://learn.microsoft.com/azure/foundry/observability/how-to/cloud-evaluation-deployed-interactions#evaluate-traces-preview) |
| 연속·예약 평가 | 위와 같은 trace 접근 권한과 반복 구성 | [연속 평가 설정](https://learn.microsoft.com/azure/foundry/observability/how-to/how-to-monitor-agents-dashboard#set-up-continuous-evaluation) |
| 에이전트 red team(금지 행동, 민감 데이터 유출) | 에이전트 대상 | [클라우드에서 AI red teaming 실행](https://learn.microsoft.com/azure/foundry/how-to/develop/run-ai-red-teaming-cloud) |
