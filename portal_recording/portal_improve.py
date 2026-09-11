import json
import subprocess
import sys
import zipfile
from pathlib import Path

root = Path.cwd()


def run(*args):
    print("\n$ " + " ".join(args), flush=True)
    subprocess.run(args, check=True)


run(sys.executable, "scripts/workshop.py", "feedback", "--label", "baseline",
    "--row-id", "baseline-sol-D01", "--reviewer", "assistant",
    "--reason", "AI-assisted portal workshop review: actual trace and evidence show a document title instead of the required source ID. Verify the explicit V2 citation and policy instructions against the same frozen dataset; not production approval.")
run(sys.executable, "scripts/workshop.py", "set-prompt", "v2")
run("azd", "deploy", "--no-prompt")
run(sys.executable, "scripts/workshop.py", "collect", "--split", "dev", "--label", "improved")
run(sys.executable, "scripts/workshop.py", "evaluate", "--label", "improved")
run(sys.executable, str(Path.home() / "portal_monitor.py"), "--label", "improved")
run(sys.executable, "scripts/workshop.py", "collect", "--split", "holdout", "--label", "holdout")
run(sys.executable, "scripts/workshop.py", "evaluate", "--label", "holdout")
run(sys.executable, str(Path.home() / "portal_monitor.py"), "--label", "holdout")
run(sys.executable, "scripts/workshop.py", "verify", "--baseline", "baseline", "--candidate", "improved", "--holdout", "holdout")
results = root / "src/agent/.foundry/results"
summary = {"recorded_surface": "Actual Foundry and Azure Cloud Shell", "runs": []}
for label in ("baseline", "improved", "holdout"):
    record = json.loads((results / label / "evaluation.json").read_text())
    manifest = json.loads((results / label / "manifest.json").read_text())
    summary["runs"].append({
        "label": label, "agent_version": manifest["agent"]["version"],
        "run_id": record["run_id"], "evaluation_id": record["evaluation_id"],
        "status": record["status"], "rows": record["expected_rows"],
    })
summary["verification"] = json.loads((results / "verified-evidence.json").read_text())
(root / "portal-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
with zipfile.ZipFile(Path.home() / "portal-evidence.zip", "w", zipfile.ZIP_DEFLATED) as bundle:
    bundle.write(root / "portal-summary.json", "portal-summary.json")
    for folder in ("results", "datasets", "suites", "evaluators"):
        for path in (root / "src/agent/.foundry" / folder).rglob("*"):
            if path.is_file() and path.suffix in {".json", ".jsonl", ".kql"}:
                bundle.write(path, path.relative_to(root / "src/agent/.foundry"))
print("PORTAL_FULL_LOOP_VERIFIED", flush=True)
