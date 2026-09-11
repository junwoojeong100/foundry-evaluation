import json
import time
from urllib.request import urlopen

deadline = time.monotonic() + 7200
last = None
while time.monotonic() < deadline:
    with urlopen("http://127.0.0.1:8877/api/state", timeout=10) as response:
        state = json.load(response)
    failed = [(name, job) for name, job in state["jobs"].items() if job["status"] == "failed"]
    if failed:
        raise SystemExit(json.dumps({"failed": failed}, ensure_ascii=False))
    completed = sum(job["status"] == "completed" for job in state["jobs"].values())
    status = (state["running"], completed)
    if status != last:
        print(json.dumps({"running": status[0], "completed": completed, "total": 29}, ensure_ascii=False), flush=True)
        last = status
    if completed == 29:
        print("All real recording steps completed.", flush=True)
        break
    time.sleep(3)
else:
    raise SystemExit("Recording run exceeded its bounded execution time.")
