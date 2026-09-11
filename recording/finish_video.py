import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/recording"


def main():
    capture = json.loads((ROOT / ".recording/render-result.json").read_text(encoding="utf-8"))
    plan = json.loads((ROOT / ".recording/render-plan.json").read_text(encoding="utf-8"))
    if capture["status"] != "completed":
        raise ValueError("Headless recording has not completed.")
    source = Path(capture["video"])
    if not source.is_relative_to(OUT / "raw") or not source.exists():
        raise ValueError("Unexpected raw video path.")
    metadata = OUT / "chapters.ffmetadata"
    lines = [";FFMETADATA1", "title=모델은 바꾸고 조직의 학습은 남기는 15분 실습", "comment=실제 Azure CLI/SDK 실행기록을 Playwright headless로 녹화한 편집본. 대기구간 제거. 한국어 AI 합성 음성."]
    for chapter in plan["chapters"]:
        lines.extend([
            "[CHAPTER]", "TIMEBASE=1/1000",
            f"START={round(chapter['start']*1000)}",
            f"END={round((chapter['start']+chapter['duration'])*1000)}",
            f"title={chapter['index']+1:02} {chapter['title']}",
        ])
    metadata.write_text("\n".join(lines) + "\n", encoding="utf-8")
    lead = max(0.0, (capture["started"] - capture["page_created"]) / 1000)
    output = OUT / "foundry-learning-loop-15min-ko.mp4"
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-ss", f"{lead:.3f}", "-i", str(source), "-i", str(OUT / "narration-ko.wav"),
        "-i", str(metadata), "-map", "0:v:0", "-map", "1:a:0", "-map_metadata", "2",
        "-vf", "fps=25,format=yuv420p", "-c:v", "libx264", "-preset", "veryfast",
        "-crf", "21", "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
        "-metadata:s:a:0", "language=kor", "-t", "900", "-movflags", "+faststart",
        str(output),
    ], check=True)
    info = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_streams", "-show_format", "-show_chapters",
        "-of", "json", str(output),
    ], text=True))
    video = next(stream for stream in info["streams"] if stream["codec_type"] == "video")
    audio = next(stream for stream in info["streams"] if stream["codec_type"] == "audio")
    length = float(info["format"]["duration"])
    if abs(length - 900) > 0.2 or (video["width"], video["height"]) != (1920, 1080):
        raise ValueError("Video duration or dimensions do not meet the delivery contract.")
    if len(info["chapters"]) != 12 or audio["codec_name"] != "aac":
        raise ValueError("Missing chapters or narration audio.")
    subprocess.run([
        "ffmpeg", "-v", "error", "-i", str(output), "-f", "null", "-"
    ], check=True)
    summary = {
        "video": output.name, "duration_seconds": length, "width": video["width"],
        "height": video["height"], "video_codec": video["codec_name"], "audio_codec": audio["codec_name"],
        "chapters": len(info["chapters"]), "headless_capture": True,
        "waiting_intervals_excluded": True, "capture_method": "Playwright recordVideo",
        "presentation": "recorded-result walkthrough after actual fresh Azure execution; not the Foundry portal UI",
        "audio": "Korean AI-generated Yuna narration", "full_decode_checked": True,
    }
    (OUT / "video-verification.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
