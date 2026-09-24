# If a step fails: stop, identify the cause, and resume safely

[Return to the English guide](../README.md) · [한국어](troubleshooting.ko.md)

**Keep the current folder and error output. Find only the failed stage:**
[sign-in](#login) · [environment setup](#setup-resume) · [retrieval](#retrieval) · [calibration](#calibration) · [collection](#collection-retry) · [evaluation](#evaluation-retry) · [traces](#telemetry) · [Levels 2–3](#levels) · [cleanup](#cleanup-recovery).
If the stage is unclear, use the tables below. **Do not restart the whole workshop.**

**First distinguish execution failure from low quality.**

| What you see | Next action |
|---|---|
| Exception, missing/duplicate response, or evaluator error | Stop the next step and [recover the failed command](#resume) |
| `collect` prints `business=False` | A business check failed, not the command. If collection finishes without errors, continue to that stage's evaluation. |
| Completed evaluation with low valid scores | Preserve the scores and finish that stage's checkpoint and portal check. For `baseline`, [review in step 6](../README.md#lab-d); for `improved`, [compare in 7-4](../README.md#compare-results); for `holdout`, [verify in step 9](../README.md#lab-g). |
| Missing or incomplete traces | Check ingestion, access, and the [query window](#telemetry); do not claim complete evidence |
| Only a recording of a successful run | Treat it as observation, not your own completed execution |

Share the failed command, error message, current step, and result label with the instructor. Do not share passwords, tokens, the full `.env`, or screenshots containing personal information.

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

Use the first incomplete stage to choose the recovery section. A completed manifest does not mean the whole workshop completed.

For a new experiment or another language, obtain unused names and use a separate folder. Deleting previous ownership or results is not a valid recovery strategy. If you were creating the Azure environment rather than collecting responses, use [setup recovery](#setup-resume).

<a id="symptoms"></a>

## Common symptoms

| Symptom | What to inspect |
|---|---|
| Missing `.env` or required setting | Put the instructor's complete file in the repository root; do not guess another team's deployment names |
| `read: -p: no coprocess` or activation path missing | Start Bash and use Terminal A's absolute `pwd` path |
| Language mismatch | Use the original language/workspace. `LAB_LANGUAGE=en` selects English; a missing setting preserves legacy Korean behavior. Never mix the two sets of results. |
| Nonempty `missing_models` | Ask the instructor to confirm all three exact deployments, versions, access, and quota; no substitutes |
| `The fixed auxiliary planner/judge deployment is missing` | The owner completes [auxiliary model preparation](instructor.en.md#auxiliary-model) and checks the actual `LAB_AUX_DEPLOYMENT` in `.env`. Neither `--allow-missing-models` nor `prepare-models` skips or creates that deployment. |
| Wrong account or tenant | Repeat [the two sign-ins and checks](../README.md#login); do not change a global default subscription |
| Login appears missing only in a new terminal | Restore `export AZURE_CONFIG_DIR="$PWD/.azure-cli"` in the correct folder |
| `bind` or `set-prompt` environment error | Confirm that `bind` ran in this folder and targets the expected project/language |
| Port 8088 unavailable | Check Terminal A and its readiness log; do not terminate an unrelated process |
| `prepare-iq` cannot create a role assignment | The Search identity needs planner access. Ask the environment owner to grant only that access; do not bypass ownership or grant Owner to the agent. |
| `retrieve` finishes without documents or without `TRAVEL-2026` | [Recover retrieval](#retrieval), checking registration separately from retrieval. Do not continue to local execution with empty evidence. |
| Model 404 | Distinguish the model catalog ID from the actual Azure deployment name |
| 429 or request timeout | Preserve the attempt; inspect capacity and Retry-After. If concurrency changes, use the same value for all compared cohorts. |
| Search 403 / role assignment failure | Check the user and agent instance identities separately; local success does not establish hosted permissions |
| IQ 400 | Inspect the pinned API/schema and planner deployment; a normal Search result is not an IQ replacement |
| Hosted 424 / cold start | Inspect the actual deployed version and session logs; retry that version only when ready |
| `connections/read` on startup | Use injected telemetry configuration rather than broadening access indiscriminately |
| Completed job with errors or null scores | Follow [evaluation recovery](#evaluation-retry); do not turn errors into zero scores or passes |
| `verify` succeeds but a `candidate_quality_gates` value is `false` | A valid execution can expose a quality failure. [Follow the completion decision](../README.md#completion-decision); report it and clean up, not rerun for a better score. |
| `production_release_approved: false` | Expected, even when business gates pass. This is not a permission error or a field to edit. [Separate execution, quality, and approval](../README.md#completion-decision). |
| CLI extension notice after JSON | The supplied parser separates recognized notices only. Do not upgrade the extension mid-experiment just to remove a notice. |
| Missing App Insights `ResourceId` metadata | Ask an authorized instructor to inspect the dedicated connection; do not modify a shared connection |
| Unfamiliar cleanup target | Stop and use [cleanup recovery](#cleanup-recovery). Do not edit or delete the ownership ledger to force deletion. |

<a id="login"></a>

## If the authentication browser does not open

First run the **CLI-profile and tenant/subscription input block** from [README step 1-3](../README.md#login) in the same terminal.

**Run only the command for the CLI whose sign-in failed.** If both need sign-in, run Azure CLI first, then azd.

**Azure CLI:**

```bash
az login --tenant "$LOGIN_TENANT_ID" --subscription "$LOGIN_SUBSCRIPTION_ID" \
  --use-device-code --output none
```

**azd:**

```bash
azd auth login --tenant-id "$LOGIN_TENANT_ID" --use-device-code
```

Open the address shown by each command and enter the code from **your own terminal**. Sign in with the configured account, then return to the README's [two-account verification block](../README.md#login-check), without repeating the sign-in commands.

Never share or record one-time codes. If organizational policy blocks device-code authentication, use an approved environment rather than bypassing the policy.

References: [interactive Azure CLI sign-in](https://learn.microsoft.com/cli/azure/authenticate-azure-cli-interactively) and [CLI configuration directories](https://learn.microsoft.com/cli/azure/azure-cli-configuration#cli-configuration-file).

<a id="retrieval"></a>

## If registered policies do not appear in retrieval

Use this section when step 2's question returns no **`TRAVEL-2026` in `document_ids`**, or an empty `activity`. An error-free `retrieve` command does not by itself establish that the required policy was found.

1. Confirm that `prepare-iq` ended with **`Foundry IQ ready: ...; 7 synthetic documents.`**. Retrieval's `knowledge_base` must also match your `LAB_PREFIX` plus `-kb`. If registration itself failed, resolve that error first.
2. Open the **`saved` path** printed by `retrieve` in your editor and inspect `documents`, `references`, and `activity`. If registration just finished, allow the index to become queryable, then repeat **[only step 2's same `retrieve` command](../README.md#policy-retrieval)**. Do not repeat `prepare-iq`, deployment, or response collection just to check retrieval.
3. If evidence is still missing, ask the environment owner to check your workshop's KB/source/index chain: **`LAB_PREFIX-kb` → `LAB_PREFIX-source` → `LAB_PREFIX-policies`**. Read `LAB_PREFIX` as the actual value from `.env`.

Preserve the result file and KB name. Do not change policies/questions to pass the check or use another team's KB. After recovery, finish **step 2's checkpoint and portal check**, then continue to step 3.

<a id="calibration"></a>

## If judge calibration does not pass

Check **`src/agent/.foundry/results/judge-calibration/evaluation.json`** if it exists. If the job is **still running**, or a creation/download error has been resolved, resume with:

```bash
python scripts/workshop.py calibrate
```

Use the following only when the saved `status` is **`failed` / `canceled` / `cancelled`**, or **`run → result_counts → errored` is greater than 0**. Resolve the cause first; the failed job is preserved.

```bash
python scripts/workshop.py calibrate --retry-failed
```

Malformed/missing results without a recorded failed/errored run require owner review of this calibration folder's saved status and raw output, not a forced retry. If the judge completed but did **not** distinguish the supplied amounts, review its configuration with the owner. Do not edit the examples/threshold or rerun a valid low score. Calibration is separate from the 48 agent responses.

<a id="telemetry"></a>

## If traces are missing after a pause

`monitor` defaults to the **last two hours**, even if the portal displays Last Day. For a run from the last 24 hours, extend the window while keeping the **same label**:

```bash
python scripts/workshop.py monitor --label baseline --hours 24
```

Replace `baseline` with the label whose monitoring failed (`improved` or `holdout` when applicable). `--hours` accepts whole hours from **1 to 168**. Use a window containing your original collection time; it does not recreate expired/deleted telemetry.

The query still filters the exact agent and run, and missing, duplicate, foreign, or sampled traces still fail coverage checks. If the data is recent, allow ingestion to finish and repeat only this command. If it remains incomplete, inspect access, retention, and the connected App Insights resource with the environment owner. Never recollect answers or edit `telemetry.json` to manufacture completeness.

After recovery, return to the interrupted checkpoint. If you already performed cleanup, read the saved evidence instead; starting another experiment requires a fresh workspace and names.

<a id="collection-retry"></a>

## If response collection failed

Use this path when collection failed, or when its original process **has been confirmed stopped** even though the manifest still says `running`. If it is active, wait; do not start a second collector.

Keep the original label's manifest, raw responses, and `failure.json` if present. An interrupted process may not have written that error file. Do not edit its status, score only successful rows, or overwrite that label.

**Recover only the failed stage.** Keep the models, corpus, questions, and instruction/version for that stage fixed. After addressing the cause, collect its complete matrix under a new label:

| Failed stage | New label in these examples | Use it afterward |
|---|---|---|
| Initial V1 baseline | `baseline-retry` | Feedback and `verify --baseline baseline-retry` |
| V2 dev candidate | `improved-retry` | Comparison and `verify --candidate improved-retry` |
| Frozen V2 holdout | `holdout-retry` | Comparison and `verify --holdout holdout-retry` |

Evaluate and monitor the **new label**, and use it in later commands **and file paths**. Each example assumes its retry label is unused; if it already exists, choose another unused label everywhere. Keep the other completed labels and reviewed provenance unchanged.

**Failed initial baseline, before any completed comparison:** if reducing concurrency to 2 resolves the cause, use:

```bash
python scripts/workshop.py collect --split dev --label baseline-retry --concurrency 2 &&
python scripts/workshop.py evaluate --label baseline-retry &&
python scripts/workshop.py compare --labels baseline-retry &&
python scripts/workshop.py monitor --label baseline-retry &&
python scripts/workshop.py summary --labels baseline-retry
```

Use **`baseline-retry` consistently** for later feedback, comparison, and `verify --baseline`. Use concurrency 2 for candidate and holdout too; changing only one cohort invalidates the comparison.
After all five commands finish and the summary shows `baseline-retry business-check failures:`, **open the new evaluation's report URL for step 5's portal check**. Use that summary for [case selection in 6-2](../README.md#review-case), keeping this label. Do not repeat completed collection, evaluation, or monitoring.

**Failed V2 dev or holdout after a completed baseline:** keep that baseline's recorded `concurrency` from `manifest.json`. The examples below assume **4**; use its actual value if different. Choose **one** command, not both:

```bash
python scripts/workshop.py collect --split dev --label improved-retry --concurrency 4
```

```bash
python scripts/workshop.py collect --split holdout --label holdout-retry --concurrency 4
```

After a V2 dev retry reaches **18/18**, return directly to [step 7's evaluation and comparison](../README.md#candidate-evaluation), replacing `improved` with `improved-retry`. After a holdout retry reaches **12/12**, return directly to [step 8's evaluation](../README.md#holdout-evaluation), replacing `holdout` with `holdout-retry`. Do not repeat deployment or collection at the top of those steps.

Do not redeploy, change the prompt after seeing holdout, or recreate the completed baseline and its review. A holdout execution retry is **not a new untouched validation set**. If you must change concurrency after baseline completed, start a separately controlled experiment; do not erase the original evidence.

<a id="evaluation-retry"></a>

## If only Foundry evaluation failed

First require complete response collection. Read **`src/agent/.foundry/results/<label>/evaluation.json`** if present, then choose one action:

| Saved state / failure | Next action |
|---|---|
| No run was created, polling timed out, or a result download was interrupted | Resolve the cause, then use **A**. It reuses a saved run; it creates one only if none is recorded. |
| `status: failed / canceled / cancelled`, or `run → result_counts → errored` greater than 0 | Resolve the cause, then use **B** to preserve the failed attempt and create a retry. |
| Job completed with no errored rows, but validation rejects missing/duplicate IDs, null scores, or invalid output | Stop and preserve `evaluation.json` and any `evaluation-output-raw.json`. Ask the owner to inspect the result contract. **Do not force B or edit status/scores.** |
| Job and rows completed correctly, but valid scores are low | Do not retry. Finish the report/portal checkpoint and continue the workshop. |

**A — start or resume evaluation with the same inputs:**

```bash
python scripts/workshop.py evaluate --label baseline
```

**B — retry only a recorded failed/errored run:**

```bash
python scripts/workshop.py evaluate --label baseline --retry-failed
```

Replace `baseline` with the actual label when recovering another stage. Never repeat `collect` for an evaluation failure. Finish the interrupted checkpoint before continuing.

<a id="no-failures"></a>

## If all baseline business checks pass

That is a legitimate result. Do not fabricate a failure or alter an answer/reference.

1. Select **one English dev response** from `src/agent/.foundry/results/baseline/responses.jsonl`. Note its `row_id` and `trace_id`.
2. Follow [the table in README 6-2](../README.md#review-case): compare the same response, its fixed dev reference, then its trace.
3. Write one line explaining that all business checks passed, what you inspected, and **behavior the provided V2 should preserve**. Do not claim a failure or improvement in advance.
4. Return to [6-3 to save the review](../README.md#save-review). `feedback` accepts passing dev responses too. Then review V2's suitability in step 7.

The final verification requires reviewed baseline provenance to be consumed by the candidate. Do not search the holdout for a failure to use during development.

<a id="portal-differs"></a>

## If the portal differs from a screenshot

Use your actual account, project, names, version, and time window. Tab changes can reset the selected agent version; also inspect `prompt_version` in the response.

Project-wide **Evaluations** and an agent's **Evaluation** tab are different lists. Foundry **Indexes** may not mirror the actual Search index. **Monitor → Tools** may be empty while code-level IQ spans appear in a trace.

Version comparison is under the **Version dropdown → Compare versions**, not the agent's **More** menu. Select two different versions. One **Send** submits to both panes; sending again creates additional calls.

Search an older trace by its real ID after expanding the time range. Do not substitute another agent's trace, a Korean run, or a screenshot for English execution evidence. Treat separate subscription alert/policy errors separately and never change shared settings merely to match a screenshot.

<a id="levels"></a>

## If a Level 2 or 3 command stopped

Commands that create evaluation runs save their state under **`src/agent/.foundry/results/suite/`** or **`src/agent/.foundry/results/level3/`**. Distinguish resuming a saved run from replacing a failed one below. **First confirm that the original command exited**; wait while it is still running.

Recovery does not change the step 5–9 responses or criteria. Low valid scores, successful attacks, and `Quality gate FAILED` are not reasons to retry. If the same error recurs, stop repeating the command and tell the instructor.

| Message or situation | Next action |
|---|---|
| Command exited with `... still running`, `... still generating`, or `... still in progress` | Repeat with the same arguments and labels to resume the saved run. No `--retry-failed` or file deletion is needed. |
| Terminal closed or network timeout | Confirm the original process stopped and check for a saved run. If recorded, repeat the same command to inspect/resume it. Without a record, check for duplicate creation with the instructor; do not assume success. |
| `... evaluator results failed, for example because the judge hit its rate limit` | Inspect the actual error in `suite/<label>-output.json`. Rate limiting is only one possible cause. Resolve it, then use the printed `--retry-failed` command. Failed runs remain under `attempts` in `suite.json`. |
| `Suite run for ... ended as failed` | Resolve the cause, then repeat the command with `--retry-failed`. |
| `Run register-evaluators before evaluate-suite.` or `Run evaluate-suite --labels ... first.` | Run the command the message names, then repeat. |
| `Evaluator ... already exists and is not owned by this folder` | The evaluator is not recorded as yours. Check the conflict with the instructor; do not change this folder's `LAB_PREFIX` or delete another evaluator to bypass it. |
| `... was registered with a different definition` or `The suite's evaluators changed ...` | Compare the registered definition and current code with the instructor. Restore only from a verified original; do not edit a registered evaluator to make it match. |
| `Saved ... responses changed after their suite run was created` | Compare the changed file with a verified original. Without an original, stop; do not recollect or edit hashes to force a match. |
| `... rubric results failed`, `... stress-test results failed`, or `... red-team results failed` | Resolve the cause, then follow [state-file recovery](#level-state-recovery). Distinguish execution errors from low scores. |
| `Comparison insight failed` or `Cluster insight failed` | Wait a minute, then repeat the same command. Only the failed insight is generated again; the failed one stays under `failed_attempts` in `insights.json`. |
| `Rubric generation ended as ...` or `The run ended as ...` | Review the failed status and error with the instructor. Use [state-file recovery](#level-state-recovery) only after resolving the cause and only if the message explicitly calls for deletion. |
| `... already compares the rubrics on ...` or `... already holds a ...-question run` | Arguments differ from the saved run. Resume with the recorded values. Plan a separate experiment for new conditions; do not erase the existing record. |
| An HTTP `429` (Too Many Requests) error | Wait for `Retry-After`, or one minute if absent. Choose resume or failed-run retry based on the saved status. Do not increase `--count`. |
| `This folder has no deployed hosted agent` | Check the cause with the instructor. If already cleaned up, record sections 4 and 6 as **not run** and do not redeploy. Do not claim Level 3 completion for unrun sections. |
| `... agent calls or evaluator results failed` | Resolve the recorded error, then run `evaluate-agent --split dev --retry-failed`. Only the failed model's run is replaced; the old run remains under `attempts`. |
| `The <model> run ended as failed: ... Error code: 500` | An internal service error. Wait a minute, then run `evaluate-agent --retry-failed`. If the same model fails again, tell the instructor. |
| `evaluate-traces` ends with an access error, such as `ApplicationInsightsAccessDenied` | The instructor completes [trace access preparation](instructor.en.md#levels); then follow [state-file recovery](#level-state-recovery). |
| `... traces were not found ... evaluator results failed` | For missing traces above zero, check ingestion and access. With zero missing traces but evaluator errors, inspect the judge error instead. Resolve the cause, then follow [state-file recovery](#level-state-recovery). |
| `Schedule ... already exists and is not owned by this folder` | The schedule is not recorded as yours. Check the conflict with the instructor; do not change `LAB_PREFIX` or delete the schedule. |
| `No scheduled run yet` | The first continuous-evaluation run starts at the printed time. Run `continuous-eval` again after it. |
| Continuous evaluation is `queued`/`in_progress`, or `failed`/zero traces | For waiting states, check again in one minute with the same command. For failure or zero traces, record incomplete execution and check traffic/access with the instructor. Creating a schedule is not completion. |
| Continuous evaluation is `completed` but has evaluator errors or empty results | The [row-level checkpoint](level-3.en.md#continuous-eval) has not passed. Record incomplete execution and inspect the cause; distinguish this from valid `passed: false` results. |
| The `red-team` scan is hard to find in the portal | In New Foundry, open **Evaluations → Red team** and select `<LAB_PREFIX>-red-team-sol`. Read the rates under **Overall metric results**; the list's **Issues in last run** column is not the number of successful attacks. |

A separate experiment with new names needs a new folder. Keep the names and ownership records of this existing run.

<a id="level-state-recovery"></a>

### Only when an error explicitly requires deleting a state file

**Not for waiting or low scores.** Some Level 3 commands require removing one state file to replace a failed run. Follow this order:

1. Confirm the original command exited and resolve the error's cause. Check that the named path is **one file inside this workshop's `src/agent/.foundry/results/level3/`**. Ask the instructor if the path is unclear.
2. **Back up before deleting:** use your editor to copy the file and that run's raw output (`*-output.json`, if present) into a private workshop backup folder. Confirm the run/eval/job IDs and error records are preserved. Do not upload them to a public repository.
3. Delete **only the named state file**. Never remove the whole `suite/` or `level3/` folder, ownership files, or step 5–9 responses, evaluations, or traces.
4. Retry the failed stage with the same command and arguments; new calls may cost money. If the error repeats, stop and share the original records with the instructor.

Ownership records for existing custom evaluators and generated datasets remain available for cleanup. Finish with [step 10 cleanup](../README.md#cleanup); do not repeat cleanup that already succeeded.

<a id="cleanup-recovery"></a>

## If cleanup or its verification stopped

Keep the same workspace, account, and ownership records. Files below are under **`src/agent/.foundry/results/`**.

| What finished | Next action |
|---|---|
| `cleanup --confirm` succeeded; `cleanup.json` records `completed: true`, but `check-cleanup` failed | Preserve that file and its `plan`. Resolve the reported access/propagation problem, then repeat **only the check below**. |
| Deletion itself stopped, or ownership/targets do not match | Stop automated deletion. Preserve the error, `cleanup-plan.json` if present, and ownership state. The owner must reconcile the original plan with Azure before any further deletion; partial counts are not complete cleanup. |

**Only after the deletion command succeeded:**

```bash
python scripts/workshop.py check-cleanup
```

Require the [step 10-3 checkpoint](../README.md#cleanup-check). If an object still exists or a preserved service is missing, report it; do not claim completion. Repeating `cleanup --confirm` would replace the recorded plan with the remaining ownership set, not verify the original deletion.

After a separately approved full-group deletion, use [final foundation verification](environment.en.md#final-cleanup-check), not `check-cleanup`.

<a id="setup-resume"></a>
<a id="environment-owners-resume-setup-after-closing-the-terminal"></a>

## Environment owners: resume incomplete setup

Keep the original clone and recorded `RUN_DIR`, even if setup stopped before Python installation. First confirm that the original preparation command has stopped. Do **not** generate a new `RUN_ID`, repeat a successful `init`, or overwrite a source snapshot.

Start `bash`, then enter the **original clone path** and the **existing `RUN_DIR` path** printed during setup, without quotation marks:

```bash
read -r -p "Absolute path of the original setup clone: " REPO_ROOT &&
cd "$REPO_ROOT" &&
read -r -p "Existing absolute RUN_DIR path: " RUN_DIR &&
ls "$RUN_DIR/config.json"
```

**Check the saved stage before activating the runnable workspace.** Open **`$RUN_DIR/config.json`** in your editor and confirm that its `workspace` is **this `RUN_DIR/workshop`**. If the config is missing or points elsewhere, stop and inspect the failed initialization; do not create a replacement record.

| Existing files / completed work | Next action |
|---|---|
| `config.json` exists; `workshop/` does not | From the original clone, activate `source src/agent/.venv/bin/activate`, then run only [the `prepare` command](environment.en.md#setup-snapshot) with this `RUN_DIR`. Continue to the isolated Python step afterward. |
| `workshop/` exists but `source-manifest.json` is missing | Source copying stopped partway. Preserve the directory and error for owner review; `prepare` refuses to overwrite it. Do not delete the folder or invent a manifest. |
| Snapshot/manifest exist; isolated Python installation or tests are unfinished | Enter `"$RUN_DIR/workshop"`. Use [the isolated Python step](environment.en.md#setup-python) to create the virtual environment only if missing, activate it, then resume installation/tests. Require `OK` before sign-in. |
| Snapshot, isolated Python installation, and tests completed | Restore the runnable workspace below, then select the interrupted Azure stage. |

**Only once the snapshot and Python tests are complete:**

```bash
cd "$RUN_DIR/workshop" &&
source src/agent/.venv/bin/activate &&
export AZURE_CONFIG_DIR="$PWD/.azure-cli"
```

**Checkpoint:** activation succeeds and the CLI profile points to the existing runnable workspace. No new source or Azure environment was created by restoring the terminal.

| Interrupted setup stage | Where to resume |
|---|---|
| Sign-in | Stay in this workspace and follow [README step 1-3](../README.md#login), then return to [environment step 2](environment.en.md#setup-identity) |
| Provisioning in environment steps 2–5 | Run `cd "$REPO_ROOT"`, keep `AZURE_CONFIG_DIR` unchanged, and [select the interrupted stage](environment.en.md#setup-route). Resume only its failed command with the same `--run-dir "$RUN_DIR"`. |
| Candidate preparation in environment step 6 | Stay in `"$RUN_DIR/workshop"` and resume the failed command in [step 6](environment.en.md#setup-candidates) |
| Environment already completed | Choose the [self-study or class handoff](environment.en.md#handoff); do not repeat preparation |

If a login has expired, restore it using the configured account. Never use a different account, new resource names, or deleted ownership records to bypass an error.
