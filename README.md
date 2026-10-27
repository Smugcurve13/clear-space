# Clear Space

A local-first storage cleaner for macOS and Linux. The desktop app uses a polished HTML/CSS interface inside a native PyWebView window, while Python handles local scanning and system actions.

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

## Run

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python space_quest.py
```

macOS: grant Full Disk Access only if you want it to inspect protected locations. Without it, the app scans every location macOS allows and skips the rest.

Linux: moving to Trash uses `gio trash` when it is available. PySide6 also needs the system OpenGL/EGL runtime, for example `sudo apt install libegl1` on Ubuntu.

## Test

```bash
.venv/bin/python -m unittest -v
.venv/bin/python -m py_compile desktop_app.py space_core.py space_quest.py
node --check web/app.js
```
