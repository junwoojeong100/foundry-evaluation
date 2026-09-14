"""Build a guide-ordered video from real, timestamped CLI and portal recordings."""

import argparse
import hashlib
import html
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from video_links import published_video_url

ROOT = Path(__file__).resolve().parents[1]
FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
FPS = 20
PRIVATE_CONSOLE_ACTIONS = {"00-05-account", "00-06-groups"}
CHAPTER_ACTIONS = {
    2: [
        "B01-source", "B02-v1", "B03-select-v1", "B04-local-start", "B05-readiness",
        "B06-local-smoke", "B06-parser-check", "B06-local-smoke-retry",
        "B07-local-stop", "B07-local-stop-confirm", "B08-deploy-v1",
        "B09-agent-access", "B10-remote-smoke", "00-P05-foundry-retry",
        "B-P01-v1-playground", "B-P02-v1-invoke", "B-P03-v1-answer", "B-P04-v1-details",
    ],
    4: [
        "D01-compare", "D02-monitor", "D-P01-traces", "D-P02-trace-search",
        "D-P03-trace-detail", "D-P04-graph", "D-P05-retrieval-span",
        "D-P06-model-span", "D-P07-model-metadata", "D03-review", "D04-feedback",
    ],
    5: [
        "E01-prompt-diff", "E02-select-v2", "E03-deploy-v2", "E04-smoke-v2",
        "E-P01-versions", "E-P02-compare-invoke", "E-P03-compare-results",
        "E05-collect", "E06-evaluate", "E-P04-improved-report", "E07-compare",
    ],
    6: ["F01-collect", "F02-evaluate", "F-P01-holdout-report", "F03-compare"],
    7: [
        "G00-kql", "G01-improved-monitor", "G02-holdout-monitor",
        "G-P01-monitor", "G-P02-monitor-window", "G-P03-tools",
        "G-P04-operational-detail", "G03-verify",
    ],
    8: [
        "H01-cleanup-plan", "H00-sessions", "H00-pause", "H01-final-plan",
        "H02-cleanup", "H03-cleanup-check", "H-P01-agent-absent",
        "H-P02-models-cleaned", "H-P03-knowledge-cleaned", "H-P05-foundation-retained",
        "H-P06-arm-history", "H-P07-arm-error", "H-P08-policy-error", "H-P04-evidence-retained",
    ],
}


def guide_order(action: dict) -> int:
    guide = action["guide"]
    if guide.startswith("00"):
        return 0
    for index, chapter in enumerate("ABCDEFG", 1):
        if guide.startswith(chapter):
            return index
    if guide.startswith("마무리"):
        return 8
    raise ValueError(f"Unknown guide chapter: {guide}")


def presentation_order(action: dict) -> tuple[int, float]:
    chapter = guide_order(action)
    sequence = CHAPTER_ACTIONS.get(chapter)
    if sequence is None:
        return chapter, action["started"]
    if action["id"] not in sequence:
        raise ValueError(f"Place the new action explicitly in guide order: {action['id']}")
    return chapter, sequence.index(action["id"])


def run(args):
    subprocess.run(args, check=True, stdin=subprocess.DEVNULL)


def probe(path: Path) -> dict:
    return json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration,size:stream=codec_type,codec_name,width,height,r_frame_rate",
        "-of", "json", str(path),
    ]))


def fingerprint(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def timecode(seconds: float) -> str:
    seconds = int(seconds)
    return f"{seconds // 3600:02}:{seconds % 3600 // 60:02}:{seconds % 60:02}"


def srt_time(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    return f"{milliseconds // 3600000:02}:{milliseconds % 3600000 // 60000:02}:{milliseconds % 60000 // 1000:02},{milliseconds % 1000:03}"


def intervals(action: dict, page: dict) -> list[tuple[float, float]]:
    start = (action["started"] - page["started"]) / 1000
    end = (action["ended"] - page["started"]) / 1000
    if start < 0 or end <= start:
        raise ValueError(f"Invalid source timestamps for {action['id']}")
    if end - start <= 18:
        return [(start, end)]
    result = (action.get("result_at", action["ended"] - 6000) - page["started"]) / 1000
    tail = max(start + 4, min(result - 1, end - 8))
    return [(start, start + 4), (tail, end)]


def banner(action: dict, destination: Path, edited: bool, draft: bool = False):
    image = Image.new("RGB", (1920, 160), "#101a2b")
    draw = ImageDraw.Draw(image)
    label = ImageFont.truetype(FONT, 23)
    title = ImageFont.truetype(FONT, 34)
    detail = ImageFont.truetype(FONT, 24)
    kind = "실제 CLI / SDK" if action["kind"] == "cli" else "실제 Azure / Foundry Portal"
    label_text = f"{action['guide']}  |  {action['id']}  |  {kind}"
    if draft:
        label_text += "  |  촬영분 초안"
    draw.text((34, 14), label_text, font=label, fill="#86d9ce")
    draw.text((34, 48), action["title"], font=title, fill="white")
    note = action.get("check", "")
    if action["status"] == "failed":
        note = "실패한 시도입니다. 실제 오류를 보존하고 뒤의 재시도와 구분합니다."
    elif action["id"] in PRIVATE_CONSOLE_ACTIONS:
        note = "개인 계정·다른 리소스 목록은 비식별 처리했습니다. 소유권 검사 결과는 다음 절차에서 확인합니다."
    if edited:
        note += "  ·  대기/화면 확인 구간 편집"
    while draw.textlength(note, font=detail) > 1850:
        note = note[:-2]
    draw.text((34, 103), note, font=detail, fill="#cad7ed")
    image.save(destination)


def load_capture(directory: Path, filename: Path | None = None) -> dict:
    state = json.loads((filename or directory / "capture-state.json").read_text())
    annotations = directory / "annotation-overrides.json"
    if annotations.exists():
        overrides = json.loads(annotations.read_text())
        for action in state["actions"]:
            annotation = overrides.get(action["id"], {})
            if set(annotation) - {"title", "check", "guide"}:
                raise ValueError("Annotations cannot change recorded outcomes or timestamps.")
            action.update(annotation)
    if state["running"]:
        raise ValueError("The recorder is still running.")
    for page in state["pages"]:
        if not page.get("video") or not Path(page["video"]).is_file():
            raise ValueError(f"Video is not finalized: {page['key']}")
    for action in state["actions"]:
        if action["status"] == "running":
            raise ValueError(f"An action is not finished: {action['id']}")
    return state


def screenshot_copy(source: Path, destination: Path, action: dict):
    image = Image.open(source).convert("RGB")
    if action["id"] in PRIVATE_CONSOLE_ACTIONS:
        draw = ImageDraw.Draw(image)
        draw.rectangle((36, 240, 1884, 1010), fill="#101a2b")
        font = ImageFont.truetype(FONT, 31)
        draw.text((76, 380), "개인 계정 / 다른 실습의 리소스 목록 비식별", font=font, fill="white")
        draw.text((76, 435), "이 작업의 전용·공유 범위는 소유권 검사 결과에서 확인합니다.", font=font, fill="#b9cce8")
    image.save(destination, "WEBP", quality=90, method=6)


def convert_screenshots(directory: Path):
    state = json.loads((directory / "capture-state.json").read_text())
    folder = ROOT / "docs/assets" / f"live-{state['run']}" / "screenshots"
    count = 0
    for action in state["actions"]:
        for shot in action.get("screenshots", []):
            source = folder / shot["filename"]
            if source.exists():
                screenshot_copy(source, source.with_suffix(".webp"), action)
                count += 1
    print(json.dumps({"converted_real_screenshots": count, "original_pngs_retained_privately": True}))


def build(directory: Path, crf: int, draft: bool = False, capture_file: Path | None = None):
    state = load_capture(directory, capture_file)
    destination = ROOT / "docs/assets" / f"live-{state['run']}"
    destination.mkdir(parents=True, exist_ok=True)
    parts = directory / "edited-parts"
    parts.mkdir(exist_ok=True)
    pages = {page["key"]: page for page in state["pages"]}
    actions = [
        action for action in state["actions"]
        if action.get("scope") != "tooling-only" and action["status"] in {"completed", "service_ready", "failed"}
    ]
    actions.sort(key=presentation_order)
    if not actions:
        raise ValueError("There are no completed recording segments.")
    if not draft:
        successful = {action["id"] for action in actions if action["status"] in {"completed", "service_ready"}}
        required = {
            "A02-prepare-iq", "A03-retrieve", "B08-deploy-v1", "B10-remote-smoke",
            "C01-baseline", "C02-evaluation", "D02-monitor", "D04-feedback",
            "E03-deploy-v2", "E05-collect", "E06-evaluate", "F01-collect", "F02-evaluate",
            "G03-verify", "H02-cleanup", "H03-cleanup-check", "D-P02-trace-search",
            "D-P04-graph", "C-P02-baseline-report", "E-P04-improved-report",
            "F-P01-holdout-report", "G-P01-monitor", "H-P01-agent-absent",
            "H-P02-models-cleaned", "H-P03-knowledge-cleaned", "H-P04-evidence-retained",
        }
        if not required <= successful:
            raise ValueError(f"Required guide procedures are not complete: {sorted(required - successful)}")
    if not draft and any(a["kind"] == "portal" and a["status"] == "interrupted" for a in state["actions"]):
        interrupted = [a for a in state["actions"] if a["status"] == "interrupted"]
        for action in interrupted:
            if not any(a["id"].startswith(action["id"] + "-") and a["status"] == "completed" for a in actions):
                raise ValueError(f"Repeat the interrupted portal procedure before final delivery: {action['id']}")
    edl, timeline, clip_paths = [], [], []
    position = 0.0
    for index, action in enumerate(actions, 1):
        page = pages[action["page_key"]]
        video = Path(page["video"])
        source_duration = float(probe(video)["format"]["duration"])
        spans = intervals(action, page)
        caption = parts / f"{index:03}-caption.png"
        banner(action, caption, len(spans) > 1, draft)
        entry = {
            "id": action["id"], "title": action["title"], "guide": action["guide"],
            "kind": action["kind"], "status": action["status"], "start_seconds": position,
            "screenshots": [],
        }
        for shot in action["screenshots"]:
            source = destination / "screenshots" / shot["filename"]
            if not source.is_file():
                raise ValueError(f"Screenshot missing: {source}")
            target = source.with_suffix(".webp")
            screenshot_copy(source, target, action)
            entry["screenshots"].append({
                "phase": shot["phase"], "file": "screenshots/" + target.name,
                "sha256": fingerprint(target),
            })
        if not any(shot["phase"] == "before" for shot in entry["screenshots"]) or not any(
            shot["phase"] in {"after", "failed"} for shot in entry["screenshots"]
        ):
            raise ValueError(f"Before/after evidence is incomplete: {action['id']}")
        for number, (start, end) in enumerate(spans):
            end = min(end, source_duration)
            if end <= start:
                raise ValueError(f"The video does not cover the recorded action: {action['id']}")
            clip = parts / f"{index:03}-{number}.mp4"
            private = ",drawbox=x=36:y=240:w=1848:h=770:color=0x101a2b:t=fill" if action["id"] in PRIVATE_CONSOLE_ACTIONS else ""
            filters = f"[0:v]fps={FPS}{private},pad=1920:1240:0:0:color=0x101a2b[screen];[screen][1:v]overlay=0:1080:format=auto,format=yuv420p[v]"
            run([
                "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
                "-ss", f"{start:.3f}", "-i", str(video), "-i", str(caption),
                "-filter_complex", filters, "-map", "[v]", "-an", "-t", f"{end - start:.3f}",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", str(crf), "-threads", "2",
                str(clip),
            ])
            duration = float(probe(clip)["format"]["duration"])
            edl.append({
                "action": action["id"], "page_key": page["key"],
                "source_start": start, "source_end": end,
                "output_start": position, "output_duration": duration,
                "waiting_trimmed": len(spans) > 1,
                "privacy_masked": action["id"] in PRIVATE_CONSOLE_ACTIONS,
            })
            position += duration
            clip_paths.append(clip)
        entry["end_seconds"] = position
        timeline.append(entry)
        print(f"{index}/{len(actions)} {action['id']} -> {timecode(position)}", flush=True)
    concat = parts / "concat.txt"
    concat.write_text("".join(f"file '{clip.resolve()}'\n" for clip in clip_paths))
    video = destination / ("foundry-evaluation-guide-order-draft.mp4" if draft else "foundry-evaluation-guide-order.mp4")
    run([
        "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat),
        "-c", "copy", "-movflags", "+faststart", str(video),
    ])
    final = probe(video)
    duration = float(final["format"]["duration"])
    if abs(duration - position) > max(1, len(clip_paths) / FPS):
        raise ValueError("The final video's duration does not agree with its edit list.")
    (destination / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=2) + "\n")
    (destination / "edit-decision-list.json").write_text(json.dumps(edl, ensure_ascii=False, indent=2) + "\n")
    (destination / "chapters.txt").write_text("".join(
        f"{timecode(item['start_seconds'])} {item['id']} {item['title']}\n" for item in timeline
    ))
    (destination / "captions.ko.srt").write_text("\n".join(
        f"{index}\n{srt_time(item['start_seconds'])} --> {srt_time(item['end_seconds'])}\n"
        f"{item['guide']} · {item['title']}\n"
        for index, item in enumerate(timeline, 1)
    ))
    (destination / "captions.ko.vtt").write_text("WEBVTT\n\n" + "\n".join(
        f"{srt_time(item['start_seconds']).replace(',', '.')} --> {srt_time(item['end_seconds']).replace(',', '.')}\n"
        f"{item['guide']} · {item['title']}\n"
        for item in timeline
    ))
    report = {
        "run": state["run"], "headless": True, "actions": len(timeline),
        "draft": draft,
        "video_file": video.name,
        "pending": ["Authenticated Foundry portal walkthrough and final object cleanup"] if draft else [],
        "cli_actions": sum(item["kind"] == "cli" for item in timeline),
        "portal_actions": sum(item["kind"] == "portal" for item in timeline),
        "duration_seconds": duration, "bytes": video.stat().st_size,
        "video_sha256": fingerprint(video), "video": final,
        "source_videos": [
            {"page_key": p["key"], "sha256": fingerprint(Path(p["video"])),
             "duration_seconds": float(probe(Path(p["video"]))["format"]["duration"])}
            for p in state["pages"]
        ],
        "edits": "Real screen recordings ordered by guide chapter; waiting and inspection gaps trimmed; original timestamps retained; caption band added below the original 1920x1080 viewport.",
        "source_images_and_unedited_recordings": "Retained privately; no old workshop responses or footage reused.",
        "excluded_actions": [
            {"id": action["id"], "status": action["status"], "scope": action.get("scope")}
            for action in state["actions"] if action not in actions
        ],
        "annotation_overrides_sha256": fingerprint(directory / "annotation-overrides.json")
        if (directory / "annotation-overrides.json").exists() else None,
        "ordering": "CLI and portal evidence is interleaved in the guide's procedure order; original source timestamps are retained in the edit-decision list.",
    }
    (destination / "media-verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    make_player(destination, timeline, report)
    make_index(destination, timeline, report)
    print(json.dumps({"video": str(video.relative_to(ROOT)), "duration": timecode(duration), "actions": len(timeline)}, ensure_ascii=False))


def make_player(directory: Path, timeline: list, report: dict):
    links = "\n".join(
        f'<button data-time="{item["start_seconds"]}">{timecode(item["start_seconds"])} · '
        f'{html.escape(item["guide"])} · {html.escape(item["title"])}</button>'
        for item in timeline
    )
    warning = "<p><strong>초안: 추가 Foundry 포털 촬영과 최종 객체 정리는 인증 대기 중입니다. 전체 절차 완료 영상이 아닙니다.</strong></p>" if report["draft"] else ""
    hosted_link = "" if report["draft"] else (
        f'<p><a style="color:#9bcdff" href="{html.escape(published_video_url(directory / report["video_file"]), quote=True)}">'
        "GitHub에서 바로 재생</a> · 아래 플레이어는 다운로드한 자료의 로컬 챕터 재생용입니다.</p>"
    )
    page = f"""<!doctype html><html lang="ko"><meta charset="utf-8">
<title>Foundry 실습 순서 통합 영상</title>
<style>body{{margin:28px;background:#111827;color:#eef4ff;font:18px sans-serif}}video{{width:min(100%,1400px);display:block}}button{{display:block;background:#21334d;color:white;border:0;margin:6px 0;padding:10px;text-align:left;cursor:pointer}}p{{max-width:1200px;line-height:1.6}}</style>
<h1>실습 순서 통합본 · CLI + 실제 포털</h1>
{warning}
{hosted_link}
<p>각 절차의 실제 실행 화면입니다. 대기·화면 확인 구간을 줄였으며 로그인 화면과 개인 정보는 제외했습니다.
이 영상의 길이는 Azure 준비·실습의 실제 소요 시간이 아닙니다.</p>
<video controls preload="metadata" src="{report['video_file']}"><track kind="captions" srclang="ko" label="한국어" src="captions.ko.vtt"></video>
<h2>절차 바로가기</h2>{links}
<script>const video=document.querySelector("video");document.querySelectorAll("button").forEach(button=>button.onclick=()=>{{video.currentTime=Number(button.dataset.time);video.play();video.scrollIntoView({{behavior:"smooth"}});}});</script></html>"""
    (directory / "index.html").write_text(page)


def make_index(directory: Path, timeline: list, report: dict):
    relative = directory.relative_to(ROOT / "docs").as_posix()
    video_url = None if report["draft"] else published_video_url(directory / report["video_file"])
    playback = (
        f"로컬 MP4 초안: `{relative}/{report['video_file']}`"
        if report["draft"] else f"[통합 영상 바로 재생]({video_url})"
    )
    lines = [
        "# 절차별 실제 화면과 통합 영상", "",
        "**CLI와 실제 Azure / Foundry 포털을 실습가이드 순서로 연결한 기록입니다.**", "",
        playback + " · "
        "[로컬 챕터 플레이어 사용법](#로컬에서-챕터를-눌러-재생하기) · "
        f"[챕터]({relative}/chapters.txt) · [한국어 자막]({relative}/captions.ko.srt)", "",
        f"영상 {timecode(report['duration_seconds'])} · CLI {report['cli_actions']}개 절차 · "
        f"포털 {report['portal_actions']}개 절차. 실패한 시도도 성공으로 바꾸지 않고 구분했습니다.", "",
        "실습 조작과 녹화는 Playwright headless입니다. 인증만 사용자가 별도 창에서 수행했으며, "
        "로그인·PIN 화면은 녹화하지 않았습니다. CLI는 실제 명령 출력을 보여 주는 로컬 녹화 콘솔이며 "
        "Cloud Shell 화면이 아닙니다.", "",
        "대기·화면 확인 구간은 줄였고, 설명 띠는 원래 화면 아래에 추가했습니다. 원본의 실행 시각과 "
        "편집 위치는 별도로 보존합니다. 영상 길이를 Azure 준비·실습의 실제 소요 시간으로 해석하지 않습니다.", "",
        "사진의 개인 경로·구독·리소스 이름을 그대로 복사하지 말고 **본문의 명령**과 본인 설정을 사용하세요.", "",
        "| 절차 | 화면 | 결과 | 시작 | 실행 전 | 실행 후 |", "|---|---|---|---|---|---|",
    ]
    if video_url:
        lines[6:6] = [
            "GitHub에서는 아래 플레이어의 재생 버튼을 누르거나 위 **바로 재생** 링크를 사용합니다. "
            "영상 원본은 저장소에 보존하고, 재생 링크는 GitHub의 동영상 첨부 주소를 사용합니다.",
            "", video_url, "",
        ]
    if report["draft"]:
        lines[4:4] = [
            "**미완료 범위:** 현재 영상은 실제 CLI learning loop와 Azure Portal 준비 화면을 묶은 초안입니다. "
            "추가 Foundry 포털 촬영과 최종 객체 삭제는 새 인증 창의 로그인 대기 중이며, 전체 완료로 표시하지 않습니다.", "",
        ]
    for item in timeline:
        before = next(shot for shot in item["screenshots"] if shot["phase"] == "before")
        after = next(shot for shot in item["screenshots"] if shot["phase"] in {"after", "failed"})
        state = {"completed": "실행 완료", "service_ready": "서버 실행 유지", "failed": "**실패한 시도**"}[item["status"]]
        start = timecode(item["start_seconds"])
        lines.append(
            f"| `{item['id']}` {item['title']} | {item['kind'].upper()} | {state} | "
            f"{start} | "
            f"[전]({relative}/{before['file']}) | [후]({relative}/{after['file']}) |"
        )
    lines.extend([
        "", "## 로컬에서 챕터를 눌러 재생하기", "",
        "HTML은 GitHub에서 소스로 표시될 수 있습니다. 저장소 루트에서 다음을 실행한 뒤 브라우저로 로컬 주소를 엽니다.", "",
        "```bash",
        f"python3 recording/media_server.py --directory docs/{relative} --port 8899",
        "```", "",
        "`http://127.0.0.1:8899/index.html`에서 챕터를 누르면 해당 시각으로 이동합니다. MP4 파일은 일반 동영상 플레이어로도 열 수 있습니다.", "",
        "GitHub 재생 주소와 원본 파일의 해시는 `docs/video-links.json`에서 관리합니다. "
        "영상을 다시 만들었다면 새 파일을 GitHub 영상 첨부로 게시하고 주소·해시를 갱신해야 합니다. "
        "이전 영상 주소를 새 파일의 재생 링크로 잘못 사용하는 경우 가이드 생성기가 중단합니다.", "",
        "", "## 기록의 범위", "",
        "- 구성 요소의 실행 완료와 모델별 업무 품질·실제 운영 승인은 별개입니다.",
        "- 기존 교육용 dev/holdout을 재실행했습니다. 새로운 독립 검증셋으로 포장하지 않습니다.",
        "- 원본 영상·원본 PNG·환경별 상세 결과는 로컬에 보존하며, 공개용은 비식별 화면과 선별 결과입니다.",
        "- 초기 브라우저 연결 재설정으로 중단된 이동은 완료로 처리하지 않았고, 별도 인증 후 같은 실제 대상을 다시 확인했습니다.",
        "", "[참가자 가이드](../README.md) · [새 환경 준비](environment.ko.md) · [실제 Azure 검증](validation.ko.md)", "",
    ])
    (ROOT / "docs/action-captures.ko.md").write_text("\n".join(lines))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--crf", type=int, default=24)
    parser.add_argument("--screenshots-only", action="store_true")
    parser.add_argument("--draft", action="store_true")
    parser.add_argument("--capture-file", type=Path)
    args = parser.parse_args()
    if not 18 <= args.crf <= 30:
        raise ValueError("Use a readable H.264 CRF between 18 and 30.")
    if args.screenshots_only:
        convert_screenshots(args.run_dir.resolve())
    else:
        build(args.run_dir.resolve(), args.crf, args.draft, args.capture_file)
