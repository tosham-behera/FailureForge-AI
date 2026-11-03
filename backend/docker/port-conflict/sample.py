"""Fixed, offline fixture. No input, external networking, or shell commands."""
import errno
import json
import signal
import socket
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"FailureForge sample healthy"
        self.send_response(200)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(fmt % args, flush=True)


def main():
    signal.alarm(10)
    with socket.socket() as blocker:
        blocker.bind(("127.0.0.1", 4000))
        blocker.listen(1)
        try:
            unexpected = HTTPServer(("127.0.0.1", 4000), Handler)
        except OSError as exc:
            if exc.errno != errno.EADDRINUSE:
                raise
            print(json.dumps({"phase": "before", "port": 4000,
                              "error": "EADDRINUSE", "message": str(exc)}))
        else:
            unexpected.server_close()
            raise RuntimeError("Expected port conflict was not reproduced")
        with HTTPServer(("127.0.0.1", 4001), Handler) as server:
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                connection = HTTPConnection("127.0.0.1", 4001, timeout=2)
                connection.request("GET", "/")
                response = connection.getresponse()
                body = response.read().decode()
                connection.close()
                if response.status != 200 or body != "FailureForge sample healthy":
                    raise RuntimeError("Health probe failed")
                print(json.dumps({"phase": "after", "port": 4001,
                                  "http_status": response.status, "body": body}))
            finally:
                server.shutdown()
                thread.join(timeout=2)


if __name__ == "__main__":
    main()
