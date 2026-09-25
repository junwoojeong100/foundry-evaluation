# If a step fails: stop, identify the cause, and resume safely

[Return to the English guide](../README.md) · [한국어](troubleshooting.ko.md)

**Keep the current folder and error output. Do not restart the whole workshop.**
- **Failed stage:** [sign-in](#login) · [retrieval](#retrieval) · [local run](#symptom-local) · [hosted run](#symptom-hosted) · [calibration](#calibration) · [collection](#collection-retry) · [evaluation](#evaluation-retry) · [V2 changed](#v2-changed) · [cleanup](#cleanup-recovery).
- **Evidence or optional work:** [no baseline failures](#no-failures) · [traces](#telemetry) · [portal](#portal-differs) · [completion](#symptom-completion) · [Levels 2-3](#levels).
- **Not sure?** [common symptoms](#symptoms) · [saved-state resume](#resume) if a label or state file exists · [environment-owner resume](#setup-resume) if setup failed (environment owners only).
- Run participant recovery commands from the existing workshop folder's repository root; environment-owner recovery names its own folders.
- Keep the workshop virtual environment active and restore `AZURE_CONFIG_DIR` from [README resume-shell](../README.md#resume-shell).

**First distinguish execution failure from low quality.**

| What you see | Next action |
|---|---|
| Exception, missing/duplicate response, or evaluator error | Stop the next step and [recover the failed command](#resume) |
| `collect` prints `business=False` | A business check failed, not the command. If collection finishes without errors, continue to that stage's evaluation. |
| Completed evaluation with low scores and no row errors | Valid low scores are results. Record them and return: `baseline` [step 6](../README.md#lab-d), `improved` [7-4](../README.md#compare-results), or `holdout` [8-3](../README.md#holdout-results). |
| Missing or incomplete traces | Check ingestion, access, and the [query window](#telemetry); do not claim complete evidence |
| Only a recording of a successful run | Treat it as observation, not your own completed execution |

In this guide, “instructor” and “environment owner” mean the instructor in a class and **you in self-study**. If that is you, perform the row's check yourself; if it does not resolve, stop and record the state and error. When you ask for help, share only the failed command, error, step, and result label. Never share passwords, tokens, the full `.env`, or personal-information screenshots.

<a id="resume"></a>

## Resume the failed command, not the whole block

If `collect` finished but `evaluate` stopped, do not paste the block again from `collect`.

| Stopping point | Correct next action |
|---|---|
| Deployment succeeded; `grant-agent-access` or `smoke` failed afterward | Resolve the cause and repeat **only that failed command**. Do not redeploy and create another agent version. |
| Collection failed; manifest status is `failed` | Follow [collection recovery](#collection-retry), preserving the failed attempt |
| `Evaluation is still running` | Repeat only `evaluate` with the same label |
| Evaluation failed, or result validation/download stopped | Use the [saved-status decision table](#evaluation-retry). Not every local error permits `--retry-failed`. |
| `Telemetry is incomplete` | Check ingestion/access and the [two-hour query window](#telemetry); repeat only `monitor` for that label |
| `Hosted prompt does not match` (holdout collection), or 8-2 shows different improved and holdout versions | [If V2 changed after 7-2](#v2-changed); do not delete or edit results |
| `Label ... already exists` | Read the status files below. If collection is `completed`, find the next unfinished evaluation/trace step. If `failed`, recover collection. If `running`, check the original process: wait while active; [recover collection](#collection-retry) only after confirming it stopped. |
| Reviewed regression already exists | Verify its row, reason, language, and source trace. Continue only if they match the intended review; do not overwrite it. |
| Cleanup or its verification stopped | Use [cleanup recovery](#cleanup-recovery); do not repeat successful deletion to fix a failed check. |
| A Level 2 or 3 command stopped | Use [Level 2–3 recovery](#levels); your step 5–9 results stay unchanged |

**Reopened a terminal?** Open your **existing workshop folder**, not a new clone, and follow [the terminal restore block](../README.md#resume-shell). Do not repeat `init`, `bind`, deployment, or collection just because the terminal is empty.

Read these files under **`src/agent/.foundry/results/<label>/`** without editing them:

| File | Completion evidence | What it covers |
|---|---|---|
| `manifest.json` | `status: completed` | Response collection only |
| `evaluation.json` | `status: completed`, expected `run → result_counts → total`, no errored rows | Foundry job status |
| `evaluation-results.json` | One row per response, with both evaluator results | Row-level evaluation, not trace coverage |
| `telemetry.json` | `complete: true` and matching `expected_trace_count` / `observed_trace_count` | Trace coverage for this label |

Choose the recovery section for the first incomplete file; a completed manifest is not whole-workshop completion. For a new experiment or language, use unused names in a separate folder, and never delete ownership or results to recover. If Azure environment setup failed, use [setup recovery](#setup-resume).

**Checkpoint:** the first incomplete saved state identifies one failed stage and one matching recovery section.

**If not:** preserve the current folder and error output. Look up the error message in [common symptoms](#symptoms); in a class, show the stage, label, and status files to the instructor.

**Next:** open the matching section above, or use [common symptoms](#symptoms) when the stage is still unclear.

<a id="symptoms"></a>

## Common symptoms

Use the matching row, then return to the failed checkpoint. If it persists, preserve the error and use the linked recovery section or the instructor.

**Setup and sign-in**

| Route | Symptom | Cause or check | Action / exact return |
|---|---|---|---|
| Setup | Missing `.env` or required setting | The workshop cannot infer private deployment names. | Add the complete file; return to [step 1-1 `.env` check](../README.md#workspace-settings). |
| Setup | `read: -p: no coprocess` or activation path missing | The shell or folder is not the recorded workshop shell/path. | Run `bash`, then [restore the terminal](../README.md#resume-shell) in the existing folder. Do not clone again. |
| Setup | Language mismatch | `LAB_LANGUAGE=en` selects English; `LAB_LANGUAGE=ko` or a missing setting selects Korean. | Use the original language/workspace; return to [step 1-1 `.env` check](../README.md#workspace-settings). |
| Setup | Nonempty `missing_models` | One of the three exact deployments, versions, access paths, or quotas is unavailable. | Check that the `MODEL_*_DEPLOYMENT` values in `.env` are exactly as received, then ask the environment owner to deploy them (for your own environment, [environment step 6-1](environment.en.md#setup-candidates)); return to [preflight](../README.md#project-binding). |
| Setup | `The fixed auxiliary planner/judge deployment is missing` | The actual `LAB_AUX_DEPLOYMENT` in `.env` is not ready. | Owner completes [auxiliary model preparation](instructor.en.md#auxiliary-model); return to [preflight](../README.md#project-binding). |
| Setup | `bind` or `set-prompt` environment error | This folder may not be bound to the expected project/language. | Confirm `bind` ran in this folder; return to [bind project](../README.md#bind-project). |
| Sign-in | Wrong account or tenant | A CLI is signed into the wrong identity or subscription. | Repeat the two sign-ins/checks; return to [login check](../README.md#login-check). |
| Sign-in | Login appears missing only in a new terminal | The new shell did not inherit the local CLI profile path. | Restore `AZURE_CONFIG_DIR`; return to [terminal restore](../README.md#resume-shell). |

**Run and evidence**

| Route | Symptom | Cause or check | Action / exact return |
|---|---|---|---|
| <a id="symptom-local"></a>Local run | Port 8088 unavailable | Terminal A may not be serving, or another process owns the port. | For `Connection refused`, wait for A's `Running on ...:8088`, then repeat only B's request block. For `Address already in use`, stop only another workshop server you started with `Ctrl+C` in its window, then resume [3-1](../README.md#local). Do not stop an unfamiliar process. |
| Retrieval | `prepare-iq` cannot create a role assignment | The Search identity needs planner access. | Check [access](instructor.en.md#access), then rerun the failed [2-1 registration](../README.md#knowledge-registration). Do not skip to 2-2 retrieval yet. |
| Retrieval | `retrieve` finishes without documents or without `TRAVEL-2026` | Registration and retrieval are separate checks. | [Recover retrieval](#retrieval); return to [policy retrieval](../README.md#policy-retrieval). |
| <a id="symptom-hosted"></a>Hosted run | Search 403 / role assignment failure | Local user permissions and hosted agent instance permissions differ. | Check both identities; return to [hosted access](../README.md#agent-access). |
| Hosted run | Hosted 424 / cold start | The hosted version may not be ready. | After 1–2 minutes, repeat only `smoke` from [hosted smoke](../README.md#hosted-smoke). If it still fails, inspect the error in **your agent → Playground → Log stream**. Do not redeploy. |
| Collection | 429 or request timeout | Capacity or service throttling interrupted the run. | Preserve the attempt and inspect Retry-After; return to [collection recovery](#collection-retry). |
| Trace | `connections/read` on startup | Startup may be reading connection metadata directly. | Use injected telemetry configuration; return to [hosted smoke](../README.md#hosted-smoke). |
| Evaluation | Completed job with errors or null scores | Completed job status is not row-level success. | [Recover evaluation](#evaluation-retry); return to [baseline](../README.md#baseline-evaluation), [candidate](../README.md#candidate-evaluation), or [holdout](../README.md#holdout-evaluation). |

**Completion and cleanup**

| Route | Symptom | Cause or check | Action / exact return |
|---|---|---|---|
| <a id="symptom-completion"></a>Completion | `verify` succeeds but a `candidate_quality_gates` value is `false` | A valid execution can expose a quality failure. | Report it; return to [completion decision](../README.md#completion-decision). |
| Completion | `production_release_approved: false` | This is expected even when business gates pass. | Leave the field unchanged; return to [completion decision](../README.md#completion-decision). |
| Cleanup | Unfamiliar cleanup target | Ownership records and Azure state may not match. | Stop and use [cleanup recovery](#cleanup-recovery); return to [cleanup check](../README.md#cleanup-check). |
<details>
<summary>Less common symptoms</summary>

| Route | Symptom | Cause or check | Action / exact return |
|---|---|---|---|
| Setup | Model 404 | The catalog ID may not match the Azure deployment name. | Compare `.env` and azd values; return to [preflight](../README.md#project-binding). |
| Retrieval | IQ 400 | The pinned API/schema or planner deployment may not match. | Inspect those three items; return to [policy retrieval](../README.md#policy-retrieval). |
| Setup | CLI extension notice after JSON | The supplied parser separates recognized notices only. | Do not upgrade mid-experiment; return to [preflight](../README.md#project-binding). |
| Sign-in | CLI credential timeout | Token refresh delay can look like login failure. | Distinguish timeout from failed login; return to [login check](../README.md#login-check). |
| Trace | Missing App Insights `ResourceId` metadata | The dedicated connection metadata may be incomplete. | The environment owner follows the [owner-only observability repair](instructor.en.md#observability-repair); return to [trace recovery](#telemetry). |

</details>

<a id="login"></a>

## If the authentication browser does not open

First run the **CLI-profile and tenant/subscription input block** from [README step 1-3](../README.md#login) in the same terminal.

**Run only the command for the CLI whose sign-in failed.** If both need sign-in, run Azure CLI first, then azd.

Open the address each command prints and enter the code from **your own terminal**. Sign in with the `.env` account. Never share or record one-time codes.

**Terminal — Azure CLI:**

```bash
az login --tenant "$LOGIN_TENANT_ID" --subscription "$LOGIN_SUBSCRIPTION_ID" \
  --use-device-code --output none
```

**Checkpoint:** browser sign-in finishes and the terminal prompt returns without an error. No account JSON is printed.

**If not:** preserve the error. If organizational policy blocks sign-in, use an approved environment rather than bypassing it.

**Terminal — azd:**

```bash
azd auth login --tenant-id "$LOGIN_TENANT_ID" --use-device-code
```

**Checkpoint:** browser sign-in finishes and the terminal prompt returns without an error.

**If not:** preserve the error. If organizational policy blocks sign-in, use an approved environment rather than bypassing it.

After all required sign-ins finish, return to the README's [two-account verification block](../README.md#login-check). Do not repeat successful sign-ins.

**Checkpoint:** [the two-account verification block](../README.md#login-check) shows the configured Azure CLI and azd account, tenant, and subscription.

**If not:** preserve the exact sign-in error and ask for an approved login path; do not switch accounts or tenants.

<details>
<summary>Background references</summary>

[interactive Azure CLI sign-in](https://learn.microsoft.com/cli/azure/authenticate-azure-cli-interactively) · [CLI configuration directories](https://learn.microsoft.com/cli/azure/azure-cli-configuration#cli-configuration-file)

</details>

**Next:** resume [README step 1-3](../README.md#login-check) at the verification block.

<a id="retrieval"></a>

## If registered policies do not appear in retrieval

Use this section when step 2's question returns no **`TRAVEL-2026` in `document_ids`**, or an empty `activity`. An error-free `retrieve` command does not by itself establish that the required policy was found.

**Cause:** registration can succeed while the index is not yet queryable or is connected to the wrong KB/source/index.

1. Confirm that `prepare-iq` ended with **`Foundry IQ ready: ...; 7 synthetic documents.`**. Retrieval's `knowledge_base` must also match your `LAB_PREFIX` plus `-kb`. If registration itself failed, resolve that error first.
2. Open the **`saved` path** printed by `retrieve` in your editor and inspect `documents`, `references`, and `activity`. If registration just finished, wait 1–2 minutes, then repeat **[only step 2's same `retrieve` command](../README.md#policy-retrieval)**. Do not repeat `prepare-iq`, deployment, or response collection just to check retrieval.
3. If evidence is still missing, ask the environment owner to check your workshop's KB/source/index chain: **`LAB_PREFIX-kb` → `LAB_PREFIX-source` → `LAB_PREFIX-policies`**. Read `LAB_PREFIX` as the actual value from `.env`.

Preserve the result file and KB name. Do not change policies/questions to pass the check or use another team's KB.

**Checkpoint:** the saved file's `knowledge_base` is your KB, its `documents` list includes `"id": "TRAVEL-2026"`, and `activity` is nonempty. **`document_ids` appears only in the terminal summary**, not in that file.

**If not:** give the environment owner the saved path and KB/source/index names; do not change policies, questions, or another team's KB.

**Next:** finish [step 2's checkpoint and portal check](../README.md#policy-retrieval), then continue to step 3.

<a id="calibration"></a>

## If judge calibration does not pass

Check **`src/agent/.foundry/results/judge-calibration/evaluation.json`** if it exists. If the job is **still running**, or a creation/download error has been resolved, resume with:

**Terminal — resume the existing calibration:** run this after the original command stops. There may be no output for 1–3 minutes while scoring.

```bash
python scripts/workshop.py calibrate
```

**Checkpoint:** the last line says `Judge calibration passed; ...`. Skip the retry block below.

**If not:** for `Evaluation is still running`, resume with the same command. Choose the block below only for a recorded failed/errored run. Do not retry a completed run just for low scores.

**Terminal — retry a failed calibration only:** use this when the saved `status` is **`failed` / `canceled` / `cancelled`**, or **`run → result_counts → errored` is greater than 0**. Resolve the cause first; the failed job is preserved.

```bash
python scripts/workshop.py calibrate --retry-failed
```

Malformed/missing results without a recorded failed/errored run require owner review of this calibration folder's saved status and raw output, not a forced retry. Calibration is separate from the 48 agent responses.

**Checkpoint:** the last line says `Judge calibration passed; ...`, and `calibration.json` in the same folder has `passed: true`.

**If not:** preserve the calibration folder and raw output for owner review; do not edit examples, thresholds, or rerun a valid low score.

**Next:** resume [environment judge calibration](environment.en.md#setup-calibration) if preparing the environment, or [README judge check](../README.md#5-1-check-the-judge) if running the workshop.

<a id="telemetry"></a>

## If traces are missing after a pause

`monitor` defaults to the **last two hours**, even if the portal displays Last Day. For a run from the last 24 hours, extend the window while keeping the **same label**:

**Terminal — extend the existing trace query window:**

```bash
python scripts/workshop.py monitor --label baseline --hours 24
```

Replace `baseline` with the label whose monitoring failed (`improved` or `holdout` when applicable). `--hours` accepts whole hours from **1 to 168**. Use a window containing your original collection time; it does not recreate expired/deleted telemetry.

**Checkpoint:** `telemetry.json` has `complete: true` and matching `expected_trace_count` / `observed_trace_count` for the same label.

**If not:** give the owner the label, collection time, query window, and telemetry error; do not recollect answers or edit `telemetry.json`.

<details>
<summary>Why this can still fail</summary>

The query still filters the exact agent and run, and missing, duplicate, foreign, or sampled traces still fail coverage checks. If the data is recent, allow ingestion to finish and repeat only this command. If it remains incomplete, inspect access, retention, and the connected App Insights resource with the environment owner. Never recollect answers or edit `telemetry.json` to manufacture completeness.

</details>

**Next:** do not repeat the recovered command; continue below its trace checkpoint: [baseline traces](../README.md#baseline-traces), [candidate traces](../README.md#candidate-traces), or [holdout traces](../README.md#holdout-traces). If cleanup already ran, read saved evidence only. For a new experiment, use a fresh workspace and names.

<a id="collection-retry"></a>

## If response collection failed

Use this only when:

- The original collector has stopped. Stopped means the original terminal is back at a prompt or, if you closed it, you confirmed that the process ended; if unsure, wait — never start a second command.
- You keep the failed label and original files.
- You retry the same stage once with one unused retry label.
- You do not change models, split, questions, prompt version, agent version, completed labels, reviewed source, or holdout meaning. Only [when V2 changed after 7-2](#v2-changed) do you collect with the current V2 version.
- If the retry fails, stop and keep the error.

| If this failed | Go to |
|---|---|
| Baseline before comparison | [Failed initial baseline](#collection-retry-baseline) |
| V2 dev after baseline | [V2 dev collection failed](#collection-retry-improved) |
| Holdout | [Holdout collection failed](#collection-retry-holdout) |

| Failed stage | Example retry label | Use it afterward |
|---|---|---|
| Initial V1 baseline | `baseline-retry` | Feedback and `verify --baseline baseline-retry` |
| V2 dev candidate | `improved-retry` | Comparison and `verify --candidate improved-retry` |
| Frozen V2 holdout | `holdout-retry` | Comparison and `verify --holdout holdout-retry` |

Choose the failed stage in the first table, run only that subsection's command, then apply the substitutions in the second table.

<a id="collection-retry-baseline"></a>

### Failed initial baseline

**Terminal — recollect V1:** use this after a 429 or timeout where a lower concurrency is the recovery:

```bash
python scripts/workshop.py collect --split dev --label baseline-retry --concurrency 2
```

**Checkpoint:** collection finishes at `18/18` without errors. Only **V1 collection** is complete; evaluation, portal, and trace checks still remain.

**If not:** do not create another label; preserve the error and original failure record.

**Next:** resume the main guide at [step 5-3's evaluation command](../README.md#baseline-evaluation). Note both substitutions now; do not repeat completed collection.

| Later command/path | Substitute |
|---|---|
| Every later command, file path, and example row ID that uses `baseline` | Use **`baseline-retry`**, including `feedback`, `compare`, `summary`, and `verify --baseline`. For example, `baseline-retry-sol-D01`. |
| V2 dev and holdout `collect` commands | Add **`--concurrency 2`**. |

<a id="collection-retry-improved"></a>

### V2 dev collection failed

Also use this command to collect a new label when README 7-4 shows the review was not carried (`source trace carried: no`) or [V2 changed after 7-2](#v2-changed).

**Terminal — recollect V2 dev:** check `concurrency` in the completed baseline's `manifest.json`. If it is `2`, replace `--concurrency 4` below with `--concurrency 2`.

```bash
python scripts/workshop.py collect --split dev --label improved-retry --concurrency 4
```

**Checkpoint:** collection finishes at `18/18` without errors.

**If not:** stop and preserve the error; keep the completed baseline and review unchanged.

**Next:** resume at [step 7's evaluation and comparison](../README.md#candidate-evaluation), replacing `improved` with `improved-retry`.

<a id="collection-retry-holdout"></a>

### Holdout collection failed

**Terminal — recollect holdout:** check `concurrency` in the completed baseline's `manifest.json`. If it is `2`, replace `--concurrency 4` below with `--concurrency 2`.

```bash
python scripts/workshop.py collect --split holdout --label holdout-retry --concurrency 4
```

**Checkpoint:** collection finishes at `12/12` without errors.

**If not:** stop and preserve the error; keep the frozen instructions unchanged.

**Next:** resume at [step 8's evaluation](../README.md#holdout-evaluation), replacing `holdout` with `holdout-retry`.

<a id="evaluation-retry"></a>

## If only Foundry evaluation failed

First require complete response collection. Read **`src/agent/.foundry/results/<label>/evaluation.json`** if present, then choose one action:

| Saved state / failure | Next action |
|---|---|
| No Foundry evaluation run was created, polling timed out, or a result download was interrupted | Resolve the cause, then use **A**. It reuses a saved Foundry evaluation run; it creates one only if none is recorded. |
| `status: failed / canceled / cancelled`, or `run → result_counts → errored` greater than 0 | Resolve the cause, then use **B** to preserve the failed attempt and create a retry. |
| Job completed with no errored rows, but validation rejects missing/duplicate IDs, null scores, or invalid output | Stop and preserve `evaluation.json` and any `evaluation-output-raw.json`. Ask the owner to inspect the result contract. **Do not force B or edit status/scores.** |
| Job and rows completed correctly, but valid scores are low | Do not retry. Finish the report/portal checkpoint and continue the workshop. |

Replace `baseline` below with **the label that actually failed**, including retry labels such as `improved-retry`. Run only one block, after the original command stops. There may be no output for 1–3 minutes while scoring.

**Terminal — A. start or resume evaluation with the same inputs:**

```bash
python scripts/workshop.py evaluate --label baseline
```

**Checkpoint:** `Foundry evaluation completed: ... (18 rows)`, or `(12 rows)` for holdout, appears with a report URL. Skip B below.

**If not:** use the saved-state table above again. For a polling timeout, resume with A; use B only for a recorded failed/errored run.

**Terminal — B. retry only a recorded failed/errored run:**

```bash
python scripts/workshop.py evaluate --label baseline --retry-failed
```

Never repeat `collect` for an evaluation failure.

**Checkpoint:** `evaluation.json` shows `status: completed`, the expected total count, and no errored rows; `evaluation-results.json` has one valid row per response.

**If not:** preserve `evaluation.json` and any raw output, then use the saved-state table above; do not edit status, scores, or rerun collection.

**Next:** finish the interrupted checkpoint before continuing: [baseline evaluation](../README.md#baseline-evaluation), [candidate evaluation](../README.md#candidate-evaluation), or [holdout evaluation](../README.md#holdout-evaluation).

<a id="no-failures"></a>

## If all baseline business checks pass

That is a legitimate result. Do not fabricate a failure or alter an answer/reference.

1. Put `baseline-sol-D01` (or another baseline row) into the `show` block of [README 6-2](../README.md#review-case) to see the saved response and fixed reference. Note its `row_id` and `trace_id`.
2. As in 6-2, compare the response with its fixed dev reference, then check its trace in the portal.
3. Write one line explaining that all business checks passed, what you inspected, and **behavior the provided V2 should preserve**. Do not claim a failure or improvement in advance.
4. Return to [6-3 to save the review](../README.md#save-review). `feedback` accepts passing dev responses too. Then review V2's suitability in step 7.

Final verification only checks that candidate results store the saved baseline trace ID; it does not reuse the baseline trace as candidate trace evidence. Do not search the holdout for a failure to use during development.

**Checkpoint:** the saved review names one baseline `row_id`, its `trace_id`, what you inspected, and the behavior V2 should preserve.

**If not:** return to the selected baseline response and fixed dev reference; do not use holdout or invent a failure.

**Next:** continue with [V2 deployment and candidate evaluation](../README.md#lab-e).

<a id="v2-changed"></a>

## If V2 changed after 7-2

Collect the holdout only with **the same V2 version** you evaluated in 7-3. Use this section if 8-1 collection stopped with `Hosted prompt does not match`, or if 8-2 showed different `agent_version` or `prompt_hash` values for improved and holdout. Do not delete or edit result files.

| What you did after 7-2 | What to do |
|---|---|
| Ran `set-prompt` or edited `.env` or a prompt file, without `azd deploy` | Restore the selection with **A** below, then return to 8-1. |
| Ran `azd deploy` again | The agent version changed, so the existing `improved` no longer pairs with the holdout. Follow **B** below. |

If you edited prompt files, keep your changes in a separate note, then restore **the provided originals**. Also restore any other `.env` values you changed to their 7-2 values.

| Workshop folder | Restore the original instructions |
|---|---|
| A participant's Git clone | **Terminal:** run `git restore -- src/agent/prompts` in this folder. |
| Self-study `$RUN_DIR/workshop` copy | **Editor:** copy the unchanged `src/agent/prompts/` files from the original clone into the same paths in the workshop copy. The copy has no `.git`; do not use the Git command above there. |
| Extracted ZIP folder | **Editor:** restore the original `src/agent/prompts/` files from the ZIP you started with. |

**Terminal — A. restore the V2 selection (no redeployment):**

```bash
python scripts/workshop.py set-prompt v2 &&
python scripts/workshop.py smoke
```

**Checkpoint:** `prompt_version: v2`, and `agent_version` equals the **V2 version** you noted in 7-2. If holdout collection never started, go to [8-1](../README.md#lab-f). If `holdout/manifest.json` already exists, preserve it and use [holdout recollection](#collection-retry-holdout).

**If not:** if the version differs or `Hosted prompt does not match` persists after restoring the original instructions and settings, the conditions no longer match the original V2. Follow **B**.

**B — start again from dev with the current V2 version:**

1. **Terminal:** check the current version with A's **command block** (reuse its output if you just ran it). For `Hosted prompt does not match`, run `azd deploy --no-prompt` **once**, then repeat A's command block. Once it shows `prompt_version: v2`, note the new `agent_version`.
2. Collect `improved-retry` with [V2 dev collection recovery](#collection-retry-improved). Complete README 7-3's evaluation/comparison and 7-4's summary with that label.
3. Then continue to step 8. If `holdout/manifest.json` already exists, use `holdout-retry` from [holdout recollection](#collection-retry-holdout). Use the changed labels in subsequent commands, file paths, and `verify`.

If you already saw the holdout, record `holdout reused during V2-change recovery` in your report. Do not tune instructions using those results or describe this as fresh, untouched validation.

**Checkpoint:** in 8-2's check, the new improved label and the holdout label have the same `agent_version` and `prompt_hash`.

**If not:** stop and record the error and label names. Do not delete earlier results or redeploy repeatedly to match versions.

**Next:** return to [8-1 collection](../README.md#lab-f) or [8-2's check](../README.md#holdout-evaluation).

<a id="portal-differs"></a>

## If the portal differs from a screenshot

Use your actual account, project, names, version, and time window.

| Difference | Check | Do not |
|---|---|---|
| Report URL is lost or opens the wrong report | In your editor, open `src/agent/.foundry/results/<actual-label>/evaluation.json`, copy **`run → report_url`**, and open it. | Do not repeat `collect` or `evaluate` just to retrieve the URL. |
| Tab changes show a different agent version | Re-select the intended version and compare the saved `prompt_version`. | Do not trust the visible tab after navigation without checking the saved response. |
| Project-wide **Evaluations** differs from the agent **Evaluation** tab | Open the list named in the README step. | Do not treat the two lists as interchangeable. |
| Version comparison is hard to find | Use **Version dropdown → Compare versions**, select two versions, then click **Send** once. | Do not use the agent **More** menu or send each pane separately. |
| Foundry **Indexes** is empty | Check the **Knowledge bases** source and Azure Search index separately. | Do not treat an empty Foundry index list as proof that retrieval failed. |
| **Monitor → Tools** is empty | Open the trace spans; code-level IQ spans can still be present. | Do not replace trace evidence with the portal tool list. |
| Older trace is missing | Expand the time range and search by the real trace ID. | Do not substitute another agent's trace, a Korean run, a recording, or a screenshot for English execution evidence. |
| Subscription alert or policy error appears | Treat it as a separate ARM issue for the instructor. | Do not change shared subscription settings to match a screenshot. |

Use [reference](reference.en.md) only for background, and [instructor guide](instructor.en.md) only when permissions or model preparation are needed.

**Checkpoint:** the portal screen matches your actual account, project, agent version, time window, and saved `prompt_version` or trace ID.

**If not:** preserve the screenshot and saved result file path for the instructor; do not change shared subscription settings.

**Next:** return to the interrupted portal check, or continue to [holdout results](../README.md#holdout-results) if that was the active step.

<a id="levels"></a>

## If a Level 2 or 3 command stopped

Confirm the original command has exited.
Level 2–3 state lives under **`src/agent/.foundry/results/suite/`** or **`src/agent/.foundry/results/level3/`**.
Choose the exact message below.
Recovery keeps step 5–9 evidence and ownership records; a separate experiment needs a new folder.
Valid low scores, successful attacks, `Quality gate FAILED`, and `Composite gate FAILED` are not retry reasons; if the same error recurs, tell the instructor.

Most failures match these visible rows:

| Message or situation | Next action |
|---|---|
| Command exited with `... still running`, `... still generating`, or `... still in progress` | Repeat with the same arguments and labels to resume the saved Foundry evaluation run. No `--retry-failed` or file deletion is needed. |
| Terminal closed or network timeout | Confirm the original process stopped and check for a saved Foundry evaluation run. If recorded, repeat the same command to inspect or resume it. Without a record, check for duplicate creation with the instructor; do not assume success. |
| `... evaluator results failed, for example because the judge hit its rate limit` | Inspect the actual error in `suite/<label>-output.json`. Rate limiting is only one possible cause. Resolve it, then use the printed `--retry-failed` command. Failed runs remain under `attempts` in `suite.json`. |
| `Suite run for ... ended as failed` | Resolve the cause, then repeat the command with `--retry-failed`. |

If your exact message is not in the table above, open the list below and follow only the matching row.

<details>
<summary>Other Level 2-3 messages (open only if your exact message is not above)</summary>

When a row says to run a command named by the failed output, copy that exact `python scripts/workshop.py ...` command and arguments from the output; do not invent arguments.

**Suite and evaluator setup**

| Message or situation | Next action |
|---|---|
| `Run register-evaluators before evaluate-suite.` or `Run evaluate-suite --labels ... first.` | Run the command the message names, then repeat. |
| `Evaluator ... already exists and is not owned by this folder` | The evaluator is not recorded as yours. Check the conflict with the instructor; do not change this folder's `LAB_PREFIX` or delete another evaluator to bypass it. |
| `... was registered with a different definition` or `The suite's evaluators changed ...` | Compare the registered definition and current code with the instructor. Restore only from a verified original; do not edit a registered evaluator to make it match. |
| `Saved ... responses changed after their suite run was created` | Compare the changed file with a verified original. Without an original, stop; do not recollect or edit hashes to force a match. |
| `... rubric results failed`, `... stress-test results failed`, `... red-team results failed`, or `The red-team scan returned incomplete results ...` | Resolve the cause, then follow [state-file recovery](#level-state-recovery). Distinguish execution errors from low scores. |
| `Comparison insight failed` or `Cluster insight failed` | Wait a minute, then repeat the same command. Only the failed insight is generated again; the failed one stays under `failed_attempts` in `insights.json`. |

**Level 3 runs and trace evaluation**

| Message or situation | Next action |
|---|---|
| `Rubric generation ended as ...` or `The run ended as ...` | Review the failed status and error with the instructor. Use [state-file recovery](#level-state-recovery) only after resolving the cause and only if the message explicitly calls for deletion. |
| `... already compares the rubrics on ...` or `... already holds a ...-question run` | Arguments differ from the saved Foundry evaluation run. Resume with the recorded values. Plan a separate experiment for new conditions; do not erase the existing record. |
| An HTTP `429` (Too Many Requests) error | Wait for `Retry-After`, or one minute if absent. Choose resume or failed-run retry based on the saved status. Do not increase `--count`. |
| `This folder has no deployed hosted agent` | Check the cause with the instructor. If already cleaned up, record sections 4 and 6 as **skipped, not completed** and do not redeploy. Do not claim Level 3 completion for unrun sections. |
| `... agent calls or evaluator results failed` | Resolve the recorded error, if any (a run can also finish without one evaluator's results), then run `python scripts/workshop.py evaluate-agent --split dev --retry-failed`. Only the failed model's run is replaced; the old run remains under `attempts`. |
| `The <model> run ended as failed: ... Error code: 500` | An internal service error. Wait a minute, then run `python scripts/workshop.py evaluate-agent --retry-failed`. |
| `The <model> run ended as failed: ... Error code: 401 ... PermissionDenied` | Section 4 calls the Foundry account's evaluation API as you, so you need **Foundry User** on the Foundry account; a project-scope assignment is not enough ([Levels preparation](instructor.en.md#levels)). After the environment owner assigns it and it applies (up to an hour), run `python scripts/workshop.py evaluate-agent --split dev --retry-failed`. |
| `evaluate-traces` ends with an access error, such as `ApplicationInsightsAccessDenied` | The instructor completes [trace access preparation](instructor.en.md#levels); then follow [state-file recovery](#level-state-recovery). |
| `... traces were not found ... evaluator results failed` | For missing traces above zero, check ingestion and access. With zero missing traces but evaluator errors, inspect the judge error instead. Resolve the cause, then follow [state-file recovery](#level-state-recovery). |

**Continuous evaluation and portal lookup**

| Message or situation | Next action |
|---|---|
| `Schedule ... already exists and is not owned by this folder` | The schedule is not recorded as yours. Check the conflict with the instructor; do not change `LAB_PREFIX` or delete the schedule. |
| `No scheduled run yet` | The first continuous-evaluation run starts at the printed time. Run `continuous-eval` again after it. |
| Continuous evaluation is `queued`/`in_progress`, or `failed`/zero traces | For waiting states, check again in one minute with the same command. For failure or zero traces, record incomplete execution and check traffic/access with the instructor. Creating a schedule is not completion. |
| Continuous evaluation is `completed` but has evaluator errors or empty results | The [row-level checkpoint](level-3.en.md#continuous-eval) has not passed. Record incomplete execution and inspect the cause; distinguish this from valid `passed: false` results. |
| The `red-team` scan is hard to find in the portal | In New Foundry, open **Evaluations → Red team** and select `<LAB_PREFIX>-red-team-sol`. Read the rates under **Overall metric results**; the list's **Issues in last run** column is not the number of successful attacks. |

</details>

**Checkpoint:** the Level 2-3 command either resumes to completion or records the exact failed saved state under `suite/` or `level3/`.

**If not:** stop repeating the command and share the saved state and raw error with the instructor.

**Next:** return to the interrupted Level 2 or Level 3 checkpoint, or continue to [step 10 cleanup](../README.md#cleanup) after optional work is complete.



<a id="level-state-recovery"></a>

### Level 3 only: when an error explicitly requires deleting a state file

**Not for waiting or low scores.** Some Level 3 commands require removing one state file to replace a failed run. Follow this order:

1. From the repository root, confirm the original command exited and resolve the error's cause.
2. **Back up before deleting:** Only the one state file named by the error is eligible; this block backs it up and rejects every other path. It creates `../workshop-backup/` and copies the named state file plus its sibling `<same-stem>-output.json` if present.

```bash
read -r -p "State file named in the error: " STATE_FILE &&
case "$STATE_FILE" in
  src/agent/.foundry/results/level3/*)
    if [ ! -f "$STATE_FILE" ]; then
      echo "Stop: state file not found"
      exit 1
    fi
    mkdir -p ../workshop-backup &&
    cp "$STATE_FILE" ../workshop-backup/ &&
    file_stem="${STATE_FILE%.*}" &&
    if [ -f "${file_stem}-output.json" ]; then
      cp "${file_stem}-output.json" ../workshop-backup/
    fi
    ;;
  *)
    echo "Stop: not a level3 state file"
    exit 1
    ;;
esac
```

3. Before deleting, confirm the copy is in `../workshop-backup/` and keep the terminal output. **Delete only that file, in the same shell, after the backup holds its IDs.** Never use wildcards.

```bash
rm -- "$STATE_FILE"
```

**Checkpoint:** the named file is gone and its copy remains in `../workshop-backup/`.

**If not:** stop; do not delete anything else.

**Next:** retry the failed stage once with the same command and arguments; new calls may cost money. If the error repeats, stop and share the original records with the instructor. Then finish with [step 10 cleanup](../README.md#cleanup); existing ownership records remain available for it, and cleanup that already succeeded is not repeated.

<a id="cleanup-recovery"></a>

## If cleanup or its verification stopped

Keep the same workspace, account, and ownership records. Files below are under **`src/agent/.foundry/results/`**.

| What finished | Next action |
|---|---|
| `cleanup --confirm` succeeded; `cleanup.json` records `completed: true`, but `check-cleanup` failed | Preserve that file and its `plan`. Resolve the reported access/propagation problem, then repeat **only the check below**. |
| Deletion itself stopped, or ownership/targets do not match | Stop automated deletion. Preserve the error, `cleanup-plan.json` if present, and ownership state. Before any further deletion, the owner (you, in self-study) checks that the plan's names match `LAB_AGENT_NAME` and `LAB_PREFIX` in this folder's `.env` and reconciles the original plan with Azure; partial counts are not complete cleanup. |

**Terminal — only after the deletion command succeeded:**

```bash
python scripts/workshop.py check-cleanup
```

Require the [step 10-3 checkpoint](../README.md#cleanup-check). If an object still exists or a preserved service is missing, report it; do not claim completion. Repeating `cleanup --confirm` would replace the recorded plan with the remaining ownership set, not verify the original deletion.

After a separately approved full-group deletion, use [final foundation verification](environment.en.md#final-cleanup-check), not `check-cleanup`.

**Checkpoint:** [step 10-3](../README.md#cleanup-check) confirms owned objects are gone and preserved shared services still exist.

**If not:** keep the cleanup files and reported Azure state for the owner; do not run `cleanup --confirm` again to replace the original plan.

**Next:** return to [10-3 cleanup verification](../README.md#cleanup-check). To retire your exclusive group, follow the [creation-record and deletion-scope checks](environment.en.md#final-cleanup).

<a id="setup-resume"></a>
<a id="environment-owners-resume-setup-after-closing-the-terminal"></a>

## Environment owners: resume incomplete setup

**Participants: stop here unless you were preparing the Azure environment.** Keep the original clone and `RUN_DIR`; do **not** make a new `RUN_ID`, repeat `init`, or overwrite a snapshot.

**Terminal — check the existing paths:** start `bash`, then paste the original clone path and existing `RUN_DIR` without quotes:

```bash
read -r -p "Absolute path of the original setup clone: " REPO_ROOT &&
cd "$REPO_ROOT" &&
read -r -p "Existing absolute RUN_DIR path: " RUN_DIR &&
ls "$RUN_DIR/config.json"
```

**Checkpoint:** the existing `config.json` path prints. Open it in your editor and check that `workspace` points to `workshop` under this `RUN_DIR`.

**If not:** recheck both paths in your notes. If the file is missing or belongs to another run, do not create or overwrite records.

| Existing files / completed work | Next action |
|---|---|
| `config.json` only; no `workshop/` | Run `source src/agent/.venv/bin/activate` in the original clone. Run only [the `prepare` command](environment.en.md#setup-snapshot) with this `RUN_DIR`, then continue to Python setup. |
| `workshop/` but no `source-manifest.json` | Source copy stopped. Keep the folder and error; do not delete it or invent a manifest. |
| Snapshot and manifest; Python or tests unfinished | Enter `"$RUN_DIR/workshop"`, run [isolated Python setup](environment.en.md#setup-python), and require `OK` before sign-in. |
| Snapshot, Python, and tests done | Restore the runnable workspace below, then pick the interrupted Azure stage. |

**Terminal — only if the snapshot and Python tests are complete:**

```bash
cd "$RUN_DIR/workshop" &&
source src/agent/.venv/bin/activate &&
export AZURE_CONFIG_DIR="$PWD/.azure-cli"
```

**Checkpoint:** activation succeeds and the CLI profile points to the existing runnable workspace; no new source or Azure environment was created.

**If not:** for a path error, compare it with `workspace` in `config.json` above. If the virtual environment is missing, use the incomplete Python/tests row above.

**Did a block joined with `&&` fail?** Commands after the failed command did not run. Resolve the cause, then continue **from the failed line through the end of that block** in order. When running one line at a time, remove its trailing `&&`. Do not repeat the successful earlier lines.

| Interrupted setup stage | Where to resume |
|---|---|
| Sign-in | Resume the unfinished sign-in in [environment 2-1](environment.en.md#setup-identity). Do not repeat successful sign-ins. |
| Provisioning in environment steps 2–5 | Run `cd "$REPO_ROOT"`, keep `AZURE_CONFIG_DIR`, [select the interrupted stage](environment.en.md#setup-route), and run its failed command and remaining unexecuted commands with the same `--run-dir "$RUN_DIR"`. |
| Candidate preparation in environment step 6 | Stay in `"$RUN_DIR/workshop"` and resume the failed [step 6](environment.en.md#setup-candidates) command. |
| Candidates ready; only calibration unfinished | Resume at [judge calibration](environment.en.md#setup-calibration) in the same workspace; do not repeat `prepare-models` |
| Environment already completed | Choose the [handoff](environment.en.md#handoff); do not repeat preparation. |

If login expired, use the configured account; do not bypass errors with another account, new names, or deleted ownership records.

**Checkpoint:** the original workspace, `RUN_DIR`, virtual environment, and `AZURE_CONFIG_DIR` are restored, and only the interrupted environment step is selected.

**If not:** preserve `config.json`, `RUN_DIR`, and the last error. In self-study you are the environment owner: check that `subscription` and `run_id` in `config.json` match this run, then resume only with the same `RUN_DIR`. Do not generate a new `RUN_ID` or overwrite the snapshot.

**Next:** return to the matching environment step above, or to [README bind](../README.md#bind-project) after handoff is complete.
