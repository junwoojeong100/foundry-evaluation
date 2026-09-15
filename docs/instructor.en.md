# Instructor prerequisites for the English workshop

Participants follow [README.en.md](../README.en.md#start). Keep infrastructure creation and recording production out of their 120-minute path. Use [new-environment setup](environment.en.md) when the required Azure foundation does not yet exist.

## What to hand to each team

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

## Separate rehearsal from participant execution

Use a separate folder, prefix, and agent name for rehearsal. Do not create a participant's KB, source, index, or agent in advance under their reserved names; a fresh participant folder will correctly refuse to overwrite unowned objects.

If model deployments are shared within the approved workshop foundation, keep their **actual deployment names** in `MODEL_*_DEPLOYMENT`. Do not rename a deployment in `.env` to a resource that does not exist.

Do not copy someone else's `.azure`, `.foundry` ownership files, authentication cache, or results to bypass a guard. A participant's cleanup deletes only objects recorded as owned by that folder. The instructor remains responsible for prepared models and foundation-service costs.

## Access boundaries

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

## Install and verify locally

From the rehearsal repository root:

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

1. Prepare the rehearsal `.env` with `LAB_LANGUAGE=en` and actual resource/deployment values.
2. Complete [README step 1-3](../README.en.md#login), including both CLI sign-ins and the identity checks. Keep the configured subscription explicit.
3. Run `python scripts/workshop.py preflight --allow-missing-models`.
4. If the four candidates are missing, use `python scripts/workshop.py prepare-models` to create only the owned, prefixed deployments.
5. Run `python scripts/workshop.py preflight` again and require `language: en` and `missing_models: []`.
6. Bind the project, create English IQ objects, and complete actual local and hosted smoke invocations using the README order.
7. Run `python scripts/workshop.py calibrate` before interpreting native scores. These two fixed English examples are not part of the 64 candidate responses.

If evaluation reports missing App Insights `ResourceId` metadata, inspect connection ownership first. Only an authorized instructor may use `repair-observability --confirm` on a dedicated workshop connection. Do not modify a shared connection to make an example work.

An execution failure can be retried with preserved inputs and evidence. A low quality score is not a reason to use `--retry-failed`, lower the rubric, or substitute a different model.

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
