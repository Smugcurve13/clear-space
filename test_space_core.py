import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from space_core import build_ai_prompt, classify_path, is_apple_hidden, list_directory, scan_storage, suggest_large_inactive, trash_command


class SpaceCoreTests(unittest.TestCase):
    def test_classifies_games_before_generic_archives(self):
        category, guidance = classify_path(Path("/Users/me/Steam/steamapps/common/Orbit/Game.pak"))

        self.assertEqual(category, "Games")
        self.assertIn("game", guidance.lower())

    def test_detects_only_macos_hidden_flag_as_apple_hidden(self):
        class HiddenStat:
            st_flags = 32768

        self.assertTrue(is_apple_hidden(Path("/Users/me/Library/Hidden"), HiddenStat(), platform="darwin"))
        self.assertFalse(is_apple_hidden(Path("/Users/me/.config"), HiddenStat(), platform="linux"))

    def test_scan_omits_apple_hidden_folders(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            visible = root / "Visible"
            hidden = root / "Private"
            visible.mkdir()
            hidden.mkdir()
            (visible / "keep.bin").write_bytes(b"x" * 20)
            (hidden / "skip.bin").write_bytes(b"x" * 100)

            with patch("space_core.is_apple_hidden", side_effect=lambda path: path == hidden):
                result = scan_storage(root, minimum_item_size=1, item_limit=10)

            self.assertNotIn(hidden, result.directory_sizes)
            self.assertEqual(result.directory_sizes[root], 20)

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

    def test_suggestions_keep_media_as_files_and_group_other_items_as_inactive_folders(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            old_video = root / "old-video.mov"
            archive_folder = root / "Archives"
            archive_folder.mkdir()
            old_archive = archive_folder / "backup.zip"
            old_video.write_bytes(b"x" * 40)
            old_archive.write_bytes(b"x" * 50)
            now = time.time()
            old_time = now - 180 * 86400
            os.utime(old_video, (old_time, old_time))
            os.utime(old_archive, (old_time, old_time))

            result = scan_storage(root, minimum_item_size=1, item_limit=10)
            suggestions = suggest_large_inactive(
                result.chunks,
                result.directory_sizes,
                result.directory_latest_access,
                now=now,
                limit=5,
            )

            self.assertTrue(any(item.entry.path.name == "old-video.mov" and item.entry.kind == "File" for item in suggestions))
            self.assertTrue(any(item.entry.path.name == "Archives" and item.entry.kind == "Folder" for item in suggestions))

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
