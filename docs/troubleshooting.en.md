# If a step fails: stop, identify the cause, and resume safely

[Return to the English guide](../README.md)

Distinguish **execution failure** from **low quality**. An exception, missing/duplicate response, evaluator error, or absent trace is not success. A completed evaluation with low valid scores is evidence for the review step.

Share the failed command, error message, current step, and result label with the instructor. Do not share passwords, tokens, the full `.env`, or screenshots containing personal information.

<a id="resume"></a>

## Resume the failed command, not the whole block

If `collect` finished but `evaluate` stopped, do not paste the block again from `collect`.

| Stopping point | Correct next action |
|---|---|
| Collection failed; manifest status is `failed` | Follow [collection recovery](#collection-retry), preserving the failed attempt |
| `Evaluation is still running` | Repeat only `evaluate` with the same label |
| Evaluation is failed/canceled or has error rows | Resolve the cause, then follow [evaluation recovery](#evaluation-retry) with `--retry-failed` |
| `Telemetry is incomplete` | Repeat only `monitor` with the same label after checking ingestion/filter/access |
| `Label ... already exists` | Read the manifest. For `completed`, continue with evaluation; for `failed`, recover collection. If `running`, establish whether the original process is still active before starting anything else. |
| Reviewed regression already exists | Verify its row, reason, language, and source trace. Continue only if they match the intended review; do not overwrite it. |

In a new terminal, start Bash, return to the correct workspace, activate its virtual environment, and set `AZURE_CONFIG_DIR` to that workspace's `.azure-cli`.

For a new experiment or another language, obtain unused names and use a separate folder. Deleting previous ownership or results is not a valid recovery strategy.

## Common symptoms

| Symptom | What to inspect |
|---|---|
| Missing `.env` or required setting | Put the instructor's complete file in the repository root; do not guess another team's deployment names |
| `read: -p: no coprocess` or activation path missing | Start Bash and use Terminal A's absolute `pwd` path |
| Language mismatch | Use the original language/workspace. `LAB_LANGUAGE=en` selects English; a missing setting preserves legacy Korean behavior. Never mix the two sets of results. |
| Nonempty `missing_models` | Ask the instructor to confirm all four exact deployments, versions, access, and quota; no substitutes |
| Wrong account or tenant | Repeat [the two sign-ins and checks](../README.md#login); do not change a global default subscription |
| Login appears missing only in a new terminal | Restore `export AZURE_CONFIG_DIR="$PWD/.azure-cli"` in the correct folder |
| `bind` or `set-prompt` environment error | Confirm that `bind` ran in this folder and targets the expected project/language |
| Port 8088 unavailable | Check Terminal A and its readiness log; do not terminate an unrelated process |
| Model 404 | Distinguish the model catalog ID from the actual Azure deployment name |
| 429 or request timeout | Preserve the attempt; inspect capacity and Retry-After. If concurrency changes, use the same value for all compared cohorts. |
| Search 403 / role assignment failure | Check the user and agent instance identities separately; local success does not establish hosted permissions |
| IQ 400 | Inspect the pinned API/schema and planner deployment; a normal Search result is not an IQ replacement |
| Hosted 424 / cold start | Inspect the actual deployed version and session logs; retry that version only when ready |
| `connections/read` on startup | Use injected telemetry configuration rather than broadening access indiscriminately |
| Completed job with errors or null scores | Inspect every output row; do not turn errors into zero scores or passes |
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

Open the address shown by each command and enter the code from **your own terminal**. Sign in with the configured account, then return to the README's two-account verification block.

Never share or record one-time codes. If organizational policy blocks device-code authentication, use an approved environment rather than bypassing the policy.

References: [interactive Azure CLI sign-in](https://learn.microsoft.com/cli/azure/authenticate-azure-cli-interactively) and [CLI configuration directories](https://learn.microsoft.com/cli/azure/azure-cli-configuration#cli-configuration-file).

<a id="collection-retry"></a>

## If response collection failed

Keep the failed label's `failure.json`, manifest, and raw responses. Do not score only successful rows or overwrite that label.

After addressing the cause, collect the complete matrix under a new label. For a failed **initial baseline**, for example:

```bash
python scripts/workshop.py collect --split dev --label baseline-retry --concurrency 2 &&
python scripts/workshop.py evaluate --label baseline-retry &&
python scripts/workshop.py compare --labels baseline-retry &&
python scripts/workshop.py monitor --label baseline-retry
```

Use **`baseline-retry` consistently** for later feedback, comparison, and `verify --baseline`. Use concurrency 2 for candidate and holdout too; changing only one cohort invalidates the comparison.

If the baseline and its review already completed, recover the failed later stage rather than creating a different baseline. A new experiment requires a new controlled scope, not deleted history.

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

1. Select an uncertain **English dev** row from `baseline/responses.jsonl`.
2. Inspect its own trace, evidence, and answer.
3. Explain that the baseline passed and what aspect warranted review.
4. Decide whether comparing the provided V2 is justified; do not claim improvement in advance.
5. Use the real row ID and review reason with `feedback`.

The final verification requires reviewed baseline provenance to be consumed by the candidate. Do not search the holdout for a failure to use during development.

## If the portal differs from a screenshot

Use your actual account, project, names, version, and time window. Tab changes can reset the selected agent version; also inspect `prompt_version` in the response.

Project-wide **Evaluations** and an agent's **Evaluation** tab are different lists. Foundry **Indexes** may not mirror the actual Search index. **Monitor → Tools** may be empty while code-level IQ spans appear in a trace.

Version comparison is under the **Version dropdown → Compare versions**, not the agent's **More** menu. Select two different versions. One **Send** submits to both panes; sending again creates additional calls.

Search an older trace by its real ID after expanding the time range. Do not substitute another agent's trace, a Korean run, or a screenshot for English execution evidence. Treat separate subscription alert/policy errors separately and never change shared settings merely to match a screenshot.
