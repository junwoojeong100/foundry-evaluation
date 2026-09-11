import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src" / "agent"), str(ROOT / "scripts")]

from pydantic import ValidationError

from common import digest, label_dir, read_jsonl
from cloud_setup import agent_principal, cleanup_plan
from contracts import Invocation, MODEL_SPECS, PolicyAnswer
from experiments import normalize_eval_items, parse_invocation_output, reviewed_cases
from grading import grade, numeric_values, percentile, validate_matrix
from knowledge import canonical_context
from main import telemetry_connection
from prompting import load_prompt
from observability import telemetry_boolean
from settings import azure_url, credential, safe_name


class ContractTests(unittest.TestCase):
    def test_cleanup_plan_does_not_change_as_ownership_is_removed(self):
        state = {
            "agent_owned": "test-agent",
            "owned_models": [{"name": "test-sol", "id": "model-id"}],
            "owned_search_paths": ["indexes/test-policies"],
            "owned_roles": ["role-id"],
        }
        plan = cleanup_plan(state)
        state["owned_models"].clear()
        state["owned_roles"].clear()
        state["owned_search_paths"].clear()
        self.assertEqual(plan["models"][0]["id"], "model-id")
        self.assertEqual(plan["role_assignments"], ["role-id"])
        self.assertEqual(plan["search_objects"], ["indexes/test-policies"])

    def test_four_exact_model_ids(self):
        self.assertEqual(
            {name for name, _ in MODEL_SPECS.values()},
            {"gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna", "gpt-6-astra"},
        )

    def test_model_alias_and_extra_prompt_are_rejected(self):
        with self.assertRaises(ValidationError):
            Invocation(query="test", model_key="other", case_id="D01", run_id="test")
        with self.assertRaises(ValidationError):
            Invocation(query="test", model_key="sol", case_id="D01", run_id="test", prompt_version="v2")

    def test_schema_has_no_freeform_decision(self):
        with self.assertRaises(ValidationError):
            PolicyAnswer(answer="test", decision="approved_by_ai", citations=[])

    def test_text_json_contract_is_strict_without_model_json_schema_support(self):
        parsed = PolicyAnswer.model_validate_json('{"answer":"ok","decision":"allowed","citations":[]}')
        self.assertEqual(parsed.decision, "allowed")
        with self.assertRaises(ValidationError):
            PolicyAnswer.model_validate_json('```json\n{"answer":"ok"}\n```')
        with self.assertRaises(ValidationError):
            PolicyAnswer.model_validate_json('{"answer":"ok","decision":"allowed","citations":[],"unexpected":1}')

    def test_effective_prompt_hash_includes_common_output_contract(self):
        prompt, fingerprint = load_prompt("v1")
        self.assertIn('"citations"', prompt)
        self.assertEqual(len(fingerprint), 64)
        self.assertNotEqual(fingerprint, load_prompt("v2")[1])

    def test_agent_role_targets_instance_not_blueprint_identity(self):
        principal = "11111111-1111-4111-8111-111111111111"
        record = {
            "instance_identity": {"principal_id": principal},
            "blueprint": {"principal_id": "22222222-2222-4222-8222-222222222222"},
        }
        self.assertEqual(agent_principal(record), principal)
        with self.assertRaises(ValueError):
            agent_principal(record, record["blueprint"]["principal_id"])

    def test_cli_credential_selects_subscription_without_conflicting_tenant_flag(self):
        with patch.dict("os.environ", {"LAB_AUTH_MODE": "cli", "AZURE_SUBSCRIPTION_ID": "test-sub"}):
            with patch("settings.AzureCliCredential") as factory:
                credential()
        factory.assert_called_once_with(subscription="test-sub", process_timeout=60)

    def test_endpoint_and_name_guards(self):
        for value in ("https://evil.example", "https://user:pass@a.services.ai.azure.com", "http://a.services.ai.azure.com"):
            with self.assertRaises(ValueError):
                azure_url(value, ".services.ai.azure.com", "endpoint")
        with self.assertRaises(ValueError):
            label_dir("../escape")
        with self.assertRaises(ValueError):
            safe_name("../other", "prefix")


class DatasetTests(unittest.TestCase):
    def test_dataset_shape_split_and_citation_integrity(self):
        dev = read_jsonl(ROOT / "data" / "dev.jsonl")
        holdout = read_jsonl(ROOT / "data" / "holdout.jsonl")
        self.assertEqual((len(dev), len(holdout)), (6, 4))
        self.assertFalse({row["case_id"] for row in dev} & {row["case_id"] for row in holdout})
        policies = json.loads((ROOT / "data" / "policies.json").read_text())
        keys = {item["id"] for item in policies}
        for case in dev + holdout:
            self.assertTrue(set(case["allowed_citations"]) <= keys)
            self.assertTrue(case["ground_truth"])
        for prompt in ("v1", "v2"):
            text = (ROOT / "src" / "agent" / "prompts" / f"{prompt}.txt").read_text()
            self.assertFalse(any(row["query"] in text for row in holdout))

    def test_context_hash_is_order_independent_but_content_sensitive(self):
        a = {"id": "a", "title": "A", "content": "one"}
        b = {"id": "b", "title": "B", "content": "two"}
        self.assertEqual(canonical_context([a, b]), canonical_context([b, a]))
        self.assertNotEqual(canonical_context([a, b])[1], canonical_context([a, {**b, "content": "new"}])[1])

    def test_dataset_hash_changes_on_expected_answer_change(self):
        original = read_jsonl(ROOT / "data" / "dev.jsonl")
        modified = copy.deepcopy(original)
        modified[0]["expected_decision"] = "not_allowed"
        self.assertNotEqual(digest(original), digest(modified))

    def test_reviewed_regression_is_reused_without_changing_frozen_cases(self):
        cases = read_jsonl(ROOT / "data" / "dev.jsonl")
        record = {**cases[0], "lineage": {"source_trace_id": "a" * 32}}
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            path = directory / "regression-test.jsonl"
            path.write_text(json.dumps(record))
            reused, provenance = reviewed_cases(cases, directory)
            self.assertEqual(reused, cases)
            self.assertEqual(provenance["D01"][0]["source_trace_id"], "a" * 32)
            path.write_text(json.dumps({**record, "expected_decision": "not_allowed"}))
            with self.assertRaises(ValueError):
                reviewed_cases(cases, directory)


class HostingTests(unittest.TestCase):
    def test_telemetry_boolean_supports_typed_and_string_boolean_results(self):
        for value in (True, "True", "true"):
            self.assertTrue(telemetry_boolean(value))
        for value in (False, "False", "false"):
            self.assertFalse(telemetry_boolean(value))
        for value in (None, "", "unknown", 1):
            with self.assertRaises(ValueError):
                telemetry_boolean(value)

    def test_injected_telemetry_needs_no_connection_read_permission(self):
        with patch.dict("os.environ", {"APPLICATIONINSIGHTS_CONNECTION_STRING": "injected-test-value"}, clear=True):
            with patch("main.AIProjectClient") as project:
                self.assertEqual(telemetry_connection(None, None), "injected-test-value")
                project.assert_not_called()

    def test_platform_otlp_is_supported_without_credential_fallback(self):
        with patch.dict("os.environ", {"OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4318"}, clear=True):
            with patch("main.AIProjectClient") as project:
                self.assertIsNone(telemetry_connection(None, None))
                project.assert_not_called()

    def test_missing_hosted_exporter_fails_explicitly(self):
        with patch.dict("os.environ", {"LAB_AUTH_MODE": "managed"}, clear=True):
            with self.assertRaises(ValueError):
                telemetry_connection(None, None)


class GradingTests(unittest.TestCase):
    def setUp(self):
        self.case = read_jsonl(ROOT / "data" / "dev.jsonl")[0]
        self.row = {
            "answer": "1박 한도는 180,000원이며 허용됩니다.",
            "decision": "allowed", "citations": ["TRAVEL-2026"], "source_ids": ["TRAVEL-2026"],
        }

    def test_valid_grounded_answer_passes(self):
        self.assertTrue(grade(self.row, self.case)["passed"])

    def test_missing_fabricated_or_irrelevant_citations_fail(self):
        for citations in ([], ["MADE-UP"], ["TRAVEL-2025"]):
            with self.subTest(citations=citations):
                self.assertFalse(grade({**self.row, "citations": citations}, self.case)["passed"])

    def test_wrong_decision_and_amount_fail(self):
        self.assertFalse(grade({**self.row, "decision": "not_allowed"}, self.case)["passed"])
        self.assertFalse(grade({**self.row, "answer": "한도는 150000원입니다."}, self.case)["passed"])

    def test_korean_and_comma_amounts(self):
        self.assertIn("180000", numeric_values("18만원"))
        self.assertIn("165000", numeric_values("16.5만 원"))
        self.assertIn("180000", numeric_values("180,000원"))

    def test_nearest_rank_percentile(self):
        self.assertEqual(percentile([1, 2, 3, 4], 0.95), 4)
        with self.assertRaises(ValueError):
            percentile([], 0.5)

    def test_matrix_requires_every_model_and_no_duplicates(self):
        cases = [{"case_id": "D01"}]
        rows = [
            {"model_key": key, "case_id": "D01", "trace_id": f"{index + 1:032x}", "prompt_hash": "p", "context_hash": "c"}
            for index, key in enumerate(MODEL_SPECS)
        ]
        validate_matrix(rows, cases)
        for invalid in (rows[:-1], rows + [rows[0]], [{**rows[0], "error": "timeout"}, *rows[1:]]):
            with self.assertRaises(ValueError):
                validate_matrix(invalid, cases)
        with self.assertRaises(ValueError):
            validate_matrix([{**rows[0], "trace_id": "0" * 32}, *rows[1:]], cases)


class EvaluationTests(unittest.TestCase):
    def test_azd_raw_http_framing(self):
        self.assertEqual(
            parse_invocation_output('HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{"answer":"ok"}'),
            {"answer": "ok"},
        )
        with self.assertRaises(ValueError):
            parse_invocation_output('HTTP/1.1 502 Bad Gateway\n\n{"error":"failed"}')
        with self.assertRaises(ValueError):
            parse_invocation_output("HTTP/1.1 200 OK\nContent-Type: application/json")

    def item(self):
        return {
            "status": "pass", "datasource_item_id": "0",
            "results": [
                {"name": "groundedness", "passed": True, "score": 5},
                {"name": "relevance", "passed": False, "score": 2},
            ],
        }

    def test_native_failed_grade_is_not_an_execution_error(self):
        result = normalize_eval_items([self.item()], [{"row_id": "r1"}])
        self.assertFalse(result[0]["results"][1]["passed"])

    def test_missing_output_or_null_score_is_not_success(self):
        with self.assertRaises(ValueError):
            normalize_eval_items([], [{"row_id": "r1"}])
        for score in (None, float("nan"), float("inf"), True):
            item = self.item()
            item["results"][0]["score"] = score
            with self.assertRaises(ValueError):
                normalize_eval_items([item], [{"row_id": "r1"}])

    def test_unknown_result_mapping_fails(self):
        item = self.item()
        item["datasource_item_id"] = "100"
        with self.assertRaises(ValueError):
            normalize_eval_items([item], [{"row_id": "r1"}])


if __name__ == "__main__":
    unittest.main()
