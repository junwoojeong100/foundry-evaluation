"""Export only verified, non-secret facts from this run's actual result files."""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def export(directory: Path):
    config = json.loads((directory / "config.json").read_text())
    results = Path(config["workspace"]) / "src/agent/.foundry/results"
    evidence = json.loads((results / "verified-evidence.json").read_text())
    if not evidence["component_execution_verified"] or evidence["primary_model_outputs"] != 64 or evidence["distinct_verified_traces"] != 64:
        raise ValueError("The actual 64-response/64-trace verification has not passed.")
    report = {
        "run": config["run_id"], "resource_group": config["resource_group"],
        "region": config["region"], "foundry_account": config["account"], "project": config["project"],
        "component_execution_verified": True, "primary_responses": 64, "verified_traces": 64,
        "models": evidence["models"], "production_release_approved": evidence["production_release_approved"],
        "cohorts": [], "reused_baseline_trace_ids": evidence["reused_baseline_trace_ids"],
        "data_scope": "Existing synthetic educational dev/holdout; not a newly created independent test set.",
        "reviewer": "assistant; not human production approval",
    }
    for label in ("baseline", "improved", "holdout"):
        folder = results / label
        manifest = json.loads((folder / "manifest.json").read_text())
        business = json.loads((folder / "business-summary.json").read_text())
        native = json.loads((folder / "evaluation-results.json").read_text())
        evaluation = json.loads((folder / "evaluation.json").read_text())
        telemetry = json.loads((folder / "telemetry.json").read_text())
        record = {
            "label": label, "agent_version": manifest["agent"]["version"],
            "prompt_version": manifest["prompt_version"], "prompt_hash": manifest["prompt_hash"],
            "dataset_hash": manifest["dataset_hash"], "corpus_hash": manifest["corpus_hash"],
            "response_run_id": manifest["run_id"], "rows": manifest["expected_rows"],
            "started_at": manifest["started_at"], "status": manifest["status"],
            "business": {key: {name: value[name] for name in (
                "total", "business_passed", "business_gate", "input_tokens", "output_tokens",
            )} for key, value in business.items()},
            "evaluation_id": evaluation["evaluation_id"], "evaluation_run_id": evaluation["run_id"],
            "evaluation_status": evaluation["status"], "native_evaluators": {},
            "verified_traces": telemetry["observed_trace_count"],
        }
        for name in ("groundedness", "relevance"):
            grades = [grade for row in native for grade in row["results"] if grade["name"] == name]
            if len(grades) != manifest["expected_rows"] or any(
                grade.get("score") is None or not isinstance(grade.get("passed"), bool) for grade in grades
            ):
                raise ValueError("A native evaluation row is missing or has a null score.")
            record["native_evaluators"][name] = {
                "passed": sum(grade["passed"] is True for grade in grades), "total": len(grades),
            }
        report["cohorts"].append(record)
    cleanup = results / "cleanup-check.json"
    pause = results / "session-pause.json"
    if cleanup.exists():
        data = json.loads(cleanup.read_text())
        if (
            data.get("temporary_hosted_agent_absent") is not True
            or data.get("temporary_model_deployments_absent") != 4
            or data.get("temporary_search_objects_absent") != 3
            or data.get("temporary_role_assignments_absent") != 3
        ):
            raise ValueError("The final cleanup has not been verified.")
        report["resource_state"] = {
            **data, "final_object_cleanup": "verified",
            "foundation_costs": "Search service operation and telemetry retention can still incur charges.",
        }
    elif pause.exists():
        data = json.loads(pause.read_text())
        report["resource_state"] = {
            "sessions_stopped": len(data["stopped_sessions"]),
            "active_sessions_remaining": data["active_sessions_remaining"],
            "agent_versions_models_and_knowledge_preserved": data["agent_versions_models_and_knowledge_preserved"],
            "final_object_cleanup": "pending authenticated portal capture",
        }
    portal = directory / "portal-verification.json"
    if portal.exists():
        report["portal_recording"] = json.loads(portal.read_text())
    target = ROOT / "docs/assets" / f"live-{config['run_id']}" / "azure-verification.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"exported": str(target.relative_to(ROOT)), "responses": 64, "traces": 64}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    export(args.run_dir.resolve())
