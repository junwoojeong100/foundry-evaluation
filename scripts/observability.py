import json
from typing import Any

import httpx
from azure.ai.projects import AIProjectClient

from cloud_setup import resources
from common import REPO_ROOT, label_dir, write_json
from experiments import completed_rows
from grading import percentile
from settings import RuntimeConfig, credential


def telemetry_boolean(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.lower() in {"true", "false"}:
        return value.lower() == "true"
    raise ValueError(f"Unrecognized telemetry boolean: {value!r}")


def monitor(label: str) -> None:
    config = RuntimeConfig.from_env()
    manifest, responses = completed_rows(label)
    found = resources()
    app_id = found["app_insights"]["properties"]["AppId"]
    query = (REPO_ROOT / "queries" / "monitor.kql").read_text()
    query = query.replace("__AGENT_NAME__", config.agent_name).replace("__RUN_ID__", manifest["run_id"])
    print(query)
    token = credential().get_token("https://api.applicationinsights.io/.default")
    response = httpx.post(
        f"https://api.applicationinsights.io/v1/apps/{app_id}/query",
        headers={"Authorization": f"Bearer {token.token}"},
        json={"query": query, "timespan": "PT2H"}, timeout=120, follow_redirects=False,
    )
    response.raise_for_status()
    payload = response.json()
    write_json(label_dir(label) / "telemetry-raw.json", payload)
    if payload.get("error"):
        raise ValueError(f"Application Insights query failed: {payload['error']}")
    tables = payload.get("tables")
    if not tables:
        raise ValueError("Application Insights returned no table.")
    table = tables[0]
    columns = [column["name"] for column in table["columns"]]
    rows = [dict(zip(columns, values, strict=True)) for values in table["rows"]]
    for row in rows:
        row["success"] = telemetry_boolean(row["success"])
    wanted = {row["trace_id"] for row in responses}
    observed = {row["trace_id"] for row in rows}
    result: dict[str, Any] = {
        "language": config.language,
        "run_id": manifest["run_id"],
        "app_insights_resource_id": found["app_insights"]["id"],
        "query": query, "rows": rows,
        "expected_trace_count": len(wanted),
        "observed_trace_count": len(wanted & observed),
        "complete": wanted == observed and len(rows) == len(wanted)
        and all(row["sample_weight"] == 1 for row in rows),
    }
    summary = {}
    for key in config.deployments:
        selected = [row for row in rows if row["model_key"] == key]
        if selected:
            summary[key] = {
                "requests": len(selected),
                "success_rate": sum(row["success"] is True for row in selected) / len(selected),
                "server_p50_ms": percentile([row["duration_ms"] for row in selected], 0.5),
                "server_p95_ms": percentile([row["duration_ms"] for row in selected], 0.95),
                "input_tokens": sum(row["input_tokens"] for row in selected),
                "output_tokens": sum(row["output_tokens"] for row in selected),
            }
    result["operational_summary"] = summary
    write_json(label_dir(label) / "telemetry.json", result)
    print(json.dumps({key: value for key, value in result.items() if key not in {"query", "rows"}}, ensure_ascii=False, indent=2))
    if not result["complete"]:
        raise ValueError("Telemetry is incomplete, not a zero-error success. Wait for ingestion and rerun monitor.")
    if not manifest.get("session_stopped", False):
        with AIProjectClient(endpoint=config.project_endpoint, credential=credential()) as project:
            project.agents.stop_session(config.agent_name, manifest["session_id"])
        manifest["session_stopped"] = True
        write_json(label_dir(label) / "manifest.json", manifest)
        print(f"Verified telemetry and stopped session {manifest['session_id']}.")
