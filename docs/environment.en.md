# Instructor: create a new English Azure environment

**Outcome:** an English-only workshop group in **Sweden Central**, with Foundry, Search, telemetry, four candidate models, and a fixed auxiliary planner/judge.

Participants with a prepared `.env` should skip this document and start at [README step 1](../README.md#start). Use Git, Python 3.13, Azure CLI, azd with the Foundry extension, and Bash/WSL.

> New services incur costs. Use synthetic data, preserve shared/Korean resources, and never change the default Azure CLI subscription used by other work. Sweden Central resource placement does not mean GlobalStandard model inference is confined to that region.

## 1. Create an isolated English source workspace

Use a **Git clone**, not an extracted ZIP: the preparation tool records the actual source commit and file hashes. Work in the same Bash terminal and stop on an error.

Prepare a root `.env` from `.env.example`; do not overwrite an unrelated configuration.

| Initial field | Value |
|---|---|
| `AZURE_SUBSCRIPTION_ID` | Authorized workshop subscription |
| `AZURE_TENANT_ID` | Its tenant |
| `AZURE_EXPECTED_USERNAME` | Account that will sign in |
| `AZURE_RESOURCE_GROUP` | Previous group to inspect, or an empty value if none |
| `LAB_LANGUAGE` | `en` |

Keep the other template settings. New service names, endpoints, and deployment names will be generated in the isolated folder. Do not put credentials in `.env`.

```bash
python3.13 -m venv src/agent/.venv &&
source src/agent/.venv/bin/activate &&
python -m pip install -r requirements.lock.txt
```

Choose a fresh run ID once and keep `RUN_DIR` throughout:

```bash
REPO_ROOT="$(pwd)"
RUN_ID="en-$(date -u +%Y%m%d-%H%M%S)"
RUN_DIR="$REPO_ROOT/.workshop/$RUN_ID"
python scripts/prepare_environment.py init --run-dir "$RUN_DIR" --language en &&
python scripts/prepare_environment.py prepare --run-dir "$RUN_DIR"
```

Install and test the isolated source:

```bash
cd "$RUN_DIR/workshop" &&
python3.13 -m venv src/agent/.venv &&
source src/agent/.venv/bin/activate &&
python -m pip install -r requirements.lock.txt &&
python -m unittest discover -s tests -v
```

**Checkpoint:** tests end with `OK`; `source-manifest.json` records the source commit and hashes. The generated `.env` has `LAB_LANGUAGE=en`, new owned names, and no reused `.azure`, `.foundry`, or virtual environment.

Stay in `$RUN_DIR/workshop` for sign-in so the later English agent uses the same isolated CLI profile.

## 2. Verify identity, preservation, and capacity

Complete only [README step 1-3](../README.md#login): CLI profile, tenant/subscription inputs, Azure CLI sign-in, azd sign-in, and both account checks. Return here afterward. Do **not** run README preflight/bind yet; the foundation is not ready.

Then return to the original repository root:

```bash
cd "$REPO_ROOT" &&
python scripts/provision_environment.py identity --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py ownership --run-dir "$RUN_DIR" --preserve-existing &&
python scripts/provision_environment.py model-capacity --run-dir "$RUN_DIR"
```

**Checkpoint:** all identity matches are true, the subscription is Enabled, existing groups are explicitly preserved, and capacity is verified for the exact model versions.

`--preserve-existing` means **keep all existing groups**, including the Korean workshop. This command does not delete groups. Without that flag, finding previous candidates stops the command for a manual ownership review.

Each Azure CLI operation passes the configured subscription explicitly. Capacity availability and subscription quota are separate checks; model preparation validates quota again.

## 3. Create the new group and foundation services

Review the generated names in `config.json`, then run:

```bash
python scripts/provision_environment.py group --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py foundry --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py project --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py logs --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py insights --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py search --run-dir "$RUN_DIR"
```

**Checkpoint:** the new group contains the Foundry account/project, Search, Application Insights, and Log Analytics in Sweden Central. Azure Portal **Resources** and **Tags** should match this run's names and `workshop`, `cleanup-scope`, and `run` tags.

![Actual English-only foundation resources in Sweden Central](assets/live-en-20260916-0240/screenshots/00-environment.webp)

The example's **2 Failed** deployment-history entries are separate automatic alert/governance failures, not failed creation of these five resources. Their [actual causes are documented](validation.en.md#8-read-operational-and-setup-errors-honestly); do not change shared subscription settings just to remove the indicator.

The provisioner requires both ownership tags and this run's creation record. A tag alone is not authorization to modify another resource.

Search uses Basic with one replica/partition. Its `semanticSearch` and `knowledgeRetrieval` free settings do **not** make Search uptime or model calls free.

If only the local Search wait expires, preserve that attempt and continue waiting for the **same resource**:

```bash
python scripts/provision_environment.py search-status --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py wait-search --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py search-status --run-dir "$RUN_DIR"
```

Require `provisioning_state: Succeeded` and `status: running`; do not recreate the service or change region just to obtain a green screen.

## 4. Grant scoped access and create connections

The `user-*` operations target **the user verified in step 2**, not every future participant. Prepare other users according to the [instructor access checklist](instructor.en.md#access-boundaries).

```bash
python scripts/provision_environment.py user-foundry --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py user-model --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py user-search-service --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py user-search-data --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py project-monitor --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py insights-connection --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py search-connection --run-dir "$RUN_DIR"
```

**Checkpoint:** user roles are scoped to the new project/account/Search; the project identity can read the new telemetry. Search uses an Entra connection, and the App Insights connection has its actual `ResourceId` metadata.

The agent's instance identity is created later. Grant its Search/model access in [README step 4](../README.md#deploy), not by assigning broad Owner permissions to it.

## 5. Deploy the fixed auxiliary model and verify endpoints

```bash
python scripts/provision_environment.py auxiliary --run-dir "$RUN_DIR" &&
python scripts/provision_environment.py ready --run-dir "$RUN_DIR"
```

**Checkpoint:** the actual returned project and model endpoints match the new environment. They are different endpoints with different purposes.

The auxiliary deployment is `gpt-5.4-mini` / `2026-03-17`. It is the planner/judge, not a replacement for one of the four candidates.

## 6. Prepare candidates and hand over the English configuration

```bash
cd "$RUN_DIR/workshop" &&
source src/agent/.venv/bin/activate &&
python scripts/workshop.py preflight --allow-missing-models &&
python scripts/workshop.py prepare-models &&
python scripts/workshop.py preflight &&
python scripts/workshop.py calibrate
```

**Checkpoint:** `language: en`, the four exact candidate identities/versions, `deployed: true`, `missing_models: []`, and a successful judge calibration. The two calibration examples are not part of the 64 candidate outputs.

Continue rehearsal at README **step 1-4** in this folder. Authentication is already complete. For participants, supply complete English `.env` values and **unused** team prefixes/agent names, but retain the actual prepared model deployment names.

Do not copy ownership, authentication, or result files to a participant's folder. Do not switch the Korean workspace's language or overwrite its knowledge objects.

## Costs and boundaries

Participant cleanup removes only that folder's owned runtime objects. It does not remove every instructor-prepared model or foundation service. The instructor manages remaining Search, logging, auxiliary-model, and foundation costs.

The actual English results and scope are explained in [English evaluation results](validation.en.md). Resource pictures and scores from another language/run are not substitutes for this execution.

Sources: [Foundry basic infrastructure example](https://github.com/Azure-Samples/azd-ai-starter-basic/tree/main/infra) and [Search knowledge-retrieval billing settings](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-enable-disable).
