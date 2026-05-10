import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from memos_cli.client import MemosClient, normalize_resource_name
from memos_cli.config import Context
from memos_cli.errors import APIError


class Handler(BaseHTTPRequestHandler):
    seen = {}

    def do_GET(self):
        Handler.seen["auth"] = self.headers.get("Authorization")
        Handler.seen["path"] = self.path
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}).encode())

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        Handler.seen["body"] = json.loads(self.rfile.read(length).decode())
        self.send_response(400)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"message": "bad request"}).encode())

    def log_message(self, *_args):
        pass


class ClientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def test_request_auth_and_query(self):
        client = MemosClient(Context(self.base, "tok", "root"))
        data = client.request("GET", "/api/v1/memos", params={"pageSize": 2, "empty": ""})
        self.assertEqual(data, {"ok": True})
        self.assertEqual(Handler.seen["auth"], "Bearer tok")
        self.assertEqual(Handler.seen["path"], "/api/v1/memos?pageSize=2")

    def test_api_error_message(self):
        client = MemosClient(Context(self.base, "tok", "root"))
        with self.assertRaises(APIError) as ctx:
            client.request("POST", "/bad", body={"x": 1})
        self.assertEqual(ctx.exception.status, 400)
        self.assertIn("bad request", str(ctx.exception))
        self.assertEqual(Handler.seen["body"], {"x": 1})

    def test_normalize_resource_name(self):
        self.assertEqual(normalize_resource_name("abc", "memos"), "memos/abc")
        self.assertEqual(normalize_resource_name("memos/abc", "memos"), "memos/abc")


if __name__ == "__main__":
    unittest.main()

