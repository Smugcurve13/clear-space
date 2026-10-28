import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from desktop_app import DesktopApi, main


class DesktopApiTests(unittest.TestCase):
    def test_scan_returns_root_puzzle_folders_and_browsable_file_lists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "Steam").mkdir()
            target = root / "Steam" / "orbit.pak"
            target.write_bytes(b"x" * 30)
            api = DesktopApi(minimum_item_size=10)

            payload = api.scan(str(root))
            detail = api.browse(str(root / "Steam"))

            self.assertEqual(payload["folders"][0]["name"], "Steam")
            self.assertEqual(payload["folders"][0]["display_size"], "30 B")
            self.assertEqual(detail["files"][0]["kind"], "File")
            self.assertEqual(detail["files"][0]["name"], "orbit.pak")

    def test_default_scan_scope_is_the_current_user_home(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "movie.mp4").write_bytes(b"x" * 30)
            api = DesktopApi(minimum_item_size=10)

            with patch("desktop_app.default_scan_root", return_value=root):
                payload = api.scan()

            self.assertEqual(payload["root"], str(root))

    def test_ai_prompt_is_only_available_for_a_scanned_item(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "archive.zip"
            target.write_bytes(b"x" * 30)
            api = DesktopApi(minimum_item_size=10)
            api.scan(str(root))

            prompt = api.ai_prompt(str(target))

            self.assertIn("No file contents were read", prompt)
            with self.assertRaises(ValueError):
                api.ai_prompt("/not-a-scanned-item")

    def test_main_passes_a_string_url_to_pywebview(self):
        with patch("desktop_app.webview.create_window") as create_window, patch("desktop_app.webview.start"):
            main()

        self.assertIsInstance(create_window.call_args.args[1], str)
        self.assertTrue(create_window.call_args.args[1].endswith("web/index.html"))


if __name__ == "__main__":
    unittest.main()
