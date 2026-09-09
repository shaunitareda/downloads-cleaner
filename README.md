# Downloads Cleaner

A small, local-first Windows utility for turning a cluttered Downloads folder into something manageable.

Downloads Cleaner previews how files will be organized, sorts them into sensible categories, and lets you undo the cleanup if you change your mind.

## Features

- Preview changes before moving anything
- Organizes files into:
  - Documents
  - Images
  - Video
  - Audio
  - Archives
  - Installers
  - Other
- Ignores existing subfolders
- Handles filename collisions safely
- Supports Unicode filenames
- Undo the most recent cleanup
- Never deletes files
- Never overwrites existing files
- No account required
- No cloud uploads
- No telemetry

## Privacy

Downloads Cleaner is intentionally local-first.

Your files stay on your computer. The application does not upload filenames, file contents, usage information, or other data to a remote service.

## How it works

Only files at the top level of the selected folder are considered for organization. Existing subfolders are left untouched.

Before anything is moved, Downloads Cleaner shows a preview of the proposed changes.

After organizing, a local transaction record is stored at:

`UsefulBytePress\DownloadsCleaner\last-cleanup.json`

This allows the last cleanup to be reversed. A successful undo removes the transaction record; an incomplete undo preserves it so the operation can be retried or inspected.

## Run from source

Requires Python 3 with Tkinter.

```powershell
git clone https://github.com/shaunitareda/downloads-cleaner.git
cd downloads-cleaner
python app.py
```

## Tests

The organizer has automated tests covering:

- file classification
- existing subfolder handling
- hidden-file handling
- destination collisions
- organize/undo round trips
- Unicode filenames
- undo collision protection

Run them with:

```powershell
python -m unittest
```

## Project status

Downloads Cleaner is currently an experimental prototype.

The core organizer and undo system are implemented and tested. Native Windows testing and standalone executable packaging are the next major milestones.

It is not currently intended for production use or distribution.

## Built with

- Python
- Tkinter
- PyInstaller
- GitHub Actions

## Development

This project is part of my exploration of practical AI-assisted software development. I use AI as a development partner while remaining involved in product decisions, implementation direction, debugging, testing, and release decisions.

## License

No open-source license has been assigned yet. The source is publicly viewable, but no permission to copy, modify, or redistribute it is granted unless a license is added later.
