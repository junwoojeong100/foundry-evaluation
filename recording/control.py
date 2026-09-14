"""Send a UI operation to the recording owner's private Unix socket."""

import argparse
import http.client
import json
import socket
from pathlib import Path


class UnixConnection(http.client.HTTPConnection):
    def __init__(self, filename: Path, timeout: int = 180):
        super().__init__("localhost", timeout=timeout)
        self.filename = filename

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect(str(self.filename))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--timeout", type=int)
    parser.add_argument("request", help="JSON operation; never include passwords or tokens.")
    args = parser.parse_args()
    request = json.loads(args.request)
    timeout = args.timeout or (900 if request.get("op") == "finish" else 180)
    if not 1 <= timeout <= 1800:
        parser.error("--timeout must be between 1 and 1800 seconds.")
    body = json.dumps(request).encode()
    connection = UnixConnection(args.run_dir / "control.sock", timeout)
    try:
        connection.request("POST", "/control", body=body, headers={"Content-Type": "application/json"})
        response = connection.getresponse()
        data = json.loads(response.read())
        print(json.dumps(data, ensure_ascii=False, indent=2))
        if response.status != 200:
            raise SystemExit(1)
    finally:
        connection.close()


if __name__ == "__main__":
    main()
