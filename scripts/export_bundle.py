import hashlib
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "src" / "agent" / ".foundry" / "results"
DESTINATION = ROOT / "artifacts"
EXCLUDED_PARTS = {".venv", ".foundry", ".azure", ".git", ".recording", "__pycache__", ".pytest_cache"}
RESPONSE_FIELDS = (
    "row_id", "case_id", "model_key", "configured_model_id",
    "configured_model_version", "deployment", "inference_api",
    "query", "answer", "decision", "citations", "source_ids",
    "ground_truth", "citation_required", "context_hash", "prompt_version",
    "prompt_hash", "agent_version", "agent_response_id", "trace_id",
    "input_tokens", "output_tokens", "latency_seconds", "client_latency_seconds",
    "business_grade", "regression_source_trace_ids",
)


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    verified = read(RESULTS / "verified-evidence.json")
    if verified.get("component_execution_verified") is not True:
        raise ValueError("Run workshop.py verify before exporting evidence.")
    if not read(RESULTS / "cleanup.json").get("completed"):
        raise ValueError("Complete temporary-resource cleanup before creating the handoff bundle.")
    cleanup_check = read(RESULTS / "cleanup-check.json")
    if cleanup_check.get("temporary_hosted_agent_absent") is not True:
        raise ValueError("Run workshop.py check-cleanup before exporting.")
    state = read(ROOT / "src" / "agent" / ".foundry" / "local-state.json")
    if any(state.get(key) for key in ("agent_owned", "owned_models", "owned_search_paths", "owned_roles")):
        raise ValueError("The latest ownership ledger still contains temporary resources.")
    write(DESTINATION / "verification-summary.json", verified)
    write(DESTINATION / "comparison.json", read(RESULTS / "comparison.json"))
    for run in verified["runs"]:
        label = run["label"]
        if not re.fullmatch(r"[a-z][a-z0-9-]{0,39}", label):
            raise ValueError("Unsafe evidence label.")
        source = RESULTS / label
        target = DESTINATION / "results" / label
        manifest = read(source / "manifest.json")
        write(target / "manifest.json", {
            key: manifest[key] for key in (
                "label", "run_id", "split", "dataset_hash", "corpus_hash",
                "prompt_version", "prompt_hash", "status", "started_at", "completed_at",
                "concurrency", "session_stopped",
            )
        } | {"agent_version": manifest["agent"]["version"]})
        rows = [
            json.loads(line) for line in (source / "responses.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        sanitized = [{key: row[key] for key in RESPONSE_FIELDS if key in row} for row in rows]
        (target / "responses.jsonl").write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in sanitized), encoding="utf-8"
        )
        evaluation = read(source / "evaluation.json")
        write(target / "evaluation.json", {
            "evaluation_id": evaluation["evaluation_id"], "run_id": evaluation["run_id"],
            "status": evaluation["status"], "result_counts": evaluation["run"]["result_counts"],
            "report_url": evaluation["run"].get("report_url"),
        })
        write(target / "evaluation-results.json", read(source / "evaluation-results.json"))
        telemetry = read(source / "telemetry.json")
        write(target / "telemetry.json", {
            key: telemetry[key] for key in (
                "run_id", "rows", "expected_trace_count", "observed_trace_count",
                "complete", "operational_summary",
            )
        })
    calibration = read(RESULTS / "judge-calibration" / "calibration.json")
    write(DESTINATION / "judge-calibration.json", {
        "authoring": "AI-assisted, explicitly specified reference examples; not target-model outputs",
        "groundedness": calibration["groundedness"], "passed": calibration["passed"],
        "evaluation_id": read(RESULTS / "judge-calibration" / "evaluation.json")["evaluation_id"],
        "run_id": read(RESULTS / "judge-calibration" / "evaluation.json")["run_id"],
    })
    for path in (ROOT / "src" / "agent" / ".foundry" / "datasets").glob("regression-*.jsonl"):
        destination = DESTINATION / "regressions" / path.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        for record in records:
            lineage = record["lineage"]
            lineage["original_reference_source_label"] = lineage["ground_truth_source"]
            lineage["ground_truth_source"] = "fixed AI-assisted workshop reference dataset; not the evaluated model response"
            lineage["export_note"] = "Reference-authoring wording clarified; question, rubric, source trace and reviewer are unchanged."
        destination.write_text(
            "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records), encoding="utf-8"
        )
    write(DESTINATION / "cleanup-summary.json", {
        "temporary_resources_removed": True,
        "preserved": read(RESULTS / "cleanup.json")["plan"]["preserved"],
        "app_insights_resource_id_metadata_repair_retained": True,
    })
    write(DESTINATION / "cleanup-check.json", cleanup_check)
    archive = DESTINATION / "foundry-learning-loop-ko.zip"
    roots = [
        ROOT / name for name in (
            "README.md", "AGENTS.md", ".gitignore", ".env.example", "azure.yaml",
            "requirements.txt", "requirements.lock.txt", "docs", "data", "queries",
            "scripts", "tests", "src/agent", "artifacts",
        )
    ]
    files = set()
    for root in roots:
        candidates = root.rglob("*") if root.is_dir() else [root]
        for path in candidates:
            relative = path.relative_to(ROOT)
            if (
                path.is_file() and not path.is_symlink()
                and not EXCLUDED_PARTS.intersection(relative.parts)
                and relative.parts[:2] != ("artifacts", "recording")
                and path.name != ".env" and path.suffix not in {".pyc", ".zip"}
            ):
                files.add(path)
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(files):
            bundle.write(path, path.relative_to(ROOT))
    with zipfile.ZipFile(archive) as bundle:
        if bundle.testzip() is not None:
            raise ValueError("Archive integrity check failed.")
        for name in bundle.namelist():
            parts = Path(name).parts
            if EXCLUDED_PARTS.intersection(parts) or Path(name).name == ".env":
                raise ValueError(f"Private runtime file leaked into archive: {name}")
            text = bundle.read(name).decode("utf-8")
            if re.search(r"InstrumentationKey=[0-9a-f-]{36}", text, re.I) or re.search(r"Bearer eyJ[\w-]+\.", text):
                raise ValueError(f"A credential-like value was found in {name}.")
    print(f"Exported {len(files)} files: {archive.relative_to(ROOT)}")
    print(f"SHA256: {hashlib.sha256(archive.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
