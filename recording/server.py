import argparse
import json
import os
import re
import secrets
import signal
import subprocess
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import psutil
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
CONFIG = json.loads((ROOT / ".recording" / "config.json").read_text())
WORKSPACE = Path(CONFIG["workspace"])
RESULTS = WORKSPACE / "src" / "agent" / ".foundry" / "results"
PRIVATE = ROOT / ".recording"
PYTHON = str(WORKSPACE / "src" / "agent" / ".venv" / "bin" / "python")
LOCAL_PORT = CONFIG["local_port"]
PORT = CONFIG["console_port"]
ORIGIN = f"http://127.0.0.1:{PORT}"
TOKEN = secrets.token_urlsafe(32)
VALUES = {key: value for key, value in dotenv_values(WORKSPACE / ".env").items() if value}
REDACTIONS = {
    VALUES.get("AZURE_EXPECTED_USERNAME", ""): "[계정 비식별]",
    str(ROOT.parent.parent): "[사용자 홈]",
    VALUES.get("AZURE_AI_ACCOUNT_NAME", ""): "[Foundry 계정]",
    VALUES.get("AZURE_SEARCH_NAME", ""): "[Search 서비스]",
}
SOURCE_FILES = {
    "agent": "src/agent/policy_agent.py",
    "host": "src/agent/main.py",
    "contract": "src/agent/contracts.py",
    "knowledge": "src/agent/knowledge.py",
    "v1": "src/agent/prompts/v1.txt",
    "v2": "src/agent/prompts/v2.txt",
    "policies": "data/policies.json",
    "dev": "data/dev.jsonl",
    "holdout": "data/holdout.jsonl",
    "monitor": "queries/monitor.kql",
    "dependencies": "src/agent/requirements.txt",
    "evaluation": "scripts/experiments.py",
}
STEPS = [
    ("dependencies", "01", "Python 환경 준비", "고정된 패키지 설치", "python -m venv · pip install"),
    ("models", "02", "네 모델 준비", "실제 model ID / version / quota 확인", "python scripts/workshop.py prepare-models"),
    ("bind", "02", "프로젝트 연결", "기존 프로젝트에 녹화 전용 agent 연결", "python scripts/workshop.py bind"),
    ("preflight", "02", "시작 조건 검증", "계정·모델·관측 연결의 실제 확인", "python scripts/workshop.py preflight"),
    ("calibrate", "02", "Judge calibration", "고정한 정답과 오답을 실제 평가", "python scripts/workshop.py calibrate"),
    ("knowledge", "03", "Foundry IQ 준비", "Index → knowledge source → knowledge base", "python scripts/workshop.py prepare-iq"),
    ("retrieve", "03", "실제 지식 검색", "query planning · references 확인", "python scripts/workshop.py retrieve --query …"),
    ("local-start", "05", "로컬 서버 시작", "같은 Python 코드를 먼저 실행", "azd ai agent run --no-client --port 8878"),
    ("local-smoke", "05", "로컬 실제 호출", "mock 없이 IQ와 모델을 호출", "azd ai agent invoke --local --input-file …"),
    ("local-stop", "05", "로컬 서버 종료", "녹화용 프로세스만 종료", "로컬 서버 종료"),
    ("deploy-v1", "06", "Hosted Agent V1", "소스 ZIP → 관리형 실행", "azd deploy --no-prompt"),
    ("roles", "06", "최소 접근 권한", "agent instance의 Search / 모델 권한", "python scripts/workshop.py grant-agent-access"),
    ("remote-smoke", "06", "원격 실제 호출", "새 hosted agent의 응답 확인", "python scripts/workshop.py smoke --model astra"),
    ("baseline", "07", "네 모델 baseline", "6문항 × 4모델 = 실제 24응답", "collect --split dev --label baseline"),
    ("eval-baseline", "07", "Foundry baseline 평가", "groundedness · relevance · 업무 기준", "evaluate --label baseline"),
    ("monitor-baseline", "08", "실패 trace 확인", "100% telemetry와 operation_Id 연결", "monitor --label baseline"),
    ("feedback", "08", "실패를 회귀 데이터로", "기준 정답은 유지하고 lineage를 보존", "feedback --label baseline --reviewer assistant …"),
    ("prompt-v2", "09", "V2 지침 선택", "인용·적용 날짜·보류 기준을 명시", "python scripts/workshop.py set-prompt v2"),
    ("deploy-v2", "09", "새 버전 배포", "baseline은 보존하고 immutable version 생성", "azd deploy --no-prompt"),
    ("improved", "10", "같은 dev 재실행", "질문·정답·평가기준은 고정", "collect --split dev --label improved"),
    ("eval-improved", "10", "V2 실제 재평가", "좋아진 점과 남은 실패를 함께 확인", "evaluate --label improved"),
    ("monitor-improved", "10", "V2 trace 확인", "24개 실제 trace / 회귀 lineage", "monitor --label improved"),
    ("holdout", "10", "고정된 후보의 holdout", "4문항 × 4모델, prompt 재수정 없음", "collect --split holdout --label holdout"),
    ("eval-holdout", "10", "Holdout 실제 평가", "이 결과를 보고 prompt를 바꾸지 않음", "evaluate --label holdout"),
    ("monitor-holdout", "11", "운영 신호 확인", "HTTP 성공률과 업무 품질을 분리", "monitor --label holdout"),
    ("verify", "11", "전체 증거 확인", "64응답 · 64trace · 실제 Foundry run", "verify --baseline baseline --candidate improved --holdout holdout"),
    ("cleanup-plan", "12", "정리 범위 확인", "기존 공유 자원은 삭제하지 않음", "cleanup --dry-run"),
    ("cleanup", "12", "실습 자원 정리", "이 실행에서 만든 자원만 삭제", "cleanup --confirm"),
    ("check-cleanup", "12", "삭제 재확인", "Azure에서 실제 부재와 기존 자원 보존 확인", "check-cleanup"),
]
INDEX = {step[0]: {"id": step[0], "chapter": step[1], "title": step[2], "description": step[3], "command": step[4]} for step in STEPS}
LOCK = threading.Lock()
STATE = {"running": None, "jobs": {}, "events": [], "started_at": datetime.now(timezone.utc).isoformat()}
if (PRIVATE / "state.json").exists():
    STATE = json.loads((PRIVATE / "state.json").read_text(encoding="utf-8"))
    if STATE.get("running"):
        raise RuntimeError("A previous step was interrupted; inspect its owned process before resuming.")
LOCAL_PROCESS = None


def redact(text: str) -> str:
    for actual, replacement in REDACTIONS.items():
        if actual:
            text = text.replace(actual, replacement)
    text = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", text)
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[계정 비식별]", text)
    text = re.sub(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", "[ID 비식별]", text, flags=re.I)
    text = re.sub(r"(?i)InstrumentationKey=[^;\s\"']+", "InstrumentationKey=[비식별]", text)
    text = re.sub(r"(?i)(Bearer\s+)[A-Za-z0-9_.-]{30,}", r"\1[비식별]", text)
    text = re.sub(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", "[토큰 비식별]", text)
    text = re.sub(r"([?&](?:sig|token|client_secret|code)=)[^&\s]+", r"\1[비식별]", text, flags=re.I)
    return text


def emit(step: str, kind: str, text: str = "", **extra) -> None:
    event = {"time": time.time(), "step": step, "kind": kind, "text": redact(text), **extra}
    with LOCK:
        STATE["events"].append(event)
        with (PRIVATE / "events.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, ensure_ascii=False) + "\n")
    if kind != "output":
        print(json.dumps(event, ensure_ascii=False), flush=True)


def execute(step: str, args: list[str], timeout: int = 1800) -> None:
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    proc = subprocess.Popen(args, cwd=WORKSPACE, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    deadline = time.monotonic() + timeout
    assert proc.stdout is not None
    for line in proc.stdout:
        emit(step, "output", line.rstrip())
        if time.monotonic() > deadline:
            proc.terminate()
            raise TimeoutError(f"{step} timed out.")
    code = proc.wait()
    if code:
        raise RuntimeError(f"{step}: process exited with {code}; actual failure retained.")


def workshop(step: str, *args: str) -> None:
    execute(step, [PYTHON, "-u", "scripts/workshop.py", *args])


def local_output(proc) -> None:
    if proc.stdout:
        for line in proc.stdout:
            emit("local-start", "output", line.rstrip())


def stop_local() -> None:
    global LOCAL_PROCESS
    if LOCAL_PROCESS is None or LOCAL_PROCESS.poll() is not None:
        return
    parent = psutil.Process(LOCAL_PROCESS.pid)
    children = parent.children(recursive=True)
    parent.send_signal(signal.SIGINT)
    _, alive = psutil.wait_procs([parent, *children], timeout=10)
    for process in alive:
        process.terminate()
    _, alive = psutil.wait_procs(alive, timeout=5)
    for process in alive:
        process.kill()
    LOCAL_PROCESS = None


def run_step(step: str) -> None:
    global LOCAL_PROCESS
    try:
        emit(step, "start", INDEX[step]["command"])
        if step == "dependencies":
            execute(step, ["python3.13", "-m", "venv", "src/agent/.venv"])
            execute(step, [PYTHON, "-m", "pip", "install", "--disable-pip-version-check", "-q", "-r", "requirements.lock.txt"])
            execute(step, [PYTHON, "-m", "pip", "check"])
        elif step == "models":
            workshop(step, "prepare-models")
        elif step == "bind":
            workshop(step, "bind")
        elif step == "preflight":
            workshop(step, "preflight")
        elif step == "calibrate":
            workshop(step, "calibrate")
        elif step == "knowledge":
            workshop(step, "prepare-iq")
        elif step == "retrieve":
            workshop(step, "retrieve", "--query", "2026년 9월 국내 출장 숙박비 한도는 얼마인가요?")
        elif step == "local-start":
            import socket
            with socket.socket() as sock:
                if sock.connect_ex(("127.0.0.1", LOCAL_PORT)) == 0:
                    raise RuntimeError("Recording port is already occupied; no existing process will be stopped.")
            env = os.environ.copy()
            env["VIRTUAL_ENV"] = str(WORKSPACE / "src/agent/.venv")
            env["PATH"] = str(WORKSPACE / "src/agent/.venv/bin") + os.pathsep + env["PATH"]
            LOCAL_PROCESS = subprocess.Popen(
                ["azd", "ai", "agent", "run", "--no-client", "--port", str(LOCAL_PORT)],
                cwd=WORKSPACE, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            )
            threading.Thread(target=local_output, args=(LOCAL_PROCESS,), daemon=True).start()
            from urllib.request import urlopen
            from urllib.error import URLError
            deadline = time.monotonic() + 240
            while time.monotonic() < deadline:
                if LOCAL_PROCESS.poll() is not None:
                    raise RuntimeError("Local agent stopped before readiness.")
                try:
                    with urlopen(f"http://127.0.0.1:{LOCAL_PORT}/readiness", timeout=2) as response:
                        if response.status == 200:
                            emit(step, "output", "GET /readiness → 200; 실제 로컬 서버 준비 완료")
                            break
                except URLError:
                    time.sleep(1)
            else:
                raise TimeoutError("Local agent did not become ready.")
        elif step == "local-smoke":
            case = json.loads((WORKSPACE / "data/dev.jsonl").read_text(encoding="utf-8").splitlines()[0])
            request_file = WORKSPACE / "recording-request.json"
            request_file.write_text(json.dumps({"query": case["query"], "model_key": "sol", "case_id": "D01", "run_id": "recording-local"}, ensure_ascii=False), encoding="utf-8")
            execute(step, ["azd", "ai", "agent", "invoke", CONFIG["agent_name"], "--local", "--protocol", "invocations", "--port", str(LOCAL_PORT), "--input-file", str(request_file), "--output", "raw"])
        elif step == "local-stop":
            stop_local()
            emit(step, "output", "이 녹화에서 시작한 로컬 프로세스만 종료했습니다.")
        elif step in {"deploy-v1", "deploy-v2"}:
            execute(step, ["azd", "deploy", "--no-prompt"])
        elif step == "roles":
            workshop(step, "grant-agent-access")
        elif step == "remote-smoke":
            workshop(step, "smoke", "--model", "astra")
        elif step in {"baseline", "improved", "holdout"}:
            workshop(step, "collect", "--split", "holdout" if step == "holdout" else "dev", "--label", step)
        elif step.startswith("eval-"):
            workshop(step, "evaluate", "--label", step.removeprefix("eval-"))
        elif step.startswith("monitor-"):
            workshop(step, "monitor", "--label", step.removeprefix("monitor-"))
        elif step == "feedback":
            rows = [json.loads(line) for line in (RESULTS / "baseline/responses.jsonl").read_text(encoding="utf-8").splitlines()]
            failures = [row for row in rows if not row["business_grade"]["passed"]]
            if not failures:
                raise RuntimeError("No baseline failure was observed; do not invent a failure for the video.")
            chosen = next((row for row in failures if row["case_id"] == "D01"), failures[0])
            workshop(step, "feedback", "--label", "baseline", "--row-id", chosen["row_id"], "--reviewer", "assistant",
                     "--reason", "녹화 검증의 AI 검토: 실제 검색 근거와 trace를 대조하고, 유효 인용과 정책 적용 규칙을 명시한 V2를 같은 기준으로 검증한다. 사람의 운영 승인으로 간주하지 않는다.")
        elif step == "prompt-v2":
            workshop(step, "set-prompt", "v2")
        elif step == "verify":
            workshop(step, "verify", "--baseline", "baseline", "--candidate", "improved", "--holdout", "holdout")
        elif step == "cleanup-plan":
            workshop(step, "cleanup", "--dry-run")
        elif step == "cleanup":
            workshop(step, "cleanup", "--confirm")
        elif step == "check-cleanup":
            workshop(step, "check-cleanup")
        else:
            raise ValueError("Unknown recording step.")
        with LOCK:
            STATE["jobs"][step].update(status="completed", ended=time.time())
        emit(step, "end", "실제 명령 실행 완료", status="completed")
    except (OSError, ValueError, RuntimeError, TimeoutError, subprocess.SubprocessError) as exc:
        with LOCK:
            STATE["jobs"][step].update(status="failed", ended=time.time(), error=redact(str(exc)))
        emit(step, "end", str(exc), status="failed")
    finally:
        with LOCK:
            STATE["running"] = None
            (PRIVATE / "state.json").write_text(json.dumps(STATE, ensure_ascii=False, indent=2), encoding="utf-8")


def live_results() -> dict:
    result = {}
    for label in ("baseline", "improved", "holdout"):
        folder = RESULTS / label
        if not (folder / "manifest.json").exists():
            continue
        manifest = json.loads((folder / "manifest.json").read_text())
        item = {"status": manifest["status"], "version": manifest["agent"]["version"], "run_id": manifest["run_id"]}
        if (folder / "responses.jsonl").exists():
            rows = [json.loads(line) for line in (folder / "responses.jsonl").read_text(encoding="utf-8").splitlines() if line]
            item["rows"] = [{key: row.get(key) for key in ("row_id", "case_id", "model_key", "answer", "decision", "citations", "source_ids", "trace_id", "business_grade", "input_tokens", "output_tokens", "latency_seconds", "regression_source_trace_ids")} for row in rows]
        for name, filename in (("business", "business-summary.json"), ("evaluation", "evaluation.json"), ("telemetry", "telemetry.json")):
            file = folder / filename
            if file.exists():
                data = json.loads(file.read_text(encoding="utf-8"))
                if name == "evaluation":
                    item[name] = {key: data.get(key) for key in ("status", "evaluation_id", "run_id", "expected_rows")}
                elif name == "telemetry":
                    item[name] = {key: data.get(key) for key in ("complete", "expected_trace_count", "observed_trace_count", "operational_summary")}
                else:
                    item[name] = data
        result[label] = item
    return result


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def respond(self, payload, status=200, content_type="application/json; charset=utf-8"):
        data = payload if isinstance(payload, bytes) else json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.headers.get("Host") != f"127.0.0.1:{PORT}":
            self.respond({"error": "Invalid host"}, 403)
            return
        route = urlparse(self.path)
        if route.path == "/":
            self.respond((HERE / "index.html").read_bytes(), content_type="text/html; charset=utf-8")
        elif route.path in {"/app.js", "/style.css"}:
            content_type = "text/javascript; charset=utf-8" if route.path.endswith(".js") else "text/css; charset=utf-8"
            self.respond((HERE / route.path[1:]).read_bytes(), content_type=content_type)
        elif route.path == "/api/config":
            self.respond({"token": TOKEN, "steps": list(INDEX.values()), "namespace": CONFIG["prefix"], "date": "2026-09-11", "mode": "실제 실행"})
        elif route.path == "/api/story":
            self.respond(json.loads((ROOT / ".recording" / "render-plan.json").read_text(encoding="utf-8")))
        elif route.path == "/api/capture":
            kind = parse_qs(route.query).get("kind", ["render"])[0]
            if kind not in {"live", "render"}:
                self.respond({"error": "Invalid capture kind"}, 400)
                return
            path = PRIVATE / f"{kind}-result.json"
            self.respond(json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"status": "pending"})
        elif route.path == "/api/state":
            with LOCK:
                copy = {"running": STATE["running"], "jobs": dict(STATE["jobs"]), "events": list(STATE["events"])}
            copy["results"] = live_results()
            for name in ("verified-evidence", "cleanup-check"):
                file = RESULTS / f"{name}.json"
                if file.exists():
                    copy[name] = json.loads(file.read_text(encoding="utf-8"))
            self.respond(json.loads(redact(json.dumps(copy, ensure_ascii=False))))
        elif route.path == "/api/source":
            key = parse_qs(route.query).get("key", [""])[0]
            if key not in SOURCE_FILES:
                self.respond({"error": "Source is not allowed"}, 404)
                return
            self.respond({"path": SOURCE_FILES[key], "text": redact((WORKSPACE / SOURCE_FILES[key]).read_text(encoding="utf-8"))})
        elif route.path == "/favicon.ico":
            self.respond(b"", 204, "image/x-icon")
        else:
            self.respond({"error": "Not found"}, 404)

    def do_POST(self):
        if (
            self.headers.get("Host") != f"127.0.0.1:{PORT}"
            or self.headers.get("Origin") != ORIGIN
            or not secrets.compare_digest(self.headers.get("X-Recording-Token", ""), TOKEN)
        ):
            self.respond({"error": "Request origin/token rejected"}, 403)
            return
        route = urlparse(self.path).path
        if route not in {"/api/run", "/api/capture"}:
            self.respond({"error": "Unknown mutation route"}, 404)
            return
        size = int(self.headers.get("Content-Length", "0"))
        if not 0 < size <= (131072 if route == "/api/capture" else 4096):
            self.respond({"error": "Invalid request size"}, 400)
            return
        try:
            body = json.loads(self.rfile.read(size))
            if route == "/api/capture":
                kind = body.pop("kind")
                if kind not in {"live", "render"} or body.get("status") not in {"completed", "failed"}:
                    raise ValueError("Invalid capture report.")
                video = Path(body.get("video", "")).resolve()
                if not video.is_relative_to(ROOT / "artifacts/recording/raw") or not video.is_file():
                    raise ValueError("Capture report must point at an actual local video.")
                (PRIVATE / f"{kind}-result.json").write_text(json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")
                self.respond({"saved": kind})
                return
            step = body["step"]
            if step not in INDEX:
                raise ValueError("Unknown step.")
            with LOCK:
                if STATE["running"]:
                    self.respond({"error": "Another real command is running"}, 409)
                    return
                if STATE["jobs"].get(step, {}).get("status") == "completed":
                    self.respond({"error": "Step already completed; use recorded-result view"}, 409)
                    return
                STATE["running"] = step
                STATE["jobs"][step] = {"status": "running", "started": time.time()}
            threading.Thread(target=run_step, args=(step,), daemon=True).start()
            self.respond({"started": step})
        except (KeyError, ValueError, json.JSONDecodeError) as exc:
            self.respond({"error": str(exc)}, 400)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()
    if args.port != PORT:
        raise SystemExit("Use the configured localhost port.")
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Recording console ready at {ORIGIN}", flush=True)
    try:
        server.serve_forever()
    finally:
        stop_local()
        server.server_close()
