# Clear Space

A local-first storage cleaner for macOS and Linux. The desktop app renders your user-account folders as a drill-down puzzle, while Python performs a one-pass local scan and native system actions.

## Alpha download

The first alpha is `v0.0.1-alpha.1`. Download the bundle that matches your machine from the GitHub Releases page:

- macOS: unzip the matching `macos-arm64` (Apple Silicon) or `macos-x86_64` (Intel) archive, drag **Clear Space.app** into Applications, then run `xattr -cr "/Applications/Clear Space.app"` before its first Control-click → Open launch.
- Linux x86_64: extract the `.tar.gz`, then run `./Clear\ Space/Clear\ Space`.

Linux packages are built on Ubuntu and require a graphical desktop plus its normal OpenGL/EGL runtime.

## Stack

- Python 3 + PyWebView
- Vanilla HTML, CSS, and JavaScript
- Python standard-library filesystem scanning and platform actions
- No server, cloud account, database, telemetry, AI SDK, or file uploads

## Safety

- Scanning is read-only.
- Every result is marked as a **File** or **Folder** before you act.
- **Reveal** opens its location in Finder on macOS, or the containing folder on Linux.
- **Move to Trash** opens a native confirmation first and uses the system Trash. It never calls `rm` or permanently deletes items.
- **Ask any AI** generates a copyable prompt with metadata only. It does not read or upload file contents.
- Apple-hidden folders are excluded from scan results and suggestions on macOS.

## Run

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python space_quest.py
```

macOS: the default scan is your current user account, not the whole drive. Choose another folder only when you deliberately want to inspect it.

Linux: moving to Trash uses `gio trash` when it is available. PySide6 also needs the system OpenGL/EGL runtime, for example `sudo apt install libegl1` on Ubuntu.

## Test

```bash
.venv/bin/python -m unittest -v
.venv/bin/python -m py_compile desktop_app.py space_core.py space_quest.py
node --check web/app.js
```

## Release

```bash
.venv/bin/pip install -r requirements.txt -r requirements-build.txt
.venv/bin/python build_release.py
```

Tagging `v0.0.1-alpha.1` runs GitHub Actions to build unsigned native alpha bundles for macOS (Apple Silicon and Intel) and Linux x86_64, then publishes the matching prerelease notes from `release_notes.py`.
