import json
import time
from urllib.request import urlopen

deadline = time.monotonic() + 1500
while time.monotonic() < deadline:
    with urlopen("http://127.0.0.1:8877/api/capture?kind=render", timeout=10) as response:
        result = json.load(response)
    if result["status"] == "failed":
        raise SystemExit(json.dumps(result, ensure_ascii=False))
    if result["status"] == "completed":
        print(json.dumps(result, ensure_ascii=False), flush=True)
        break
    time.sleep(10)
else:
    raise SystemExit("Headless render did not finish within its bounded time.")
