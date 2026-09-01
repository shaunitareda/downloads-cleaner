from __future__ import annotations

import ctypes
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

CATEGORY_EXTENSIONS = {
    "Documents": {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".rtf", ".csv", ".odt", ".ods", ".odp", ".md"},
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".svg", ".heic", ".avif"},
    "Video": {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".wmv"},
    "Audio": {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".wma"},
    "Archives": {".zip", ".7z", ".rar", ".tar", ".gz", ".bz2", ".xz"},
    "Installers": {".exe", ".msi", ".msix", ".appx", ".appxbundle", ".msixbundle"},
}
CATEGORY_ORDER = tuple(CATEGORY_EXTENSIONS) + ("Other",)


@dataclass(frozen=True)
class MovePlan:
    source: str
    destination: str
    category: str
    status: str = "ready"
    reason: str = ""


def classify_file(path: Path) -> str:
    suffix = path.suffix.lower()
    for category, extensions in CATEGORY_EXTENSIONS.items():
        if suffix in extensions:
            return category
    return "Other"


def _is_hidden_or_system(path: Path) -> bool:
    if path.name.startswith("."):
        return True
    if os.name != "nt":
        return False
    try:
        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
        if attrs == -1:
            return False
        return bool(attrs & (0x2 | 0x4))
    except Exception:
        return False


def scan_folder(folder: Path) -> list[MovePlan]:
    folder = folder.expanduser().resolve()
    if not folder.exists() or not folder.is_dir():
        raise ValueError("Selected path is not a folder.")

    plans: list[MovePlan] = []
    for source in sorted(folder.iterdir(), key=lambda p: p.name.lower()):
        if not source.is_file() or _is_hidden_or_system(source):
            continue
        category = classify_file(source)
        destination = folder / category / source.name
        if destination.exists():
            plans.append(MovePlan(str(source), str(destination), category, "skip", "destination exists"))
        else:
            plans.append(MovePlan(str(source), str(destination), category))
    return plans


def summarize(plans: Iterable[MovePlan]) -> dict[str, int]:
    counts = {category: 0 for category in CATEGORY_ORDER}
    total = 0
    skipped = 0
    for plan in plans:
        total += 1
        counts[plan.category] += 1
        if plan.status != "ready":
            skipped += 1
    return {"Total": total, **counts, "Skipped": skipped}


def _atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def execute_cleanup(plans: Iterable[MovePlan], log_path: Path) -> dict:
    transaction = {"version": 1, "complete": False, "moves": [], "skipped": [], "errors": []}
    _atomic_write_json(log_path, transaction)

    for plan in plans:
        source = Path(plan.source)
        destination = Path(plan.destination)
        if plan.status != "ready":
            transaction["skipped"].append({**asdict(plan)})
            _atomic_write_json(log_path, transaction)
            continue
        try:
            if not source.exists():
                raise FileNotFoundError("source no longer exists")
            if destination.exists():
                transaction["skipped"].append({**asdict(plan), "reason": "destination exists"})
                _atomic_write_json(log_path, transaction)
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.rename(source, destination)
            transaction["moves"].append({"source": str(source), "destination": str(destination), "category": plan.category})
            _atomic_write_json(log_path, transaction)
        except Exception as exc:
            transaction["errors"].append({**asdict(plan), "error": str(exc)})
            _atomic_write_json(log_path, transaction)

    transaction["complete"] = True
    _atomic_write_json(log_path, transaction)
    return transaction


def undo_cleanup(log_path: Path) -> dict:
    if not log_path.exists():
        raise FileNotFoundError("No cleanup transaction is available to undo.")
    transaction = json.loads(log_path.read_text(encoding="utf-8"))
    result = {"restored": [], "skipped": [], "errors": []}

    for move in reversed(transaction.get("moves", [])):
        original = Path(move["source"])
        current = Path(move["destination"])
        try:
            if original.exists():
                result["skipped"].append({**move, "reason": "original path already exists"})
                continue
            if not current.exists():
                result["skipped"].append({**move, "reason": "organized file no longer exists"})
                continue
            original.parent.mkdir(parents=True, exist_ok=True)
            os.rename(current, original)
            result["restored"].append(move)
        except Exception as exc:
            result["errors"].append({**move, "error": str(exc)})

    if not result["skipped"] and not result["errors"]:
        log_path.unlink(missing_ok=True)
    else:
        transaction["last_undo"] = result
        _atomic_write_json(log_path, transaction)
    return result
