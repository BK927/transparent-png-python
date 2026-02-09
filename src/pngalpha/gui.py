"""
Drag-and-drop GUI for pngalpha.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

from PIL import Image, ImageTk
from pngalpha.core import extract_alpha_two_pass

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD

    BaseTk = TkinterDnD.Tk
    DND_AVAILABLE = True
except ImportError:
    DND_FILES = "DND_Files"
    BaseTk = tk.Tk
    DND_AVAILABLE = False


IMAGE_FILE_TYPES = [
    ("Image files", "*.png *.jpg *.jpeg *.bmp *.webp *.tif *.tiff"),
    ("All files", "*.*"),
]
SUPPORTED_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".bmp",
    ".webp",
    ".tif",
    ".tiff",
}

COLORS = {
    "window_bg": "#f3f5f7",
    "card_bg": "#ffffff",
    "card_border": "#d7dde4",
    "title_fg": "#1f2a37",
    "subtitle_fg": "#5b6673",
    "accent": "#1c6dd0",
    "btn_fg": "#ffffff",
    "drop_bg": "#f8fafc",
    "drop_fg": "#6a7480",
    "drop_border": "#d1d7de",
    "drop_hover_bg": "#ecf4ff",
    "drop_hover_border": "#6da3ea",
    "drop_ready_bg": "#eef9f1",
    "drop_ready_border": "#52a56f",
    "status_idle_bg": "#eef2f6",
    "status_idle_fg": "#5b6673",
    "status_run_bg": "#eaf2ff",
    "status_run_fg": "#1c6dd0",
    "status_ok_bg": "#eaf8ef",
    "status_ok_fg": "#2c8f52",
    "status_err_bg": "#fdecec",
    "status_err_fg": "#b62d2d",
    "output_bg": "#f7f9fb",
    "output_fg": "#2b3642",
}


class DropBox:
    """Visual state holder for a drop target."""

    def __init__(self, target: tk.Label, button: tk.Button, placeholder_text: str) -> None:
        self.target = target
        self.button = button
        self.placeholder_text = placeholder_text
        self.preview_image: ImageTk.PhotoImage | None = None
        self.has_path = False
        self.hovered = False


class PngAlphaGui(BaseTk):
    """Main drag-and-drop application window."""

    def __init__(self) -> None:
        super().__init__()
        self.title("pngalpha - Drag and Drop")
        self.geometry("860x520")
        self.resizable(False, False)
        self.configure(bg=COLORS["window_bg"])

        self.white_path: Path | None = None
        self.black_path: Path | None = None
        self.last_output_path: Path | None = None
        self.is_processing = False

        self.output_var = tk.StringVar(value="-")
        self.status_var = tk.StringVar(value="")

        self.status_badge: tk.Label | None = None
        self.open_output_btn: tk.Button | None = None

        self.white_box: DropBox | None = None
        self.black_box: DropBox | None = None

        self._build_layout()
        self._set_status(
            "Drop white and black background images to start automatic conversion.",
            "idle",
        )

        if not DND_AVAILABLE:
            self._set_status(
                "Drag-and-drop unavailable. Install tkinterdnd2 or use Browse buttons.",
                "error",
            )
            messagebox.showwarning(
                "Drag and drop unavailable",
                "Please install tkinterdnd2 to use drag and drop.\n"
                "You can still use the Browse buttons.",
            )

    def _build_layout(self) -> None:
        container = tk.Frame(self, bg=COLORS["window_bg"], padx=18, pady=18)
        container.pack(fill="both", expand=True)

        self._build_header(container)
        self._build_drop_area(container)
        self._build_info_card(container)
        self._build_action_row(container)

    def _build_header(self, parent: tk.Widget) -> None:
        header = tk.Frame(
            parent,
            bg=COLORS["card_bg"],
            padx=16,
            pady=14,
            highlightthickness=1,
            highlightbackground=COLORS["card_border"],
        )
        header.pack(fill="x")

        tk.Label(
            header,
            text="pngalpha",
            bg=COLORS["card_bg"],
            fg=COLORS["title_fg"],
            font=("Segoe UI", 19, "bold"),
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            header,
            text="Drag two images below (white background, black background). "
            "Conversion starts automatically.",
            bg=COLORS["card_bg"],
            fg=COLORS["subtitle_fg"],
            font=("Segoe UI", 10),
            anchor="w",
        ).pack(fill="x")

    def _build_drop_area(self, parent: tk.Widget) -> None:
        drop_area = tk.Frame(parent, bg=COLORS["window_bg"])
        drop_area.pack(fill="both", expand=True, pady=(14, 10))
        drop_area.columnconfigure(0, weight=1)
        drop_area.columnconfigure(1, weight=1)
        drop_area.rowconfigure(0, weight=1)

        self.white_box = self._create_drop_box(
            parent=drop_area,
            column=0,
            title="Image on White",
            drop_handler=self._on_drop_white,
            enter_handler=self._on_drag_enter_white,
            leave_handler=self._on_drag_leave_white,
            browse_handler=self._browse_white,
            help_text="Drop white background image",
            placeholder_text="Drop white background image here",
        )
        self.black_box = self._create_drop_box(
            parent=drop_area,
            column=1,
            title="Image on Black",
            drop_handler=self._on_drop_black,
            enter_handler=self._on_drag_enter_black,
            leave_handler=self._on_drag_leave_black,
            browse_handler=self._browse_black,
            help_text="Drop black background image",
            placeholder_text="Drop black background image here",
        )

    def _build_info_card(self, parent: tk.Widget) -> None:
        info = tk.Frame(
            parent,
            bg=COLORS["card_bg"],
            padx=14,
            pady=14,
            highlightthickness=1,
            highlightbackground=COLORS["card_border"],
        )
        info.pack(fill="x", pady=(0, 10))
        info.columnconfigure(1, weight=1)
        info.columnconfigure(2, weight=0)

        tk.Label(
            info,
            text="Output",
            width=9,
            anchor="w",
            bg=COLORS["card_bg"],
            fg=COLORS["title_fg"],
            font=("Segoe UI", 10, "bold"),
        ).grid(row=0, column=0, sticky="w")

        output_entry = tk.Entry(
            info,
            textvariable=self.output_var,
            state="readonly",
            relief="flat",
            readonlybackground=COLORS["output_bg"],
            fg=COLORS["output_fg"],
            disabledforeground=COLORS["output_fg"],
            font=("Consolas", 10),
            bd=0,
        )
        output_entry.grid(row=0, column=1, sticky="ew", padx=(6, 8), ipady=7)

        self.open_output_btn = tk.Button(
            info,
            text="Open Folder",
            command=self._open_output_folder,
            bg=COLORS["status_idle_bg"],
            fg=COLORS["status_idle_fg"],
            activebackground=COLORS["status_idle_bg"],
            activeforeground=COLORS["status_idle_fg"],
            relief="flat",
            bd=0,
            padx=10,
            pady=6,
            state="disabled",
        )
        self.open_output_btn.grid(row=0, column=2, sticky="e")

        tk.Label(
            info,
            text="Status",
            width=9,
            anchor="w",
            bg=COLORS["card_bg"],
            fg=COLORS["title_fg"],
            font=("Segoe UI", 10, "bold"),
        ).grid(row=1, column=0, sticky="w", pady=(10, 0))
        self.status_badge = tk.Label(
            info,
            textvariable=self.status_var,
            anchor="w",
            padx=10,
            pady=6,
            font=("Segoe UI", 10),
            bg=COLORS["status_idle_bg"],
            fg=COLORS["status_idle_fg"],
            relief="flat",
        )
        self.status_badge.grid(row=1, column=1, columnspan=2, sticky="ew", padx=(6, 0), pady=(10, 0))

    def _build_action_row(self, parent: tk.Widget) -> None:
        action_row = tk.Frame(parent, bg=COLORS["window_bg"])
        action_row.pack(fill="x")
        tk.Button(
            action_row,
            text="Reset",
            command=self._reset,
            bg=COLORS["accent"],
            fg=COLORS["btn_fg"],
            activebackground=COLORS["accent"],
            activeforeground=COLORS["btn_fg"],
            relief="flat",
            bd=0,
            padx=16,
            pady=9,
            font=("Segoe UI", 10, "bold"),
        ).pack(side="right")

    def _create_drop_box(
        self,
        parent: tk.Widget,
        column: int,
        title: str,
        drop_handler,
        enter_handler,
        leave_handler,
        browse_handler,
        help_text: str,
        placeholder_text: str,
    ) -> DropBox:
        box = tk.Frame(
            parent,
            bg=COLORS["card_bg"],
            padx=12,
            pady=12,
            highlightthickness=1,
            highlightbackground=COLORS["card_border"],
        )
        box.grid(
            row=0,
            column=column,
            sticky="nsew",
            padx=(0 if column == 0 else 8, 0),
        )

        tk.Label(
            box,
            text=title,
            anchor="w",
            bg=COLORS["card_bg"],
            fg=COLORS["title_fg"],
            font=("Segoe UI", 11, "bold"),
        ).pack(fill="x")
        tk.Label(
            box,
            text=help_text,
            anchor="w",
            bg=COLORS["card_bg"],
            fg=COLORS["subtitle_fg"],
            font=("Segoe UI", 9),
        ).pack(fill="x", pady=(2, 8))

        target = tk.Label(
            box,
            text=placeholder_text,
            bg=COLORS["drop_bg"],
            fg=COLORS["drop_fg"],
            justify="center",
            wraplength=360,
            height=9,
            font=("Segoe UI", 10),
            highlightthickness=2,
            highlightbackground=COLORS["drop_border"],
            highlightcolor=COLORS["drop_border"],
            padx=10,
            pady=8,
        )
        target.pack(fill="both", expand=True)

        button = tk.Button(
            box,
            text="Browse...",
            command=browse_handler,
            bg=COLORS["accent"],
            fg=COLORS["btn_fg"],
            activebackground=COLORS["accent"],
            activeforeground=COLORS["btn_fg"],
            relief="flat",
            bd=0,
            padx=14,
            pady=7,
            font=("Segoe UI", 9, "bold"),
        )
        button.pack(pady=(10, 0))

        drop_box = DropBox(target=target, button=button, placeholder_text=placeholder_text)
        self._apply_drop_box_style(drop_box)

        if DND_AVAILABLE:
            self._register_drop_target(target, drop_handler, enter_handler, leave_handler)
            self._register_drop_target(box, drop_handler, enter_handler, leave_handler)

        return drop_box

    @staticmethod
    def _register_drop_target(widget: tk.Widget, drop_handler, enter_handler, leave_handler) -> None:
        widget.drop_target_register(DND_FILES)
        widget.dnd_bind("<<DropEnter>>", enter_handler)
        widget.dnd_bind("<<DropLeave>>", leave_handler)
        widget.dnd_bind("<<Drop>>", drop_handler)

    def _on_drag_enter_white(self, event) -> str:
        if self.white_box is not None:
            self.white_box.hovered = True
            self._apply_drop_box_style(self.white_box)
        return getattr(event, "action", "copy")

    def _on_drag_leave_white(self, event) -> str:
        if self.white_box is not None:
            self.white_box.hovered = False
            self._apply_drop_box_style(self.white_box)
        return getattr(event, "action", "copy")

    def _on_drag_enter_black(self, event) -> str:
        if self.black_box is not None:
            self.black_box.hovered = True
            self._apply_drop_box_style(self.black_box)
        return getattr(event, "action", "copy")

    def _on_drag_leave_black(self, event) -> str:
        if self.black_box is not None:
            self.black_box.hovered = False
            self._apply_drop_box_style(self.black_box)
        return getattr(event, "action", "copy")

    def _apply_drop_box_style(self, drop_box: DropBox) -> None:
        if drop_box.hovered:
            bg = COLORS["drop_hover_bg"]
            border = COLORS["drop_hover_border"]
            fg = COLORS["title_fg"]
        elif drop_box.has_path:
            bg = COLORS["drop_ready_bg"]
            border = COLORS["drop_ready_border"]
            fg = COLORS["title_fg"]
        else:
            bg = COLORS["drop_bg"]
            border = COLORS["drop_border"]
            fg = COLORS["drop_fg"]
        drop_box.target.configure(
            bg=bg,
            highlightbackground=border,
            highlightcolor=border,
            fg=fg,
        )

    def _set_drop_box_preview(self, drop_box: DropBox, path: Path) -> None:
        try:
            with Image.open(path) as img:
                preview = img.convert("RGBA")
                preview.thumbnail((360, 220), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(preview)
        except Exception:
            drop_box.preview_image = None
            drop_box.target.configure(
                image="",
                text="Preview unavailable\n(unsupported or broken image)",
                compound="center",
            )
            return

        drop_box.preview_image = photo
        drop_box.target.configure(image=photo, text="", compound="center")

    def _clear_drop_box_preview(self, drop_box: DropBox) -> None:
        drop_box.preview_image = None
        drop_box.target.configure(image="", text=drop_box.placeholder_text, compound="center")

    def _set_status(self, message: str, level: str) -> None:
        self.status_var.set(message)
        if self.status_badge is None:
            return
        if level == "running":
            bg = COLORS["status_run_bg"]
            fg = COLORS["status_run_fg"]
        elif level == "ok":
            bg = COLORS["status_ok_bg"]
            fg = COLORS["status_ok_fg"]
        elif level == "error":
            bg = COLORS["status_err_bg"]
            fg = COLORS["status_err_fg"]
        else:
            bg = COLORS["status_idle_bg"]
            fg = COLORS["status_idle_fg"]
        self.status_badge.configure(bg=bg, fg=fg)

    def _set_open_output_button_state(self, enabled: bool) -> None:
        if self.open_output_btn is None:
            return
        if enabled:
            self.open_output_btn.configure(
                state="normal",
                bg=COLORS["accent"],
                fg=COLORS["btn_fg"],
                activebackground=COLORS["accent"],
                activeforeground=COLORS["btn_fg"],
            )
        else:
            self.open_output_btn.configure(
                state="disabled",
                bg=COLORS["status_idle_bg"],
                fg=COLORS["status_idle_fg"],
                activebackground=COLORS["status_idle_bg"],
                activeforeground=COLORS["status_idle_fg"],
            )

    def _set_input_buttons_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        if self.white_box is not None:
            self.white_box.button.configure(state=state)
        if self.black_box is not None:
            self.black_box.button.configure(state=state)

    def _on_drop_white(self, event) -> None:
        path = self._extract_dropped_image_path(event)
        if path is None:
            return
        self.white_path = path
        if self.white_box is not None:
            self._set_drop_box_preview(self.white_box, path)
            self.white_box.has_path = True
            self.white_box.hovered = False
            self._apply_drop_box_style(self.white_box)
        self._auto_convert_if_ready()

    def _on_drop_black(self, event) -> None:
        path = self._extract_dropped_image_path(event)
        if path is None:
            return
        self.black_path = path
        if self.black_box is not None:
            self._set_drop_box_preview(self.black_box, path)
            self.black_box.has_path = True
            self.black_box.hovered = False
            self._apply_drop_box_style(self.black_box)
        self._auto_convert_if_ready()

    def _extract_dropped_image_path(self, event) -> Path | None:
        dropped_items = self.tk.splitlist(event.data)
        if not dropped_items:
            return None

        candidate = Path(dropped_items[0])
        if not candidate.is_file():
            self._set_status("Dropped item is not a file.", "error")
            messagebox.showerror("Invalid drop", f"Not a file:\n{candidate}")
            return None
        if candidate.suffix.lower() not in SUPPORTED_SUFFIXES:
            self._set_status("Unsupported image extension.", "error")
            messagebox.showerror("Invalid file type", f"Unsupported image extension:\n{candidate.suffix}")
            return None
        return candidate

    def _browse_white(self) -> None:
        selected = self._choose_image_file()
        if selected is None:
            return
        self.white_path = selected
        if self.white_box is not None:
            self._set_drop_box_preview(self.white_box, selected)
            self.white_box.has_path = True
            self._apply_drop_box_style(self.white_box)
        self._auto_convert_if_ready()

    def _browse_black(self) -> None:
        selected = self._choose_image_file()
        if selected is None:
            return
        self.black_path = selected
        if self.black_box is not None:
            self._set_drop_box_preview(self.black_box, selected)
            self.black_box.has_path = True
            self._apply_drop_box_style(self.black_box)
        self._auto_convert_if_ready()

    def _choose_image_file(self) -> Path | None:
        selected = filedialog.askopenfilename(title="Select image", filetypes=IMAGE_FILE_TYPES)
        if not selected:
            return None
        return Path(selected)

    def _open_output_folder(self) -> None:
        if self.last_output_path is None:
            return
        folder_path = self.last_output_path.parent
        if not folder_path.exists():
            return
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(folder_path))
            elif sys.platform == "darwin":
                subprocess.run(["open", str(folder_path)], check=False)
            else:
                subprocess.run(["xdg-open", str(folder_path)], check=False)
        except Exception as exc:
            messagebox.showerror("Open folder failed", str(exc))

    def _auto_convert_if_ready(self) -> None:
        if self.is_processing:
            return

        if self.white_path is None and self.black_path is None:
            self._set_status(
                "Drop white and black background images to start automatic conversion.",
                "idle",
            )
            return
        if self.white_path is None:
            self._set_status("White image is missing.", "idle")
            return
        if self.black_path is None:
            self._set_status("Black image is missing.", "idle")
            return

        output_path = self._suggest_output_path(self.white_path)
        self.last_output_path = output_path
        self.output_var.set(str(output_path))
        self._set_open_output_button_state(False)
        self._set_input_buttons_enabled(False)
        self._set_status("Processing...", "running")
        self.update_idletasks()

        self.is_processing = True
        try:
            extract_alpha_two_pass(
                str(self.white_path),
                str(self.black_path),
                str(output_path),
            )
        except Exception as exc:
            self._set_status("Conversion failed.", "error")
            messagebox.showerror("Conversion failed", str(exc))
        else:
            self._set_status(f"Done: {output_path.name}", "ok")
            self._set_open_output_button_state(True)
        finally:
            self._set_input_buttons_enabled(True)
            self.is_processing = False

    @staticmethod
    def _suggest_output_path(white_path: Path) -> Path:
        return white_path.with_name(f"{white_path.stem}_transparent.png")

    def _reset(self) -> None:
        self.white_path = None
        self.black_path = None
        self.last_output_path = None
        self.output_var.set("-")
        if self.white_box is not None:
            self._clear_drop_box_preview(self.white_box)
            self.white_box.has_path = False
            self.white_box.hovered = False
            self._apply_drop_box_style(self.white_box)
        if self.black_box is not None:
            self._clear_drop_box_preview(self.black_box)
            self.black_box.has_path = False
            self.black_box.hovered = False
            self._apply_drop_box_style(self.black_box)
        self._set_input_buttons_enabled(True)
        self._set_open_output_button_state(False)
        self._set_status(
            "Drop white and black background images to start automatic conversion.",
            "idle",
        )


def main() -> int:
    """GUI entry point."""
    app = PngAlphaGui()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
