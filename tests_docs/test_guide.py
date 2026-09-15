import argparse
import importlib
import re
import shlex
import subprocess
import sys
import unittest
from collections import Counter
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "recording")]
GUIDES = [
    ROOT / "README.md",
    *(ROOT / "docs" / name for name in (
        "instructor.ko.md", "environment.ko.md", "reference.ko.md", "troubleshooting.ko.md",
    )),
]


def bash_blocks(text):
    return re.findall(r"^```bash\n(.*?)^```$", text, re.MULTILINE | re.DOTALL)


def shell_commands(block):
    return [
        shlex.split(line.strip().removesuffix("&&").strip(), comments=True)
        for line in block.replace("\\\n", " ").splitlines() if line.strip()
    ]


class ParsedArguments(Exception):
    def __init__(self, namespace):
        super().__init__("Stopped after argument parsing, before command dispatch.")
        self.namespace = namespace


def parse_only(module, arguments):
    original = argparse.ArgumentParser.parse_args

    def stop_before_dispatch(parser, *args, **kwargs):
        raise ParsedArguments(original(parser, arguments))

    with ExitStack() as stack:
        if module.__name__ == "workshop":
            stack.enter_context(patch.object(module, "load_settings_env"))
        stack.enter_context(patch.object(argparse.ArgumentParser, "parse_args", stop_before_dispatch))
        try:
            module.main()
        except ParsedArguments as parsed:
            return parsed.namespace
    raise AssertionError("The command did not stop at its parser.")


def anchors(text):
    found = set(re.findall(r'<[^>]+\b(?:id|name)=["\']([^"\']+)["\']', text))
    counts = Counter()
    for title in re.findall(r"^#{1,6} +(.+)$", text, re.MULTILINE):
        title = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", title)
        title = re.sub(r"<[^>]+>", "", title)
        slug = re.sub(r"[^\w -]", "", title.lower()).replace(" ", "-")
        found.add(f"{slug}-{counts[slug]}" if counts[slug] else slug)
        counts[slug] += 1
    return found


class GuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readme = (ROOT / "README.md").read_text()
        cls.blocks = bash_blocks(cls.readme)
        cls.commands = [command for block in cls.blocks for command in shell_commands(block)]
        workshop = importlib.import_module("workshop")
        cls.workshop_args = [
            parse_only(workshop, command[2:])
            for command in cls.commands if command[:2] == ["python", "scripts/workshop.py"]
        ]

    def test_participant_path_starts_early_and_has_ten_clear_steps(self):
        lines = self.readme.splitlines()
        self.assertLessEqual(lines.index("```bash") + 1, 40)
        self.assertLessEqual(len(lines), 400)
        steps = re.findall(
            r"^## (\d+)\. [^\n]+\n(.*?)(?=^## |\Z)", self.readme, re.MULTILINE | re.DOTALL,
        )
        self.assertEqual([int(number) for number, _ in steps], list(range(1, 11)))
        for number, body in steps:
            with self.subTest(step=number):
                self.assertIn("**할 일:**", body)
                self.assertIn("**완료 확인:**", body)
                self.assertTrue(bash_blocks(body))
                self.assertLessEqual(body.count("!["), 1)

    def test_required_commands_are_visible_and_images_are_optional(self):
        details = re.findall(r"<details>.*?</details>", self.readme, re.DOTALL)
        self.assertTrue(details)
        for detail in details:
            self.assertFalse(bash_blocks(detail))
        visible = re.sub(r"<details>.*?</details>", "", self.readme, flags=re.DOTALL)
        self.assertNotIn("![", visible)
        self.assertLessEqual(self.readme.count("!["), 10)

    def test_bash_examples_have_valid_syntax_without_execution(self):
        for path in GUIDES:
            for index, block in enumerate(bash_blocks(path.read_text())):
                with self.subTest(file=path.name, block=index):
                    result = subprocess.run(
                        ["bash", "-n"], input=block, text=True, capture_output=True, check=False,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)

    def test_copied_participant_blocks_stop_on_command_failure(self):
        for index, block in enumerate(self.blocks):
            lines = [line.strip() for line in block.replace("\\\n", " ").splitlines() if line.strip()]
            with self.subTest(block=index):
                self.assertTrue(all(line.endswith("&&") for line in lines[:-1]))
        test_block = next(i for i, block in enumerate(self.blocks) if "unittest discover -s tests -v" in block)
        cloud_block = next(i for i, block in enumerate(self.blocks) if "workshop.py preflight" in block)
        self.assertLess(test_block, cloud_block)
        dry_run = next(i for i, block in enumerate(self.blocks) if "cleanup --dry-run" in block)
        confirm = next(i for i, block in enumerate(self.blocks) if "cleanup --confirm" in block)
        self.assertLess(dry_run, confirm)

    def test_python_examples_match_real_parsers_before_any_dispatch(self):
        modules = {
            "scripts/workshop.py": importlib.import_module("workshop"),
            "recording/action_setup.py": importlib.import_module("action_setup"),
            "recording/provision.py": importlib.import_module("provision"),
        }
        for path in GUIDES:
            for block in bash_blocks(path.read_text()):
                for command in shell_commands(block):
                    if not command or command[0] != "python" or command[1] == "-m":
                        continue
                    with self.subTest(file=path.name, command=command):
                        self.assertIn(command[1], modules)
                        parse_only(modules[command[1]], command[2:])

    def test_participant_command_order_preserves_the_learning_loop(self):
        self.assertEqual([args.command for args in self.workshop_args], [
            "preflight", "bind", "prepare-iq", "retrieve", "set-prompt", "smoke",
            "grant-agent-access", "smoke", "collect", "evaluate", "compare", "monitor",
            "feedback", "set-prompt", "smoke", "collect", "evaluate", "compare",
            "collect", "evaluate", "compare", "monitor", "monitor", "verify",
            "cleanup", "cleanup", "check-cleanup",
        ])
        self.assertEqual([command for command in self.commands if command[0] == "azd"], [
            ["azd", "ai", "agent", "run", "--no-client"],
            ["azd", "deploy", "--no-prompt"],
            ["azd", "deploy", "--no-prompt"],
        ])
        prompts = [args.version for args in self.workshop_args if args.command == "set-prompt"]
        self.assertEqual(prompts, ["v1", "v2"])
        self.assertEqual([args.local for args in self.workshop_args if args.command == "smoke"], [True, False, False])
        for version, next_command in (
            ("v1", ["azd", "ai", "agent", "run", "--no-client"]),
            ("v2", ["azd", "deploy", "--no-prompt"]),
        ):
            index = self.commands.index(["python", "scripts/workshop.py", "set-prompt", version])
            self.assertEqual(self.commands[index + 1], next_command)
        local_smoke = self.commands.index(["python", "scripts/workshop.py", "smoke", "--local"])
        deployment = self.commands.index(["azd", "deploy", "--no-prompt"])
        grant = self.commands.index(["python", "scripts/workshop.py", "grant-agent-access"])
        self.assertLess(local_smoke, deployment)
        self.assertEqual(deployment + 1, grant)
        collect = [args for args in self.workshop_args if args.command == "collect"]
        self.assertEqual([(args.split, args.label, args.concurrency) for args in collect], [
            ("dev", "baseline", 4), ("dev", "improved", 4), ("holdout", "holdout", 4),
        ])
        for operation in ("evaluate", "monitor"):
            self.assertEqual(
                [args.label for args in self.workshop_args if args.command == operation],
                ["baseline", "improved", "holdout"],
            )
        feedback = next(args for args in self.workshop_args if args.command == "feedback")
        self.assertEqual(
            (feedback.label, feedback.row_id, feedback.reason, feedback.reviewer),
            ("baseline", "$ROW_ID", "$REVIEW_REASON", "human"),
        )
        verify = next(args for args in self.workshop_args if args.command == "verify")
        self.assertEqual((verify.baseline, verify.candidate, verify.holdout), ("baseline", "improved", "holdout"))
        self.assertNotIn("data/holdout.jsonl", "\n".join(self.blocks))

    def test_model_contract_and_verification_fields_are_preserved(self):
        from contracts import MODEL_SPECS

        reference = (ROOT / "docs/reference.ko.md").read_text()
        for key, (model, version) in MODEL_SPECS.items():
            self.assertIn(f"| `{key}` | `{model}` | `{version}` |", reference)
        for field in (
            "labels → baseline → business_failures", "component_execution_verified: true",
            "primary_model_outputs: 64", "distinct_verified_traces: 64",
            "candidate_quality_gates", "production_release_approved: false",
        ):
            self.assertIn(field, self.readme)

    def test_environment_examples_use_one_run_directory_not_recorded_names(self):
        blocks = bash_blocks((ROOT / "docs/environment.ko.md").read_text())
        commands = [command for block in blocks for command in shell_commands(block)]
        run_commands = [command for command in commands if "--run-dir" in command]
        self.assertTrue(run_commands)
        for command in run_commands:
            self.assertEqual(command[command.index("--run-dir") + 1], "$RUN_DIR")
        self.assertNotIn("20260914-2034", "\n".join(blocks))
        self.assertNotIn("cd ../../..", "\n".join(blocks))
        local_check = next(i for i, block in enumerate(blocks) if "unittest discover -s tests -v" in block)
        first_cloud = next(i for i, block in enumerate(blocks) if "provision.py identity" in block)
        self.assertLess(local_check, first_cloud)

    def test_all_public_local_links_and_anchors_resolve(self):
        documents = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]
        for path in documents:
            for target in re.findall(r"\]\(([^)\s]+)\)", path.read_text()):
                url = urlsplit(target)
                if url.scheme or url.netloc:
                    continue
                destination = (path.parent / unquote(url.path)).resolve() if url.path else path
                with self.subTest(file=path.name, link=target):
                    self.assertTrue(destination.is_relative_to(ROOT), f"Link leaves the repository: {target}")
                    self.assertTrue(destination.exists(), f"Missing target: {destination}")
                    if url.fragment:
                        self.assertTrue(destination.is_file())
                        self.assertIn(unquote(url.fragment), anchors(destination.read_text()))


if __name__ == "__main__":
    unittest.main()
