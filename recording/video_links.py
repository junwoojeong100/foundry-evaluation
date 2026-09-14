"""Resolve a published video URL only when it matches the actual video bytes."""

import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/video-links.json"


def published_video_url(video: Path, manifest: Path = MANIFEST, root: Path = ROOT) -> str:
    path = video.resolve()
    relative = path.relative_to(root.resolve()).as_posix()
    data = json.loads(manifest.read_text())
    entry = data["videos"].get(relative)
    if entry is None:
        raise ValueError(f"Upload {relative} to GitHub media and register its URL before publishing the guide.")
    parsed = urlsplit(entry["url"])
    if (
        parsed.scheme != "https" or parsed.hostname != "github.com"
        or not parsed.path.startswith("/user-attachments/assets/")
        or parsed.query or parsed.fragment
    ):
        raise ValueError("Use a canonical GitHub attachment URL, not a temporary signed or repository-blob link.")
    with path.open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    if actual != entry["sha256"] or path.stat().st_size != entry["bytes"]:
        raise ValueError(f"The published URL belongs to different video bytes: {relative}. Upload the new version first.")
    if entry["content_type"] != "video/mp4":
        raise ValueError("The registered playback content type is not video/mp4.")
    return entry["url"]
