import base64
import json
import signal
import sys
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "recording"))

from action_server import Recording, redact
from provision import check_group_ownership, owned_tags, principal_from_access_token


class RecordingPrivacyTests(unittest.TestCase):
    def test_identity_and_credentials_are_redacted(self):
        text = (
            "person@example.com 12345678-1234-1234-1234-123456789abc "
            "InstrumentationKey=private; Bearer abcdefghijklmnopqrstuvwxyz012345 "
            "https://example.test/?sig=secret&token=secret"
        )
        result = redact(text)
        for secret in ("person@example.com", "12345678-", "private", "abcdefghijklmnopqrstuvwxyz", "=secret"):
            self.assertNotIn(secret, result)

    def test_lineage_and_model_versions_remain_visible(self):
        text = "trace=0123456789abcdef0123456789abcdef eval_12345 gpt-6-astra 2026-09-03"
        self.assertEqual(redact(text), text)

    def test_terminal_control_sequences_are_removed(self):
        self.assertEqual(redact("\x1b[31mfailed\x1b[0m"), "failed")


class RecordingOwnershipTests(unittest.TestCase):
    def test_principal_uses_the_explicit_subscription_token_without_logging_it(self):
        principal = "11111111-1111-4111-8111-111111111111"
        payload = base64.urlsafe_b64encode(json.dumps({
            "tid": "test-tenant", "upn": "person@example.com", "oid": principal,
        }).encode()).decode().rstrip("=")
        token = "header." + payload + ".signature"
        self.assertEqual(principal_from_access_token(token, "test-tenant", "person@example.com"), principal)
        with self.assertRaises(ValueError):
            principal_from_access_token(token, "different-tenant", "person@example.com")
        with self.assertRaises(ValueError):
            principal_from_access_token(token, "test-tenant", "different@example.com")

    def test_mutations_require_both_creation_record_and_exact_tags(self):
        config = {"run_id": "test-run", "resource_group": "rg-test"}
        group = {"id": "/subscriptions/test/resourceGroups/rg-test", "name": "rg-test",
                 "location": "swedencentral", "tags": owned_tags("test-run")}
        check_group_ownership(group, config, group["id"])
        with self.assertRaises(ValueError):
            check_group_ownership(group, config, None)
        with self.assertRaises(ValueError):
            check_group_ownership({**group, "tags": {"workshop": "other"}}, config, group["id"])
        with self.assertRaises(ValueError):
            check_group_ownership({**group, "location": "eastus"}, config, group["id"])


class RecordingProcessTests(unittest.TestCase):
    def test_stop_only_signals_the_recording_owned_process_group(self):
        recording = Recording.__new__(Recording)
        process = Mock(pid=12345)
        process.poll.return_value = None
        process.wait.return_value = 0
        recording.processes = {"local": process}
        recording.lock = threading.RLock()
        recording.emit = Mock()
        recording.state = {
            "jobs": {"stop": {}},
            "services": {"local": {"readiness": "http://127.0.0.1:8088/readiness"}},
        }
        with patch("action_server.os.killpg") as kill, patch("action_server.socket.socket") as socket:
            socket.return_value.__enter__.return_value.connect_ex.return_value = 1
            recording.stop_service({"id": "stop", "stop_service": "local"})
        kill.assert_called_once_with(12345, signal.SIGINT)
        self.assertEqual(recording.state["services"]["local"]["status"], "stopped")

    def test_unowned_process_cannot_be_stopped(self):
        recording = Recording.__new__(Recording)
        recording.processes = {}
        with patch("action_server.os.killpg") as kill:
            with self.assertRaises(ValueError):
                recording.stop_service({"id": "stop", "stop_service": "unowned"})
        kill.assert_not_called()


if __name__ == "__main__":
    unittest.main()
