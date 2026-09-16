# If a step fails: stop, identify the cause, and resume safely

[Return to the English guide](../README.md) · [한국어](troubleshooting.ko.md)

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
| Collection failed; manifest status is `failed` | Follow [collection recovery](#collection-retry), preserving the failed attempt |
| `Evaluation is still running` | Repeat only `evaluate` with the same label |
| Evaluation is failed/canceled or has error rows | Resolve the cause, then follow [evaluation recovery](#evaluation-retry) with `--retry-failed` |
| `Telemetry is incomplete` | Check ingestion/access and the [two-hour query window](#telemetry); repeat only `monitor` for that label |
| `Label ... already exists` | Read the manifest. For `completed`, continue with evaluation; for `failed`, recover collection. If `running`, establish whether the original process is still active before starting anything else. |
| Reviewed regression already exists | Verify its row, reason, language, and source trace. Continue only if they match the intended review; do not overwrite it. |

**Reopened a terminal?** Open your **existing workshop folder**, not a new clone, and follow [the terminal restore block](../README.md#resume-shell). Do not repeat `init`, `bind`, deployment, or collection just because the terminal is empty.

Under **`src/agent/.foundry/results/<label>/`**, `manifest.json` describes **collection only**. Check `evaluation.json` for evaluation status and `telemetry.json` for trace coverage; a completed collection is not a completed evaluation.

For a new experiment or another language, obtain unused names and use a separate folder. Deleting previous ownership or results is not a valid recovery strategy. If you were creating the Azure environment rather than collecting responses, use [setup recovery](#setup-resume).

## Common symptoms

| Symptom | What to inspect |
|---|---|
| Missing `.env` or required setting | Put the instructor's complete file in the repository root; do not guess another team's deployment names |
| `read: -p: no coprocess` or activation path missing | Start Bash and use Terminal A's absolute `pwd` path |
| Language mismatch | Use the original language/workspace. `LAB_LANGUAGE=en` selects English; a missing setting preserves legacy Korean behavior. Never mix the two sets of results. |
| Nonempty `missing_models` | Ask the instructor to confirm all four exact deployments, versions, access, and quota; no substitutes |
| `The fixed auxiliary planner/judge deployment is missing` | The owner completes [auxiliary model preparation](instructor.en.md#auxiliary-model) and checks the actual `LAB_AUX_DEPLOYMENT` in `.env`. Neither `--allow-missing-models` nor `prepare-models` skips or creates that deployment. |
| Wrong account or tenant | Repeat [the two sign-ins and checks](../README.md#login); do not change a global default subscription |
| Login appears missing only in a new terminal | Restore `export AZURE_CONFIG_DIR="$PWD/.azure-cli"` in the correct folder |
| `bind` or `set-prompt` environment error | Confirm that `bind` ran in this folder and targets the expected project/language |
| Port 8088 unavailable | Check Terminal A and its readiness log; do not terminate an unrelated process |
| `prepare-iq` cannot create a role assignment | The Search identity needs planner access. Ask the environment owner to grant only that access; do not bypass ownership or grant Owner to the agent. |
| Model 404 | Distinguish the model catalog ID from the actual Azure deployment name |
| 429 or request timeout | Preserve the attempt; inspect capacity and Retry-After. If concurrency changes, use the same value for all compared cohorts. |
| Search 403 / role assignment failure | Check the user and agent instance identities separately; local success does not establish hosted permissions |
| IQ 400 | Inspect the pinned API/schema and planner deployment; a normal Search result is not an IQ replacement |
| Hosted 424 / cold start | Inspect the actual deployed version and session logs; retry that version only when ready |
| `connections/read` on startup | Use injected telemetry configuration rather than broadening access indiscriminately |
| Completed job with errors or null scores | Inspect every output row; do not turn errors into zero scores or passes |
| `verify` succeeds but a `candidate_quality_gates` value is `false` | A valid execution can expose a quality failure. [Follow the completion decision](../README.md#completion-decision); report it and clean up, not rerun for a better score. |
| `production_release_approved: false` | Expected, even when business gates pass. This is not a permission error or a field to edit. [Read the three outcomes](../README.md#completion-decision). |
| CLI extension notice after JSON | The supplied parser separates recognized notices only. Do not upgrade the extension mid-experiment just to remove a notice. |
| Missing App Insights `ResourceId` metadata | Ask an authorized instructor to inspect the dedicated connection; do not modify a shared connection |
| Unfamiliar cleanup target | Stop. Do not edit or delete the ownership ledger to force deletion. |

<a id="login"></a>

## If the authentication browser does not open

First run the **CLI-profile and tenant/subscription input block** from [README step 1-3](../README.md#login) in the same terminal.

```bash
az login --tenant "$LOGIN_TENANT_ID" --subscription "$LOGIN_SUBSCRIPTION_ID" \
  --use-device-code --output none &&
azd auth login --tenant-id "$LOGIN_TENANT_ID" --use-device-code
```

Open the address shown by each command and enter the code from **your own terminal**. Sign in with the configured account, then return to the README's [two-account verification block](../README.md#login-check), without repeating the sign-in commands.

Never share or record one-time codes. If organizational policy blocks device-code authentication, use an approved environment rather than bypassing the policy.

References: [interactive Azure CLI sign-in](https://learn.microsoft.com/cli/azure/authenticate-azure-cli-interactively) and [CLI configuration directories](https://learn.microsoft.com/cli/azure/azure-cli-configuration#cli-configuration-file).

<a id="calibration"></a>

## If judge calibration does not pass

If the evaluation is **still running**, repeat only:

```bash
python scripts/workshop.py calibrate
```

If its native job failed, was canceled, or contains error rows, resolve the cause first, then preserve the failed job and retry:

```bash
python scripts/workshop.py calibrate --retry-failed
```

If the job completed but the judge did **not** distinguish the supplied supported and unsupported amounts, stop and review the judge/configuration with the environment owner. Do not edit the examples or threshold, or repeatedly rerun a valid low score until it passes. Calibration is separate from the 64 agent responses.

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

Keep the failed label's `failure.json`, manifest, and raw responses. Do not score only successful rows or overwrite that label.

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
python scripts/workshop.py monitor --label baseline-retry
```

Use **`baseline-retry` consistently** for later feedback, comparison, and `verify --baseline`. Use concurrency 2 for candidate and holdout too; changing only one cohort invalidates the comparison.
After all four commands finish, **open the new evaluation's report URL for step 5's portal check**, then continue at [case selection in 6-2](../README.md#review-case) using this label. Do not repeat completed collection, evaluation, or monitoring.

**Failed V2 dev or holdout after a completed baseline:** keep that baseline's recorded `concurrency` from `manifest.json`. The examples below assume **4**; use its actual value if different. Choose **one** command, not both:

```bash
python scripts/workshop.py collect --split dev --label improved-retry --concurrency 4
```

```bash
python scripts/workshop.py collect --split holdout --label holdout-retry --concurrency 4
```

After a V2 dev retry reaches **24/24**, return directly to [step 7's evaluation and comparison](../README.md#candidate-evaluation), replacing `improved` with `improved-retry`. After a holdout retry reaches **16/16**, return directly to [step 8's evaluation](../README.md#holdout-evaluation), replacing `holdout` with `holdout-retry`. Do not repeat deployment or collection at the top of those steps.

Do not redeploy, change the prompt after seeing holdout, or recreate the completed baseline and its review. A holdout execution retry is **not a new untouched validation set**. If you must change concurrency after baseline completed, start a separately controlled experiment; do not erase the original evidence.

<a id="evaluation-retry"></a>

## If only Foundry evaluation failed

First require complete response collection. If only local polling timed out while the cloud run is still active, resume the **same evaluation**:

```bash
python scripts/workshop.py evaluate --label baseline
```

If the stored run actually failed, was canceled, or returned error rows, resolve the cause and create a preserved retry:

```bash
python scripts/workshop.py evaluate --label baseline --retry-failed
```

`--retry-failed` is not for low quality scores. Replace `baseline` with the actual label when recovering another stage. Finish the interrupted step's checkpoint before continuing.

<a id="no-failures"></a>

## If all baseline business checks pass

That is a legitimate result. Do not fabricate a failure or alter an answer/reference.

1. Select **one English dev response** from `src/agent/.foundry/results/baseline/responses.jsonl`. Note its `row_id`, `case_id`, `model_key`, and `trace_id`.
2. Follow [items 2–4 of README 6-2](../README.md#review-case) to compare that response, its fixed dev reference, and its trace.
3. Explain that all business checks passed, what you inspected, and why comparing the provided V2 is useful. Do not claim a failure or improvement in advance.
4. Return to [6-3 to save the review](../README.md#save-review). `feedback` accepts passing dev responses too. Then review V2's suitability in step 7.

The final verification requires reviewed baseline provenance to be consumed by the candidate. Do not search the holdout for a failure to use during development.

## If the portal differs from a screenshot

Use your actual account, project, names, version, and time window. Tab changes can reset the selected agent version; also inspect `prompt_version` in the response.

Project-wide **Evaluations** and an agent's **Evaluation** tab are different lists. Foundry **Indexes** may not mirror the actual Search index. **Monitor → Tools** may be empty while code-level IQ spans appear in a trace.

Version comparison is under the **Version dropdown → Compare versions**, not the agent's **More** menu. Select two different versions. One **Send** submits to both panes; sending again creates additional calls.

Search an older trace by its real ID after expanding the time range. Do not substitute another agent's trace, a Korean run, or a screenshot for English execution evidence. Treat separate subscription alert/policy errors separately and never change shared settings merely to match a screenshot.

<a id="setup-resume"></a>

## Environment owners: resume setup after closing the terminal

Use this only if [environment step 1](environment.en.md) completed the source snapshot and Python environment. Do **not** generate a new `RUN_ID` or run `init` / `prepare` again.

Start `bash`, then enter the **original clone path** and the **existing `RUN_DIR` path** printed during setup, without quotation marks:

```bash
read -r -p "Absolute path of the original setup clone: " REPO_ROOT &&
cd "$REPO_ROOT" &&
read -r -p "Existing absolute RUN_DIR path: " RUN_DIR &&
ls "$RUN_DIR/config.json" "$RUN_DIR/source-manifest.json" &&
cd "$RUN_DIR/workshop" &&
source src/agent/.venv/bin/activate &&
export AZURE_CONFIG_DIR="$PWD/.azure-cli"
```

**Checkpoint:** both recorded files exist, activation succeeds, and the CLI profile points to the existing runnable workspace. If a file is missing, stop and inspect that incomplete setup with the environment owner; do not manufacture a replacement manifest.

| Interrupted setup stage | Where to resume |
|---|---|
| Sign-in | Stay in this workspace and follow [README step 1-3](../README.md#login), then return to environment step 2 |
| Provisioning in environment steps 2–5 | Run `cd "$REPO_ROOT"`, keep `AZURE_CONFIG_DIR` unchanged, then resume only the failed command with the same `--run-dir "$RUN_DIR"` |
| Candidate preparation in environment step 6 | Stay in `"$RUN_DIR/workshop"` and resume the failed command |
| Environment already completed | Choose the [self-study or class handoff](environment.en.md#handoff); do not repeat preparation |

If a login has expired, restore it using the configured account. Never use a different account, new resource names, or deleted ownership records to bypass an error.
