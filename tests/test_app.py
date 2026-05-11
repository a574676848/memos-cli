import json
import tempfile
import threading
import unittest
from contextlib import redirect_stderr, redirect_stdout
from http.server import BaseHTTPRequestHandler, HTTPServer
from io import StringIO
from pathlib import Path

from memos_cli.app import main


def run_cli(argv):
    stdout = StringIO()
    stderr = StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = main(argv)
    return code, stdout.getvalue(), stderr.getvalue()


class Handler(BaseHTTPRequestHandler):
    seen = []

    def _json(self, payload, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())

    def do_GET(self):
        Handler.seen.append(("GET", self.path, None))
        if self.path.startswith("/api/v1/auth/me"):
            self._json({"user": {"name": "users/root", "username": "root"}})
        else:
            self._json({"memos": [{"name": "memos/1", "content": "hello"}]})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length).decode() or "{}")
        Handler.seen.append(("POST", self.path, body))
        self._json({"name": "memos/2", **body})

    def do_PATCH(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length).decode() or "{}")
        Handler.seen.append(("PATCH", self.path, body))
        self._json(body)

    def do_DELETE(self):
        Handler.seen.append(("DELETE", self.path, None))
        self._json({})

    def log_message(self, *_args):
        pass


class AppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def setUp(self):
        Handler.seen.clear()
        self.tmp = tempfile.TemporaryDirectory()
        self.config = str(Path(self.tmp.name) / "config.yaml")
        code, _, _ = run_cli(["-j", "--config", self.config, "config", "init", "--server", self.base, "--token", "tok"])
        self.assertEqual(code, 0)

    def tearDown(self):
        self.tmp.cleanup()

    def test_auth_status(self):
        code, _, _ = run_cli(["--config", self.config, "auth", "status"])
        self.assertEqual(code, 0)
        self.assertEqual(Handler.seen[-1][0], "GET")
        self.assertTrue(Handler.seen[-1][1].startswith("/api/v1/auth/me"))

    def test_memo_create_and_update(self):
        code, _, _ = run_cli(["--config", self.config, "memo", "create", "hello"])
        self.assertEqual(code, 0)
        self.assertEqual(Handler.seen[-1], ("POST", "/api/v1/memos", {"content": "hello", "visibility": "PRIVATE"}))

        code, _, _ = run_cli(["--config", self.config, "memo", "update", "1", "--content", "changed"])
        self.assertEqual(code, 0)
        method, path, body = Handler.seen[-1]
        self.assertEqual(method, "PATCH")
        self.assertEqual(path, "/api/v1/memos/1?updateMask=content")
        self.assertEqual(body["content"], "changed")

    def test_raw_api(self):
        code, _, _ = run_cli(["--config", self.config, "api", "GET", "/api/v1/memos", "--param", "pageSize=1"])
        self.assertEqual(code, 0)
        self.assertEqual(Handler.seen[-1][1], "/api/v1/memos?pageSize=1")

    def test_upgrade_dry_run(self):
        code, stdout, _ = run_cli(["-j", "upgrade", "--manager", "pip", "--source", ".", "--dry-run"])
        self.assertEqual(code, 0)
        payload = json.loads(stdout)
        self.assertEqual(payload["manager"], "pip")
        self.assertEqual(payload["command"][-2:], ["--upgrade", "."])
        self.assertTrue(payload["dry_run"])

    def test_upgrade_default_source_uses_github(self):
        code, stdout, _ = run_cli(["-j", "upgrade", "--manager", "pip", "--dry-run"])
        self.assertEqual(code, 0)
        payload = json.loads(stdout)
        self.assertEqual(payload["command"][-1], "git+https://github.com/a574676848/memos-cli.git")


if __name__ == "__main__":
    unittest.main()
