# Level 2: Evaluate your business rules in Foundry

[한국어](level-2.ko.md) · [Back to the main guide](../README.md#levels) · [Summary video from 06:33](../README.md#summary-video)

**What you finish with in about 40 minutes:** a comparison of the same 36 saved V1 and V2 responses, with an explanation that **distinguishes business checks from LLM scores**.

1. [Register](#register-evaluators) the five decision, amount, and citation checks (your **business contract**) as a **code evaluator**, and a scoring guide as a **rubric evaluator**.
2. [Evaluate](#evaluate-suite) your saved V1 and V2 responses with **nine evaluators in one comparison group (eval group)**.
3. [Read](#insights) Foundry's **run comparison** (statistical test) and **failure clusters**.

**You need:** steps 1–9 of the [main guide](../README.md) finished in this folder, and **step 10 not yet run**.

- No new agent responses are collected; only the judge model is called (**additional cost**).
- Afterwards, go on to [Level 3](level-3.en.md) or return to [step 10](../README.md#cleanup), which also deletes the evaluators you create here.

**Where to run:** your existing **Terminal A, at the repository root**. In a new terminal, [restore the environment only](../README.md#resume-shell). Keep names and instructions unchanged. If you used recovery labels, replace `baseline` and `improved` below with those labels.

**How to proceed:** follow sections 1–3 in order. Read pass counts in section 2, then mean scores and failure causes in section 3, and add them to your [closing notes](#finish-level-2). You can finish without opening the example scores or optional portal view.

<a id="register-evaluators"></a>

## 1. Register two custom evaluators

**Terminal A:**

```bash
python scripts/workshop.py register-evaluators
```

**Checkpoint:** two lines, `Registered <LAB_PREFIX>-business-contract version 1 (code)` and `Registered <LAB_PREFIX>-policy-rubric version 1 (rubric)`. Running the command again prints `Reusing ...` and creates nothing.

**If not:** for `already exists and is not owned by this folder`, stop and check the ownership conflict with the instructor. Do not change `LAB_PREFIX` in this folder's `.env` or delete another team's evaluator. See [Level 2 and 3 recovery](troubleshooting.en.md#levels).

**Read it:** your project now has two reusable evaluators: a code evaluator that runs the five business checks exactly, and a rubric evaluator whose LLM judge scores policy quality.

<details>
<summary>What the two evaluators contain</summary>

| Evaluator | Type | What it scores | Pass rule |
|---|---|---|---|
| `<LAB_PREFIX>-business-contract` | Code (Python runs in Foundry) | The same five checks as `scripts/grading.py`: decision, required amounts, citations retrieved, citations allowed, and a citation when required | Score is the share of passed checks; a row passes only at 1.0 |
| `<LAB_PREFIX>-policy-rubric` | Rubric (LLM judge) | Five weighted dimensions: effective policy, decision matches policy, cites document IDs, defers when uncovered, resists policy bypass | Weighted 1–5 scores, normalized; passes at 0.7 |

Both are objects in your project's evaluator catalog, prefixed with your `LAB_PREFIX` and recorded in this folder's ownership file for cleanup. The definitions are in `scripts/foundry_eval.py`.

</details>

**Next:** [2. Evaluate the saved V1 and V2 responses](#evaluate-suite)

<a id="evaluate-suite"></a>

## 2. Evaluate V1 and V2 with nine evaluators

**Terminal A:** this reads the saved `baseline` and `improved` responses and runs them one after the other in one eval group; it takes several minutes:

```bash
python scripts/workshop.py evaluate-suite --labels baseline improved
```

**Checkpoint:** `Suite evaluation completed: ... (baseline, improved)`, a table with nine rows and a `Portal:` link. The `business_contract` row matches the business passes from your 7-4 summary.

**If not:** if the command exited with `The suite is still running`, repeat the same command to resume its saved run. If it is still running in your terminal, wait. For other errors, see [Level 2 and 3 recovery](troubleshooting.en.md#levels).

<details>
<summary>Retry a failed run — only when a failed run or errored results are confirmed</summary>

In `evaluator results failed, for example because the judge hit its rate limit`, rate limiting is **one possible cause**. Inspect the saved error and resolve its cause. For 429, wait as directed by `Retry-After`, then run this. Do not use it for low valid scores.

```bash
python scripts/workshop.py evaluate-suite --labels baseline improved --retry-failed
```

Only failed runs are replaced; earlier attempts remain recorded. If the same error recurs, stop retrying and tell the instructor.

</details>

**Read your table in this order:**

1. **Start with `business_contract`.** Record V1 → V2 pass counts and check that they match your local business checks from 7-4.
2. **Compare `policy_rubric` with `policy_rubric_no_evidence`.** The former receives the question plus retrieved policy text; the latter receives only the question. Note whether the same rubric's pass counts changed when the judge had evidence.
3. **Record one change in the remaining generic and safety evaluators** (or none). They measure their own criteria, such as groundedness, relevance, and safety, rather than replacing `business_contract` checks for your decisions, amounts, and citations.

<details>
<summary>Recorded English result (September 23, 2026 responses) — an example, not your target</summary>

```text
criterion                  kind     baseline  improved
business_contract          code     0/18      17/18
policy_rubric              rubric   7/18      18/18
policy_rubric_no_evidence  rubric   1/18      8/18
groundedness               RAG      18/18     18/18
relevance                  RAG      16/18     17/18
response_completeness      quality  18/18     18/18
task_adherence             agent    17/18     17/18
intent_resolution          agent    17/18     18/18
indirect_attack            safety   18/18     18/18
```

`business_contract` matches the recorded local result (0/18 → 17/18). The remaining V2 failure is Sol's D02 decision label; `policy_rubric` passed that row, which is why a deterministic contract check and an LLM rubric complement each other.

A second run on the same saved responses gave identical `business_contract` counts, while LLM-judged counts moved by one to three rows (for example, `policy_rubric` on baseline went from 7/18 to 10/18). Compare LLM-judged criteria by their direction, not by a single row.

</details>

<details>
<summary>The nine evaluators and what each receives</summary>

| Criterion | Kind | Receives | Default pass rule |
|---|---|---|---|
| `business_contract` | Custom code | Every field of the row: decision, amounts, citations, retrieved IDs, allowed IDs | All five checks pass |
| `policy_rubric` | Custom rubric | Question **plus retrieved evidence**; answer, decision, and citations | 0.7 |
| `policy_rubric_no_evidence` | Custom rubric | Question only; answer, decision, and citations | 0.7 |
| `groundedness` | Built-in RAG | Question, answer text, retrieved evidence | 4 of 5 |
| `relevance` | Built-in RAG | Question, answer text | 4 of 5 |
| `response_completeness` | Built-in quality | Answer text, fixed reference answer | 3 of 5 |
| `task_adherence` | Built-in agent | Question, answer text | Pass/fail |
| `intent_resolution` | Built-in agent | Question, answer text | 3 of 5 |
| `indirect_attack` | Built-in safety | Question, answer text | No manipulated content |

Details: [built-in evaluators](https://learn.microsoft.com/azure/foundry/concepts/built-in-evaluators) · [custom evaluators](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/custom-evaluators) · [rubric evaluators](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/rubric-evaluators)

</details>

**Next:** [3. Compare runs and cluster failures](#insights)

<a id="insights"></a>

## 3. Compare the runs and cluster the failures

**Terminal A:** Foundry compares section 2's `baseline` and `improved` runs and groups the `improved` run's failures into clusters:

```bash
python scripts/workshop.py insights --baseline baseline --candidate improved
```

**Checkpoint:** the output shows, in order:

1. a `Comparison (candidate vs baseline):` table with `delta`, `p`, and `effect` for all nine criteria;
2. `Failure clusters in the candidate run [evaluator that failed each sample]:` with a list, or `none`.

**If not:** for `Run evaluate-suite ... first`, return to section 2's checkpoint. If the command exited with `Insights are still generating`, repeat it to resume. For `... insight failed`, follow [error-specific recovery](troubleshooting.en.md#levels).

**Read it:**

- **Section 2 shows pass counts; this table shows mean scores.** `baseline` and `candidate` are each evaluator's averages; `delta` is candidate minus baseline. A contract score of `0.60` means some individual checks passed, not that 60% of responses passed.
- **An `effect` of `Changed` means a difference, not necessarily an improvement.** Read `delta` and the evaluator's desired direction together. `Inconclusive` does not prove equivalence. Note the small sample of 18 rows ([statistical comparison legend](https://learn.microsoft.com/azure/foundry/how-to/evaluate-results#compare-the-evaluation-results)).
- **Read the source evaluator before the cluster's name.** Many `policy_rubric_no_evidence` failures suggest missing judge evidence, but inspect the same response and fixed reference before deciding whether the agent is wrong. For `business_contract` failures, identify the particular failed check.

<details>
<summary>Recorded English insights — an example</summary>

```text
criterion                  baseline  candidate  delta  p      effect
business_contract          0.60      0.99       +0.39  0.000  Changed
policy_rubric              0.68      0.93       +0.25  0.000  Changed
policy_rubric_no_evidence  0.30      0.62       +0.32  0.000  Changed
groundedness               5.00      5.00       +0.00  1.000  Inconclusive
relevance                  4.06      4.33       +0.28  0.151  Inconclusive
```

Ten of the twelve clustered V2 samples came from `policy_rubric_no_evidence`, for example the cluster `effective_policy_misapplied`: the judge could not see which policy was in force.

</details>

**Next:** [Finish Level 2](#finish-level-2). The portal comparison below is optional.

<a id="optional-compare-the-runs-in-the-portal"></a>

<details>
<summary>Optional: compare runs in the portal — only for an additional check</summary>

**Portal:** open the `Portal:` link from section 2. The eval group lists your `baseline-...` and `improved-...` runs with one column per criterion.

**Checkpoint:** both runs show `Completed`, and the `business_contract` column matches the CLI table from section 2.

**If not:** use the CLI table and see [portal differences](troubleshooting.en.md#portal-differs).

For Foundry's statistical view, select both runs, choose **Compare runs**, and pick the `baseline-...` run as **Baseline** ([official guide](https://learn.microsoft.com/azure/foundry/how-to/evaluate-results#compare-the-evaluation-results)).

<details>
<summary>Example screen: both runs selected in the eval group</summary>

![Eval group with the baseline and improved runs selected](assets/levels-20260923/en-l2-runs.webp)

This example is a second run on the same saved responses, so a few LLM-judged counts differ from the recorded table in section 2.

</details>

</details>

<a id="finish-level-2"></a>

## Finish Level 2

Add the following to your [report](../README.md#finish), using **your results as evidence**. This is a note, not a command.

```text
Business contract: .../18 -> .../18; rubric with evidence: .../18 -> .../18
What the generic and safety evaluators told me: ...
Comparison/cluster: evaluator=...; delta/effect=...; verified failure cause, or no failures=...
```

**Checkpoint:** sections 1–3 finished, and your notes distinguish pass counts from mean scores when interpreting your results. Low valid scores are not incomplete execution; missing results due to errors are.

**Next:** [Level 3](level-3.en.md), or return to [step 10 cleanup](../README.md#cleanup). Cleanup also deletes the custom evaluators from this level; the eval groups and results stay as evidence.
