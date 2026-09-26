"""Credential-free evaluation lesson using authored examples, never cloud results."""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from grading import grade, paired_outcomes

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_KIND = "synthetic_offline_demonstration"
VARIANTS = ("baseline", "candidate")


def require_text(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a nonempty string.")


def require_strings(value: Any, field: str) -> None:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"{field} must be a list of nonempty strings.")
    if len(value) != len(set(value)):
        raise ValueError(f"{field} must not contain duplicates.")


def validate_fixture(document: Any, language: str) -> None:
    if not isinstance(document, dict) or document.get("evidence_kind") != EVIDENCE_KIND:
        raise ValueError("Only explicitly marked synthetic offline fixtures are accepted.")
    if type(document.get("schema_version")) is not int or document["schema_version"] != 1:
        raise ValueError("Unsupported offline fixture schema_version.")
    if document.get("language") != language:
        raise ValueError("Fixture language does not match --language.")
    policy = document.get("policy")
    if not isinstance(policy, dict):
        raise ValueError("A synthetic policy is required.")
    for field in ("id", "text"):
        require_text(policy.get(field), f"policy.{field}")
    cases = document.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("Offline fixtures require nonempty cases.")
    seen = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("Every case must be an object.")
        for field in ("case_id", "category", "query", "expected_decision"):
            require_text(case.get(field), field)
        if case["case_id"] in seen:
            raise ValueError(f"Duplicate offline case: {case['case_id']}.")
        seen.add(case["case_id"])
        for field in ("source_ids", "allowed_citations", "required_numbers"):
            require_strings(case.get(field), field)
        if set(case["source_ids"]) - {policy["id"]} or set(case["allowed_citations"]) - {policy["id"]}:
            raise ValueError("Case references an unknown synthetic policy.")
        if type(case.get("citation_required")) is not bool:
            raise ValueError("citation_required must be boolean.")
        responses = case.get("responses")
        if not isinstance(responses, dict) or set(responses) != set(VARIANTS):
            raise ValueError("Every case requires exactly baseline and candidate responses.")
        for name, response in responses.items():
            if not isinstance(response, dict):
                raise ValueError(f"{name} response must be an object.")
            for field in ("answer", "decision", "human_reference_reason"):
                require_text(response.get(field), f"{name}.{field}")
            require_strings(response.get("citations"), f"{name}.citations")
            if type(response.get("human_reference_passed")) is not bool:
                raise ValueError("human_reference_passed must be boolean, not an inferred judge score.")


def evaluate_fixture(language: str) -> dict[str, Any]:
    if language not in {"en", "ko"}:
        raise ValueError("Language must be en or ko.")
    path = ROOT / "data" / "offline" / f"{language}.json"
    raw = path.read_bytes()
    document = json.loads(raw)
    validate_fixture(document, language)
    rows = []
    paired_rows: dict[str, list[dict[str, Any]]] = {variant: [] for variant in VARIANTS}
    for case in document["cases"]:
        context = document["policy"]["text"] if case["source_ids"] else ""
        responses = {}
        for variant in VARIANTS:
            response = case["responses"][variant]
            business_grade = grade({**response, "source_ids": case["source_ids"]}, case)
            responses[variant] = {**response, "business_grade": business_grade}
            paired_rows[variant].append({
                "model_key": "authored_examples", "case_id": case["case_id"],
                "business_grade": business_grade,
                "context_hash": hashlib.sha256(context.encode("utf-8")).hexdigest(),
            })
        rows.append({
            **{key: value for key, value in case.items() if key != "responses"},
            "context": context, "responses": responses,
        })
    summaries = {}
    for variant in VARIANTS:
        summaries[variant] = {
            "total": len(rows),
            "business_passed": sum(row["responses"][variant]["business_grade"]["passed"] for row in rows),
            "human_reference_passed": sum(row["responses"][variant]["human_reference_passed"] for row in rows),
            "code_reference_disagreement_case_ids": [
                row["case_id"] for row in rows
                if row["responses"][variant]["business_grade"]["passed"]
                != row["responses"][variant]["human_reference_passed"]
            ],
        }
    return {
        "schema_version": 1, "evidence_kind": EVIDENCE_KIND, "language": language,
        "source": path.relative_to(ROOT).as_posix(), "fixture_sha256": hashlib.sha256(raw).hexdigest(),
        "response_origin": "authored teaching examples, not model generations",
        "human_reference_origin": "authored answer key, not a new human or LLM review",
        "azure_calls_made": 0, "model_calls_made": 0, "foundry_evaluation_performed": False,
        "eligible_for_cloud_verification": False, "production_release_approved": False,
        "summaries": summaries,
        "paired": paired_outcomes(paired_rows["baseline"], paired_rows["candidate"])["authored_examples"],
        "rows": rows,
    }


def render_report(report: dict[str, Any]) -> str:
    korean = report["language"] == "ko"
    title = "레벨 0: 오프라인 평가 실습" if korean else "Level 0: offline evaluation lesson"
    warning = (
        "직접 작성한 합성 답변을 채점한 결과입니다. 모델·Azure·Foundry 평가 호출은 0회이며, 실제 실행 증거가 아닙니다."
        if korean else
        "These are authored synthetic answers. There were zero model, Azure, or Foundry evaluation calls. "
        "This is not live execution evidence."
    )
    lines = [
        f"# {title}", "", warning, "",
        f"`evidence_kind: {EVIDENCE_KIND}` · `production_release_approved: false`", "",
        "| variant | business checks | authored human reference |",
        "|---|---:|---:|",
    ]
    for variant in VARIANTS:
        counts = report["summaries"][variant]
        lines.append(
            f"| {variant} | {counts['business_passed']}/{counts['total']} | "
            f"{counts['human_reference_passed']}/{counts['total']} |"
        )
    pair = report["paired"]
    regressions = ", ".join(pair["regressed_case_ids"]) or "none"
    disagreements = ", ".join(report["summaries"]["candidate"]["code_reference_disagreement_case_ids"]) or "none"
    lines.extend([
        "", f"fail->pass: {pair['fail_to_pass']} · pass->fail: {pair['pass_to_fail']} ({regressions})",
        f"candidate code/reference disagreements: {disagreements}", "",
        "| case | baseline checks | candidate checks | candidate reference | failed candidate checks |",
        "|---|---|---|---|---|",
    ])
    for row in report["rows"]:
        before, after = row["responses"]["baseline"], row["responses"]["candidate"]
        failed = ", ".join(key for key, passed in after["business_grade"]["checks"].items() if not passed) or "none"
        outcomes = [
            "PASS" if passed else "FAIL" for passed in (
                before["business_grade"]["passed"], after["business_grade"]["passed"], after["human_reference_passed"],
            )
        ]
        lines.append(f"| {row['case_id']} | {' | '.join(outcomes)} | {failed} |")
    lines.extend(["", "## " + ("후보 답변 검토" if korean else "Review the candidate answers"), ""])
    for row in report["rows"]:
        after = row["responses"]["candidate"]
        lines.extend([
            f"### {row['case_id']}", "",
            row["query"], "",
            after["answer"], "",
            f"`decision: {after['decision']}` · `expected: {row['expected_decision']}`", "",
            after["human_reference_reason"], "",
        ])
    lines.extend([
        "## " + ("증거의 경계" if korean else "Evidence boundaries"), "",
        (
            "평균이 올라도 기존 통과 사례가 실패할 수 있고, 코드가 통과해도 답변 의미가 틀릴 수 있습니다. "
            "참조 판정은 교육용 정답표이지 새 judge 평가가 아닙니다. 이 파일을 본평가 48응답이나 trace로 사용하지 않습니다."
            if korean else
            "A higher aggregate can hide a regression, and passing code checks does not prove semantic correctness. "
            "Reference labels are an authored answer key, not a new judge evaluation. "
            "Do not use this file as part of the 48 live responses or as trace evidence."
        ), "",
        f"Source: `{report['source']}`", f"SHA-256: `{report['fixture_sha256']}`", "",
    ])
    return "\n".join(lines)


def save_report(report: dict[str, Any], directory: Path) -> None:
    directory = directory.resolve()
    if ".foundry" in directory.parts:
        raise ValueError("Offline demonstrations must stay outside .foundry cloud evidence directories.")
    content = {
        "report.json": json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        "report.md": render_report(report),
    }
    for name, text in content.items():
        destination = directory / name
        if destination.is_symlink():
            raise ValueError(f"Refusing a symlink output: {destination}")
        if destination.exists() and destination.read_text(encoding="utf-8") != text:
            raise ValueError(f"{destination} differs. Preserve it and choose a new --output-dir.")
    directory.mkdir(parents=True, exist_ok=True)
    for name, text in content.items():
        destination = directory / name
        if not destination.exists():
            with destination.open("x", encoding="utf-8") as output:
                output.write(text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--language", choices=["en", "ko"], default="en")
    parser.add_argument("--output-dir", type=Path, help="Default: artifacts/offline/<language>; never .foundry.")
    parser.add_argument("--fail-on-regression", action="store_true", help="Exit 1 if a baseline pass becomes a failure.")
    args = parser.parse_args()
    try:
        report = evaluate_fixture(args.language)
        directory = args.output_dir or ROOT / "artifacts" / "offline" / args.language
        save_report(report, directory)
    except (OSError, ValueError) as error:
        parser.exit(2, f"Offline lesson error: {error}\n")
    for variant in VARIANTS:
        counts = report["summaries"][variant]
        print(f"{variant}: business {counts['business_passed']}/{counts['total']}")
    print(f"pass->fail: {', '.join(report['paired']['regressed_case_ids']) or 'none'}")
    print(
        "code/reference disagreement: "
        + (", ".join(report["summaries"]["candidate"]["code_reference_disagreement_case_ids"]) or "none")
    )
    print("SYNTHETIC OFFLINE ONLY: Azure/model calls=0; production_release_approved=false")
    print(f"Saved: {directory / 'report.md'}")
    print(f"Saved: {directory / 'report.json'}")
    if args.fail_on_regression and report["paired"]["pass_to_fail"]:
        print("Regression gate: FAIL (expected teaching example; do not weaken the gate).")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
