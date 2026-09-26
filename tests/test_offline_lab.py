import contextlib
import copy
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from offline_lab import EVIDENCE_KIND, evaluate_fixture, main, render_report, save_report, validate_fixture


class OfflineLessonTests(unittest.TestCase):
    def test_both_editions_teach_improvement_regression_and_a_metric_blind_spot(self):
        for language in ("en", "ko"):
            with self.subTest(language=language):
                report = evaluate_fixture(language)
                self.assertEqual(report["summaries"]["baseline"]["business_passed"], 2)
                self.assertEqual(report["summaries"]["candidate"]["business_passed"], 5)
                self.assertEqual(report["summaries"]["candidate"]["human_reference_passed"], 4)
                self.assertEqual(report["summaries"]["candidate"]["total"], 8)
                self.assertEqual(report["paired"]["fail_to_pass"], 4)
                self.assertEqual(report["paired"]["pass_to_fail"], 1)
                self.assertEqual(report["paired"]["both_pass"], 1)
                self.assertEqual(report["paired"]["both_fail"], 2)
                self.assertEqual(report["paired"]["regressed_case_ids"], ["O04"])
                self.assertEqual(report["summaries"]["candidate"]["code_reference_disagreement_case_ids"], ["O05"])

    def test_examples_are_not_cloud_evidence_or_automated_judge_results(self):
        report = evaluate_fixture("en")
        self.assertEqual(report["evidence_kind"], EVIDENCE_KIND)
        self.assertEqual(report["azure_calls_made"], 0)
        self.assertEqual(report["model_calls_made"], 0)
        self.assertFalse(report["foundry_evaluation_performed"])
        self.assertFalse(report["eligible_for_cloud_verification"])
        self.assertFalse(report["production_release_approved"])
        self.assertIn("authored", report["human_reference_origin"])
        self.assertEqual(len(report["fixture_sha256"]), 64)
        self.assertNotIn("trace_id", json.dumps(report))
        self.assertNotIn("native_mean_score", json.dumps(report))

    def test_translation_preserves_the_experiment_but_not_the_text_hash(self):
        english, korean = evaluate_fixture("en"), evaluate_fixture("ko")
        self.assertEqual(english["summaries"], korean["summaries"])
        self.assertEqual(english["paired"], korean["paired"])
        self.assertNotEqual(english["fixture_sha256"], korean["fixture_sha256"])
        for en, ko in zip(english["rows"], korean["rows"], strict=True):
            for field in ("case_id", "category", "expected_decision", "required_numbers",
                          "source_ids", "allowed_citations", "citation_required"):
                self.assertEqual(en[field], ko[field])
            for variant in ("baseline", "candidate"):
                self.assertEqual(en["responses"][variant]["business_grade"], ko["responses"][variant]["business_grade"])

    def test_fixture_schema_fails_explicitly_on_missing_or_malformed_evidence(self):
        valid = json.loads((ROOT / "data" / "offline" / "en.json").read_text(encoding="utf-8"))
        invalid = []
        for field, value in (("evidence_kind", "live"), ("schema_version", True), ("cases", []), ("language", "ko")):
            invalid.append({**valid, field: value})
        duplicate = copy.deepcopy(valid)
        duplicate["cases"].append(duplicate["cases"][0])
        invalid.append(duplicate)
        for field, value in (("query", ""), ("source_ids", "DEMO-MEALS"), ("citation_required", 1),
                             ("source_ids", ["UNKNOWN"]), ("responses", {})):
            changed = copy.deepcopy(valid)
            changed["cases"][0][field] = value
            invalid.append(changed)
        changed = copy.deepcopy(valid)
        changed["cases"][0]["responses"]["candidate"]["human_reference_passed"] = "true"
        invalid.append(changed)
        for document in invalid:
            with self.subTest(document=document):
                with self.assertRaises(ValueError):
                    validate_fixture(document, "en")

    def test_reports_are_deterministic_and_existing_different_outputs_are_preserved(self):
        report = evaluate_fixture("ko")
        self.assertEqual(report, evaluate_fixture("ko"))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "reports"
            save_report(report, output)
            original = {path.name: path.read_bytes() for path in output.iterdir()}
            save_report(report, output)
            self.assertEqual(original, {path.name: path.read_bytes() for path in output.iterdir()})
            self.assertEqual(json.loads(original["report.json"]), report)
            self.assertIn(EVIDENCE_KIND, original["report.md"].decode("utf-8"))
            (output / "report.md").write_text("Keep my annotations.", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "new --output-dir"):
                save_report(report, output)
            self.assertEqual((output / "report.md").read_text(encoding="utf-8"), "Keep my annotations.")
            self.assertEqual((output / "report.json").read_bytes(), original["report.json"])

    def test_offline_reports_cannot_be_written_to_cloud_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / ".foundry" / "results"
            with self.assertRaisesRegex(ValueError, "outside .foundry"):
                save_report(evaluate_fixture("en"), output)
            self.assertFalse(output.exists())

    def test_markdown_identifies_regressions_and_reference_disagreements(self):
        for language in ("en", "ko"):
            text = render_report(evaluate_fixture(language))
            self.assertIn("| baseline | 2/8 | 2/8 |", text)
            self.assertIn("| candidate | 5/8 | 4/8 |", text)
            self.assertIn("pass->fail: 1 (O04)", text)
            self.assertIn("candidate code/reference disagreements: O05", text)
            self.assertIn("| O05 | FAIL | PASS | FAIL | none |", text)
            self.assertIn("production_release_approved: false", text)

    def test_cli_exit_codes_distinguish_completion_regression_and_input_errors(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            arguments = ["offline_lab.py", "--language", "en", "--output-dir", directory]
            with patch.object(sys, "argv", arguments):
                self.assertEqual(main(), 0)
            with patch.object(sys, "argv", [*arguments, "--fail-on-regression"]):
                self.assertEqual(main(), 1)
            with patch.object(sys, "argv", ["offline_lab.py", "--language", "invalid"]), \
                    contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                main()
            self.assertEqual(error.exception.code, 2)
            (Path(directory) / "report.json").write_text("preserve", encoding="utf-8")
            with patch.object(sys, "argv", arguments), contextlib.redirect_stderr(io.StringIO()), \
                    self.assertRaises(SystemExit) as error:
                main()
            self.assertEqual(error.exception.code, 2)

    def test_runs_without_site_packages_credentials_live_data_or_network(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "scripts").mkdir()
            (root / "data" / "offline").mkdir(parents=True)
            for name in ("offline_lab.py", "grading.py"):
                shutil.copyfile(ROOT / "scripts" / name, root / "scripts" / name)
            for language in ("en", "ko"):
                shutil.copyfile(ROOT / "data" / "offline" / f"{language}.json",
                                root / "data" / "offline" / f"{language}.json")
            environment = {key: value for key, value in os.environ.items()
                           if not key.startswith(("AZURE_", "FOUNDRY_", "LAB_", "MODEL_", "OPENAI_", "PYTHON"))}
            runner = (
                "import runpy, socket, sys; "
                "from unittest.mock import patch; "
                "sys.path.insert(0, 'scripts'); "
                "sys.argv=['scripts/offline_lab.py', '--language', sys.argv[1]]; "
                "\nwith patch('socket.socket', side_effect=AssertionError('Network is forbidden')), "
                "patch('socket.getaddrinfo', side_effect=AssertionError('DNS is forbidden')), "
                "patch('subprocess.Popen', side_effect=AssertionError('External commands are forbidden')):"
                "\n runpy.run_path('scripts/offline_lab.py', run_name='__main__')"
            )
            for language in ("en", "ko"):
                result = subprocess.run([sys.executable, "-S", "-c", runner, language], cwd=root, env=environment,
                                        capture_output=True, text=True, encoding="utf-8", timeout=15, check=False)
                self.assertEqual(result.returncode, 0, result.stderr)
                report = json.loads((root / "artifacts" / "offline" / language / "report.json").read_text(encoding="utf-8"))
                self.assertEqual(report["summaries"]["candidate"]["business_passed"], 5)
            self.assertFalse((root / ".env").exists())
            self.assertFalse((root / "src").exists())


if __name__ == "__main__":
    unittest.main()
