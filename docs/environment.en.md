# Create a new English Azure environment — instructor or self-study

[English workshop](../README.md) · [한국어](environment.ko.md)

**Outcome:** a new, paid English workshop environment in **Sweden Central**, with Foundry, Search, telemetry, three candidates, a planner/judge, and a ready-to-use `.env`. This setup is preparation work outside the 120-minute participant workshop.

**Use this page only when you need new foundation services (Foundry account/project, Search, telemetry, and model deployments).** If you already received a complete `.env`, skip this page and start at [README step 1](../README.md#start). If services exist but preparation is incomplete, use [existing-environment preparation](instructor.en.md#existing-foundation). Do not run both paths.

If you create the environment here, class, rehearsal, and self-study owners all follow steps 1–6, then choose one [handoff](#handoff) after calibration.

**Before starting:** Use one Bash/WSL terminal and run one block at a time. If you close it, follow the resume steps below.

- Tools: `git`, `python3.13`, `az`, `azd`, Bash/WSL, curl, an editor, and a browser.
- Access: the signed-in owner can create the listed resources and scoped RBAC role assignments.

Start at step 1 in an unused Git clone.

<details>
<summary>Prerequisite details</summary>

Use the instructor [tools](instructor.en.md#tools) and [access](instructor.en.md#access) checks if anything above is uncertain.

</details>

<a id="setup-route"></a>

**Route:** [1. Workspace](#setup-workspace) → [2. Identity/capacity](#setup-identity) → [3. Services](#setup-foundation) → [4. Access/connections](#setup-access) → [5. Auxiliary model](#setup-auxiliary) → [6. Candidates/calibration](#setup-candidates) → [handoff](#handoff).

> New services incur costs. Use synthetic data only.
>
> Preserve shared and Korean-workshop resources. Do not change another workflow's default Azure CLI subscription. Sweden Central is the resource-group location; GlobalStandard model inference is not a Sweden-only residency guarantee.

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
| `REPO_ROOT` | Original clone, guides, and preparation tools | Initial setup and provisioning in steps 2–5 |
| `RUN_DIR` | This run's configuration and creation records | Pass as `--run-dir` only; **do not run commands here** |
| `RUN_DIR/workshop` | Isolated source and its generated `.env` | Python tests, sign-in, step 6, and the participant exercise |

### 1-1. Create or enter the clone

If you are not already at the root of an **unused Git clone**, start here.

**Terminal — parent folder for a new clone:**

```bash
git clone https://github.com/junwoojeong100/foundry-evaluation.git foundry-evaluation-setup-en &&
cd foundry-evaluation-setup-en
```

**Checkpoint:** `README.md` is in the current folder.

**If not:** stop and move to the unused clone root before continuing. Do not run setup from a ZIP or an old workshop folder.

<a id="initial-settings"></a>

### 1-2. Fill the initial `.env`

**Editor — current clone root (later saved as `$REPO_ROOT`):**

1. Copy `.env.example` to `.env` in this clone root.
2. Fill exactly the rows below; leave every other template value unchanged.

- Do not create `.env.txt` or overwrite an existing `.env`.
- Never add passwords, API keys, or tokens.
- Subscription ID: [Azure Portal](https://portal.azure.com/) **Subscriptions → your subscription → Overview**; tenant ID: **Microsoft Entra ID → Overview**. Portal sign-in does not sign in `az` or `azd`.

| Initial field | Value |
|---|---|
| `AZURE_SUBSCRIPTION_ID` | Authorized workshop subscription |
| `AZURE_TENANT_ID` | Its tenant |
| `AZURE_EXPECTED_USERNAME` | Account that will sign in |
| `AZURE_RESOURCE_GROUP` | Previous group to inspect; if none, keep **`AZURE_RESOURCE_GROUP=`** |
| `LAB_LANGUAGE` | `en` |

The tools generate service names, endpoints, and deployment names in the isolated folder.

**Checkpoint:** `.env` is saved in the current clone root; `AZURE_SUBSCRIPTION_ID`, `AZURE_TENANT_ID`, `AZURE_EXPECTED_USERNAME`, and `LAB_LANGUAGE=en` are filled, and `AZURE_RESOURCE_GROUP` is a previous group name or intentionally left as `AZURE_RESOURCE_GROUP=`.

**If not:** fix `.env` before installing tools; do not continue with placeholders or secrets.

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

Choose a fresh run ID once. Do not reuse an example ID or an existing `RUN_DIR`; keep the printed path for every later block.

**Terminal — current clone root (saved as `$REPO_ROOT` here):**

```bash
REPO_ROOT="$(pwd)" &&
RUN_ID="en-$(date -u +%Y%m%d-%H%M%S)" &&
RUN_DIR="$REPO_ROOT/.workshop/$RUN_ID" &&
printf 'RUN_DIR=%s\n' "$RUN_DIR" &&
python scripts/prepare_environment.py init --run-dir "$RUN_DIR" --language en
```

Save the printed absolute `RUN_DIR` path now.

**Checkpoint:** `init` finishes and creates **`$RUN_DIR/config.json`**. It records the chosen names; it has not copied the source or created Azure resources.

**If not:** keep the output and the same `RUN_DIR`, then use [setup recovery](troubleshooting.en.md#setup-resume). Do not restart with a new run ID.

<details>
<summary>Resume in a new terminal</summary>

```bash
read -r -p "Absolute path of this clone (REPO_ROOT): " REPO_ROOT &&
read -r -p "Printed RUN_DIR path: " RUN_DIR &&
cd "$REPO_ROOT" &&
source src/agent/.venv/bin/activate
```

Step 2 sign-in commands set `AZURE_CONFIG_DIR`; if you are already past step 2, also run `export AZURE_CONFIG_DIR="$RUN_DIR/workshop/.azure-cli"`.

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

**Checkpoint:** tests end with `OK`; **`$RUN_DIR/source-manifest.json`** records the source commit and hashes. **`$RUN_DIR/workshop/.env`** has `LAB_LANGUAGE=en`, new owned names, and no reused `.azure`, `.foundry`, or virtual environment.

**If not:** stop before Azure operations and follow [Python setup recovery](troubleshooting.en.md#setup-resume). Do not recreate an existing virtual environment or source snapshot.

Start step 2 in **`$RUN_DIR/workshop`**; step 2-2 then sends you back to **`$REPO_ROOT`** for provisioning.

<a id="setup-identity"></a>

## 2. Verify identity, preservation, and capacity

### 2-1. Sign in to Azure CLI and azd

Sign in from **`$RUN_DIR/workshop`** so the English agent later uses this isolated CLI profile. Do **not** run README `preflight` or `bind` yet; the foundation does not exist.

**Terminal — runtime folder (`$RUN_DIR/workshop`):** enter the IDs. This keeps the sign-in in this folder's `.azure-cli/` (never share or commit it):

```bash
export AZURE_CONFIG_DIR="$PWD/.azure-cli" &&
read -r -p "AZURE_TENANT_ID value from .env: " LOGIN_TENANT_ID &&
read -r -p "AZURE_SUBSCRIPTION_ID value from .env: " LOGIN_SUBSCRIPTION_ID
```

**Terminal — runtime folder (`$RUN_DIR/workshop`):** sign in to Azure CLI. Choose the `.env` subscription if asked.

```bash
az login --tenant "$LOGIN_TENANT_ID" --subscription "$LOGIN_SUBSCRIPTION_ID" --output none
```

**Terminal — runtime folder (`$RUN_DIR/workshop`):** sign in to azd with the same account.

```bash
azd auth login --tenant-id "$LOGIN_TENANT_ID"
```

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
- From the `model-capacity` output: GlobalStandard records for `gpt-6-sol`, `gpt-6-luna`, `gpt-6-astra`, and the auxiliary `gpt-5.4-mini`.

**If not:** do not create resources. Use the sign-in checkpoint above for an identity mismatch; resolve access/capacity errors with the owner, then [resume only the failed setup command](troubleshooting.en.md#setup-resume). Do not substitute a subscription, model, or region.

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

**Portal — Azure Portal → Resource groups → this run's group:** open the new group.

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

**If not:** have the owner check the principal and scope in the error, then [resume only the failed role/connection command](troubleshooting.en.md#setup-resume). Do not work around it with broad Owner access or changes to shared connections.

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
source src/agent/.venv/bin/activate
```

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

**If not:** resolve model access, quota, or deployment errors, then [recover only the failed preparation in the same folder](troubleshooting.en.md#setup-resume).

<a id="setup-calibration"></a>

### 6-2. Check the judge

**Terminal — runtime folder (`$RUN_DIR/workshop`):** check the judge: run this after candidate preparation finishes.

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
| You, for one-off self-study | Stay in **`$RUN_DIR/workshop`** and run [the README `bind` command](../README.md#bind-project). Step 6 `prepare-models` already verified readiness; do not repeat cloning, installation, sign-in, or a separate README `preflight`. |
| Instructor rehearsing for a class | Keep this folder for model ownership. Use a [separate rehearsal clone](instructor.en.md#rehearsal-workspace) with new runtime names so rehearsal cleanup cannot delete the shared models. |
| A new participant | Give them a complete English `.env` with **unused** team names and the **actual prepared model deployment names**. Do not send `.azure`, `.foundry`, ownership files, auth caches, or results. Before sending, run the [team handoff checklist](instructor.en.md#handoff). They save that `.env` in a fresh folder and start at [README step 1](../README.md#start). |

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

Stop here unless you own a personal foundation and have finished README cleanup.

<details>
<summary>Optional after README step 10: delete a personal foundation</summary>

<a id="final-cleanup"></a>

**Final cleanup of a personal foundation — a separate choice**

**Only the environment owner proceeds, after completing `cleanup` and `check-cleanup` in README step 10.** Deleting the foundation is a separate decision; participant cleanup or a Copilot CLI execution request does not approve deleting an entire group.

| Environment | Choose this path |
|---|---|
| Existing/shared environment, or a group needed by later participants/classes | **Preserve the foundation and auxiliary deployment.** The owner manages remaining costs, retention, and the final shutdown date. Do not delete the group below. |
| An **exclusively owned group newly created by this guide's tools**, with no other users or future exercises | After verifying ownership below, you may delete **only that group**. |
| Missing creation records or uncertain ownership/users | Stop and consult the owner. A name or tag alone does not authorize deletion. |

<a id="final-cleanup-check"></a>

<details>
<summary>Owner-only deletion procedure: verify, delete, and confirm</summary>

**1. Preserve evidence and verify the deletion scope**

Keep the required local responses, evaluations, regression records, `verified-evidence.json`, and `cleanup-check.json`. Do not assume Foundry report URLs or Azure traces will remain accessible after deletion. Do not share or commit authentication caches, passwords, or tokens.

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
- **Resources** show only services recorded for this run: Foundry account/project, Search, App Insights, Log Analytics, and the auxiliary deployment.
- **Current usage** shows no other users or future class dependency.

Stop if there is an unrecorded resource, an unclear cross-group dependency, or a future class using this group. Do not edit tags or ownership files to make the checks pass.

**2. Delete only the reviewed group**

**This removes the entire group and its remaining services; the group itself cannot be recovered.** Proceed only after the owner reviews the exact scope and impact and decides to delete it. If Copilot CLI performs the action, **approve this specific subscription, group, and deletion impact separately**.

**Portal:** on that group's page, select **Delete resource group**, enter the **reviewed group name** in the confirmation field, and confirm deletion. Do not expand the scope to another group or shared environment. Follow the [official resource-group deletion procedure](https://learn.microsoft.com/azure/azure-resource-manager/management/delete-resource-group#delete-resource-group).

**3. Confirm deletion and review remaining charges**

**Portal:** wait for the **deletion-completed notification**, then refresh Resource groups in the same subscription and confirm that the exact group name is absent. Submitting the request is not completion. If locks, permissions, or dependencies prevent deletion, preserve the error and consult the owner; do not remove protections as a workaround.

**Do not rerun `check-cleanup` afterward.** It checks README step 10, where the foundation remains; use the portal outcome above to verify full-group deletion. Previously incurred usage and delayed charges may still appear. Review the subscription's **Cost Management → Cost analysis**; successful deletion does not mean a zero bill.

Sources: [Foundry basic infrastructure example](https://github.com/Azure-Samples/azd-ai-starter-basic/tree/main/infra) and [Search knowledge-retrieval billing settings](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-enable-disable).


</details>
</details>
