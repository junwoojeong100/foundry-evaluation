import json
import os
import shutil
import sys
import uuid
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / ".recording" / "workshop"


def main() -> None:
    if WORKSPACE.exists():
        raise SystemExit("Recording workspace already exists; reuse it rather than overwriting evidence.")
    WORKSPACE.mkdir(parents=True)
    for name in ("azure.yaml", "requirements.txt", "requirements.lock.txt", "AGENTS.md", ".gitignore"):
        shutil.copyfile(ROOT / name, WORKSPACE / name)
    for name in ("data", "queries", "scripts", "tests"):
        shutil.copytree(ROOT / name, WORKSPACE / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copytree(
        ROOT / "src" / "agent",
        WORKSPACE / "src" / "agent",
        ignore=shutil.ignore_patterns(".venv", ".foundry", ".env", "__pycache__", "*.pyc"),
    )
    suffix = uuid.uuid4().hex[:5]
    prefix = f"ll-video-{suffix}"
    values = {key: value for key, value in dotenv_values(ROOT / ".env").items() if value is not None}
    values.update({
        "LAB_PREFIX": prefix,
        "LAB_AGENT_NAME": f"frontier-video-{suffix}",
        "LAB_PROMPT_VERSION": "v1",
        "LAB_AUTH_MODE": "cli",
    })
    for model in ("SOL", "TERRA", "LUNA", "ASTRA"):
        values[f"MODEL_{model}_DEPLOYMENT"] = f"{prefix}-{model.lower()}"
    env_file = WORKSPACE / ".env"
    env_file.write_text("".join(f"{key}={value}\n" for key, value in values.items()), encoding="utf-8")
    os.chmod(env_file, 0o600)
    config = {
        "workspace": str(WORKSPACE),
        "bootstrap_python": sys.executable,
        "agent_name": values["LAB_AGENT_NAME"],
        "prefix": prefix,
        "local_port": 8878,
        "console_port": 8877,
    }
    (ROOT / ".recording" / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(json.dumps({"workspace": str(WORKSPACE.relative_to(ROOT)), "new_namespace": prefix, "prior_run_unchanged": True}))


if __name__ == "__main__":
    main()
