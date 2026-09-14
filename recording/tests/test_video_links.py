import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "recording"))
from video_links import published_video_url


class VideoLinkTests(unittest.TestCase):
    def fixture(self, root: Path):
        video = root / "clip.mp4"
        video.write_bytes(b"test media bytes")
        entry = {
            "url": "https://github.com/user-attachments/assets/11111111-1111-4111-8111-111111111111",
            "content_type": "video/mp4", "bytes": video.stat().st_size,
            "sha256": hashlib.sha256(video.read_bytes()).hexdigest(),
        }
        manifest = root / "links.json"
        manifest.write_text(json.dumps({"videos": {"clip.mp4": entry}}))
        return video, manifest, entry

    def test_resolves_only_the_registered_video_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            video, manifest, entry = self.fixture(root)
            self.assertEqual(published_video_url(video, manifest, root), entry["url"])
            video.write_bytes(b"changed media")
            with self.assertRaises(ValueError):
                published_video_url(video, manifest, root)

    def test_missing_registration_fails_explicitly(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            video, manifest, _ = self.fixture(root)
            manifest.write_text('{"videos": {}}')
            with self.assertRaises(ValueError):
                published_video_url(video, manifest, root)

    def test_temporary_or_non_playback_urls_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            video, manifest, entry = self.fixture(root)
            for url in [
                "https://raw.githubusercontent.com/example/repo/main/clip.mp4",
                "https://github.com/example/repo/blob/main/clip.mp4",
                "https://private-user-images.githubusercontent.com/clip.mp4?jwt=temporary",
                entry["url"] + "?token=temporary",
            ]:
                with self.subTest(url=url):
                    manifest.write_text(json.dumps({"videos": {"clip.mp4": {**entry, "url": url}}}))
                    with self.assertRaises(ValueError):
                        published_video_url(video, manifest, root)

    def test_all_tracked_videos_have_matching_public_urls(self):
        videos = subprocess.check_output(
            ["git", "ls-files", "-z", "*.mp4", "*.webm"], cwd=ROOT, text=True,
        ).split("\0")
        registered = json.loads((ROOT / "docs/video-links.json").read_text())["videos"]
        self.assertEqual(set(filter(None, videos)), set(registered))
        for name in filter(None, videos):
            with self.subTest(video=name):
                self.assertTrue(published_video_url(ROOT / name).startswith("https://github.com/user-attachments/assets/"))

    def test_public_markdown_has_no_repository_file_video_links(self):
        files = subprocess.check_output(
            ["git", "ls-files", "-z", "*.md"], cwd=ROOT, text=True,
        ).split("\0")
        for name in filter(None, files):
            for target in re.findall(r"\]\(([^)]+)\)", (ROOT / name).read_text()):
                with self.subTest(file=name, link=target):
                    self.assertIsNone(re.search(r"\.(mp4|webm)(?:[?#].*)?$", target, re.I))

    def test_chapter_times_do_not_expand_into_repeated_github_players(self):
        text = (ROOT / "docs/action-captures.ko.md").read_text()
        self.assertIsNone(re.search(r"user-attachments/assets/[^)\s]+#t=", text))
        self.assertIn("로컬 챕터 플레이어 사용법", text)


if __name__ == "__main__":
    unittest.main()
