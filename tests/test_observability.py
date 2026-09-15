import contextlib
import io
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src" / "agent"), str(ROOT / "scripts")]

import observability
import workshop


class MonitoringTests(unittest.TestCase):
    def setUp(self):
        self.config = SimpleNamespace(
            agent_name="test-agent", language="en", deployments={"sol": "test-sol"},
            project_endpoint="https://test.services.ai.azure.com/api/projects/test",
        )
        self.row = ["a" * 32, "sol", "True", 1, 100, 20, 5]
        self.columns = [
            "trace_id", "model_key", "success", "sample_weight", "duration_ms",
            "input_tokens", "output_tokens",
        ]

    @contextlib.contextmanager
    def recorded_query(self, rows):
        payload = {"tables": [{
            "columns": [{"name": name} for name in self.columns], "rows": rows,
        }]}
        with contextlib.ExitStack() as stack:
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            stack.enter_context(patch("observability.RuntimeConfig.from_env", return_value=self.config))
            stack.enter_context(patch("observability.completed_rows", return_value=(
                {"run_id": "baseline-test", "session_id": "test-session"},
                [{"trace_id": "a" * 32}],
            )))
            stack.enter_context(patch("observability.resources", return_value={
                "app_insights": {"id": "test-resource", "properties": {"AppId": "test-app"}},
            }))
            credential = stack.enter_context(patch("observability.credential"))
            credential.return_value.get_token.return_value.token = "test-token"
            post = stack.enter_context(patch("observability.httpx.post"))
            post.return_value.json.return_value = payload
            write = stack.enter_context(patch("observability.write_json"))
            project = stack.enter_context(patch("observability.AIProjectClient"))
            yield post, write, project

    def test_default_and_extended_windows_keep_both_filters_and_api_in_sync(self):
        for hours in (2, 24, 168):
            with self.subTest(hours=hours), self.recorded_query([self.row]) as (post, write, project):
                if hours == 2:
                    observability.monitor("baseline")
                else:
                    observability.monitor("baseline", hours)
                request = post.call_args.kwargs["json"]
                self.assertEqual(request["timespan"], f"PT{hours}H")
                self.assertEqual(request["query"].count(f"ago({hours}h)"), 2)
                self.assertNotIn("__", request["query"])
                self.assertIn('agentName == "test-agent"', request["query"])
                self.assertIn('["lab.run_id"]) == "baseline-test"', request["query"])
                self.assertIn("join kind=inner agentRequests on operation_Id", request["query"])
                report = next(call.args[1] for call in write.call_args_list if call.args[0].name == "telemetry.json")
                self.assertEqual(report["lookback_hours"], hours)
                self.assertTrue(report["complete"])
                self.assertEqual(report["observed_trace_count"], 1)
                project.return_value.__enter__.return_value.agents.stop_session.assert_called_once_with(
                    "test-agent", "test-session",
                )

    def test_invalid_windows_fail_before_environment_or_cloud_access(self):
        for hours in (0, -1, 169, True, 1.5, "24"):
            with self.subTest(hours=hours), patch("observability.RuntimeConfig.from_env") as config:
                with self.assertRaisesRegex(ValueError, "whole number from 1 to 168"):
                    observability.monitor("baseline", hours)
                config.assert_not_called()

    def test_extended_window_still_rejects_missing_duplicate_foreign_and_sampled_traces(self):
        invalid_rows = [
            [], [self.row, self.row], [["b" * 32, *self.row[1:]]],
            [[*self.row[:3], 2, *self.row[4:]]],
        ]
        for rows in invalid_rows:
            with self.subTest(rows=rows), self.recorded_query(rows) as (_, write, project):
                with self.assertRaisesRegex(ValueError, "Telemetry is incomplete"):
                    observability.monitor("baseline", 24)
                report = next(call.args[1] for call in write.call_args_list if call.args[0].name == "telemetry.json")
                self.assertFalse(report["complete"])
                project.assert_not_called()

    def test_failed_trace_is_not_converted_to_success(self):
        row = [*self.row[:2], "False", *self.row[3:]]
        with self.recorded_query([row]) as (_, write, _):
            observability.monitor("baseline", 24)
            report = next(call.args[1] for call in write.call_args_list if call.args[0].name == "telemetry.json")
            self.assertFalse(report["rows"][0]["success"])
            self.assertEqual(report["operational_summary"]["sol"]["success_rate"], 0)

    def test_cli_passes_the_default_or_requested_window_to_monitor(self):
        for options, hours in (([], 2), (["--hours", "24"], 24)):
            with self.subTest(hours=hours), patch("workshop.load_settings_env"), patch("workshop.monitor") as monitor:
                with patch.object(sys, "argv", ["workshop.py", "monitor", "--label", "baseline", *options]):
                    workshop.main()
                monitor.assert_called_once_with("baseline", hours)


if __name__ == "__main__":
    unittest.main()
