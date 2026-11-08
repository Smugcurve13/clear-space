"""Canonical release notes for the app and GitHub releases."""

from version import __version__


NOTES = {
    "0.0.1-alpha.3": {
        "NEW": [],
        "CHANGED": ["macOS releases now preserve the app bundle's code signature when unzipped."],
        "FIXED": ["macOS application icon is included in release bundles."],
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
