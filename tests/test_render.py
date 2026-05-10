import unittest

from memos_cli.render import render


class RenderTests(unittest.TestCase):
    def test_json_render(self):
        self.assertIn('"a": 1', render({"a": 1}, "json"))

    def test_table_render_list_response(self):
        text = render({"memos": [{"name": "memos/1", "content": "hello", "visibility": "PRIVATE"}]}, "table")
        self.assertIn("name", text)
        self.assertIn("memos/1", text)
        self.assertIn("hello", text)

    def test_csv_render(self):
        text = render({"users": [{"name": "users/root", "username": "root"}]}, "csv")
        self.assertIn("name", text.splitlines()[0])
        self.assertIn("users/root", text)


if __name__ == "__main__":
    unittest.main()

