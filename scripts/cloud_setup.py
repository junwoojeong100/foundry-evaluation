import json
import os
import uuid
from typing import Any

import httpx
import yaml
from azure.ai.projects import AIProjectClient
from azure.core.exceptions import ResourceNotFoundError
from dotenv import set_key

from common import (
    FOUNDRY_DIR, REPO_ROOT, RESULTS_DIR, authenticate, az, azd, digest,
    load_state, read_json, runtime_env, save_state, write_json,
)
from contracts import MODEL_SPECS
from knowledge import SEARCH_API_VERSION, SEARCH_SCOPE
from settings import RuntimeConfig, credential, required

ROLE_SEARCH_READER = "1407120a-92aa-4202-b7e9-c0e197c71c8f"
ROLE_COGNITIVE_USER = "a97b65f3-24c7-4388-baec-2e87135dc908"
ROLE_OPENAI_USER = "5e0bd9bd-7b93-4f28-af87-19fc36ad61bd"


def resources() -> dict[str, Any]:
    authenticate()
    group = required("AZURE_RESOURCE_GROUP")
    account = az("cognitiveservices", "account", "show", "--name", required("AZURE_AI_ACCOUNT_NAME"), "--resource-group", group)
    projects = az("resource", "list", "--resource-group", group, "--resource-type", "Microsoft.CognitiveServices/accounts/projects")
    expected = f"{account['name']}/{required('AZURE_AI_PROJECT_NAME')}"
    matches = [project for project in projects if project["name"] == expected]
    if len(matches) != 1:
        raise ValueError("Expected exactly one matching Foundry project in the selected resource group.")
    project = az("resource", "show", "--ids", matches[0]["id"], "--api-version", "2025-06-01")
    endpoint = project["properties"]["endpoints"]["AI Foundry API"].rstrip("/")
    if endpoint != RuntimeConfig.from_env().project_endpoint:
        raise ValueError("Configured project endpoint does not match Azure's returned endpoint.")
    model_endpoint = account["properties"]["endpoints"]["Azure OpenAI Legacy API - Latest moniker"].rstrip("/")
    if model_endpoint != RuntimeConfig.from_env().model_endpoint:
        raise ValueError("Model endpoint must belong to the selected project's parent Foundry account.")
    search = az("search", "service", "show", "--name", required("AZURE_SEARCH_NAME"), "--resource-group", group)
    app_insights = az("resource", "show", "--resource-group", group, "--resource-type", "Microsoft.Insights/components", "--name", required("AZURE_APPLICATION_INSIGHTS_NAME"), "--api-version", "2020-02-02")
    return {"account": account, "project": project, "search": search, "app_insights": app_insights}


def deployments() -> list[dict[str, Any]]:
    return az(
        "cognitiveservices", "account", "deployment", "list",
        "--name", required("AZURE_AI_ACCOUNT_NAME"),
        "--resource-group", required("AZURE_RESOURCE_GROUP"),
    )


def verify_deployment(item: dict[str, Any], key: str) -> None:
    model_name, model_version = MODEL_SPECS[key]
    actual = item["properties"]["model"]
    if (actual["name"], actual["version"]) != (model_name, model_version):
        raise ValueError(f"Deployment {item['name']} is not {model_name}/{model_version}. No substitution is allowed.")
    if item["properties"]["provisioningState"] != "Succeeded":
        raise ValueError(f"Deployment {item['name']} is not ready.")


def preflight(allow_missing: bool = False) -> dict[str, Any]:
    config = RuntimeConfig.from_env()
    found = resources()
    catalog = az("cognitiveservices", "model", "list", "--location", found["account"]["location"])
    usage = az("cognitiveservices", "usage", "list", "--location", found["account"]["location"])
    deployed = {item["name"]: item for item in deployments()}
    model_records = []
    missing = []
    for key, (name, version) in MODEL_SPECS.items():
        entries = [entry["model"] for entry in catalog if entry["model"]["name"] == name and entry["model"]["version"] == version]
        if not entries:
            raise ValueError(f"{name}/{version} is unavailable in the selected region.")
        model = entries[0]
        if model.get("capabilities", {}).get("chatCompletion") != "true":
            raise ValueError(f"{name} has no Chat Completions capability in this region.")
        sku = next((item for item in model["skus"] if item["name"] == "GlobalStandard"), None)
        if sku is None:
            raise ValueError(f"{name} has no GlobalStandard SKU.")
        quota = next((item for item in usage if item["name"]["value"] == sku["usageName"]), None)
        if quota is None:
            raise ValueError(f"No quota record for {name}.")
        deployment = deployed.get(config.deployments[key])
        if deployment:
            verify_deployment(deployment, key)
        else:
            missing.append(key)
        model_records.append({
            "key": key, "model": name, "version": version,
            "deployment": config.deployments[key],
            "deployed": deployment is not None,
            "available_quota": quota["limit"] - quota["currentValue"],
            "sku": "GlobalStandard",
        })
    auxiliary = deployed.get(required("LAB_AUX_DEPLOYMENT"))
    if not auxiliary or auxiliary["properties"]["provisioningState"] != "Succeeded":
        raise ValueError("The fixed auxiliary planner/judge deployment is missing.")
    if auxiliary["properties"]["model"]["name"] != required("LAB_AUX_MODEL"):
        raise ValueError("Auxiliary model identity mismatch.")
    with AIProjectClient(endpoint=config.project_endpoint, credential=credential()) as project:
        if not project.telemetry.get_application_insights_connection_string():
            raise ValueError("Application Insights is not connected to this project.")
        insights = [item for item in project.connections.list() if "insight" in str(item.type).lower()]
        if len(insights) != 1:
            raise ValueError("Exactly one Application Insights connection is required.")
        resource_id = insights[0].metadata.get("ResourceId", "")
        if resource_id.casefold() != found["app_insights"]["id"].casefold():
            raise ValueError("App Insights ResourceId metadata is missing/mismatched. Inspect repair-observability before evaluating.")
    result = {
        "subscription": required("AZURE_SUBSCRIPTION_ID"),
        "tenant": required("AZURE_TENANT_ID"),
        "project_id": found["project"]["id"],
        "region": found["account"]["location"],
        "search_id": found["search"]["id"],
        "app_insights_id": found["app_insights"]["id"],
        "models": model_records,
        "auxiliary_model": auxiliary["properties"]["model"],
        "missing_models": missing,
    }
    write_json(RESULTS_DIR / "preflight.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if missing and not allow_missing:
        raise ValueError(f"Missing deployments: {missing}. Run prepare-models; no automatic fallback.")
    return result


def prepare_models() -> None:
    result = preflight(allow_missing=True)
    state = load_state()
    for model in result["models"]:
        if model["deployed"]:
            continue
        if model["available_quota"] < 50:
            raise ValueError(f"Insufficient quota for {model['model']}; 50 units required.")
        if not model["deployment"].startswith(state["scope"]["prefix"] + "-"):
            raise ValueError("New deployments must use the owned workshop prefix.")
        print(f"Creating {model['deployment']} -> {model['model']} ({model['version']})")
        item = az(
            "cognitiveservices", "account", "deployment", "create",
            "--name", required("AZURE_AI_ACCOUNT_NAME"), "--resource-group", required("AZURE_RESOURCE_GROUP"),
            "--deployment-name", model["deployment"], "--model-name", model["model"],
            "--model-version", model["version"], "--model-format", "OpenAI",
            "--sku-name", "GlobalStandard", "--sku-capacity", "50",
        )
        state["owned_models"].append({"name": model["deployment"], "id": item["id"], "model": model["model"], "version": model["version"]})
        save_state(state)
        verify_deployment(item, model["key"])
    preflight()


def ensure_role(principal_id: str, scope_id: str, role_id: str) -> None:
    roles = az("role", "assignment", "list", "--scope", scope_id, "--include-inherited")
    if any(role["principalId"] == principal_id and role["roleDefinitionId"].endswith(role_id) for role in roles):
        return
    state = load_state()
    assignment_name = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{scope_id}/{principal_id}/{role_id}"))
    created = az(
        "role", "assignment", "create", "--name", assignment_name,
        "--assignee-object-id", principal_id, "--assignee-principal-type", "ServicePrincipal",
        "--role", role_id, "--scope", scope_id,
    )
    state["owned_roles"].append(created["id"])
    save_state(state)


def search_client(config: RuntimeConfig) -> httpx.Client:
    token = credential().get_token(SEARCH_SCOPE)
    return httpx.Client(
        base_url=config.search_endpoint + "/",
        headers={"Authorization": f"Bearer {token.token}"},
        params={"api-version": SEARCH_API_VERSION},
        timeout=120, follow_redirects=False,
    )


def prepare_iq() -> None:
    config = RuntimeConfig.from_env()
    found = resources()
    state = load_state()
    documents = read_json(REPO_ROOT / "data" / "policies.json")
    corpus_hash = digest(documents)
    if state.get("corpus_hash") not in (None, corpus_hash):
        raise ValueError("The knowledge corpus changed; create a new workshop prefix for a new experiment.")
    ensure_role(found["search"]["identity"]["principalId"], found["account"]["id"], ROLE_COGNITIVE_USER)
    state = load_state()
    definitions = [
        (f"indexes/{config.index_name}", {
            "name": config.index_name,
            "fields": [
                {"name": "id", "type": "Edm.String", "key": True, "filterable": True},
                {"name": "title", "type": "Edm.String", "searchable": True, "retrievable": True},
                {"name": "content", "type": "Edm.String", "searchable": True, "retrievable": True},
            ],
            "semantic": {"configurations": [{
                "name": "policy-semantic",
                "prioritizedFields": {
                    "titleField": {"fieldName": "title"},
                    "prioritizedContentFields": [{"fieldName": "content"}],
                },
            }]},
        }),
        (f"knowledgesources/{config.source_name}", {
            "name": config.source_name, "kind": "searchIndex",
            "searchIndexParameters": {
                "searchIndexName": config.index_name,
                "semanticConfigurationName": "policy-semantic",
                "sourceDataFields": [{"name": field} for field in ("id", "title", "content")],
            },
        }),
        (f"knowledgebases/{config.kb_name}", {
            "name": config.kb_name,
            "description": "Synthetic Korean policy workshop. No customer data.",
            "knowledgeSources": [{"name": config.source_name}],
            "outputMode": "extractiveData",
            "retrievalReasoningEffort": {"kind": "low"},
            "models": [{
                "kind": "azureOpenAI",
                "azureOpenAIParameters": {
                    "resourceUri": found["account"]["properties"]["endpoints"]["Azure OpenAI Legacy API - Latest moniker"],
                    "deploymentId": required("LAB_AUX_DEPLOYMENT"),
                    "modelName": required("LAB_AUX_MODEL"),
                },
            }],
        }),
    ]
    with search_client(config) as client:
        for path, body in definitions:
            existing = client.get(path)
            if existing.status_code == 200:
                if path not in state["owned_search_paths"]:
                    raise ValueError(f"Refusing to overwrite an unowned Search object: {path}")
                print(f"Reusing owned object: {path}")
            elif existing.status_code == 404:
                created = client.put(path, headers={"If-None-Match": "*"}, json=body)
                created.raise_for_status()
                state["owned_search_paths"].append(path)
                save_state(state)
                print(f"Created: {path}")
            else:
                existing.raise_for_status()
            if path.startswith("indexes/"):
                uploaded = client.post(
                    f"{path}/docs/index",
                    json={"value": [{"@search.action": "mergeOrUpload", **doc} for doc in documents]},
                )
                uploaded.raise_for_status()
                statuses = uploaded.json().get("value", [])
                if len(statuses) != len(documents) or any(not item.get("status") for item in statuses):
                    raise ValueError("Search returned a partial document upload failure.")
        state["corpus_hash"] = corpus_hash
        save_state(state)
    print(f"Foundry IQ ready: {config.kb_name}; {len(documents)} synthetic documents.")


def repair_observability(confirm: bool) -> None:
    config = RuntimeConfig.from_env()
    found = resources()
    with AIProjectClient(endpoint=config.project_endpoint, credential=credential()) as project:
        connections = [
            item for item in project.connections.list()
            if "insight" in str(item.type).lower()
        ]
    if len(connections) != 1:
        raise ValueError("Select exactly one App Insights connection before repairing metadata.")
    connection = connections[0]
    if not connection.id.startswith(found["project"]["id"] + "/connections/"):
        raise ValueError("App Insights connection belongs to a different project.")
    uri = f"https://management.azure.com{connection.id}?api-version=2025-10-01-preview"
    current = az("rest", "--method", "get", "--uri", uri)
    metadata = current["properties"].get("metadata", {})
    desired = found["app_insights"]["id"]
    existing = metadata.get("ResourceId")
    if existing:
        if existing.casefold() != desired.casefold():
            raise ValueError("Existing ResourceId points at another App Insights resource.")
        print("App Insights ResourceId metadata is already correct.")
        return
    print(f"Add ResourceId metadata only: {connection.id} -> {desired}")
    if not confirm:
        raise ValueError("Use repair-observability --confirm to apply this metadata-only change.")
    body = {"properties": {
        "authType": current["properties"]["authType"],
        "metadata": {**metadata, "ResourceId": desired},
    }}
    az("rest", "--method", "patch", "--uri", uri, "--body", json.dumps(body))
    verified = az("rest", "--method", "get", "--uri", uri)
    if verified["properties"]["metadata"].get("ResourceId", "").casefold() != desired.casefold():
        raise ValueError("The App Insights metadata repair did not persist.")
    for field in ("authType", "category", "target"):
        if verified["properties"].get(field) != current["properties"].get(field):
            raise ValueError(f"Unexpected change to App Insights connection {field}.")
    state = load_state()
    state.setdefault("connection_repairs", []).append({
        "connection_id": connection.id,
        "previous_metadata": metadata,
        "added_resource_id": desired,
        "retained_after_cleanup": True,
    })
    save_state(state)
    print("ResourceId metadata verified. Endpoint and credentials were not changed.")


def bind() -> None:
    config = RuntimeConfig.from_env()
    found = resources()
    auth = azd("auth", "status")
    if auth.get("status") != "authenticated" or auth.get("email", "").casefold() != required("AZURE_EXPECTED_USERNAME").casefold():
        raise ValueError("azd must be logged in to the requested account; sign in manually.")
    state = load_state()
    with AIProjectClient(endpoint=config.project_endpoint, credential=credential()) as project:
        try:
            project.agents.get(config.agent_name)
        except ResourceNotFoundError:
            state["agent_reserved_absent"] = config.agent_name
            save_state(state)
        else:
            if state.get("agent_owned") != config.agent_name:
                raise ValueError("This agent name already exists and is not owned by this workshop.")
    manifest_path = REPO_ROOT / "azure.yaml"
    if not manifest_path.exists():
        azd(
            "ai", "agent", "init", "--no-prompt", "--src", "./src/agent",
            "--agent-name", config.agent_name, "--project-id", found["project"]["id"],
            "--model-deployment", required("LAB_AUX_DEPLOYMENT"), "--deploy-mode", "code",
            "--runtime", "python_3_13", "--entry-point", "main.py", "--protocol", "invocations",
            json_output=False,
        )
    else:
        manifest = yaml.safe_load(manifest_path.read_text())
        services = manifest["services"]
        candidates = [name for name, service in services.items() if service.get("host") == "azure.ai.agent"]
        if len(candidates) != 1:
            raise ValueError("bind supports exactly one workshop agent service.")
        old_name = candidates[0]
        service = services.pop(old_name)
        if service.get("project", "").removeprefix("./") != "src/agent":
            raise ValueError("Unexpected agent source directory.")
        service["name"] = config.agent_name
        services[config.agent_name] = service
        manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
        if not (REPO_ROOT / ".azure" / "config.json").exists():
            azd("env", "new", config.prefix, "--subscription", required("AZURE_SUBSCRIPTION_ID"), "--location", found["account"]["location"], "--no-prompt", json_output=False)
        else:
            values = azd("env", "get-values")
            if values.get("AZURE_SUBSCRIPTION_ID") not in (None, required("AZURE_SUBSCRIPTION_ID")):
                raise ValueError("Existing azd environment targets a different subscription.")
            if values.get("FOUNDRY_PROJECT_ENDPOINT") not in (None, config.project_endpoint):
                raise ValueError("Existing azd environment targets a different project.")
    values = {
        **runtime_env(),
        "AZURE_SUBSCRIPTION_ID": required("AZURE_SUBSCRIPTION_ID"),
        "AZURE_TENANT_ID": required("AZURE_TENANT_ID"),
        "AZURE_LOCATION": found["account"]["location"],
        "AZURE_AI_PROJECT_ID": found["project"]["id"],
    }
    for name, value in values.items():
        azd("env", "set", name, value, json_output=False)
    print(f"Bound {config.agent_name} to {found['project']['id']}. No new project was provisioned.")


def set_prompt(version: str) -> None:
    if version not in {"v1", "v2"}:
        raise ValueError("Unknown prompt version.")
    set_key(REPO_ROOT / ".env", "LAB_PROMPT_VERSION", version, quote_mode="never")
    os.environ["LAB_PROMPT_VERSION"] = version
    azd("env", "set", "LAB_PROMPT_VERSION", version, json_output=False)
    print(f"Selected {version}; run azd deploy to create a new immutable hosted version.")


def agent_principal(record: dict[str, Any], override: str | None = None) -> str:
    discovered = (record.get("instance_identity") or {}).get("principal_id")
    if override and discovered and override != discovered:
        raise ValueError("The supplied principal ID is not this agent's instance identity.")
    principal_id = discovered or override
    if not principal_id:
        raise ValueError("Agent principal ID was not returned. Use the agent Identity pane's object ID with --principal-id.")
    uuid.UUID(principal_id)
    return principal_id


def grant_agent_access(principal_id: str | None = None) -> None:
    config = RuntimeConfig.from_env()
    found = resources()
    with AIProjectClient(endpoint=config.project_endpoint, credential=credential()) as project:
        agent = project.agents.get(config.agent_name)
        record = agent.as_dict()
    write_json(RESULTS_DIR / "hosted-agent.json", record)
    principal_id = agent_principal(record, principal_id)
    state = load_state()
    if state.get("agent_owned") != config.agent_name and state.get("agent_reserved_absent") != config.agent_name:
        raise ValueError("Agent ownership has not been established by bind.")
    ensure_role(principal_id, found["search"]["id"], ROLE_SEARCH_READER)
    ensure_role(principal_id, found["account"]["id"], ROLE_OPENAI_USER)
    state = load_state()
    state["agent_owned"] = config.agent_name
    state["agent_principal_id"] = principal_id
    save_state(state)
    print(f"Search read and Foundry model inference access configured for {config.agent_name}.")


def cleanup_plan(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "agent": state.get("agent_owned"),
        "models": [dict(model) for model in state["owned_models"]],
        "search_objects": list(reversed(state["owned_search_paths"])),
        "role_assignments": list(state["owned_roles"]),
        "preserved": ["existing Foundry project", "existing Search service", "existing App Insights", "evaluation evidence"],
    }


def cleanup(confirm: bool) -> None:
    authenticate()
    config = RuntimeConfig.from_env()
    state = load_state()
    plan = cleanup_plan(state)
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    if not confirm:
        return
    write_json(RESULTS_DIR / "cleanup-plan.json", plan)
    if state.get("agent_owned"):
        if state["agent_owned"] != config.agent_name:
            raise ValueError("Agent ownership mismatch.")
        azd("ai", "agent", "delete", config.agent_name, "--force", "--no-prompt", json_output=False)
        state.pop("agent_owned")
        save_state(state)
    with search_client(config) as client:
        for path in list(reversed(state["owned_search_paths"])):
            if path.split("/", 1)[1] not in {config.kb_name, config.source_name, config.index_name}:
                raise ValueError("Unexpected Search cleanup path.")
            deleted = client.delete(path)
            if deleted.status_code != 404:
                deleted.raise_for_status()
            state["owned_search_paths"].remove(path)
            save_state(state)
    current = {item["name"]: item for item in deployments()}
    for model in list(state["owned_models"]):
        if not model["name"].startswith(config.prefix + "-"):
            raise ValueError("Unexpected deployment cleanup name.")
        if model["name"] in current:
            item = current[model["name"]]
            if item["id"] != model["id"] or item["properties"]["model"]["name"] != model["model"] or item["properties"]["model"]["version"] != model["version"]:
                raise ValueError("Deployment changed since creation; refusing cleanup.")
            az("cognitiveservices", "account", "deployment", "delete", "--name", required("AZURE_AI_ACCOUNT_NAME"), "--resource-group", required("AZURE_RESOURCE_GROUP"), "--deployment-name", model["name"])
        state["owned_models"].remove(model)
        save_state(state)
    for assignment in list(state["owned_roles"]):
        az("role", "assignment", "delete", "--ids", assignment)
        state["owned_roles"].remove(assignment)
        save_state(state)
    state["cleanup_complete"] = True
    save_state(state)
    write_json(RESULTS_DIR / "cleanup.json", {"plan": plan, "completed": True})
    print("Owned workshop resources removed; shared infrastructure and evidence preserved.")


def check_cleanup() -> dict[str, Any]:
    config = RuntimeConfig.from_env()
    found = resources()
    plan = read_json(RESULTS_DIR / "cleanup.json")["plan"]
    if plan["agent"]:
        with AIProjectClient(endpoint=config.project_endpoint, credential=credential()) as project:
            try:
                project.agents.get(plan["agent"])
            except ResourceNotFoundError:
                pass
            else:
                raise ValueError("The temporary hosted agent still exists.")
    active_models = {item["name"] for item in deployments()}
    if any(model["name"] in active_models for model in plan["models"]):
        raise ValueError("A temporary model deployment still exists.")
    with search_client(config) as client:
        for path in plan["search_objects"]:
            response = client.get(path)
            if response.status_code == 200:
                raise ValueError(f"A temporary Search object still exists: {path}")
            if response.status_code != 404:
                response.raise_for_status()
    for assignment in plan["role_assignments"]:
        assignment_scope = assignment.rsplit("/providers/Microsoft.Authorization/roleAssignments/", 1)[0]
        roles = az("role", "assignment", "list", "--scope", assignment_scope, "--include-inherited")
        if any(role["id"].casefold() == assignment.casefold() for role in roles):
            raise ValueError("A temporary role assignment still exists.")
    with AIProjectClient(endpoint=config.project_endpoint, credential=credential()) as project:
        connections = [item for item in project.connections.list() if "insight" in str(item.type).lower()]
    if len(connections) != 1 or connections[0].metadata.get("ResourceId", "").casefold() != found["app_insights"]["id"].casefold():
        raise ValueError("The non-destructive App Insights metadata correction was not retained.")
    result = {
        "temporary_hosted_agent_absent": True,
        "temporary_model_deployments_absent": len(plan["models"]),
        "temporary_search_objects_absent": len(plan["search_objects"]),
        "temporary_role_assignments_absent": len(plan["role_assignments"]),
        "existing_foundry_project_preserved": True,
        "existing_search_service_preserved": True,
        "existing_application_insights_preserved": True,
        "existing_auxiliary_model_preserved": required("LAB_AUX_DEPLOYMENT") in active_models,
        "app_insights_metadata_correction_retained": True,
    }
    if not result["existing_auxiliary_model_preserved"]:
        raise ValueError("The pre-existing auxiliary deployment is missing.")
    write_json(RESULTS_DIR / "cleanup-check.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result
