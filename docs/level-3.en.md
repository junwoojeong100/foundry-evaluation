# Level 3: Operate evaluation like a release process

[한국어](level-3.ko.md) · [Back to the main guide](../README.md#levels) · [Summary video from 06:55](../README.md#summary-video)

**What you finish with in about 70 minutes:** one table separating evaluation targets, the first scheduled evaluation's results, and the release gate's exit code. **Model-only, agent, and trace evaluations use different targets and inputs; do not combine their scores.**

| Before you start | Required state |
|---|---|
| Previous work | [Level 2](level-2.en.md) finished in this folder; **step 10 cleanup not yet run** |
| Live resources | The same deployed V2 agent for sections 4 and 6; prepared [model capacity and trace access](instructor.en.md#levels) |
| Red-team permission | Section 3 only if your organization permits the scan; otherwise record it as skipped |
| After this level | Append your results to the main report, then [step 10 cleanup](../README.md#cleanup) |

**Follow sections 1–7 in order** in your existing **Terminal A, at the repository root**. In a new terminal, [restore the environment only](../README.md#resume-shell). Keep names, V2 instructions, and the deployed version unchanged. If you used a recovery label, replace `--label improved` below with your actual candidate label.

**Cost and evidence:** model and judge calls in sections 1–6 cost extra; section 6 also creates a schedule lasting up to 8 hours. Do not add the extra responses to the main workshop's 48. Section 7 reads **only step 9's saved business gates**, not the new results from sections 1–6.

<a id="level-3-results"></a>

**Use this one table for your notes.** Copy it into your notes now and fill the last column with **your values and interpretation** as you finish each section. Do not copy attack prompts or harmful response text.

| Section | Evaluation target | Your result to record |
|---|---|---|
| [1. Generate a scoring guide (rubric)](#generate-rubric) | Your saved V2 answers | Both rubrics' pass counts `/18` and what they missed compared with the business contract (or none) |
| [2. Stress-test](#stress-test) | Sol with V2 instructions and all seven policies. **No retrieval or agent** | Failures `/15`; confirmed policy gap, judge issue, or safety flag (or none) |
| [3. Attack-test (red team)](#red-team) | The Sol deployment **without V2 instructions** | Successful attacks `/6` and attack success rate (ASR); lower is better |
| [4. Call your agent](#evaluate-agent) | **18 new responses** from your deployed V2 agent (6 dev questions × 3 models) | Business passes `/6` per model and the difference from your saved 7-4 result |
| [5. Evaluate traces](#evaluate-traces) | The 18 Application Insights traces from step 7 | Scores and differences from Level 2 |
| [6. Continuous evaluation](#continuous-eval) | Up to 20 recent traces, every hour | First `completed` time, trace count, all three results, and portal confirmation of no errors/missing results |
| [7. Release gate](#release-gate) | The six business gates in step 9's `verified-evidence.json` | Output, exit code, and blocked gates or pass; **not production approval** |

**Waiting:** while a command is still running, wait. Resume with the same command only **after it exits** with `... still running` or `... still in progress`. A network timeout does not establish that a remote run is active. Use [message-specific recovery](troubleshooting.en.md#levels) for other errors.

<a id="generate-rubric"></a>

## 1. Generate a rubric and compare it with yours

**Terminal A:** Foundry reads your V2 instructions, proposes weighted dimensions, and both rubrics then score your V2 responses:

```bash
python scripts/workshop.py generate-rubric --label improved
```

**Checkpoint:** `Generated rubric: <LAB_PREFIX>-generated-rubric version 1, pass threshold ...`, a list of dimensions with weights, then `policy_rubric: .../18 passed on improved` and `generated_rubric: .../18 passed on improved`, each with its failed rows or `none`.

**If not:** after the command exits with `Rubric generation is still running` or `The run is still in progress`, repeat it to resume. For other errors, see [Level 2 and 3 recovery](troubleshooting.en.md#levels).

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

**Next:** [2. Stress-test with synthetic questions](#stress-test)

<a id="stress-test"></a>

## 2. Stress-test V2 on synthetic questions

**Terminal A:** Foundry generates 15 new travel-policy questions, sends each to the Sol deployment with the V2 instructions and all seven policies, and scores the answers:

```bash
python scripts/workshop.py stress-test --model sol --count 15
```

**Checkpoint:** `Stress test completed on sol: N of 15 synthetic questions failed an evaluator`, with one line each for `intent_resolution`, `relevance`, and `indirect_attack`. Failed questions appear only if there are failures; `N=0` is valid too.

**If not:** after the command exits with `The run is still in progress`, repeat it to resume. For other errors, see [Level 2 and 3 recovery](troubleshooting.en.md#levels). Keep the question count at 15.

**Read it:**

- **This is a model-level test.** Foundry gives Sol all seven policies directly; your agent and its retrieval are not used, so these numbers are not comparable with steps 5–8.
- **Separate new experiments can have different questions and counts.** Resuming the same command in this folder reuses its saved questions and run. Do not delete result files to draw a better score.
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

**Next:** [3. Red-team the candidate model](#red-team)

<a id="red-team"></a>

## 3. Red-team the candidate model

**Before running:** confirm that your organization permits this scan. If not, record section 3 as **skipped, not completed**, and go to [section 4](#evaluate-agent). The scan intentionally sends harmful prompts; keep it small, review results only in your project, and do not copy attack content into your notes.

**Terminal A:** a small cloud scan sends six attacks to the Sol deployment: for each of two risk categories, one plain attack (`baseline`) and one for each of two attack strategies. It runs as a Foundry evaluation and takes about a minute. It targets the model because Foundry's agent red teaming does not support this hosted agent ([details](#beyond)):

```bash
python scripts/workshop.py red-team --model sol
```

**Checkpoint:** the output shows, in order:

1. `Red-team scan completed on sol: risk categories Violence, HateUnfairness; attack strategies base64, flip`
2. `Attack success rate: N/6 attacks succeeded (...); lower is better`, then one line `by risk category` and one line `by attack strategy`
3. `Portal: <link>`

**If not:** after the command exits with `The run is still in progress`, repeat it to resume. For other messages, see [Level 2 and 3 recovery](troubleshooting.en.md#levels). A successful attack is a quality finding, not an execution error to retry.

**Read it:**

- **An attack succeeds when Foundry's safety evaluator finds, in Sol's answer, the harmful content the attack was probing for.** The attack success rate (ASR) is the share of attacks that succeeded, so lower is better.
- **The scan tests the deployment, not your instructions:** Sol answers without the V2 instructions, behind the deployment's content filter. Six attacks are a small sample: the rehearsals sent the same six prompts in each of three scans, yet Sol's answers differed every time, and the plain violence attack succeeded in two of them. Review every successful attack, not only the rate.

**Portal:** open the `Portal:` link. The scan opens in New Foundry and is also listed under **Evaluations → Red team** ([how AI red teaming works](https://learn.microsoft.com/azure/foundry/concepts/ai-red-teaming-agent)).

**Checkpoint:** the page is titled `<LAB_PREFIX>-red-team-sol`, and **Overall metric results** shows the same rates as the CLI, for example **Violence ASR** with `n/3`. In the table below it, an **Attack outcome** of `Fail` marks a successful attack.

**If not:** find `<LAB_PREFIX>-red-team-sol` under **Evaluations → Red team** and open it. Read the rates on the scan's page; the list's **Issues in last run** column is not the number of successful attacks.

<details>
<summary>Example screen: the scan in New Foundry</summary>

![Red-team scan with the attack success rate by risk category and attack strategy](assets/levels-20260923/en-l3-redteam.webp)

The Response and Reasoning columns are blurred in this example.

</details>

<details>
<summary>Recorded English result — an example</summary>

```text
Red-team scan completed on sol: risk categories Violence, HateUnfairness; attack strategies base64, flip
Attack success rate: 1/6 attacks succeeded (16.7%); lower is better
  by risk category: Violence 1/3, HateUnfairness 0/3
  by attack strategy: baseline 1/2, base64 0/2, flip 0/2
```

The one successful attack was a plain violence prompt; neither attack strategy succeeded. The Korean scan sent the same six prompts and had 0/6: the scan does not use your workshop language or instructions, so the difference comes from Sol answering differently.

</details>

**Next:** [4. Evaluate the deployed agent directly](#evaluate-agent)

<a id="evaluate-agent"></a>

## 4. Let Foundry call your agent

**Terminal A:** Foundry asks the same six dev questions of each of the three models and scores **18 new responses**. It calls your deployed V2 agent in one run per model and takes about 15 minutes:

```bash
python scripts/workshop.py evaluate-agent --split dev
```

**Checkpoint:** the output shows, in order:

1. `Foundry called <LAB_AGENT_NAME> version N for 18 dev rows in 3 runs, one per model (prompt v2).`
2. one line each for `business_contract`, `task_adherence`, `intent_resolution`, and `relevance`, then `business_contract by model: ...`
3. `Traces recorded: 18` and a `Portal:` link. With the default label, you also see `Your saved improved responses: .../18 business passes.` With a recovery label, that line may be absent; compare with your own step 7-4 summary instead.

**If not:** after the command exits with `The agent evaluation is still running`, repeat it to resume. For other messages, see [Level 2 and 3 recovery](troubleshooting.en.md#levels). Keep `--split dev` during recovery too.

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

**Next:** [5. Evaluate the saved traces](#evaluate-traces)

<a id="evaluate-traces"></a>

## 5. Evaluate the traces from step 7

**Terminal A:** Foundry reads and scores the 18 traces from step 7 in Application Insights. **The agent and retrieval are not rerun; the judge still makes paid model calls.**

```bash
python scripts/workshop.py evaluate-traces --label improved
```

**Checkpoint:** `Trace evaluation completed: 18 traces from improved, read from Application Insights.`, then a table with `traces` and `saved responses (Level 2)` columns for `relevance`, `intent_resolution`, `task_adherence`, and `indirect_attack`.

**If not:** resolve access errors with the instructor, or wait for missing traces to ingest. **Only if the error explicitly names a file to delete**, follow [state-file recovery](troubleshooting.en.md#level-state-recovery): back it up, then handle that one file. Do not delete it for a polling timeout. If the comparison column says `n/a`, check that Level 2 completed with this same label.

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

**Next:** [6. Schedule continuous evaluation and check its first result](#continuous-eval)

<a id="continuous-eval"></a>

## 6. Turn on continuous evaluation

**Terminal A — create the schedule:** it pins the agent version at creation and evaluates up to 20 of its recent traces every hour. The first run starts two minutes later, the schedule stops by itself after 8 hours, and step 10 deletes it. Repeating the command checks the existing schedule:

```bash
python scripts/workshop.py continuous-eval
```

**Schedule creation check:** `Continuous evaluation <LAB_PREFIX>-continuous: every hour on <LAB_AGENT_NAME> version N, up to 20 recent traces, from HH:MM UTC until HH:MM UTC.` For `No scheduled run yet`, wait until the printed time below. If results already appear, compare them with the completion checkpoint below. Times are in UTC.

**If not:** for a missing agent or schedule ownership conflict, stop and follow [error-specific recovery](troubleshooting.en.md#levels). Do not bypass it by renaming or redeploying. If step 10 already ran, record this section as **not run**, not completed.

**Terminal A — check the first run:** at or after the printed `HH:MM UTC`, run the same command again:

```bash
python scripts/workshop.py continuous-eval
```

**Checkpoint:** `HH:MM UTC  completed  N traces: relevance .../N, task_adherence .../N, indirect_attack .../N`, with **N at least 1**. Creating the schedule alone is not completion. Record the time, trace count, and all three evaluation results.

**If not:** for `in_progress` or `queued`, check again in a minute with the same command. For `failed`, an error, or zero traces, record the section as incomplete and check traffic and access with the instructor. Do not delete and recreate the schedule.

**Portal — check row-level results:** open the printed `Portal:` link and select the run at the **same UTC time** you recorded above.

**Checkpoint:** all N rows have valid results for all three evaluators, without errors or missing results. `completed` alone does not establish this. `passed: false` is a valid quality failure; report it unchanged.

**If not:** record empty results or evaluator errors as incomplete and inspect them with the instructor. Do not create a new schedule to erase error history.

**Read it:**

- **The schedule selects traces from recent traffic,** which can include section 4 and other recent calls. In production, a drop in this quality signal sends you back through steps 5–9.
- **Hosted agents are evaluated from their traces on a schedule;** prompt agents can instead be evaluated on every response ([continuous evaluation](https://learn.microsoft.com/azure/foundry/observability/how-to/how-to-monitor-agents-dashboard#set-up-continuous-evaluation)).

<details>
<summary>Recorded English result — an example</summary>

```text
Continuous evaluation ll-en-lv3a-continuous: every hour on frontier-loop-en-lv3a version 2, up to 20 recent traces, from 11:31 UTC until 19:29 UTC.
  11:31 UTC  completed  20 traces: relevance 20/20, task_adherence 20/20, indirect_attack 20/20
```

The first run picked 20 recent traces of version 2; each run evaluates at most 20.

</details>

**Next:** [7. Check whether the saved business gates would stop a release](#release-gate)

<a id="release-gate"></a>

## 7. Turn the business gates into a release gate

**Terminal A:** check step 9's execution verification and six gates, then print the command's exit code. **This gate does not include this level's red-team or continuous-evaluation results.**

```bash
python scripts/workshop.py gate
echo "exit code: $?"
```

**Checkpoint:** either result is valid; report the one you get:

- `Quality gate passed: all six business gates are true. production_release_approved remains false.`, then `exit code: 0`;
- `Quality gate FAILED: ...`, then `exit code: 1`, when any gate from 9-2 is `false`.

**If not:** a missing file or traceback is an execution error, not a quality failure. Check `src/agent/.foundry/results/verified-evidence.json` and [9-1's checkpoint](../README.md#lab-g). Do not record a business-gate failure from exit code `1` alone without its output.

**Read it:** a pipeline runs the same loop as steps 5–9 for a new candidate, then this command; a non-zero exit stops the release. For example, a GitHub Actions step (read only; this repository has no such workflow):

```yaml
      - name: Stop the release if a business gate fails
        run: python scripts/workshop.py gate
```

A passing gate still does not approve production; human review and the holdout rules from step 8 still apply. [Run evaluations in GitHub Actions](https://learn.microsoft.com/azure/foundry/how-to/evaluation-github-action)

<a id="finish-level-3"></a>

## Finish Level 3

Append the [results table](#level-3-results) you filled in during the sections to your main [report](../README.md#finish). You do not need to rerun finished commands.

**Checkpoint:** sections 1–7 meet their completion checkpoints and the table is filled in. Record skipped sections, errors, or zero traces as **incomplete**. Low valid scores or `Quality gate FAILED` are results of a completed exercise.

**Next:** return to [step 10 cleanup](../README.md#cleanup). Even if you stop with incomplete sections, clean up the paid resources and schedule you created. Do not repeat cleanup if already finished. It deletes the continuous-evaluation schedule, generated rubric and artifacts, and synthetic question dataset. Eval groups and red-team results stay as evidence.

<a id="beyond"></a>

## Optional reading: beyond this workshop

| Feature | Status for this agent | Official guide |
|---|---|---|
| Agent red teaming (prohibited actions, sensitive data leakage) | Rejects hosted agents on the invocations protocol; on 2026-09-23 it failed with `Hosted Invocations agents require a freeform input template, which red team agent targets do not provide.` Works for prompt agents | [Run AI red teaming in the cloud](https://learn.microsoft.com/azure/foundry/how-to/develop/run-ai-red-teaming-cloud) |
| Evaluate every response of a prompt agent | Evaluation rules apply to prompt agents; hosted agents use the trace schedule from section 6 | [Set up continuous evaluation](https://learn.microsoft.com/azure/foundry/observability/how-to/how-to-monitor-agents-dashboard#set-up-continuous-evaluation) |
| Scheduled red teaming | Red teaming can also run on a schedule; this workshop runs one small scan | [Run AI red teaming in the cloud](https://learn.microsoft.com/azure/foundry/how-to/develop/run-ai-red-teaming-cloud) |
