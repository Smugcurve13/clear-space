import os
import tempfile
import time
import unittest
from pathlib import Path

from space_core import build_ai_prompt, classify_path, list_directory, scan_storage, suggest_large_inactive, trash_command


class SpaceCoreTests(unittest.TestCase):
    def test_classifies_games_before_generic_archives(self):
        category, guidance = classify_path(Path("/Users/me/Steam/steamapps/common/Orbit/Game.pak"))

        self.assertEqual(category, "Games")
        self.assertIn("game", guidance.lower())

    def test_scan_groups_readable_storage_into_understandable_categories(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "Movies").mkdir()
            (root / "Steam").mkdir()
            (root / "Movies" / "clip.mp4").write_bytes(b"x" * 20)
            (root / "Steam" / "game.pak").write_bytes(b"x" * 30)
            (root / "notes.pdf").write_bytes(b"x" * 5)

            result = scan_storage(root, minimum_item_size=10, item_limit=10)

            self.assertEqual([(chunk.path.name, chunk.category) for chunk in result.chunks], [("game.pak", "Games"), ("clip.mp4", "Photos & videos")])
            self.assertEqual(result.category_sizes["Games"], 30)
            self.assertEqual(result.category_sizes["Photos & videos"], 20)
            self.assertEqual(result.category_sizes["Documents"], 5)

    def test_scan_reports_the_current_folder_and_file_count(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "Library").mkdir()
            (root / "Library" / "cache.bin").write_bytes(b"x" * 12)
            updates = []

            scan_storage(root, minimum_item_size=1, item_limit=10, on_progress=updates.append)

            self.assertTrue(updates)
            self.assertEqual(updates[-1]["files_scanned"], 1)
            self.assertEqual(updates[-1]["bytes_scanned"], 12)
            self.assertEqual(updates[-1]["current_path"], str(root))

    def test_scan_builds_folder_sizes_and_lists_direct_entries(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "Projects").mkdir()
            (root / "Projects" / "build.bin").write_bytes(b"x" * 30)
            (root / "photo.jpg").write_bytes(b"x" * 20)

            result = scan_storage(root, minimum_item_size=1, item_limit=10)
            folders, files = list_directory(root, result.directory_sizes)

            self.assertEqual(result.directory_sizes[root / "Projects"], 30)
            self.assertEqual(folders[0].path.name, "Projects")
            self.assertEqual(files[0].path.name, "photo.jpg")

    def test_suggestions_prioritise_large_files_with_old_access_signals(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            old_file = root / "old-video.mov"
            recent_file = root / "recent-video.mov"
            old_file.write_bytes(b"x" * 40)
            recent_file.write_bytes(b"x" * 100)
            now = time.time()
            os.utime(old_file, (now - 180 * 86400, now - 180 * 86400))

            chunks = scan_storage(root, minimum_item_size=1, item_limit=10).chunks
            suggestions = suggest_large_inactive(chunks, now=now, limit=5)

            self.assertEqual(suggestions[0].entry.path.name, "old-video.mov")
            self.assertGreaterEqual(suggestions[0].days_since_access, 179)

    def test_ai_prompt_only_contains_metadata_and_requests_a_safe_review(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            path = root / "archive.zip"
            path.write_bytes(b"x" * 12)
            chunk = scan_storage(root, minimum_item_size=1, item_limit=1).chunks[0]

            prompt = build_ai_prompt(chunk)

            self.assertIn("No file contents were read", prompt)
            self.assertIn("archive.zip", prompt)
            self.assertIn("before moving it to Trash", prompt)

    def test_trash_command_uses_the_platform_trash_not_rm(self):
        path = Path("/Users/me/Downloads/archive.zip")

        self.assertEqual(trash_command("linux", path), ["gio", "trash", str(path)])
        self.assertEqual(trash_command("darwin", path)[0], "osascript")
        self.assertNotIn("rm", trash_command("darwin", path))


if __name__ == "__main__":
    unittest.main()
