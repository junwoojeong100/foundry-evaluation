# Level 2: Let Foundry evaluate your business contract

[한국어](level-2.ko.md) · [Back to the main guide](../README.md#levels)

**In about 40 minutes you will:**

1. Register the five business checks as a **Foundry custom code evaluator** and the policy criteria as a **rubric evaluator**.
2. Evaluate your saved V1 and V2 responses with **nine evaluators in one eval group**.
3. Read Foundry's **run comparison** (statistical test) and **failure clusters**.

**You need:** steps 1–9 of the [main guide](../README.md) finished in the same folder, and **step 10 not yet run**; cleanup deletes the evaluators you create here. No new agent responses are collected; only the judge model is called.

**Why this level exists:** in step 7, the business pass count changed from 0/18 to 17/18 in the recorded run, while Foundry's groundedness stayed at 18/18. The business result came from local Python. Here you make Foundry itself measure that contract and compare it with other evaluator types.

<a id="register-evaluators"></a>

## 1. Register two custom evaluators

**Terminal A:**

```bash
python scripts/workshop.py register-evaluators
```

**Checkpoint:** two lines, `Registered <LAB_PREFIX>-business-contract version 1 (code)` and `Registered <LAB_PREFIX>-policy-rubric version 1 (rubric)`. Running the command again prints `Reusing ...` and creates nothing.
**If not:** `already exists and is not owned by this folder` means another team uses your `LAB_PREFIX`; ask the instructor for an unused one. For other errors, see [Level 2 and 3 recovery](troubleshooting.en.md#levels).

<details>
<summary>What the two evaluators contain</summary>

| Evaluator | Type | What it scores | Pass rule |
|---|---|---|---|
| `<LAB_PREFIX>-business-contract` | Code (Python runs in Foundry) | The same five checks as `scripts/grading.py`: decision, required amounts, citations retrieved, citations allowed, and a citation when required | Score is the share of passed checks; a row passes only at 1.0 |
| `<LAB_PREFIX>-policy-rubric` | Rubric (LLM judge) | Five weighted dimensions: effective policy, decision matches policy, cites document IDs, defers when uncovered, resists policy bypass | Weighted 1–5 scores, normalized; passes at 0.7 |

Both are objects in your project's evaluator catalog, prefixed with your `LAB_PREFIX` and recorded in this folder's ownership file for cleanup. The definitions are in `scripts/foundry_eval.py`.

</details>

<a id="evaluate-suite"></a>

## 2. Evaluate V1 and V2 with nine evaluators

**Terminal A:** this reads the saved `baseline` and `improved` responses and runs them one after the other in one eval group; it takes several minutes:

```bash
python scripts/workshop.py evaluate-suite --labels baseline improved
```

**Checkpoint:** `Suite evaluation completed: ... (baseline, improved)`, a table with nine rows and a `Portal:` link. The `business_contract` row matches the business passes from your 7-4 summary.
**If not:** `evaluator results failed, for example because the judge hit its rate limit` means the shared judge was busy; run the same command with `--retry-failed` added. A timeout message means the runs are still going; run the same command again to resume.

**Read the table in three parts:**

- **Your contract (`business_contract`)** reproduces the local business checks inside Foundry.
- **The same rubric with and without evidence** differ: `policy_rubric` receives the question plus the retrieved policy text, while `policy_rubric_no_evidence` receives only the question. A judge sees only what you map to it.
- **Generic evaluators** (`groundedness`, `relevance`, `response_completeness`, `task_adherence`, `intent_resolution`, and the safety evaluator `indirect_attack`) barely move, because they do not know your contract.

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

<a id="insights"></a>

## 3. Compare the runs and cluster the failures

**Terminal A:**

```bash
python scripts/workshop.py insights --baseline baseline --candidate improved
```

**Checkpoint:** a `Comparison (candidate vs baseline):` table with `delta`, `p`, and `effect` for all nine criteria, then `Failure clusters in the candidate run [evaluator that failed each sample]:` with a list, or `none`.
**If not:** `Run evaluate-suite ... first` means section 2 has not completed. A timeout means the insights are still generating, and `... insight failed` means one could not be generated; in both cases, run the same command again.

**Read it:**

- **`effect`** is Foundry's statistical test on the two runs: `Changed` means a significant difference (p at most 0.05), and `Inconclusive` means too few rows or p of 0.05 or more. With 18 rows per run, only large changes become significant.
- **Each cluster lists the evaluators whose failures it contains.** If most samples come from `policy_rubric_no_evidence`, the cluster describes a judge that lacked evidence, not a real agent problem. Check the source before acting on a suggestion.

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

## 4. Optional: compare the runs in the portal

**Portal:** open the `Portal:` link from section 2, select the `baseline-...` and `improved-...` runs, and select **Compare**. The comparison view uses the same statistical test and colors each cell by effect ([official guide](https://learn.microsoft.com/azure/foundry/how-to/evaluate-results#compare-the-evaluation-results)).

**Checkpoint:** each evaluator appears with both runs side by side. Your custom evaluators appear under their `LAB_PREFIX` names.
**If not:** use the CLI table from section 3; see [portal differences](troubleshooting.en.md#portal-differs).

## Finish Level 2

Add one sentence to your report: **which evaluator answers which question.** For example: the contract check decides pass or fail; the rubric with evidence explains quality; generic evaluators and the safety evaluator watch for regressions they are designed for.

**Next:** [Level 3](level-3.en.md), or return to [step 10 cleanup](../README.md#cleanup). Cleanup also deletes the custom evaluators from this level; the eval groups and results stay as evidence.
