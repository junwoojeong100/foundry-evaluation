import hashlib
import json
import re
import subprocess
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def tracked_files(*patterns):
    output = subprocess.check_output(["git", "ls-files", "-z", *patterns], cwd=ROOT, text=True)
    return set(filter(None, output.split("\0")))


class GuideMediaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.videos = json.loads((ROOT / "docs/video-links.json").read_text())["videos"]
        cls.documents = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]

    def test_exactly_one_registered_summary_video_is_shipped(self):
        actual = tracked_files("*.mp4", "*.webm", "*.mov")
        self.assertEqual(len(actual), 1)
        self.assertEqual(actual, set(self.videos))
        for name, entry in self.videos.items():
            path = (ROOT / name).resolve()
            self.assertTrue(path.is_relative_to(ROOT))
            with path.open("rb") as stream:
                self.assertEqual(hashlib.file_digest(stream, "sha256").hexdigest(), entry["sha256"])
            self.assertEqual(path.stat().st_size, entry["bytes"])
            self.assertEqual(entry["content_type"], "video/mp4")
            self.assertEqual(entry["duration_seconds"], 1315.55)
            self.assertRegex(
                entry["url"],
                r"^https://github\.com/user-attachments/assets/[0-9a-f-]{36}$",
            )

    def test_public_guides_link_only_the_single_playable_video(self):
        links = []
        for path in self.documents:
            for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
                self.assertIsNone(re.search(r"\.(mp4|webm|mov)(?:[?#].*)?$", target, re.I))
                if "github.com/user-attachments/assets/" in target:
                    links.append(target)
        self.assertEqual(links, [next(iter(self.videos.values()))["url"]])

    def test_every_shipped_asset_is_used_by_a_guide_or_the_video_configuration(self):
        needed = set(self.videos)
        for path in self.documents:
            for target in re.findall(r"\]\(([^)\s]+)\)", path.read_text()):
                url = urlsplit(target)
                if url.scheme or url.netloc or not url.path:
                    continue
                destination = (path.parent / unquote(url.path)).resolve()
                if destination.is_relative_to(ROOT / "docs/assets"):
                    needed.add(destination.relative_to(ROOT).as_posix())
        self.assertEqual(tracked_files("docs/assets/*"), needed)

    def test_record_only_files_and_recording_tools_are_not_shipped(self):
        self.assertFalse(tracked_files("artifacts/*", "recording/*", "portal_recording/*"))
        for name in (
            "action-captures.ko.md", "recording.ko.md", "portal-recording.ko.md",
            "video-playback-verification.json", "sources.ko.md",
        ):
            self.assertFalse((ROOT / "docs" / name).exists())


if __name__ == "__main__":
    unittest.main()
