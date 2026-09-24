import argparse
import contextlib
import html
import importlib
import io
import json
import re
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

FENCES = re.compile(r"^```([^\n]*)\n(.*?)^```[ \t]*$", re.MULTILINE | re.DOTALL)
LINKS = re.compile(r"!?\[[^\]\n]*\]\(([^)\s]+)\)")
COMMANDS = re.compile(r"^[ \t]*(?:run: )?python scripts/(\w+)\.py(?:[ \t]+([^\n]*))?$", re.MULTILINE)


def blocks(text):
    for match in FENCES.finditer(text):
        yield match[1].strip(), text.count("\n", 0, match.start()) + 1, match[2]


def prose(text):
    return FENCES.sub(lambda match: "\n" * match[0].count("\n"), text)


def anchors(text):
    text = prose(text)
    result = set(re.findall(r'<a\s+id="([^"]+)"\s*></a>', text))
    used = set()
    for heading in re.findall(r"^#{1,6} (.+)$", text, re.MULTILINE):
        heading = re.sub(r"<[^>]*>", "", html.unescape(heading))
        slug = re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")
        candidate, suffix = slug, 0
        while candidate in used:
            suffix += 1
            candidate = f"{slug}-{suffix}"
        used.add(candidate)
        result.add(candidate)
    return result


def commands(text):
    for language, line, body in blocks(text):
        if language not in {"bash", "yaml"}:
            continue
        body = body.replace("\\\n", " ")
        for match in COMMANDS.finditer(body):
            arguments = shlex.split(match[2] or "")
            if arguments and arguments[-1] == "&&":
                arguments.pop()
            yield line, match[1], arguments


def normalized_commands(text):
    result = []
    for _, script, arguments in commands(text):
        for option in ("--query", "--language"):
            if option in arguments:
                arguments[arguments.index(option) + 1] = "<localized>"
        result.append((script, arguments))
    return result


class MarkdownParsingTests(unittest.TestCase):
    def test_anchors_include_korean_explicit_and_duplicate_headings(self):
        text = '# Same title\n## Same title\n## Same title-1\n## 같은 제목!\n<a id="stable"></a>\n'
        self.assertEqual(
            anchors(text), {"same-title", "same-title-1", "same-title-1-1", "같은-제목", "stable"},
        )

    def test_examples_are_not_links_or_headings(self):
        text = '```text\n# Not a heading\n[example](missing.md)\n```\n[real](README.md)\n'
        self.assertEqual(anchors(text), set())
        self.assertEqual(LINKS.findall(prose(text)), ["README.md"])

    def test_commands_keep_quoted_arguments_and_continuations(self):
        text = (
            '```bash\npython scripts/workshop.py feedback --label baseline \\\n'
            '  --reason "Explain the actual evidence" --row-id "$ROW_ID" &&\n'
            'python scripts/workshop.py summary --labels baseline\n```\n'
        )
        self.assertEqual(
            [args for _, _, args in commands(text)],
            [
                ["feedback", "--label", "baseline", "--reason", "Explain the actual evidence",
                 "--row-id", "$ROW_ID"],
                ["summary", "--labels", "baseline"],
            ],
        )

    def test_workflow_examples_are_checked_too(self):
        text = "```yaml\n- name: Gate\n  run: python scripts/workshop.py gate\n```\n"
        self.assertEqual(list(commands(text)), [(1, "workshop", ["gate"])])

    def test_only_a_recorded_source_snapshot_can_skip_missing_guides(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "workshop"
            root.mkdir()
            with patch.object(sys.modules[__name__], "ROOT", root):
                with self.assertRaises(FileNotFoundError):
                    DocumentationTests.setUpClass()
                (root.parent / "source-manifest.json").write_text("{}\n")
                with self.assertRaisesRegex(unittest.SkipTest, "Runtime snapshots omit guides"):
                    DocumentationTests.setUpClass()


class DocumentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT / "README.md").exists() and (ROOT.parent / "source-manifest.json").is_file():
            raise unittest.SkipTest("Runtime snapshots omit guides; check documentation in the original clone.")
        paths = [ROOT / "README.md", ROOT / "README.ko.md", *sorted((ROOT / "docs").glob("*.md"))]
        cls.documents = {path: path.read_text(encoding="utf-8") for path in paths}

    def test_local_links_images_and_fragments(self):
        for path, text in self.documents.items():
            for match in LINKS.finditer(prose(text)):
                target = urlsplit(match[1])
                if target.scheme or target.netloc:
                    continue
                with self.subTest(document=path.name, target=match[1]):
                    destination = (path.parent / unquote(target.path)).resolve() if target.path else path
                    self.assertTrue(destination.is_relative_to(ROOT), "Link escapes the repository.")
                    self.assertTrue(destination.exists(), f"Missing target: {destination}")
                    if target.fragment and destination.suffix == ".md":
                        self.assertIn(
                            unquote(target.fragment),
                            anchors(destination.read_text(encoding="utf-8")),
                            f"Missing anchor in {destination.name}",
                        )

    def test_fences_and_details_are_balanced(self):
        for path, text in self.documents.items():
            with self.subTest(document=path.name):
                self.assertEqual(
                    len(re.findall(r"^```", text, re.MULTILINE)),
                    2 * len(list(blocks(text))),
                    "Unclosed code fence.",
                )
                depth = 0
                for tag in re.findall(r"</?details>", prose(text)):
                    depth += 1 if tag == "<details>" else -1
                    self.assertGreaterEqual(depth, 0, "Closing details without an opening tag.")
                self.assertEqual(depth, 0, "Unclosed details.")

    def test_bash_examples_have_valid_syntax_without_execution(self):
        for path, text in self.documents.items():
            for language, line, body in blocks(text):
                if language != "bash":
                    continue
                with self.subTest(document=path.name, line=line):
                    result = subprocess.run(
                        ["bash", "--noprofile", "--norc", "-n"],
                        input=body, text=True, capture_output=True, check=False,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)

    def test_json_examples_are_valid(self):
        for path, text in self.documents.items():
            for language, line, body in blocks(text):
                if language == "json":
                    with self.subTest(document=path.name, line=line):
                        json.loads(body)

    def test_python_cli_examples_match_the_actual_parsers(self):
        workshop = importlib.import_module("workshop")
        parsers = {}
        for name in ("workshop", "prepare_environment", "provision_environment"):
            module = importlib.import_module(name)
            # Capture the real parser before settings, dispatch, or cloud operations.
            with patch.object(workshop, "load_settings_env"), patch.object(
                argparse.ArgumentParser, "parse_args", autospec=True, side_effect=SystemExit(0),
            ) as parse:
                with self.assertRaises(SystemExit) as stopped:
                    module.main()
                self.assertEqual(stopped.exception.code, 0)
                parse.assert_called_once()
                parsers[name] = parse.call_args.args[0]
        checked = 0
        for path, text in self.documents.items():
            for line, name, arguments in commands(text):
                with self.subTest(document=path.name, line=line, script=name, arguments=arguments):
                    self.assertIn(name, parsers, "Add this CLI's parser to the documentation check.")
                    errors = io.StringIO()
                    with contextlib.redirect_stderr(errors), contextlib.redirect_stdout(io.StringIO()):
                        try:
                            parsers[name].parse_args(arguments)
                        except SystemExit as error:
                            self.assertEqual(error.code, 0, errors.getvalue())
                    checked += 1
        self.assertGreater(checked, 0, "No CLI examples were checked.")

    def test_english_and_korean_guides_use_the_same_commands(self):
        self.assertEqual(
            {path.name.removesuffix(".en.md") for path in self.documents if path.name.endswith(".en.md")},
            {path.name.removesuffix(".ko.md") for path in self.documents
             if path.parent == ROOT / "docs" and path.name.endswith(".ko.md")},
            "Every supporting guide needs both language editions.",
        )
        pairs = [(ROOT / "README.md", ROOT / "README.ko.md")]
        pairs.extend((path, path.with_name(path.name.replace(".en.md", ".ko.md")))
                     for path in sorted((ROOT / "docs").glob("*.en.md")))
        for english, korean in pairs:
            with self.subTest(document=english.name):
                self.assertIn(korean, self.documents, "Missing Korean guide.")
                self.assertEqual(
                    normalized_commands(self.documents[english]),
                    normalized_commands(self.documents[korean]),
                )

    def test_main_workshop_keeps_the_controlled_experiment(self):
        expected = {
            "set-prompt": [["set-prompt", "v1"], ["set-prompt", "v2"]],
            "collect": [
                ["collect", "--split", "dev", "--label", "baseline"],
                ["collect", "--split", "dev", "--label", "improved"],
                ["collect", "--split", "holdout", "--label", "holdout"],
            ],
            "evaluate": [["evaluate", "--label", label] for label in ("baseline", "improved", "holdout")],
            "verify": [["verify", "--baseline", "baseline", "--candidate", "improved", "--holdout", "holdout"]],
            "cleanup": [["cleanup", "--dry-run"], ["cleanup", "--confirm"]],
        }
        for name in ("README.md", "README.ko.md"):
            documented = [args for _, script, args in commands(self.documents[ROOT / name])
                          if script == "workshop"]
            for command, arguments in expected.items():
                with self.subTest(document=name, command=command):
                    self.assertEqual([args for args in documented if args[0] == command], arguments)

    def test_start_routes_precede_the_first_command(self):
        for name, language in (("README.md", "en"), ("README.ko.md", "ko")):
            text = self.documents[ROOT / name]
            introduction = text.split("```bash", 1)[0]
            with self.subTest(document=name):
                self.assertIn('<a id="start-here"></a>', introduction)
                for guide in ("instructor", "environment", "troubleshooting", "copilot"):
                    self.assertIn(f"docs/{guide}.{language}.md", introduction)
                sequence = ("start", "lab-a", "local", "deploy", "lab-c", "lab-d",
                            "lab-e", "lab-f", "lab-g", "cleanup")
                positions = [text.index(f'<a id="{anchor}"></a>') for anchor in sequence]
                self.assertEqual(positions, sorted(positions))


if __name__ == "__main__":
    unittest.main()
