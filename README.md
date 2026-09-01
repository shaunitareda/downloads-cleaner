# One-Click Downloads Cleaner

A tiny local-first Windows utility from Useful Byte Press / Virtualsis LLC.

## Status
Prototype v0.1 source is implemented. Core organizer logic has a test suite covering classification, subfolder/hidden-file skipping, destination collisions, organize/undo round trips, Unicode filenames, and undo collision protection.

The next gate is native Windows testing and packaging. Do not sell or distribute this prototype as production-ready yet.

## Run from source
Requires Python 3 with Tkinter.

```powershell
python app.py
```

## Product promise
- Local only
- No account
- No cloud uploads
- No telemetry
- No deletion
- No overwriting
- Preview before organizing
- Undo last cleanup

## v0.1 behavior
Only top-level files in the selected folder are considered. Existing subfolders are ignored. Files are grouped into Documents, Images, Video, Audio, Archives, Installers, and Other.

## Transaction log
The GUI stores its last cleanup transaction under the user's local application-data directory at:

`UsefulBytePress\DownloadsCleaner\last-cleanup.json`

The log records successful moves so Undo can restore them. A fully successful undo removes the transaction log. An incomplete undo preserves it for retry/inspection.

## Before release
1. Test on Windows 10 and Windows 11.
2. Test Windows hidden/system attributes.
3. Test files open/locked by common applications.
4. Test long paths and unusual Unicode names.
5. Stress-test hundreds/thousands of files.
6. Repeat organize/undo cycles.
7. Package as a standalone `.exe` so buyers do not need Python.
8. Scan packaged binary with Windows Defender and VirusTotal before distribution.
9. Code-sign later if sales justify the certificate cost; do not incur that expense for the initial validation experiment unless SmartScreen makes the unsigned build impractical.
