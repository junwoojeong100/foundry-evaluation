# Instructor prerequisites for the English workshop

[English workshop](../README.md) · [한국어](instructor.ko.md)

Participants follow [README.md](../README.md#start). Keep infrastructure creation and recording production out of their 120-minute path. Use [new-environment setup](environment.en.md) when the required Azure foundation does not yet exist.

**Self-study:** “instructor” means the environment owner, which can be you. Complete preparation once, then use the participant path. You still need an approved subscription, model access/capacity, and the permissions below; this guide cannot grant them.

**Preparation order:** [tools](#tools) → [access](#access) → choose the setup path below → [separate rehearsal](#rehearsal-workspace) → [team handoff](#handoff).

| Azure foundation | Setup path |
|---|---|
| Foundry, Search, or connected telemetry is not ready | [Create a dedicated environment](environment.en.md); do not run both setup paths |
| Those services already exist; models/access still need checking | [Prepare with the existing foundation](#existing-foundation) |

<a id="tools"></a>

## Install and check the local tools

| Tool | Installation reference / requirement |
|---|---|
| Git | [Install Git](https://git-scm.com/downloads) |
| Python | [Install Python](https://www.python.org/downloads/), selecting **3.13.x**; `python3.13` must work in the workshop terminal |
| Azure CLI | [Install Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) |
| azd | [Install Azure Developer CLI](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd) |
| Windows terminal | [Install WSL](https://learn.microsoft.com/windows/wsl/install); install the Linux tools **inside WSL**, not only on Windows |

Use Bash (`bash`) on macOS/Linux, or a WSL Bash terminal on Windows. A text editor such as VS Code is enough for reading JSON and editing `.env`.

```bash
git --version &&
python3.13 --version &&
az version &&
azd version &&
azd extension list
```

If a command is missing, install that tool and repeat this check. If `microsoft.foundry` has **no installed version**, install it once:

```bash
azd extension install microsoft.foundry
```

Then confirm the agent commands are available:

```bash
azd ai agent --help
```

Require the command list to include `run` and `invoke`. An update notice is not itself a failure of the installed commands; do not run “update all” or downgrade tools mid-experiment. If the installed commands fail, resolve the compatible azd/extension versions before starting.

Participants with ready services and a complete `.env` return to [README step 1](../README.md#start). Environment owners continue with [access](#access), then choose the setup path above.

<a id="handoff"></a>

## What to hand to each team

Use this checklist **after rehearsal**, not as a replacement for provisioning.

| Item | Instructor responsibility |
|---|---|
| Account | Confirm access to the intended subscription, tenant, project, and model deployments. Participants sign in and complete MFA in README step 1-3. |
| Complete `.env` | Use `.env.example`, fill the actual values, and set **`LAB_LANGUAGE=en`**. Do not include passwords, API keys, or tokens. |
| Ready services | Foundry project, Search, connected Application Insights, four fixed candidates, and the auxiliary planner/judge |
| Unused names | A unique `LAB_PREFIX` and `LAB_AGENT_NAME` for each team |
| Tools | Git, Python 3.13, Azure CLI, azd with the Foundry extension, and Bash/WSL |
| Access support | A person who can resolve narrowly scoped role assignment, 403, and capacity issues |

A new participant clone has no local azd binding. The participant must run **`bind` in their own folder**, even if the instructor has already bound another copy.

English and Korean must use **separate folders, prefixes, agent names, and knowledge objects**. Do not flip `LAB_LANGUAGE` in a workspace that already owns resources or contains experiment results. The runtime rejects mixed-language ownership, responses, evaluations, and regression lineage.

<a id="rehearsal-workspace"></a>
<a id="separate-rehearsal-from-participant-execution"></a>

## Separate model preparation, rehearsal, and participant execution

**For a class, keep model ownership in the preparation folder.** Do not rehearse the full exercise in that folder: its step-10 cleanup can delete the models you intend to share with participants.

After model preparation completes, create a separate rehearsal clone. If the example folder already exists, use another unused name; do not delete the existing folder.

```bash
git clone https://github.com/junwoojeong100/foundry-evaluation.git foundry-evaluation-rehearsal-en &&
cd foundry-evaluation-rehearsal-en
```

Copy **only the completed `.env`** into this clone using your editor. Keep `LAB_LANGUAGE=en` and the actual project, endpoints, and model deployment names. Change **`LAB_PREFIX` and `LAB_AGENT_NAME` to unused rehearsal names**. Then follow [README steps 1–10](../README.md#start), skipping its clone block because this folder is already ready.

Reserve different prefixes and agent names for participants. Do not create their KB, source, index, or agent in advance; a fresh participant folder will correctly refuse to overwrite unowned objects.

If model deployments are shared within the approved workshop foundation, keep their **actual deployment names** in `MODEL_*_DEPLOYMENT`. Do not rename a deployment in `.env` to a resource that does not exist.

Do not copy someone else's `.azure`, `.foundry` ownership files, authentication cache, or results to bypass a guard. A participant's cleanup deletes only objects recorded as owned by that folder. The instructor remains responsible for prepared models and foundation-service costs.

**After rehearsal cleanup, before handoff:** return to the model-preparation folder and its CLI profile, run `python scripts/workshop.py preflight`, and require all four deployments plus `missing_models: []`. If a model is missing, stop handoff and restore preparation first. Do not clean up the preparation folder's models while teams still use them.

Use the [rehearsal timing](#rehearsal) below. For **one-off self-study with no later participants**, staying in the preparation folder is valid; its owned-model cleanup is then intentional.

<a id="access"></a>

## Access boundaries

The environment owner needs permission to create the resource group/resources and to assign the listed roles at their target scopes. **Contributor alone does not grant role-assignment permission** (`Microsoft.Authorization/roleAssignments/write`); an authorized access administrator must provide it or perform those operations. Do not give administrator/Owner permissions to the agent as a shortcut. Participants without assignment permission need the owner for `prepare-iq` and `grant-agent-access`.

| Principal | Required purpose | Scope |
|---|---|---|
| Participant | Foundry access plus the required development/deployment operations | Approved project/account |
| Preparation operator | Create model deployments and Search schemas | Dedicated workshop resources |
| Document loader | Search Service Contributor and Search Index Data Contributor | Workshop Search |
| Search managed identity | Cognitive Services User for planner inference | Planner's Foundry account |
| Agent instance identity | Search Index Data Reader and Cognitive Services OpenAI User | Workshop Search and candidate-model account |
| Monitoring operator / project identity | Read the connected telemetry | Application Insights / Logs |

Users, the project identity, and the agent's **instance identity** are not interchangeable. Local inference success does not prove that the hosted agent has data access. Do not grant broad Owner access as a shortcut.

This exercise uses synthetic documents shared by the team. It does not implement per-document authorization, tenant-isolated end-user retrieval, or on-behalf-of identity propagation for a production product.

<a id="existing-foundation"></a>
<a id="install-and-verify-locally"></a>

## Install and verify locally — existing foundation

Use this path only when the foundation services already exist. If you completed the new-environment guide, use its handoff instead; do not repeat this setup.

Use an unused clone as your **model-preparation folder**. If needed, use the clone block in [README step 1-1](../README.md#source-setup), then return here. Run from that clone's root:

```bash
python3.13 -m venv src/agent/.venv &&
source src/agent/.venv/bin/activate &&
python -m pip install -r requirements.txt &&
python -m unittest discover -s tests -v
```

Do not continue to Azure operations until the result is **`OK`**. The tests cover both languages and ensure that English translations retain the same policy IDs, monetary rules, and frozen case contracts.

Use the pinned package versions. `requirements.lock.txt` is the validated dependency snapshot; do not upgrade frameworks, extensions, or SDKs indiscriminately during a workshop.

Installation references: [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli), [azd](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd), and the [Hosted Agent quickstart](https://learn.microsoft.com/azure/foundry/agents/quickstarts/quickstart-hosted-agent).

## Safe preparation with an existing foundation

1. Prepare this folder's `.env` with `LAB_LANGUAGE=en`, unused preparation names, and actual resource/deployment values.
2. Complete [README step 1-3](../README.md#login), including both CLI sign-ins and the identity checks. Keep the configured subscription explicit.
3. Run `python scripts/workshop.py preflight --allow-missing-models`.
4. If the four candidates are missing, use `python scripts/workshop.py prepare-models` to create only the owned, prefixed deployments.
5. Run `python scripts/workshop.py preflight` again and require `language: en` and `missing_models: []`.
6. Run `python scripts/workshop.py calibrate` and require **`Judge calibration passed`**. README step 5 repeats this check in each participant workspace; matching completed calibration is reused. The two fixed examples are not part of the 64 candidate responses.
7. For a class, use the [separate rehearsal folder](#rehearsal-workspace), then hand off to participants. For one-off self-study, stay here and continue at [README step 1-4](../README.md#project-binding): bind → IQ retrieval → local smoke → deployment/access → hosted smoke. Do not run both paths.

If evaluation reports missing App Insights `ResourceId` metadata, inspect connection ownership first. Only an authorized instructor may use `repair-observability --confirm` on a dedicated workshop connection. Do not modify a shared connection to make an example work.

An execution failure can be retried with preserved inputs and evidence. A low quality score is not a reason to use `--retry-failed`, lower the rubric, or substitute a different model.

<details>
<summary>What bind does — explanation, not another step to execute</summary>

`bind` uses the provided `azure.yaml` to create or reuse this folder's azd environment and set its team-specific service/agent name. It does not reprovision the Foundry project. Do not run `azd ai agent init` again, copy another folder's state, or ignore subscription/project conflicts.

Keep the local server in a trusted development environment, never expose it publicly, and stop it after the local check. Local and platform-authenticated hosted endpoints have different security boundaries.

</details>

<a id="rehearsal"></a>

## Rehearsal timing

| Time | Participant steps | Observable outcome |
|---|---|---|
| 00–10 min | 1. Prepare | Offline tests, two sign-ins, identity check, preflight, and binding |
| 10–25 min | 2. Knowledge | Actual English document IDs and IQ activity |
| 25–40 min | 3–4. Local and hosted | Real answers in both environments |
| 40–55 min | 5. Baseline | 24 actual English responses and completed native evaluation |
| 55–70 min | 6. Review | A real trace and reviewed regression case |
| 70–85 min | 7. V2 | New version, same 24 dev cases |
| 85–100 min | 8. Holdout | Frozen candidate and 16 responses |
| 100–110 min | 9. Observe | 64 responses, 64 traces, and complete lineage |
| 110–115 min | 10. Cleanup | Only the folder's owned objects removed |
| 115–120 min | Buffer | Evaluation and telemetry ingestion delay |

The 120 minutes assume a prepared environment. Rehearse model deployment, cold starts, RBAC propagation, response generation, evaluator completion, and telemetry ingestion. Do not shorten an overrun by omitting a model, retrieval, or evaluation and calling the workshop complete.

## Cleanup and maintenance

Review `cleanup --dry-run` before confirming. Never delete an entire shared resource group or run `azd down` against shared resources. Retained Search and logging resources may continue to cost money.

Before changing Foundry agent code or instructions, read the `microsoft-foundry` skill guidance. Keep synthetic-data-only boundaries, the configured subscription, model identities, prompt/data versions, and trace lineage. Run the offline tests before cloud operations.

Actual English cloud results belong in [the English evaluation explanation](validation.en.md), separately from the [Korean experiment](validation.ko.md). A translated question is not a newly independent holdout case.
