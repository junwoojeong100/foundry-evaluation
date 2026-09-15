"""Prepare an isolated workshop source and configuration before provisioning."""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def initialize(directory: Path, language: str | None = None):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,31}", directory.name):
        raise ValueError("Use a 1-32 character lowercase/digit/hyphen run ID.")
    if directory.exists():
        raise ValueError("The workshop directory already exists; choose another run.")
    values = dotenv_values(ROOT / ".env")
    selected_language = language if language is not None else values.get("LAB_LANGUAGE", "ko")
    if selected_language not in {"ko", "en"}:
        raise ValueError("Workshop language must be ko or en.")
    if not all(values.get(key) for key in (
        "AZURE_SUBSCRIPTION_ID", "AZURE_TENANT_ID", "AZURE_EXPECTED_USERNAME",
    )):
        raise ValueError("The repository must identify the authorized account, subscription and tenant.")
    directory.mkdir(parents=True)
    config = {
        "run_id": directory.name, "workspace": str(directory / "workshop"),
        "language": selected_language,
        "prefix": "ll-" + directory.name, "region": "swedencentral",
        "resource_group": "rg-foundry-evaluation-" + directory.name,
        "account": "fe-" + directory.name, "project": "learning-loop",
        "search": "fe-search-" + directory.name,
        "logs": "fe-logs-" + directory.name,
        "insights": "fe-insights-" + directory.name,
        "old_resource_group": values["AZURE_RESOURCE_GROUP"],
        "subscription": values["AZURE_SUBSCRIPTION_ID"],
        "tenant": values["AZURE_TENANT_ID"],
        "username": values["AZURE_EXPECTED_USERNAME"],
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
        ).strip(),
    }
    write_json(directory / "config.json", config)
    os.chmod(directory / "config.json", 0o600)
    print(json.dumps({key: config[key] for key in ("run_id", "resource_group", "region", "prefix", "language")}))


def prepare(directory: Path):
    config = json.loads((directory / "config.json").read_text())
    language = config.get("language", "ko")
    if language not in {"ko", "en"}:
        raise ValueError("Workshop language must be ko or en.")
    workspace = directory / "workshop"
    if Path(config["workspace"]).resolve() != workspace.resolve():
        raise ValueError("The configured source must stay inside this workshop directory.")
    if workspace.exists():
        raise ValueError("The source snapshot already exists; it will not be overwritten.")
    workspace.mkdir()
    for name in ("azure.yaml", "requirements.txt", "requirements.lock.txt", ".gitignore"):
        shutil.copyfile(ROOT / name, workspace / name)
    for name in ("data", "queries", "scripts", "tests"):
        shutil.copytree(ROOT / name, workspace / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copytree(
        ROOT / "src/agent", workspace / "src/agent",
        ignore=shutil.ignore_patterns(".venv", ".foundry", ".env", "__pycache__", "*.pyc"),
    )
    values = dict(dotenv_values(ROOT / ".env"))
    values.update({
        "AZURE_RESOURCE_GROUP": config["resource_group"],
        "AZURE_AI_ACCOUNT_NAME": config["account"],
        "AZURE_AI_PROJECT_NAME": config["project"],
        "AZURE_SEARCH_NAME": config["search"],
        "AZURE_APPLICATION_INSIGHTS_NAME": config["insights"],
        "FOUNDRY_PROJECT_ENDPOINT": f"https://{config['account']}.services.ai.azure.com/api/projects/{config['project']}",
        "AZURE_SEARCH_ENDPOINT": f"https://{config['search']}.search.windows.net",
        "AZURE_OPENAI_ENDPOINT": f"https://{config['account']}.openai.azure.com",
        "LAB_PREFIX": config["prefix"], "LAB_AGENT_NAME": config["prefix"] + "-agent",
        "LAB_AUX_DEPLOYMENT": config["prefix"] + "-judge",
        "LAB_PROMPT_VERSION": "v1", "LAB_AUTH_MODE": "cli",
        "LAB_LANGUAGE": language,
    })
    for key in ("SOL", "TERRA", "LUNA", "ASTRA"):
        values[f"MODEL_{key}_DEPLOYMENT"] = config["prefix"] + "-" + key.lower()
    (workspace / ".env").write_text("".join(f"{key}={value}\n" for key, value in values.items() if value is not None))
    os.chmod(workspace / ".env", 0o600)
    manifest = {
        "revision": config["source_revision"],
        "files": {
            str(path.relative_to(workspace)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(workspace.rglob("*")) if path.is_file() and path.name != ".env"
        },
    }
    write_json(directory / "source-manifest.json", manifest)
    print(json.dumps({
        "source_revision": manifest["revision"], "source_files": len(manifest["files"]),
        "new_workspace": str(workspace.relative_to(ROOT)),
        "resource_group": config["resource_group"], "region": config["region"],
        "previous_run_preserved": True,
    }, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=["init", "prepare"])
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--language", choices=["ko", "en"], help="Language for init; prepare reuses the saved configuration.")
    args = parser.parse_args()
    directory = args.run_dir.resolve()
    if not directory.is_relative_to(ROOT / ".workshop"):
        raise ValueError("Use a workspace under the repository's ignored .workshop folder.")
    if args.operation == "init":
        initialize(directory, args.language)
    else:
        if args.language is not None:
            parser.error("--language is only valid with init.")
        prepare(directory)


if __name__ == "__main__":
    main()
