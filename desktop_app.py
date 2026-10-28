import shutil
import subprocess
import sys
from pathlib import Path
from threading import Lock

import webview

from space_core import StorageEntry, build_ai_prompt, format_bytes, list_directory, scan_storage, trash_command

MINIMUM_ITEM_SIZE = 100 * 1024 * 1024
WEB_ROOT = Path(__file__).parent / "web"


def default_scan_root() -> Path:
    return Path.home()


class DesktopApi:
    def __init__(self, minimum_item_size=MINIMUM_ITEM_SIZE):
        self.minimum_item_size = minimum_item_size
        self.root = default_scan_root()
        self.window = None
        self.entries = {}
        self.directory_sizes = {self.root: 0}
        self._status_lock = Lock()
        self._scan_status = {"state": "idle", "current_path": str(self.root), "top_level": str(self.root), "files_scanned": 0, "folders_scanned": 0, "bytes_scanned": 0, "items_found": 0}

    def get_scan_status(self):
        with self._status_lock:
            return dict(self._scan_status)

    def _update_scan_status(self, **update):
        with self._status_lock:
            self._scan_status.update(update)

    def choose_folder(self):
        if self.window is None:
            return None
        selected = self.window.create_file_dialog(webview.FileDialog.FOLDER, directory=str(self.root))
        return str(selected[0]) if selected else None

    def scan(self, root=None):
        root_path = Path(root).expanduser() if root else default_scan_root()
        if not root_path.is_dir():
            raise ValueError("Choose a readable folder.")
        self.root = root_path.resolve()
        self._update_scan_status(
            state="scanning",
            current_path=str(self.root),
            top_level=str(self.root),
            files_scanned=0,
            folders_scanned=0,
            bytes_scanned=0,
            items_found=0,
        )
        try:
            result = scan_storage(
                self.root,
                self.minimum_item_size,
                100,
                on_progress=lambda update: self._update_scan_status(state="scanning", **update),
            )
        except Exception:
            self._update_scan_status(state="failed")
            raise
        self.directory_sizes = result.directory_sizes
        self._update_scan_status(state="complete", current_path=str(self.root), top_level=str(self.root), items_found=len(result.chunks))
        return self._directory_payload(self.root)

    def browse(self, path):
        directory = Path(path).resolve()
        if directory not in self.directory_sizes:
            raise ValueError("That folder is not part of the current scan.")
        return self._directory_payload(directory)

    def _entry_payload(self, entry: StorageEntry):
        self.entries[str(entry.path)] = entry
        return {
            "path": str(entry.path),
            "name": entry.path.name,
            "parent": str(entry.path.parent),
            "kind": entry.kind,
            "category": entry.category,
            "size": entry.size,
            "display_size": format_bytes(entry.size),
            "guidance": entry.guidance,
        }

    def _directory_payload(self, directory: Path):
        folders, files = list_directory(directory, self.directory_sizes)
        return {
            "root": str(self.root),
            "free_space": format_bytes(shutil.disk_usage(self.root).free),
            "folder": {
                "path": str(directory),
                "name": directory.name or str(directory),
                "size": self.directory_sizes.get(directory, 0),
                "display_size": format_bytes(self.directory_sizes.get(directory, 0)),
            },
            "folders": [self._entry_payload(entry) for entry in folders],
            "files": [self._entry_payload(entry) for entry in files[:200]],
            "has_more_files": len(files) > 200,
        }

    def ai_prompt(self, path):
        return build_ai_prompt(self._entry(path))

    def reveal(self, path):
        target = self._entry(path).path
        command = ["open", "-R", str(target)] if sys.platform == "darwin" else ["xdg-open", str(target.parent)]
        subprocess.run(command, check=True)
        return True

    def move_to_trash(self, path):
        chunk = self._entry(path)
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

    def _entry(self, path):
        try:
            return self.entries[path]
        except KeyError as error:
            raise ValueError("That item is not part of the current view.") from error


def main():
    api = DesktopApi()
    window = webview.create_window("Clear Space", str(WEB_ROOT / "index.html"), js_api=api, width=1120, height=760, min_size=(820, 600))
    api.window = window
    webview.start()


if __name__ == "__main__":
    main()
