"""Provision only the new, explicitly owned workshop environment."""

import argparse
import base64
import hashlib
import json
import os
import shlex
import subprocess
import sys
import time
import uuid
from pathlib import Path
from urllib.parse import urlencode

from dotenv import dotenv_values, set_key

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "foundry-evaluation"
FOUNDRY_API = "2025-06-01"
CONNECTION_API = "2025-04-01-preview"
SEARCH_API = "2026-03-01-preview"
ROLE_FOUNDRY_USER = "53ca6127-db72-4b80-b1b0-d745d6d5456d"
ROLE_OPENAI_USER = "5e0bd9bd-7b93-4f28-af87-19fc36ad61bd"
ROLE_SEARCH_SERVICE = "7ca78c08-252a-4471-8644-bb5ff32d4ba0"
ROLE_SEARCH_DATA = "8ebe5a00-799e-43f5-93ac-243d3dce84a7"
ROLE_LOG_READER = "73c42c96-874c-492b-b04d-ab87d138a893"
AUXILIARY_VERSION = "2026-03-17"


def owned_tags(run: str) -> dict[str, str]:
    return {
        "workshop": REPOSITORY, "cleanup-scope": "exclusive",
        "purpose": "synthetic-data-only", "run": run,
    }


def check_group_ownership(group: dict, config: dict, recorded_id: str | None):
    if not recorded_id or group.get("id", "").casefold() != recorded_id.casefold():
        raise ValueError("This run has no creation record for the resource group.")
    if group["name"] != config["resource_group"] or group["location"] != "swedencentral":
        raise ValueError("Resource group name or region does not match the requested scope.")
    if any((group.get("tags") or {}).get(key) != value for key, value in owned_tags(config["run_id"]).items()):
        raise ValueError("Resource group ownership tags changed; do not modify it.")


def principal_from_access_token(token: str, tenant: str, username: str) -> str:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Azure CLI did not return a JWT access token.")
    payload = parts[1]
    claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    if claims["tid"] != tenant:
        raise ValueError("The issued ARM token belongs to a different tenant.")
    claimed_username = claims.get("upn") or claims.get("preferred_username")
    if claimed_username and claimed_username.casefold() != username.casefold():
        raise ValueError("The issued ARM token belongs to a different user.")
    principal = claims["oid"]
    uuid.UUID(principal)
    return principal


class Provisioner:
    def __init__(self, directory: Path):
        self.directory = directory.resolve()
        self.config = json.loads((directory / "config.json").read_text())
        self.workspace = Path(self.config["workspace"])
        self.state_path = directory / "infrastructure-state.json"
        self.state = json.loads(self.state_path.read_text()) if self.state_path.exists() else {
            "run": self.config["run_id"], "resources": {}, "roles": [],
        }
        if self.state["run"] != self.config["run_id"]:
            raise ValueError("Infrastructure evidence belongs to a different run.")
        self.group_id = f"/subscriptions/{self.config['subscription']}/resourceGroups/{self.config['resource_group']}"

    def save(self):
        temporary = self.state_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.state, ensure_ascii=False, indent=2) + "\n")
        os.chmod(temporary, 0o600)
        temporary.replace(self.state_path)

    def az(self, *args: str):
        command = [
            "az", *args, "--subscription", self.config["subscription"],
            "--only-show-errors", "--output", "json",
        ]
        print("$ " + shlex.join(command), flush=True)
        result = subprocess.run(command, capture_output=True, text=True, timeout=1800, check=False)
        if result.returncode:
            raise RuntimeError(f"Azure command failed ({result.returncode}): {result.stderr}\n{result.stdout}")
        return json.loads(result.stdout) if result.stdout.strip() else None

    def identity(self):
        account = self.az("account", "show")
        if (
            account["id"] != self.config["subscription"]
            or account["tenantId"] != self.config["tenant"]
            or account["user"]["name"].casefold() != self.config["username"].casefold()
            or account["state"] != "Enabled"
        ):
            raise ValueError("Azure identity does not match the explicitly requested account and scope.")
        token = self.az("account", "get-access-token", "--resource", "https://management.azure.com/")
        self.state["principal_id"] = principal_from_access_token(
            token["accessToken"], self.config["tenant"], self.config["username"],
        )
        self.state["identity_verified"] = True
        self.save()
        print(json.dumps({
            "requested_account_matches": True, "configured_subscription_matches": True,
            "configured_tenant_matches": True, "subscription_state": account["state"],
            "default_subscription_changed": False,
        }, indent=2))

    def guard(self):
        if not self.state.get("identity_verified"):
            raise ValueError("Verify the requested identity before creating any resource.")
        account = self.az("account", "show")
        if account["id"] != self.config["subscription"] or account["user"]["name"].casefold() != self.config["username"].casefold():
            raise ValueError("The executing identity changed.")
        group = self.az("group", "show", "--name", self.config["resource_group"])
        check_group_ownership(group, self.config, self.state.get("group_id"))

    def ownership(self, preserve_existing: bool = False):
        groups = self.az("group", "list")
        candidates = [
            group for group in groups
            if group["name"] != self.config["resource_group"]
            and (
                (group.get("tags") or {}).get("workshop") == REPOSITORY
                or REPOSITORY in group["name"]
            )
        ]
        eligible = [
            group["name"] for group in candidates
            if (group.get("tags") or {}).get("workshop") == REPOSITORY
            and (group.get("tags") or {}).get("cleanup-scope") == "exclusive"
        ]
        report = {
            "dedicated_old_groups": eligible,
            "unverified_candidates": [group["name"] for group in candidates if group["name"] not in eligible],
            "shared_previous_environment_preserved": self.config["old_resource_group"],
            "other_repository_groups_preserved": [
                group["name"] for group in groups
                if (group.get("tags") or {}).get("workshop") == "microsoft-foundry-v2-labs"
            ],
            "groups_deleted": [],
            "existing_groups_explicitly_preserved": preserve_existing,
        }
        self.state["ownership_audit"] = report
        self.save()
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if candidates and not preserve_existing:
            raise ValueError("Inspect the exact candidate inventories before any group deletion.")

    def group(self):
        if not self.state.get("identity_verified") or "ownership_audit" not in self.state:
            raise ValueError("Identity and old-group ownership inspection must precede creation.")
        exists = self.az("group", "exists", "--name", self.config["resource_group"])
        if exists:
            self.guard()
            print("Reusing only the group whose creation is recorded by this run.")
            return
        group = self.az(
            "group", "create", "--name", self.config["resource_group"], "--location", "swedencentral",
            "--tags", *(f"{key}={value}" for key, value in owned_tags(self.config["run_id"]).items()),
        )
        self.state["group_id"] = group["id"]
        self.save()
        check_group_ownership(group, self.config, self.state["group_id"])
        print(json.dumps({
            "name": group["name"], "location": group["location"], "tags": group["tags"],
            "state": group["properties"]["provisioningState"],
        }, indent=2))

    def get(self, key: str):
        resource = self.state["resources"][key]
        return self.az(
            "rest", "--method", "get", "--uri",
            f"https://management.azure.com{resource['id']}?api-version={resource['api_version']}",
        )

    def wait_ready(self, key: str, result: dict):
        if not key.endswith("-connection"):
            deadline = time.monotonic() + (1800 if key == "search" else 900)
            while str(result.get("properties", {}).get("provisioningState", "")).casefold() != "succeeded":
                status = result.get("properties", {}).get("provisioningState")
                if str(status).casefold() in {"failed", "canceled", "cancelled"}:
                    raise RuntimeError(f"{key} provisioning failed: {status}")
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"{key} local wait expired; Azure's last state is {status}. Resume the same resource, do not recreate it.")
                print(f"{key}: actual provisioning state {status}; waiting", flush=True)
                time.sleep(10)
                result = self.get(key)
        print(json.dumps({
            "resource": key, "name": result["name"], "location": result.get("location"),
            "state": result.get("properties", {}).get("provisioningState", "connection-created"),
        }, indent=2))
        return result

    def put(self, key: str, suffix: str, version: str, body: dict):
        self.guard()
        resource_id = self.group_id + "/providers/" + suffix
        if key in self.state["resources"]:
            if self.state["resources"][key]["id"] != resource_id:
                raise ValueError("A recorded resource ID changed.")
            existing = self.get(key)
            print(json.dumps({"resource": key, "reused_owned_resource": existing["name"]}))
            return self.wait_ready(key, existing)
        body_path = self.directory / f"{key}-request.json"
        body_path.write_text(json.dumps(body))
        os.chmod(body_path, 0o600)
        try:
            result = self.az(
                "rest", "--method", "put", "--uri",
                f"https://management.azure.com{resource_id}?api-version={version}",
                "--body", "@" + str(body_path),
            )
        finally:
            if key == "insights-connection":
                body_path.unlink()
        if not result or result.get("id", "").casefold() != resource_id.casefold():
            raise ValueError("Azure did not return the expected resource ID; inspect the actual operation.")
        self.state["resources"][key] = {
            "id": result["id"], "api_version": version,
            "body_sha256": hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest(),
        }
        self.save()
        return self.wait_ready(key, result)

    def role(self, principal: str, principal_type: str, resource_key: str, role_id: str):
        self.guard()
        scope = self.state["resources"][resource_key]["id"]
        assignments = self.az("role", "assignment", "list", "--scope", scope, "--include-inherited")
        if any(
            item["principalId"] == principal and item["roleDefinitionId"].endswith(role_id)
            for item in assignments
        ):
            print(json.dumps({"scope_resource": resource_key, "role": role_id, "already_assigned": True}))
            return
        name = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{scope}/{principal}/{role_id}"))
        assignment = self.az(
            "role", "assignment", "create", "--name", name,
            "--assignee-object-id", principal, "--assignee-principal-type", principal_type,
            "--role", role_id, "--scope", scope,
        )
        self.state["roles"].append(assignment["id"])
        self.save()
        print(json.dumps({"scope_resource": resource_key, "principal_type": principal_type, "role": role_id, "created": True}))

    def model_capacity(self):
        sys.path.insert(0, str(self.workspace / "src/agent"))
        from contracts import MODEL_SPECS

        env = dotenv_values(self.workspace / ".env")
        models = [(name, version, 50) for name, version in MODEL_SPECS.values()]
        models.append((env["LAB_AUX_MODEL"], AUXILIARY_VERSION, 100))
        report = []
        for name, version, required_capacity in models:
            query = urlencode({
                "api-version": "2024-10-01", "modelFormat": "OpenAI",
                "modelName": name, "modelVersion": version,
            })
            result = self.az(
                "rest", "--method", "get", "--uri",
                f"https://management.azure.com/subscriptions/{self.config['subscription']}"
                f"/providers/Microsoft.CognitiveServices/locations/swedencentral/modelCapacities?{query}",
            )
            rows = [
                row["properties"] for row in result["value"]
                if row["properties"].get("skuName") == "GlobalStandard"
            ]
            if not rows or not any(
                isinstance(row.get("availableCapacity"), (int, float))
                and row["availableCapacity"] >= required_capacity for row in rows
            ):
                raise ValueError(f"No verified GlobalStandard capacity for {name}/{version}; no model or region substitution.")
            report.append({"model": name, "version": version, "required_capacity": required_capacity, "capacity_records": rows})
        self.state["model_capacity"] = report
        self.save()
        print(json.dumps(report, indent=2))

    def execute(self, operation: str, preserve_existing: bool = False):
        config = self.config
        tags = owned_tags(config["run_id"])
        located = {"location": "swedencentral", "tags": tags}
        account_suffix = f"Microsoft.CognitiveServices/accounts/{config['account']}"
        project_suffix = account_suffix + f"/projects/{config['project']}"
        if operation == "ownership":
            self.ownership(preserve_existing)
        elif operation in {"identity", "group"}:
            getattr(self, operation)()
        elif operation == "model-capacity":
            self.model_capacity()
        elif operation == "search-status":
            result = self.get("search")
            print(json.dumps({
                "name": result["name"], "location": result["location"],
                "provisioning_state": result["properties"].get("provisioningState"),
                "status": result["properties"].get("status"),
                "status_details": result["properties"].get("statusDetails"),
            }, indent=2))
        elif operation == "wait-search":
            self.guard()
            self.wait_ready("search", self.get("search"))
        elif operation == "foundry":
            self.put("foundry", account_suffix, FOUNDRY_API, {
                **located, "kind": "AIServices", "sku": {"name": "S0"},
                "identity": {"type": "SystemAssigned"},
                "properties": {
                    "allowProjectManagement": True, "customSubDomainName": config["account"],
                    "publicNetworkAccess": "Enabled", "disableLocalAuth": True,
                    "networkAcls": {"defaultAction": "Allow", "virtualNetworkRules": [], "ipRules": []},
                },
            })
        elif operation == "project":
            self.put("project", project_suffix, FOUNDRY_API, {
                **located, "identity": {"type": "SystemAssigned"},
                "properties": {"displayName": "Learning loop workshop", "description": "Synthetic data only. Dedicated foundry-evaluation workshop."},
            })
        elif operation == "logs":
            self.put("logs", f"Microsoft.OperationalInsights/workspaces/{config['logs']}", "2022-10-01", {
                **located, "properties": {"sku": {"name": "PerGB2018"}, "retentionInDays": 30},
            })
        elif operation == "insights":
            self.put("insights", f"Microsoft.Insights/components/{config['insights']}", "2020-02-02", {
                **located, "kind": "web",
                "properties": {"Application_Type": "web", "WorkspaceResourceId": self.state["resources"]["logs"]["id"]},
            })
        elif operation == "search":
            self.put("search", f"Microsoft.Search/searchServices/{config['search']}", SEARCH_API, {
                **located, "sku": {"name": "basic"}, "identity": {"type": "SystemAssigned"},
                "properties": {
                    "replicaCount": 1, "partitionCount": 1, "hostingMode": "default",
                    "publicNetworkAccess": "enabled", "disableLocalAuth": True,
                    "semanticSearch": "free", "knowledgeRetrieval": "free",
                },
            })
        elif operation in {"user-foundry", "user-model", "user-search-service", "user-search-data"}:
            resource, role = {
                "user-foundry": ("project", ROLE_FOUNDRY_USER),
                "user-model": ("foundry", ROLE_OPENAI_USER),
                "user-search-service": ("search", ROLE_SEARCH_SERVICE),
                "user-search-data": ("search", ROLE_SEARCH_DATA),
            }[operation]
            self.role(self.state["principal_id"], "User", resource, role)
        elif operation == "project-monitor":
            principal = self.get("project")["identity"]["principalId"]
            for key in ("insights", "logs"):
                self.role(principal, "ServicePrincipal", key, ROLE_LOG_READER)
        elif operation == "insights-connection":
            insights = self.get("insights")
            self.put("insights-connection", project_suffix + "/connections/workshop-insights", CONNECTION_API, {
                "properties": {
                    "category": "AppInsights", "target": insights["id"], "authType": "ApiKey",
                    "isSharedToAll": True, "credentials": {"key": insights["properties"]["ConnectionString"]},
                    "metadata": {"ApiType": "Azure", "ResourceId": insights["id"]},
                },
            })
        elif operation == "search-connection":
            self.put("search-connection", project_suffix + "/connections/workshop-search", CONNECTION_API, {
                "properties": {
                    "category": "CognitiveSearch", "target": f"https://{config['search']}.search.windows.net",
                    "authType": "AAD", "isSharedToAll": True,
                    "metadata": {
                        "ApiType": "Azure", "ApiVersion": "2026-04-01", "type": "azure_ai_search",
                        "ResourceId": self.state["resources"]["search"]["id"],
                    },
                },
            })
        elif operation == "auxiliary":
            self.put(
                "auxiliary", account_suffix + f"/deployments/{config['prefix']}-judge", FOUNDRY_API,
                {"sku": {"name": "GlobalStandard", "capacity": 100},
                 "properties": {"model": {"format": "OpenAI", "name": "gpt-5.4-mini", "version": AUXILIARY_VERSION}, "versionUpgradeOption": "NoAutoUpgrade"}},
            )
        elif operation == "ready":
            self.guard()
            account, project = self.get("foundry"), self.get("project")
            endpoint = project["properties"]["endpoints"]["AI Foundry API"].rstrip("/")
            endpoints = account["properties"]["endpoints"]
            model_endpoint = endpoints["Azure OpenAI Legacy API - Latest moniker"].rstrip("/")
            values = dotenv_values(self.workspace / ".env")
            for key, actual in (("FOUNDRY_PROJECT_ENDPOINT", endpoint), ("AZURE_OPENAI_ENDPOINT", model_endpoint)):
                if values[key].rstrip("/") != actual:
                    set_key(self.workspace / ".env", key, actual, quote_mode="never")
            self.state["project_id"] = project["id"]
            self.state["project_endpoint"] = endpoint
            self.state["model_endpoint"] = model_endpoint
            self.save()
            print(json.dumps({
                "group": config["resource_group"], "region": config["region"],
                "project": project["name"], "project_endpoint": endpoint,
                "model_endpoint": model_endpoint, "search": config["search"],
                "resources": list(self.state["resources"]),
                "scope": "only newly created, tagged workshop resources",
            }, indent=2))
        else:
            raise ValueError("Unknown provisioning operation.")


OPERATIONS = [
    "identity", "ownership", "group", "foundry", "project", "logs", "insights", "search",
    "user-foundry", "user-model", "user-search-service", "user-search-data",
    "project-monitor", "insights-connection", "search-connection", "auxiliary", "ready",
    "model-capacity", "search-status", "wait-search",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=OPERATIONS)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--preserve-existing", action="store_true", help="For ownership: explicitly retain every existing group; never delete them.")
    args = parser.parse_args()
    directory = args.run_dir.resolve()
    if not directory.is_relative_to(ROOT / ".workshop"):
        raise ValueError("Use an isolated .workshop directory in this repository.")
    if args.preserve_existing and args.operation != "ownership":
        parser.error("--preserve-existing is only valid with ownership.")
    Provisioner(directory).execute(args.operation, args.preserve_existing)


if __name__ == "__main__":
    main()
