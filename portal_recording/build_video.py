import argparse
import hashlib
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/foundry-portal-recording"
WORK = ROOT / ".portal-recording"
STORY_PATH = ROOT / "portal_recording/story.json"
FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
FPS = 25


def run(args):
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL)


def duration(path):
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "csv=p=0", str(path),
    ], text=True).strip())


def stamp(seconds):
    milliseconds = round(seconds * 1000)
    hours, milliseconds = divmod(milliseconds, 3600000)
    minutes, milliseconds = divmod(milliseconds, 60000)
    seconds, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_plan():
    story = json.loads(STORY_PATH.read_text())
    metadata = json.loads((OUT / "capture-metadata.json").read_text())
    pages = {item["key"]: item for item in metadata["pages"]}
    plan = {"target_seconds": story["target_seconds"], "chapters": [], "cues": [], "clips": []}
    cursor = 0
    for chapter_index, chapter in enumerate(story["chapters"]):
        chapter_start = cursor
        for cue in chapter["cues"]:
            cue_start = cursor
            cue_index = len(plan["cues"])
            for clip in cue["clips"]:
                length = clip["to"] - clip["from"]
                if length <= 0 or clip["seconds"] <= 0:
                    raise ValueError("Clip durations must be positive.")
                if clip["seconds"] < length / 2:
                    raise ValueError("A cut must not accelerate portal interactions beyond 2x.")
                source = pages[clip["page"]]
                path = Path(source["video"])
                if not path.is_file() or not path.is_relative_to(OUT / "raw"):
                    raise ValueError("The source must be an existing actual portal recording.")
                offset = clip["from"] - source["offset_ms"] / 1000
                if offset < 0 or (clip["page"] == "main" and clip["from"] < 59.124):
                    raise ValueError("Unrecorded or privacy-excluded source interval.")
                plan["clips"].append({
                    **clip, "index": len(plan["clips"]), "cue": cue_index,
                    "start": cursor, "source": str(path), "source_offset": offset,
                    "freeze_seconds": max(0, clip["seconds"] - length),
                    "speed": max(1, length / clip["seconds"]),
                    "surface": "portal.azure.com" if clip["page"] == "main" and clip["from"] > 1000 else "ai.azure.com",
                })
                cursor += clip["seconds"]
            plan["cues"].append({
                "index": cue_index, "chapter": chapter_index, "start": cue_start,
                "duration": cursor - cue_start, "caption": cue["caption"], "text": cue["text"],
                "title": chapter["title"],
            })
        plan["chapters"].append({
            "index": chapter_index, "title": chapter["title"],
            "start": chapter_start, "duration": cursor - chapter_start,
        })
    if cursor != story["target_seconds"] or cursor != 900:
        raise ValueError(f"The actual edit timeline is {cursor}s, not 900s.")
    return story, metadata, plan


def wrapped(draw, text, font, width):
    lines = [""]
    for char in text:
        if draw.textlength(lines[-1] + char, font=font) > width:
            lines.append(char)
        else:
            lines[-1] += char
    return [line.strip() for line in lines]


def caption_image(cue):
    image = Image.new("RGB", (1920, 120), "#0a1220")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 1920, 3), fill="#8870ff")
    label_font = ImageFont.truetype(FONT, 23)
    text_font = ImageFont.truetype(FONT, 34)
    label = f"{cue['chapter'] + 1:02}  {cue['title']}  |  실제 포털 원본 · 대기 편집 · 읽기용 화면 정지 포함"
    draw.text((40, 11), label, font=label_font, fill="#b6c3db")
    lines = wrapped(draw, cue["caption"], text_font, 1840)
    if len(lines) > 2:
        raise ValueError("Caption exceeds two readable lines.")
    for index, line in enumerate(lines):
        draw.text((40, 44 + index * 36), line, font=text_font, fill="white")
    image.save(WORK / "captions" / f"{cue['index']:03}.png")


def prepare():
    story, metadata, plan = load_plan()
    for folder in ("audio", "captions", "clips"):
        (WORK / folder).mkdir(parents=True, exist_ok=True)

    def synthesize(cue):
        base = WORK / "audio" / f"{cue['index']:03}"
        text = base.with_suffix(".txt")
        voice = base.with_suffix(".aiff")
        changed = not text.exists() or text.read_text() != cue["text"]
        text.write_text(cue["text"], encoding="utf-8")
        if changed or not voice.exists():
            run(["say", "-v", story["voice"], "-r", str(story["voice_rate"]), "-o", str(voice), "-f", str(text)])
        raw_duration = duration(voice)
        tempo = raw_duration / (cue["duration"] - 0.8)
        cue["raw_voice_seconds"] = raw_duration
        cue["voice_tempo"] = tempo
        return cue

    with ThreadPoolExecutor(max_workers=2) as pool:
        plan["cues"] = list(pool.map(synthesize, plan["cues"]))
    write_json(WORK / "render-plan.json", plan)
    invalid = [
        {"cue": cue["index"], "seconds": cue["duration"], "tempo": round(cue["voice_tempo"], 3)}
        for cue in plan["cues"] if not 0.70 <= cue["voice_tempo"] <= 1.55
    ]
    if invalid:
        raise ValueError(f"Revise narration that is too slow or fast: {invalid}")

    audio_lines, caption_lines, subtitle_lines = [], [], []
    for cue in plan["cues"]:
        voice = WORK / "audio" / f"{cue['index']:03}.aiff"
        wav = WORK / "audio" / f"{cue['index']:03}.wav"
        run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(voice),
            "-af", f"atempo={cue['voice_tempo']:.8f},apad", "-t", str(cue["duration"]),
            "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(wav),
        ])
        audio_lines.append(f"file '{wav}'")
        caption_image(cue)
        caption_lines.extend([
            f"file '{WORK / 'captions' / f'{cue['index']:03}.png'}'",
            f"duration {cue['duration']}",
        ])
        subtitle_lines.extend([
            str(cue["index"] + 1), f"{stamp(cue['start'])} --> {stamp(cue['start'] + cue['duration'])}",
            cue["caption"], "",
        ])
    caption_lines.append(f"file '{WORK / 'captions' / f'{plan['cues'][-1]['index']:03}.png'}'")
    (WORK / "audio-concat.txt").write_text("\n".join(audio_lines) + "\n")
    (WORK / "caption-concat.txt").write_text("\n".join(caption_lines) + "\n")
    (OUT / "captions-ko.srt").write_text("\n".join(subtitle_lines), encoding="utf-8")
    run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
        "-i", str(WORK / "audio-concat.txt"), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,apad",
        "-t", "900", "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(WORK / "narration-ko.wav"),
    ])
    chapter_lines = [
        ";FFMETADATA1", "title=실제 Foundry 포털에서 경험하는 Learning Loop",
        "comment=실제 포털 Playwright headless 원본 편집. 대기 제거 및 읽기용 화면 정지. 한국어 AI 합성 음성.",
    ]
    for chapter in plan["chapters"]:
        chapter_lines.extend([
            "[CHAPTER]", "TIMEBASE=1/1000", f"START={chapter['start'] * 1000}",
            f"END={(chapter['start'] + chapter['duration']) * 1000}",
            f"title={chapter['index'] + 1:02} {chapter['title']}",
        ])
    (OUT / "chapters.ffmetadata").write_text("\n".join(chapter_lines) + "\n", encoding="utf-8")
    (OUT / "chapters.txt").write_text(
        "\n".join(f"{ch['start'] // 60:02}:{ch['start'] % 60:02} {ch['title']}" for ch in plan["chapters"]) + "\n",
        encoding="utf-8",
    )
    write_json(OUT / "edit-decision-list.json", {
        "method": "Cuts, up to 2x playback, and explicitly disclosed reading holds of actual portal footage",
        "target_seconds": 900,
        "waiting_intervals_excluded": True,
        "reconstructed_ui": False,
        "narration": "AI-generated Korean Yuna voice",
        "chapters": plan["chapters"],
        "clips": [
            {**{key: value for key, value in clip.items() if key != "source"}, "source": "raw/" + Path(clip["source"]).name}
            for clip in plan["clips"]
        ],
    })
    write_json(OUT / "source-footage.json", {
        "started": metadata["started"], "method": metadata["method"], "headless": metadata["headless"],
        "sources": [
            {"key": source["key"], "offset_ms": source["offset_ms"],
             "video": "raw/" + Path(source["video"]).name, "sha256": sha256(Path(source["video"]))}
            for source in metadata["pages"]
        ],
        "excluded": "Login was never recorded; initial unmasked welcome, setup failures, and long waits were not selected.",
        "supplemental_ui_evaluation": metadata["supplemental_ui_evaluation"],
    })
    print(f"Prepared {len(plan['cues'])} Korean cues, {len(plan['clips'])} real-footage cuts, 12 chapters, 900 seconds.")
    print(f"Voice tempo range: {min(c['voice_tempo'] for c in plan['cues']):.2f}-{max(c['voice_tempo'] for c in plan['cues']):.2f}")


def render():
    _, _, plan = load_plan()
    (WORK / "clips").mkdir(parents=True, exist_ok=True)

    def render_clip(clip):
        signature = hashlib.sha256(json.dumps(clip, sort_keys=True).encode()).hexdigest()[:12]
        output = WORK / "clips" / f"{clip['index']:03}-{signature}.mp4"
        if output.exists() and abs(duration(output) - clip["seconds"]) < 0.05:
            return output
        filters = [f"setpts=(PTS-STARTPTS)/{clip['speed']:.9f}", f"fps={FPS}"]
        masks = [[1680, 0, 240, 44], *clip.get("redactions", [])]
        if clip["surface"] == "portal.azure.com":
            masks.append([1500, 920, 420, 160])
        for x, y, width, height in masks:
            filters.append(f"drawbox=x={x}:y={y}:w={width}:h={height}:color=black:t=fill")
        if clip["freeze_seconds"]:
            filters.append(f"tpad=stop_mode=clone:stop_duration={clip['freeze_seconds']:.6f}")
        filters.extend(["scale=1706:960:flags=lanczos", "pad=1920:1080:107:0:color=0x0a1220", "setsar=1", "format=yuv420p"])
        run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-ss", f"{clip['source_offset']:.6f}", "-t", f"{clip['to'] - clip['from']:.6f}", "-i", clip["source"],
            "-vf", ",".join(filters), "-frames:v", str(round(clip["seconds"] * FPS)), "-an",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-threads", "2", str(output),
        ])
        if abs(duration(output) - clip["seconds"]) > 0.05:
            raise ValueError(f"Clip {clip['index']} does not match its edit duration.")
        return output

    with ThreadPoolExecutor(max_workers=3) as pool:
        clips = list(pool.map(render_clip, plan["clips"]))
    (WORK / "clip-concat.txt").write_text("".join(f"file '{clip}'\n" for clip in clips))
    run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
        "-i", str(WORK / "clip-concat.txt"), "-c", "copy", str(WORK / "cuts.mp4"),
    ])
    if abs(duration(WORK / "cuts.mp4") - 900) > 0.05:
        raise ValueError("The concatenated actual portal footage is not 900 seconds.")
    output = OUT / "foundry-portal-learning-loop-15min-ko.mp4"
    run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(WORK / "cuts.mp4"), "-i", str(WORK / "narration-ko.wav"),
        "-f", "concat", "-safe", "0", "-i", str(WORK / "caption-concat.txt"),
        "-i", str(OUT / "chapters.ffmetadata"), "-i", str(OUT / "captions-ko.srt"),
        "-filter_complex", "[0:v][2:v]overlay=0:960:eof_action=repeat:format=auto,format=yuv420p[v]",
        "-map", "[v]", "-map", "1:a:0", "-map", "4:0", "-map_metadata", "3",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-threads", "4",
        "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-c:s", "mov_text", "-disposition:s:0", "0",
        "-metadata:s:a:0", "language=kor", "-metadata:s:s:0", "language=kor",
        "-r", str(FPS), "-t", "900", "-movflags", "+faststart", str(output),
    ])
    print(f"Encoded actual portal recording: {output.name} ({output.stat().st_size:,} bytes)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "render"))
    action = parser.parse_args().command
    {"prepare": prepare, "render": render}[action]()
