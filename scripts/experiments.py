import json
import math
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import httpx
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import TestingCriterionAzureAIEvaluator, VersionRefIndicator
from azure.core.exceptions import AzureError
from azure.identity import get_bearer_token_provider

from cloud_setup import preflight
from common import (
    FOUNDRY_DIR, REPO_ROOT, RESULTS_DIR, azd, binding, digest, label_dir, load_state,
    parse_azd_json, read_json, read_jsonl, utc_stamp, validate_azd_suffix, write_json, write_jsonl,
)
from contracts import Invocation, MODEL_SPECS, PolicyAnswer
from grading import grade, paired_outcomes, summarize, validate_matrix
from prompting import load_prompt
from settings import RuntimeConfig, credential, data_directory, required, workshop_language


def dataset(split: str) -> list[dict[str, Any]]:
    if split not in {"dev", "holdout"}:
        raise ValueError("Dataset split must be dev or holdout.")
    return read_jsonl(data_directory() / f"{split}.jsonl")


def require_run_language(record: dict[str, Any]) -> None:
    if record.get("language", "ko") != workshop_language():
        raise ValueError("Results belong to another language. Use its original workspace and language setting.")


def reviewed_cases(
    cases: list[dict[str, Any]], directory: Path
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    frozen = {case["case_id"]: case for case in cases}
    selected = dict(frozen)
    provenance: dict[str, list[dict[str, Any]]] = {}
    for path in sorted(directory.glob("regression-*.jsonl")):
        for record in read_jsonl(path):
            case_id = record["case_id"]
            if case_id not in frozen:
                raise ValueError("A new regression case requires a separately versioned dataset.")
            logical_case = {key: record[key] for key in frozen[case_id]}
            if logical_case != frozen[case_id]:
                raise ValueError("Reviewed regression changed the frozen question/rubric; do not mix evaluation versions.")
            lineage = record.get("lineage")
            if not isinstance(lineage, dict) or not lineage.get("source_trace_id"):
                raise ValueError("A reviewed regression must retain its source trace.")
            require_run_language(lineage)
            selected[case_id] = logical_case
            provenance.setdefault(case_id, []).append({"file": path.name, **lineage})
    return [selected[case["case_id"]] for case in cases], provenance


def parse_invocation_output(output: str) -> dict[str, Any]:
    normalized = output
    if normalized.startswith("HTTP/"):
        header, separator, body = normalized.partition("\r\n\r\n")
        if not separator:
            header, separator, body = normalized.partition("\n\n")
        if not separator:
            raise ValueError("azd raw HTTP output has no response body.")
        status = int(header.splitlines()[0].split()[1])
        if not 200 <= status < 300:
            raise ValueError(f"Agent returned HTTP {status}: {body[:500]}")
        lengths = [
            line.partition(":")[2].strip()
            for line in header.splitlines()[1:]
            if line.partition(":")[0].casefold() == "content-length"
        ]
        if lengths:
            if len(lengths) != 1:
                raise ValueError("Ambiguous HTTP Content-Length in azd output.")
            size = int(lengths[0])
            encoded = body.encode("utf-8")
            if size < 0 or len(encoded) < size:
                raise ValueError("The invocation HTTP response body is truncated.")
            result = json.loads(encoded[:size])
            validate_azd_suffix(encoded[size:].decode("utf-8"))
        else:
            result = parse_azd_json(body)
    else:
        result = parse_azd_json(normalized)
    if not isinstance(result, dict):
        raise ValueError("Expected a JSON object from the agent.")
    return result


def validate_response(result: dict[str, Any], payload: Invocation, config: RuntimeConfig) -> None:
    if result.get("error"):
        raise ValueError(f"Hosted invocation did not succeed: {result}")
    PolicyAnswer.model_validate({key: result[key] for key in ("answer", "decision", "citations")})
    for key, value in payload.model_dump().items():
        if result.get(key) != value:
            raise ValueError(f"Invocation response has mismatched {key}.")
    if result.get("language", "ko") != config.language:
        raise ValueError("Hosted language does not match this workspace. Bind and redeploy the correct language.")
    name, version = MODEL_SPECS[payload.model_key]
    if (
        result.get("deployment") != config.deployments[payload.model_key]
        or result.get("configured_model_id") != name
        or result.get("configured_model_version") != version
        or result.get("inference_api") != "foundry-account-chat-completions"
    ):
        raise ValueError("Hosted model routing does not match the verified deployment contract.")
    if result.get("prompt_version") != config.prompt_version or result.get("prompt_hash") != digest_prompt(config.prompt_version):
        raise ValueError("Hosted prompt does not match the selected local prompt. Redeploy before collecting.")


def invoke(
    payload: Invocation, *, local: bool = False, version: str | None = None,
    fresh_session: bool = False,
) -> dict[str, Any]:
    config = RuntimeConfig.from_env()
    request_file = RESULTS_DIR / "requests" / f"{payload.run_id}-{payload.model_key}-{payload.case_id}.json"
    write_json(request_file, payload.model_dump())
    args = [
        "ai", "agent", "invoke", config.agent_name, "--protocol", "invocations",
        "--input-file", str(request_file), "--output", "raw",
    ]
    if local:
        args.append("--local")
    elif version:
        args.extend(["--version", version])
    if fresh_session:
        args.append("--new-session")
    started = time.perf_counter()
    output = azd(*args, json_output=False)
    request_file.with_suffix(".http").write_text(output, encoding="utf-8")
    result = parse_invocation_output(output)
    validate_response(result, payload, config)
    result["client_latency_seconds"] = round(time.perf_counter() - started, 3)
    return result


def digest_prompt(version: str) -> str:
    return load_prompt(version, workshop_language())[1]


def smoke(local: bool, model_key: str = "sol", case_id: str = "D01") -> None:
    config = RuntimeConfig.from_env()
    agent_binding = None if local else binding()
    matches = [case for case in dataset("dev") if case["case_id"] == case_id]
    if len(matches) != 1:
        raise ValueError("Smoke case must identify one of the dev dataset cases.")
    case = matches[0]
    request = Invocation(
        query=case["query"], case_id=case["case_id"], model_key=model_key,
        run_id=f"smoke-{utc_stamp()}",
    )
    result = invoke(
        request, local=local, version=agent_binding["version"] if agent_binding else None,
        fresh_session=True,
    )
    result["agent_version"] = "local" if local else agent_binding["version"]
    path = RESULTS_DIR / f"smoke-{config.prompt_version}-{'local' if local else 'hosted'}-{utc_stamp()}.json"
    write_json(path, result)
    print(json.dumps({
        **{key: result[key] for key in ("answer", "decision", "citations", "source_ids", "trace_id", "model_key", "prompt_version", "agent_version", "input_tokens", "output_tokens")},
        "language": result.get("language", "ko"),
    }, ensure_ascii=False, indent=2))
    print(f"Saved: {path.relative_to(REPO_ROOT)}")


def collect(split: str, label: str, concurrency: int = 4) -> None:
    if concurrency not in {1, 2, 4}:
        raise ValueError("Concurrency must be 1, 2 or 4.")
    config = RuntimeConfig.from_env()
    run_dir = label_dir(label)
    if (run_dir / "manifest.json").exists():
        raise ValueError(f"Label {label} already exists. Use a new label; raw evidence is not overwritten.")
    verified = preflight()
    agent_binding = binding()
    cases = dataset(split)
    regressions: dict[str, list[dict[str, Any]]] = {}
    if split == "dev":
        cases, regressions = reviewed_cases(cases, FOUNDRY_DIR / "datasets")
    run_id = f"{label}-{utc_stamp()}"
    manifest = {
        "label": label, "run_id": run_id, "split": split, "language": config.language,
        "dataset_hash": digest(cases),
        "corpus_hash": digest(read_json(data_directory(config.language) / "policies.json")),
        "prompt_version": config.prompt_version, "prompt_hash": digest_prompt(config.prompt_version),
        "agent": agent_binding, "models": verified["models"],
        "expected_rows": len(cases) * len(MODEL_SPECS),
        "concurrency": concurrency,
        "reviewed_regressions": regressions,
        "status": "running", "started_at": utc_stamp(),
    }
    write_json(run_dir / "manifest.json", manifest)
    rows: list[dict[str, Any]] = []
    token_credential = credential()
    token_provider = get_bearer_token_provider(token_credential, "https://ai.azure.com/.default")
    expected_path = f"{config.project_endpoint}/agents/{config.agent_name}/endpoint/protocols/invocations"
    if agent_binding["endpoint"].split("?", 1)[0] != expected_path:
        raise ValueError("The hosted endpoint does not belong to the verified project/agent.")
    request = None
    try:
        with AIProjectClient(endpoint=config.project_endpoint, credential=token_credential) as project:
            session = project.agents.create_session(
                config.agent_name,
                version_indicator=VersionRefIndicator(agent_version=agent_binding["version"]),
            )
            manifest["session_id"] = session.agent_session_id
            manifest["transport"] = "pinned-version SDK session + authenticated HTTP"
            manifest["session_stopped"] = False
            write_json(run_dir / "manifest.json", manifest)
            endpoint = httpx.URL(agent_binding["endpoint"]).copy_merge_params(
                {"agent_session_id": session.agent_session_id}
            )
            with httpx.Client(timeout=180, follow_redirects=False) as client:
                def run_one(payload: Invocation, bearer: str) -> dict[str, Any]:
                    started = time.perf_counter()
                    response = client.post(
                        endpoint,
                        headers={"Authorization": f"Bearer {bearer}"},
                        json=payload.model_dump(),
                    )
                    raw_path = run_dir / "http" / f"{payload.model_key}-{payload.case_id}.json"
                    write_json(raw_path, {
                        "status": response.status_code, "body": response.text,
                        "request_id": response.headers.get("x-request-id"),
                        "session_id": response.headers.get("x-agent-session-id"),
                    })
                    response.raise_for_status()
                    row = response.json()
                    validate_response(row, payload, config)
                    row["client_latency_seconds"] = round(time.perf_counter() - started, 3)
                    return row

                with ThreadPoolExecutor(max_workers=concurrency) as pool:
                    for case in cases:
                        bearer = token_provider()
                        futures = {}
                        for key in MODEL_SPECS:
                            payload = Invocation(query=case["query"], case_id=case["case_id"], model_key=key, run_id=run_id)
                            futures[pool.submit(run_one, payload, bearer)] = payload
                        for future in as_completed(futures):
                            request = futures[future]
                            row = future.result()
                            row.update({
                                "row_id": f"{label}-{request.model_key}-{case['case_id']}", "split": split,
                                "agent_version": agent_binding["version"],
                                "ground_truth": case["ground_truth"],
                                "citation_required": case["citation_required"],
                                "business_grade": grade(row, case),
                                "regression_source_trace_ids": [
                                    item["source_trace_id"]
                                    for item in regressions.get(case["case_id"], [])
                                ],
                            })
                            rows.append(row)
                            write_jsonl(run_dir / "responses.jsonl", rows)
                            print(f"{len(rows):02d}/{manifest['expected_rows']} {row['row_id']} business={row['business_grade']['passed']} trace={row['trace_id']}")
    except (RuntimeError, ValueError, AzureError, httpx.HTTPError, subprocess.TimeoutExpired) as exc:
        write_json(run_dir / "failure.json", {
            "request": request.model_dump() if request else None,
            "error_type": type(exc).__name__, "error": str(exc), "completed_rows": len(rows),
        })
        manifest["status"] = "failed"
        write_json(run_dir / "manifest.json", manifest)
        raise
    validate_matrix(rows, cases)
    manifest["status"] = "completed"
    manifest["completed_at"] = utc_stamp()
    manifest["responses_hash"] = digest(rows)
    write_json(run_dir / "manifest.json", manifest)
    write_json(run_dir / "business-summary.json", summarize(rows))
    print(f"Session {manifest['session_id']} retained for telemetry/log inspection; monitor stops it after verification.")


def completed_rows(label: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    run_dir = label_dir(label)
    manifest = read_json(run_dir / "manifest.json")
    require_run_language(manifest)
    if manifest["status"] != "completed":
        raise ValueError(f"{label} is incomplete; do not score only the successful prefix.")
    rows = read_jsonl(run_dir / "responses.jsonl")
    for row in rows:
        require_run_language(row)
    cases = dataset(manifest["split"])
    if digest(cases) != manifest["dataset_hash"] or digest(rows) != manifest["responses_hash"]:
        raise ValueError("Dataset or raw responses changed after collection.")
    validate_matrix(rows, cases)
    return manifest, rows


def normalize_eval_items(items: list[dict[str, Any]], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if len(items) != len(rows):
        raise ValueError("Evaluation output count does not match input count.")
    normalized = []
    seen = set()
    for item in items:
        if item.get("status") in {"error", "errored", "failed"}:
            raise ValueError(f"Evaluation item {item.get('id')} has an execution error.")
        source = item.get("datasource_item") or {}
        row_id = source.get("row_id")
        if not row_id:
            source_id = str(item.get("datasource_item_id", ""))
            if not source_id.isdigit() or not 0 <= int(source_id) < len(rows):
                raise ValueError("Cannot map an evaluation result to its source row.")
            row_id = rows[int(source_id)]["row_id"]
        if row_id not in {row["row_id"] for row in rows} or row_id in seen:
            raise ValueError("Unknown or duplicate evaluation row ID.")
        seen.add(row_id)
        results = item.get("results")
        if not isinstance(results, list) or len(results) != 2:
            raise ValueError("Expected exactly two evaluator results per row.")
        for result in results:
            if result.get("error") or not isinstance(result.get("passed"), bool):
                raise ValueError(f"Evaluator error or missing pass/fail result for {row_id}.")
            score = result.get("score")
            if not isinstance(score, (int, float)) or isinstance(score, bool) or not math.isfinite(score):
                raise ValueError(f"Missing numeric native evaluator score for {row_id}.")
        normalized.append({"row_id": row_id, "results": results})
    return normalized


def evaluate(label: str, timeout: int = 600, retry_failed: bool = False) -> None:
    manifest, rows = completed_rows(label)
    run_evaluation(label, rows, manifest["agent"]["version"], manifest["run_id"], timeout, retry_failed)


def run_evaluation(
    label: str, rows: list[dict[str, Any]], agent_version: str | None,
    source_run_id: str, timeout: int = 600, retry_failed: bool = False,
) -> None:
    config = RuntimeConfig.from_env()
    load_state()
    run_dir = label_dir(label)
    evaluation_file = run_dir / "evaluation.json"
    existing = read_json(evaluation_file) if evaluation_file.exists() else None
    if existing is not None:
        require_run_language(existing)
    fields = ("row_id", "query", "response", "context", "ground_truth")
    items = [{field: (row["answer"] if field == "response" else row[field]) for field in fields} for row in rows]
    criteria = []
    with AIProjectClient(endpoint=config.project_endpoint, credential=credential(), allow_preview=True) as project:
        for name in ("groundedness", "relevance"):
            cache = FOUNDRY_DIR / "evaluators" / f"{name}.json"
            version = read_json(cache)["version"] if cache.exists() else "latest"
            evaluator = project.beta.evaluators.get_version(f"builtin.{name}", version).as_dict()
            write_json(cache, evaluator)
            init_schema = evaluator["definition"]["init_parameters"]
            if "deployment_name" not in init_schema["properties"]:
                raise ValueError(f"Unexpected {name} evaluator initialization contract.")
            criteria.append(TestingCriterionAzureAIEvaluator(
                type="azure_ai_evaluator", name=name,
                evaluator_name=f"builtin.{name}", evaluator_version=evaluator["version"],
                initialization_parameters={"deployment_name": required("LAB_AUX_DEPLOYMENT"), "threshold": 4},
                data_mapping={
                    "query": "{{item.query}}", "response": "{{item.response}}",
                    **({"context": "{{item.context}}"} if name == "groundedness" else {}),
                },
            ))
    suite = {
        "data_source_config": {
            "type": "custom",
            "item_schema": {"type": "object", "properties": {field: {"type": "string"} for field in fields}, "required": list(fields)},
        },
        "testing_criteria": criteria,
        "judge_deployment": required("LAB_AUX_DEPLOYMENT"),
    }
    write_json(FOUNDRY_DIR / "suites" / f"{label}.json", suite)
    write_jsonl(FOUNDRY_DIR / "datasets" / f"{label}-evaluation.jsonl", items)
    record = existing if existing is not None else {
        "label": label, "language": config.language, "input_hash": digest(items), "suite_hash": digest(suite),
        "agent_version": agent_version, "expected_rows": len(rows),
        "source_kind": "hosted_agent_outputs" if agent_version else "specified_judge_calibration",
    }
    if record["input_hash"] != digest(items) or record["suite_hash"] != digest(suite):
        raise ValueError("Existing evaluation has different inputs or evaluators.")
    if retry_failed:
        errors = (record.get("run", {}).get("result_counts") or {}).get("errored") or 0
        if record.get("status") not in {"failed", "canceled", "cancelled"} and errors == 0:
            raise ValueError("--retry-failed requires a recorded failed/errored run.")
        write_json(run_dir / f"evaluation-attempt-{utc_stamp()}.json", record)
        for field in ("run_id", "status", "run"):
            record.pop(field, None)
        write_json(evaluation_file, record)
    with AIProjectClient(endpoint=config.project_endpoint, credential=credential()) as project:
        with project.get_openai_client() as client:
            if "evaluation_id" not in record:
                created = client.evals.create(
                    name=f"{config.prefix}-{label}",
                    data_source_config=suite["data_source_config"],
                    testing_criteria=criteria,
                    metadata={
                        "lab_run": source_run_id,
                        "lab_language": config.language,
                        "source_kind": record["source_kind"],
                        **({"lab_agent": config.agent_name} if agent_version else {}),
                    },
                )
                record["evaluation_id"] = created.id
                write_json(evaluation_file, record)
            if "run_id" not in record:
                run = client.evals.runs.create(
                    eval_id=record["evaluation_id"], name=f"{label}-{source_run_id}",
                    data_source={"type": "jsonl", "source": {"type": "file_content", "content": [{"item": item} for item in items]}},
                )
                record["run_id"] = run.id
                write_json(evaluation_file, record)
            deadline = time.monotonic() + timeout
            while True:
                run = client.evals.runs.retrieve(record["run_id"], eval_id=record["evaluation_id"])
                record["status"] = run.status
                record["run"] = run.model_dump(mode="json")
                write_json(evaluation_file, record)
                if run.status in {"completed", "failed", "canceled", "cancelled"}:
                    break
                if time.monotonic() >= deadline:
                    raise TimeoutError("Evaluation is still running. Re-run evaluate with the same label to resume without creating another run.")
                time.sleep(5)
            if run.status != "completed":
                raise ValueError(f"Foundry evaluation did not complete: {run.status}. Inspect {evaluation_file}.")
            counts = record["run"].get("result_counts") or {}
            if counts.get("errored", 0):
                raise ValueError(f"Foundry evaluation has {counts['errored']} errored rows.")
            raw_items = [
                item.model_dump(mode="json")
                for item in client.evals.runs.output_items.list(run_id=record["run_id"], eval_id=record["evaluation_id"])
            ]
            write_json(run_dir / "evaluation-output-raw.json", raw_items)
            results = normalize_eval_items(raw_items, rows)
            write_json(run_dir / "evaluation-results.json", results)
    print(f"Foundry evaluation completed: {record['evaluation_id']} / {record['run_id']} ({len(results)} rows)")
    if record["run"].get("report_url"):
        print(record["run"]["report_url"])


def calibrate(timeout: int = 600, retry_failed: bool = False) -> None:
    english = workshop_language() == "en"
    context = (
        "Hanbit Technology's synthetic domestic business travel lodging limit is KRW 180000 per night."
        if english else "한빛기술의 합성 국내 출장 숙박비 한도는 1박 180000원이다."
    )
    query = "What is the domestic business travel lodging limit?" if english else "국내 출장 숙박비 한도는 얼마인가요?"
    expected = "KRW 180000 per night" if english else "1박 180000원"
    rows = [
        {
            "row_id": "calibration-grounded", "query": query,
            "answer": "The domestic business travel lodging limit is KRW 180000 per night." if english else "국내 출장 숙박비 한도는 1박 180000원입니다.",
            "context": context, "ground_truth": expected,
        },
        {
            "row_id": "calibration-ungrounded", "query": query,
            "answer": "The domestic business travel lodging limit is KRW 990000 per night." if english else "국내 출장 숙박비 한도는 1박 990000원입니다.",
            "context": context, "ground_truth": expected,
        },
    ]
    label = "judge-calibration"
    run_evaluation(label, rows, None, f"calibration-{utc_stamp()}", timeout, retry_failed)
    results = read_json(label_dir(label) / "evaluation-results.json")
    groundedness = {
        row["row_id"]: next(item["passed"] for item in row["results"] if item["name"] == "groundedness")
        for row in results
    }
    passed = groundedness == {"calibration-grounded": True, "calibration-ungrounded": False}
    write_json(label_dir(label) / "calibration.json", {
        "source": "two explicitly specified examples, not target-model outputs",
        "groundedness": groundedness, "passed": passed,
    })
    if not passed:
        raise ValueError("Judge calibration did not separate grounded and fabricated claims. Review before using scores.")
    print("Judge calibration passed; these two manual examples are not counted as hosted-model outputs.")


def compare(labels: list[str]) -> dict[str, Any]:
    if not labels or len(labels) != len(set(labels)):
        raise ValueError("Comparison labels must be nonempty and unique.")
    report: dict[str, Any] = {"labels": {}, "paired_comparisons": [], "comparison_notes": []}
    dev_hashes = set()
    corpus_hashes = set()
    concurrency_values = set()
    dev_rows: dict[str, list[dict[str, Any]]] = {}
    for label in labels:
        manifest, rows = completed_rows(label)
        if manifest["split"] == "dev":
            dev_hashes.add(manifest["dataset_hash"])
            dev_rows[label] = rows
        corpus_hashes.add(manifest["corpus_hash"])
        concurrency_values.add(manifest["concurrency"])
        summary = summarize(rows)
        eval_path = label_dir(label) / "evaluation-results.json"
        if eval_path.exists():
            eval_results = {item["row_id"]: item["results"] for item in read_json(eval_path)}
            if set(eval_results) != {row["row_id"] for row in rows}:
                raise ValueError("Evaluation results do not cover the exact response set.")
            for key in MODEL_SPECS:
                selected = [row for row in rows if row["model_key"] == key]
                summary[key]["foundry_evaluators"] = {}
                for name in ("groundedness", "relevance"):
                    scores = [result for row in selected for result in eval_results[row["row_id"]] if result["name"] == name]
                    if len(scores) != len(selected):
                        raise ValueError(f"Incomplete {name} evaluator results.")
                    summary[key]["foundry_evaluators"][name] = {
                        "native_mean_score": sum(score["score"] for score in scores) / len(scores),
                        "native_passed": sum(score["passed"] for score in scores),
                        "total": len(scores),
                    }
        else:
            report["comparison_notes"].append(f"{label}: cloud evaluation not yet verified.")
        contexts: dict[str, set[str]] = {}
        for row in rows:
            contexts.setdefault(row["case_id"], set()).add(row["context_hash"])
        differing = [case for case, hashes in contexts.items() if len(hashes) > 1]
        report["labels"][label] = {
            "language": manifest.get("language", "ko"),
            "split": manifest["split"], "agent_version": manifest["agent"]["version"],
            "dataset_hash": manifest["dataset_hash"], "prompt_hash": manifest["prompt_hash"],
            "models": summary, "different_context_cases": differing,
            "business_failures": [
                {"row_id": row["row_id"], "trace_id": row["trace_id"], "checks": row["business_grade"]["checks"]}
                for row in rows if not row["business_grade"]["passed"]
            ],
        }
    if len(dev_hashes) > 1 or len(corpus_hashes) > 1:
        raise ValueError("Before/after comparison requires identical dev dataset and knowledge corpus.")
    if len(concurrency_values) != 1:
        raise ValueError("Use the same concurrency for compared experiment runs.")
    if len(dev_rows) > 1:
        baseline = next(iter(dev_rows))
        for candidate in list(dev_rows)[1:]:
            report["paired_comparisons"].append({
                "baseline": baseline, "candidate": candidate,
                "models": paired_outcomes(dev_rows[baseline], dev_rows[candidate]),
            })
    changed_between_runs = any(
        model["context_changed_case_ids"]
        for pair in report["paired_comparisons"] for model in pair["models"].values()
    )
    if changed_between_runs or any(item["different_context_cases"] for item in report["labels"].values()):
        report["comparison_notes"].append("Retrieval contexts differ for some cases; these are end-to-end results, not isolated model rankings.")
    report["comparison_notes"].append(
        "Wilson 95% intervals assume independent Bernoulli trials. These small, curated datasets are not "
        "representative production samples; do not pool models or languages or treat the intervals as release approval."
    )
    report["comparison_notes"].append("A business gate is not automatic deployment approval. Inspect Foundry scores, holdout and human review.")
    write_json(RESULTS_DIR / "comparison.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


def summary_table(labels: list[str]) -> str:
    """Print the saved comparison as a compact table; reads local results only."""
    comparison_path = RESULTS_DIR / "comparison.json"
    if not comparison_path.exists():
        raise ValueError(f"{comparison_path} is missing; run compare --labels {' '.join(labels)} first.")
    report = read_json(comparison_path)
    missing = [label for label in labels if label not in report.get("labels", {})]
    if missing:
        raise ValueError(f"comparison.json lacks {', '.join(missing)}; run compare --labels {' '.join(labels)} first.")
    sections = [report["labels"][label] for label in labels]
    last = labels[-1]
    lines: list[str] = []

    responses_path = label_dir(last) / "responses.jsonl"
    if len(labels) > 1 and responses_path.exists():
        candidates = read_jsonl(responses_path)
        for path in sorted((FOUNDRY_DIR / "datasets").glob("regression-*.jsonl")):
            case = read_jsonl(path)[0]
            lineage = case["lineage"]
            for row in candidates:
                if row["case_id"] != case["case_id"] or row["model_key"] != lineage["model_key"]:
                    continue
                failed = [check for check, ok in row["business_grade"]["checks"].items() if not ok]
                outcome = "passed" if row["business_grade"]["passed"] else f"failed ({', '.join(failed)})"
                carried = "yes" if lineage["source_trace_id"] in row.get("regression_source_trace_ids", []) else "no"
                lines.append(
                    f"Reviewed case {lineage['source_row_id']} -> {row['row_id']}: business {outcome}; "
                    f"source trace carried: {carried}"
                )
    if lines:
        lines.append("")

    def across(render: Any) -> str:
        return " -> ".join(render(section) for section in sections)

    def evaluator(model: dict[str, Any], name: str) -> str:
        score = model.get("foundry_evaluators", {}).get(name)
        return f"{score['native_passed']}/{score['total']}" if score else "n/a"

    table = [["model", "business", "required citations", "groundedness", "relevance", "tokens in/out", "p50/p95 s"]]
    for key in MODEL_SPECS:
        table.append([
            key,
            across(lambda section: f"{section['models'][key]['business_passed']}/{section['models'][key]['total']}"),
            across(lambda section: (
                f"{section['models'][key]['required_citation_passed']}/"
                f"{section['models'][key]['required_citation_total']}"
            )),
            across(lambda section: evaluator(section["models"][key], "groundedness")),
            across(lambda section: evaluator(section["models"][key], "relevance")),
            across(lambda section: f"{section['models'][key]['input_tokens']}/{section['models'][key]['output_tokens']}"),
            across(lambda section: (
                f"{section['models'][key]['latency_p50_seconds']:.2f}/"
                f"{section['models'][key]['latency_p95_seconds']:.2f}"
            )),
        ])
    widths = [max(len(row[column]) for row in table) for column in range(len(table[0]))]
    lines.extend("  ".join(cell.ljust(width) for cell, width in zip(row, widths)).rstrip() for row in table)

    business = [
        f"{item['row_id']} ({', '.join(check for check, ok in item['checks'].items() if not ok)})"
        for item in report["labels"][last]["business_failures"]
    ]
    lines.extend(["", f"{last} business-check failures: {', '.join(business) or 'none'}"])
    eval_path = label_dir(last) / "evaluation-results.json"
    if eval_path.exists():
        native = [
            f"{row['row_id']} ({result['name']} {'n/a' if result.get('score') is None else format(result['score'], 'g')})"
            for row in read_json(eval_path) for result in row["results"] if not result["passed"]
        ]
        lines.append(f"{last} Foundry-score failures: {', '.join(native) or 'none'}")
    for pair in report.get("paired_comparisons", []):
        if pair["baseline"] not in labels or pair["candidate"] not in labels:
            continue
        lines.extend(["", f"Paired business checks {pair['baseline']} -> {pair['candidate']} (same model + case):"])
        for key in MODEL_SPECS:
            item = pair["models"][key]
            regressions = ", ".join(item["regressed_case_ids"]) or "none"
            contexts = ", ".join(item["context_changed_case_ids"]) or "none"
            lines.append(
                f"{key}: {item['fail_to_pass']} fail->pass; {item['pass_to_fail']} pass->fail "
                f"(cases: {regressions}); changed context: {contexts}"
            )
    intervals = [
        (key, report["labels"][last]["models"][key].get("business_pass_rate_wilson_95"))
        for key in MODEL_SPECS
    ]
    if all(interval is not None for _, interval in intervals):
        lines.extend(["", f"{last} business pass rate: illustrative Wilson 95% intervals"])
        for key, interval in intervals:
            lines.append(f"{key}: [{interval['lower']:.1%}, {interval['upper']:.1%}]")
        lines.append("Independent-trial assumption only; curated cases do not establish production accuracy.")
    text = "\n".join(lines)
    print(text)
    return text


def show_row(label: str, row_id: str) -> dict[str, Any]:
    """Print one saved answer beside its fixed reference; reads local files only and calls no model."""
    manifest, rows = completed_rows(label)
    selected = [row for row in rows if row["row_id"] == row_id]
    if len(selected) != 1:
        raise ValueError(f"Unknown row ID for {label}: {row_id!r}. Copy a row ID from the summary or collect output.")
    row = selected[0]
    case = next(item for item in dataset(manifest["split"]) if item["case_id"] == row["case_id"])
    view = {
        "row_id": row_id, "case_id": row["case_id"], "model_key": row["model_key"], "trace_id": row["trace_id"],
        "query": row["query"],
        "saved_response": {key: row[key] for key in ("answer", "decision", "citations", "source_ids")},
        "business_checks": row["business_grade"]["checks"],
        "fixed_reference": {key: case[key] for key in (
            "category", "ground_truth", "expected_decision", "required_numbers", "allowed_citations", "citation_required",
        )},
        "files": {
            "saved_response": (label_dir(label) / "responses.jsonl").relative_to(REPO_ROOT).as_posix(),
            "fixed_reference": (data_directory() / f"{manifest['split']}.jsonl").relative_to(REPO_ROOT).as_posix(),
        },
    }
    print(json.dumps(view, ensure_ascii=False, indent=2))
    return view


def feedback(label: str, row_id: str, reason: str, reviewer: str = "human") -> None:
    manifest, rows = completed_rows(label)
    if manifest["split"] != "dev":
        raise ValueError("Holdout data cannot be harvested into prompt-development regression data.")
    if len(reason.strip()) < 10:
        raise ValueError("Record a meaningful review reason.")
    if reviewer not in {"human", "assistant"}:
        raise ValueError("Reviewer must be human or assistant.")
    selected = [row for row in rows if row["row_id"] == row_id]
    if len(selected) != 1:
        raise ValueError("Unknown row ID.")
    row = selected[0]
    telemetry = read_json(label_dir(label) / "telemetry.json")
    if row["trace_id"] not in {item["trace_id"] for item in telemetry["rows"]}:
        raise ValueError("The selected response has not been verified in real telemetry.")
    case = next(item for item in dataset("dev") if item["case_id"] == row["case_id"])
    record = {
        **case,
        "lineage": {
            "language": manifest.get("language", "ko"),
            "source_trace_id": row["trace_id"], "source_row_id": row_id,
            "agent_version": row["agent_version"], "model_key": row["model_key"],
            "prompt_hash": row["prompt_hash"], "context_hash": row["context_hash"],
            "source_run": manifest["run_id"], "review_reason": reason,
            "reviewer_type": reviewer,
            "ground_truth_source": "fixed dev reference dataset; not the evaluated model response",
        },
    }
    destination = FOUNDRY_DIR / "datasets" / f"regression-{row_id}.jsonl"
    if destination.exists():
        raise ValueError("This reviewed regression record already exists; do not overwrite lineage.")
    write_jsonl(destination, [record])
    print(f"Reviewed trace-to-dataset record saved: {destination.relative_to(REPO_ROOT)}")


def verify_evidence(baseline: str, candidate: str, holdout: str) -> dict[str, Any]:
    labels = [baseline, candidate, holdout]
    loaded = {label: completed_rows(label) for label in labels}
    base_manifest, base_rows = loaded[baseline]
    candidate_manifest, candidate_rows = loaded[candidate]
    holdout_manifest, holdout_rows = loaded[holdout]
    if [loaded[label][0]["split"] for label in labels] != ["dev", "dev", "holdout"]:
        raise ValueError("Expected dev baseline, dev candidate and separate holdout.")
    if base_manifest["dataset_hash"] != candidate_manifest["dataset_hash"]:
        raise ValueError("The dev dataset changed between baseline and candidate.")
    if candidate_manifest["prompt_hash"] != holdout_manifest["prompt_hash"]:
        raise ValueError("The candidate prompt changed before holdout.")
    if base_manifest["agent"]["version"] == candidate_manifest["agent"]["version"]:
        raise ValueError("The improvement must be a new hosted agent version.")
    if candidate_manifest["agent"]["version"] != holdout_manifest["agent"]["version"]:
        raise ValueError("Holdout must use the frozen candidate agent version.")
    expected_rows = [
        len(dataset(split)) * len(MODEL_SPECS) for split in ("dev", "dev", "holdout")
    ]
    if [len(base_rows), len(candidate_rows), len(holdout_rows)] != expected_rows:
        raise ValueError(
            "The final comparison must contain exactly "
            + " + ".join(str(count) for count in expected_rows) + " model outputs."
        )
    all_traces = {row["trace_id"] for _, rows in loaded.values() for row in rows}
    if len(all_traces) != sum(expected_rows):
        raise ValueError(f"Expected {sum(expected_rows)} distinct trace IDs.")
    expected_old_traces = {row["trace_id"] for row in base_rows}
    reused_traces = {
        trace_id for row in candidate_rows
        for trace_id in row.get("regression_source_trace_ids", [])
    }
    if not reused_traces or not reused_traces <= expected_old_traces:
        raise ValueError("The reviewed baseline trace was not consumed by candidate regression evaluation.")
    runs = []
    criteria_hashes = set()
    for label, (manifest, rows) in loaded.items():
        evaluation = read_json(label_dir(label) / "evaluation.json")
        require_run_language(evaluation)
        results = read_json(label_dir(label) / "evaluation-results.json")
        telemetry = read_json(label_dir(label) / "telemetry.json")
        require_run_language(telemetry)
        suite = read_json(FOUNDRY_DIR / "suites" / f"{label}.json")
        criteria_hashes.add(digest(suite["testing_criteria"]))
        counts = evaluation["run"]["result_counts"]
        if (
            evaluation["status"] != "completed"
            or counts["total"] != len(rows)
            or (counts.get("errored") or 0) != 0
            or len(results) != len(rows)
        ):
            raise ValueError(f"{label}: incomplete or errored Foundry evaluation.")
        if {item["row_id"] for item in results} != {row["row_id"] for row in rows}:
            raise ValueError(f"{label}: evaluation rows do not match model outputs.")
        for item in results:
            for result in item["results"]:
                if not 1 <= result["score"] <= 5 or result["passed"] != (result["score"] >= 4):
                    raise ValueError("Unexpected native evaluator scale/threshold.")
        if (
            not telemetry["complete"]
            or {item["trace_id"] for item in telemetry["rows"]} != {row["trace_id"] for row in rows}
            or not all(item["success"] and item["sample_weight"] == 1 for item in telemetry["rows"])
        ):
            raise ValueError(f"{label}: full, unsampled successful telemetry is not verified.")
        for key in MODEL_SPECS:
            if not any(
                row["model_key"] == key
                and any(activity["type"] == "modelQueryPlanning" for activity in row["activity"])
                for row in rows
            ):
                raise ValueError(f"{label}/{key}: no real Foundry IQ planning evidence.")
        runs.append({
            "label": label, "agent_version": manifest["agent"]["version"],
            "rows": len(rows), "traces": telemetry["observed_trace_count"],
            "evaluation_id": evaluation["evaluation_id"], "evaluation_run_id": evaluation["run_id"],
        })
    if len(criteria_hashes) != 1:
        raise ValueError("Evaluator definitions changed during the comparison.")
    comparison = compare(labels)
    evidence = {
        "language": workshop_language(),
        "component_execution_verified": True, "primary_model_outputs": sum(expected_rows),
        "distinct_verified_traces": len(all_traces), "models": MODEL_SPECS, "runs": runs,
        "reused_baseline_trace_ids": sorted(reused_traces),
        "candidate_quality_gates": {
            key: {
                "dev": comparison["labels"][candidate]["models"][key]["business_gate"],
                "holdout": comparison["labels"][holdout]["models"][key]["business_gate"],
            } for key in MODEL_SPECS
        },
        "production_release_approved": False,
    }
    write_json(RESULTS_DIR / "verified-evidence.json", evidence)
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    return evidence
