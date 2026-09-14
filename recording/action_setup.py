"""Prepare an isolated source snapshot and a reproducible recording action list."""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def initialize(directory: Path):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,31}", directory.name):
        raise ValueError("Use a 1-32 character lowercase/digit/hyphen run ID.")
    if directory.exists():
        raise ValueError("The recording directory already exists; preserve it and choose another run.")
    values = dotenv_values(ROOT / ".env")
    if not all(values.get(key) for key in (
        "AZURE_SUBSCRIPTION_ID", "AZURE_TENANT_ID", "AZURE_EXPECTED_USERNAME",
    )):
        raise ValueError("The repository must identify the authorized account, subscription and tenant.")
    directory.mkdir(parents=True)
    workspace = directory / "workshop"
    prefix = "ll-0914-" + directory.name.rsplit("-", 1)[-1]
    config = {
        "run_id": directory.name, "workspace": str(workspace), "port": 8897,
        "prefix": prefix, "region": "swedencentral",
        "resource_group": "rg-foundry-evaluation-" + directory.name,
        "account": "fe-" + directory.name,
        "project": "learning-loop",
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
        "environment": {
            "AZURE_SUBSCRIPTION_ID": values["AZURE_SUBSCRIPTION_ID"],
            "AZURE_TENANT_ID": values["AZURE_TENANT_ID"],
        },
    }
    write_json(directory / "config.json", config)
    os.chmod(directory / "config.json", 0o600)
    python = str(workspace / "src/agent/.venv/bin/python")
    actions = [
        {
            "id": "00-01-source", "guide": "00 · 시작 전 준비", "title": "새 실행용 소스와 설정 준비",
            "argv": [sys.executable, "recording/action_setup.py", "prepare", "--run-dir", str(directory)],
            "cwd": str(ROOT), "check": "이전 실행을 덮어쓰지 않은 새 폴더와 source manifest",
        },
        {
            "id": "00-02-venv", "guide": "00 · 시작 전 준비", "title": "Python 3.13 가상환경 생성",
            "argv": ["python3.13", "-m", "venv", "src/agent/.venv"],
            "check": "이번 실행 폴더 안에 생성한 독립 가상환경",
        },
        {
            "id": "00-02-check-packages", "guide": "00 · 시작 전 준비", "title": "새 가상환경의 의존성 확인",
            "argv": [python, "-c", "import pydantic; import azure.ai.projects; print('Required imports are available')"],
            "check": "새 환경에 패키지가 없으면 오류를 보존하고 다음 고정 버전 설치로 해결",
        },
        {
            "id": "00-03-dependencies", "guide": "00 · 시작 전 준비", "title": "고정된 의존성 설치",
            "argv": [python, "-m", "pip", "install", "--disable-pip-version-check", "-q", "-r", "requirements.lock.txt"],
            "check": "기존 검증 버전 유지 · 다른 모델이나 SDK로 자동 대체하지 않음",
        },
        {
            "id": "00-04-tests", "guide": "00 · 시작 전 준비", "title": "Azure 실행 전 로컬 검사",
            "argv": [python, "-m", "unittest", "discover", "-s", "tests", "-v"],
            "check": "전체 테스트 OK · 이 결과는 Azure 성공을 의미하지 않음",
        },
        {
            "id": "00-05-account", "guide": "00 · 계정과 소유권", "title": "지정 계정과 구독 확인",
            "argv": ["az", "account", "show", "--subscription", config["subscription"],
                     "--query", "{name:name,id:id,tenant:tenantId,state:state,user:user.name}", "-o", "json"],
            "check": "강사가 지정한 계정·구독·tenant · 기본 구독은 변경하지 않음",
        },
        {
            "id": "00-06-groups", "guide": "00 · 계정과 소유권", "title": "기존 리소스 그룹의 소유권 조사",
            "argv": ["az", "group", "list", "--subscription", config["subscription"],
                     "--query", "[].{name:name,location:location,tags:tags}", "-o", "json"],
            "check": "리포 전용이라는 근거 없는 공유 그룹은 삭제하지 않음",
        },
        {
            "id": "00-07-old-resources", "guide": "00 · 계정과 소유권", "title": "이전 환경이 공유 자원인지 확인",
            "argv": ["az", "resource", "list", "--subscription", config["subscription"],
                     "--resource-group", config["old_resource_group"],
                     "--query", "[].{name:name,type:type,location:location,tags:tags}", "-o", "json"],
            "check": "다른 실습·공유 프로젝트가 들어 있으면 그룹 전체 삭제 금지",
        },
        {
            "id": "00-08-model-catalog", "guide": "00 · 모델 사전 확인", "title": "Sweden Central의 네 모델과 보조 모델 확인",
            "argv": ["az", "cognitiveservices", "model", "list", "--subscription", config["subscription"],
                     "--location", "swedencentral", "--query",
                     "[?model.name=='gpt-5.6-sol' || model.name=='gpt-5.6-terra' || model.name=='gpt-5.6-luna' || model.name=='gpt-6-astra' || model.name=='gpt-5.4-mini'].model",
                     "-o", "json"],
            "check": "실제 모델 ID·버전·GlobalStandard 지원 · 모델 대체 없음",
        },
        {
            "id": "00-09-quota", "guide": "00 · 모델 사전 확인", "title": "실제 모델 배포의 남은 할당량 확인",
            "argv": ["az", "cognitiveservices", "usage", "list", "--subscription", config["subscription"],
                     "--location", "swedencentral", "--query",
                     "[?contains(name.value, 'GlobalStandard') && (contains(name.value, 'gpt-5.6') || contains(name.value, 'gpt-6-astra') || contains(name.value, 'gpt-5.4-mini'))].{name:name.value,used:currentValue,limit:limit}",
                     "-o", "json"],
            "check": "limit - used가 필요한 용량 이상 · 다른 리전으로 임의 이동하지 않음",
        },
    ]
    write_json(directory / "actions.json", actions)
    print(json.dumps({key: config[key] for key in ("run_id", "resource_group", "region", "prefix")}))


def prepare(directory: Path):
    config = json.loads((directory / "config.json").read_text())
    workspace = Path(config["workspace"])
    if workspace.exists():
        raise ValueError("The source snapshot already exists; it will not be overwritten.")
    workspace.mkdir()
    for name in ("azure.yaml", "requirements.txt", "requirements.lock.txt", "AGENTS.md", ".gitignore"):
        shutil.copyfile(ROOT / name, workspace / name)
    for name in ("data", "queries", "scripts", "tests", "recording"):
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
    args = parser.parse_args()
    directory = args.run_dir.resolve()
    if not directory.is_relative_to(ROOT / ".recording"):
        raise ValueError("Recording workspaces must be under the repository's ignored .recording folder.")
    (initialize if args.operation == "init" else prepare)(directory)


if __name__ == "__main__":
    main()
