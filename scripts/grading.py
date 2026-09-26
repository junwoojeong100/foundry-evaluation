import math
import re
from statistics import NormalDist
from typing import Any


def numeric_values(text: str) -> set[str]:
    values = set(re.findall(r"\d[\d,]*(?:\.\d+)?", text))
    normalized = {value.replace(",", "") for value in values}
    for match in re.finditer(r"(\d+(?:\.\d+)?)\s*만\s*(?:원)?", text):
        normalized.add(str(round(float(match.group(1)) * 10000)))
    return normalized


def grade(row: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    citations = row["citations"]
    sources = set(row["source_ids"])
    allowed = set(case["allowed_citations"])
    checks = {
        "decision": row["decision"] == case["expected_decision"],
        "required_numbers": set(case["required_numbers"]) <= numeric_values(row["answer"]),
        "citations_retrieved": all(citation in sources for citation in citations),
        "citations_relevant": all(citation in allowed for citation in citations),
        "citation_present": not case["citation_required"] or bool(citations),
    }
    return {"passed": all(checks.values()), "checks": checks}


def validate_matrix(rows: list[dict[str, Any]], cases: list[dict[str, Any]]) -> None:
    from contracts import MODEL_SPECS

    ids = [case["case_id"] for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate case IDs in dataset.")
    expected = {(key, case_id) for key in MODEL_SPECS for case_id in ids}
    actual = [(row["model_key"], row["case_id"]) for row in rows]
    if len(actual) != len(set(actual)) or set(actual) != expected:
        raise ValueError("Incomplete/duplicate model matrix; errors cannot be omitted.")
    if any(row.get("error") for row in rows):
        raise ValueError("An invocation failed; do not evaluate a success-only subset.")
    for row in rows:
        if not re.fullmatch(r"[0-9a-f]{32}", row["trace_id"]) or int(row["trace_id"], 16) == 0:
            raise ValueError("A real nonzero trace ID is required for every invocation.")
        if not row.get("prompt_hash") or not row.get("context_hash"):
            raise ValueError("Missing prompt/evidence lineage.")
    if len({row["prompt_hash"] for row in rows}) != 1:
        raise ValueError("Prompt changed during collection.")


def percentile(values: list[float], percent: float) -> float:
    if not values:
        raise ValueError("Cannot calculate a percentile from missing observations.")
    return sorted(values)[max(0, math.ceil(len(values) * percent) - 1)]


def wilson_interval(passed: int, total: int) -> dict[str, float]:
    """Two-sided 95% Wilson interval; assumes independent Bernoulli trials."""
    if type(passed) is not int or type(total) is not int or total <= 0 or not 0 <= passed <= total:
        raise ValueError("Wilson interval requires integer counts with 0 <= passed <= total and total > 0.")
    z = NormalDist().inv_cdf(0.975)
    rate = passed / total
    denominator = 1 + z * z / total
    center = (rate + z * z / (2 * total)) / denominator
    radius = z * math.sqrt(rate * (1 - rate) / total + z * z / (4 * total * total)) / denominator
    return {"lower": max(0.0, center - radius), "upper": min(1.0, center + radius)}


def paired_outcomes(
    baseline: list[dict[str, Any]], candidate: list[dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    """Match complete response sets by model and case, never by file order."""
    def index(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
        if not rows:
            raise ValueError("Paired comparison requires nonempty response sets.")
        indexed = {}
        for row in rows:
            key = (row["model_key"], row["case_id"])
            if key in indexed:
                raise ValueError("Duplicate model/case pair in comparison.")
            if row.get("error") or type(row["business_grade"]["passed"]) is not bool:
                raise ValueError("Paired comparison requires valid boolean grades, not invocation errors.")
            if not row.get("context_hash"):
                raise ValueError("Paired comparison requires retrieval context hashes.")
            indexed[key] = row
        return indexed

    before, after = index(baseline), index(candidate)
    if before.keys() != after.keys():
        raise ValueError("Paired comparison requires exactly the same model/case pairs; missing rows cannot be dropped.")
    result: dict[str, dict[str, Any]] = {}
    for model, case_id in sorted(before):
        key = (model, case_id)
        previous, current = before[key]["business_grade"]["passed"], after[key]["business_grade"]["passed"]
        entry = result.setdefault(model, {
            "total": 0, "both_pass": 0, "both_fail": 0, "fail_to_pass": 0, "pass_to_fail": 0,
            "improved_case_ids": [], "regressed_case_ids": [], "context_changed_case_ids": [],
        })
        entry["total"] += 1
        if previous and current:
            entry["both_pass"] += 1
        elif not previous and not current:
            entry["both_fail"] += 1
        elif current:
            entry["fail_to_pass"] += 1
            entry["improved_case_ids"].append(case_id)
        else:
            entry["pass_to_fail"] += 1
            entry["regressed_case_ids"].append(case_id)
        if before[key]["context_hash"] != after[key]["context_hash"]:
            entry["context_changed_case_ids"].append(case_id)
    for entry in result.values():
        entry["pass_rate_delta"] = (entry["fail_to_pass"] - entry["pass_to_fail"]) / entry["total"]
    return result


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    from contracts import MODEL_SPECS

    summaries: dict[str, Any] = {}
    for key in MODEL_SPECS:
        selected = [row for row in rows if row["model_key"] == key]
        if not selected:
            raise ValueError(f"Missing model {key}.")
        required = [row for row in selected if row["citation_required"]]
        passed = sum(row["business_grade"]["passed"] for row in selected)
        cited = sum(
            row["business_grade"]["checks"]["citation_present"]
            and row["business_grade"]["checks"]["citations_retrieved"]
            and row["business_grade"]["checks"]["citations_relevant"]
            for row in required
        )
        summaries[key] = {
            "total": len(selected),
            "business_passed": passed,
            "business_pass_rate": passed / len(selected),
            "business_pass_rate_wilson_95": wilson_interval(passed, len(selected)),
            "check_pass_counts": {
                check: sum(row["business_grade"]["checks"][check] for row in selected)
                for check in selected[0]["business_grade"]["checks"]
            },
            "required_citation_passed": cited,
            "required_citation_total": len(required),
            "input_tokens": sum(row["input_tokens"] for row in selected),
            "output_tokens": sum(row["output_tokens"] for row in selected),
            "latency_p50_seconds": percentile([row["latency_seconds"] for row in selected], 0.5),
            "latency_p95_seconds": percentile([row["latency_seconds"] for row in selected], 0.95),
            "business_gate": passed / len(selected) >= 0.8 and cited == len(required),
        }
    return summaries
