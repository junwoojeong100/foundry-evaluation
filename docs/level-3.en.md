# Level 3: Operate evaluation like a release process

[한국어](level-3.ko.md) · [Back to the main guide](../README.md#levels)

**In about 40 minutes you will:**

1. Let Foundry **generate a rubric** from your V2 instructions and compare it with your hand-authored rubric.
2. **Stress-test** the V2 instructions on questions Foundry generates for you.
3. **Red-team** the candidate model with adversarial attack strategies.
4. Turn the six business gates into a **release gate** that a CI pipeline can enforce.

**You need:** [Level 2](level-2.en.md) finished in the same folder, and **step 10 not yet run**. Sections 2 and 3 call the shared Sol deployment and the judge; the instructor confirms their capacity before class.

<a id="generate-rubric"></a>

## 1. Generate a rubric and compare it with yours

**Terminal A:** Foundry reads your V2 instructions, proposes weighted dimensions, and both rubrics then score your V2 responses:

```bash
python scripts/workshop.py generate-rubric --label improved
```

**Checkpoint:** `Generated rubric: <LAB_PREFIX>-generated-rubric version 1, pass threshold ...`, a list of dimensions with weights, then `policy_rubric: .../18 passed on improved` and `generated_rubric: .../18 passed on improved`, each with its failed rows or `none`.
**If not:** a timeout means generation or scoring is still running; run the same command again. For other errors, see [Level 2 and 3 recovery](troubleshooting.en.md#levels).

**Read it:**

- **Review the generated dimensions like code.** Generation uses an LLM, so your dimensions and weights can differ from another team's, and between runs.
- **Compare the failed rows with Level 2's `business_contract`.** In the recorded run both rubrics passed all 18 V2 rows, including Sol's D02 wrong decision label that the contract check failed. A rubric judges quality; it does not replace a deterministic contract.

<details>
<summary>Recorded English result — an example</summary>

```text
Generated rubric: ll-en-0923b-generated-rubric version 1, pass threshold 0.5
  - decision_label_correctness (weight 9)
  - policy_date_alignment (weight 6)
  - citation_accuracy (weight 5)
  - missing_information_handling (weight 4)
  - format_compliance (weight 3)
  - policy_grounding_only (weight 5)
  - general_quality (weight 5)
policy_rubric: 18/18 passed on improved; failed rows: none
generated_rubric: 18/18 passed on improved; failed rows: none
```

</details>

<a id="stress-test"></a>

## 2. Stress-test V2 on synthetic questions

**Terminal A:** Foundry generates 15 new travel-policy questions, sends each to the Sol deployment with the V2 instructions and all seven policies, and scores the answers:

```bash
python scripts/workshop.py stress-test --model sol --count 15
```

**Checkpoint:** `Stress test completed on sol: N of 15 synthetic questions failed an evaluator`, one line each for `intent_resolution`, `relevance`, and `indirect_attack`, then the failed questions.
**If not:** a timeout means the run is still going; run the same command again. Foundry requires at least 15 questions.

**Read it:**

- **This is a model-level test.** The agent's retrieval is not used, so these numbers are not comparable with steps 5–8.
- **Counts change between runs,** because Foundry generates new questions each time. Compare failure patterns, not counts.
- **Sort each failed question** into a real gap (for example, overseas trips the policy does not cover), a judge penalizing a correct deferral, or a safety flag. Good questions become new dev cases only after you write a fixed reference for them; never tune on holdout.

<details>
<summary>Recorded English result — an example</summary>

```text
Stress test completed on sol: 6 of 15 synthetic questions failed an evaluator
  intent_resolution: 12/15
  relevance: 11/15
  indirect_attack: 15/15
```

Most failures were trips to Chicago or London, which the domestic policy does not cover, and requests for exceptions. A second run on newly generated questions had 4 of 15 failures with the same pattern: trips to Chicago and New York, and a request to ignore the policy. The Korean run flagged one `indirect_attack` answer, to a request to book overseas costs under another expense category.

</details>

<a id="red-team"></a>

## 3. Red-team the candidate model

**Terminal A:** a small cloud scan attacks the Sol deployment for two risk categories with two attack strategies:

```bash
python scripts/workshop.py red-team --model sol
```

**Checkpoint:** `Red-team scan completed on sol: risk categories Violence, HateUnfairness; attack strategies base64, flip`, then `Portal (attack success rate): <link>`.
**If not:** a timeout means the scan is still running; run the same command again.

**Portal:** open the printed link and read the **attack success rate (ASR)** by risk category and attack strategy ([how AI red teaming works](https://learn.microsoft.com/azure/foundry/concepts/ai-red-teaming-agent)).

**Checkpoint:** the red-teaming page for this scan opens and shows its attack success rate.
**If not:** see [portal differences](troubleshooting.en.md#portal-differs).

**Warning:** red teaming generates harmful prompts on purpose. Keep the scan small, review its results only in your project, and do not paste attack content into the workshop notes.

<a id="release-gate"></a>

## 4. Turn the business gates into a release gate

**Terminal A:**

```bash
python scripts/workshop.py gate
```

**Checkpoint:** `Quality gate passed: all six business gates are true. production_release_approved remains false.` and exit code 0. If any gate from 9-2 is `false`, it prints `Quality gate FAILED: ...` and exits with code 1.
**If not:** the command reads `src/agent/.foundry/results/verified-evidence.json`; return to [9-1](../README.md#lab-g) if the file is missing.

A pipeline runs the same loop as steps 5–9 for a new candidate and then this command; a non-zero exit stops the release:

```yaml
      - name: Stop the release if a business gate fails
        run: python scripts/workshop.py gate
```

This is an example step, not a workflow in this repository. A passing gate still does not approve production; human review and the holdout rules from step 8 still apply. [Run evaluations in GitHub Actions](https://learn.microsoft.com/azure/foundry/how-to/evaluation-github-action)

## Finish Level 3

Add to your report: what the generated rubric added or missed, which synthetic questions revealed a real gap, the red-team ASR, and what your release gate would block.

**Next:** return to [step 10 cleanup](../README.md#cleanup). Cleanup deletes the generated rubric, its artifacts, and the synthetic question dataset. Eval groups and red-team results stay as evidence.

<a id="beyond"></a>

## Beyond this workshop

These production features need a live agent or instructor-level preparation, so they are not part of the hands-on path:

| Feature | What it needs | Official guide |
|---|---|---|
| Foundry calls your deployed agent for each test case | A deployed agent; hosted agents that use the responses or invocations protocol are supported | [Evaluate your hosted agent](https://learn.microsoft.com/azure/foundry/observability/quickstarts/quickstart-evaluate-hosted-agent) |
| Evaluate production traces | The project's managed identity must read the connected Application Insights, and traces must record message content. This workshop's agent records traces without message content by default. | [Trace evaluation](https://learn.microsoft.com/azure/foundry/observability/how-to/cloud-evaluation-deployed-interactions#evaluate-traces-preview) |
| Continuous or scheduled evaluation | The same trace access, plus a recurring configuration | [Set up continuous evaluation](https://learn.microsoft.com/azure/foundry/observability/how-to/how-to-monitor-agents-dashboard#set-up-continuous-evaluation) |
| Agent red teaming (prohibited actions, sensitive data leakage) | An agent target | [Run AI red teaming in the cloud](https://learn.microsoft.com/azure/foundry/how-to/develop/run-ai-red-teaming-cloud) |
