"""Serve the local guide player with byte ranges for reliable chapter seeking."""

import argparse
import re
import shutil
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def byte_range(value: str, size: int) -> tuple[int, int]:
    match = re.fullmatch(r"bytes=(\d*)-(\d*)", value)
    if not match or size <= 0:
        raise ValueError("Unsupported byte range.")
    first, last = match.groups()
    if not first:
        if not last or int(last) <= 0:
            raise ValueError("Invalid suffix range.")
        return max(0, size - int(last)), size - 1
    start = int(first)
    end = min(int(last), size - 1) if last else size - 1
    if start >= size or end < start:
        raise ValueError("Range outside the file.")
    return start, end


class Handler(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    selected_range = None

    def end_headers(self):
        self.send_header("Accept-Ranges", "bytes")
        super().end_headers()

    def send_head(self):
        self.selected_range = None
        value = self.headers.get("Range")
        filename = Path(self.translate_path(self.path))
        if not value or not filename.is_file():
            return super().send_head()
        size = filename.stat().st_size
        try:
            self.selected_range = byte_range(value, size)
        except ValueError:
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{size}")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return None
        source = filename.open("rb")
        start, end = self.selected_range
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(str(filename)))
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()
        return source

    def copyfile(self, source, output):
        if self.selected_range is None:
            shutil.copyfileobj(source, output)
            return
        start, end = self.selected_range
        source.seek(start)
        remaining = end - start + 1
        while remaining:
            block = source.read(min(65536, remaining))
            if not block:
                raise OSError("Media file ended before its declared byte range.")
            output.write(block)
            remaining -= len(block)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8899)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), partial(Handler, directory=str(args.directory.resolve())))
    print(f"Local media player: http://127.0.0.1:{args.port}/index.html", flush=True)
    server.serve_forever()
