import argparse
import json
import re
import subprocess
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from build_video import OUT, ROOT, WORK, duration, sha256, write_json

VIDEO = OUT / "foundry-portal-learning-loop-15min-ko.mp4"
ORIGINAL_SHA256 = "59838801ba8082f8fc0f20e4ff871e96235e879467275342dc3f84a1e9c2a86e"
FRAMES = WORK / "verification-frames"


def inspect():
    info = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_format", "-show_streams", "-show_chapters", "-of", "json", str(VIDEO),
    ], text=True))
    video = next(item for item in info["streams"] if item["codec_type"] == "video")
    audio = next(item for item in info["streams"] if item["codec_type"] == "audio")
    if (
        abs(float(info["format"]["duration"]) - 900) > 0.05
        or (video["width"], video["height"]) != (1920, 1080)
        or video["codec_name"] != "h264"
        or audio["codec_name"] != "aac"
        or len(info["chapters"]) != 12
    ):
        raise ValueError("The delivered video does not meet its media contract.")
    subprocess.run([
        "ffmpeg", "-v", "error", "-xerror", "-i", str(VIDEO),
        "-map", "0:v:0", "-map", "0:a:0", "-f", "null", "-",
    ], check=True)
    edl = json.loads((OUT / "edit-decision-list.json").read_text())
    FRAMES.mkdir(exist_ok=True)
    samples = []
    for clip in edl["clips"]:
        for suffix, time in (
            ("a", clip["start"] + 0.2),
            ("m", clip["start"] + clip["seconds"] / 2),
            ("z", clip["start"] + clip["seconds"] - 0.2),
        ):
            samples.append({
                "file": FRAMES / f"{clip['index']:03}-{suffix}.png",
                "time": time, "clip": clip["index"], "surface": clip["surface"],
            })

    def extract(sample):
        subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", str(sample["time"]),
            "-i", str(VIDEO), "-frames:v", "1", "-threads", "1", str(sample["file"]),
        ], check=True)
        return sample

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(extract, samples))
    font = ImageFont.load_default(size=17)
    screenshots = OUT / "screenshots"
    screenshots.mkdir(exist_ok=True)
    for offset in range(0, len(samples), 24):
        sheet = Image.new("RGB", (1920, 1800), "#20252b")
        draw = ImageDraw.Draw(sheet)
        for index, sample in enumerate(samples[offset:offset + 24]):
            x, y = (index % 4) * 480, (index // 4) * 300
            with Image.open(sample["file"]) as image:
                sheet.paste(image.resize((480, 270)), (x, y + 30))
            draw.text((x + 6, y + 5), f"{sample['file'].stem} | {sample['time']:.1f}s", fill="white", font=font)
        sheet.save(screenshots / f"contact-{offset // 24 + 1:02}.jpg", quality=90)
    for chapter in edl["chapters"]:
        time = chapter["start"] + chapter["duration"] / 2
        subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", str(time),
            "-i", str(VIDEO), "-frames:v", "1", str(screenshots / f"chapter-{chapter['index'] + 1:02}.png"),
        ], check=True)
    write_json(WORK / "media-check.json", {
        "sha256": sha256(VIDEO), "duration_seconds": duration(VIDEO),
        "resolution": "1920x1080", "video_codec": "h264", "audio_codec": "aac",
        "chapters": 12, "full_decode_checked": True, "sampled_frames": len(samples),
    })
    print(f"Full decode passed; exported {len(samples)} start/middle/end frames across {len(edl['clips'])} cuts.")


def finalize():
    media = json.loads((WORK / "media-check.json").read_text())
    findings = json.loads((WORK / "ocr-findings.json").read_text())
    if len(findings) != media["sampled_frames"] or any(item["findings"] for item in findings):
        raise ValueError("Sampled-frame privacy review is incomplete or has findings.")
    if sha256(VIDEO) != media["sha256"]:
        raise ValueError("The video changed after the decode/frame checks.")
    original = ROOT / "artifacts/recording/foundry-learning-loop-15min-ko.mp4"
    if sha256(original) != ORIGINAL_SHA256:
        raise ValueError("The original local-console video was changed.")
    secrets = re.compile(
        r"[?&](?:sig|token|access_token|code)=|(?:InstrumentationKey|AccountKey|SharedAccessKey)="
        r"|/(?:Users|home)/junwoo|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}",
        re.IGNORECASE,
    )
    with zipfile.ZipFile(OUT / "portal-final-evidence.zip") as bundle:
        if bundle.testzip() is not None:
            raise ValueError("Evidence ZIP is corrupt.")
        for name in bundle.namelist():
            if secrets.search(bundle.read(name).decode("utf-8")):
                raise ValueError(f"Sensitive material in evidence entry: {name}")
        evidence = json.loads(bundle.read("portal-summary.json"))
        comparison = json.loads(bundle.read("results/comparison.json"))
    verified = evidence["verification"]
    cleanup = evidence["cleanup"]
    if verified["primary_model_outputs"] != 64 or verified["distinct_verified_traces"] != 64:
        raise ValueError("The primary 64-response loop is incomplete.")
    if verified["production_release_approved"] is not False:
        raise ValueError("AI-assisted review must not be presented as production approval.")
    if (
        not cleanup["temporary_hosted_agent_absent"]
        or len(cleanup["ui_created_models_deleted"]) != 4
        or cleanup["temporary_search_objects_absent"] != 3
        or cleanup["temporary_role_assignments_absent"] != 2
        or not cleanup["ui_created_monitoring_reader_removed"]
        or not cleanup["existing_shared_agent_preserved"]
        or not cleanup["existing_shared_knowledge_base_preserved"]
    ):
        raise ValueError("Scoped cleanup or shared-resource preservation is incomplete.")
    scores = {}
    for label, item in comparison["labels"].items():
        models = list(item["models"].values())
        scores[label] = {
            "rows": sum(model["total"] for model in models),
            "business_passed": sum(model["business_passed"] for model in models),
            **{
                metric: sum(model["foundry_evaluators"][metric]["native_passed"] for model in models)
                for metric in ("groundedness", "relevance")
            },
        }
    write_json(OUT / "run-summary.json", {**evidence, "aggregate_scores": scores})
    edl = json.loads((OUT / "edit-decision-list.json").read_text())
    source = json.loads((OUT / "source-footage.json").read_text())
    for item in source["sources"]:
        if sha256(OUT / item["video"]) != item["sha256"]:
            raise ValueError("The recorded source footage changed.")
    report = {
        **media, "video": VIDEO.name, "bytes": VIDEO.stat().st_size,
        "headless_capture": True, "actual_portal_surfaces": ["ai.azure.com", "portal.azure.com"],
        "native_foundry_screen_seconds": sum(clip["seconds"] for clip in edl["clips"] if clip["surface"] == "ai.azure.com"),
        "native_azure_cloud_shell_screen_seconds": sum(clip["seconds"] for clip in edl["clips"] if clip["surface"] == "portal.azure.com"),
        "reading_hold_seconds": round(sum(clip["freeze_seconds"] for clip in edl["clips"]), 2),
        "reconstructed_ui": False, "waiting_intervals_excluded": True,
        "korean_keypoint_captions": 47, "audio": "AI-generated Korean Yuna narration",
        "primary_outputs": 64, "verified_traces": 64, "scores": scores,
        "production_release_approved": False, "scoped_cleanup_verified": True,
        "retained": cleanup["retained"], "sampled_frame_privacy_checks_passed": True,
        "evidence_secret_scan_passed": True, "original_video_preserved": True,
        "original_video_sha256": ORIGINAL_SHA256,
        "native_trace_dataset_creation_completed": False,
        "continuous_or_scheduled_evaluation_enabled": False,
    }
    write_json(OUT / "delivery-verification.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("inspect", "finalize"))
    {"inspect": inspect, "finalize": finalize}[parser.parse_args().command]()
