# One-Click Downloads Cleaner — v0.1 Product Specification

## Experiment goal
Build a tiny, local-first Windows utility that safely organizes a cluttered folder with preview and one-click undo. Target launch price: $4.99.

## v0.1 scope
1. Choose a folder (default suggestion: Downloads).
2. Scan without modifying anything.
3. Classify top-level files into Documents, Images, Video, Audio, Archives, Installers, and Other.
4. Preview every planned move before execution.
5. Organize by creating category folders and moving files.
6. Undo the most recent cleanup from a transaction log.

## Safety invariants
- Never delete files.
- Never overwrite an existing file.
- Never upload files or filenames.
- Never require an account.
- Ignore subfolders in v0.1.
- Skip hidden/system files where detectable.
- Skip/report files that cannot be moved.
- Record successful moves before presenting cleanup as complete.
- Undo must restore each successfully moved file to its original path when possible.
- Name collisions during organize or undo must stop/skip safely rather than overwrite.

## File categories
Documents: pdf, doc, docx, xls, xlsx, ppt, pptx, txt, rtf, csv, odt, ods, odp, md
Images: jpg, jpeg, png, gif, webp, bmp, tif, tiff, svg, heic, avif
Video: mp4, mov, avi, mkv, webm, m4v, wmv
Audio: mp3, wav, flac, m4a, aac, ogg, wma
Archives: zip, 7z, rar, tar, gz, bz2, xz
Installers: exe, msi, msix, appx, appxbundle, msixbundle
Other: everything else

## UX
Primary flow: Choose Folder → Scan → Preview Cleanup → Organize → Undo Last Cleanup.

Scan summary should show total top-level files and counts by category. Preview should show source and destination for every planned move. Completion should show moved/skipped/error counts. Undo should be prominent after a successful cleanup.

## Explicitly out of scope
No recursive organization, deletion, duplicate detection, AI, cloud sync, folder monitoring, scheduled cleanup, regex/rules engine, account/login, telemetry, subscriptions, or admin privileges.

## Validation gate before sale
Test on disposable folders containing hundreds of dummy files, Unicode filenames, extensionless files, duplicate destination names, pre-existing category folders, locked/in-use files, hidden files, very long names/paths where supported, and repeated organize/undo cycles. Product does not ship until tests demonstrate no silent deletion or overwrite and undo behavior is reliable.
