#!/usr/bin/env python3
"""Stage stub for k6 smoke (issue #104): canned loan decisions + dup-key memory.
Run: python engine/load/stub.py 8099. No deps, stdlib only.
"""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import sys

SEEN = {}

class H(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0)) or 0))
        key = body.get("client_key", "")
        if key in SEEN:
            out = SEEN[key]
        else:
            out = {"decision": "REVIEW" if body.get("requested_amount", 0) > 500000000 else "APPROVE",
                   "txn_ref": f"TXN-{abs(hash(key)) % 10**8:08d}"}
            SEEN[key] = out
        data = json.dumps(out).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    HTTPServer(("127.0.0.1", int(sys.argv[1]) if len(sys.argv) > 1 else 8099), H).serve_forever()
