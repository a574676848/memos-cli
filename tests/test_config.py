import os
import stat
import tempfile
import unittest
from pathlib import Path

from memos_cli.config import Config, Context, active_context, load_config, parse_config, save_config


class ConfigTests(unittest.TestCase):
    def test_parse_and_active_context(self):
        cfg = parse_config(
            '''
version: "1"
default_context: production
contexts:
  production:
    server: "http://127.0.0.1:5230"
    token: "secret"
    username: "root"
'''
        )
        ctx = active_context(cfg)
        self.assertEqual(ctx.server, "http://127.0.0.1:5230")
        self.assertEqual(ctx.token, "secret")
        self.assertEqual(ctx.username, "root")

    def test_save_uses_0600(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "config.yaml"
            save_config(Config(contexts={"default": Context("http://x", "tok", "root")}), path)
            mode = stat.S_IMODE(path.stat().st_mode)
            self.assertEqual(mode, 0o600)
            cfg, loaded_path = load_config(str(path))
            self.assertEqual(loaded_path, path)
            self.assertEqual(cfg.contexts["default"].token, "tok")

    def test_env_override(self):
        cfg = Config(contexts={"default": Context("http://x", "tok", "root")})
        old_server = os.environ.get("MEMOS_SERVER")
        old_token = os.environ.get("MEMOS_TOKEN")
        os.environ["MEMOS_SERVER"] = "http://override"
        os.environ["MEMOS_TOKEN"] = "override-token"
        try:
            ctx = active_context(cfg)
        finally:
            if old_server is None:
                os.environ.pop("MEMOS_SERVER", None)
            else:
                os.environ["MEMOS_SERVER"] = old_server
            if old_token is None:
                os.environ.pop("MEMOS_TOKEN", None)
            else:
                os.environ["MEMOS_TOKEN"] = old_token
        self.assertEqual(ctx.server, "http://override")
        self.assertEqual(ctx.token, "override-token")


if __name__ == "__main__":
    unittest.main()

