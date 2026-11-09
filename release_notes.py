"""Canonical release notes for the app and GitHub releases."""

from version import __version__


NOTES = {
    "0.0.1-alpha.4": {
        "NEW": ["Import selected iPhone photos and videos to a chosen hard-drive folder without deleting the originals."],
        "CHANGED": [],
        "FIXED": [],
    }
}


def render_markdown(version=__version__):
    notes = NOTES.get(version)
    if not notes:
        return ""
    sections = [f"# Clear Space v{version}"]
    for category in ("NEW", "CHANGED", "FIXED"):
        entries = notes[category]
        if entries:
            sections.append(f"## {category.title()}\n" + "\n".join(f"- {entry}" for entry in entries))
    return "\n\n".join(sections) + "\n"


if __name__ == "__main__":
    print(render_markdown(), end="")
