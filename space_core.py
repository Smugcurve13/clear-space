from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Chunk:
    path: Path
    size: int
    kind: str
    category: str
    guidance: str


@dataclass(frozen=True)
class StorageEntry:
    path: Path
    size: int
    kind: str
    category: str
    guidance: str


@dataclass(frozen=True)
class ScanResult:
    chunks: list[Chunk]
    category_sizes: dict[str, int]
    directory_sizes: dict[Path, int]


VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".m4v", ".webm"}
PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".gif", ".raw", ".psd"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".aiff", ".flac", ".m4a"}
DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".pages", ".numbers", ".key", ".txt"}
ARCHIVE_EXTENSIONS = {".zip", ".rar", ".7z", ".tar", ".gz", ".dmg", ".pkg", ".iso"}
GAME_EXTENSIONS = {".pak", ".bundle", ".obb", ".unity3d"}
VIRTUAL_ROOT_NAMES = {"dev", "proc", "sys", "run"}


def classify_path(path: Path) -> tuple[str, str]:
    lower_path = str(path).lower()
    suffix = path.suffix.lower()
    parts = {part.lower() for part in path.parts}
    if suffix in GAME_EXTENSIONS or parts & {"steam", "epic", "blizzard", "minecraft", "steamapps", "games"}:
        return "Games", "Game data detected from its name or location. Check the game launcher before removal."
    if suffix in VIDEO_EXTENSIONS or suffix in PHOTO_EXTENSIONS:
        return "Photos & videos", "Personal media may be irreplaceable. Open it before deciding."
    if suffix in AUDIO_EXTENSIONS:
        return "Audio", "Audio files can be personal or project material. Review before removal."
    if "time machine" in lower_path or "backups.backupdb" in lower_path:
        return "Backups", "A backup can protect other files. Check its date and source first."
    if suffix in DOCUMENT_EXTENSIONS:
        return "Documents", "Potentially important work or records. Keep unless you recognise it."
    if any(name in parts for name in {"cache", "caches", ".cache"}):
        return "Caches", "Usually recreated by an app, but close the related app before removal."
    if parts & {"node_modules", ".venv", "venv", "deriveddata", "build", "dist"}:
        return "Developer files", "Often rebuildable from a project, but check the project first."
    if path.name.lower().endswith(".app") or suffix in {".app", ".exe"}:
        return "Apps", "An application or app bundle. Remove only if you no longer use it."
    if suffix in ARCHIVE_EXTENSIONS:
        return "Archives & installers", "Often removable after confirming the original is no longer needed."
    return "Other", "Unknown data. Open or reveal it before making a decision."


def scan_storage(root: Path, minimum_item_size: int, item_limit: int, on_progress=None) -> ScanResult:
    root = root.resolve()
    category_sizes: dict[str, int] = {}
    chunks: list[Chunk] = []
    directory_sizes: dict[Path, int] = {root: 0}
    files_scanned = 0
    folders_scanned = 0
    bytes_scanned = 0

    def report(current_path: Path):
        if not on_progress:
            return
        try:
            relative = current_path.relative_to(root)
            top_level = str(root / relative.parts[0]) if relative.parts else str(root)
        except ValueError:
            top_level = str(root)
        on_progress(
            {
                "current_path": str(current_path),
                "top_level": top_level,
                "files_scanned": files_scanned,
                "folders_scanned": folders_scanned,
                "bytes_scanned": bytes_scanned,
                "items_found": len(chunks),
            }
        )

    report(root)
    for directory, subdirs, filenames in os.walk(root, topdown=True, followlinks=False, onerror=lambda _: None):
        directory_path = Path(directory)
        folders_scanned += 1
        directory_sizes.setdefault(directory_path, 0)
        if directory_path.parent == root:
            report(directory_path)
        if directory_path == root and root == Path("/"):
            subdirs[:] = [name for name in subdirs if name not in VIRTUAL_ROOT_NAMES]
        for dirname in list(subdirs):
            child = directory_path / dirname
            if child.is_symlink():
                subdirs.remove(dirname)
                continue
            directory_sizes.setdefault(child, 0)
        for filename in filenames:
            path = directory_path / filename
            try:
                if path.is_symlink():
                    continue
                size = path.stat().st_size
            except OSError:
                continue
            files_scanned += 1
            bytes_scanned += size
            directory_sizes[directory_path] += size
            category, guidance = classify_path(path)
            category_sizes[category] = category_sizes.get(category, 0) + size
            if size >= minimum_item_size:
                chunks.append(Chunk(path, size, "File", category, guidance))
            if files_scanned % 500 == 0:
                report(directory_path)
        if folders_scanned % 25 == 0:
            report(directory_path)

    for directory in sorted(directory_sizes, key=lambda path: len(path.parts), reverse=True):
        if directory != root and directory.parent in directory_sizes:
            directory_sizes[directory.parent] += directory_sizes[directory]
    report(root)
    chunks.sort(key=lambda chunk: chunk.size, reverse=True)
    return ScanResult(chunks[:item_limit], category_sizes, directory_sizes)


def list_directory(path: Path, directory_sizes: dict[Path, int]) -> tuple[list[StorageEntry], list[StorageEntry]]:
    folders: list[StorageEntry] = []
    files: list[StorageEntry] = []
    try:
        entries = list(os.scandir(path))
    except OSError:
        return folders, files
    for entry in entries:
        entry_path = Path(entry.path)
        try:
            if entry.is_symlink():
                continue
            if entry.is_dir(follow_symlinks=False):
                category, guidance = classify_path(entry_path)
                folders.append(StorageEntry(entry_path, directory_sizes.get(entry_path, 0), "Folder", category, guidance))
            else:
                size = entry.stat(follow_symlinks=False).st_size
                category, guidance = classify_path(entry_path)
                files.append(StorageEntry(entry_path, size, "File", category, guidance))
        except OSError:
            continue
    folders.sort(key=lambda entry: entry.size, reverse=True)
    files.sort(key=lambda entry: entry.size, reverse=True)
    return folders, files


def format_bytes(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{int(value)} B" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    raise AssertionError("unreachable")


def trash_command(platform: str, path: Path) -> list[str]:
    if platform == "darwin":
        script = "on run argv\n tell application \"Finder\" to delete (POSIX file (item 1 of argv))\nend run"
        return ["osascript", "-e", script, str(path)]
    return ["gio", "trash", str(path)]


def build_ai_prompt(entry: Chunk | StorageEntry) -> str:
    return f"""I need help deciding whether a local storage item may be safe to remove.

No file contents were read or shared. This is metadata only:
- Name: {entry.path.name}
- Path: {entry.path}
- Type: {entry.kind}
- Size: {format_bytes(entry.size)}
- Category: {entry.category}
- Local guidance: {entry.guidance}

Based only on this metadata, tell me:
1. What it is likely to be.
2. What I should check before moving it to Trash.
3. What could break or be lost if I remove it.
4. Whether the safest default is keep, archive, or move to Trash.

Treat uncertainty as keep. Do not tell me to run destructive commands."""
