import shutil
import subprocess
import sys
from pathlib import Path

import webview

from space_core import build_ai_prompt, format_bytes, scan_storage, trash_command

MINIMUM_ITEM_SIZE = 100 * 1024 * 1024
WEB_ROOT = Path(__file__).parent / "web"


class DesktopApi:
    def __init__(self, minimum_item_size=MINIMUM_ITEM_SIZE):
        self.minimum_item_size = minimum_item_size
        self.root = Path("/")
        self.window = None
        self.chunks = {}

    def choose_folder(self):
        if self.window is None:
            return None
        selected = self.window.create_file_dialog(webview.FileDialog.FOLDER, directory=str(self.root))
        return str(selected[0]) if selected else None

    def scan(self, root=None):
        root_path = Path(root or self.root).expanduser()
        if not root_path.is_dir():
            raise ValueError("Choose a readable folder.")
        self.root = root_path.resolve()
        result = scan_storage(self.root, self.minimum_item_size, 100)
        self.chunks = {str(chunk.path): chunk for chunk in result.chunks}
        categories = [
            {"name": name, "size": size, "display_size": format_bytes(size)}
            for name, size in sorted(result.category_sizes.items(), key=lambda item: item[1], reverse=True)
        ]
        chunks = [
            {
                "path": str(chunk.path),
                "name": chunk.path.name,
                "parent": str(chunk.path.parent),
                "kind": chunk.kind,
                "category": chunk.category,
                "size": chunk.size,
                "display_size": format_bytes(chunk.size),
                "guidance": chunk.guidance,
            }
            for chunk in result.chunks
        ]
        return {
            "root": str(self.root),
            "free_space": format_bytes(shutil.disk_usage(self.root).free),
            "categories": categories,
            "chunks": chunks,
        }

    def ai_prompt(self, path):
        return build_ai_prompt(self._chunk(path))

    def reveal(self, path):
        target = self._chunk(path).path
        command = ["open", "-R", str(target)] if sys.platform == "darwin" else ["xdg-open", str(target.parent)]
        subprocess.run(command, check=True)
        return True

    def move_to_trash(self, path):
        chunk = self._chunk(path)
        if self.window is None:
            raise RuntimeError("The desktop window is not ready.")
        approved = self.window.create_confirmation_dialog(
            "Move to Trash?",
            f"Move this {chunk.kind.lower()} to Trash?\n\n{chunk.path.name}\n{format_bytes(chunk.size)}\n\nIt will not be permanently deleted.",
        )
        if not approved:
            return False
        subprocess.run(trash_command(sys.platform, chunk.path), check=True)
        return True

    def _chunk(self, path):
        try:
            return self.chunks[path]
        except KeyError as error:
            raise ValueError("That item is not part of the current scan.") from error


def main():
    api = DesktopApi()
    window = webview.create_window("Clear Space", str(WEB_ROOT / "index.html"), js_api=api, width=1120, height=760, min_size=(820, 600))
    api.window = window
    webview.start()


if __name__ == "__main__":
    main()
