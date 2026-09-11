import argparse
import json
import sys
from datetime import timedelta
from pathlib import Path

root = Path.cwd()
sys.path[:0] = [str(root / "src/agent"), str(root / "scripts")]

from azure.ai.projects import AIProjectClient
from azure.monitor.query import LogsQueryClient, LogsQueryStatus

from cloud_setup import resources
from common import label_dir, write_json
from experiments import completed_rows
from grading import percentile
from observability import telemetry_boolean
from settings import RuntimeConfig, credential

parser = argparse.ArgumentParser(description="Cloud Shell-compatible resource-scoped Azure Monitor query.")
parser.add_argument("--label", required=True)
args = parser.parse_args()
config = RuntimeConfig.from_env()
manifest, responses = completed_rows(args.label)
found = resources()
query = (root / "queries/monitor.kql").read_text()
query = query.replace("__AGENT_NAME__", config.agent_name).replace("__RUN_ID__", manifest["run_id"])
print(query, flush=True)
with LogsQueryClient(credential()) as client:
    result = client.query_resource(found["app_insights"]["id"], query, timespan=timedelta(hours=2))
if result.status != LogsQueryStatus.SUCCESS:
    raise RuntimeError(f"Azure Monitor returned a partial/failed result: {result}")
table = result.tables[0]
rows = [dict(zip(table.columns, row, strict=True)) for row in table.rows]
for row in rows:
    row["success"] = telemetry_boolean(row["success"])
    row["timestamp"] = str(row["timestamp"])
wanted = {row["trace_id"] for row in responses}
observed = {row["trace_id"] for row in rows}
complete = wanted == observed and len(rows) == len(wanted) and all(row["sample_weight"] == 1 for row in rows)
summary = {}
for key in config.deployments:
    selected = [row for row in rows if row["model_key"] == key]
    if selected:
        summary[key] = {
            "requests": len(selected),
            "success_rate": sum(row["success"] for row in selected) / len(selected),
            "server_p50_ms": percentile([row["duration_ms"] for row in selected], .5),
            "server_p95_ms": percentile([row["duration_ms"] for row in selected], .95),
            "input_tokens": sum(row["input_tokens"] for row in selected),
            "output_tokens": sum(row["output_tokens"] for row in selected),
        }
evidence = {
    "run_id": manifest["run_id"], "query": query, "rows": rows,
    "app_insights_resource_id": found["app_insights"]["id"],
    "expected_trace_count": len(wanted), "observed_trace_count": len(wanted & observed),
    "complete": complete, "operational_summary": summary,
    "query_path": "Azure Monitor LogsQueryClient.query_resource via Cloud Shell",
}
write_json(label_dir(args.label) / "telemetry.json", evidence)
print(json.dumps({key: value for key, value in evidence.items() if key not in {"rows", "query"}}, indent=2))
if not complete:
    raise RuntimeError("Not all real traces were returned; wait for ingestion and rerun.")
if not manifest.get("session_stopped"):
    with AIProjectClient(endpoint=config.project_endpoint, credential=credential()) as project:
        project.agents.stop_session(config.agent_name, manifest["session_id"])
    manifest["session_stopped"] = True
    write_json(label_dir(args.label) / "manifest.json", manifest)
print("PORTAL_MONITOR_VERIFIED")
