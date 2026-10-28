# Design Reference: Clear Space

Use this prompt in Stitch. Upload the provided Clear Space logo with it.

---

Design a premium macOS desktop app called **Clear Space**.

It is a local-first storage cleaner for one person. It scans only the current user account folder by default, not the entire system drive. The product must feel calm, fast, intelligent, and native to macOS, with the polish and restrained confidence of Wispr Flow. Do not make it look like a generic SaaS dashboard, a file manager, or a gamified children’s app.

## Logo use

Use the uploaded logo as:

- The macOS app icon direction.
- A small in-app brand mark in the top-left header.

Do not overuse the logo as decoration.

## Core product idea

The user’s storage is visualised as a connected puzzle made from their real folder hierarchy.

After scanning:

- The first screen shows the current user’s top-level folders as interconnected Tetris-like puzzle pieces.
- Each puzzle piece represents a folder, not a category.
- Each piece has the folder name and a clear size badge, for example: `Library — 42.8 GB`.
- Larger folders receive larger puzzle pieces.
- The puzzle should feel spatial, organised, and satisfying, not like random rectangles or a treemap chart.
- Clicking a folder piece drills into that folder.
- Inside it, show its child folders as another puzzle layout.
- Continue this folder-path interaction until the user reaches direct files.
- At each level, show direct files as a clean list below the puzzle, not as cards or boxes.

## Do not use

- Category cards such as Photos, Games, Caches, or Documents on the main screen.
- Pie charts, bar charts, analytics dashboards, or fake system metrics.
- Large privacy banners saying “Local scan” or “Nothing uploads.”
- Generic mission, XP, gamification, or productivity-dashboard language.
- A fake percent-complete scan indicator.

## Scan experience

Create a dedicated active-scan screen:

- Heading: **Your space is taking shape.**
- Show a clean indeterminate progress bar, not a fake percentage.
- Show real progress text such as:
  - `3.2 GB scanned`
  - `Scanning ~/Library/Application Support`
  - `12,948 files checked`
- While scanning, small folder puzzle pieces should appear one by one as top-level folders are reached, making the storage map feel like it is assembling live.
- Use subtle motion only: pieces gently arrive and connect. No excessive animation.
- The scan starts with the current user account and includes Library, Downloads, Documents, Desktop, Movies, Music, Pictures, projects, and hidden user folders where readable.
- System folders are intentionally not part of the default scan.

## Folder explorer screen

Design the post-scan browser:

- Header with small logo, app name, current folder breadcrumb or path, available free space, back button, and “Scan another folder.”
- Main area: connected Tetris-like folder puzzle pieces with large, readable size badges.
- Each puzzle piece must be visibly clickable.
- Use a refined soft-neutral surface with restrained tinted puzzle colours that still feel cohesive.
- Puzzle pieces should have hierarchy through size, spacing, and typography, not visual clutter.
- A direct-file list sits below the puzzle.

## File list endpoint

When showing files in a folder:

- Use a clean, compact list with generous spacing, not card grids.
- Each row shows:
  - FILE or FOLDER label.
  - Name.
  - Short guidance text.
  - Prominent size badge.
- Use icon-only actions for:
  - Reveal in Finder.
  - Move to Trash.
- “Ask any AI” must be visually separate from those two actions: a small outlined button with a sparkle icon and the text **Ask any AI**.
- Moving to Trash always requires a native confirmation. Do not imply permanent deletion.
- “Ask any AI” opens a simple prompt sheet or modal explaining that only metadata is included, never file content.

## Visual direction

- macOS-native, high-end utility aesthetic.
- Light mode first.
- Warm off-white or pearl background, ink-black typography, muted blue accents drawn from the uploaded logo, subtle lilac, mint, and peach puzzle-piece variation.
- Strong typography hierarchy, large clean headings, minimal borders.
- Rounded corners, but not excessive pill UI.
- Use whitespace deliberately.
- Desktop-first at 1440×900, but keep the layout responsive down to a narrow desktop window.
- Accessible contrast, visible focus states, and 44px minimum targets where possible.

## Create these four complete screens

1. **Welcome**: “Make room without guessing.” with “Scan my account” and “Choose a folder instead.”
2. **Active scan**: real GB scanned, current path, files checked, and live assembling puzzle pieces.
3. **Root folder puzzle**: top-level home-folder pieces with size badges.
4. **Nested folder explorer**: child-folder puzzle plus direct-file list and separate Ask Any AI action.

The design should make storage feel understandable and navigable, not technical or intimidating.
