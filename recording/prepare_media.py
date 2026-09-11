import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STORY = json.loads((ROOT / "recording/story.json").read_text(encoding="utf-8"))
OUT = ROOT / "artifacts/recording"
AUDIO = OUT / "audio"
AUDIO.mkdir(parents=True, exist_ok=True)


def run(args):
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL)


def duration(path):
    return float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)], text=True
    ).strip())


def stamp(seconds):
    milliseconds = round(seconds * 1000)
    hours, milliseconds = divmod(milliseconds, 3600000)
    minutes, milliseconds = divmod(milliseconds, 60000)
    seconds, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"


def main():
    assert sum(chapter["duration"] for chapter in STORY["chapters"]) == STORY["target_seconds"] == 900
    plan = {"target_seconds": 900, "chapters": [], "cues": [], "narration": "AI-generated Korean voice (Yuna)"}
    subtitle_lines, audio_files = [], []
    cursor = 0.0
    cue_number = 0
    for chapter in STORY["chapters"]:
        raw = []
        for index, cue in enumerate(chapter["cues"]):
            base = AUDIO / f"{chapter['chapter']+1:02}-{index+1:02}"
            text = base.with_suffix(".txt")
            text.write_text(cue["text"], encoding="utf-8")
            voice = base.with_suffix(".aiff")
            if not voice.exists():
                run(["say", "-v", STORY["voice"], "-r", str(STORY["voice_rate"]), "-o", str(voice), "-f", str(text)])
            raw.append((cue, voice, duration(voice)))
        total = sum(item[2] for item in raw)
        padding = 1.0 * len(raw)
        speech_budget = chapter["duration"] - padding
        tempo = total / speech_budget
        if not 0.70 <= tempo <= 1.50:
            raise ValueError(f"Chapter {chapter['chapter']+1}: narration rate {tempo:.2f} is unnatural; revise the script.")
        plan["chapters"].append({"index": chapter["chapter"], "title": chapter["title"], "start": cursor, "duration": chapter["duration"]})
        for index, (cue, voice, raw_duration) in enumerate(raw):
            target = raw_duration / tempo + 1.0
            wav = AUDIO / f"final-{chapter['chapter']+1:02}-{index+1:02}.wav"
            run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(voice),
                "-af", f"atempo={tempo:.8f},apad", "-t", f"{target:.6f}",
                "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(wav),
            ])
            cue_number += 1
            item = {
                **cue, "index": cue_number, "chapter": chapter["chapter"],
                "start": round(cursor, 6), "duration": round(target, 6),
                "audio": str(wav.relative_to(ROOT)),
            }
            plan["cues"].append(item)
            audio_files.append(wav)
            subtitle_lines.extend([
                str(cue_number),
                f"{stamp(cursor)} --> {stamp(cursor + target)}",
                cue["caption"],
                "",
            ])
            cursor += target
        print(f"Chapter {chapter['chapter']+1:02}: {chapter['duration']}s, voice tempo {tempo:.2f}", flush=True)
    if abs(cursor - 900) > 0.01:
        raise ValueError(f"Unexpected timeline duration: {cursor}")
    concat = AUDIO / "concat.txt"
    concat.write_text("".join(f"file '{path.resolve()}'\n" for path in audio_files), encoding="utf-8")
    run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,apad", "-t", "900",
        "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(OUT / "narration-ko.wav"),
    ])
    (ROOT / ".recording/render-plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "captions-ko.srt").write_text("\n".join(subtitle_lines), encoding="utf-8")
    (OUT / "chapters.txt").write_text(
        "\n".join(f"{int(ch['start'])//60:02}:{int(ch['start'])%60:02} {ch['title']}" for ch in plan["chapters"]) + "\n",
        encoding="utf-8",
    )
    print(f"Narration prepared: {duration(OUT / 'narration-ko.wav'):.3f}s", flush=True)


if __name__ == "__main__":
    main()
