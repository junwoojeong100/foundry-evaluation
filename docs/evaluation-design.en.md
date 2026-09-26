# Design an evaluation that supports a decision

[한국어](evaluation-design.ko.md) · [Start without Azure](offline.en.md) · [Read your real results](validation.en.md#read-your-results) · [Compatibility and sources](compatibility.en.md)

**Define the decision, freeze the experiment, then inspect both improvements and regressions.** A high average, a successful HTTP request, or a completed Foundry evaluation is not production approval.

Use this reference when adapting the workshop to your own application. It does not add required steps to the 120-minute workshop.

## 1. Write the evaluation contract before calling a model

| Decision to make | Workshop example | For your application, record |
|---|---|---|
| What is being evaluated? | One independent policy question and answer | Turn, complete conversation, retrieval step, tool call, or end-to-end task |
| What must remain correct? | Decision, amount, source identity, authority boundary | Business invariants and the impact of violating each one |
| What may improve? | Instructions V1 → V2 | **One intended change** and its hypothesis |
| What stays fixed? | Models, dev questions, corpus, judge, evaluators, concurrency | Versions, hashes, runtime settings, and input distribution |
| What counts as failure? | Wrong answer; missing/invalid evidence; an invocation error | Separate quality failure, service failure, and missing measurement |
| Who decides? | A reviewer explains a case; no production authorization is issued | Accountable owner, review process, and rollback criterion |
| What can be spent? | Bounded questions; extra Level 2/3 calls are separate | Call/token/time budgets and a stop condition |

**Do not select a threshold after seeing the scores.** The workshop's business gate is at least 80% per model and all required citations valid; its native quality threshold is 4 on a 1–5 scale. These are workshop choices, not universal Foundry defaults or an acceptable risk level for every business.

## 2. Choose a metric only if you can supply its evidence

| Question | Suitable signal | Required evidence | Important limitation |
|---|---|---|---|
| Is the answer supported by retrieved text? | Groundedness | Answer and actual retrieved context; query helps | A faithfully repeated outdated policy can still be the wrong policy |
| Does it address the request? | Relevance | Query and answer | A justified refusal may need domain-specific interpretation |
| Is the business contract correct? | Deterministic code checks | Structured decision, fixed reference, amount and citation rules | Token/number presence does not establish full semantic correctness |
| Does it follow the intended policy and authority? | Reviewed domain rubric | Instructions, expected behavior, policy evidence, response | A judge may share biases or miss subtle contradictions |
| Did a tool call do the right thing? | Tool-call/process evaluation | Actual calls, arguments, tool results, and expected behavior | Final answer text alone cannot prove tool execution |
| Is content unsafe or susceptible to attacks? | Safety evaluators and approved red teaming | Authorized target and explicit risk taxonomy | ASR direction differs from quality scores; zero observed attacks is not proof of safety |
| Does a whole dialogue succeed? | Conversation-level evaluation | Full ordered turns, state, actions, final outcome | An average of single-turn scores is not conversation success |

**This repository implements:** Level 1 business checks plus groundedness/relevance; Level 2 custom code/rubric and additional built-ins; Level 3 generated rubrics, synthetic stress tests, model red teaming, agent-target, trace and scheduled evaluation.

**It does not implement a general multi-turn, multimodal, or tool-trajectory benchmark.** The Level 3 red-team target is the model without V2 instructions, not the complete RAG agent. Follow the [official workflow map](https://learn.microsoft.com/azure/foundry/observability/how-to/cloud-evaluation#choose-your-starting-point) for other evaluation units.

### Do not mix API families or output shapes

The live path uses `AIProjectClient.get_openai_client().evals`, not the classic local `azure.ai.evaluation.evaluate()` API. For saved responses, mapping reads `{{item...}}`. Target-generated evaluation can also map `{{sample.output_text}}` or full `{{sample.output_items}}`, depending on the evaluator.

In Level 1, `response` is the saved **answer text**, `context` is the actual retrieval result, and `ground_truth` is **not mapped to either native evaluator**. The separate code grader checks `decision` and `citations`. Selecting “groundedness” does not automatically validate these structured fields. See [the exact input table](validation.en.md#business-checks) and [current SDK guidance](https://learn.microsoft.com/azure/foundry/observability/how-to/cloud-evaluation-datasets).

## 3. Dataset card: what these numbers represent

| Property | Live workshop | Offline lesson |
|---|---|---|
| Origin | Authored synthetic company policies and questions | Authored synthetic meal policy, answers, and answer key |
| Personal/customer data in supplied text | None intended; no production traces are supplied | None; no network data is used |
| Languages | Separate Korean and English cohorts | Separate Korean and English fixtures |
| Policy documents | 7 per language | 1 separate teaching policy per language |
| Development set | 6 questions per language | All 8 cases are teaching examples |
| Holdout | 4 questions per language; reveal only after freezing V2 | **None**; this is not a generalization test |
| Observations | 18 V1 dev + 18 V2 dev + 12 frozen-V2 holdout | 8 authored pairs; **not** 16 model calls |
| Provenance | Dataset/corpus/prompt hashes, model versions, run and trace IDs | Fixture SHA-256 and `synthetic_offline_demonstration` marker |
| Label meaning | Fixed case reference plus a real reviewer record | Supplied `human_reference_*` answer key, not new human review |
| Allowed conclusion | Behavior on these fixed examples | Understanding evaluation mechanics |
| Disallowed conclusion | Production reliability or a general model ranking | Model performance, live cloud success, or production approval |

The live data is in `data/` and `data/en/`; offline fixtures are in `data/offline/`. **Do not read or copy holdout answers into prompt-development data.** `feedback` refuses holdout harvesting. A public teaching holdout is not a secret production test and cannot establish protection from training contamination.

### Build a representative dataset for real use

Start from permitted, de-identified traffic and expert-written edge cases. Keep source/provenance, scenario family, language, severity, applicable policy date, expected behavior, reviewer, and split. Include missing evidence, obsolete/conflicting documents, boundary amounts, legitimate refusals, and unsupported actions—not just easy questions.

Split by **conversation, document, scenario family, or time period** as appropriate, not merely by row. Paraphrases of the same scenario in dev and holdout create leakage. Report critical and minority slices separately; a large easy slice must not hide a small high-impact failure.

Human-review generated questions and labels before treating them as truth. Do not allow the target system to be its own sole ground-truth authority. Version dataset changes rather than deleting difficult cases, and reserve a fresh final set if the old holdout has already guided improvements.

## 4. Calibrate the judge; do not blindly trust it

The live `calibrate` step checks one supported and one unsupported answer. **Two examples are a smoke check, not statistical validation of a judge.**

For your own application, build a separately reviewed calibration set covering clear passes, clear failures, borderline decisions, justified refusals, and high-impact cases. Have reviewers resolve disagreements independently of the model. Measure both:

- **False acceptance:** judge passes an unacceptable answer.
- **False rejection:** judge fails an acceptable answer.

Stratify by language, scenario, and risk. Compare with more than one qualified reviewer or judge when the impact warrants it. Keep judge deployment/version, rubric, thresholds, and input mappings fixed across the experiment. Low agreement calls for rubric/input inspection, not automatic relabeling of the human references.

Level 2 compares code and rubric judgments and deliberately removes evidence in one ablation. Neither the deterministic checker nor the LLM judge is a universal gold standard. The offline `O05` case makes a code-grader blind spot executable.

## 5. Pair the same cases; an average can conceal damage

`compare` now records **both directions of change** for dev runs, keyed by `(model_key, case_id)`. File ordering is irrelevant. It refuses duplicate/missing pairs. The first dev label in the requested order is the reference for subsequent dev labels; holdout is never paired against different dev questions.

Older saved comparisons remain readable. To add the new diagnostics, rerun only `compare` with your same actual labels; do not repeat collection or judge calls.

After the normal [step 7 comparison](../README.md#compare-results), inspect `comparison.json → paired_comparisons` and the extra `summary` lines:

| Field | Meaning |
|---|---|
| `fail_to_pass`, `improved_case_ids` | Previously failing cases that now pass |
| `pass_to_fail`, `regressed_case_ids` | Previously passing cases that now fail |
| `both_pass`, `both_fail` | Cases whose pass/fail outcome did not change |
| `context_changed_case_ids` | Retrieval text differs between the paired responses |
| `pass_rate_delta` | `(fail_to_pass - pass_to_fail) / total`, a descriptive difference |

**Always review regressions, even if the net delta is positive.** Different retrieval context means the observation is end-to-end, not proof that only the prompt or model caused the change. Equal context alone still does not establish causality.

These fields are additional diagnostics. They **do not silently change** the existing Level 1/3 gate thresholds. If production policy disallows any critical regression, make that a separate explicit, reviewed gate. The offline `--fail-on-regression` flag demonstrates that distinction.

## 6. Four passes do not mean 100% reliable

Each model's summary contains `business_pass_rate_wilson_95.lower` and `.upper`. `summary` renders these as **illustrative two-sided 95% Wilson intervals**.

For **4/4** passes, the interval is approximately **51.0%–100.0%**, not proof of a 100% underlying success rate. Implementation: [`wilson_interval()`](../scripts/grading.py); method reference: [Wilson score interval](https://www.statsmodels.org/stable/generated/statsmodels.stats.proportion.proportion_confint.html).

**The assumption matters more than the formula:** the binomial calculation assumes independent trials from a stable success probability. This small, deliberately curated workshop set is not a representative production sample, so the interval is an illustration of sample-size uncertainty, not a calibrated production guarantee.

Do not pool the three models' answers to the same four questions into 12 independent observations of one model. Do not pool translations or repeatedly evaluate the same answers to inflate the denominator. Interval overlap/non-overlap is not a paired significance test.

For operational studies, predeclare sample size, scenario coverage, repeated-run count, budget, and analysis method. Repeated runs expose stochastic variation; use independent scenario units or a justified clustered analysis. The repository does not implement bootstrap confidence intervals for deltas or automatic significance claims.

## 7. Triage failures before changing instructions

| Business checks | Native scores | Investigate first |
|---|---|---|
| Pass | Pass | Remaining semantic, policy-date, safety, and authority gaps; small-sample limits |
| Fail | Pass | Structured decision/citation contract versus fluent answer text |
| Pass | Fail | Grader blind spots, legitimate refusal, judge input/context, rubric fit |
| Fail | Fail | Retrieval evidence, policy selection, answer generation, and evaluator mappings |

An HTTP error, missing evaluator row, invalid score, timeout, or missing trace is **incomplete evidence**, not a zero score or a success. Preserve the failed attempt. Reuse/resume the same remote run where supported; do not rerun valid low scores until one happens to pass.

Use the actual trace to distinguish retrieval, model, format, tool, and evaluator failures. Fix one cause, keep the same dev set and evaluator definitions, compare again, then freeze the candidate before holdout.

## 8. Cost, privacy, and a responsible release boundary

Budget separately for **target inference + retrieval planning/Search + judge calls + hosted compute + logs/storage**. Two labels with 18 responses each and two native criteria already represent 72 row/criterion judgments; this is a planning count, **not a promise of exactly 72 billable API calls**. Retries, service execution, calibration, and extra levels can change usage.

Use observed tokens with the deployment's current input/cached-input/output prices. Keep missing price/usage data as unknown, never `$0`. Native model-target estimated cost can be partial and is not total Azure billing. See [official cost limitations](https://learn.microsoft.com/azure/foundry/observability/how-to/cloud-evaluation-results#review-model-target-latency-and-estimated-cost) and the workshop's [measurement boundaries](validation.en.md#tradeoffs).

Before using real data, obtain permission for the **data and destination**, redact it, choose appropriate region/network/storage/retention, and restrict access. `.gitignore` prevents accidental Git additions; it is not encryption or a data-loss-prevention system. Do not publish `.env`, raw traces, evaluation artifacts, or identity-bearing screenshots. Continuous evaluation is ongoing processing with ongoing cost, not a free final check.

For release, record quality and safety signals, coverage gaps, operating cost/latency budgets, human sign-off, monitoring/alert owners, a rollback mechanism, and the next review date. This workshop always keeps `production_release_approved=false`.
