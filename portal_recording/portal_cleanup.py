import argparse
import json
import sys
import zipfile
from pathlib import Path

root = Path.cwd()
sys.path[:0] = [str(root / "scripts"), str(root / "src/agent")]

from azure.ai.projects import AIProjectClient
from cloud_setup import check_cleanup, deployments, resources, search_client
from common import RESULTS_DIR, az, read_json, write_json
from settings import RuntimeConfig, credential


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm-role-id", required=True)
    args = parser.parse_args()
    config = RuntimeConfig.from_env()
    if (config.prefix, config.agent_name) != ("portal0911", "portal-learning-loop-0911"):
        raise ValueError("This cleanup supplement is scoped to the portal recording.")
    found = resources()
    scope = found["app_insights"]["id"]
    roles = az("role", "assignment", "list", "--scope", scope)
    matches = [role for role in roles if role["id"].casefold() == args.confirm_role_id.casefold()]
    if len(matches) != 1:
        raise ValueError("The explicitly confirmed UI-created role must exist exactly once.")
    role = matches[0]
    if (
        role["principalId"] != "5d69651e-8a30-4b72-b16e-15fd60e59a48"
        or role["roleDefinitionName"] != "Monitoring Reader"
        or role["scope"].casefold() != scope.casefold()
        or role["createdOn"] != "2026-09-11T02:16:54.226692+00:00"
    ):
        raise ValueError("The role assignment differs from the recorded creation evidence.")
    az("role", "assignment", "delete", "--ids", role["id"])
    remaining_roles = az("role", "assignment", "list", "--scope", scope)
    if any(item["id"].casefold() == role["id"].casefold() for item in remaining_roles):
        raise ValueError("The temporary UI-created role assignment still exists.")
    result = check_cleanup()
    names = {item["name"] for item in deployments()}
    expected = [f"portal0911-{key}" for key in ("sol", "terra", "luna", "astra")]
    if names.intersection(expected):
        raise ValueError("A UI-created model deployment is still present.")
    with AIProjectClient(endpoint=config.project_endpoint, credential=credential()) as project:
        shared = project.agents.get("microsoft-iq-workflow-agent")
        if shared.name != "microsoft-iq-workflow-agent":
            raise ValueError("The pre-existing shared agent was not preserved.")
    with search_client(config) as client:
        response = client.get("knowledgebases/microsoft-iq-knowledge-base")
        response.raise_for_status()
    result.update({
        "ui_created_models_deleted": expected,
        "ui_created_monitoring_reader_removed": {
            key: role[key] for key in ("id", "principalId", "scope", "roleDefinitionName", "createdOn")
        },
        "existing_shared_agent_preserved": True,
        "existing_shared_knowledge_base_preserved": True,
        "retained": ["portal0911-dev:1", "evaluation runs and their datasets", "telemetry and annotations"],
    })
    write_json(RESULTS_DIR / "portal-cleanup-check.json", result)
    summary = read_json(root / "portal-summary.json")
    summary["cleanup"] = result
    write_json(root / "portal-summary.json", summary)
    with zipfile.ZipFile(Path.home() / "portal-final-evidence.zip", "w", zipfile.ZIP_DEFLATED) as bundle:
        bundle.write(root / "portal-summary.json", "portal-summary.json")
        for folder in ("results", "datasets", "suites", "evaluators"):
            for path in (root / "src/agent/.foundry" / folder).rglob("*"):
                if path.is_file() and path.suffix in {".json", ".jsonl", ".kql"}:
                    bundle.write(path, path.relative_to(root / "src/agent/.foundry"))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("PORTAL_CLEANUP_VERIFIED")


if __name__ == "__main__":
    main()
