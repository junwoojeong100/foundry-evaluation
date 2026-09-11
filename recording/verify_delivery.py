import hashlib
import json
import re
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / ".recording"
OUT = ROOT / "artifacts/recording"


def main():
    config = json.loads((PRIVATE / "config.json").read_text())
    workspace = Path(config["workspace"])
    results = workspace / "src/agent/.foundry/results"
    state = json.loads((PRIVATE / "state.json").read_text(encoding="utf-8"))
    if len(state["jobs"]) != 29 or any(job["status"] != "completed" for job in state["jobs"].values()):
        raise ValueError("Not all real workshop commands completed.")
    evidence = json.loads((results / "verified-evidence.json").read_text())
    cleanup = json.loads((results / "cleanup-check.json").read_text())
    if evidence["primary_model_outputs"] != 64 or evidence["distinct_verified_traces"] != 64:
        raise ValueError("The recording run does not contain the complete verified experiment.")
    if not cleanup["temporary_hosted_agent_absent"] or cleanup["temporary_model_deployments_absent"] != 4:
        raise ValueError("Recording resources were not fully cleaned up.")
    events_text = (PRIVATE / "events.jsonl").read_text(encoding="utf-8")
    username = dotenv_values(workspace / ".env")["AZURE_EXPECTED_USERNAME"]
    if username in events_text or re.search(r"Bearer eyJ[\w-]+\.", events_text):
        raise ValueError("A sensitive account/token value remains in visible recording logs.")
    if re.search(r"InstrumentationKey=[0-9a-f-]{36}", events_text, re.I):
        raise ValueError("An instrumentation key remains in visible recording logs.")
    video = json.loads((OUT / "video-verification.json").read_text())
    if abs(video["duration_seconds"] - 900) > .2 or not video["full_decode_checked"]:
        raise ValueError("Video delivery checks are incomplete.")
    film = OUT / video["video"]
    summary = {
        "video": str(film.relative_to(ROOT)),
        "duration_seconds": video["duration_seconds"],
        "resolution": "1920x1080",
        "chapters": video["chapters"],
        "headless_browser": "Chromium via Playwright",
        "source": "fresh 2026-09-11 Azure execution in an isolated namespace",
        "real_commands_completed": len(state["jobs"]),
        "verified_model_outputs": evidence["primary_model_outputs"],
        "verified_traces": evidence["distinct_verified_traces"],
        "candidate_quality_gates": evidence["candidate_quality_gates"],
        "production_release_approved": False,
        "temporary_cloud_resources_cleaned": True,
        "visible_log_privacy_checks_passed": True,
        "sha256": hashlib.sha256(film.read_bytes()).hexdigest(),
        "presentation_disclosure": "Local browser console showing real execution records; not a recording of the Foundry portal UI.",
        "audio_disclosure": "Korean AI-generated narration; on-screen text and SRT are key-point captions.",
    }
    (OUT / "delivery-verification.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
