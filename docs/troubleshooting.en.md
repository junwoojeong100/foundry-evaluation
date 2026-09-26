# Resume a paused workshop without repeating completed work

[Return to the English guide](../README.md) · [한국어](troubleshooting.ko.md)

**After a normal break, [resume the next unexecuted block](#resume). After an error, preserve the current folder and error output, then choose below.**
- **Failed stage:** [offline tests](#offline-tests) · [sign-in](#login) · [retrieval](#retrieval) · [local run](#symptom-local) · [deployment](#deployment-recovery) · [hosted run](#symptom-hosted) · [calibration](#calibration) · [collection](#collection-retry) · [evaluation](#evaluation-retry) · [review record](#review-recovery) · [V2 changed](#v2-changed) · [cleanup](#cleanup-recovery).
- **Evidence or optional work:** [no baseline failures](#no-failures) · [traces](#telemetry) · [portal](#portal-differs) · [completion](#symptom-completion) · [Levels 2-3](#levels).
- **Not sure?** [common symptoms](#symptoms) · [saved-state resume](#resume) if a label or state file exists · [environment-owner resume](#setup-resume) if setup failed (environment owners only).
- Run participant recovery commands from the existing workshop folder's repository root; environment-owner recovery names its own folders.
- If the virtual environment already exists, restore it and `AZURE_CONFIG_DIR` with [README resume-shell](../README.md#resume-shell).

**First distinguish execution failure from low quality.**

| What you see | Next action |
|---|---|
| Exception, missing/duplicate response, or evaluator error | Stop the next step and [recover the failed command](#resume) |
| `collect` prints `business=False` | A business check failed, not the command. If collection finishes without errors, continue to that stage's evaluation. |
| Completed evaluation with low scores and no row errors | Record them without repeating the completed `evaluate`. Continue with the next unfinished action: `baseline` [5-4 report check](../README.md#baseline-report), `improved` [7-3 save comparison](../README.md#candidate-comparison), or `holdout` [8-2 save comparison and check frozen V2](../README.md#holdout-comparison). Skip blocks already completed. |
| Missing or incomplete traces | Check ingestion, access, and the [query window](#telemetry); do not claim complete evidence |
| Only a recording of a successful run | Treat it as observation, not your own completed execution |

In this guide, “instructor” and “environment owner” mean the instructor in a class and **you in self-study**. If that is you, perform the row's check yourself; if it does not resolve, stop and record the state and error. When you ask for help, share only the failed command, error, step, and result label. Never share passwords, tokens, the full `.env`, or personal-information screenshots.

<a id="resume"></a>

## Resume from where you stopped

**First check for active work.** If the original terminal or job is still running, wait; do not start a second command. If you lost the collection terminal, use the [local collector check](#collector-status).

**Long-pause limit:** `monitor` looks back at most **168 hours (7 days)**. If collection finished but you have not confirmed `complete: true` in `telemetry.json`, finish [trace verification](#telemetry) within that window. Preserve completed trace evidence; it does not need another query. This query limit is separate from Azure retention.

| How you stopped | What to do now |
|---|---|
| Closed the terminal during sign-in without an error | [Restore the terminal](../README.md#resume-shell), then run [only the ID-input block](../README.md#login-input) to restore `LOGIN_TENANT_ID` and `LOGIN_SUBSCRIPTION_ID`. Continue unfinished sign-in/verification without repeating successful sign-ins. For environment preparation, use [setup resume](#setup-resume). |
| Virtual environment exists; normal break with the last completed block noted | [Restore the terminal](../README.md#resume-shell) in the existing folder and start the **next block** in your notes. For example: 2-3 completed → start 3-1. Do not repeat completed deployment, collection, or evaluation. |
| Before creating the virtual environment (before 1-2) | Return to the existing folder in Bash and continue after the last completed block. Do not run `source .../activate` yet. If 1-1 is complete, continue [1-2](../README.md#python-setup). |
| An error occurred, or completion is uncertain | Use the failed-stage table and saved state below. File existence alone does not establish portal checks or human review. |

**For errors, repeat the failed command, not the whole block.** If `collect` finished but `evaluate` stopped, do not paste the block again from `collect`. Only recollection needs a new label; evaluation and trace recovery keep the existing label.

| Stopping point | Correct next action |
|---|---|
| `azd deploy` itself failed, or deployment success is uncertain | [Check deployment status](#deployment-recovery). Do not mistake a starting or older version for a successful new deployment. |
| Deployment succeeded; `grant-agent-access` or `smoke` failed afterward | Resolve the cause and repeat **only that failed command**. Do not redeploy and create another agent version. |
| Collection failed; manifest status is `failed` | Follow [collection recovery](#collection-retry), preserving the failed attempt |
| `Evaluation is still running` | Repeat only `evaluate` with the same label |
| Evaluation failed, or result validation/download stopped | Use the [saved-status decision table](#evaluation-retry). Not every local error permits `--retry-failed`. |
| `Telemetry is incomplete` | Check ingestion/access and the [two-hour query window](#telemetry); repeat only `monitor` for that label |
| `Hosted prompt does not match` (holdout collection), or 8-2 shows different improved and holdout versions | [If V2 changed after 7-2](#v2-changed); do not delete or edit results |
| `Label ... already exists` | Read the status files below. If collection is `completed`, find the next unfinished evaluation/trace step. If `failed`, recover collection. If `running`, use the [local collector check](#collector-status) and recover collection only after confirming it stopped. |
| A `feedback` record exists, or the wrong row was saved | [Check the review record](#review-recovery). Its row, reason, language, and trace must match an actual review. Adding another row does not exclude the mistaken one. |
| Cleanup or its verification stopped | Use [cleanup recovery](#cleanup-recovery); do not repeat successful deletion to fix a failed check. |
| A Level 2 or 3 command stopped | Use [Level 2–3 recovery](#levels); your step 5–9 results stay unchanged |

**When checking saved files:** the table below applies only to a label whose **5-2 collection has started**. Missing files are normal before collection. If creation/deployment completion is unclear and no output remains, confirm the state with the owner before rerunning. An empty terminal is not a reason for a new clone, `init`, or `bind`.

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

<a id="collector-status"></a>

## If you closed or lost the collection terminal

**Check your account's local `workshop.py collect` process, not the Azure agent.** A closed window or a manifest marked `running` does not establish whether it stopped. These commands only inspect processes; they do not terminate any.

**Terminal — macOS, Linux, or WSL: list your collectors:**

```bash
COLLECTOR_PROCESSES=$(ps -ww -u "$(id -u)" -o pid=,etime=,args=) &&
printf '%s\n' "$COLLECTOR_PROCESSES" |
  awk '/[w]orkshop[.]py[[:space:]]+collect/ { print; found = 1 } END { if (!found) print "No matching local collector." }'
```

**Checkpoint:** each row starts with a PID, then elapsed time and the command. `No matching local collector.` means this account has no matching collector. If rows appear, compare `--label` with your original command, then run **only your OS's block** below.

**If not:** preserve a lookup error and do not recollect. An error does not mean no collector exists.

**Terminal — macOS only: check that PID's working folder:**

```bash
read -r -p "Collector PID from the list: " COLLECTOR_PID &&
lsof -a -p "$COLLECTOR_PID" -d cwd -Fn
```

**Terminal — Linux or WSL only: check that PID's working folder:**

```bash
read -r -p "Collector PID from the list: " COLLECTOR_PID &&
readlink "/proc/$COLLECTOR_PID/cwd"
```

**Checkpoint:** compare the path on macOS's line starting with `n`, or the Linux/WSL output path, with your recorded workshop folder. **Wait if any collector in this folder remains**, even under another label. Leave processes in other folders untouched.

**If not:** the process may have ended during the lookup, so check the first list again. If missing tools or access errors prevent checking its folder, the state is uncertain. Preserve the error instead of terminating anything or recollecting.

**Next:** once no collector remains in this folder, inspect the [saved state](#resume). A `completed` collection continues at the next unfinished step; a failed collection, or `running` left after the process ended, uses [collection recovery](#collection-retry). Process termination does not establish collection success.

<a id="deployment-recovery"></a>

## If the deployment command itself failed

**Use this for a failed `azd deploy` in 4-1 or 7-2.** Note the step, last error, and agent name/version printed by the attempt. Wait if the original command is still running. If deployment succeeded and only `grant-agent-access` or `smoke` failed, [recover that command](#resume), not deployment.

**Terminal — query status only, in the same folder:**

```bash
azd ai agent show --output json
```

This command uses the name/version in `azure.yaml` and the current azd environment. **First match the returned version to the attempted deployment's target.** An `active` older V1 does not prove a new V2 deployment succeeded.

| Confirmed state | Next action |
|---|---|
| The target version is still starting | Wait and repeat only the status query. Do not overlap deployments. |
| The target version is confirmed `active` | For the first deployment, continue [4-2 access](../README.md#agent-access); for V2, continue [7-2's new-version check](../README.md#candidate-smoke). Do not skip the response check. |
| The target deployment failed or was never created, and the cause is resolved | Retry once at [4-1](../README.md#deploy-code), or only `azd deploy --no-prompt` from [7-2](../README.md#candidate-deploy) for V2. Do not repeat a successful `set-prompt`. |
| Only an older version appears, the query fails, or the target version is unknown | Have the owner reconcile the output and target version with **Agents → your agent → Playground → Log stream** in the portal. A visible version alone is not success or permission to redeploy. |

**Checkpoint:** the attempted target version and current state are confirmed, identifying one next action in the table.

**If not:** if the retry fails or state cannot be confirmed, stop and preserve the error. Follow [the early-stop path](../README.md#stop-early); reconcile created objects and ownership with the owner before cleanup.

<a id="symptoms"></a>

## Common symptoms

Use the matching row, then return to the failed checkpoint. If it persists, preserve the error and use the linked recovery section or the instructor.

**Setup and sign-in**

| Route | Symptom | Cause or check | Action / exact return |
|---|---|---|---|
| Setup | Missing `.env` or required setting | The workshop cannot infer private deployment names. | Add the complete file; return to [step 1-1 `.env` check](../README.md#workspace-settings). |
| Setup | Offline tests end with `FAIL` or `ERROR` | Distinguish Python, virtual-environment, and dependency errors from test failures. | Use [offline-test recovery](#offline-tests); do not start Azure operations before `OK`. |
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
| Deployment | `azd deploy` error or uncertain outcome | Distinguish the previous version from this attempt's target. | [Check deployment status](#deployment-recovery), then return only to the unfinished block. |
| Retrieval | `prepare-iq` cannot create a role assignment | The Search identity needs planner access. | Check [access](instructor.en.md#access), then rerun the failed [2-1 registration](../README.md#knowledge-registration). Do not skip to 2-2 retrieval yet. |
| Retrieval | `retrieve` finishes without documents or without `TRAVEL-2026` | Registration and retrieval are separate checks. | [Recover retrieval](#retrieval); return to [policy retrieval](../README.md#policy-retrieval). |
| <a id="symptom-hosted"></a>Hosted run | Search 403 / role assignment failure | Local user permissions and hosted agent instance permissions differ. | Check both identities; return to [hosted access](../README.md#agent-access). |
| Hosted run | Hosted 424 / cold start | The hosted version may not be ready. | After 1–2 minutes, repeat only `smoke` from [hosted smoke](../README.md#hosted-smoke). If it still fails, inspect the error in **your agent → Playground → Log stream**. Do not redeploy. |
| Collection | 429 or request timeout | Capacity or service throttling interrupted the run. | Preserve the attempt and inspect Retry-After; return to [collection recovery](#collection-retry). |
| Trace | `connections/read` on startup | Startup may be reading connection metadata directly. | Do not change code or roles; follow [startup-log checks and handoff](#hosted-telemetry). Once resolved, resume only the original step's `smoke`. |
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
| Setup/trace | No Application Insights connection or multiple connections | Existing resources do not establish a project connection. | The owner checks [existing-service settings](instructor.en.md#existing-service-checks), then returns to the original failed command. |
| Setup/evaluation/trace | Missing App Insights `ResourceId` metadata | The dedicated connection metadata may be incomplete. | Follow the original-command return table in [owner-only observability repair](instructor.en.md#observability-repair). Do not start trace/evaluation recovery after an initial preflight failure. |

</details>

<a id="offline-tests"></a>

## If the offline tests fail

**Resolve this before Azure sign-in or deployment.** Preserve the first `FAIL` or `ERROR` test name and traceback. Run the following in **the same folder** where the tests failed. For new-environment setup, that is `RUN_DIR/workshop`, not the original clone.

**Terminal — check the existing virtual environment and dependencies:**

```bash
source src/agent/.venv/bin/activate &&
python --version &&
python -c 'import sys; print(sys.executable); print(sys.prefix)' &&
python -m pip check
```

**Checkpoint:** Python is `3.13.x`, the executable and environment paths are under this folder's `src/agent/.venv`, and the last line is `No broken requirements found.` This check alone does not mean the tests passed.

**If not:** resolve only the matching cause below.

| Finding | Next action |
|---|---|
| Missing `activate` file | Return to your original install path: [participant 1-2](../README.md#python-setup), [new environment 1-6](environment.en.md#setup-python), or [existing-environment Python setup](instructor.en.md#existing-python). Create only a missing virtual environment; preserve the source and run records. |
| Wrong Python version or environment path | Check the current folder and [Python 3.13 installation](instructor.en.md#tools). Do not use another folder's Python or delete the existing environment as a workaround. |
| The original error is `ModuleNotFoundError`, or `pip check` reports conflicting dependencies | Use the pinned-dependency repair below only after the Python version and paths match. |
| Environment checks pass, but an assertion or other test failure remains | Give the test name, traceback, and Python version to the instructor. For self-study, remove secrets/personal information, check or report a [repository issue](https://github.com/junwoojeong100/foundry-evaluation/issues), and stop. Do not edit tests, policies, or fixed references to get `OK`. |

**Terminal — only for confirmed missing or conflicting dependencies:**

```bash
python -m pip install -r requirements.lock.txt &&
python -m pip check
```

**Checkpoint:** installation finishes without errors and prints `No broken requirements found.`.

**If not:** preserve the download/dependency error and stop. Do not switch to arbitrary versions or global installation.

**Terminal — rerun only the same tests after resolving the cause:**

```bash
python -m unittest discover -s tests -v
```

**Checkpoint:** the run ends with `OK`. The new-environment runtime copy may show `OK (skipped=1)` because it omits only the documentation checks.

**If not:** give the first failing name and error to the support contact; keep Azure operations on hold.

| Original test path | Continue after `OK` |
|---|---|
| Participant README 1-2 | [1-3 sign-in](../README.md#login) |
| New environment 1-6 | [2-1 sign-in](environment.en.md#setup-identity) |
| Existing-environment preparation | [1. settings and sign-in](instructor.en.md#existing-settings) |

<a id="login"></a>

## If sign-in fails or authentication expires

**First note the original failed command and stage, then restore only the ID inputs in the correct folder.** Do not switch `AZURE_CONFIG_DIR` to another clone.

| Path being recovered | Restore the CLI profile and ID inputs |
|---|---|
| Participant README or a workshop already in progress | In the existing workshop folder, run [only the README ID-input block](../README.md#login-input). |
| Existing-environment preparation | In the model-preparation folder, run [only its ID-input block](instructor.en.md#login-input). |
| New-environment steps 2–6 | First `cd "$RUN_DIR/workshop"`, then run [only the environment ID-input block](environment.en.md#login-input). If `REPO_ROOT` or `RUN_DIR` is lost, [restore the existing paths](#setup-resume) first. |

The new-environment CLI profile is **`$RUN_DIR/workshop/.azure-cli`**. Setting it to `$PWD/.azure-cli` in the original provisioning clone selects a different cache; enter the IDs from the runtime folder above.

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

<a id="login-return"></a>

**If you repaired only Azure CLI and have not signed in to azd yet, finish azd sign-in first.** If only azd failed and Azure CLI already succeeded, go straight to verification. Keep the same folder and do not repeat successful sign-ins.

Follow one row for **the path you were on before opening this page**. Run its verification block only after both sign-ins finish.

| Where you were signing in | If azd sign-in is still unattempted | Verify after both sign-ins | Continue afterward |
|---|---|---|---|
| Participant README 1-3 | [README block 3: azd](../README.md#azd-login) | [README sign-in check](../README.md#login-check) | README 1-4 project check |
| New environment 2-1 | [Environment azd sign-in](environment.en.md#azd-login) | [Environment sign-in check](environment.en.md#login-check) | That guide's 2-2 identity, preservation, and capacity check |
| Existing-environment preparation 1 | [Existing-environment azd sign-in](instructor.en.md#azd-login) | [Existing-environment sign-in check](instructor.en.md#login-check) | Choose candidate deployment names there → 2 auxiliary deployment |
| Authentication expired during the workshop or existing-environment preparation | Do not restart initial sign-in; recover only the expired CLI above | Only the sign-in check from the [README](../README.md#login-check) for the workshop, or [existing-environment guide](instructor.en.md#login-check) for preparation | Return to **recovery for the original failed command** in your notes. Do not repeat completed preflight, `bind`, or deployment. |
| Authentication expired during new-environment steps 2–6 | Recover only the expired CLI above | Only the [environment sign-in check](environment.en.md#login-check) block | For steps 2–5, `cd "$REPO_ROOT"`, keep `AZURE_CONFIG_DIR`, and resume the original failed command. For step 6, stay in `RUN_DIR/workshop`. |

**Until new-environment preparation finishes, do not continue to README `preflight` or `bind`.**

**Checkpoint:** the chosen verification block shows the Azure CLI and azd account, tenant, and subscription matching that folder's `.env`.

**If not:** preserve the exact sign-in error and ask for an approved login path; do not switch accounts or tenants.

<details>
<summary>Background references</summary>

[interactive Azure CLI sign-in](https://learn.microsoft.com/cli/azure/authenticate-azure-cli-interactively) · [CLI configuration directories](https://learn.microsoft.com/cli/azure/azure-cli-configuration#cli-configuration-file)

</details>

**Next:** follow only the table's **Continue afterward** column. After recovering an expired sign-in mid-workshop, do not restart the initial preparation below the verification block.

<a id="hosted-telemetry"></a>

## If startup logs show `connections/read`

**Participant:** stop at the original step. Find the error under **your agent → Playground → Log stream** and give the environment owner only the failed step, `LAB_AGENT_NAME`, available deployment version, and relevant error excerpt. Do not share connection strings, tokens, or the full `.env`; do not grant the agent Owner or edit source to get past the error.

**Environment owner:** open the deployed source and `azure.yaml` in your editor. The supplied `telemetry_connection` in `src/agent/main.py` does not query project connections when `APPLICATIONINSIGHTS_CONNECTION_STRING` or `OTEL_EXPORTER_OTLP_ENDPOINT` is injected. The supplied hosted service's `env` in `azure.yaml` does not pass `LAB_AUTH_MODE=cli`. If the deployed version differs or you cannot confirm runtime injection, send the error and version to the source maintainer or platform support. Do not copy connection strings or redeploy without identifying the cause.

**Checkpoint:** after resolving the cause, only the original step's `smoke` runs without a startup error and meets that step's language, instruction, and numeric-version requirements.

**If not:** preserve the error and current version and stop. If the repair redeployed after 7-2, use [V2-change recovery](#v2-changed) to restore comparable conditions.

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

<a id="calibration-return"></a>

**Next:** after `Judge calibration passed`, return to the path you came from. Calibration is already complete; do not run it again or switch preparation paths.

| Where calibration stopped | Next unexecuted step |
|---|---|
| Participant README 5-1 | [5-2 baseline collection](../README.md#baseline-collection) |
| New-environment preparation 6-2 | [6-3 handoff](environment.en.md#handoff) |
| Existing-environment preparation 3 | [Choose rehearsal or self-study](instructor.en.md#after-calibration) |

<a id="telemetry"></a>

## If traces are missing after a pause

`monitor` defaults to the **last two hours**, even if the portal displays Last Day. For a run from the last 24 hours, extend the window while keeping the **same label**:

**Terminal — extend the existing trace query window:** enter the actual label and hours covering the collection time (`24` for the last day, at most `168`).

```bash
read -r -p "Actual label whose traces need checking: " RESULT_LABEL &&
read -r -p "Lookback hours (1–168; 24 for the last day): " TRACE_HOURS &&
python scripts/workshop.py monitor --label "$RESULT_LABEL" --hours "$TRACE_HOURS"
```

Enter retry labels exactly as recorded. `--hours` accepts whole hours from **1 to 168**. This command cannot recover unverified traces outside that window or recreate expired/deleted telemetry.

**Checkpoint:** `telemetry.json` has `complete: true` and matching `expected_trace_count` / `observed_trace_count` for the same label.

**If not:** give the owner the label, collection time, query window, and telemetry error; do not recollect answers or edit `telemetry.json`.

<details>
<summary>Why this can still fail</summary>

The query still filters the exact agent and run, and missing, duplicate, foreign, or sampled traces still fail coverage checks. If the data is recent, allow ingestion to finish and repeat only this command. If it remains incomplete, inspect access, retention, and the connected App Insights resource with the environment owner. Never recollect answers or edit `telemetry.json` to manufacture completeness.

</details>

**If you came to check traces before pausing:** do not jump ahead to step 6 or 9. Note the checked label and return to the [early-stop instructions](../README.md#stop-early). Resume at the next unexecuted block in your original notes, using the saved files for traces already checked.

**Next — if recovering a trace error:** do not repeat the recovered command; continue below its trace checkpoint: [baseline traces](../README.md#baseline-traces), [candidate traces](../README.md#candidate-traces), or [holdout traces](../README.md#holdout-traces). If cleanup already ran, read saved evidence only. For a new experiment, use a fresh workspace and names.

<a id="collection-retry"></a>

## If response collection failed

Use this only when:

- The original collector has stopped: its terminal returned to a prompt, or the [local collector check](#collector-status) confirmed termination after you lost the window. If uncertain, do not start a second collection.
- You keep the failed label and original files.
- You retry the same stage once with one unused retry label.
- You do not change models, split, questions, prompt version, agent version, completed labels, reviewed source, or holdout meaning. Only [when V2 changed after 7-2](#v2-changed) do you collect with the current V2 version.
- If the retry fails, stop and keep the error.

| If this failed | Go to |
|---|---|
| Baseline before comparison | [Failed initial baseline](#collection-retry-baseline) |
| V2 dev after baseline | [V2 dev collection failed](#collection-retry-improved) |
| Holdout | [Holdout collection failed](#collection-retry-holdout) |

<a id="run-values"></a>

### Run values after recovery or in a new terminal

**After successful recollection, update these values in your existing notes before returning to the main guide.** Keep labels for stages you did not recover. For a stage not yet collected, note its default and change it only if it later needs recovery.

| Value to note | First-run default | Recovery value and where to use it |
|---|---|---|
| V1 dev label (`BASELINE_LABEL`) | `baseline` | After successful V1 recovery: `baseline-retry`. Use it in later `feedback`, `compare`, `summary`, `monitor`, and the value after `verify --baseline`. |
| V2 dev label (`CANDIDATE_LABEL`) | `improved` | After successful V2 recovery: `improved-retry`. Use it in later comparisons, reads, traces, and the value after `verify --candidate`. |
| V2 holdout label (`HOLDOUT_LABEL`) | `holdout` | After successful holdout recovery: `holdout-retry`. Use it in later comparisons, reads, traces, and the value after `verify --holdout`. |
| Collection `concurrency` (`COLLECTION_CONCURRENCY`) | `4` | Read the **completed V1 baseline's** `src/agent/.foundry/results/<actual label>/manifest.json`. Later V2 dev and holdout reuse it through this variable; `2` is equivalent to `--concurrency 2`. |

**Terminal — restore only in a new window or when variables differ from your notes:** enter the four actual values. Before V1 collection, use the noted initial concurrency `4`; after V1 completes, its manifest is authoritative. Do not change files or `.env`.

```bash
read -r -p "V1 dev label from your notes: " BASELINE_LABEL &&
read -r -p "V2 dev label from your notes: " CANDIDATE_LABEL &&
read -r -p "V2 holdout label from your notes: " HOLDOUT_LABEL &&
read -r -p "Collection concurrency (1, 2, 4): " COLLECTION_CONCURRENCY &&
printf 'V1 dev=%s\nV2 dev=%s\nV2 holdout=%s\nconcurrency=%s\n' \
  "$BASELINE_LABEL" "$CANDIDATE_LABEL" "$HOLDOUT_LABEL" "$COLLECTION_CONCURRENCY"
```

**Checkpoint:** no value is empty, and all four output lines match your notes and completed manifest. Recovery blocks update the relevant variables only after collection succeeds, so this input need not be repeated in the same terminal.

**If not:** repeat only this input. If unsure which label completed, inspect the [saved state](#resume) first; do not overwrite it with defaults.

**Do not edit the main commands.** Variables after `--label`, `--labels`, `--baseline`, `--candidate`, and `--holdout` supply the actual values. **Keep `--split dev` and `--split holdout` unchanged.** Copy `row_id` from the actual label's output and use that label in file paths. For example, the passing case when failures are `none` is your actual V1 label followed by `-sol-D01`. Do not rename or edit existing folders, files, row IDs, or manifests.

For example, after recovering **only V2 dev**, `CANDIDATE_LABEL=improved-retry` while the other two labels stay unchanged. Carry these notes into the [9-3 report](../README.md#finish).

**Next:** if you only restored variables or updated notes, return to the **next unexecuted block** in your original notes. Choose a failed stage above only if collection failed and still needs recovery. Opening a new terminal is not a reason to recollect.

<a id="collection-retry-baseline"></a>

### Failed initial baseline

**After resolving the cause, choose concurrency first.** Non-rate-limit errors can also be recovered; the same stopped-collector, preserved-evidence, and unused-label conditions apply.

| Resolved error | Concurrency for this retry |
|---|---|
| A 429 or timeout where reducing concurrency is the recovery | `2` |
| Another execution error | Keep `concurrency` from the failed `manifest.json`. Without a manifest, use the original command's value (`4` if omitted). |

**Terminal — recollect V1:** enter the concurrency chosen above. `2` is equivalent to `--concurrency 2`, and `4` to `--concurrency 4`; do not edit the command. V1's label and concurrency variables update only after collection succeeds.

```bash
read -r -p "Concurrency for this V1 retry (1, 2, 4): " RETRY_CONCURRENCY &&
python scripts/workshop.py collect --split dev --label baseline-retry --concurrency "$RETRY_CONCURRENCY" &&
BASELINE_LABEL=baseline-retry &&
COLLECTION_CONCURRENCY="$RETRY_CONCURRENCY"
```

**Checkpoint:** collection finishes at `18/18` without errors. Only **V1 collection** is complete; evaluation, portal, and trace checks still remain.

**If not:** do not create another label; preserve the error and original failure record.

**Next:** update your [run-value notes](#run-values) to `V1 dev=baseline-retry` and the **actual `concurrency` in the completed `baseline-retry/manifest.json`**, then resume [step 5-3's evaluation command](../README.md#baseline-evaluation). Use the same concurrency for later V2 dev and holdout collection (`--concurrency 2` if `2`). Read the example `baseline-sol-D01` as `baseline-retry-sol-D01`; do not repeat completed collection.

<a id="collection-retry-improved"></a>

### V2 dev collection failed

Also use this command to collect a new label when README 7-4 shows the review was not carried (`source trace carried: no`) or [V2 changed after 7-2](#v2-changed).

**Terminal — recollect V2 dev:** confirm `COLLECTION_CONCURRENCY` matches the completed V1's `manifest.json → concurrency`. The command reuses it and updates the V2 dev label only after success.

```bash
python scripts/workshop.py collect --split dev --label improved-retry --concurrency "$COLLECTION_CONCURRENCY" &&
CANDIDATE_LABEL=improved-retry
```

**Checkpoint:** collection finishes at `18/18` without errors.

**If not:** stop and preserve the error; keep the completed baseline and review unchanged.

**Next:** update the V2 dev label in your [run-value notes](#run-values) to `improved-retry`, then resume [step 7's evaluation and comparison](../README.md#candidate-evaluation). Keep using that value in later commands and paths.

<a id="collection-retry-holdout"></a>

### Holdout collection failed

**Terminal — recollect holdout:** confirm `COLLECTION_CONCURRENCY` matches the completed V1's `manifest.json → concurrency`. The command reuses it and updates the holdout label only after success.

```bash
python scripts/workshop.py collect --split holdout --label holdout-retry --concurrency "$COLLECTION_CONCURRENCY" &&
HOLDOUT_LABEL=holdout-retry
```

**Checkpoint:** collection finishes at `12/12` without errors.

**If not:** stop and preserve the error; keep the frozen instructions unchanged.

**Next:** update the V2 holdout label in your [run-value notes](#run-values) to `holdout-retry`, then resume [step 8's evaluation](../README.md#holdout-evaluation). Keep `--split holdout` unchanged.

<a id="evaluation-retry"></a>

## If only Foundry evaluation failed

First require complete response collection. Read **`src/agent/.foundry/results/<label>/evaluation.json`** if present, then choose one action:

| Saved state / failure | Next action |
|---|---|
| No Foundry evaluation run was created, polling timed out, or a result download was interrupted | Resolve the cause, then use **A**. It reuses a saved Foundry evaluation run; it creates one only if none is recorded. |
| `status: failed / canceled / cancelled`, or `run → result_counts → errored` greater than 0 | Resolve the cause, then use **B** to preserve the failed attempt and create a retry. |
| Job completed with no errored rows, but validation rejects missing/duplicate IDs, null scores, or invalid output | Stop and preserve `evaluation.json` and any `evaluation-output-raw.json`. Ask the owner to inspect the result contract. **Do not force B or edit status/scores.** |
| Job and rows completed correctly, but valid scores are low | Do not retry. Finish the report/portal checkpoint and continue the workshop. |

At the selected block's prompt, enter **the label that actually failed**, including retry labels such as `improved-retry`. Run only one block, after the original command stops. There may be no output for 1–3 minutes while scoring.

**Terminal — A. start or resume evaluation with the same inputs:**

```bash
read -r -p "Actual label whose evaluation needs resuming: " RESULT_LABEL &&
python scripts/workshop.py evaluate --label "$RESULT_LABEL"
```

**Checkpoint:** `Foundry evaluation completed: ... (18 rows)`, or `(12 rows)` for holdout, appears with a report URL. Skip B below.

**If not:** use the saved-state table above again. For a polling timeout, resume with A; use B only for a recorded failed/errored run.

**Terminal — B. retry only a recorded failed/errored run:**

```bash
read -r -p "Actual label with a failed evaluation to retry: " RESULT_LABEL &&
python scripts/workshop.py evaluate --label "$RESULT_LABEL" --retry-failed
```

Never repeat `collect` for an evaluation failure.

**Checkpoint:** `evaluation.json` shows `status: completed`, the expected total count, and no errored rows; `evaluation-results.json` has one valid row per response.

**If not:** preserve `evaluation.json` and any raw output, then use the saved-state table above; do not edit status, scores, or rerun collection.

**Next:** finish the interrupted checkpoint before continuing: [baseline evaluation](../README.md#baseline-evaluation), [candidate evaluation](../README.md#candidate-evaluation), or [holdout evaluation](../README.md#holdout-evaluation).

<a id="no-failures"></a>

## If all baseline business checks pass

That is a legitimate result. Do not fabricate a failure or alter an answer/reference.

1. Enter the actual V1 label's `-sol-D01` row shown in [README 6-2's](../README.md#review-case) `show` prompt, or another row from that label. Inspect its saved response and fixed reference, and note its `row_id` and `trace_id`.
2. As in 6-2, compare the response with its fixed dev reference, then check its trace in the portal.
3. Write one line explaining that all business checks passed, what you inspected, and **behavior the provided V2 should preserve**. Do not claim a failure or improvement in advance.
4. Return to [6-3 to save the review](../README.md#save-review). `feedback` accepts passing dev responses too. Then review V2's suitability in step 7.

Final verification only checks that candidate results store the saved baseline trace ID; it does not reuse the baseline trace as candidate trace evidence. Do not search the holdout for a failure to use during development.

**Checkpoint:** the saved review names one baseline `row_id`, its `trace_id`, what you inspected, and the behavior V2 should preserve.

**If not:** return to the selected baseline response and fixed dev reference; do not use holdout or invent a failure.

**Next:** continue with [V2 deployment and candidate evaluation](../README.md#lab-e).

<a id="review-recovery"></a>

## If a review already exists or was saved incorrectly

**Check this before V2 collection.** The next dev collection reads every `src/agent/.foundry/datasets/regression-*.jsonl`. Saving the correct row as well, or selecting a different row to report, does not exclude a mistaken record.

1. **Editor:** read `source_row_id`, `source_trace_id`, `review_reason`, and `language` in the existing file's `lineage`. Actually compare that row's saved response, fixed reference, and trace using [6-2](../README.md#review-case).
2. Keep a record that already matches an actual review. If you accidentally saved a different row but have now reviewed it too and its saved reason matches the evidence, note **the original mistake and the later additional review** in your existing notes.
3. If the reason, provenance, or reference is wrong, or V2 was already collected with an incorrect record, stop. Preserve the files/error and give the row ID, trace ID, and mistake description to the instructor or repository maintainer. Deleting, editing, or adding a record alone does not complete recovery.

**Checkpoint:** every remaining review record matches a row and evidence you actually reviewed; any original mistake is documented in your notes.

**If not:** do not begin V2 collection. Do not report an unverified review as valid or alter original evidence.

**Next:** complete only [6-3's saved-record check](../README.md#read-review), then continue to step 7. Do not repeat `feedback` for an existing row.

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

**Checkpoint:** `prompt_version: v2`, and `agent_version` equals the **V2 version** you noted in 7-2. Do not repeat A unless something changes afterward. If holdout collection never started, go to [8-1's collection block](../README.md#holdout-collection). If `holdout/manifest.json` already exists, preserve it and use [holdout recollection](#collection-retry-holdout).

**If not:** if the version differs or `Hosted prompt does not match` persists after restoring the original instructions and settings, the conditions no longer match the original V2. Follow **B**.

**B — start again from dev with the current V2 version:**

1. **Terminal:** check the current version with A's **command block** (reuse its output if you just ran it). For `Hosted prompt does not match`, run `azd deploy --no-prompt` **once**, then repeat A's command block. Once it shows `prompt_version: v2`, note the new `agent_version`.
2. Collect `improved-retry` with [V2 dev collection recovery](#collection-retry-improved). Complete README 7-3's evaluation/comparison and 7-4's summary with that label.
3. Use the new version as your noted V2 reference. If nothing changed afterward, go to [8-1's collection block](../README.md#holdout-collection). If `holdout/manifest.json` already exists, use `holdout-retry` from [holdout recollection](#collection-retry-holdout). Use the changed labels in subsequent commands, file paths, and `verify`.

If you already saw the holdout, record `holdout reused during V2-change recovery` in your report. Do not tune instructions using those results or describe this as fresh, untouched validation.

**Checkpoint:** in 8-2's check, the new improved label and the holdout label have the same `agent_version` and `prompt_hash`.

**If not:** stop and record the error and label names. Do not delete earlier results or redeploy repeatedly to match versions.

**Next:** return to the unfinished [8-1 collection](../README.md#holdout-collection) or [8-2's check](../README.md#holdout-comparison). Do not repeat completed collection or evaluation.

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

**Next:** return to the next unexecuted block of the interrupted portal check. If you came from [8-4's holdout report](../README.md#holdout-report), confirm its checkpoint and continue to [9-1's complete evidence check](../README.md#lab-g). Do not repeat the completed 8-3 readout.

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
| `Rubric generation ended as ...` or `The run ended as ...` | Resolve the cause and check [state-file recovery eligibility](#level-state-recovery). For rubric/stress/red-team runs with saved `status` of `failed`, `canceled`, or `cancelled`, an `Inspect <file>` message also permits archiving before one retry. |
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
| `No scheduled run yet` | If the schedule is still active, run `continuous-eval` after the printed first-run time. For an expired schedule, use [resume after expiry](level-3.en.md#continuous-expired). |
| `ends` in `continuous.json` is earlier than the current UTC time | Use [resume after expiry](level-3.en.md#continuous-expired) to check for an active run or valid completed result. With neither, record section 6 as incomplete and section 7's blocking result; do not create a new schedule. |
| Continuous evaluation is `queued`/`in_progress`, or `failed`/zero traces | For waiting states, check again in one minute with the same command. For failure or zero traces, record incomplete execution and check traffic/access with the instructor. Creating a schedule is not completion. |
| Continuous evaluation is `completed` but has evaluator errors or empty results | The [row-level checkpoint](level-3.en.md#continuous-eval) has not passed. Record incomplete execution and inspect the cause; distinguish this from valid `passed: false` results. |
| The `red-team` scan is hard to find in the portal | In New Foundry, open **Evaluations → Red team** and select `<LAB_PREFIX>-red-team-sol`. Read the rates under **Overall metric results**; the list's **Issues in last run** column is not the number of successful attacks. |

</details>

**Checkpoint:** the Level 2-3 command either resumes to completion or records the exact failed saved state under `suite/` or `level3/`.

**If not:** stop repeating the command and share the saved state and raw error with the instructor.

**Next:** return to the interrupted Level 2 or Level 3 checkpoint, or continue to [step 10 cleanup](../README.md#cleanup) after optional work is complete.



<a id="level-state-recovery"></a>

### Level 3: archive failed state before one retry

**Not for waiting, low scores, or changing labels/counts.** Confirm the original command exited, resolve the execution error, and review retry costs. Use this only in either case:

- The error explicitly names a state file to delete.
- A rubric-comparison, stress, or red-team error says `The run ended as failed/canceled/cancelled ... Inspect <file>`, and that file's `run_id` and `status` identify the same terminal failure. Check in your editor without editing the state.

Archive the file instead of deleting evidence. The word `Inspect` alone, or an uncertain state, does not authorize archiving or retrying.

**Terminal — existing workshop root:** confirm the original command exited. Paste the **file path from the error**, without the words `Delete` / `and re-run` or surrounding quotes. Both the printed absolute path and a `src/agent/...` relative path work. The block accepts only rubric, stress, red-team, or trace state files in **this folder's** `level3/`; it does not accept agent or continuous-evaluation state, raw output, or another workshop's files.

```bash
read -r -p "State file named in the error: " STATE_FILE &&
python - "$STATE_FILE" <<'PY'
from pathlib import Path
import re
import shutil
import sys
import tempfile

root = Path("src/agent/.foundry/results/level3").resolve()
entered = Path(sys.argv[1])
state = entered.resolve()
allowed = r"(rubric-compare|(?:stress|red-team)-(?:sol|luna|astra)|traces-[a-z][a-z0-9-]{0,39})\.json"
if (entered.is_symlink() or state.parent != root or not state.is_file()
        or not re.fullmatch(allowed, state.name) or state.name.endswith("-output.json")):
    raise SystemExit("Stop: not an eligible state file in this workshop's level3 folder.")
raw = state.with_name(state.stem + "-output.json")
if raw.is_symlink() or (raw.exists() and not raw.is_file()):
    raise SystemExit("Stop: unexpected raw-output path; state was not moved.")
archive = Path(tempfile.mkdtemp(prefix="failed-attempt-", dir=root))
if raw.is_file():
    shutil.copy2(raw, archive / raw.name)
state.rename(archive / state.name)
print("Archived failed state:", archive / state.name)
PY
```

**Checkpoint:** `Archived failed state:` prints the new path. In your editor, open it and confirm that the failed run/job IDs are preserved. Its sibling raw output was copied too, if present. Only the original state file moved; ownership and step 5–9 evidence remain unchanged. Each archive stays inside this workshop and has a unique name, so it cannot overwrite another attempt or language's backup.

**If not:** for `Stop:`, check the path against the exact error and your workshop folder. For a copy/move error, inspect the printed error and existing files with the owner. Do not delete files or proceed until the failed state is safely archived.

**Next:** retry once with the same command and arguments; new calls may cost money. On success, return to that Level 3 checkpoint and continue with its next section. If the error repeats or you stop the optional work, keep the archive, record the incomplete section, and go to [step 10 cleanup](../README.md#cleanup). Existing ownership records remain available; do not repeat cleanup that already succeeded.

<a id="cleanup-recovery"></a>

## If cleanup or its verification stopped

Keep the same workspace, account, and names, and confirm the original cleanup process has stopped. Plans/results are in `src/agent/.foundry/results/`; ownership is in `src/agent/.foundry/local-state.json`. Do not edit these files.

| What finished | Next action |
|---|---|
| `cleanup --confirm` succeeded; `cleanup.json` records `completed: true`, but `check-cleanup` failed | Use **A: retry verification only**. Never repeat successful deletion. |
| Deletion partly succeeded, then failed, and the owner can reconcile every original target and remaining ownership record with Azure | Use **B: reconciled, approved remaining deletion**. Archive the original plan before retrying. |
| Ownership, targets, shared dependencies, or deletion outcomes are uncertain | Stop automated deletion. Give the owner the error, plan, and ownership record. Do not edit records or run B to manufacture a completion file. |

**A — deletion succeeded; only verification failed:** preserve the completion file and its `plan`, resolve access/propagation errors, then run only this check.

```bash
python scripts/workshop.py check-cleanup
```

Require the [step 10-3 checkpoint](../README.md#cleanup-check). If an object still exists or a preserved service is missing, report it; do not claim completion. Repeating `cleanup --confirm` would replace the recorded plan with the remaining ownership set, not verify the original deletion. Do not use B to bypass this check.

<a id="partial-cleanup"></a>

**B — owner-reconciled and approved continuation of partial deletion**

1. **Editor:** create an unused archive folder under `results/` and copy the original `cleanup-plan.json`, `local-state.json` from its location above, and any `cleanup.json`/`cleanup-check.json` into it. Record the error and archive path. Do not move/edit active files or overwrite an earlier archive.
2. **Environment owner:** record whether each original target is already absent or still present in Azure. The remaining ownership record must agree. Stop if a deleted target remains recorded as owned, a shared Search/planner role or another owner is involved, or an outcome is uncertain. Do not edit records to force agreement.
3. **Terminal — inspect only the remaining plan:**

```bash
python scripts/workshop.py cleanup --dry-run
```

**Checkpoint:** only still-present, exclusively owned targets from the archived original plan remain. No new target or shared dependency is listed, and the owner approved this remaining plan. An empty list alone does not prove the original targets were deleted.

**If not:** stop further deletion and give the owner the discrepancy.

**Terminal — only after that reconciliation and separate approval:**

```bash
python scripts/workshop.py cleanup --confirm
```

**Checkpoint:** it ends with `Owned workshop resources removed; shared infrastructure and evidence preserved.`

**If not:** preserve both attempts and stop. Do not loop automatically.

**Terminal — after the remaining deletion succeeds:**

```bash
python scripts/workshop.py check-cleanup
```

**Checkpoint:** [10-3's values](../README.md#cleanup-check) match the **resumed plan**, and the owner also confirmed the earlier attempt's deleted targets are absent. The latest check covers only its latest plan; do not report smaller counts as verification of the entire original plan. Keep both attempts' evidence with the report.

**If not:** give the owner the check result and original plan; do not delete more.

**Next:** after A or B is verified, workshop cleanup is complete. To retire an exclusive environment, follow the [creation-record and deletion-scope checks](environment.en.md#final-cleanup). After separately approved whole-group deletion, use [final foundation verification](environment.en.md#final-cleanup-check), not `check-cleanup`. Never delete a shared group as a shortcut.

<a id="existing-setup-resume"></a>

## Environment owners: resume preparation with existing services

**Return to the model-preparation clone from [existing-environment preparation](instructor.en.md#existing-foundation).** This path does not require `RUN_DIR` or `config.json`. If you have not created its virtual environment, continue the next unfinished [Python setup](instructor.en.md#existing-python) command in that clone.

**Terminal — if the virtual environment already exists, restore it in Bash:**

```bash
read -r -p "Absolute path of the existing model-preparation clone: " PREP_DIR &&
cd "$PREP_DIR" &&
source src/agent/.venv/bin/activate &&
export AZURE_CONFIG_DIR="$PWD/.azure-cli" &&
pwd
```

**Checkpoint:** the path is the original model-preparation clone and the virtual environment is active. Keep `.env`, names, sign-in caches, and ownership records unchanged.

**If not:** check the recorded path and failed command. Do not create another clone, run `init`, or provision a new foundation.

| Unfinished task | Where to resume |
|---|---|
| Python installation or tests | The existing-environment path in [offline test recovery](#offline-tests) |
| Settings or sign-in | [Settings](instructor.en.md#existing-settings), or [ID input](instructor.en.md#login-input) to restore both IDs, then only unfinished sign-in/verification |
| Auxiliary deployment | The unfinished [auxiliary-deployment](instructor.en.md#auxiliary-model) task |
| Candidate checks or preparation | The failed [candidate-preparation](instructor.en.md#check-candidates) command and later unexecuted commands |
| Calibration | [Check the judge](instructor.en.md#candidate-calibration); do not repeat completed candidate preparation |
| Preparation complete | Choose [rehearsal or self-study](instructor.en.md#after-calibration) |

**Next:** go to the selected destination. Do not run the new-environment procedure below.

<a id="setup-resume"></a>
<a id="environment-owners-resume-setup-after-closing-the-terminal"></a>

## Environment owners: resume incomplete setup

**First choose your original preparation path.** Participants who were not preparing Azure return to [workshop resume](#resume).

| Preparation path | Where to resume |
|---|---|
| Used existing Foundry, Search, and observability services | [Resume existing-service preparation](#existing-setup-resume); no `RUN_DIR` is required |
| Chose `RUN_DIR` with the new dedicated-environment tools | Continue below with that same `RUN_DIR` |

**The following applies only to new dedicated-environment preparation.** Keep the original clone and `RUN_DIR`; do **not** make a new `RUN_ID`, repeat an already completed `init`, or overwrite a snapshot.

**Terminal — check the existing paths:** start `bash`, then paste the original clone path and existing `RUN_DIR` without quotes:

```bash
read -r -p "Absolute path of the original setup clone: " REPO_ROOT &&
cd "$REPO_ROOT" &&
read -r -p "Existing absolute RUN_DIR path: " RUN_DIR &&
printf 'RUN_DIR=%s\n' "$RUN_DIR"
```

**Checkpoint:** the terminal is in the original clone and the printed path matches your recorded `RUN_DIR`. Use your editor to choose the matching file state below. If `config.json` exists, first check that `workspace` points to `workshop` under this `RUN_DIR`.

**If not:** recheck both recorded paths. If a path is uncertain or belongs to another run, do not create or overwrite records.

| Existing files / completed work | Next action |
|---|---|
| `init` failed input validation and `RUN_DIR` itself does not exist | [Correct the initial settings and retry only the same `init`](#setup-init-retry). Do not generate another run ID. |
| `RUN_DIR` exists but `config.json` does not | Partial creation: preserve the folder/error for the preparation owner. This is not eligible for an `init` retry. |
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
| Sign-in | In the runtime folder, rerun [only the environment ID-input block](environment.en.md#login-input) to restore `LOGIN_TENANT_ID` and `LOGIN_SUBSCRIPTION_ID`, then continue unfinished sign-in/verification. Do not repeat successful sign-ins. |
| Provisioning in environment steps 2–5 | Run `cd "$REPO_ROOT"`, keep `AZURE_CONFIG_DIR`, [select the interrupted stage](environment.en.md#setup-route), and run its failed command and remaining unexecuted commands with the same `--run-dir "$RUN_DIR"`. |
| Candidate preparation in environment step 6 | Stay in `"$RUN_DIR/workshop"` and resume the failed [step 6](environment.en.md#setup-candidates) command. |
| Candidates ready; only calibration unfinished | Resume at [judge calibration](environment.en.md#setup-calibration) in the same workspace; do not repeat `prepare-models` |
| Environment already completed | Choose the [handoff](environment.en.md#handoff); do not repeat preparation. |

If login expired, follow the new-environment row in [sign-in recovery](#login). Keep the runtime folder's CLI profile; do not bypass errors with another account, new names, or deleted ownership records.

**Checkpoint:** the original workspace, `RUN_DIR`, virtual environment, and `AZURE_CONFIG_DIR` are restored, and only the interrupted environment step is selected.

**If not:** preserve `config.json`, `RUN_DIR`, and the last error. In self-study you are the environment owner: check that `subscription` and `run_id` in `config.json` match this run, then resume only with the same `RUN_DIR`. Do not generate a new `RUN_ID` or overwrite the snapshot.

**Next:** return to the matching environment step above, or to [README bind](../README.md#bind-project) after handoff is complete.

<a id="setup-init-retry"></a>

## If `init` failed before creating records

**Use this branch only when initial input validation failed and the recorded `RUN_DIR` itself does not exist.** First [restore the existing paths](#setup-resume) into `REPO_ROOT` and `RUN_DIR`. Correct and save the [five initial settings](environment.en.md#initial-settings) in the original clone's `.env`. Do not repeat the full block that generates a new timestamped `RUN_ID`.

**Terminal — original clone (`$REPO_ROOT`), same `RUN_DIR`:**

```bash
if [ -e "$RUN_DIR" ] || [ -L "$RUN_DIR" ]; then
  printf '%s\n' 'Stop: RUN_DIR already exists; preserve it and use saved-state recovery.' >&2
  false
else
  source src/agent/.venv/bin/activate &&
  python scripts/prepare_environment.py init --run-dir "$RUN_DIR" --language en
fi
```

**Checkpoint:** the output JSON shows `language: en` and the same `RUN_DIR` now contains `config.json`. Continue to [1-5 source copy](environment.en.md#setup-snapshot).

**If not:** preserve the error and path. If the folder already exists, use the [saved-state table](#setup-resume); do not manufacture missing files or delete the folder.
