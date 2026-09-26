import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "src" / "agent")]
from grading import paired_outcomes, summarize, wilson_interval


def response(case_id, passed, *, model="sol", context="same"):
    return {
        "row_id": f"run-{model}-{case_id}", "case_id": case_id, "model_key": model, "context_hash": context,
        "trace_id": hashlib.sha256(f"test-{model}-{case_id}".encode()).hexdigest()[:32],
        "citation_required": True, "input_tokens": 100, "output_tokens": 20, "latency_seconds": 1.0,
        "business_grade": {"passed": passed, "checks": {
            "decision": passed, "required_numbers": True, "citations_retrieved": True,
            "citations_relevant": True, "citation_present": True,
        }},
    }


class StatisticalInterpretationTests(unittest.TestCase):
    def test_wilson_interval_matches_known_small_sample_values(self):
        full = wilson_interval(4, 4)
        self.assertAlmostEqual(full["lower"], 0.5101091635, places=9)
        self.assertAlmostEqual(full["upper"], 1.0)
        none = wilson_interval(0, 4)
        self.assertAlmostEqual(none["lower"], 0.0)
        self.assertAlmostEqual(none["upper"], 1 - full["lower"])
        half = wilson_interval(50, 100)
        self.assertAlmostEqual(half["lower"], 0.4038315304, places=9)
        self.assertAlmostEqual(half["upper"], 0.5961684696, places=9)

    def test_wilson_rejects_missing_impossible_and_non_integer_counts(self):
        for passed, total in ((0, 0), (-1, 4), (5, 4), (True, 4), (1, False), (1.0, 4), (1, 4.0)):
            with self.subTest(passed=passed, total=total), self.assertRaises(ValueError):
                wilson_interval(passed, total)

    def test_more_independent_trials_narrow_the_interval(self):
        small, large = wilson_interval(4, 4), wilson_interval(40, 40)
        self.assertGreater(large["lower"], small["lower"])
        for total in range(1, 21):
            for passed in range(total + 1):
                interval = wilson_interval(passed, total)
                self.assertLessEqual(0, interval["lower"])
                self.assertLessEqual(interval["lower"], passed / total + 1e-14)
                self.assertGreaterEqual(interval["upper"] + 1e-14, passed / total)
                self.assertLessEqual(interval["upper"], 1)

    def test_summary_reports_per_model_intervals_without_changing_business_gates(self):
        from contracts import MODEL_SPECS

        rows = [response(f"H{index}", index > 0, model=model) for model in MODEL_SPECS for index in range(4)]
        original = copy.deepcopy(rows)
        result = summarize(rows)
        for value in result.values():
            self.assertEqual(value["total"], 4)
            self.assertEqual(value["business_passed"], 3)
            self.assertFalse(value["business_gate"])
            self.assertEqual(value["business_pass_rate_wilson_95"], wilson_interval(3, 4))
        self.assertEqual(rows, original)


class PairedComparisonTests(unittest.TestCase):
    def test_pairs_by_model_and_case_not_order_and_keeps_regressions(self):
        baseline = [response("D01", False), response("D02", True), response("D03", True), response("D04", False)]
        candidate = [response("D04", False), response("D02", False, context="different"),
                     response("D01", True), response("D03", True)]
        before, after = copy.deepcopy(baseline), copy.deepcopy(candidate)
        result = paired_outcomes(baseline, candidate)["sol"]
        self.assertEqual(result, {
            "total": 4, "both_pass": 1, "both_fail": 1, "fail_to_pass": 1, "pass_to_fail": 1,
            "improved_case_ids": ["D01"], "regressed_case_ids": ["D02"], "context_changed_case_ids": ["D02"],
            "pass_rate_delta": 0,
        })
        self.assertEqual(baseline, before)
        self.assertEqual(candidate, after)

    def test_models_are_not_pooled(self):
        baseline = [response("D01", False, model="sol"), response("D01", True, model="luna")]
        candidate = [response("D01", True, model="sol"), response("D01", False, model="luna")]
        result = paired_outcomes(baseline, candidate)
        self.assertEqual(result["sol"]["fail_to_pass"], 1)
        self.assertEqual(result["sol"]["pass_to_fail"], 0)
        self.assertEqual(result["luna"]["pass_to_fail"], 1)
        self.assertEqual(result["luna"]["pass_rate_delta"], -1)

    def test_missing_duplicate_errored_or_ungraded_rows_cannot_disappear(self):
        valid = [response("D01", True), response("D02", False)]
        for invalid in (
            [], valid[:-1], valid + valid[:1],
            [{**valid[0], "error": "timeout"}, valid[1]],
            [{**valid[0], "context_hash": ""}, valid[1]],
            [{**valid[0], "business_grade": {"passed": None}}, valid[1]],
            [{**valid[0], "business_grade": {"passed": 1}}, valid[1]],
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                paired_outcomes(valid, invalid)

    def test_compare_detects_between_version_context_changes_and_excludes_holdout_pairs(self):
        from contracts import MODEL_SPECS
        from experiments import compare, summary_table

        rows = {
            "base-retry": [response("D01", True, model=model, context="old") for model in MODEL_SPECS],
            "candidate-retry": [response("D01", False, model=model, context="new") for model in MODEL_SPECS],
            "holdout": [response("H01", True, model=model, context="holdout") for model in MODEL_SPECS],
        }
        manifests = {
            label: {
                "split": "holdout" if label == "holdout" else "dev", "dataset_hash": "frozen",
                "corpus_hash": "frozen", "concurrency": 4, "agent": {"version": "2"}, "prompt_hash": label,
            }
            for label in rows
        }
        with tempfile.TemporaryDirectory() as directory:
            results = Path(directory)
            with patch("experiments.completed_rows", side_effect=lambda label: (manifests[label], rows[label])), \
                    patch("experiments.RESULTS_DIR", results), patch("common.RESULTS_DIR", results), \
                    patch("experiments.FOUNDRY_DIR", results / "state"), patch("builtins.print"):
                report = compare(list(rows))
                self.assertEqual(len(report["paired_comparisons"]), 1)
                pair = report["paired_comparisons"][0]
                self.assertEqual(pair["baseline"], "base-retry")
                self.assertEqual(pair["candidate"], "candidate-retry")
                for model in MODEL_SPECS:
                    self.assertEqual(pair["models"][model]["regressed_case_ids"], ["D01"])
                    self.assertEqual(pair["models"][model]["context_changed_case_ids"], ["D01"])
                self.assertTrue(any("Retrieval contexts differ" in note for note in report["comparison_notes"]))
                self.assertTrue(any("not representative" in note for note in report["comparison_notes"]))
                original = (results / "comparison.json").read_bytes()
                text = summary_table(["base-retry", "candidate-retry"])
                self.assertIn("1 pass->fail (cases: D01); changed context: D01", text)
                self.assertIn("illustrative Wilson 95%", text)
                holdout_text = summary_table(["holdout"])
                self.assertNotIn("Paired business checks", holdout_text)
                self.assertIn("[20.7%, 100.0%]", holdout_text)
                self.assertEqual(original, (results / "comparison.json").read_bytes())
                self.assertEqual(json.loads(original), report)

    def test_compare_rejects_duplicate_or_missing_labels_before_reading_results(self):
        from experiments import compare

        for labels in ([], ["baseline", "baseline"]):
            with patch("experiments.completed_rows") as read, self.assertRaises(ValueError):
                compare(labels)
            read.assert_not_called()


if __name__ == "__main__":
    unittest.main()
