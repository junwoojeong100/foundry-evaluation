# Instructor prerequisites for the English workshop

[English workshop](../README.md) · [한국어](instructor.ko.md)

**Finish with:** ready Azure services and model deployments, a complete `.env` for each team, and a rehearsed participant path, all **outside the 120-minute workshop**.

**Who:** environment owners, including self-study learners (then "instructor" means you). Participants with a complete environment go to [README step 1](../README.md#start).

**You need:** an approved subscription, model access and capacity, the [access below](#access), and a budget; preparation and rehearsal create and call paid Azure resources (model deployments, Search, logging). The [budget worksheet](#budget) prices one recorded team: about $0.54 in tokens for the main workshop and up to about $16.55 with Levels 2–3, plus hosted-agent compute and shared costs.

**Route:**

1. **Tools and access:** [install the local tools](#tools), then [check access](#access).
2. **Foundation:** if Foundry, Search, or telemetry is missing, finish [Create a dedicated environment](environment.en.md); otherwise [prepare with the existing foundation](#existing-foundation).
3. <a id="after-calibration"></a>**After judge calibration passes, choose one delivery path:**
   - **Class:** in a [rehearsal clone](#rehearsal-workspace), complete README steps 1–9. If you will teach Levels 2–3, [rehearse them](#levels). Run README step 10 in that clone, then go to the [final model check](#final-model-check) → [timing](#rehearsal) → [handoff](#handoff). After class, [clean up](#cleanup-and-maintenance).
   - **Self-study:** return to [README `bind`](../README.md#bind-project) in the same folder.

**Start:** [install and check the local tools](#tools).

<a id="budget"></a>

<details>
<summary>Budget worksheet: what each team calls, with a sample cost</summary>

Prices vary by region and over time, so price these volumes in the [Azure pricing calculator](https://azure.microsoft.com/pricing/calculator/), set a budget alert on the resource group in [Cost Management](https://learn.microsoft.com/azure/cost-management-billing/costs/tutorial-acm-create-budgets), and compare actual cost there after rehearsal.

| Per team | Main workshop | Level 2 | Level 3 |
|---|---|---|---|
| Agent answers (each a Foundry IQ retrieval plus a candidate-model call) | 48 evaluated + 3 smoke | none | 18 (section 4) |
| Direct Sol calls | none | none | 15 stress-test answers + 6 red-team attacks |
| LLM-judge results on the auxiliary deployment | 96 + 4 calibration | 252 + one failure-clustering job | 36 rubric + 30 stress + 54 agent + 54 trace + up to 320 continuous, plus rubric and question generation |
| Safety-evaluator results | none | 36 | 15 stress + 6 red-team + 18 trace + up to 160 continuous |
| Paid objects the team creates | Hosted agent, from step 4 until step 10 cleanup | none | Continuous-evaluation schedule, for up to 8 hours or until step 10 |

The recorded English main run showed 53 agent runs and about 125.7K tokens on the agent dashboard ([recorded results](validation.en.md#dashboard)). Search, model deployments, and logging are shared and keep costing after team cleanup ([cleanup and maintenance](#cleanup-and-maintenance)).

**Sample cost from the recorded English runs:** Sweden Central list prices from the [Azure Retail Prices API](https://learn.microsoft.com/rest/api/cost-management/retail-prices/azure-retail-prices) on September 25, 2026, GlobalStandard, before tax and discounts. Replace them with your own prices before you approve a budget.

| Per team | Main workshop | Level 2 | Level 3 |
|---|---|---|---|
| Model and evaluation tokens | about $0.54 | about $2.32 | about $2.66, plus up to $11.03 for continuous evaluation |
| Hosted agent compute | $0.135 per active session-hour | none | same rate for the section 4 agent runs |

- Rates per 1M input/output tokens: Sol $2/$10, Luna $0.10/$0.50, Astra $10/$50, `gpt-5.4-mini` $0.75/$4.50. Safety results are priced on the AI evaluations meter at $20/$60.
- The token row adds the token usage saved with each answer, evaluation result, and the Level 2 failure-clustering job; continuous evaluation is counted at its 160-trace maximum. The red-team scan and the rubric and question generation jobs are not included because their saved results do not report tokens.
- A hosted session is billed for 1 vCPU and 2 GiB until its idle timeout ends (15 minutes by default).
- Shared costs continue: Search Basic $0.101 per hour (about $74 per month) and Log Analytics ingestion $2.99 per GB after the free allowance.

</details>

<a id="tools"></a>

## Install and check the local tools

**This is the basic setup, even when you run commands yourself.** If you use Copilot CLI, finish these checks first and follow the [Copilot CLI guide](copilot.en.md) separately; manual runs do not need Copilot CLI, Node.js, or Playwright.

| Tool | Installation reference / requirement |
|---|---|
| Git | [Install Git](https://git-scm.com/downloads) |
| Python | [Install Python](https://www.python.org/downloads/), selecting **3.13.x**; `python3.13` must work in the workshop terminal |
| Azure CLI | [Install Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) |
| azd | [Install Azure Developer CLI](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd) |
| Bash | Required shell. [GNU Bash](https://www.gnu.org/software/bash/) |
| curl | Required transfer tool. [curl packages for your platform](https://curl.se/download.html) |
| Editor | [Install VS Code](https://code.visualstudio.com/download) or use an existing editor that can open `.env` and JSON files |
| Browser | [Install Edge](https://www.microsoft.com/edge/download) or [Chrome](https://www.google.com/chrome/) for sign-in and Foundry portal checks |
| Windows only: WSL terminal | [Install WSL](https://learn.microsoft.com/windows/wsl/install) |

Run workshop commands in Bash: macOS/Linux use the local terminal; Windows uses WSL with the Linux tools installed inside WSL. Windows editors and browsers are fine for manual checks.

**Terminal — check CLI tools:** it stops at the first missing command; install only that tool, then repeat the check.

```bash
bash --version &&
curl --version &&
git --version &&
python3.13 --version &&
az version &&
azd version &&
azd extension list
```

**Checkpoint:** every command prints a version or JSON result, and `azd extension list` finishes successfully.

**If not:** install or repair only the missing tool, then rerun the same block. On Ubuntu/WSL: run `sudo apt-get update` once; for Bash run `sudo apt-get install bash`; for curl run `sudo apt-get install curl`.

Approve installation in your own terminal; never send the password through chat.

<details>
<summary>Platform notes for missing tools</summary>

On macOS, check `/bin/bash`, `/usr/bin/curl`, and PATH before treating a built-in command as missing. Other Linux distributions use their package manager.

</details>

**Terminal — any folder, only if `microsoft.foundry` has no installed version:**

```bash
azd extension install microsoft.foundry &&
azd extension list
```

**Checkpoint:** `azd extension list` shows an installed `microsoft.foundry` version.

**If not:** repair the azd installation, then rerun only this command.

**Terminal — verify agent commands:**

```bash
azd ai agent --help
```

**Checkpoint:** the command list includes `run` and `invoke`.

**If not:** repair the azd/`microsoft.foundry` extension version before starting. An update notice is not itself a failure; do not run “update all” or downgrade tools mid-experiment.

If you are not preparing Azure yourself, stop here and return to [README step 1](../README.md#start) or the [Copilot CLI guide](copilot.en.md); otherwise continue to [access](#access). Install Python packages in that path's virtual-environment step, not globally here.

<details>
<summary>Reference: Azure services and conditions to prepare</summary>

| Item | Required state |
|---|---|
| Azure subscription | The workshop subscription and tenant, selected explicitly |
| Foundry | A project of type `Microsoft.CognitiveServices/accounts/projects` |
| Region | A region where the Hosted Agent and all three models are actually available |
| Models | Actual Sol/Luna/Astra (`gpt-6-sol`, `gpt-6-luna`, `gpt-6-astra`) deployments plus the fixed auxiliary deployment for IQ planning and judging |
| Search | Supports semantic/agentic retrieval, with a system-assigned identity and Entra RBAC |
| Observability | Application Insights connected to the project, plus Logs read access |
| Local | Python 3.13, Azure CLI, azd, and the `microsoft.foundry` extension |
| Sign-in | Participants can sign in to both CLIs and complete MFA in README step 1-3 |
| Data | Synthetic documents only; a different workshop prefix for each team |

Agent hosting and the SDK packages can have different GA/preview status; do not treat one as the other.

</details>

<a id="access"></a>

## Access boundaries

The environment owner needs permission to create or use the workshop resources and to assign the listed roles at their target scopes. **Contributor alone does not grant role-assignment permission** (`Microsoft.Authorization/roleAssignments/write`).

An authorized access administrator must provide that permission or perform the assignments. Do not give administrator/Owner permissions to the agent as a shortcut. Participants without assignment permission need the owner for `prepare-iq` and `grant-agent-access`.

For each row, confirm the assignment in the target scope's **Access control (IAM) → Check access**, or get the access administrator's confirmation. Do not swap managed identities or scopes.

| Principal | Required purpose | Scope |
|---|---|---|
| Participant | Foundry access plus the required development/deployment operations | Approved project/account |
| Preparation operator | Create model deployments and Search schemas | Dedicated workshop resources |
| Document loader | Search Service Contributor and Search Index Data Contributor | Workshop Search |
| Search managed identity | Cognitive Services User for planner inference | Planner's Foundry account |
| Agent instance identity | Search Index Data Reader and Cognitive Services OpenAI User | Workshop Search and candidate-model account |
| Monitoring operator / project identity | Read the connected telemetry | Application Insights / Logs |

Local success does not prove hosted access. Grant only the roles above: an older role name in the portal (such as Azure AI User) is no reason to grant Owner, and roles that are already sufficient need nothing added. The agent calls models through the account endpoint, so its identity needs neither the project's `Foundry User` nor Owner. Remove roles you added while diagnosing when you clean up the test environment.

**Checkpoint:** every row has a named principal with the exact role at the exact scope, and the environment owner either can create those role assignments or has an authorized access administrator who agreed to.

**If not:** stop preparation until an authorized access administrator grants the role or performs the assignment; do not continue with Contributor-only access.

<details>
<summary>Production boundary and supported environments</summary>

This exercise uses synthetic documents shared by the team. It does not implement per-document authorization, tenant-isolated end-user retrieval, or on-behalf-of identity propagation for a production product. A Search reader role alone does not filter documents per user.

Supported hosted-agent environments are listed in the [Hosted Agent quickstart](https://learn.microsoft.com/azure/foundry/agents/quickstarts/quickstart-hosted-agent).

</details>

**Next:** with an existing foundation, continue to [Prepare with an existing foundation](#existing-foundation); for new services, return to [Create a dedicated environment](environment.en.md).

<a id="existing-foundation"></a>
<a id="install-and-verify-locally"></a>

## Prepare with an existing foundation

Use this path only when the foundation services already exist. If you completed the new-environment guide, use its handoff instead; do not repeat this setup.

**Order for this path:** check the scope and pass the local tests below, then [1. settings and sign-in](#existing-settings) → [2. auxiliary deployment](#auxiliary-model) → [3. candidates and calibration](#check-candidates) → rehearsal or self-study handoff.

**Check the scope first:** the Foundry account/project, Search, and connected Application Insights must be in the configured **`AZURE_RESOURCE_GROUP`**, and the candidate and auxiliary models must be deployments of that Foundry account. If they are split across groups or accounts, stop and align the setup with the owner; do not move shared resources to fit the example.

Use an unused clone as your **model-preparation folder**.

**Terminal — parent folder for clones:** create the model-preparation clone. If you already have an unused clone, skip this block and `cd` into its root.

**Before running:** if `foundry-evaluation-model-prep-en` already exists, replace both folder names in the block with one unused name. Do not delete the existing folder.

```bash
git clone https://github.com/junwoojeong100/foundry-evaluation.git foundry-evaluation-model-prep-en &&
cd foundry-evaluation-model-prep-en
```

**Checkpoint:** the terminal is at the root of the new model-preparation clone, which contains `README.md` and `scripts/`.

**If not:** rerun the block with one unused folder name, or `cd` into the root of an unused clone you already have.

**Terminal — model-preparation folder:**

```bash
python3.13 -m venv src/agent/.venv &&
source src/agent/.venv/bin/activate &&
python -m pip install -r requirements.txt &&
python -m unittest discover -s tests -v
```

**Checkpoint:** the test run ends with **`OK`**. The tests cover both languages and verify the fixed policy IDs, monetary rules, and frozen case contracts.

**If not:** fix the failing offline test before any Azure operation; keep the pinned dependencies in `requirements.lock.txt`.

<details>
<summary>Pinned package versions</summary>

Framework and Foundry SDK version ceilings can differ, so the workshop pins Agent Framework Foundry 1.11.0, core 1.16.0, OpenAI adapter 1.14.1, Azure AI Projects 2.3.0, and Agent Server Invocations 1.1.0. Do not upgrade frameworks, extensions, or SDKs indiscriminately during a workshop. `requirements.lock.txt` is the validated full dependency snapshot; to reproduce the same Python environment, use `python -m pip install -r requirements.lock.txt`.

</details>

**Next:** [copy the actual settings, sign in, and name the candidates](#existing-settings).

<a id="existing-settings"></a>
<a id="1-configure-and-sign-in"></a>

### 1. Copy the actual settings, sign in, and name the candidates

**Editor — model-preparation folder:**

- If you received a complete `.env`, verify its fields against the table below; do not replace it.
- Otherwise copy `.env.example` to **`.env` at this clone's root**, then fill only the fields below.

Copy only the displayed names and endpoints: never API keys, browser URLs, `/openai/v1/`, or full Resource IDs.

| `.env` field | Where to get the value |
|---|---|
| `AZURE_SUBSCRIPTION_ID` / `AZURE_TENANT_ID` | Azure Portal: **Subscriptions → your subscription → Overview** for the subscription ID; **Microsoft Entra ID → Overview** for its directory's tenant ID |
| `AZURE_EXPECTED_USERNAME` | The approved account's sign-in name (UPN), not its display name |
| `AZURE_RESOURCE_GROUP` | Azure Portal: the **Resource group** containing the existing workshop services |
| `AZURE_AI_ACCOUNT_NAME` / `AZURE_AI_PROJECT_NAME` | Foundry: the selected project's **resource name / project name**. The resource is the project's parent account, not the project itself. |
| `FOUNDRY_PROJECT_ENDPOINT` | Foundry: the selected project's **Overview → project endpoint**, ending in `/api/projects/<project>` |
| `AZURE_OPENAI_ENDPOINT` | Azure Portal: the **same Foundry account → Keys and Endpoint**, using its Azure OpenAI base endpoint ending in `.openai.azure.com` |
| `AZURE_SEARCH_NAME` / `AZURE_SEARCH_ENDPOINT` | Azure Portal: the intended **Search service → Overview**, copying its name and **URL** ending in `.search.windows.net` |
| `AZURE_APPLICATION_INSIGHTS_NAME` | Name of the **Application Insights resource connected to this project**, in the same group; not the Log Analytics workspace name |
| `MODEL_*_DEPLOYMENT` | Foundry **Build → Models**; copy actual candidate deployment names when they exist. Name missing candidates with the candidate table below. |

Keep the template defaults `LAB_LANGUAGE=en`, `LAB_PROMPT_VERSION=v1`, and `LAB_AUTH_MODE=cli`. Choose unused `LAB_PREFIX` and `LAB_AGENT_NAME` values. Record `LAB_AUX_DEPLOYMENT` later, in [step 2](#auxiliary-model). Do not paste `FOUNDRY_PROJECT_ENDPOINT` into `AZURE_OPENAI_ENDPOINT`.

**Checkpoint:** the table's fields hold the names and endpoints shown in the portal, and `LAB_LANGUAGE=en`, `LAB_PROMPT_VERSION=v1`, and `LAB_AUTH_MODE=cli` are unchanged.

**If not:** fix only `.env` before signing in.

<details>
<summary>Copilot CLI return point</summary>

If you came from the Copilot CLI guide only to collect settings, return to [plan review](copilot.en.md#plan-review) now. CLI sign-in belongs to the later execution phase.

</details>

After the local tests pass, sign in from the **model-preparation folder** so this folder uses its own isolated CLI profile. Run only the four sign-in blocks below; they match [README step 1-3](../README.md#login), but do **not** run README preflight or bind yet because the auxiliary model is not ready.

**Terminal A — 1. enter the IDs:** this keeps the sign-in in this folder's `.azure-cli/` (never share or commit it):

```bash
export AZURE_CONFIG_DIR="$PWD/.azure-cli" &&
read -r -p "AZURE_TENANT_ID value from .env: " LOGIN_TENANT_ID &&
read -r -p "AZURE_SUBSCRIPTION_ID value from .env: " LOGIN_SUBSCRIPTION_ID
```

**Checkpoint:** the two prompts accepted the tenant and subscription IDs from `.env`, and the terminal stayed in the model-preparation folder.

**If not:** rerun only this ID-entry block before signing in.

**Terminal A — 2. sign in to Azure CLI:** choose the `.env` subscription if asked:

```bash
az login --tenant "$LOGIN_TENANT_ID" --subscription "$LOGIN_SUBSCRIPTION_ID" --output none
```

**Checkpoint:** Azure CLI opens sign-in if needed and returns to the prompt without error.

**If not:** retry this block with the configured tenant and subscription, then use [authentication troubleshooting](troubleshooting.en.md#login).

**Terminal A — 3. sign in to azd** with the same account:

```bash
azd auth login --tenant-id "$LOGIN_TENANT_ID"
```

**Checkpoint:** azd login completes for the same account.

**If not:** rerun only the azd login block with the configured tenant.

<a id="login-check"></a>

**Terminal A — 4. verify both sign-ins:**

```bash
az account show --subscription "$LOGIN_SUBSCRIPTION_ID" \
  --query "{user:user.name,tenant:tenantId,subscription:id,state:state}" --output json &&
azd auth status --output json
```

**Checkpoint:** CLI `user` and azd `email` equal `AZURE_EXPECTED_USERNAME`; `tenant` and `subscription` equal the `.env` IDs; `state` is `Enabled`; `status` is `authenticated`.

**If not:** sign in again with the configured account; if no browser opens, see [authentication troubleshooting](troubleshooting.en.md#login).

**Editor — choose candidate deployment names before preflight:** update the three `MODEL_*_DEPLOYMENT` values in `.env` using this table.

| Candidate state | Value for its `MODEL_*_DEPLOYMENT` |
|---|---|
| The required model/version is already deployed | Copy its **actual deployment name**; it does not need your new prefix. |
| The candidate is not deployed yet | Reserve an unused name formed from your actual `LAB_PREFIX` plus `-sol`, `-luna`, or `-astra`. Step 3 creates the missing deployments. |

**Checkpoint:** each `MODEL_*_DEPLOYMENT` value is either an actual existing deployment name or an unused `<LAB_PREFIX>-sol` / `-luna` / `-astra` name.

**If not:** fix only those three `.env` values before running preflight.

Template names such as `ll-team01-sol` are not proof of an existing deployment. Keep the fixed [model IDs and versions](reference.en.md#model-names); prepare the auxiliary deployment separately below.

<a id="auxiliary-model"></a>

### 2. Prepare the auxiliary deployment first

**Before the exercise, the environment owner prepares one `gpt-5.4-mini` auxiliary deployment** that Foundry IQ planning and LLM judging share. `prepare-models` does not create it, and `--allow-missing-models` tolerates **only missing candidates**: the command still stops without this deployment. Work in order: inspect existing deployments, create one only if none matches, then record the actual name in `.env`.

**Portal — inspect existing deployments:**

1. Sign in to [Foundry](https://ai.azure.com/) with the configured account.
2. In **New Foundry**, open the project matching `AZURE_AI_ACCOUNT_NAME` and `AZURE_AI_PROJECT_NAME`.
3. Open **Build → Models** and check an existing deployment against these requirements:

| Check | Fixed workshop requirement |
|---|---|
| Location | The **same Foundry account** configured in `.env` |
| Model ID / version | `gpt-5.4-mini` / `2026-03-17` |
| Deployment type | **Global Standard** (`GlobalStandard`), not a PTU reservation |
| Version stability | No automatic version upgrades (`NoAutoUpgrade`) |
| Deployment status | **`Succeeded`** |

If the **Build → Models** columns are hard to find, open the example below and compare only model, version, status, and deployment type.

<details>
<summary>Optional screenshot from the recorded Korean example (open only to locate Build → Models fields)</summary>

Use this only for field positions, not text matching. Your portal language, deployment names, prefix, and timestamps may differ. This recorded run shows **Build → Models → Deployments** with three candidate deployments plus `gpt-5.4-mini`, all `Succeeded` and `Global Standard`.

![Recorded Foundry deployments example](assets/live-ko-20260923b/screenshots/S1-P01-models-after.webp)

</details>

Reuse an existing deployment only if every row matches.

**Portal — create only if none matches:** at **Discover → Models → `gpt-5.4-mini` → Deploy → Custom settings**, create `<LAB_PREFIX>-judge` with **Global Standard**, version `2026-03-17`, `NoAutoUpgrade`, and approved capacity. Stop if model access, version/type, or quota is unavailable; do not substitute another model or modify a shared deployment.

**Checkpoint:** an existing or new auxiliary deployment matches every row above and shows `Succeeded`.

**If not:** fix model access, version or type, quota, or deployment status before editing `.env`.

**Editor — record the auxiliary deployment:** record these values in this folder's `.env`, and save the deployment's Resource ID somewhere participant cleanup does not touch.

| Key | Value to record |
|---|---|
| `LAB_AUX_DEPLOYMENT` | **Actual deployment name copied from Build → Models** |
| `LAB_AUX_MODEL` | `gpt-5.4-mini` |

**Checkpoint:** the deployment is in the `.env` Foundry account/project, meets the requirements above, and the two `.env` values match **the actual deployment name and model ID**. IQ planning and evaluation judging share this deployment, and its Resource ID is saved outside participant cleanup.

**If not:** stop here and fix the auxiliary deployment or its two `.env` values first; do not modify a shared deployment or substitute a model.

<a id="check-candidates"></a>

### 3. Check the candidates and calibrate the judge

**Terminal — check current models:** use the same model-preparation folder. The auxiliary deployment must already be ready.

```bash
python scripts/workshop.py preflight --allow-missing-models
```

**Checkpoint:** the command finishes without errors and prints `language: en` and `missing_models`. If the list is **`[]`, the candidates are ready**: skip creation and go to [judge calibration](#candidate-calibration).

**If not:** resolve auxiliary-model errors in the [previous step](#auxiliary-model), or use the [symptom table](troubleshooting.en.md#symptoms) for other errors. Do not proceed to model creation after a failed check.

**Terminal — create only if `missing_models` lists candidates:** this creates only missing, prefixed deployments and runs `preflight` at the end. New deployments use `GlobalStandard` capacity 50 and `NoAutoUpgrade`; existing deployments are preserved.

```bash
python scripts/workshop.py prepare-models
```

**Checkpoint:** the command finishes without errors and its **last JSON** has `language: en`, `deployed: true` for all three candidates, and `missing_models: []`. Do not run another separate `preflight`.

**If not:** resolve model access, quota, or deployment errors, then recover only the failed command in the same folder. Do not change names, substitute models, or create a new foundation as a workaround ([symptom table](troubleshooting.en.md#symptoms)).

<a id="candidate-calibration"></a>

**Terminal — check the judge (both paths):**

```bash
python scripts/workshop.py calibrate
```

**Checkpoint:** **`Judge calibration passed`**. README step 5 repeats this check in each participant workspace; matching completed calibration is reused. The two fixed examples are not part of the 48 candidate responses.

**If not:** [recover only calibration](troubleshooting.en.md#calibration), not completed model preparation.

If evaluation reports missing Application Insights `ResourceId` metadata, open the owner-only recovery below before retrying.

<details>
<summary>Owner-only observability recovery</summary>

Use the [observability symptom row](troubleshooting.en.md#symptoms). Only an authorized instructor may repair a dedicated workshop connection; never modify a shared connection to make an example work.

Use `python scripts/workshop.py repair-observability --confirm` only after confirming the connection is dedicated to this workshop.

After resolving the cause, choose [calibration recovery](troubleshooting.en.md#calibration) or [evaluation recovery](troubleshooting.en.md#evaluation-retry) based on the saved run status. A local error alone does not authorize `--retry-failed`; never retry a valid low score to force a pass.

</details>

**Next:** for a class, use the [separate rehearsal folder](#rehearsal-workspace). For self-study, return to [README `bind`](../README.md#bind-project) in this same folder. Do not repeat completed cloning, installation, sign-in, or preflight.

<a id="rehearsal-workspace"></a>
<a id="separate-rehearsal-from-participant-execution"></a>

## Separate model preparation, rehearsal, and participant execution

**For a class, keep model ownership in the preparation folder.** Do not rehearse the full exercise in that folder: its step-10 cleanup can delete the models you intend to share with participants.

```text
Preparation folder (owns the shared models)
  -> copy only .env, change LAB_PREFIX/LAB_AGENT_NAME -> rehearsal clone: steps 1-9 -> optional Levels 2/3 -> step 10
  -> copy only .env, change LAB_PREFIX/LAB_AGENT_NAME -> each team's clone: same path
```

**Terminal — outside the model-preparation clone, in the parent folder for rehearsal clones:** after model preparation completes, create the default rehearsal clone.

**Before running:** if `foundry-evaluation-rehearsal-en` already exists, replace both folder names in the block with one unused name. Do not delete the existing folder.

```bash
git clone https://github.com/junwoojeong100/foundry-evaluation.git foundry-evaluation-rehearsal-en &&
cd foundry-evaluation-rehearsal-en
```

**Checkpoint:** the terminal is at the root of the new rehearsal clone, which contains `README.md` and `scripts/`.

**If not:** rerun the block with one unused folder name, or `cd` into the root of an unused clone you already have.

**Editor — rehearsal clone `.env`:** copy **only** the model-preparation folder's completed `.env` into this clone's root. Keep `LAB_LANGUAGE=en`, the project, endpoints, and model deployment names unchanged. Change only **`LAB_PREFIX` and `LAB_AGENT_NAME`** to unused rehearsal names.

**Checkpoint:** the rehearsal clone has `.env` with `LAB_LANGUAGE=en`, the actual endpoints and deployment names, and unused `LAB_PREFIX` / `LAB_AGENT_NAME`.

**If not:** fix only `.env` in the rehearsal clone. Do not copy `.azure`, `.foundry`, authentication caches, or results.

**README — rehearsal clone:** in this clone, start at [README step 1-1](../README.md#source-setup) right after its clone block, using the `.env` you just copied, and complete README steps 1–9 in order; then return here.

**Checkpoint:** in this clone, README 9-1 `verify` shows `component_execution_verified: true`, `primary_model_outputs: 48`, and `distinct_verified_traces: 48`, and the 9-2 dashboard shows data.

**If not:** recover only in the README step that failed; do not continue to Levels or cleanup.

<details>
<summary>Bind and local-server background</summary>

`bind` uses the provided `azure.yaml` to create or reuse this folder's azd environment and set its team-specific service/agent name. It does not reprovision the Foundry project. Do not run `azd ai agent init` again, copy another folder's state, or ignore subscription/project conflicts.

Keep the local server in a trusted development environment, never expose it publicly, and stop it after the local check. Local and platform-authenticated hosted endpoints have different security boundaries.

</details>

**Next:** if you will teach Levels 2/3, continue with [Prepare Levels 2 and 3](#levels); otherwise run [README step 10](../README.md#cleanup) in this clone, then the [final model check](#final-model-check).

<a id="levels"></a>

## Prepare Levels 2 and 3

Rehearse only the levels you will teach ([Level 2](level-2.en.md), [Level 3](level-3.en.md)), after README step 9 in the rehearsal clone and before its step 10. Teams do them between steps 9 and 10 in their own folders. Before teams start, confirm trace access, judge and Sol capacity, red-team approval if you teach section 3, and cleanup boundaries. Level 3 section 4 calls the Foundry account's evaluation API as each participant, so participants need **Foundry User** on the Foundry account; a project-scope assignment, such as the one `user-foundry` creates in the [new-environment guide](environment.en.md), is not enough.

**Terminal — prepare trace access for existing foundations:** run once in the model-preparation folder for the shared foundation. Rehearsal and team folders do not need this command after it succeeds. New environments created with [the new-environment guide](environment.en.md) already have these roles.

```bash
python scripts/workshop.py prepare-trace-access
```

**Checkpoint:** the command finishes without errors and prints `Trace access is ready. This shared preparation is not recorded as team-owned, so team cleanup keeps it.` It may also print `Log Analytics Reader is already assigned...` or `Assigned Log Analytics Reader...`.

**If not:** stop Level 2/3 preparation and have the environment owner resolve the reported managed-identity, workspace, or RBAC issue. Do not let teams start trace evaluation yet.

Before teaching Level 3 red teaming, get organization approval for harmful-prompt testing; otherwise skip Level 3 section 3. Use only the synthetic workshop data; do not connect real employee data.

<details>
<summary>Level 2/3 rehearsal checklist</summary>

If teaching Levels 2–3, rehearse capacity, trace access, red-team approval, and cleanup boundaries.

| Check | Why |
|---|---|
| Judge capacity | Rate-limit risk → stagger teams or raise approved judge capacity. |
| Sol deployment | Shared Sol load → confirm capacity for `stress-test` and `red-team`. |
| Live agent calls | Hosted-agent load → rehearse 18 Foundry calls per team across three parallel runs. |
| Trace access | Covered by the `prepare-trace-access` command above. |
| Continuous evaluation | Scheduled judge usage → confirm up to 20 traces hourly for 8 hours per team. |
| Preview APIs | Preview API drift → rehearse custom/generated evaluators, insights, synthetic data, and red teaming close to class date. |
| Ownership | Cleanup boundary → team cleanup deletes only team-created custom evaluators and generated datasets; eval groups, insights, and red-team scans remain. |

**Trace content:** the agent's model spans record the full model input (the question with the retrieved policies) and the answer. That is what trace evaluation reads.

**Not supported here:** Agent red teaming is not supported for this hosted-agent protocol, so Level 3 red-teams the model deployment instead. See [beyond this workshop](level-3.en.md#beyond).

</details>

**Next:** run [README step 10](../README.md#cleanup) in the rehearsal clone, then the [final model check](#final-model-check).

<a id="final-model-check"></a>

## Final model check before handoff

**Terminal — model-preparation folder:** restore its environment and check the models before handoff.

```bash
source src/agent/.venv/bin/activate &&
export AZURE_CONFIG_DIR="$PWD/.azure-cli" &&
python scripts/workshop.py preflight
```

**Checkpoint:** the command finishes without errors and shows all three candidate deployments with `missing_models: []`.

**If not:** stop handoff and return to [3. Check the candidates](#check-candidates) in this folder. Do not clean up models while teams still use them.

**Next:** [rehearsal timing](#rehearsal).

<a id="rehearsal"></a>

## Rehearsal timing

The 120 minutes assume a prepared environment. Do not shorten the workshop by omitting a model, retrieval, or evaluation. If timing slips, measure these delays: model deployment, agent deployment, cold start, RBAC propagation, evaluator completion, and telemetry ingestion.

| Time | Participant steps | Observable outcome |
|---|---|---|
| 00–10 min | 1. Prepare | Offline tests, two sign-ins, identity check, preflight, and binding |
| 10–25 min | 2. Knowledge | Actual English document IDs and IQ activity |
| 25–40 min | 3–4. Local and hosted | Real answers in both environments |
| 40–55 min | 5. Baseline | 18 actual English responses and completed Foundry evaluation |
| 55–70 min | 6. Review | A real trace and reviewed regression case |
| 70–85 min | 7. V2 | New version, same 6 dev questions × 3 models = 18 responses |
| 85–100 min | 8. Holdout | Frozen candidate and 12 responses |
| 100–110 min | 9. Observe | 48 responses, 48 traces, and complete lineage |
| 110–115 min | 10. Cleanup | Only the folder's owned objects removed |
| 115–120 min | Buffer | Evaluation and telemetry ingestion delay |

**Checkpoint:** the rehearsal fits 120 minutes without dropping retrieval, any model, evaluation, or cleanup.

**If not:** adjust capacity, concurrency, or readiness before participants start.

During class, if a team is delayed more than 10 minutes by an environment problem, restore that folder's settings and access with the team. If a different environment is needed, start a separate run with a new folder and names; do not carry over earlier responses or ownership records.

**Next:** [team handoff](#handoff).

<a id="handoff"></a>

## What to hand to each team

Use this checklist only after rehearsal cleanup, the [final model check](#final-model-check), and the [timing](#rehearsal) all pass. Participants then follow README steps 1–10; Levels 2–3 go after step 9, before cleanup.

**Editor:** prepare one team packet with a complete `.env`, the README step-1 link, and the support contact.

| Item | Instructor responsibility |
|---|---|
| Account | Confirm access to the intended subscription, tenant, project, and model deployments. Participants sign in and complete MFA in README step 1-3. |
| Complete `.env` | Use `.env.example`, fill the actual values, and set **`LAB_LANGUAGE=en`**. Do not include passwords, API keys, or tokens. Each participant runs `bind` in their own folder; an instructor-bound copy does not count. |
| Ready services | Foundry project, Search, connected Application Insights, three fixed candidates, and the auxiliary deployment. Keep shared deployment names unchanged in `MODEL_*_DEPLOYMENT`; the instructor owns model and foundation costs. |
| Unused names | A unique `LAB_PREFIX` and `LAB_AGENT_NAME` for each team, with English and Korean runs in separate folders. Reserve names only; do not pre-create participant-owned KB, source, index, or agent resources. |
| Tools | Pass the [basic tool checks](#tools). Complete [additional Copilot CLI setup](copilot.en.md) separately if using it. |
| Access support | A person who can resolve narrowly scoped role assignment, 403, and capacity issues |
| Levels 2–3 | If teaching them, the judge and Sol capacity for all teams ([Prepare Levels 2 and 3](#levels)) |

**Checkpoint:** every row in the table is confirmed, and each team packet holds a complete `.env` with unique `LAB_PREFIX` and `LAB_AGENT_NAME`, the README step-1 link, and the support contact; then send the packet and [README step 1](../README.md#start).

**If not:** withhold the team packet and fix the missing account, setting, service, name, tool, or support owner before participants start.

## Cleanup and maintenance

**README — each owned workshop folder:** use the [README step-10 dry run](../README.md#cleanup) before confirming cleanup. Continue only when the listed names match that folder's owned objects. Never delete an entire shared resource group or run `azd down` against shared resources. Shared Search, model deployments, and logging keep costing after team cleanup; the environment owner tracks them in Cost Management.

For an exclusively owned self-study group, use [final foundation cleanup](environment.en.md#final-cleanup) after README step 10.

**Checkpoint:** each folder's README step-10 dry run lists only objects owned by that folder.

**If not:** stop cleanup and resolve the ownership or environment mismatch before confirming deletion.

**Next:** preparation and cleanup are complete. Use the maintainer checks below only when editing these guides.

<a id="documentation-checks"></a>

<details>
<summary>Maintainer checks when editing these guides</summary>

## When updating the guides

Before changing Foundry agent code or instructions, read the `microsoft-foundry` skill guidance. Use synthetic data only, do not change shared Azure resources or the default CLI subscription, and name the configured subscription in Azure commands. Keep the links between models, instructions, datasets, and traces; do not substitute models or count missing or failed rows as successes. Keep documented commands matched to the code, and pass the offline tests before any Azure run.

Keep English and Korean execution paths aligned. Lead with the outcome and starting conditions, distinguishing **a new workshop from an existing run** first. Collapse alternative paths such as environment preparation or tool delegation, along with background explanations.

Each execution step must name **where to act, the command, its completion evidence, and the recovery path**. Give collection, evaluation, aggregation, trace lookup, verification, **candidate preparation, and calibration one command and one checkpoint each**. Recovery pages should fix the failed task, then link to **the main guide's next unexecuted command**, not duplicate a bundle of later steps. Do not repeat checks that a command already performs internally.

Place each collapsed example screen right after the checkpoint it illustrates. A setup guide's return link must target the next unexecuted command. Put the final report after evidence and portal checks; distinguish **provenance links, execution completion, and quality passes**. Recorded answers and scores are examples, not the reader's target results. Keep actual cloud results in the separate [English](validation.en.md) and [Korean](validation.ko.md) result pages; a translated question is not a newly independent holdout case.

From the **original clone**, with its virtual environment active, run:

```bash
python -m unittest discover -s tests -p 'test_docs.py' -v
```

This checks local links/anchors/assets, code-block structure, Bash/JSON syntax, Python CLI arguments against the actual parsers, and matching English/Korean command sequences. It also checks separate checkpoints in the main, candidate-preparation, and collection-recovery paths; **If not** guidance in participant and environment-preparation guides; recovery links to the next command; and the **dashboard → report → cleanup** order. It does **not** execute the example commands, contact Azure, or revalidate recorded cloud scores. Runnable source snapshots omit the guides and skip these documentation checks.

Also follow [the starting instructions](../README.md#start-here) as a participant, an environment owner, and a returning user. Check that **the next action, completion signal, and next destination** require no guesswork. Automated checks cannot establish that a first-time reader understands the instructions.

</details>
