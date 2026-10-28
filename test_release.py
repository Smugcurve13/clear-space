import unittest

from build_release import asset_name
from release_notes import render_markdown
from version import __version__


class ReleaseMetadataTests(unittest.TestCase):
    def test_alpha_version_and_notes_match(self):
        self.assertEqual(__version__, "0.0.1-alpha.1")
        rendered = render_markdown()
        self.assertIn(f"Clear Space v{__version__}", rendered)
        self.assertIn("## New", rendered)

    def test_asset_names_are_platform_specific(self):
        self.assertEqual(asset_name("Darwin", "arm64"), "Clear-Space-v0.0.1-alpha.1-macos-arm64.zip")
        self.assertEqual(asset_name("Linux", "x86_64"), "Clear-Space-v0.0.1-alpha.1-linux-x86_64.tar.gz")


if __name__ == "__main__":
    unittest.main()
