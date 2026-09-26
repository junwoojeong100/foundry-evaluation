import argparse
import contextlib
import html
import importlib
import inspect
import io
import json
import os
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
sys.path[:0] = [str(ROOT / "src" / "agent"), str(ROOT / "scripts")]

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

    def test_ci_files_are_inactive_valid_and_use_real_commands(self):
        import yaml
        workshop = importlib.import_module("workshop")
        with patch.object(workshop, "load_settings_env"), patch.object(
            argparse.ArgumentParser, "parse_args", autospec=True, side_effect=SystemExit(0),
        ) as parse:
            with self.assertRaises(SystemExit):
                workshop.main()
        parser = parse.call_args.args[0]
        templates = sorted((ROOT / "ci").glob("*.yml"))
        scripts = sorted((ROOT / "ci").glob("*.sh"))
        self.assertTrue(templates and scripts, "The Level 3 guide links to the CI template and its stage script.")
        found = []
        for path in [*templates, *scripts]:
            text = path.read_text(encoding="utf-8")
            with self.subTest(file=path.name):
                if path.suffix == ".yml":
                    workflow = yaml.safe_load(text)
                    # PyYAML reads the bare key `on` as True.
                    self.assertIn("workflow_dispatch", workflow.get("on", workflow.get(True)))
                    self.assertTrue(workflow["jobs"])
                    for stage in re.findall(r"bash (ci/[\w-]+\.sh) ([\w-]+)", text):
                        self.assertTrue((ROOT / stage[0]).is_file(), stage)
                        self.assertIn(f"  {stage[1]})", (ROOT / stage[0]).read_text(encoding="utf-8"))
                else:
                    result = subprocess.run(["bash", "-n", str(path)], text=True, capture_output=True, check=False)
                    self.assertEqual(result.returncode, 0, result.stderr)
                for match in COMMANDS.finditer(text):
                    script, arguments = match[1], shlex.split(match[2] or "")
                    found.append(arguments)
                    self.assertEqual(script, "workshop")
                    with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                        try:
                            parser.parse_args(arguments)
                        except SystemExit as error:
                            self.assertEqual(error.code, 0, arguments)
        self.assertTrue(any(arguments[:2] == ["gate", "--composite"] for arguments in found))
        self.assertIn(["verify", "--baseline", "baseline", "--candidate", "improved", "--holdout", "holdout"], found)

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

    def test_experiment_map_matches_the_question_sets_and_model_count(self):
        from contracts import MODEL_SPECS

        expected = [("baseline", "V1", "dev"), ("improved", "V2", "dev"), ("holdout", "V2", "holdout")]
        for name, directory in (("README.md", ROOT / "data" / "en"), ("README.ko.md", ROOT / "data")):
            text = self.documents[ROOT / name]
            plan = text.split('<a id="evaluation-runs"></a>', 1)[1].split("```bash", 1)[0]
            rows = re.findall(
                r"^\| `(baseline|improved|holdout)` \| ([^|\n]+) \| ([^|\n]+) \| (\d+) \|",
                plan, re.MULTILINE,
            )
            with self.subTest(document=name):
                evaluation = text.split('<a id="lab-c"></a>', 1)[1].split('<a id="lab-d"></a>', 1)[0]
                self.assertIn(
                    '<a id="evaluation-runs"></a>', evaluation.split("```bash", 1)[0],
                    "Explain the experiment at the first evaluation step, before its commands.",
                )
                self.assertNotIn(
                    '<a id="evaluation-runs"></a>', text.split('<a id="start"></a>', 1)[0],
                    "Keep the detailed experiment map out of the getting-started path.",
                )
                self.assertEqual([row[0] for row in rows], [label for label, _, _ in expected])
                for (_, instructions, questions, responses), (_, version, split) in zip(rows, expected):
                    question_count = sum(
                        bool(line.strip())
                        for line in (directory / f"{split}.jsonl").read_text(encoding="utf-8").splitlines()
                    )
                    self.assertEqual(re.findall(r"\bV\d+\b", instructions), [version])
                    self.assertIn(f"`{split}`", questions)
                    self.assertEqual(re.findall(r"\d+", questions), [str(question_count)])
                    self.assertEqual(int(responses), question_count * len(MODEL_SPECS))
                self.assertEqual(sum(int(row[3]) for row in rows), 48)

    def test_required_result_reading_is_not_hidden_in_optional_details(self):
        sections = (
            ("lab-c", "lab-d", ("collect", "evaluate", "groundedness", "relevance")),
            ("review-case", "save-review", (
                "query", "saved_response", "fixed_reference", "business_checks", "row_id", "trace_id",
            )),
            ("metric-fields", "portal-comparison", (
                "business", "required citations", "groundedness", "relevance", "tokens in/out", "p50/p95 s",
            )),
        )
        for name in ("README.md", "README.ko.md"):
            visible = re.sub(r"<details>.*?</details>", "", self.documents[ROOT / name], flags=re.DOTALL)
            for start, end, terms in sections:
                with self.subTest(document=name, section=start):
                    section = visible.split(f'<a id="{start}"></a>', 1)[1]
                    section = section.split(f'<a id="{end}"></a>', 1)[0]
                    for term in terms:
                        self.assertIn(f"`{term}`", section)

    def test_case_review_explains_all_checks_including_empty_citations(self):
        from grading import grade

        row = {"answer": "", "decision": "allowed", "citations": [], "source_ids": []}
        case = {"expected_decision": "allowed", "required_numbers": [],
                "allowed_citations": [], "citation_required": True}
        checks = grade(row, case)["checks"]
        self.assertTrue(checks["citations_retrieved"] and checks["citations_relevant"])
        self.assertFalse(checks["citation_present"])
        self.assertTrue(grade(row, {**case, "citation_required": False})["passed"])
        for name in ("README.md", "README.ko.md"):
            text = re.sub(r"<details>.*?</details>", "", self.documents[ROOT / name], flags=re.DOTALL)
            review = text.split('<a id="review-case"></a>', 1)[1].split('<a id="save-review"></a>', 1)[0]
            with self.subTest(document=name):
                self.assertEqual(re.findall(r"^\| `(\w+)` \|", review, re.MULTILINE), list(checks))
                for field in ("citation_required", "source_ids", "allowed_citations", "ground_truth"):
                    self.assertIn(f"`{field}`", review)
                self.assertIn("`[]`", review)

    def test_comparison_reads_the_reviewed_saved_v2_answer_before_holdout(self):
        from contracts import MODEL_SPECS

        for name in ("README.md", "README.ko.md"):
            text = self.documents[ROOT / name]
            visible = re.sub(r"<details>.*?</details>", "", text, flags=re.DOTALL)
            evaluation = visible.split('<a id="evaluation-runs"></a>', 1)[1].split("```bash", 1)[0]
            comparison = visible.split('<a id="compare-results"></a>', 1)[1].split('<a id="lab-f"></a>', 1)[0]
            report = text.split('<a id="finish"></a>', 1)[1].split('<a id="levels"></a>', 1)[0]
            with self.subTest(document=name):
                for key, (model, _) in MODEL_SPECS.items():
                    self.assertIn(f"`{key}`", evaluation)
                    self.assertIn(f"`{model}`", evaluation)
                self.assertIn("`LAB_AGENT_NAME`", evaluation)
                self.assertEqual(
                    [(script, args) for _, script, args in commands(comparison)],
                    [
                        ("workshop", ["summary", "--labels", "baseline", "improved"]),
                        ("workshop", ["show", "--label", "improved", "--row-id", "$V2_ROW_ID"]),
                    ],
                    "Inspect the linked saved row, not a new smoke/Playground answer.",
                )
                self.assertIn('read -r -p ', comparison)
                for field in ("case_id", "model_key", "trace_id", "saved_response", "fixed_reference"):
                    self.assertIn(f"`{field}`", comparison)
                template = next(body for kind, _, body in blocks(report) if kind == "text")
                self.assertIn("V2 row", template)

    def test_main_workshop_reads_holdout_scores_before_reporting(self):
        for name, language in (("README.md", "en"), ("README.ko.md", "ko")):
            text = self.documents[ROOT / name]
            holdout = text.split('<a id="lab-f"></a>', 1)[1].split('<a id="lab-g"></a>', 1)[0]
            report = text.split('<a id="finish"></a>', 1)[1].split('<a id="cleanup"></a>', 1)[0]
            with self.subTest(document=name):
                self.assertEqual(
                    [(script, args) for _, script, args in commands(holdout)],
                    [
                        ("workshop", ["collect", "--split", "holdout", "--label", "holdout"]),
                        ("workshop", ["evaluate", "--label", "holdout"]),
                        ("workshop", ["compare", "--labels", "baseline", "improved", "holdout"]),
                        ("workshop", ["summary", "--labels", "holdout"]),
                    ],
                    "Read holdout separately, not as a before/after comparison with different dev questions.",
                )
                self.assertIn('<a id="holdout-results"></a>', holdout)
                for field in ("groundedness", "relevance", "holdout business-check failures:",
                              "holdout Foundry-score failures:"):
                    self.assertIn(field, holdout)
                self.assertIn("](#holdout-results)", report)
                recovery = self.documents[ROOT / "docs" / f"troubleshooting.{language}.md"]
                self.assertIn(f"../{name}#holdout-results", recovery)

    def test_start_routes_precede_the_first_command(self):
        for name, language in (("README.md", "en"), ("README.ko.md", "ko")):
            text = self.documents[ROOT / name]
            introduction = text.split("```bash", 1)[0]
            with self.subTest(document=name):
                self.assertIn('<a id="start-here"></a>', introduction)
                for guide in ("instructor", "environment", "troubleshooting", "copilot"):
                    self.assertIn(f"docs/{guide}.{language}.md", introduction)
                primary_start = introduction.split("<details>", 1)[0]
                self.assertIn("](#start)", primary_start)
                self.assertIn(f"docs/troubleshooting.{language}.md#resume", primary_start)
                self.assertIn(f"docs/environment.{language}.md", primary_start)
                self.assertIn("](#bind-project)", primary_start)
                self.assertNotIn(f"docs/copilot.{language}.md", primary_start)
                self.assertNotIn("#existing-foundation", primary_start)
                sequence = ("start", "lab-a", "local", "deploy", "lab-c", "lab-d",
                            "lab-e", "lab-f", "lab-g", "cleanup")
                positions = [text.index(f'<a id="{anchor}"></a>') for anchor in sequence]
                self.assertEqual(positions, sorted(positions))

    def test_class_handoff_identifies_the_runner_before_commands(self):
        for name, language, marker, runner in (
            ("README.md", "en", "**Class runner:**", "one person"),
            ("README.ko.md", "ko", "**수업 실행자:**", "한 명"),
        ):
            text = self.documents[ROOT / name]
            introduction = re.sub(r"<details>.*?</details>", "", text, flags=re.DOTALL)
            introduction = introduction.split("```bash", 1)[0]
            settings = text.split('<a id="workspace-settings"></a>', 1)[1].split("```bash", 1)[0]
            handoff = self.documents[ROOT / "docs" / f"instructor.{language}.md"]
            handoff = handoff.split('<a id="handoff"></a>', 1)[1].split("\n## ", 2)[1]
            with self.subTest(document=name):
                self.assertIn(marker, introduction)
                runner_instruction = introduction.split(marker, 1)[1].split("\n", 1)[0]
                self.assertIn(runner, runner_instruction)
                for field in ("LAB_PREFIX", "LAB_AGENT_NAME"):
                    self.assertIn(field, runner_instruction)
                    self.assertIn(field, handoff)
                for field in ("AZURE_EXPECTED_USERNAME", "MFA"):
                    self.assertIn(field, settings)
                    self.assertIn(field, handoff)

    def test_existing_environment_starts_bash_before_prompting_for_input(self):
        for language in ("en", "ko"):
            text = self.documents[ROOT / "docs" / f"instructor.{language}.md"]
            setup = text.split('<a id="existing-foundation"></a>', 1)[1]
            setup = setup.split('<a id="rehearsal-workspace"></a>', 1)[0]
            shell_blocks = [body for kind, _, body in blocks(setup) if kind == "bash"]
            with self.subTest(language=language):
                self.assertEqual(shell_blocks[0].strip(), "bash")
                self.assertTrue(any("read -r -p" in body for body in shell_blocks[1:]))
                for link in ("#tools", "#access"):
                    self.assertIn(f"]({link})", setup.split("```bash", 1)[0])
                tools = text.split('<a id="tools"></a>', 1)[1].split('<a id="access"></a>', 1)[0]
                self.assertIn("](#existing-foundation)", tools,
                              "Tool checks must not send existing-environment learners to new provisioning.")

    def test_existing_environment_explicitly_sets_the_edition_language(self):
        template = (ROOT / ".env.example").read_text(encoding="utf-8")
        default_language = re.search(r"^LAB_LANGUAGE=(ko|en)$", template, re.MULTILINE).group(1)
        for language in ("en", "ko"):
            text = self.documents[ROOT / "docs" / f"instructor.{language}.md"]
            settings = text.split('<a id="existing-settings"></a>', 1)[1].split("```bash", 1)[0]
            examples = [
                dict(re.findall(r"^(LAB_\w+)=(\w+)$", body, re.MULTILINE))
                for kind, _, body in blocks(settings) if kind == "text" and "LAB_LANGUAGE=" in body
            ]
            with self.subTest(language=language):
                self.assertEqual(examples, [{
                    "LAB_LANGUAGE": language, "LAB_PROMPT_VERSION": "v1", "LAB_AUTH_MODE": "cli",
                }], "A fresh template needs an explicit edition setting before sign-in and preflight.")
                explanation = settings.split("```text", 1)[0]
                self.assertIn(".env.example", explanation)
                self.assertIn(f"`{default_language}`", explanation)

    def test_login_recovery_returns_to_each_original_preparation_path(self):
        for name, language in (("README.md", "en"), ("README.ko.md", "ko")):
            recovery = self.documents[ROOT / "docs" / f"troubleshooting.{language}.md"]
            recovery = recovery.split('<a id="login"></a>', 1)[1].split('<a id="retrieval"></a>', 1)[0]
            returns = recovery.split('<a id="login-return"></a>', 1)[1]
            destinations = {
                f"../{name}#login-check": ROOT / name,
                f"environment.{language}.md#login-check": ROOT / "docs" / f"environment.{language}.md",
                f"instructor.{language}.md#login-check": ROOT / "docs" / f"instructor.{language}.md",
            }
            with self.subTest(language=language):
                self.assertEqual(
                    {link for link in LINKS.findall(prose(returns)) if link.endswith("#login-check")},
                    set(destinations),
                )
            for link, path in destinations.items():
                with self.subTest(language=language, destination=link):
                    check = self.documents[path].split('<a id="login-check"></a>', 1)[1]
                    body = next(body for kind, _, body in blocks(check) if kind == "bash")
                    self.assertIn('az account show --subscription "$LOGIN_SUBSCRIPTION_ID"', body)
                    self.assertIn("azd auth status --output json", body)
                    self.assertNotIn("auth login", body)
            environment = self.documents[destinations[f"environment.{language}.md#login-check"]]
            after_login = environment.split('<a id="login-check"></a>', 1)[1]
            _, script, arguments = next(commands(after_login))
            self.assertEqual((script, arguments), (
                "provision_environment", ["identity", "--run-dir", "$RUN_DIR"],
            ), "New-environment recovery must return before provisioning, not to README preflight.")

    def test_calibration_recovery_returns_to_the_next_unexecuted_stage(self):
        for name, language in (("README.md", "en"), ("README.ko.md", "ko")):
            recovery = self.documents[ROOT / "docs" / f"troubleshooting.{language}.md"]
            recovery = recovery.split('<a id="calibration-return"></a>', 1)[1]
            recovery = recovery.split('<a id="telemetry"></a>', 1)[0]
            with self.subTest(language=language):
                self.assertEqual(set(LINKS.findall(prose(recovery))), {
                    f"../{name}#baseline-collection",
                    f"environment.{language}.md#handoff",
                    f"instructor.{language}.md#after-calibration",
                })
                destination = self.documents[ROOT / name].split('<a id="baseline-collection"></a>', 1)[1]
                _, script, arguments = next(commands(destination))
                self.assertEqual((script, arguments), (
                    "workshop", ["collect", "--split", "dev", "--label", "baseline"],
                ))

    def test_offline_test_recovery_keeps_the_original_preparation_path(self):
        for name, language in (("README.md", "en"), ("README.ko.md", "ko")):
            recovery = self.documents[ROOT / "docs" / f"troubleshooting.{language}.md"]
            recovery = recovery.split('<a id="offline-tests"></a>', 1)[1]
            recovery = recovery.split('<a id="login"></a>', 1)[0]
            with self.subTest(language=language):
                shell_blocks = [body for kind, _, body in blocks(recovery) if kind == "bash"]
                self.assertEqual(len(shell_blocks), 3)
                self.assertIn("source src/agent/.venv/bin/activate", shell_blocks[0])
                self.assertIn("python --version", shell_blocks[0])
                self.assertIn("sys.executable", shell_blocks[0])
                self.assertIn("sys.prefix", shell_blocks[0])
                self.assertIn("python -m pip check", shell_blocks[0])
                self.assertEqual(shell_blocks[1].strip(), (
                    "python -m pip install -r requirements.lock.txt &&\npython -m pip check"
                ))
                self.assertEqual(shell_blocks[2].strip(), "python -m unittest discover -s tests -v")
                for target in (f"../{name}#login", f"environment.{language}.md#setup-identity",
                               f"instructor.{language}.md#existing-settings"):
                    self.assertIn(target, LINKS.findall(prose(recovery)))
                self.assertIn("ModuleNotFoundError", recovery)
                self.assertIn("assertion", recovery)
                for path in (ROOT / name, ROOT / "docs" / f"environment.{language}.md",
                             ROOT / "docs" / f"instructor.{language}.md"):
                    self.assertIn(f"troubleshooting.{language}.md#offline-tests", self.documents[path])

    def test_login_recovery_links_unattempted_azd_before_verification(self):
        for name, language in (("README.md", "en"), ("README.ko.md", "ko")):
            recovery = self.documents[ROOT / "docs" / f"troubleshooting.{language}.md"]
            returns = recovery.split('<a id="login-return"></a>', 1)[1].split("<details>", 1)[0]
            for link, path in (
                (f"../{name}", ROOT / name),
                (f"environment.{language}.md", ROOT / "docs" / f"environment.{language}.md"),
                (f"instructor.{language}.md", ROOT / "docs" / f"instructor.{language}.md"),
            ):
                with self.subTest(language=language, path=path.name):
                    self.assertLess(returns.index(f"{link}#azd-login"), returns.index(f"{link}#login-check"))
                    text = self.documents[path]
                    login = text.split('<a id="azd-login"></a>', 1)[1]
                    login = login.split('<a id="login-check"></a>', 1)[0]
                    shell_blocks = [body for kind, _, body in blocks(login) if kind == "bash"]
                    self.assertEqual(
                        [body.strip() for body in shell_blocks],
                        ['azd auth login --tenant-id "$LOGIN_TENANT_ID"'],
                    )

    def test_low_score_return_preserves_report_comparison_and_freeze_checks(self):
        for name, language in (("README.md", "en"), ("README.ko.md", "ko")):
            text = self.documents[ROOT / name]
            recovery = self.documents[ROOT / "docs" / f"troubleshooting.{language}.md"]
            decision = recovery.split('<a id="resume"></a>', 1)[0]
            with self.subTest(language=language):
                for anchor in ("baseline-report", "candidate-comparison", "holdout-comparison"):
                    self.assertIn(f"../{name}#{anchor}", LINKS.findall(prose(decision)))
                report = text.split('<a id="baseline-report"></a>', 1)[1]
                report = report.split('<a id="lab-d"></a>', 1)[0]
                self.assertIn("Completed", report)
                self.assertEqual(list(commands(report)), [])
                for anchor, labels in (
                    ("candidate-comparison", ["baseline", "improved"]),
                    ("holdout-comparison", ["baseline", "improved", "holdout"]),
                ):
                    destination = text.split(f'<a id="{anchor}"></a>', 1)[1]
                    _, script, args = next(commands(destination))
                    self.assertEqual((script, args), ("workshop", ["compare", "--labels", *labels]))
                holdout = text.split('<a id="holdout-comparison"></a>', 1)[1]
                holdout = holdout.split('<a id="holdout-results"></a>', 1)[0]
                self.assertIn("agent_version", holdout)
                self.assertIn("prompt_hash", holdout)

    def test_report_review_recovery_starts_with_a_read_not_feedback(self):
        for name in ("README.md", "README.ko.md"):
            text = self.documents[ROOT / name]
            report = text.split('<a id="finish"></a>', 1)[1].split('<a id="levels"></a>', 1)[0]
            with self.subTest(document=name):
                self.assertIn("#read-review", LINKS.findall(prose(report)))
                self.assertNotIn("#save-review", LINKS.findall(prose(report)))
                read = text.split('<a id="read-review"></a>', 1)[1].split('<a id="lab-e"></a>', 1)[0]
                shell_blocks = [body.strip() for kind, _, body in blocks(read) if kind == "bash"]
                self.assertEqual(shell_blocks, [
                    'python -m json.tool --no-ensure-ascii "src/agent/.foundry/datasets/regression-$ROW_ID.jsonl"',
                ])
                self.assertEqual(list(commands(read)), [])

    def test_v2_recovery_returns_to_collection_without_reentering_the_warning(self):
        for name, language in (("README.md", "en"), ("README.ko.md", "ko")):
            text = self.documents[ROOT / name]
            recovery = self.documents[ROOT / "docs" / f"troubleshooting.{language}.md"]
            recovery = recovery.split('<a id="v2-changed"></a>', 1)[1]
            recovery = recovery.split('<a id="portal-differs"></a>', 1)[0]
            with self.subTest(language=language):
                self.assertIn(f"../{name}#holdout-collection", LINKS.findall(prose(recovery)))
                self.assertIn(f"../{name}#holdout-comparison", LINKS.findall(prose(recovery)))
                self.assertNotIn(f"../{name}#lab-f", LINKS.findall(prose(recovery)))
                self.assertIn("improved-retry", recovery)
                self.assertIn("holdout-retry", recovery)
                self.assertIn("prompt_hash", recovery)
                destination = text.split('<a id="holdout-collection"></a>', 1)[1]
                _, script, args = next(commands(destination))
                self.assertEqual((script, args), (
                    "workshop", ["collect", "--split", "holdout", "--label", "holdout"],
                ))
                self.assertLess(text.index('<a id="lab-f"></a>'), text.index('<a id="holdout-collection"></a>'))

    def test_init_recovery_reuses_the_missing_run_and_rejects_existing_paths(self):
        setup = importlib.import_module("prepare_environment")
        for language in ("en", "ko"):
            recovery = self.documents[ROOT / "docs" / f"troubleshooting.{language}.md"]
            resume = recovery.split('<a id="setup-resume"></a>', 1)[1]
            resume = resume.split('<a id="setup-init-retry"></a>', 1)[0]
            retry = recovery.split('<a id="setup-init-retry"></a>', 1)[1]
            shell_blocks = [body for kind, _, body in blocks(retry) if kind == "bash"]
            with self.subTest(language=language):
                self.assertIn("#setup-init-retry", LINKS.findall(prose(resume)))
                self.assertIn(f"environment.{language}.md#setup-snapshot", LINKS.findall(prose(retry)))
                self.assertEqual(len(shell_blocks), 1)
                self.assertEqual(
                    [(script, args) for _, script, args in commands(retry)],
                    [("prepare_environment", ["init", "--run-dir", "$RUN_DIR", "--language", language])],
                )
                self.assertNotIn("date ", shell_blocks[0])
                self.assertNotIn('ls "$RUN_DIR/config.json"', next(
                    body for kind, _, body in blocks(resume) if kind == "bash"
                ))
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory).resolve()
                run = root / ".workshop" / f"{language}-fixture"
                values = {
                    "AZURE_SUBSCRIPTION_ID": "fixture-subscription",
                    "AZURE_TENANT_ID": "fixture-tenant",
                    "AZURE_EXPECTED_USERNAME": "runner@example.invalid",
                    "AZURE_RESOURCE_GROUP": "",
                }
                with patch.object(setup, "ROOT", root), \
                        patch.object(setup, "dotenv_values", return_value={}) as settings, \
                        patch.object(setup.subprocess, "check_output", return_value="fixture-revision\n"):
                    with self.assertRaisesRegex(ValueError, "authorized account"):
                        setup.initialize(run, language)
                    self.assertFalse(run.exists(), "Input validation must fail before creating the run.")
                    settings.return_value = values
                    with contextlib.redirect_stdout(io.StringIO()):
                        setup.initialize(run, language)
                    config = json.loads((run / "config.json").read_text())
                    self.assertEqual(config["language"], language)
                    self.assertEqual(config["workspace"], str(run / "workshop"))
                    with self.assertRaisesRegex(ValueError, "already exists"):
                        setup.initialize(run, language)
                original = (run / "config.json").read_bytes()
                partial = run.with_name(f"{language}-partial")
                partial.mkdir()
                link = run.with_name(f"{language}-link")
                link.symlink_to(run.with_name(f"{language}-missing"))
                for existing in (run, partial, link):
                    with self.subTest(language=language, existing=existing.name):
                        result = subprocess.run(
                            ["bash", "--noprofile", "--norc", "-c", shell_blocks[0]],
                            cwd=root, env={**os.environ, "RUN_DIR": str(existing)},
                            text=True, capture_output=True, check=False, timeout=10,
                        )
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn("Stop: RUN_DIR already exists", result.stderr)
                        self.assertEqual((run / "config.json").read_bytes(), original)
                        self.assertEqual(list(partial.iterdir()), [])
                        self.assertTrue(link.is_symlink())

    def test_access_checklist_names_roles_and_separates_human_and_project_access(self):
        expected_roles = {
            "user-foundry": "Foundry User",
            "user-model": "Cognitive Services OpenAI User",
            "user-search-service": "Search Service Contributor",
            "user-search-data": "Search Index Data Contributor",
            "project-monitor": "Log Analytics Reader",
        }
        for language in ("en", "ko"):
            text = self.documents[ROOT / "docs" / f"instructor.{language}.md"]
            access = text.split('<a id="access"></a>', 1)[1].split('<a id="existing-foundation"></a>', 1)[0]
            rows = re.findall(r"^\| .+\|$", access, re.MULTILINE)
            with self.subTest(language=language):
                for operation, role in expected_roles.items():
                    matching = [row for row in rows if f"`{operation}`" in row]
                    self.assertEqual(len(matching), 1, operation)
                    self.assertIn(f"| {role} |", matching[0])
                monitoring = [row for row in rows if "| Log Analytics Reader |" in row]
                self.assertEqual(len(monitoring), 2, "Human access and project identity need separate rows.")
                self.assertIn("prepare-trace-access", next(row for row in rows if "`project-monitor`" in row))
                self.assertTrue(any("| Reader |" in row and "AZURE_RESOURCE_GROUP" in row for row in rows))
                discovery = next(row for row in rows if "| Reader |" in row)
                for field in ("AZURE_SUBSCRIPTION_ID", "preflight", "collect"):
                    self.assertIn(field, discovery)
                self.assertTrue(any("| Cognitive Services OpenAI Contributor |" in row for row in rows))

    def test_shared_planner_access_is_prepared_outside_team_ownership(self):
        for name, language in (("README.md", "en"), ("README.ko.md", "ko")):
            instructor = self.documents[ROOT / "docs" / f"instructor.{language}.md"]
            access = instructor.split('<a id="access"></a>', 1)[1]
            access = access.split('<a id="existing-foundation"></a>', 1)[0]
            preparation = instructor.split('<a id="shared-search-access"></a>', 1)[1]
            preparation = preparation.split("```bash", 1)[0]
            with self.subTest(language=language):
                self.assertIn("](#shared-search-access)", access)
                for field in ("AZURE_SEARCH_NAME", "AZURE_AI_ACCOUNT_NAME",
                              "Cognitive Services User", "owned_roles", "local-state.json"):
                    self.assertIn(field, preparation)
                main = self.documents[ROOT / name]
                cleanup = main.split('<a id="cleanup-plan"></a>', 1)[1]
                self.assertIn(f"docs/instructor.{language}.md#shared-search-access", cleanup)
                self.assertEqual(main.count(f"docs/instructor.{language}.md#role-recovery"), 2)
                recovery = access.split('<a id="role-recovery"></a>', 1)[1]
                for field in ("prepare-iq", "grant-agent-access", "hosted-agent.json",
                              "instance_identity", "principal_id", "LAB_AGENT_NAME"):
                    self.assertIn(field, recovery)

    def test_subscription_quota_is_checked_before_creating_paid_foundation(self):
        from contracts import MODEL_SPECS

        expected = {model: "50" for model, _ in MODEL_SPECS.values()}
        expected["gpt-5.4-mini"] = "100"
        for language in ("en", "ko"):
            text = self.documents[ROOT / "docs" / f"environment.{language}.md"]
            with self.subTest(language=language):
                self.assertLess(text.index('<a id="subscription-quota"></a>'),
                                text.index('<a id="setup-foundation"></a>'))
                quota = text.split('<a id="subscription-quota"></a>', 1)[1]
                quota = quota.split('<a id="setup-foundation"></a>', 1)[0]
                self.assertEqual(dict(re.findall(
                    r"^\| `([^`]+)`[^|\n]*\| (\d+) capacity units \|$", quota, re.MULTILINE,
                )), expected)
                for field in ("Sweden Central", "GlobalStandard", "TPM", "RUN_DIR",
                              "https://learn.microsoft.com/azure/foundry/openai/how-to/quota"):
                    self.assertIn(field, quota)

    def test_cleanup_recovery_separates_verification_from_partial_deletion(self):
        for language in ("en", "ko"):
            text = self.documents[ROOT / "docs" / f"troubleshooting.{language}.md"]
            recovery = text.split('<a id="cleanup-recovery"></a>', 1)[1]
            recovery = re.split(r'\n<a id="(?!partial-cleanup")[^"]+"></a>', recovery, maxsplit=1)[0]
            verification, remaining = recovery.split('<a id="partial-cleanup"></a>', 1)
            with self.subTest(language=language):
                self.assertEqual([args for _, _, args in commands(verification)], [["check-cleanup"]])
                self.assertEqual([args for _, _, args in commands(remaining)], [
                    ["cleanup", "--dry-run"], ["cleanup", "--confirm"], ["check-cleanup"],
                ])
                self.assertIn("src/agent/.foundry/local-state.json", verification)
                before_retry = remaining.split("```bash", 1)[0]
                for filename in ("cleanup-plan.json", "local-state.json", "cleanup.json", "cleanup-check.json"):
                    self.assertIn(filename, before_retry)
                self.assertIn(f"environment.{language}.md#final-cleanup-check", remaining)

    def test_partial_cleanup_retry_preserves_original_evidence_and_uses_remaining_plan(self):
        cloud = importlib.import_module("cloud_setup")
        state = {
            "agent_owned": "fixture-agent", "owned_models": [], "owned_search_paths": [],
            "owned_roles": ["fixture-role"],
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            results = root / "results"
            results.mkdir()
            ownership = root / "local-state.json"
            ownership.write_text(json.dumps(state))
            with patch.object(cloud, "authenticate"), \
                    patch.object(cloud.RuntimeConfig, "from_env") as config, \
                    patch.object(cloud, "load_state", return_value=state), \
                    patch.object(cloud, "save_state", side_effect=lambda value: ownership.write_text(json.dumps(value))), \
                    patch.object(cloud, "RESULTS_DIR", results), \
                    patch.object(cloud, "search_client"), \
                    patch.object(cloud, "deployments", return_value=[]), \
                    patch.object(cloud, "azd") as delete_agent, \
                    patch.object(cloud, "az", side_effect=[RuntimeError("fixture role deletion failed"), {}]), \
                    contextlib.redirect_stdout(io.StringIO()):
                config.return_value.agent_name = "fixture-agent"
                with self.assertRaisesRegex(RuntimeError, "fixture role deletion failed"):
                    cloud.cleanup(confirm=True)
                self.assertNotIn("agent_owned", state)
                self.assertEqual(state["owned_roles"], ["fixture-role"])
                self.assertFalse((results / "cleanup.json").exists())
                archive = results / "original-attempt"
                archive.mkdir()
                originals = {
                    "cleanup-plan.json": (results / "cleanup-plan.json").read_bytes(),
                    "local-state.json": ownership.read_bytes(),
                }
                for name, contents in originals.items():
                    (archive / name).write_bytes(contents)
                cloud.cleanup(confirm=False)
                self.assertEqual((results / "cleanup-plan.json").read_bytes(), originals["cleanup-plan.json"])
                cloud.cleanup(confirm=True)
                completed = json.loads((results / "cleanup.json").read_text())
                self.assertTrue(completed["completed"])
                self.assertIsNone(completed["plan"]["agent"])
                self.assertEqual(completed["plan"]["role_assignments"], ["fixture-role"])
                self.assertEqual(json.loads(originals["cleanup-plan.json"])["agent"], "fixture-agent")
                delete_agent.assert_called_once()
                for name, contents in originals.items():
                    self.assertEqual((archive / name).read_bytes(), contents)

    def test_early_stop_uses_owned_objects_not_completed_evaluations(self):
        from cloud_setup import cleanup_plan

        plan = cleanup_plan({"owned_models": [], "owned_search_paths": [], "owned_roles": []})
        self.assertIsNone(plan["agent"])
        self.assertEqual(plan["search_objects"], [])
        self.assertIn("evaluation evidence", plan["preserved"])
        for name, language in (("README.md", "en"), ("README.ko.md", "ko")):
            text = self.documents[ROOT / name]
            stop = text.split('<a id="stop-early"></a>', 1)[1].split('<a id="cleanup-plan"></a>', 1)[0]
            cleanup = text.split('<a id="cleanup-plan"></a>', 1)[1]
            foundation = self.documents[ROOT / "docs" / f"environment.{language}.md"]
            foundation = foundation.split('<a id="final-cleanup"></a>', 1)[1]
            with self.subTest(language=language):
                self.assertIn("#stop-early", text.split('<a id="start"></a>', 1)[0])
                self.assertIn("#cleanup-plan", LINKS.findall(prose(stop)))
                self.assertIn(f"docs/environment.{language}.md#final-cleanup", LINKS.findall(prose(stop)))
                self.assertEqual(list(commands(stop)), [], "Stopping early must not synthesize missing results.")
                _, script, args = next(commands(cleanup))
                self.assertEqual((script, args), ("workshop", ["cleanup", "--dry-run"]))
                self.assertIn("agent: null", cleanup)
                self.assertIn(f"../{name}#stop-early", LINKS.findall(prose(foundation)))

    def test_reference_returns_do_not_skip_workspace_preparation(self):
        for name, language in (("README.md", "en"), ("README.ko.md", "ko")):
            text = self.documents[ROOT / "docs" / f"reference.{language}.md"]
            models = text.split('<a id="model-names"></a>', 1)[1].split('<a id="execution-path"></a>', 1)[0]
            endpoints = text.split('<a id="endpoints"></a>', 1)[1].split('<a id="language"></a>', 1)[0]
            with self.subTest(language=language):
                self.assertIn(f"../{name}#workspace-settings", LINKS.findall(prose(models)))
                self.assertIn(f"../{name}#start", LINKS.findall(prose(endpoints)))
                self.assertNotIn(f"../{name}#lab-a", LINKS.findall(prose(endpoints)))

    def test_independent_commands_have_individual_checkpoints(self):
        evidence_stages = {"collect", "evaluate", "compare", "monitor", "summary", "verify"}
        guides = [(ROOT / name, evidence_stages) for name in ("README.md", "README.ko.md")]
        guides.extend(
            (ROOT / "docs" / f"{guide}.{language}.md", stages)
            for guide, stages in (
                ("environment", {"prepare-models", "calibrate"}),
                ("instructor", {"preflight", "prepare-models", "calibrate"}),
                ("troubleshooting", {"collect"}),
            )
            for language in ("en", "ko")
        )
        for path, stages in guides:
            korean = path.name.endswith(".ko.md")
            checkpoint, recovery = ("**완료 확인:**", "**다르면:**") if korean else ("**Checkpoint:**", "**If not:**")
            text = self.documents[path]
            fences = list(FENCES.finditer(text))
            checked = set()
            for index, fence in enumerate(fences):
                documented = list(commands(fence[0]))
                if not any(script == "workshop" and args[0] in stages
                           for _, script, args in documented):
                    continue
                with self.subTest(document=path.name, command=fence[2].strip()):
                    self.assertEqual(len(documented), 1, "Keep independently recoverable stages separate.")
                    checked.add(documented[0][2][0])
                    end = fences[index + 1].start() if index + 1 < len(fences) else len(text)
                    following = re.split(
                        r"\n(?:#{2,3} |\*\*(?:Terminal|Editor|Portal|터미널|편집기|포털))",
                        text[fence.end():end], maxsplit=1,
                    )[0]
                    self.assertIn(checkpoint, following)
                    self.assertIn(recovery, following)
            self.assertEqual(checked, stages, path.name)

    def test_collection_recovery_returns_to_evaluation_without_repeating_later_stages(self):
        routes = (
            ("baseline", "dev", "2", "baseline-evaluation"),
            ("improved", "dev", "4", "candidate-evaluation"),
            ("holdout", "holdout", "4", "holdout-evaluation"),
        )
        for name, language in (("README.md", "en"), ("README.ko.md", "ko")):
            main = self.documents[ROOT / name]
            recovery = self.documents[ROOT / "docs" / f"troubleshooting.{language}.md"]
            recovery = recovery.split('<a id="collection-retry"></a>', 1)[1]
            recovery = recovery.split('<a id="evaluation-retry"></a>', 1)[0]
            with self.subTest(document=name):
                self.assertEqual(
                    [(script, args) for _, script, args in commands(recovery)],
                    [
                        ("workshop", ["collect", "--split", split, "--label", f"{label}-retry",
                                      "--concurrency", concurrency])
                        for label, split, concurrency, _ in routes
                    ],
                    "Collection recovery must not duplicate later evaluation or review commands.",
                )
            for label, _, _, anchor in routes:
                with self.subTest(document=name, label=label):
                    self.assertIn(f"../{name}#{anchor}", recovery)
                    destination = main.split(f'<a id="{anchor}"></a>', 1)[1]
                    _, script, arguments = next(commands(destination))
                    self.assertEqual((script, arguments), ("workshop", ["evaluate", "--label", label]))

    def test_new_environment_separates_model_preparation_from_calibration(self):
        for language in ("en", "ko"):
            path = ROOT / "docs" / f"environment.{language}.md"
            preparation = self.documents[path].split('<a id="setup-candidates"></a>', 1)[1]
            preparation = preparation.split('<a id="handoff"></a>', 1)[0]
            with self.subTest(document=path.name):
                self.assertEqual(
                    [(script, args) for _, script, args in commands(preparation)],
                    [("workshop", ["prepare-models"]), ("workshop", ["calibrate"])],
                    "prepare-models already runs preflight before and after creating missing models.",
                )
                calibration = preparation.split('<a id="setup-calibration"></a>', 1)[1]
                _, script, arguments = next(commands(calibration))
                self.assertEqual((script, arguments), ("workshop", ["calibrate"]))
                recovery = self.documents[ROOT / "docs" / f"troubleshooting.{language}.md"]
                self.assertIn(f"environment.{language}.md#setup-calibration", recovery)

    def test_self_study_setup_returns_to_the_binding_command(self):
        for name, language in (("README.md", "en"), ("README.ko.md", "ko")):
            text = self.documents[ROOT / name]
            with self.subTest(document=name):
                binding = text.split('<a id="bind-project"></a>', 1)[1]
                _, script, arguments = next(commands(binding))
                self.assertEqual((script, arguments), ("workshop", ["bind"]))
                for guide in ("environment", "instructor"):
                    preparation = self.documents[ROOT / "docs" / f"{guide}.{language}.md"]
                    self.assertIn(f"../{name}#bind-project", preparation)
                    self.assertIn(f"../{name}#how-to-follow", preparation)

    def test_report_preserves_monitor_fields_and_is_reused_by_optional_levels(self):
        report_path = "src/agent/.foundry/results/workshop-report.txt"
        for name, language in (("README.md", "en"), ("README.ko.md", "ko")):
            text = self.documents[ROOT / name]
            report = text.split('<a id="finish"></a>', 1)[1].split('<a id="levels"></a>', 1)[0]
            template = next(body for kind, _, body in blocks(report) if kind == "text")
            with self.subTest(document=name):
                self.assertIn(report_path, report)
                for field in ("Agent runs", "Total tokens", "production_release_approved=false"):
                    self.assertIn(field, template)
            for level in ("level-2", "level-3"):
                path = ROOT / "docs" / f"{level}.{language}.md"
                with self.subTest(document=path.name):
                    self.assertIn(report_path, self.documents[path].split("```bash", 1)[0])

    def test_assisted_execution_saves_and_reviews_the_main_report_before_cleanup(self):
        report_path = "src/agent/.foundry/results/workshop-report.txt"
        for name, language, cleanup in (("README.md", "en", "cleanup"), ("README.ko.md", "ko", "정리")):
            text = self.documents[ROOT / "docs" / f"copilot.{language}.md"]
            execution = text.split("### 3-2.", 1)[1].split('<a id="finish"></a>', 1)[0]
            prompt = next(body for kind, _, body in blocks(execution) if kind == "text")
            reporting = next(line for line in prompt.splitlines() if line.startswith("5."))
            completion = text.split('<a id="finish"></a>', 1)[1].split("<details>", 1)[0]
            with self.subTest(language=language):
                self.assertIn(report_path, self.documents[ROOT / name])
                self.assertIn("9-3", reporting)
                self.assertLess(reporting.index(report_path), reporting.index(cleanup))
                self.assertIn("production_release_approved=false", reporting)
                self.assertIn(report_path, completion)
                self.assertIn(f"../{name}#finish", completion)
                guards = prompt.split("6.", 1)[1]
                self.assertIn("workshop-report.txt", guards,
                              "The narrative report needs an exception to script-only evidence creation.")
                self.assertIn("--reviewer assistant", prompt)

    def test_assisted_recovery_allows_new_collection_labels_without_overwriting_old_ones(self):
        experiments = importlib.import_module("experiments")
        common = importlib.import_module("common")
        with tempfile.TemporaryDirectory() as directory:
            results = Path(directory)
            manifest = results / "baseline" / "manifest.json"
            manifest.parent.mkdir()
            original = '{"status": "failed", "run_id": "fixture-original"}\n'
            manifest.write_text(original, encoding="utf-8")
            with patch.object(common, "RESULTS_DIR", results), \
                    patch.object(experiments.RuntimeConfig, "from_env"), \
                    patch.object(experiments, "preflight", side_effect=AssertionError("No Azure calls")):
                with self.assertRaisesRegex(ValueError, "Label baseline already exists"):
                    experiments.collect("dev", "baseline")
            self.assertEqual(manifest.read_text(encoding="utf-8"), original)
        for language in ("en", "ko"):
            text = self.documents[ROOT / "docs" / f"copilot.{language}.md"]
            execution = text.split("### 3-2.", 1)[1].split('<a id="finish"></a>', 1)[0]
            prompt = next(body for kind, _, body in blocks(execution) if kind == "text")
            with self.subTest(language=language):
                self.assertIn(f"docs/troubleshooting.{language}.md#collection-retry", prompt)
                self.assertIn("retry label", prompt)
                recovery = self.documents[ROOT / "docs" / f"troubleshooting.{language}.md"]
                self.assertIn(["collect", "--split", "dev", "--label", "baseline-retry", "--concurrency", "2"],
                              [args for _, _, args in commands(recovery)])

    def test_assisted_handoffs_cover_initial_edits_terminal_and_foundation_costs(self):
        for name, language in (("README.md", "en"), ("README.ko.md", "ko")):
            text = self.documents[ROOT / "docs" / f"copilot.{language}.md"]
            execution = text.split("### 3-2.", 1)[1].split('<a id="finish"></a>', 1)[0]
            prompt = next(body for kind, _, body in blocks(execution) if kind == "text")
            sign_in = next(line for line in prompt.splitlines() if line.startswith("2."))
            completion = text.split('<a id="finish"></a>', 1)[1]
            completion = re.sub(r"<details>.*?</details>", "", completion, flags=re.DOTALL)
            with self.subTest(language=language):
                self.assertIn(".env.example", text.split("### 3-2.", 1)[0])
                self.assertIn(f"environment.{language}.md#initial-settings", text)
                self.assertIn(f"docs/instructor.{language}.md#existing-foundation", prompt)
                self.assertIn("LAB_AUX_DEPLOYMENT", prompt.split("6.", 1)[1])
                for field in ("bash", "resume-shell", "RUN_DIR/workshop"):
                    self.assertIn(field, sign_in)
                self.assertLess(execution.index(f"../{name}#resume-shell"),
                                execution.index(f"../{name}#login)"))
                self.assertIn(f"environment.{language}.md#final-cleanup", completion)
                self.assertIn("workshop-report.txt", completion)

    def test_ci_setup_covers_publication_and_recovered_review_inputs(self):
        import yaml

        workflow = yaml.safe_load((ROOT / "ci" / "release-gate.yml").read_text())
        trigger = workflow.get("on", workflow.get(True))["workflow_dispatch"]
        self.assertIn("baseline-<model_key>-<case_id>", trigger["inputs"]["review_row_id"]["description"])
        for name, language in (("README.md", "en"), ("README.ko.md", "ko")):
            text = self.documents[ROOT / "docs" / f"level-3.{language}.md"]
            setup = text.split('<a id="ci-setup"></a>', 1)[1]
            setup = setup.split('<a id="ci-review-provenance"></a>', 1)[0]
            with self.subTest(language=language):
                for field in ("Fork", "RUN_DIR/workshop", ".git", "ci/", "gh --version",
                              "gh auth status", "Add file", ".github/workflows/release-gate.yml",
                              "Run workflow", "baseline-<model_key>-<case_id>",
                              "baseline-retry-sol-D01", "baseline-sol-D01",
                              f"../{name}#review-case"):
                    self.assertIn(field, setup)
                self.assertLess(setup.index("Add file"), setup.index("Run workflow"))
                errored = next(row for row in setup.splitlines() if row.startswith("| `errored rows`"))
                for field in ("evaluation.json", "429", "Retry-After"):
                    self.assertIn(field, errored)
                self.assertNotIn("PermissionDenied", errored)
                for field in ("workshop-results", "`evaluate`", "`gate`", "artifact"):
                    self.assertIn(field, setup)

    def test_ci_review_documentation_distinguishes_new_answers_from_original_provenance(self):
        from experiments import feedback

        text = (ROOT / "ci" / "evaluate-candidate.sh").read_text(encoding="utf-8")
        baseline = text.split("  baseline)", 1)[1].split(";;", 1)[0]
        calls = [args for _, _, args in commands(f"```bash\n{baseline}\n```\n")]
        review = next(args for args in calls if args[0] == "feedback")
        self.assertLess(next(i for i, args in enumerate(calls) if args[0] == "collect"), calls.index(review))
        self.assertNotIn("--reviewer", review)
        reviewer = inspect.signature(feedback).parameters["reviewer"].default
        for name, language in (("README.md", "en"), ("README.ko.md", "ko")):
            text = self.documents[ROOT / "docs" / f"level-3.{language}.md"]
            boundary = text.split('<a id="ci-review-provenance"></a>', 1)[1].split("\n\n", 2)[1]
            with self.subTest(language=language):
                for field in ("review_reason", "row_id", "trace_id", "feedback", "verify", reviewer):
                    self.assertIn(f"`{field}`", boundary)
                for anchor in ("save-review", "finish"):
                    self.assertIn(f"../{name}#{anchor}", boundary)

    def test_optional_levels_locate_the_evidence_needed_for_interpretation(self):
        for language in ("en", "ko"):
            level2 = self.documents[ROOT / "docs" / f"level-2.{language}.md"]
            level3 = self.documents[ROOT / "docs" / f"level-3.{language}.md"]
            level3 = re.sub(r"<details>.*?</details>", "", level3, flags=re.DOTALL)
            with self.subTest(language=language):
                suite = level2.split('<a id="evaluate-suite"></a>', 1)[1].split("<details>", 1)[0]
                self.assertIn("/6", suite)
                self.assertIn("18", suite)
                rubric = level3.split('<a id="generate-rubric"></a>', 1)[1]
                rubric = rubric.split('<a id="stress-test"></a>', 1)[0]
                self.assertIn("7-4", rubric)
                self.assertIn("failed rows: none", rubric)
                stress = level3.split('<a id="stress-test"></a>', 1)[1]
                stress = stress.split('<a id="red-team"></a>', 1)[0]
                self.assertIn("src/agent/.foundry/results/level3/stress-sol.json", stress)
                for field in ("failed_questions", "query", "failed"):
                    self.assertIn(f"`{field}`", stress)
                continuous = level3.split('<a id="continuous-eval"></a>', 1)[1]
                continuous = continuous.split('<a id="release-gate"></a>', 1)[0]
                self.assertIn("src/agent/.foundry/results/level3/continuous.json", continuous)
                for field in ("runs", "created", "run_id"):
                    self.assertIn(f"`{field}`", continuous)

    def test_level3_recovery_archives_only_eligible_state_without_losing_evidence(self):
        recovery_blocks = []
        for language in ("en", "ko"):
            recovery = self.documents[ROOT / "docs" / f"troubleshooting.{language}.md"]
            recovery = recovery.split('<a id="level-state-recovery"></a>', 1)[1]
            recovery = recovery.split('<a id="cleanup-recovery"></a>', 1)[0]
            shell_blocks = [body for kind, _, body in blocks(recovery) if kind == "bash"]
            self.assertEqual(len(shell_blocks), 1, "Recovery archives state; it needs no separate deletion block.")
            recovery_blocks.append(shell_blocks[0])
        self.assertEqual(*recovery_blocks, "Both editions must preserve evidence in the same way.")
        body = recovery_blocks[0]
        env = {**os.environ, "PATH": str(Path(sys.executable).parent) + os.pathsep + os.environ.get("PATH", "")}
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory).resolve() / "workshop with spaces"
            relative = Path("src/agent/.foundry/results/level3/stress-sol.json")
            state = workspace / relative
            state.parent.mkdir(parents=True)
            raw = state.with_name("stress-sol-output.json")
            ownership = workspace / "src/agent/.foundry/local-state.json"
            ownership.write_text('{"language":"en","owned_schedules":["fixture"]}\n')
            foreign = workspace.parent / "other-language" / relative
            foreign.parent.mkdir(parents=True)
            foreign.write_text('{"eval_id":"foreign-fixture"}\n')
            preserved = {ownership: ownership.read_bytes(), foreign: foreign.read_bytes()}

            def run(path):
                return subprocess.run(
                    ["bash", "--noprofile", "--norc", "-c", body],
                    input=str(path) + "\n", cwd=workspace, env=env,
                    text=True, capture_output=True, check=False, timeout=10,
                )

            archives = {}
            for number, path in enumerate((relative, state)):
                with self.subTest(path_form="relative" if number == 0 else "absolute"):
                    state.write_text(json.dumps({"eval_id": f"fixture-{number}", "status": "failed"}))
                    raw.write_text(json.dumps([{"id": f"output-fixture-{number}"}]))
                    originals = {state.name: state.read_bytes(), raw.name: raw.read_bytes()}
                    result = run(path)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    archived = Path(result.stdout.strip().removeprefix("Archived failed state: "))
                    self.assertEqual(archived.name, state.name)
                    self.assertEqual(archived.parent.parent, state.parent)
                    self.assertTrue(archived.parent.name.startswith("failed-attempt-"))
                    self.assertFalse(state.exists())
                    for filename, contents in originals.items():
                        saved = archived.parent / filename
                        self.assertEqual(saved.read_bytes(), contents)
                        archives[saved] = contents
                    self.assertEqual(raw.read_bytes(), originals[raw.name])
            self.assertEqual(len(list(state.parent.glob("failed-attempt-*"))), 2)

            rejected = [foreign, raw, state.with_name("traces-missing.json")]
            for filename in ("agent-dev.json", "continuous.json"):
                path = state.with_name(filename)
                path.write_text('{"run_id":"nonretryable-fixture"}\n')
                preserved[path] = path.read_bytes()
                rejected.append(path)
            symlink = state.with_name("red-team-sol.json")
            symlink.symlink_to(foreign)
            rejected.append(symlink)
            state.write_text('{"eval_id":"keep-on-copy-error"}\n')
            preserved[state] = state.read_bytes()
            raw.unlink()
            raw.symlink_to(foreign)
            rejected.append(state)
            for path in rejected:
                with self.subTest(rejected=str(path)):
                    result = run(path)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("Stop:", result.stderr)
                    self.assertEqual(len(list(state.parent.glob("failed-attempt-*"))), 2)
                    for saved, contents in {**preserved, **archives}.items():
                        self.assertEqual(saved.read_bytes(), contents)

    def test_dashboard_is_checked_before_reporting_and_cleanup(self):
        for name in ("README.md", "README.ko.md"):
            text = self.documents[ROOT / name]
            with self.subTest(document=name):
                sequence = ("lab-g", "operational-dashboard", "finish", "cleanup")
                positions = [text.index(f'<a id="{anchor}"></a>') for anchor in sequence]
                self.assertEqual(positions, sorted(positions))
                report = text[positions[2]:positions[3]]
                self.assertIn("src/agent/.foundry/results/verified-evidence.json", report)

    def test_execution_checkpoints_have_recovery_paths(self):
        guides = [ROOT / "README.md", ROOT / "README.ko.md"]
        guides.extend(ROOT / "docs" / f"{guide}.{language}.md"
                      for guide in ("level-2", "level-3", "environment", "instructor")
                      for language in ("en", "ko"))
        for path in guides:
            korean = path.name.endswith(".ko.md")
            checkpoint, recovery = ("**완료 확인:**", "**다르면:**") if korean else ("**Checkpoint:**", "**If not:**")
            text = prose(self.documents[path])
            starts = [match.start() for match in re.finditer(re.escape(checkpoint), text)]
            self.assertTrue(starts, f"{path.name} has no checkpoints.")
            for start, end in zip(starts, [*starts[1:], len(text)]):
                heading = re.search(r"^#{1,3} ", text[start:end], re.MULTILINE)
                with self.subTest(document=path.name, line=text.count("\n", 0, start) + 1):
                    self.assertIn(recovery, text[start:start + heading.start()] if heading else text[start:end])


if __name__ == "__main__":
    unittest.main()
