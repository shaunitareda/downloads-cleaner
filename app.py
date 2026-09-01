from __future__ import annotations

import os
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from organizer import CATEGORY_ORDER, execute_cleanup, scan_folder, summarize, undo_cleanup

APP_NAME = "One-Click Downloads Cleaner"


def default_log_path() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share"))
    return base / "UsefulBytePress" / "DownloadsCleaner" / "last-cleanup.json"


class DownloadsCleaner(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_NAME)
        self.geometry("900x640")
        self.minsize(760, 520)
        self.folder = tk.StringVar(value=str(Path.home() / "Downloads"))
        self.status = tk.StringVar(value="Choose a folder, then scan it. Nothing is changed during a scan.")
        self.plans = []
        self._build_ui()

    def _build_ui(self) -> None:
        outer = ttk.Frame(self, padding=18)
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text=APP_NAME, font=("Segoe UI", 19, "bold")).pack(anchor="w")
        ttk.Label(outer, text="Organize a messy folder locally — with preview and undo.").pack(anchor="w", pady=(2, 16))

        chooser = ttk.Frame(outer)
        chooser.pack(fill="x")
        ttk.Entry(chooser, textvariable=self.folder).pack(side="left", fill="x", expand=True)
        ttk.Button(chooser, text="Choose Folder", command=self.choose_folder).pack(side="left", padx=(8, 0))
        ttk.Button(chooser, text="Scan", command=self.scan).pack(side="left", padx=(8, 0))

        self.summary_frame = ttk.Frame(outer)
        self.summary_frame.pack(fill="x", pady=14)
        self.summary_labels = {}
        for column, name in enumerate(("Total",) + CATEGORY_ORDER + ("Skipped",)):
            box = ttk.Frame(self.summary_frame, padding=(8, 4))
            box.grid(row=0, column=column, sticky="nsew")
            ttk.Label(box, text=name, font=("Segoe UI", 9, "bold")).pack()
            value = ttk.Label(box, text="0")
            value.pack()
            self.summary_labels[name] = value
            self.summary_frame.columnconfigure(column, weight=1)

        ttk.Label(outer, text="Preview", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        table_frame = ttk.Frame(outer)
        table_frame.pack(fill="both", expand=True, pady=(6, 12))
        columns = ("file", "category", "destination", "status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        self.tree.heading("file", text="File")
        self.tree.heading("category", text="Category")
        self.tree.heading("destination", text="Destination")
        self.tree.heading("status", text="Status")
        self.tree.column("file", width=220)
        self.tree.column("category", width=100)
        self.tree.column("destination", width=340)
        self.tree.column("status", width=120)
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        actions = ttk.Frame(outer)
        actions.pack(fill="x")
        self.organize_button = ttk.Button(actions, text="Organize", command=self.organize, state="disabled")
        self.organize_button.pack(side="left")
        ttk.Button(actions, text="Undo Last Cleanup", command=self.undo).pack(side="left", padx=(8, 0))
        ttk.Label(actions, textvariable=self.status).pack(side="right")

    def choose_folder(self) -> None:
        selected = filedialog.askdirectory(initialdir=self.folder.get() or str(Path.home()))
        if selected:
            self.folder.set(selected)
            self.scan()

    def scan(self) -> None:
        try:
            self.plans = scan_folder(Path(self.folder.get()))
        except Exception as exc:
            messagebox.showerror(APP_NAME, str(exc))
            return
        for item in self.tree.get_children():
            self.tree.delete(item)
        for plan in self.plans:
            source = Path(plan.source)
            status = "Ready" if plan.status == "ready" else f"Skipped: {plan.reason}"
            self.tree.insert("", "end", values=(source.name, plan.category, plan.destination, status))
        values = summarize(self.plans)
        for name, label in self.summary_labels.items():
            label.configure(text=str(values.get(name, 0)))
        ready = sum(1 for plan in self.plans if plan.status == "ready")
        self.organize_button.configure(state="normal" if ready else "disabled")
        self.status.set(f"Preview ready: {ready} file(s) can be organized. No files have moved yet.")

    def organize(self) -> None:
        ready = [plan for plan in self.plans if plan.status == "ready"]
        if not ready:
            return
        if not messagebox.askyesno(APP_NAME, f"Organize {len(ready)} file(s)?\n\nNothing will be deleted or overwritten."):
            return
        result = execute_cleanup(self.plans, default_log_path())
        moved, skipped, errors = len(result["moves"]), len(result["skipped"]), len(result["errors"])
        self.status.set(f"Done: {moved} moved, {skipped} skipped, {errors} errors.")
        messagebox.showinfo(APP_NAME, f"Cleanup complete.\n\nMoved: {moved}\nSkipped: {skipped}\nErrors: {errors}\n\nUndo Last Cleanup is available.")
        self.scan()

    def undo(self) -> None:
        try:
            result = undo_cleanup(default_log_path())
        except FileNotFoundError as exc:
            messagebox.showinfo(APP_NAME, str(exc))
            return
        except Exception as exc:
            messagebox.showerror(APP_NAME, str(exc))
            return
        restored, skipped, errors = len(result["restored"]), len(result["skipped"]), len(result["errors"])
        self.status.set(f"Undo: {restored} restored, {skipped} skipped, {errors} errors.")
        messagebox.showinfo(APP_NAME, f"Undo complete.\n\nRestored: {restored}\nSkipped: {skipped}\nErrors: {errors}")
        self.scan()


if __name__ == "__main__":
    DownloadsCleaner().mainloop()
