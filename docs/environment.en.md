# Create a new English Azure environment — instructor or self-study

[English workshop](../README.md) · [한국어](environment.ko.md)

**Outcome:** a new, paid English workshop environment in **Sweden Central**, with Foundry, Search, telemetry, three candidates, a planner/judge, and a ready-to-use `.env`. This setup is preparation work outside the 120-minute participant workshop.

**Use this page only when you need new foundation services (Foundry account/project, Search, telemetry, and model deployments).** If you already received a complete `.env`, skip this page and start at [README step 1](../README.md#start). If services exist but preparation is incomplete, use [existing-environment preparation](instructor.en.md#existing-foundation). Do not run both paths.

**Self-study:** “instructor” and “environment owner” mean you. Follow the prerequisites below → steps 1–6 here → README 1-4 `bind`. Do not run the instructor rehearsal or team handoff.

**Check two prerequisites.** Do not repeat checks you already finished.

1. Finish [tool installation and checks](instructor.en.md#tools): Git, Python 3.13, Azure CLI, azd and its extension, Bash/WSL, curl, an editor, and a browser.
2. Check [access](instructor.en.md#access). Use an active subscription Owner role, or have an approved access administrator support the required resource creation and scoped role assignments.

**Then return to [step 1 on this page](#setup-workspace).** Use one Bash/WSL terminal and run one block at a time. Do not continue through the rest of the instructor guide.

<a id="setup-route"></a>

**Route:** [1. Workspace](#setup-workspace) → [2. Identity/capacity](#setup-identity) → [3. Services](#setup-foundation) → [4. Access/connections](#setup-access) → [5. Auxiliary model](#setup-auxiliary) → [6. Candidates/calibration](#setup-candidates) → [handoff](#handoff).

**Waiting or stopping:** `search: actual provisioning state ...; waiting` every 10 seconds is normal (up to 15 minutes per resource, 30 for Search). Created services keep costing money even if you stop. Check the [budget](instructor.en.md#budget); when you no longer need your dedicated group, verify its creation records and use [final cleanup](#final-cleanup). Even after a completed workshop, README step 10 alone does not stop foundation costs.

> New services incur costs. Use synthetic data only.
>
> Preserve shared and Korean-workshop resources. Do not change another workflow's default Azure CLI subscription. The resource group is created in Sweden Central, but GlobalStandard model requests may be processed in other regions.

<details>
<summary>Optional: delegate this setup to Copilot CLI</summary>

Start with [the Copilot CLI installation and startup guide](copilot.en.md). If that page sent you here only for initial settings, stop after filling the table in step 1 and return to [plan review](copilot.en.md#plan-review). Do not run setup in both places.

</details>

<a id="setup-workspace"></a>

## 1. Create an isolated English source workspace

Use a **Git clone**, not an extracted ZIP: the preparation tool records the actual source commit and file hashes.

**You type commands only in `REPO_ROOT` and `RUN_DIR/workshop`; `RUN_DIR` is only a record path:**

| Path | Purpose | Where commands run |
|---|---|---|
| `REPO_ROOT` | Original clone, guides, and preparation tools; its `.env` holds only initial settings | Initial setup and provisioning in steps 2–5 |
| `RUN_DIR` | This run's configuration and creation records | Pass as `--run-dir` only; **do not run commands here** |
| `RUN_DIR/workshop` | Isolated source and a **separate `.env` filled by the tools** | Python tests, sign-in, step 6, and the participant exercise |

### 1-1. Create or enter the clone

If you already have an **unused Git clone**, start Bash and enter its root. Run only `ls README.md && pwd` instead of the clone block below.

**Terminal — start Bash:** use Bash, not macOS's default zsh or PowerShell. On Windows, open a WSL terminal.

```bash
bash
```

**Checkpoint:** a new input prompt appears. Keep using this terminal.

**If not:** check [Bash/WSL installation](instructor.en.md#tools).

**Terminal — parent folder for a new clone:**

```bash
git clone https://github.com/junwoojeong100/foundry-evaluation.git foundry-evaluation-setup-en &&
cd foundry-evaluation-setup-en &&
ls README.md &&
pwd
```

**Checkpoint:** `README.md` and the current clone's absolute path are printed.

**If not:** for `already exists`, replace both folder names in the block with the same unused name. Do not run setup from a ZIP or an old workshop folder.

<a id="initial-settings"></a>

### 1-2. Fill the initial `.env`

**Editor — current clone root (later saved as `$REPO_ROOT`):**

1. Open this clone with VS Code **File → Open Folder**. In the Explorer, copy and paste `.env.example` in the same location, then rename the copy to `.env`.
2. Fill only the five rows below and save with **Ctrl+S (macOS: Cmd+S)**. Leave every other template value unchanged.

- Do not create `.env.txt` or overwrite an existing `.env`.
- Never add passwords, API keys, or tokens.
- Subscription ID: [Azure Portal](https://portal.azure.com/) **Subscriptions → your subscription → Overview**; tenant ID: **Microsoft Entra ID → Overview**. Portal sign-in does not sign in `az` or `azd`.

| Initial field | Value |
|---|---|
| `AZURE_SUBSCRIPTION_ID` | Authorized workshop subscription; in self-study, a subscription where you are Owner |
| `AZURE_TENANT_ID` | Its tenant |
| `AZURE_EXPECTED_USERNAME` | Sign-in name/email of the account you will use, not its display name |
| `AZURE_RESOURCE_GROUP` | On a first run, leave it empty: **`AZURE_RESOURCE_GROUP=`**. Use a group name only to confirm a previous run's group as preserved |
| `LAB_LANGUAGE` | `en` |

**Fill only those five fields now.** Leave other `<...>` placeholders and example deployment names unchanged. The tools generate service names, endpoints, and deployment names in a separate `.env` in the isolated folder. This initial file is not the **complete `.env`** given to class participants.

**Checkpoint:** `.env` is saved in the current clone root; `AZURE_SUBSCRIPTION_ID`, `AZURE_TENANT_ID`, `AZURE_EXPECTED_USERNAME`, and `LAB_LANGUAGE=en` are filled, and `AZURE_RESOURCE_GROUP` is a previous group name or intentionally left as `AZURE_RESOURCE_GROUP=`.

**If not:** correct any wrong value or remaining `<...>` placeholder in those five fields (`AZURE_RESOURCE_GROUP=` may intentionally be empty). Do not guess the other fields or add secrets.

### 1-3. Install the setup tools

**Terminal — current clone root (saved as `$REPO_ROOT` below):**

```bash
python3.13 -m venv src/agent/.venv &&
source src/agent/.venv/bin/activate &&
python -m pip install -r requirements.lock.txt
```

**Checkpoint:** `pip` ends without errors.

**If not:** fix the Python or package error before creating `RUN_DIR`; do not continue with a partial virtual environment.

### 1-4. Create the run folder

This block generates a fresh run ID from the current time. Run it once and keep the printed path for every later block.

**Terminal — current clone root (saved as `$REPO_ROOT` here):**

```bash
REPO_ROOT="$(pwd)" &&
RUN_ID="en-$(date -u +%Y%m%d-%H%M%S)" &&
RUN_DIR="$REPO_ROOT/.workshop/$RUN_ID" &&
printf 'REPO_ROOT=%s\nRUN_DIR=%s\n' "$REPO_ROOT" "$RUN_DIR" &&
python scripts/prepare_environment.py init --run-dir "$RUN_DIR" --language en
```

Copy the printed `REPO_ROOT=` and `RUN_DIR=` lines into your notes now; you resume with these two paths after reopening a terminal.

**Checkpoint:** the output JSON shows `language: en` and **`$RUN_DIR/config.json`** is created. Find it in the VS Code Explorer under **`.workshop → this run's ID → config.json`**. It records the chosen names; it has not copied the source or created Azure resources.

**If not:** keep the output and the same `RUN_DIR`, then use [setup recovery](troubleshooting.en.md#setup-resume). Do not restart with a new run ID.

<details>
<summary>Resume in a new terminal</summary>

**Terminal — restore the original clone:** run `bash` first. At each prompt, paste only the recorded path after `=`, without quotes.

```bash
read -r -p "Absolute path of this clone (REPO_ROOT): " REPO_ROOT &&
read -r -p "Printed RUN_DIR path: " RUN_DIR &&
cd "$REPO_ROOT" &&
source src/agent/.venv/bin/activate &&
export AZURE_CONFIG_DIR="$RUN_DIR/workshop/.azure-cli" &&
pwd
```

**Checkpoint:** the original clone path prints and the prompt shows `(.venv)`. If you completed step 2, its cached sign-in is reused.

**If not:** use [setup recovery](troubleshooting.en.md#setup-resume) to check the existing paths. Do not create a new run ID.

</details>

<a id="setup-snapshot"></a>

### 1-5. Copy the source snapshot

Next, create the runnable source snapshot.

**Terminal — original clone (`$REPO_ROOT`):**

```bash
python scripts/prepare_environment.py prepare --run-dir "$RUN_DIR"
```

**Checkpoint:** **`$RUN_DIR/source-manifest.json`** and **`$RUN_DIR/workshop/.env`** exist; this generated `.env` is now the runnable configuration.

**If not:** inspect the source-copy state using [setup recovery](troubleshooting.en.md#setup-resume). Do not repeat `init` or overwrite the existing folder.

Editing the original clone's `.env` does not update the generated copy; keep the saved configuration and ownership records intact when resuming.

<a id="setup-python"></a>

### 1-6. Install and test the isolated source

**Terminal — runtime folder (`$RUN_DIR/workshop`):**

```bash
cd "$RUN_DIR/workshop" &&
python3.13 -m venv src/agent/.venv &&
source src/agent/.venv/bin/activate &&
python -m pip install -r requirements.lock.txt &&
python -m unittest discover -s tests -v
```

**Checkpoint:** tests end with `OK` (`OK (skipped=1)` is normal: the runtime copy omits guides, so it skips the documentation checks). **`$RUN_DIR/source-manifest.json`** records the source commit and hashes. **`$RUN_DIR/workshop/.env`** has `LAB_LANGUAGE=en`, new owned names, and no reused `.azure`, `.foundry`, or virtual environment.

**If not:** stop before Azure operations. For folder/source-copy problems, use [saved setup recovery](troubleshooting.en.md#setup-resume); for installation or test failures, use [offline-test recovery](troubleshooting.en.md#offline-tests). Do not recreate an existing virtual environment or source snapshot.

Start step 2 in **`$RUN_DIR/workshop`**; step 2-2 then sends you back to **`$REPO_ROOT`** for provisioning.

<a id="setup-identity"></a>

## 2. Verify identity, preservation, and capacity

### 2-1. Sign in to Azure CLI and azd

Sign in from **`$RUN_DIR/workshop`** so the English agent later uses this isolated CLI profile. Do **not** run README `preflight` or `bind` yet; the foundation does not exist.

After each sign-in command, finish browser sign-in with the `.env` account, `AZURE_EXPECTED_USERNAME`. Choose **Use another account** if a different one appears.

**Terminal — runtime folder (`$RUN_DIR/workshop`):** enter the IDs. This keeps the sign-in in this folder's `.azure-cli/` (never share or commit it):

```bash
export AZURE_CONFIG_DIR="$PWD/.azure-cli" &&
read -r -p "AZURE_TENANT_ID value from .env: " LOGIN_TENANT_ID &&
read -r -p "AZURE_SUBSCRIPTION_ID value from .env: " LOGIN_SUBSCRIPTION_ID
```

**Checkpoint:** the prompt returns after you enter both IDs. Sign-in has not started yet.

**If not:** rerun this block with only each value after `=` in `.env`. For `read: -p: no coprocess`, run `bash` first.

**Terminal — runtime folder (`$RUN_DIR/workshop`):** sign in to Azure CLI. Choose the `.env` subscription if asked.

```bash
az login --tenant "$LOGIN_TENANT_ID" --subscription "$LOGIN_SUBSCRIPTION_ID" --output none
```

**Checkpoint:** browser sign-in finishes and the prompt returns without an error. `--output none` suppresses the account JSON.

**If not:** [recover only Azure CLI sign-in](troubleshooting.en.md#login), then continue to the next block.

<a id="azd-login"></a>

**Terminal — runtime folder (`$RUN_DIR/workshop`):** sign in to azd with the same account.

```bash
azd auth login --tenant-id "$LOGIN_TENANT_ID"
```

**Checkpoint:** browser sign-in finishes and the prompt returns without an error.

**If not:** [recover only azd sign-in](troubleshooting.en.md#login); do not repeat a successful Azure CLI sign-in.

<a id="login-check"></a>

**Terminal — runtime folder (`$RUN_DIR/workshop`):** verify both sign-ins.

```bash
az account show --subscription "$LOGIN_SUBSCRIPTION_ID" \
  --query "{user:user.name,tenant:tenantId,subscription:id,state:state}" --output json &&
azd auth status --output json
```

**Checkpoint:** CLI `user` and azd `email` equal `AZURE_EXPECTED_USERNAME`; `tenant` and `subscription` equal the `.env` IDs; `state` is `Enabled`; `status` is `authenticated`.

**If not:** sign in again with the configured account; if no browser opens, use [authentication troubleshooting](troubleshooting.en.md#login).

### 2-2. Check identity, preservation, and capacity

Continue in the same terminal used in 2-1. If you reopened it, first run **Resume in a new terminal** from 1-4 so `AZURE_CONFIG_DIR` points to `$RUN_DIR/workshop/.azure-cli`.

**Terminal — original clone (`$REPO_ROOT`):**

```bash
cd "$REPO_ROOT" &&
python scripts/provision_environment.py identity --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py ownership --run-dir "$RUN_DIR" --preserve-existing &&
python scripts/provision_environment.py model-capacity --run-dir "$RUN_DIR"
```

**Checkpoint:** Read the final JSON from each command and check only these fields:

- From the `identity` output: `requested_account_matches: true`, `configured_subscription_matches: true`, `configured_tenant_matches: true`, `subscription_state: Enabled`, and `default_subscription_changed: false`;
- From the `ownership` output: `existing_groups_explicitly_preserved: true`;
- From `model-capacity`: GlobalStandard records for the three candidates and auxiliary `gpt-5.4-mini`. Each model's `capacity_records` must include a record whose `availableCapacity` meets `required_capacity` (`50` per candidate, `100` for the auxiliary model). This is service capacity, **not your subscription's unused quota**.

**If not:** do not create resources. For an identity mismatch, return to the sign-in check; for an access error, use [access checks](instructor.en.md#access). For `No verified GlobalStandard capacity`, recheck only the same `model-capacity` command; stop here if capacity is still insufficient. Service capacity and subscription quota are separate, so a quota increase alone may not resolve this. Do not change subscriptions, models, or regions, or create another run ID.

<a id="subscription-quota"></a>

**Environment owner — check subscription quota before billable services:** in [model quota management](https://learn.microsoft.com/azure/foundry/openai/how-to/quota#view-and-request-quotas-in-foundry-portal), select the configured subscription, **Sweden Central**, and **GlobalStandard**. Compare available quota after existing allocations, not the total limit, with these deployment capacities.

| Model | Unused deployment capacity required for this environment |
|---|---:|
| `gpt-6-sol` | 50 capacity units |
| `gpt-6-luna` | 50 capacity units |
| `gpt-6-astra` | 50 capacity units |
| `gpt-5.4-mini` planner/judge | 100 capacity units |

A capacity unit is not a request count. If the portal shows TPM, use the linked documentation's **model-specific conversion**, not one common ratio for all models.

**Checkpoint:** all four models have enough unused subscription quota and the service capacity checked above. Step 6-1 checks candidate quota again because usage can change.

**If not:** if model-specific units or available quota cannot be verified, consult the subscription administrator and do not create resources. For insufficient quota, request an increase and **do not enter step 3 until it is granted and available**. Keep the same `RUN_DIR`; do not create the Search/logging foundation while waiting. Recheck this step's capacity and quota when resuming. A pending request is not available quota.

<a id="setup-foundation"></a>

## 3. Create the new group and foundation services

Review the generated names in **`$RUN_DIR/config.json`**, then run.

**Terminal — original clone (`$REPO_ROOT`):**

```bash
python scripts/provision_environment.py group --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py foundry --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py project --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py logs --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py insights --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py search --run-dir "$RUN_DIR"
```

**Checkpoint:** the last JSON shows `resource: search` and `state: Succeeded`, and the prompt returns.

**If not:** use [setup recovery](troubleshooting.en.md#setup-resume) to continue only the failed command and the remaining commands that did not run. If only the Search wait expired, use the collapsed recovery block below.

**Portal — Azure Portal → Resource groups:** search for `resource_group` from `config.json` and open that new group.

**Checkpoint:** the new resource group matches this shape:

```text
Subscription
└─ Resource group for this run (`run=$RUN_ID`, Sweden Central)
   ├─ Foundry account/project
   ├─ Search
   ├─ Application Insights
   └─ Log Analytics
```

**Resources** lists only this run's generated names; nothing from an old or shared group appears. **Tags** include `workshop=foundry-evaluation`, `cleanup-scope=exclusive`, `purpose=synthetic-data-only`, and `run=$RUN_ID`.

- Search uses Basic with one replica/partition; its `semanticSearch` and `knowledgeRetrieval` free settings do **not** make Search uptime or model calls free.
- The portal's ARM **Deployments** list is not the Foundry model-deployment list.

**If not:** identify the failed command in the output and [inspect the existing creation record](troubleshooting.en.md#setup-resume). Do not repeat successful creation commands or create another group. If only the Search wait expired, use the recovery immediately below.

<details>
<summary>Recovery only: the local Search wait expired</summary>

Preserve that attempt and continue waiting for the **same resource**.

**Terminal — original clone (`$REPO_ROOT`):**

```bash
python scripts/provision_environment.py search-status --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py wait-search --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py search-status --run-dir "$RUN_DIR"
```

**Checkpoint:** the same Search resource reports `provisioning_state: Succeeded` and `status: running`. Continue with step 4.

**If not:** keep the output and resume setup recovery for the same `RUN_DIR`.

</details>

<a id="setup-access"></a>

## 4. Grant scoped access and create connections

This step grants only scoped access and connections on this run's new resources:

- The four `user-*` commands grant Foundry, model, and Search roles only to **the user verified in step 2**; prepare other participants with the [instructor access checklist](instructor.en.md#access).
- `project-monitor` gives the project identity telemetry access.
- The two connection commands create a keyless Microsoft Entra (`AAD`) Search connection and an App Insights connection whose metadata records the actual `ResourceId`.
- The agent instance identity is created later; grant it Search/model access with `grant-agent-access` in [README step 4](../README.md#deploy), not broad Owner.

**Terminal — original clone (`$REPO_ROOT`):**

```bash
python scripts/provision_environment.py user-foundry --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py user-model --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py user-search-service --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py user-search-data --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py project-monitor --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py insights-connection --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py search-connection --run-dir "$RUN_DIR"
```

**Checkpoint:** the commands finish without errors. Every role line shows `created: true` or `already_assigned: true`, with `scope_resource` values `project`, `foundry`, and `search` for your user and `insights` and `logs` for the project identity. The connection outputs show `resource: insights-connection` and `resource: search-connection`.

**If not:** have the environment owner (you, in self-study) check the principal and scope in the error, then [resume only the failed role/connection command](troubleshooting.en.md#setup-resume). For `AuthorizationFailed`, first confirm that the signed-in account can assign roles at that scope (for example, subscription Owner). Do not work around it with broad Owner access or changes to shared connections.

<a id="setup-auxiliary"></a>

## 5. Deploy the auxiliary model and verify endpoints

Deploy the planner/judge and refresh the run folder with Azure's actual endpoints.

**Terminal — original clone (`$REPO_ROOT`):** deploy the auxiliary model and refresh endpoints.

```bash
python scripts/provision_environment.py auxiliary --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py ready --run-dir "$RUN_DIR"
```

**Checkpoint:** **`$RUN_DIR/workshop/.env`** contains the returned project endpoint and Azure OpenAI endpoint for this new environment; they differ from each other and from any previous run. The auxiliary deployment is `gpt-5.4-mini` / `2026-03-17`, the planner/judge, not a replacement for one of the three candidates.

**If not:** inspect [the same run's setup state](troubleshooting.en.md#setup-resume). If `auxiliary` succeeded and only `ready` failed, recover only `ready`; never guess the endpoints.

<a id="setup-candidates"></a>

## 6. Prepare candidates, calibrate, and choose the next handoff

### 6-1. Prepare the candidates

Prepare the candidate deployments in the runtime folder, then calibrate the judge before handoff.

**Terminal — runtime folder (`$RUN_DIR/workshop`):** enter the runtime folder: use the same terminal that completed step 5.

```bash
cd "$RUN_DIR/workshop" &&
source src/agent/.venv/bin/activate &&
export AZURE_CONFIG_DIR="$PWD/.azure-cli"
```

**Checkpoint:** the `(.venv)` prompt returns without an error. Run subsequent commands in `$RUN_DIR/workshop`, not the original clone.

**If not:** restore the existing `RUN_DIR` path with [setup recovery](troubleshooting.en.md#setup-resume).

**Terminal — runtime folder (`$RUN_DIR/workshop`):** prepare candidate models. This checks readiness, creates only missing paid candidate deployments, and checks again. Do not run a separate `preflight` around it.

```bash
python scripts/workshop.py prepare-models
```

**Checkpoint:** the command finishes without errors. Its **last JSON** shows:

- `language: en`;
- all three candidates have `deployed: true`;
- `missing_models: []`;
- fixed identities/versions are `gpt-6-sol` / `2026-09-22`, `gpt-6-luna` / `2026-09-22`, and `gpt-6-astra` / `2026-09-03`.

The first JSON's `missing_models` may describe the state before creation.

<details>
<summary>Optional example only: recorded readiness fields</summary>

This recorded screenshot shows the fields to check: `language: en`, `missing_models: []`, and `deployed: true` for each candidate. It was captured from the readiness check that `prepare-models` already runs; do not run it separately. Your deployment names can differ from the example.

![Recorded English readiness fields for three candidate deployments](assets/live-en-20260923b/screenshots/01-ready.webp)

</details>

**If not:** for `Insufficient quota ... 50 units required`, use [model quota management](https://learn.microsoft.com/azure/foundry/openai/how-to/quota) to request an increase for that subscription, Sweden Central, and model. After it takes effect, rerun this command; it creates only missing candidates. For other errors, [recover in the same folder](troubleshooting.en.md#setup-resume); do not substitute models.

<a id="setup-calibration"></a>

### 6-2. Check the judge

**Terminal — runtime folder (`$RUN_DIR/workshop`):** check the judge after candidate preparation finishes. There may be no output for 1–3 minutes.

```bash
python scripts/workshop.py calibrate
```

**Checkpoint:** **`Judge calibration passed`**. The two calibration examples are not part of the 48 candidate outputs.

**If not:** [recover only calibration](troubleshooting.en.md#calibration). Do not repeat completed candidate preparation.

<a id="handoff"></a>

### 6-3. Choose one handoff

**Choose one handoff:**

| Who continues | Folder and next action |
|---|---|
| You, for one-off self-study | Run the **open the workshop folder** block below, read [how to follow the README](../README.md#how-to-follow), then continue from [`bind`](../README.md#bind-project). Cloning, installation, sign-in, and preflight are already complete; do not repeat them. |
| Instructor rehearsing for a class | Keep this folder for model ownership. Use a [separate rehearsal clone](instructor.en.md#rehearsal-workspace) with new runtime names so rehearsal cleanup cannot delete the shared models. |
| A new participant | Give them a complete English `.env` with **unused** team names and the **actual prepared model deployment names**. Do not send `.azure`, `.foundry`, ownership files, auth caches, or results. Before sending, run the [team handoff checklist](instructor.en.md#handoff). They save that `.env` in a fresh folder and start at [README step 1](../README.md#start). |

**Terminal — only when you continue yourself, open the workshop folder:** paste only the path after `RUN_DIR=` in your notes; in a new terminal, run `bash` first.

```bash
read -r -p "RUN_DIR path from your notes: " RUN_DIR &&
cd "$RUN_DIR/workshop" &&
source src/agent/.venv/bin/activate &&
export AZURE_CONFIG_DIR="$PWD/.azure-cli" &&
pwd
```

**Checkpoint:** the printed path ends with `/workshop`. Note this path too: it is "this folder" in the README and the workshop folder you use for step 3's Terminal B.

**If not:** for `No such file or directory`, paste the `RUN_DIR` you noted again, without quotes.

**Editor — when you continue yourself:** open the printed `/workshop` folder with VS Code **File → Open Folder**. Read `.env` and results in **this copy**. It omits the README, `docs/`, and `.git`, so read the guide in your browser or original clone. **Only the reading location differs: keep running commands in the terminal's `/workshop` folder.** Read [how to follow the steps](../README.md#how-to-follow), then go to [README 1-4 `bind`](../README.md#bind-project).

**Checkpoint:** you chose exactly one row, and its recipient has the folder or complete `.env` that row describes.

**If not:** do not start README step 1; complete the chosen row first.

- Do not overwrite Korean-workshop language or knowledge objects; participant cleanup removes only that folder's owned runtime objects.
- The environment owner manages foundation, Search, logging, auxiliary-model costs, and [English result-scope questions](validation.en.md).

<details>
<summary>Reference: why setup checks matter</summary>

- `--preserve-existing` keeps all existing groups, including the Korean workshop; without it, previous candidates stop the command for manual ownership review.
- Each Azure CLI operation passes the configured subscription explicitly. Capacity availability and subscription quota are separate checks; model preparation validates quota again.
- The provisioner requires both ownership tags and this run's creation record; a tag alone is not authorization to modify another resource.

</details>

Stop here. **If you created this environment for self-study,** return to this guide after README step 10 and delete the resource group with the [final cleanup](#final-cleanup) below; only that stops the costs.

<a id="final-cleanup"></a>

## Final cleanup: delete your exclusive resource group after README step 10

**Only the environment owner proceeds.** After a completed workshop, first finish README step 10's `cleanup` and `check-cleanup`. **If you end setup or the main workshop early,** you can also delete the group after verifying the creation records and exclusive ownership below. If the main workshop started, first follow [the README early-stop path](../README.md#stop-early). Result files that do not exist yet are not required. Deletion is irreversible. Participant cleanup or a Copilot CLI execution request is not authorization to delete a whole group.

| Environment | Choose this path |
|---|---|
| Existing/shared environment, or a group needed by later participants/classes | **Preserve the foundation and auxiliary deployment.** The owner manages remaining costs, retention, and the final shutdown date. Do not delete the group below. |
| An **exclusively owned group newly created by this guide's tools**, with no other users or future exercises | After verifying ownership below, you may delete **only that group**. |
| Missing creation records or uncertain ownership/users | Stop and consult the owner. A name or tag alone does not authorize deletion. |

<a id="final-cleanup-check"></a>

**1. Preserve evidence and verify the deletion scope**

Keep the local responses, evaluations, and regression records already created, plus `verified-evidence.json` and `cleanup-check.json` if they exist. Do not manufacture missing results for an early exit. Do not assume Foundry report URLs or Azure traces will remain accessible after deletion. Do not share or commit authentication caches, passwords, or tokens.

**Editor — recorded run folder (`$RUN_DIR`):** open `config.json` and `infrastructure-state.json` from the **same recorded `RUN_DIR`**. Do not create a new run.

| Check | Values that must match |
|---|---|
| Run | `config.json → run_id` and `infrastructure-state.json → run` |
| Group to delete | `config.json → resource_group`. **Preserve `old_resource_group`.** |
| Subscription / Resource ID | `config.json → subscription` and the subscription/group in `infrastructure-state.json → group_id` |
| Created services | Resource IDs recorded under `infrastructure-state.json → resources` |

**Portal:** in [Azure Portal](https://portal.azure.com/), verify the configured account, tenant, and subscription, then open **Resource groups → that group**. Confirm:

- **Resource ID** matches the recorded `group_id`.
- **Location** is Sweden Central (`swedencentral`).
- **Tags** match `workshop=foundry-evaluation`, `cleanup-scope=exclusive`, `purpose=synthetic-data-only`, and `run=your run_id`.
- **Resources** show only services recorded for this run: Foundry account/project, Search, App Insights, and Log Analytics. Model deployments are not listed separately; they live inside the Foundry account and are deleted with the group.
- **Current usage** shows no other users or future class dependency.

Stop if there is an unrecorded resource, an unclear cross-group dependency, or a future class using this group. Do not edit tags or ownership files to make the checks pass.

**2. Delete only the reviewed group**

**This removes the entire group and its remaining services; the group itself cannot be recovered.** Proceed only after the owner reviews the exact scope and impact and decides to delete it. If Copilot CLI performs the action, **approve this specific subscription, group, and deletion impact separately**.

**Portal:** on that group's page, select **Delete resource group**, enter the **reviewed group name** in the confirmation field, and confirm deletion. Do not expand the scope to another group or shared environment. Follow the [official resource-group deletion procedure](https://learn.microsoft.com/azure/azure-resource-manager/management/delete-resource-group#delete-resource-group).

**3. Confirm deletion and review remaining charges**

**Portal:** wait for the **deletion-completed notification**, then refresh Resource groups in the same subscription and confirm that the exact group name is absent. Submitting the request is not completion. If locks, permissions, or dependencies prevent deletion, preserve the error and consult the owner; do not remove protections as a workaround.

**Do not rerun `check-cleanup` afterward.** It checks README step 10, where the foundation remains; use the portal outcome above to verify full-group deletion. Previously incurred usage and delayed charges may still appear. Review the subscription's **Cost Management → Cost analysis**; successful deletion does not mean a zero bill.

Sources: [Foundry basic infrastructure example](https://github.com/Azure-Samples/azd-ai-starter-basic/tree/main/infra) and [Search knowledge-retrieval billing settings](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-enable-disable).
