import json
import zipfile
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/foundry-portal-recording"
OUT.mkdir(parents=True, exist_ok=True)
values = {key: value for key, value in dotenv_values(ROOT / ".env").items() if value is not None}
values.pop("AZURE_EXPECTED_USERNAME", None)
values.update({
    "LAB_PREFIX": "portal0911",
    "LAB_AGENT_NAME": "portal-learning-loop-0911",
    "LAB_PROMPT_VERSION": "v1",
    "LAB_AUTH_MODE": "cli",
})
for model in ("SOL", "TERRA", "LUNA", "ASTRA"):
    values[f"MODEL_{model}_DEPLOYMENT"] = f"portal0911-{model.lower()}"
bootstrap = '''import json, subprocess
from pathlib import Path
values = json.loads(Path("portal-settings.json").read_text())
account = json.loads(subprocess.check_output(["az","account","show","--subscription",values["AZURE_SUBSCRIPTION_ID"],"-o","json"],text=True))
if account["id"] != values["AZURE_SUBSCRIPTION_ID"] or account["tenantId"] != values["AZURE_TENANT_ID"]:
    raise SystemExit("Wrong subscription or tenant.")
values["AZURE_EXPECTED_USERNAME"] = account["user"]["name"]
Path(".env").write_text("".join(f"{k}={v}\\n" for k,v in values.items()))
Path(".env").chmod(0o600)
print("Configured the selected Azure identity; no credential values are printed.")
'''
archive = OUT / "portal-workshop-source.zip"
with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
    for name in ("azure.yaml", "requirements.txt", "requirements.lock.txt", "AGENTS.md", ".gitignore"):
        bundle.write(ROOT / name, name)
    for folder in ("scripts", "data", "queries", "tests", "src/agent"):
        for path in (ROOT / folder).rglob("*"):
            relative = path.relative_to(ROOT)
            if (
                path.is_file() and not path.is_symlink()
                and not {".venv", ".foundry", "__pycache__"}.intersection(relative.parts)
                and path.name != ".env" and path.suffix != ".pyc"
            ):
                bundle.write(path, relative)
    bundle.writestr("portal-settings.json", json.dumps(values, indent=2))
    bundle.writestr("portal_bootstrap.py", bootstrap)
with zipfile.ZipFile(archive) as bundle:
    assert bundle.testzip() is None
    assert ".env" not in bundle.namelist()
print(f"Prepared source-only upload: {archive.name} ({archive.stat().st_size} bytes)")
