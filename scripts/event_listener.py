"""Minimal TMF630 event listener for trying out the hub (used by the Bruno demo, tests/TMFC008/demo/5 events).

    python scripts/event_listener.py [--port 9099]

Accepts the notifications the API posts to <callback>/listener/<eventType> (any POST path) and keeps them:

    GET    /events    -> [{"path", "eventType", "receivedAt", "event"}, ...] in order of arrival
    DELETE /events    -> forget them

Register a hub with the callback http://<this host>:<port>/<name>; its events arrive under the path /<name>/listener/...
(the API must be able to reach the host: from a container use host.docker.internal).
"""
import argparse
import json
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

received = []
lock = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    def _reply(self, status, body=None):
        payload = b"" if body is None else json.dumps(body).encode()
        self.send_response(status)
        if payload:
            self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        try:
            event = json.loads(raw)
        except ValueError:
            return self._reply(400, {"error": "not JSON"})
        with lock:
            received.append({
                "path": self.path,
                "eventType": event.get("eventType") if isinstance(event, dict) else None,
                "receivedAt": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                "event": event,
            })
        print(f"{self.path}  {received[-1]['eventType']}", flush=True)
        self._reply(201)

    def do_GET(self):
        if self.path.split("?")[0] != "/events":
            return self._reply(404, {"error": "GET /events"})
        with lock:
            self._reply(200, list(received))

    def do_DELETE(self):
        if self.path.split("?")[0] != "/events":
            return self._reply(404, {"error": "DELETE /events"})
        with lock:
            received.clear()
        self._reply(204)

    def log_message(self, *args):
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, default=9099)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("0.0.0.0", args.port), Handler)
    print(f"Event listener on port {args.port} (GET/DELETE /events)", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
