"""Stop only the verified workshop agent's compute while preserving its versions."""

import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    sys.path[:0] = [str(workspace / "src/agent"), str(workspace / "scripts")]
    from settings import RuntimeConfig, load_settings_env
    from common import RESULTS_DIR, authenticate, azd, binding, load_state, write_json

    load_settings_env()
    authenticate()
    config = RuntimeConfig.from_env()
    binding()
    if load_state().get("agent_owned") != config.agent_name:
        raise ValueError("Do not stop sessions of an unowned agent.")
    before = azd("ai", "agent", "sessions", "list", "--agent-name", config.agent_name)
    if set(before) != {"data"} or not isinstance(before["data"], list):
        raise ValueError("Inspect the session pagination contract before stopping sessions.")
    stopped = []
    for item in before["data"]:
        session = item["agent_session_id"]
        if item["status"] not in {"active", "idle"}:
            raise ValueError(f"Unexpected session state: {item['status']}")
        print(f"Stop owned agent session: {session}", flush=True)
        print(azd("ai", "agent", "sessions", "stop", session, "--agent-name", config.agent_name, json_output=False))
        stopped.append(session)
    after = azd("ai", "agent", "sessions", "list", "--agent-name", config.agent_name)
    if set(after) != {"data"} or not isinstance(after["data"], list):
        raise ValueError("The verification session list is incomplete or paginated.")
    if any(item["status"] not in {"idle", "stopped"} for item in after["data"]):
        raise ValueError("A workshop session is still running or has an unknown state.")
    report = {
        "agent": config.agent_name, "stopped_sessions": stopped,
        "before": before, "after": after, "active_sessions_remaining": 0,
        "agent_versions_models_and_knowledge_preserved": True,
        "reason": "Preserve the actual environment for the pending authenticated portal recording.",
    }
    write_json(RESULTS_DIR / "session-pause.json", report)
    print(json.dumps({
        "agent": config.agent_name, "sessions_stopped": len(stopped),
        "active_sessions_remaining": 0, "agent_versions_models_and_knowledge_preserved": True,
    }, indent=2))


if __name__ == "__main__":
    main()
