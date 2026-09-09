from __future__ import annotations

import os
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from organizer import CATEGORY_ORDER, execute_cleanup, scan_folder, summarize, undo_cleanup

APP_NAME = "Downloads Cleaner"


def default_log_path() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share"))
    return base / "UsefulBytePress" / "DownloadsCleaner" / "last-cleanup.json"


class DownloadsCleaner(tk.Tk):
    def __init__(self) -> None:
        super().__init__()

        self.title(APP_NAME)
        self.geometry("960x650")
        self.minsize(820, 560)

        self.folder = tk.StringVar(value=str(Path.home() / "Downloads"))
        self.status = tk.StringVar(
            value="Choose a folder and scan it to preview your cleanup."
        )
        self.plans = []

        self._configure_styles()
        self._build_ui()

    def _configure_styles(self) -> None:
        style = ttk.Style(self)

        if "vista" in style.theme_names():
            style.theme_use("vista")

        style.configure(
            "Title.TLabel",
            font=("Segoe UI", 22, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            font=("Segoe UI", 10),
        )
        style.configure(
            "Section.TLabel",
            font=("Segoe UI", 11, "bold"),
        )
        style.configure(
            "CounterTitle.TLabel",
            font=("Segoe UI", 9),
        )
        style.configure(
            "CounterValue.TLabel",
            font=("Segoe UI", 16, "bold"),
        )
        style.configure(
            "Status.TLabel",
            font=("Segoe UI", 9),
        )

        style.configure("Treeview", rowheight=28)
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))

    def _build_ui(self) -> None:
        outer = ttk.Frame(self, padding=(24, 22, 24, 18))
        outer.pack(fill="both", expand=True)

        # Header
        ttk.Label(
            outer,
            text=APP_NAME,
            style="Title.TLabel",
        ).pack(anchor="w")

        ttk.Label(
            outer,
            text="A simple, local-first way to organize a cluttered folder.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(2, 20))

        # Folder selector
        chooser = ttk.Frame(outer)
        chooser.pack(fill="x", pady=(0, 18))

        folder_entry = ttk.Entry(
            chooser,
            textvariable=self.folder,
            font=("Segoe UI", 10),
        )
        folder_entry.pack(side="left", fill="x", expand=True, ipady=3)

        ttk.Button(
            chooser,
            text="Choose Folder",
            command=self.choose_folder,
        ).pack(side="left", padx=(8, 0))

        ttk.Button(
            chooser,
            text="Scan Folder",
            command=self.scan,
        ).pack(side="left", padx=(8, 0))

        # Summary
        summary_header = ttk.Frame(outer)
        summary_header.pack(fill="x")

        ttk.Label(
            summary_header,
            text="Scan summary",
            style="Section.TLabel",
        ).pack(side="left")

        ttk.Label(
            summary_header,
            text="Nothing moves until you choose Organize.",
            style="Status.TLabel",
        ).pack(side="right")

        self.summary_frame = ttk.Frame(outer)
        self.summary_frame.pack(fill="x", pady=(8, 20))

        self.summary_labels = {}

        names = ("Total",) + CATEGORY_ORDER + ("Skipped",)

        for column, name in enumerate(names):
            box = ttk.Frame(
                self.summary_frame,
                padding=(8, 7),
                relief="groove",
                borderwidth=1,
            )
            box.grid(
                row=0,
                column=column,
                sticky="nsew",
                padx=(0 if column == 0 else 3, 0),
            )

            ttk.Label(
                box,
                text=name,
                style="CounterTitle.TLabel",
            ).pack()

            value = ttk.Label(
                box,
                text="0",
                style="CounterValue.TLabel",
            )
            value.pack(pady=(1, 0))

            self.summary_labels[name] = value
            self.summary_frame.columnconfigure(column, weight=1)

        # Preview
        ttk.Label(
            outer,
            text="Preview",
            style="Section.TLabel",
        ).pack(anchor="w")

        table_frame = ttk.Frame(outer)
        table_frame.pack(fill="both", expand=True, pady=(7, 14))

        columns = ("file", "category", "destination", "status")
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
        )

        self.tree.heading("file", text="File")
        self.tree.heading("category", text="Category")
        self.tree.heading("destination", text="Destination")
        self.tree.heading("status", text="Status")

        self.tree.column("file", width=230, minwidth=150)
        self.tree.column("category", width=105, minwidth=90, anchor="center")
        self.tree.column("destination", width=380, minwidth=200)
        self.tree.column("status", width=120, minwidth=100, anchor="center")

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview,
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Footer/actions
        footer = ttk.Frame(outer)
        footer.pack(fill="x")

        self.organize_button = ttk.Button(
            footer,
            text="Organize Files",
            command=self.organize,
            state="disabled",
        )
        self.organize_button.pack(side="left")

        ttk.Button(
            footer,
            text="Undo Last Cleanup",
            command=self.undo,
        ).pack(side="left", padx=(8, 0))

        ttk.Label(
            footer,
            textvariable=self.status,
            style="Status.TLabel",
        ).pack(side="right", padx=(16, 0))

    def choose_folder(self) -> None:
        selected = filedialog.askdirectory(
            initialdir=self.folder.get() or str(Path.home())
        )
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
            status = (
                "Ready"
                if plan.status == "ready"
                else f"Skipped: {plan.reason}"
            )
            self.tree.insert(
                "",
                "end",
                values=(
                    source.name,
                    plan.category,
                    plan.destination,
                    status,
                ),
            )

        values = summarize(self.plans)

        for name, label in self.summary_labels.items():
            label.configure(text=str(values.get(name, 0)))

        ready = sum(
            1 for plan in self.plans if plan.status == "ready"
        )

        self.organize_button.configure(
            state="normal" if ready else "disabled"
        )

        if ready:
            self.status.set(
                f"{ready} file{'s' if ready != 1 else ''} ready to organize."
            )
        else:
            self.status.set("No files are ready to organize.")

    def organize(self) -> None:
        ready = [
            plan for plan in self.plans
            if plan.status == "ready"
        ]

        if not ready:
            return

        if not messagebox.askyesno(
            APP_NAME,
            f"Organize {len(ready)} file(s)?\n\n"
            "Nothing will be deleted or overwritten.",
        ):
            return

        result = execute_cleanup(
            self.plans,
            default_log_path(),
        )

        moved = len(result["moves"])
        skipped = len(result["skipped"])
        errors = len(result["errors"])

        self.status.set(
            f"Done: {moved} moved, {skipped} skipped, {errors} errors."
        )

        messagebox.showinfo(
            APP_NAME,
            "Cleanup complete.\n\n"
            f"Moved: {moved}\n"
            f"Skipped: {skipped}\n"
            f"Errors: {errors}\n\n"
            "Undo Last Cleanup is available.",
        )

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

        restored = len(result["restored"])
        skipped = len(result["skipped"])
        errors = len(result["errors"])

        self.status.set(
            f"Undo: {restored} restored, "
            f"{skipped} skipped, {errors} errors."
        )

        messagebox.showinfo(
            APP_NAME,
            "Undo complete.\n\n"
            f"Restored: {restored}\n"
            f"Skipped: {skipped}\n"
            f"Errors: {errors}",
        )

        self.scan()


if __name__ == "__main__":
    DownloadsCleaner().mainloop()
