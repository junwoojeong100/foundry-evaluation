"""Execute allowlisted workshop commands in a loopback-only recording console."""

import argparse
import json
import os
import re
import secrets
import shlex
import signal
import socket
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent


def redact(text: str) -> str:
    text = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", text)
    text = text.replace(str(ROOT.parent.parent), "[local-home]")
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[account]", text)
    text = re.sub(
        r"\b[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\b",
        "[scope-id]", text, flags=re.I,
    )
    text = re.sub(r"(?i)(InstrumentationKey=)[^;\s\"']+", r"\1[redacted]", text)
    text = re.sub(r"(?i)(Bearer\s+)[A-Za-z0-9_.-]{20,}", r"\1[redacted]", text)
    text = re.sub(r"eyJ[\w-]+\.[\w-]+\.[\w-]+", "[token]", text)
    return re.sub(
        r"(?i)([?&](?:sig|token|client_secret|code)=)[^&\s]+",
        r"\1[redacted]", text,
    )


class Recording:
    def __init__(self, directory: Path):
        self.directory = directory.resolve()
        self.config = json.loads((directory / "config.json").read_text())
        (self.directory / "raw").mkdir(exist_ok=True)
        (ROOT / "docs/assets" / f"live-{self.config['run_id']}" / "screenshots").mkdir(parents=True, exist_ok=True)
        self.port = self.config["port"]
        self.origin = f"http://127.0.0.1:{self.port}"
        self.token = secrets.token_urlsafe(32)
        self.lock = threading.RLock()
        self.processes: dict[str, subprocess.Popen] = {}
        state_path = directory / "console-state.json"
        self.state = json.loads(state_path.read_text()) if state_path.exists() else {
            "running": None, "jobs": {}, "events": [],
        }
        if self.state["running"]:
            raise RuntimeError("An interrupted recording needs explicit inspection before restart.")
        self.state.setdefault("services", {})

    def actions(self) -> dict:
        rows = json.loads((self.directory / "actions.json").read_text())
        if len({row["id"] for row in rows}) != len(rows):
            raise ValueError("Recording action IDs must be unique.")
        return {row["id"]: row for row in rows}

    def public_actions(self) -> list:
        return [
            {
                "id": row["id"], "title": row["title"], "guide": row["guide"],
                "command": redact(shlex.join(row["argv"])),
                "check": row.get("check", ""),
            }
            for row in self.actions().values()
        ]

    def save(self):
        target = self.directory / "console-state.json"
        temporary = target.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.state, ensure_ascii=False, indent=2))
        temporary.replace(target)

    def emit(self, action: str, kind: str, text: str):
        event = {"time": time.time(), "action": action, "kind": kind, "text": redact(text)}
        with self.lock:
            self.state["events"].append(event)
            with (self.directory / "console-events.jsonl").open("a") as stream:
                stream.write(json.dumps(event, ensure_ascii=False) + "\n")
            self.save()

    def start(self, action_id: str):
        action = self.actions()[action_id]
        with self.lock:
            if self.state["running"]:
                raise ValueError("Another command is still running.")
            if action_id in self.state["jobs"]:
                raise ValueError("Preserve the prior attempt; register a new action ID to retry.")
            self.state["running"] = action_id
            self.state["jobs"][action_id] = {
                "status": "running", "started": time.time(),
                "argv": redact(shlex.join(action["argv"])),
            }
            self.save()
        threading.Thread(target=self.execute, args=(action,), daemon=True).start()

    def stream(self, action_id: str, process: subprocess.Popen):
        assert process.stdout is not None
        for line in process.stdout:
            self.emit(action_id, "output", line.rstrip())

    def service_ready(self, action: dict, process: subprocess.Popen):
        address = urlsplit(action["readiness"])
        if address.scheme != "http" or address.hostname != "127.0.0.1" or not address.port:
            raise ValueError("Service readiness must target an explicit loopback port.")
        threading.Thread(target=self.stream, args=(action["id"], process), daemon=True).start()
        deadline = time.monotonic() + 240
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(f"Local service exited before readiness: {process.returncode}")
            try:
                with urlopen(action["readiness"], timeout=2) as response:
                    ready = response.status == 200
            except (URLError, TimeoutError):
                ready = False
            if ready:
                if process.poll() is not None:
                    raise RuntimeError("Local service exited during the readiness check.")
                self.emit(action["id"], "service_ready", "GET /readiness -> HTTP 200 | owned process remains running")
                with self.lock:
                    self.state["jobs"][action["id"]].update(
                        status="service_ready", ended=time.time(), pid=process.pid,
                        completion_criterion="HTTP 200; process is still running",
                    )
                    self.state["services"][action["id"]] = {
                        "pid": process.pid, "readiness": action["readiness"], "status": "running",
                    }
                return
            time.sleep(1)
        raise TimeoutError("Local service did not reach readiness within 240 seconds.")

    def stop_service(self, action: dict):
        target = action["stop_service"]
        process = self.processes.get(target)
        if process is None or process.poll() is not None:
            raise ValueError("The recording-owned service is not running; inspect its prior output.")
        self.emit(action["id"], "control", f"Ctrl+C equivalent: SIGINT -> owned process group {process.pid}")
        os.killpg(process.pid, signal.SIGINT)
        forced = False
        try:
            code = process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            forced = True
            self.emit(action["id"], "output", "SIGINT timed out; terminating only this recording-owned process group.")
            os.killpg(process.pid, signal.SIGTERM)
            try:
                code = process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.emit(action["id"], "output", "SIGTERM timed out; killing only this recording-owned process group.")
                os.killpg(process.pid, signal.SIGKILL)
                code = process.wait(timeout=10)
        address = urlsplit(self.state["services"][target]["readiness"])
        deadline = time.monotonic() + 15
        while True:
            with socket.socket() as sock:
                closed = sock.connect_ex((address.hostname, address.port)) != 0
            if closed:
                break
            if time.monotonic() >= deadline:
                raise RuntimeError("The local port is still occupied. Do not deploy until the owned service is inspected.")
            time.sleep(0.25)
        with self.lock:
            self.state["services"][target].update(status="stopped", ended=time.time())
            self.state["jobs"][action["id"]].update(
                status="completed", ended=time.time(), service_exit_code=code, forced=forced,
            )
        self.emit(action["id"], "completed", f"Owned local service stopped; port is closed; exit code {code}; forced={forced}")

    def verify_service_stopped(self, action: dict):
        target = action["verify_service_stopped"]
        service = self.state["services"].get(target)
        if not service:
            raise ValueError("No owned service record exists.")
        try:
            os.kill(service["pid"], 0)
        except ProcessLookupError:
            self.emit(action["id"], "output", f"Recorded process {service['pid']} no longer exists.")
        else:
            raise ValueError("The recorded PID still exists; inspect it before declaring cleanup complete.")
        address = urlsplit(service["readiness"])
        with socket.socket() as sock:
            if sock.connect_ex((address.hostname, address.port)) == 0:
                raise ValueError("The recorded service port is still accepting connections.")
        with self.lock:
            service.update(status="stopped", ended=time.time())
            self.state["jobs"][action["id"]].update(status="completed", ended=time.time())
        self.emit(action["id"], "completed", "Owned parent PID absent and local service port closed; no additional process was killed.")

    def execute(self, action: dict):
        action_id = action["id"]
        timeout = None
        process = None
        try:
            if action.get("stop_service"):
                self.stop_service(action)
                return
            if action.get("verify_service_stopped"):
                self.verify_service_stopped(action)
                return
            self.emit(action_id, "command", "$ " + shlex.join(action["argv"]))
            env = os.environ.copy()
            env.update(self.config.get("environment", {}))
            env.update(action.get("environment", {}))
            env.update({"PYTHONUNBUFFERED": "1", "NO_COLOR": "1", "TERM": "dumb"})
            cwd = Path(action.get("cwd", self.config["workspace"])).resolve()
            if not cwd.is_relative_to(ROOT):
                raise ValueError("Recording commands must stay inside this repository.")
            if action.get("readiness"):
                address = urlsplit(action["readiness"])
                if address.scheme != "http" or address.hostname != "127.0.0.1" or not address.port:
                    raise ValueError("Use an explicit loopback service port.")
                with socket.socket() as sock:
                    if sock.connect_ex((address.hostname, address.port)) == 0:
                        raise ValueError("The local port is already occupied; no existing process will be stopped.")
            process = subprocess.Popen(
                action["argv"], cwd=cwd, env=env, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, bufsize=1, start_new_session=True,
            )
            self.processes[action_id] = process
            if action.get("readiness"):
                with self.lock:
                    self.state["services"][action_id] = {
                        "pid": process.pid, "readiness": action["readiness"], "status": "starting",
                    }
            timed_out = threading.Event()

            def expire():
                timed_out.set()
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGTERM)

            timeout = threading.Timer(action.get("timeout", 1800), expire)
            timeout.start()
            if action.get("readiness"):
                self.service_ready(action, process)
                return
            self.stream(action_id, process)
            code = process.wait()
            if timed_out.is_set():
                raise TimeoutError("Command timed out; this attempt remains a failure.")
            if code:
                raise RuntimeError(f"Command exited with {code}; output and attempt preserved.")
            self.emit(action_id, "completed", "Exit code 0 | actual command completed")
            with self.lock:
                self.state["jobs"][action_id].update(
                    status="completed", exit_code=code, ended=time.time(),
                )
        except (OSError, ValueError, RuntimeError, TimeoutError, subprocess.SubprocessError) as exc:
            if action.get("readiness") and process is not None and process.poll() is None:
                self.emit(action_id, "output", "Stopping the recording-owned process after startup failure.")
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=10)
            self.emit(action_id, "failed", str(exc))
            with self.lock:
                if action_id in self.state["services"]:
                    self.state["services"][action_id]["status"] = "failed"
                self.state["jobs"][action_id].update(
                    status="failed", error=redact(str(exc)), ended=time.time(),
                )
        finally:
            if timeout:
                timeout.cancel()
            with self.lock:
                self.state["running"] = None
                self.save()

    def close(self):
        for process in self.processes.values():
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)


def handler(recording: Recording):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            return

        def respond(self, body, status=200, content_type="application/json"):
            data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type + "; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(data)

        def valid_host(self):
            return self.headers.get("Host") == f"127.0.0.1:{recording.port}"

        def do_GET(self):
            if not self.valid_host():
                self.respond({"error": "Invalid host"}, 403)
                return
            route = urlsplit(self.path).path
            if route == "/":
                self.respond((HERE / "action_console.html").read_bytes(), content_type="text/html")
            elif route == "/api/config":
                self.respond({
                    "token": recording.token, "actions": recording.public_actions(),
                    "run": recording.config["run_id"],
                    "paths": {
                        "repository": str(ROOT), "private": str(recording.directory),
                        "screenshots": str(ROOT / "docs/assets" / f"live-{recording.config['run_id']}" / "screenshots"),
                    },
                })
            elif route == "/api/state":
                with recording.lock:
                    self.respond(recording.state)
            elif route == "/favicon.ico":
                self.respond(b"", 204)
            else:
                self.respond({"error": "Not found"}, 404)

        def do_POST(self):
            if (
                not self.valid_host()
                or self.headers.get("Origin") != recording.origin
                or not secrets.compare_digest(
                    self.headers.get("X-Recording-Token", ""), recording.token,
                )
            ):
                self.respond({"error": "Origin/token rejected"}, 403)
                return
            route = urlsplit(self.path).path
            if route not in {"/api/run", "/api/capture"}:
                self.respond({"error": "Not found"}, 404)
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= (2_000_000 if route == "/api/capture" else 4096):
                    raise ValueError("Invalid request size.")
                body = json.loads(self.rfile.read(size))
                if route == "/api/capture":
                    if body.get("run") != recording.config["run_id"] or not isinstance(body.get("actions"), list):
                        raise ValueError("Capture report belongs to a different recording.")
                    with recording.lock:
                        target = recording.directory / "capture-state.json"
                        temporary = target.with_suffix(".tmp")
                        temporary.write_text(json.dumps(body, ensure_ascii=False, indent=2) + "\n")
                        os.chmod(temporary, 0o600)
                        temporary.replace(target)
                    self.respond({"saved": body["run"]})
                    return
                recording.start(body["id"])
                self.respond({"started": body["id"]})
            except (ValueError, KeyError, json.JSONDecodeError) as exc:
                self.respond({"error": str(exc)}, 400)

    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True, type=Path)
    args = parser.parse_args()
    recording = Recording(args.run_dir)
    server = ThreadingHTTPServer(("127.0.0.1", recording.port), handler(recording))
    print(f"Actual CLI recording console: {recording.origin}", flush=True)
    try:
        server.serve_forever()
    finally:
        recording.close()
        server.server_close()


if __name__ == "__main__":
    main()
