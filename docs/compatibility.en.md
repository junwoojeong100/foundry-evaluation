# Compatibility, scope, and source review

[한국어](compatibility.ko.md) · [Main guide](../README.md) · [Evaluation design](evaluation-design.en.md) · [Maintaining this guide](maintaining.en.md)

**Source review date: 2026-09-26.** “Current documentation was reviewed,” “offline checks passed,” and “a live Azure run completed” are different claims. This page separates them. It does not claim that this repository has been objectively ranked first among all GitHub repositories.

## Choose the right learning path

| Path | What you do | Evidence you leave | Azure use |
|---|---|---|---|
| [Level 0](offline.en.md) · 15 min | Grade authored answers; discover a regression and a checker blind spot | Clearly marked synthetic local report | None |
| [Level 1](../README.md#start-here) · 120 min after setup | Deploy, collect, evaluate, review, improve, check holdout, clean up | 48 real responses, traces, evaluations, review lineage | Paid |
| [Level 2](level-2.en.md) · 40 min | Compare built-in, code, and domain-rubric judgments | Nine-criterion suite, disagreement and failure analysis | Extra judge/service calls |
| [Level 3](level-3.en.md) · about 70 min | Generate rubrics, stress-test, evaluate model/agent/traces, schedule, gate | Separate target-specific evidence and explicit gate decisions | Extra calls and a temporary schedule |

Level 2 follows Level 1 step 9; Level 3 follows Level 2. Both run **before cleanup**. Setup, service latency, regional availability, and time needed to obtain permissions are not guaranteed by these estimates.

## Reproducible runtime versus latest available SDK

The workshop intentionally preserves the runtime behind its recorded executions. **Do not replace its dependency set with `pip install --upgrade` during a cohort.** The default local setup and offline CI use `requirements.lock.txt`, a full pinned package snapshot, not a cryptographic package lock.

| Component | Repository contract | Where to verify |
|---|---|---|
| Cloud workshop Python | 3.13; Bash, macOS/Linux or WSL | [Tool setup](instructor.en.md#tools), `azure.yaml` |
| Offline lesson Python | 3.10+; standard library only; native Windows supported | `scripts/offline_lab.py`, credential-free CI job |
| Foundry project SDK | `azure-ai-projects==2.3.0` | `src/agent/requirements.txt`, `requirements.lock.txt` |
| Agent Framework | Foundry 1.11.0; core 1.16.0; OpenAI adapter 1.14.1 | `src/agent/requirements.txt` |
| Agent Server | Invocations 1.1.0; core 2.1.0 | `src/agent/requirements.txt` |
| OpenAI client | 2.54.0 in the full snapshot | `requirements.lock.txt` |
| Search knowledge retrieval | `2026-05-01-preview` | `src/agent/knowledge.py` |
| Model identity | Three fixed model/version pairs; actual deployment names are environment-specific | [Model contract](reference.en.md#model-names), `preflight` |
| Judge and evaluator versions | Judge deployment and first-resolved evaluator definitions remain fixed within an experiment | [Evaluation method](validation.en.md#business-checks) |
| CLI/portal evidence | Versioned recorded runs, not proof of every current CLI/portal combination | [Recorded toolchain](instructor.en.md#tools), [recorded results](validation.en.md) |

### Important current SDK difference

On the review date, [PyPI lists `azure-ai-projects` 2.7.0](https://pypi.org/project/azure-ai-projects/2.7.0/) (published 2026-09-18). **2.3.0 is this workshop's frozen version, not the latest version.** Current Learn examples cannot all be pasted into this frozen environment.

The [official SDK changelog](https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/ai/azure-ai-projects/CHANGELOG.md) documents relevant boundaries:

| Change | Why an unreviewed upgrade is unsafe |
|---|---|
| 2.4: generation jobs use `begin_create_generation_job` and return long-running pollers | The 2.3 workshop explicitly saves job IDs and polls generation jobs. Call/return contracts differ |
| 2.5: OpenAI dependency becomes `openai>=3.0.0`, using `httpx2` | Upgrading only the Foundry SDK can conflict with the frozen framework/client stack |
| 2.7: beta data-generation option constructors change | A sample can import successfully yet have different runtime behavior |

**A 2.7 migration is not claimed or silently performed here.** To migrate, create a separate environment, update the dependency set and affected calls together, preserve polling/resume/error/cleanup behavior, run offline checks, then rehearse both languages and any affected live levels with approval. Record new evidence separately. See [the maintenance procedure](maintaining.en.md#upgrades).

## New Foundry versus classic

Use **new Microsoft Foundry** documentation under `/azure/foundry/` for this workshop. Classic evaluation examples under `/azure/foundry-classic/` often use different SDKs, project types, field mappings, and output shapes.

| Topic | Current first-party source | Repository interpretation |
|---|---|---|
| Evaluation unit and client setup | [Cloud evaluation overview](https://learn.microsoft.com/azure/foundry/observability/how-to/cloud-evaluation) | Explicitly distinguish stored responses, generated targets, and conversations |
| Existing response data | [Dataset evaluation](https://learn.microsoft.com/azure/foundry/observability/how-to/cloud-evaluation-datasets) | Level 1 scores captured answers without recalling the agent |
| Model/agent invocation | [Target evaluation](https://learn.microsoft.com/azure/foundry/observability/how-to/cloud-evaluation-targets) | Level 3 creates separate observations; do not add them to the original 48 |
| Domain-specific agent criteria | [Evaluate agents](https://learn.microsoft.com/azure/foundry/observability/how-to/evaluate-agent) | Review rubrics and add safety signals; newer generation snippets need newer SDKs |
| Scores, polling, latency and cost | [Evaluation results](https://learn.microsoft.com/azure/foundry/observability/how-to/cloud-evaluation-results) | Preserve missing/error states; estimated target cost is not the Azure bill |
| Regions, limits, network and storage | [Evaluation availability](https://learn.microsoft.com/azure/foundry/concepts/evaluation-regions-limits-virtual-network) | Model availability does not imply every evaluator or red-team feature is available |
| Classic migration boundary | [Classic continuous evaluation](https://learn.microsoft.com/azure/foundry-classic/how-to/continuous-evaluation-agents) | Not interchangeable with the new-portal workflow |

Foundry role names can appear as **Foundry User/Owner** or the earlier **Azure AI User/Owner** during rollout; the rename does not change the role IDs. Check [the exact scoped role table](instructor.en.md#access), not just a familiar display name. Do not widen roles to Owner to bypass a problem.

The repository's native quality threshold **4** is intentional; a Learn example's default threshold may differ. Use the pinned evaluator definition and saved result, not an assumed platform-wide default.

## What was compared on GitHub

The following are **representative public entrypoints reviewed on 2026-09-26**, not an exhaustive survey, feature absence audit, or live execution comparison. Links pin the README revisions reviewed. Stars and update dates are not quality scores.

| Public material | Strength stated in the reviewed entrypoint | How this guide complements it |
|---|---|---|
| [Microsoft AI Tour LTG151](https://github.com/microsoft/aitour26-LTG151-build-trustworthy-ai-with-systematic-evaluations-in-microsoft-foundry/blob/8610367547fbdcf703d13a234e61e267bf5379da/README.md) | Foundry observability, evaluation, monitoring and optimization session; links to official SDK examples | One bilingual runbook with checkpoints, recovery, controlled comparison, and evidence boundaries |
| [Azure-Samples/Agentic-Evaluations](https://github.com/Azure-Samples/Agentic-Evaluations/blob/2d205f321b2e6b54ba62b5ee26c6cd79d492ab70/README.md) | Config-driven evaluation pipelines, custom judges, agentic metrics, visualization | A fixed teaching experiment and explicit per-case business contracts; not a replacement for a general framework |
| [microsoft/FrontierWeekHack](https://github.com/microsoft/FrontierWeekHack/blob/7cdcc35df535d655cdf0900ccbc71d8108a05c67/README.md) | Scenario-based agent build → monitor → evaluate → workflow labs | Evaluation-focused progression through holdout, rubric analysis, traces and release gates |
| [Korean evaluation engineering demo](https://github.com/devkimchi/foundry-evaluation-engineering-demo/blob/ea0c07122a85f6256fbf17bc382190676b885b95/README.md) | Portal-first V1/V2 comparison and interpretation of conflicting evaluator judgments | A complementary executable local lesson and hosted workflow, with code/reference disagreements exposed |

The additions here use original teaching text and fixtures. Linked repositories remain the appropriate source for their own examples and licenses.

## Evidence and known boundaries

| Claim | What supports it | What it does not establish |
|---|---|---|
| The lesson can run without credentials | Standard-library execution tests with network and subprocess calls blocked | Real model quality |
| Commands and guides stay aligned | Offline tests check parser arguments, Bash syntax, local links, language parity and fixtures | Current external portal layout or Azure availability |
| Paired diagnostics expose regressions | Tests cover shuffled rows, missing/duplicate pairs, model separation and cross-run context changes | Causal attribution or a production release policy |
| Live runs have been recorded | Dated [English](validation.en.md) and [Korean](validation.ko.md) results and recordings | A new live run on every documentation edit |
| Public CI is credential-free | `.github/workflows/validate.yml`; read-only repository permissions, no Azure sign-in | Live evaluation, provisioning, or Azure cleanup |

**Known limits:** the live path requires its fixed three model deployments and a compatible region; it is not a universal one-model quickstart. The teaching dataset is deliberately small. Production network hardening, general multi-turn/multimodal evaluation, cross-provider benchmarking, fine-tuning, and automatic production promotion are outside scope. Recorded raw cloud artifacts are not distributed; do not fabricate replacements to make a fresh clone look completed.

When a source or portal changes, report the exact guide section and a sanitized symptom using [the contribution process](maintaining.en.md). Keep the source-review date separate from the date of any new live rehearsal.
