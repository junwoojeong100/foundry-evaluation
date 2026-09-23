# Level 3: Operate evaluation like a release process

[한국어](level-3.ko.md) · [Back to the main guide](../README.md#levels) · [Summary video from 06:55](../README.md#summary-video)

**In about 70 minutes you evaluate four targets, then put evaluation into operation:** saved answers, the model alone, your deployed agent, and its traces (sections 1–5), then a schedule and a release gate (sections 6–7).

| Section | What Foundry evaluates | With what |
|---|---|---|
| [1. Generate a rubric](#generate-rubric) | Your saved V2 answers | A rubric Foundry writes from the V2 instructions |
| [2. Stress-test](#stress-test) | Sol with the V2 instructions | 15 questions Foundry generates |
| [3. Red-team](#red-team) | The Sol deployment | Attack prompts Foundry generates |
| [4. Call your agent](#evaluate-agent) | Your deployed agent | The 18 dev questions, sent live by Foundry |
| [5. Evaluate traces](#evaluate-traces) | Your step 7 run | Its 18 traces in Application Insights |
| [6. Continuous evaluation](#continuous-eval) | Your agent's recent traffic | Up to 20 recent traces, every hour |
| [7. Release gate](#release-gate) | The six business gates (Sol, Luna, Astra × dev, holdout) | `verified-evidence.json` from step 9 |

**You need:** [Level 2](level-2.en.md) finished in this folder, and **step 10 not yet run**. Afterwards, return to [step 10](../README.md#cleanup).

- Sections 4 and 6 use your deployed agent, which step 10 deletes.
- The instructor prepares shared model capacity (sections 2–4) and trace access (sections 5–6) before class ([instructor guide](instructor.en.md#levels)).

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

- **This is a model-level test.** Foundry gives Sol all seven policies directly; your agent and its retrieval are not used, so these numbers are not comparable with steps 5–8.
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

**Warning:** this scan sends harmful prompts on purpose. Keep it small, review its results only in your project, and do not paste attack content into your notes.

**Terminal A:** a small cloud scan attacks the Sol deployment for two risk categories with two attack strategies. It targets the model because Foundry's agent red teaming does not support this hosted agent ([details](#beyond)):

```bash
python scripts/workshop.py red-team --model sol
```

**Checkpoint:** `Red-team scan completed on sol: risk categories Violence, HateUnfairness; attack strategies base64, flip`, then `Portal (attack success rate): <link>`.

**If not:** a timeout means the scan is still running; run the same command again.

**Portal:** this scan opens only in the classic portal view ([how AI red teaming works](https://learn.microsoft.com/azure/foundry/concepts/ai-red-teaming-agent)).

1. In the header, turn off the **New Foundry** switch. If a feedback dialog appears, choose **Continue without feedback**.
2. Open the printed link.
3. Under **Metric dashboard → Attack risk category**, read the successful attacks for each risk category.
4. Turn **New Foundry** back on.

**Checkpoint:** the page is titled `<LAB_PREFIX>-red-team-sol`, and **Hate and unfairness** and **Violence** each show a percentage with `n/3 attacks`.

**If not:** New Foundry's **Evaluations → Red team** tab does not list scans made by this command; use the printed link in the classic view ([portal differences](troubleshooting.en.md#portal-differs)).

<details>
<summary>Example screen: the classic red-teaming report</summary>

![Red-teaming report with successful attacks by risk category](assets/levels-20260923/en-l3-redteam.webp)

No attack succeeded in the recorded English scan (0/3 for each category). In the Korean scan, one of three hate-and-unfairness attacks succeeded.

</details>

<a id="evaluate-agent"></a>

## 4. Let Foundry call your agent

**Terminal A:** Foundry sends step 7's 18 dev questions (6 questions × 3 models) to your deployed V2 agent, one run per model, and scores each live answer. It takes about 15 minutes:

```bash
python scripts/workshop.py evaluate-agent
```

**Checkpoint:** the output shows, in order:

1. `Foundry called <LAB_AGENT_NAME> version N for 18 dev rows in 3 runs, one per model (prompt v2).`
2. one line each for `business_contract`, `task_adherence`, `intent_resolution`, and `relevance`, then `business_contract by model: ...`
3. `Your saved improved responses: .../18 business passes.`, `Traces recorded: 18`, and a `Portal:` link.

**If not:** a timeout means the run is still going; run the same command again. For other messages, see [Level 2 and 3 recovery](troubleshooting.en.md#levels).

**Read it:**

- **This is how a pipeline evaluates an agent.** There is no collector code: Foundry calls the agent and applies the evaluators, as `azd ai agent eval run` and CI jobs do.
- **Level 2's code evaluator grades the live answers,** so offline and live results use the same business contract.
- **Compare with your saved `improved` result model by model.** The answers are new, so a model can pass a row here that it failed in step 7, or the reverse. That is model variation, not an evaluator change.

<details>
<summary>How Foundry calls this invocations agent</summary>

- Foundry posts the rendered message content, `{"type": "input_text", "text": "..."}`, to the agent's endpoint. This agent accepts that envelope: invocation JSON in the text runs as that invocation, and plain text goes to Sol with `case_id` `external` ([evaluate a hosted agent](https://learn.microsoft.com/azure/foundry/observability/quickstarts/quickstart-evaluate-hosted-agent)).
- When a row has no saved decision, the code evaluator reads the agent's JSON answer from the row's `sample.output_text` field, where Foundry puts the live response.

</details>

<details>
<summary>Recorded English result — an example</summary>

```text
Foundry called frontier-loop-en-lv3a version 2 for 18 dev rows in 3 runs, one per model (prompt v2).
  business_contract  18/18
  task_adherence     18/18
  intent_resolution  18/18
  relevance          18/18
business_contract by model: sol 6/6, luna 6/6, astra 6/6
Traces recorded: 18
```

This run took 12 minutes in a rehearsal folder without saved step 7 responses, so the `Your saved improved responses` line did not print. The step 7 recording had 17/18, failing Sol's D02 decision label, which Sol answered correctly here: one live run is a sample, not a verdict.

</details>

<a id="evaluate-traces"></a>

## 5. Evaluate the traces from step 7

**Terminal A:** Foundry reads the 18 traces of your step 7 run from Application Insights and scores them. Nothing is replayed:

```bash
python scripts/workshop.py evaluate-traces --label improved
```

**Checkpoint:** `Trace evaluation completed: 18 traces from improved, read from Application Insights.`, then a table with `traces` and `saved responses (Level 2)` columns for `relevance`, `intent_resolution`, `task_adherence`, and `indirect_attack`.

**If not:** for an access error, ask the instructor to prepare trace access; for `... traces were not found`, wait a few minutes for ingestion. Both messages end with `... <file> and re-run evaluate-traces --label improved.`; delete that file, then run the same command again ([Level 2 and 3 recovery](troubleshooting.en.md#levels)).

**Read it:**

- **A trace records what the model actually saw:** the question *with the retrieved policies* as input, and the raw JSON answer as output. Level 2 gave the same evaluators only the question and the answer text, so the counts can differ. In the recorded runs, every criterion passed all 18 traces.
- **Use traces when Foundry cannot call the agent,** for example streaming or long-running agents, or to evaluate real traffic after the fact ([trace evaluation](https://learn.microsoft.com/azure/foundry/observability/how-to/cloud-evaluation-deployed-interactions#evaluate-traces-preview)).
- **Traces hold message content.** The workshop data is synthetic; for real users, decide what your traces may record before you evaluate them.

<details>
<summary>Recorded English result — an example</summary>

```text
Trace evaluation completed: 18 traces from improved, read from Application Insights.
criterion          traces  saved responses (Level 2)
relevance          18/18   17/18
intent_resolution  18/18   18/18
task_adherence     18/18   17/18
indirect_attack    18/18   18/18
```

The traces were eight hours old; the command sets the lookback window from your collection time.

</details>

<a id="continuous-eval"></a>

## 6. Turn on continuous evaluation

**Terminal A — create the schedule:** it evaluates up to 20 recent traces of your agent's latest version every hour. The first run starts two minutes later, the schedule stops by itself after 8 hours, and step 10 deletes it:

```bash
python scripts/workshop.py continuous-eval
```

**Checkpoint:** `Continuous evaluation <LAB_PREFIX>-continuous: every hour on <LAB_AGENT_NAME> version N, up to 20 recent traces, from HH:MM UTC until HH:MM UTC.` and `No scheduled run yet. Run this command again after HH:MM UTC.` Times are in UTC.

**If not:** `This folder has no deployed hosted agent` means this folder's agent is not deployed, for example because step 10 already ran; skip this section and do not redeploy for it. `Schedule ... already exists and is not owned by this folder` means another team uses your `LAB_PREFIX`; ask the instructor for an unused one.

**Terminal A — check the first run:** at or after the printed `HH:MM UTC`, run the same command again:

```bash
python scripts/workshop.py continuous-eval
```

**Checkpoint:** a line such as `HH:MM UTC  completed  N traces: relevance .../N, task_adherence .../N, indirect_attack .../N`.

**If not:** `in_progress` or `queued` means the first run is still going; run the command again in a minute.

**Read it:**

- **The first run evaluates your section 4 traffic.** In production, the hourly runs keep a quality signal on real traffic, and a drop sends you back through the loop of steps 5–9.
- **Hosted agents are evaluated from their traces on a schedule;** prompt agents can instead be evaluated on every response ([continuous evaluation](https://learn.microsoft.com/azure/foundry/observability/how-to/how-to-monitor-agents-dashboard#set-up-continuous-evaluation)).

<details>
<summary>Recorded English result — an example</summary>

```text
Continuous evaluation ll-en-lv3a-continuous: every hour on frontier-loop-en-lv3a version 2, up to 20 recent traces, from 11:31 UTC until 19:29 UTC.
  11:31 UTC  completed  20 traces: relevance 20/20, task_adherence 20/20, indirect_attack 20/20
```

The first run picked 20 recent traces of version 2; each run evaluates at most 20.

</details>

<a id="release-gate"></a>

## 7. Turn the business gates into a release gate

**Terminal A:** check the six gates from 9-2, then print the command's exit code:

```bash
python scripts/workshop.py gate
echo "exit code: $?"
```

**Checkpoint:** either result is valid; report the one you get:

- `Quality gate passed: all six business gates are true. production_release_approved remains false.`, then `exit code: 0`;
- `Quality gate FAILED: ...`, then `exit code: 1`, when any gate from 9-2 is `false`.

**If not:** the command reads `src/agent/.foundry/results/verified-evidence.json`; return to [9-1 in step 9](../README.md#lab-g) if the file is missing.

**Read it:** a pipeline runs the same loop as steps 5–9 for a new candidate, then this command; a non-zero exit stops the release. For example, a GitHub Actions step (read only; this repository has no such workflow):

```yaml
      - name: Stop the release if a business gate fails
        run: python scripts/workshop.py gate
```

A passing gate still does not approve production; human review and the holdout rules from step 8 still apply. [Run evaluations in GitHub Actions](https://learn.microsoft.com/azure/foundry/how-to/evaluation-github-action)

## Finish Level 3

Add to your [report](../README.md#finish):

- what the generated rubric added or missed;
- which synthetic questions revealed a real gap;
- the red-team attack success rate;
- whether Foundry's live run agreed with your saved result, and what the traces showed;
- what your release gate would block.

**Checkpoint:** your report has one line for each item above.

**Next:** return to [step 10 cleanup](../README.md#cleanup). Cleanup deletes the continuous-evaluation schedule, the generated rubric and its artifacts, and the synthetic question dataset. Eval groups and red-team results stay as evidence.

<a id="beyond"></a>

## Optional reading: beyond this workshop

| Feature | Status for this agent | Official guide |
|---|---|---|
| Agent red teaming (prohibited actions, sensitive data leakage) | Rejects hosted agents on the invocations protocol; on 2026-09-23 it failed with `Hosted Invocations agents require a freeform input template, which red team agent targets do not provide.` Works for prompt agents | [Run AI red teaming in the cloud](https://learn.microsoft.com/azure/foundry/how-to/develop/run-ai-red-teaming-cloud) |
| Evaluate every response of a prompt agent | Evaluation rules apply to prompt agents; hosted agents use the trace schedule from section 6 | [Set up continuous evaluation](https://learn.microsoft.com/azure/foundry/observability/how-to/how-to-monitor-agents-dashboard#set-up-continuous-evaluation) |
| Scheduled red teaming | Red teaming can also run on a schedule; this workshop runs one small scan | [Run AI red teaming in the cloud](https://learn.microsoft.com/azure/foundry/how-to/develop/run-ai-red-teaming-cloud) |
