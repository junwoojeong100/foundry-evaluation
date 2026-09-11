import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from settings import REPO_ROOT, RuntimeConfig, SOURCE_DIR, load_settings_env, required

FOUNDRY_DIR = SOURCE_DIR / ".foundry"
RESULTS_DIR = FOUNDRY_DIR / "results"
STATE_PATH = FOUNDRY_DIR / "local-state.json"


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def digest(value: Any) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not rows or not all(isinstance(row, dict) for row in rows):
        raise ValueError(f"{path} must contain nonempty JSON objects.")
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def label_dir(label: str) -> Path:
    if not re.fullmatch(r"[a-z][a-z0-9-]{0,39}", label):
        raise ValueError("Labels must be 1-40 lowercase letters/digits/hyphens.")
    return RESULTS_DIR / label


def scope() -> dict[str, str]:
    load_settings_env()
    return {
        "subscription": required("AZURE_SUBSCRIPTION_ID"),
        "tenant": required("AZURE_TENANT_ID"),
        "resource_group": required("AZURE_RESOURCE_GROUP"),
        "account": required("AZURE_AI_ACCOUNT_NAME"),
        "project": required("AZURE_AI_PROJECT_NAME"),
        "prefix": required("LAB_PREFIX"),
        "agent": required("LAB_AGENT_NAME"),
    }


def load_state() -> dict[str, Any]:
    expected = scope()
    if not STATE_PATH.exists():
        return {"scope": expected, "owned_models": [], "owned_search_paths": [], "owned_roles": []}
    state = read_json(STATE_PATH)
    if state.get("scope") != expected:
        raise ValueError("Local ownership state belongs to a different Azure scope. Refusing changes.")
    return state


def save_state(state: dict[str, Any]) -> None:
    if state.get("scope") != scope():
        raise ValueError("Cannot persist ownership for a different Azure scope.")
    write_json(STATE_PATH, state)


def command(args: list[str], *, timeout: int = 600) -> str:
    completed = subprocess.run(
        args,
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if completed.returncode:
        raise RuntimeError(
            f"{' '.join(args[:5])} failed ({completed.returncode}):\n"
            f"{completed.stderr.strip()}\n{completed.stdout.strip()}"
        )
    return completed.stdout


def az(*args: str) -> Any:
    text = command(
        [
            "az", *args, "--subscription", required("AZURE_SUBSCRIPTION_ID"),
            "--only-show-errors", "--output", "json",
        ]
    )
    return json.loads(text) if text.strip() else None


def azd(*args: str, json_output: bool = True) -> Any:
    options = ["--output", "json"] if json_output else []
    text = command(["azd", *args, *options])
    return json.loads(text) if json_output and text.strip() else text


def authenticate() -> dict[str, Any]:
    load_settings_env()
    account = az("account", "show")
    if account["tenantId"] != required("AZURE_TENANT_ID"):
        raise ValueError("The selected subscription belongs to a different tenant.")
    if account["user"]["name"].casefold() != required("AZURE_EXPECTED_USERNAME").casefold():
        raise ValueError("The selected Azure CLI account is not the requested account.")
    if account["id"] != required("AZURE_SUBSCRIPTION_ID"):
        raise ValueError("Unexpected Azure subscription.")
    return account


def runtime_env() -> dict[str, str]:
    config = RuntimeConfig.from_env()
    return {
        "FOUNDRY_PROJECT_ENDPOINT": config.project_endpoint,
        "AZURE_AI_PROJECT_ENDPOINT": config.project_endpoint,
        "AZURE_SEARCH_ENDPOINT": config.search_endpoint,
        "AZURE_OPENAI_ENDPOINT": config.model_endpoint,
        "AZURE_AI_MODEL_DEPLOYMENT_NAME": required("LAB_AUX_DEPLOYMENT"),
        "LAB_PREFIX": config.prefix,
        "LAB_AGENT_NAME": config.agent_name,
        "LAB_PROMPT_VERSION": config.prompt_version,
        "LAB_AS_OF_DATE": config.as_of_date,
        "LAB_MAX_OUTPUT_TOKENS": str(config.max_output_tokens),
        **{f"MODEL_{key.upper()}_DEPLOYMENT": value for key, value in config.deployments.items()},
    }


def binding() -> dict[str, str]:
    config = RuntimeConfig.from_env()
    values = azd("env", "get-values")
    if values.get("AZURE_SUBSCRIPTION_ID") != required("AZURE_SUBSCRIPTION_ID"):
        raise ValueError("azd is bound to a different subscription.")
    if values.get("FOUNDRY_PROJECT_ENDPOINT") != config.project_endpoint:
        raise ValueError("azd is bound to a different project.")
    prefix = "AGENT_" + config.agent_name.upper().replace("-", "_")
    version = values.get(prefix + "_VERSION")
    endpoint = values.get(prefix + "_INVOCATIONS_ENDPOINT")
    if not version or not endpoint:
        raise ValueError("Deploy the agent first; azd has no version/Invocations endpoint.")
    return {"name": config.agent_name, "version": str(version), "endpoint": endpoint}
