import tempfile
import unittest
from pathlib import Path

from iphone_media import available_filename, is_phone_media, media_kind


class IPhoneMediaTests(unittest.TestCase):
    def test_accepts_iphone_photos_and_videos_only(self):
        self.assertTrue(is_phone_media("IMG_0001.HEIC"))
        self.assertTrue(is_phone_media("IMG_0002.MOV"))
        self.assertFalse(is_phone_media("notes.pdf"))
        self.assertEqual(media_kind("IMG_0002.MOV"), "Video")

    def test_keeps_existing_hard_drive_files_safe(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir)
            (destination / "IMG_0001.HEIC").write_bytes(b"kept")

            self.assertEqual(available_filename(destination, "IMG_0001.HEIC"), "IMG_0001 1.HEIC")


if __name__ == "__main__":
    unittest.main()
