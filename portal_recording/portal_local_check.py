import json
import os
import signal
import socket
import subprocess
import time
from pathlib import Path

import httpx
import psutil

root = Path.cwd()
with socket.socket() as sock:
    if sock.connect_ex(("127.0.0.1", 8088)) == 0:
        raise SystemExit("Local test port is occupied; existing processes will not be stopped.")
log_path = root / "portal-local.log"
with log_path.open("w") as log:
    proc = subprocess.Popen(["azd", "ai", "agent", "run", "--no-client"], stdout=log, stderr=subprocess.STDOUT)
    try:
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                raise RuntimeError(log_path.read_text())
            try:
                response = httpx.get("http://127.0.0.1:8088/readiness", timeout=2)
                if response.status_code == 200:
                    break
            except httpx.TransportError:
                time.sleep(1)
        else:
            raise TimeoutError("Local agent was not ready.")
        print("GET /readiness: HTTP 200", flush=True)
        case = json.loads((root / "data/dev.jsonl").read_text().splitlines()[0])
        response = httpx.post("http://127.0.0.1:8088/invocations", json={
            "query": case["query"], "case_id": case["case_id"],
            "model_key": "sol", "run_id": "portal-local",
        }, timeout=180)
        response.raise_for_status()
        data = response.json()
        print(json.dumps({key: data[key] for key in ("answer", "decision", "citations", "model_key", "prompt_version", "trace_id")}, ensure_ascii=False, indent=2))
    finally:
        if proc.poll() is None:
            parent = psutil.Process(proc.pid)
            children = parent.children(recursive=True)
            parent.send_signal(signal.SIGINT)
            _, alive = psutil.wait_procs([parent, *children], timeout=10)
            for process in alive:
                process.terminate()
            _, alive = psutil.wait_procs(alive, timeout=5)
            for process in alive:
                process.kill()
print("PORTAL_LOCAL_CHECK_DONE")
