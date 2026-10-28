"""Build one native Clear Space release archive for the current platform."""

import platform
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

from version import __version__

ROOT = Path(__file__).parent
APP_NAME = "Clear Space"
DIST = ROOT / "dist"
BUILD = ROOT / "build"
ASSETS = ROOT / "release-assets"


def asset_name(system=platform.system(), machine=platform.machine()):
    machine = machine.lower().replace("aarch64", "arm64")
    if system == "Darwin":
        return f"Clear-Space-v{__version__}-macos-{machine}.zip"
    if system == "Linux":
        return f"Clear-Space-v{__version__}-linux-{machine}.tar.gz"
    raise SystemExit(f"Unsupported release platform: {system}")


def build():
    for path in (DIST, BUILD, ASSETS):
        shutil.rmtree(path, ignore_errors=True)
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--onedir",
        "--name",
        APP_NAME,
        "--add-data",
        f"{ROOT / 'web'}{os.pathsep}web",
        "--add-data",
        f"{ROOT / 'LICENSE'}{os.pathsep}.",
        "--add-data",
        f"{ROOT / 'THIRD_PARTY_NOTICES.md'}{os.pathsep}.",
        "space_quest.py",
    ]
    subprocess.run(command, cwd=ROOT, check=True)
    ASSETS.mkdir()
    bundle = DIST / (f"{APP_NAME}.app" if platform.system() == "Darwin" else APP_NAME)
    if not bundle.exists():
        raise SystemExit(f"PyInstaller did not produce {bundle}")
    if not any(path.name == "LICENSE" for path in bundle.rglob("LICENSE")):
        raise SystemExit("Release bundle is missing LICENSE")
    if not any(path.name == "THIRD_PARTY_NOTICES.md" for path in bundle.rglob("THIRD_PARTY_NOTICES.md")):
        raise SystemExit("Release bundle is missing THIRD_PARTY_NOTICES.md")
    archive = ASSETS / asset_name()
    if platform.system() == "Darwin":
        shutil.make_archive(str(archive.with_suffix("")), "zip", DIST, bundle.name)
    else:
        with tarfile.open(archive, "w:gz") as output:
            output.add(bundle, arcname=bundle.name)
    if not archive.is_file() or archive.stat().st_size == 0:
        raise SystemExit("Release archive was not created")
    return archive


if __name__ == "__main__":
    print(build())
