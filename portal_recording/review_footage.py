import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/foundry-portal-recording"
REVIEW = OUT / "review"


def main():
    metadata = json.loads((OUT / "capture-metadata.json").read_text())
    pages = {item["key"]: item for item in metadata["pages"]}
    REVIEW.mkdir(exist_ok=True)
    tasks = []
    for segment in metadata["segments"]:
        if segment.get("exclude_reason"):
            continue
        start, end = segment["start_ms"] / 1000, segment["end_ms"] / 1000
        duration = end - start
        points = [start + min(1, duration / 4), (start + end) / 2, end - min(0.4, duration / 4)]
        for index, point in enumerate(points):
            tasks.append({
                "label": f"S{segment['index']:02}-{index} {point:.1f}s",
                "time": point,
                "page": segment.get("page_key", "main"),
                "file": REVIEW / f"s{segment['index']:02}-{index}.jpg",
            })
    for point in (3300, 3350, 4350, 4750, 4900, 5100, 5500, 6050, 6530, 6610, 7080, 7150):
        tasks.append({"label": f"Cloud result {point}s", "time": point, "page": "main", "file": REVIEW / f"cloud-{point}.jpg"})

    def extract(task):
        source = pages[task["page"]]
        timestamp = task["time"] - source["offset_ms"] / 1000
        if not task["file"].exists():
            subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-ss", f"{timestamp:.3f}", "-i", source["video"],
                "-frames:v", "1", "-vf", "scale=480:270", "-threads", "1",
                str(task["file"]),
            ], check=True)
        if not task["file"].exists():
            raise ValueError(f"No source frame for {task['label']}")
        return task

    with ThreadPoolExecutor(max_workers=6) as pool:
        frames = list(pool.map(extract, tasks))
    font = ImageFont.load_default(size=18)
    for batch in range(0, len(frames), 20):
        sheet = Image.new("RGB", (1920, 1500), "#20252b")
        draw = ImageDraw.Draw(sheet)
        for index, item in enumerate(frames[batch:batch + 20]):
            x, y = (index % 4) * 480, (index // 4) * 300
            with Image.open(item["file"]) as image:
                sheet.paste(image, (x, y + 30))
            draw.text((x + 6, y + 5), item["label"], font=font, fill="white")
        sheet.save(REVIEW / f"sheet-{batch // 20 + 1:02}.jpg", quality=90)
    print(f"Reviewed-source contact sheets: {len(frames)} frames in {(len(frames) + 19) // 20} sheets")


if __name__ == "__main__":
    main()
