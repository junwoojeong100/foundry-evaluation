import base64
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import prepare_environment
import provision_environment
from provision_environment import check_group_ownership, owned_tags, principal_from_access_token


class EnvironmentOwnershipTests(unittest.TestCase):
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


class EnvironmentPreparationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.directory = self.root / ".workshop" / "test-run"
        for name in ("azure.yaml", "requirements.txt", "requirements.lock.txt", "AGENTS.md", ".gitignore"):
            (self.root / name).write_text("fixture\n")
        for name in ("data", "queries", "scripts", "tests", "src/agent"):
            (self.root / name).mkdir(parents=True, exist_ok=True)
        (self.root / "data/policies.json").write_text('[{"id":"synthetic"}]\n')
        (self.root / "src/agent/main.py").write_text("print('fixture')\n")
        (self.root / ".env").write_text(
            "AZURE_SUBSCRIPTION_ID=test-subscription\nAZURE_TENANT_ID=test-tenant\n"
            "AZURE_EXPECTED_USERNAME=person@example.com\nAZURE_RESOURCE_GROUP=\n"
            "LAB_AUX_MODEL=gpt-5.4-mini\n",
        )
        root_patch = patch.object(prepare_environment, "ROOT", self.root)
        root_patch.start()
        self.addCleanup(root_patch.stop)
        revision_patch = patch.object(prepare_environment.subprocess, "check_output", return_value="f" * 40)
        revision_patch.start()
        self.addCleanup(revision_patch.stop)
        output_patch = patch("builtins.print")
        output_patch.start()
        self.addCleanup(output_patch.stop)

    def test_initialization_is_not_a_recording_plan(self):
        prepare_environment.initialize(self.directory)
        config = json.loads((self.directory / "config.json").read_text())
        self.assertEqual(config["prefix"], "ll-test-run")
        self.assertEqual(config["region"], "swedencentral")
        self.assertFalse((self.directory / "actions.json").exists())
        self.assertEqual((self.directory / "config.json").stat().st_mode & 0o777, 0o600)

    def test_snapshot_preserves_source_hashes_without_private_caches(self):
        for name in (".azure-cli/cache", ".azure/cache", "src/agent/.foundry/result", "src/agent/.venv/cache"):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("private fixture")
        prepare_environment.initialize(self.directory)
        prepare_environment.prepare(self.directory)
        workspace = self.directory / "workshop"
        self.assertTrue((workspace / "scripts").is_dir())
        self.assertFalse((workspace / "recording").exists())
        self.assertFalse((workspace / ".azure-cli").exists())
        self.assertFalse((workspace / "src/agent/.foundry").exists())
        self.assertFalse((workspace / "src/agent/.venv").exists())
        manifest = json.loads((self.directory / "source-manifest.json").read_text())
        self.assertEqual(manifest["revision"], "f" * 40)
        self.assertNotIn(".env", manifest["files"])
        expected = hashlib.sha256((self.root / "data/policies.json").read_bytes()).hexdigest()
        self.assertEqual(manifest["files"]["data/policies.json"], expected)
        values = prepare_environment.dotenv_values(workspace / ".env")
        self.assertEqual(values["MODEL_SOL_DEPLOYMENT"], "ll-test-run-sol")
        self.assertEqual(values["AZURE_SUBSCRIPTION_ID"], "test-subscription")
        self.assertEqual((workspace / ".env").stat().st_mode & 0o777, 0o600)

    def test_existing_runs_and_redirected_workspaces_are_rejected(self):
        prepare_environment.initialize(self.directory)
        with self.assertRaises(ValueError):
            prepare_environment.initialize(self.directory)
        config_path = self.directory / "config.json"
        config = json.loads(config_path.read_text())
        config["workspace"] = str(self.root / "elsewhere")
        config_path.write_text(json.dumps(config))
        with self.assertRaises(ValueError):
            prepare_environment.prepare(self.directory)
        self.assertFalse((self.root / "elsewhere").exists())

    def test_provision_cli_rejects_paths_outside_workshop_before_cloud_calls(self):
        with patch.object(provision_environment, "ROOT", self.root):
            with patch.object(sys, "argv", ["provision", "identity", "--run-dir", str(self.root / "other")]):
                with patch.object(provision_environment, "Provisioner") as provisioner:
                    with self.assertRaises(ValueError):
                        provision_environment.main()
                    provisioner.assert_not_called()

    def test_completed_snapshot_cannot_be_overwritten(self):
        prepare_environment.initialize(self.directory)
        prepare_environment.prepare(self.directory)
        with self.assertRaises(ValueError):
            prepare_environment.prepare(self.directory)


if __name__ == "__main__":
    unittest.main()
