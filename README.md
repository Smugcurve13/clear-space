# Clear Space

A local-first storage cleaner for macOS, with Linux support. It scans the storage it can read, groups files into understandable categories, starts with the largest category, and explains why an item needs a careful review.

## Safety

- Scanning is read-only.
- Every result is marked as a **File** or **Folder** before you act.
- **Reveal** opens its location in Finder on macOS, or the containing folder on Linux.
- **Move to Trash** always asks for confirmation and uses the system Trash. It never calls `rm` or permanently deletes items.
- **Ask any AI** generates a copyable prompt with metadata only. It does not read or upload file contents.

## Run

```bash
python3 space_quest.py
```

macOS: grant Full Disk Access only if you want it to inspect protected locations. Without it, the app scans every location macOS allows and skips the rest.

Linux: the same command works with Python 3 and Tk. Moving to Trash uses `gio trash` when it is available.

## Test

```bash
python3 -m unittest -v
python3 -m py_compile space_core.py space_quest.py
```
