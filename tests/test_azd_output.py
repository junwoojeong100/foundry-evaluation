import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src/agent"), str(ROOT / "scripts")]

from common import parse_azd_json
from experiments import parse_invocation_output

NOTICE = (
    "WARNING: A new version of extension 'Foundry agents (Beta)' is available: "
    "1.0.0-beta.10 -> 1.0.0-beta.15\n"
    "  \u2022 To update: azd extension update azure.ai.agents\n"
    "  \u2022 To update all: azd extension update --all\n\n"
)


class AzdOutputTests(unittest.TestCase):
    def test_known_update_notice_is_logged_not_mixed_into_json(self):
        with self.assertLogs("common", level="WARNING"):
            self.assertEqual(parse_azd_json('{"value":1}' + NOTICE), {"value": 1})

    def test_content_length_is_utf8_bytes_and_preserves_crlf(self):
        expected = {"answer": "\ud55c\uad6d\uc5b4"}
        body = json.dumps(expected, ensure_ascii=False, indent=2).replace("\n", "\r\n")
        raw = f"HTTP/1.1 200 OK\r\nContent-Length: {len(body.encode('utf-8'))}\r\n\r\n{body}{NOTICE}"
        with self.assertLogs("common", level="WARNING"):
            self.assertEqual(parse_invocation_output(raw), expected)

    def test_missing_content_length_still_checks_the_entire_suffix(self):
        with self.assertLogs("common", level="WARNING"):
            self.assertEqual(parse_invocation_output('HTTP/1.1 200 OK\n\n{"value":1}' + NOTICE), {"value": 1})
        for suffix in ('{"error":"failed"}', "ERROR: invocation failed", "unexpected output"):
            with self.subTest(suffix=suffix):
                with self.assertRaises(ValueError):
                    parse_invocation_output('HTTP/1.1 200 OK\n\n{"value":1}' + suffix)

    def test_truncated_or_ambiguous_http_length_is_rejected(self):
        for raw in (
            'HTTP/1.1 200 OK\nContent-Length: 999\n\n{"value":1}',
            'HTTP/1.1 200 OK\nContent-Length: 11\nContent-Length: 11\n\n{"value":1}',
        ):
            with self.assertRaises(ValueError):
                parse_invocation_output(raw)

    def test_unknown_content_after_a_sized_body_is_rejected(self):
        body = '{"value":1}'
        with self.assertRaises(ValueError):
            parse_invocation_output(f"HTTP/1.1 200 OK\nContent-Length: {len(body)}\n\n{body}" + '{"error":"failed"}')


if __name__ == "__main__":
    unittest.main()
