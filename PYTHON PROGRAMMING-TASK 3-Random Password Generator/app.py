"""Advanced-tier Tkinter GUI for the random password generator."""

from __future__ import annotations

import tkinter as tk
from collections import deque
from tkinter import messagebox, ttk

from core import (
    MAX_LENGTH,
    MIN_CHAR_TYPES,
    MIN_LENGTH,
    PasswordOptions,
    generate_password,
    password_strength,
)

HISTORY_LIMIT = 5

BG = "#0f172a"
PANEL = "#1e293b"
BORDER = "#334155"
TEXT = "#f8fafc"
MUTED = "#94a3b8"
ACCENT = "#22d3ee"
ACCENT_DIM = "#0891b2"
WEAK = "#f87171"
MEDIUM = "#fbbf24"
STRONG = "#34d399"


def copy_to_clipboard(text: str, widget: tk.Misc | None = None) -> None:
    try:
        import pyperclip

        pyperclip.copy(text)
        return
    except Exception:
        pass

    target = widget or tk._default_root
    if target is not None:
        target.clipboard_clear()
        target.clipboard_append(text)
        target.update_idletasks()


class PasswordGeneratorApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Random Password Generator")
        self.geometry("560x720")
        self.minsize(500, 680)
        self.configure(bg=BG)
        self.resizable(True, True)

        self.length_var = tk.IntVar(value=16)
        self.upper_var = tk.BooleanVar(value=True)
        self.lower_var = tk.BooleanVar(value=True)
        self.numbers_var = tk.BooleanVar(value=True)
        self.symbols_var = tk.BooleanVar(value=True)
        self.ambiguous_var = tk.BooleanVar(value=False)
        self.password_var = tk.StringVar(value="")
        self.strength_label_var = tk.StringVar(value="Set options, then generate")
        self.status_var = tk.StringVar(value="Ready")
        self.history: deque[str] = deque(maxlen=HISTORY_LIMIT)

        self._build_styles()
        self._build_ui()
        self._refresh_strength_preview()

    def _build_styles(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TFrame", background=BG)
        style.configure("Card.TFrame", background=PANEL)
        style.configure(
            "Title.TLabel",
            background=BG,
            foreground=TEXT,
            font=("Segoe UI", 20, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background=BG,
            foreground=MUTED,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Card.TLabel",
            background=PANEL,
            foreground=TEXT,
            font=("Segoe UI", 11),
        )
        style.configure(
            "Muted.TLabel",
            background=PANEL,
            foreground=MUTED,
            font=("Segoe UI", 9),
        )
        style.configure(
            "Password.TLabel",
            background=PANEL,
            foreground=ACCENT,
            font=("Consolas", 14, "bold"),
        )
        style.configure(
            "Status.TLabel",
            background=BG,
            foreground=MUTED,
            font=("Segoe UI", 9),
        )
        style.configure(
            "Accent.TButton",
            font=("Segoe UI", 11, "bold"),
            padding=8,
        )
        style.configure("TButton", font=("Segoe UI", 10), padding=6)
        style.configure(
            "TCheckbutton",
            background=PANEL,
            foreground=TEXT,
            font=("Segoe UI", 10),
        )
        style.map(
            "TCheckbutton",
            background=[("active", PANEL)],
            foreground=[("active", TEXT)],
        )
        style.configure(
            "Cyan.Horizontal.TScale",
            background=PANEL,
            troughcolor=BORDER,
        )
        style.configure(
            "TSpinbox",
            fieldbackground="#0b1220",
            background=PANEL,
            foreground=TEXT,
            arrowcolor=TEXT,
        )

    def _build_ui(self) -> None:
        outer = ttk.Frame(self, padding=20)
        outer.pack(fill=tk.BOTH, expand=True)

        ttk.Label(outer, text="Random Password Generator", style="Title.TLabel").pack(
            anchor=tk.W
        )
        ttk.Label(
            outer,
            text="Cryptographically secure passwords with your rules.",
            style="Subtitle.TLabel",
        ).pack(anchor=tk.W, pady=(0, 16))

        length_card = self._card(outer)
        ttk.Label(length_card, text="Length", style="Card.TLabel").pack(anchor=tk.W)
        ttk.Label(
            length_card,
            text=f"Minimum {MIN_LENGTH} characters. Use the slider or spinbox.",
            style="Muted.TLabel",
        ).pack(anchor=tk.W, pady=(0, 8))

        controls = ttk.Frame(length_card, style="Card.TFrame")
        controls.pack(fill=tk.X)

        self.length_scale = ttk.Scale(
            controls,
            from_=MIN_LENGTH,
            to=MAX_LENGTH,
            orient=tk.HORIZONTAL,
            variable=self.length_var,
            command=self._on_length_scale,
            style="Cyan.Horizontal.TScale",
        )
        self.length_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        self.length_spin = ttk.Spinbox(
            controls,
            from_=MIN_LENGTH,
            to=MAX_LENGTH,
            textvariable=self.length_var,
            width=5,
            command=self._refresh_strength_preview,
        )
        self.length_spin.pack(side=tk.RIGHT)
        self.length_spin.bind("<KeyRelease>", lambda _e: self._refresh_strength_preview())
        self.length_spin.bind("<FocusOut>", lambda _e: self._refresh_strength_preview())

        types_card = self._card(outer)
        ttk.Label(types_card, text="Character types", style="Card.TLabel").pack(
            anchor=tk.W
        )
        ttk.Label(
            types_card,
            text="Choose at least two. Each selected type is guaranteed in the password.",
            style="Muted.TLabel",
        ).pack(anchor=tk.W, pady=(0, 8))

        for text, var in (
            ("Uppercase letters (A–Z)", self.upper_var),
            ("Lowercase letters (a–z)", self.lower_var),
            ("Numbers (0–9)", self.numbers_var),
            ("Symbols (!@#$%^&*…)", self.symbols_var),
        ):
            ttk.Checkbutton(
                types_card,
                text=text,
                variable=var,
                command=self._refresh_strength_preview,
            ).pack(anchor=tk.W, pady=2)

        extras = self._card(outer)
        ttk.Checkbutton(
            extras,
            text="Exclude ambiguous characters (0, O, o, l, 1, I)",
            variable=self.ambiguous_var,
            command=self._refresh_strength_preview,
        ).pack(anchor=tk.W)

        result = self._card(outer)
        ttk.Label(result, text="Generated password", style="Card.TLabel").pack(
            anchor=tk.W
        )
        self.password_display = ttk.Label(
            result,
            textvariable=self.password_var,
            style="Password.TLabel",
            wraplength=480,
        )
        self.password_display.pack(anchor=tk.W, pady=(6, 10))

        ttk.Label(result, text="Strength", style="Muted.TLabel").pack(anchor=tk.W)
        bar_wrap = tk.Frame(result, bg=PANEL)
        bar_wrap.pack(fill=tk.X, pady=(4, 4))
        self.strength_canvas = tk.Canvas(
            bar_wrap, height=12, bg=BORDER, highlightthickness=0, bd=0
        )
        self.strength_canvas.pack(fill=tk.X)
        ttk.Label(
            result, textvariable=self.strength_label_var, style="Card.TLabel"
        ).pack(anchor=tk.W, pady=(4, 0))

        actions = ttk.Frame(outer)
        actions.pack(fill=tk.X, pady=(4, 8))
        ttk.Button(
            actions,
            text="Generate password",
            style="Accent.TButton",
            command=self.generate,
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 6))
        ttk.Button(actions, text="Copy to clipboard", command=self.copy_current).pack(
            side=tk.LEFT, expand=True, fill=tk.X, padx=(6, 0)
        )

        history_card = self._card(outer)
        ttk.Label(
            history_card,
            text="Session history (last 5 — not saved to disk)",
            style="Card.TLabel",
        ).pack(anchor=tk.W, pady=(0, 6))
        self.history_list = tk.Listbox(
            history_card,
            height=5,
            bg="#0b1220",
            fg=TEXT,
            selectbackground=ACCENT_DIM,
            selectforeground=TEXT,
            highlightthickness=0,
            bd=0,
            font=("Consolas", 10),
            activestyle="none",
        )
        self.history_list.pack(fill=tk.BOTH, expand=True)
        self.history_list.bind("<Double-Button-1>", lambda _e: self._copy_history_item())

        ttk.Label(outer, textvariable=self.status_var, style="Status.TLabel").pack(
            anchor=tk.W, pady=(8, 0)
        )
        self.strength_canvas.bind("<Configure>", lambda _e: self._refresh_strength_preview())

    def _card(self, parent: tk.Widget) -> ttk.Frame:
        wrap = tk.Frame(parent, bg=BORDER)
        wrap.pack(fill=tk.X, pady=(0, 12))
        inner = ttk.Frame(wrap, style="Card.TFrame", padding=12)
        inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        return inner

    def _on_length_scale(self, _value: str) -> None:
        self.length_var.set(int(float(self.length_var.get())))
        self._refresh_strength_preview()

    def _current_options(self) -> PasswordOptions:
        try:
            length = int(self.length_var.get())
        except (tk.TclError, ValueError):
            raise ValueError("Enter a valid password length.") from None
        return PasswordOptions(
            length=length,
            uppercase=self.upper_var.get(),
            lowercase=self.lower_var.get(),
            numbers=self.numbers_var.get(),
            symbols=self.symbols_var.get(),
            exclude_ambiguous=self.ambiguous_var.get(),
        )

    def _refresh_strength_preview(self) -> None:
        try:
            options = self._current_options()
            label, percent = password_strength(options)
            self._draw_strength_bar(percent, label)
            self.strength_label_var.set(f"{label}  ·  estimated from length and diversity")
        except ValueError:
            self._draw_strength_bar(0, "Weak")
            types_on = sum(
                [
                    self.upper_var.get(),
                    self.lower_var.get(),
                    self.numbers_var.get(),
                    self.symbols_var.get(),
                ]
            )
            if types_on < MIN_CHAR_TYPES:
                self.strength_label_var.set("Select at least two character types")
            else:
                self.strength_label_var.set("Adjust length or character types")

    def _draw_strength_bar(self, percent: int, label: str) -> None:
        canvas = self.strength_canvas
        canvas.delete("all")
        width = max(canvas.winfo_width(), 1)
        color = {"Weak": WEAK, "Medium": MEDIUM, "Strong": STRONG}.get(label, MUTED)
        fill_w = max(0, int(width * (percent / 100)))
        canvas.create_rectangle(0, 0, fill_w, 12, fill=color, outline="")

    def generate(self) -> None:
        try:
            options = self._current_options()
            password = generate_password(options)
        except ValueError as exc:
            messagebox.showerror("Invalid options", str(exc))
            self.status_var.set(str(exc))
            return

        self.password_var.set(password)
        label, percent = password_strength(options)
        self._draw_strength_bar(percent, label)
        self.strength_label_var.set(f"{label}  ·  {options.length} characters")

        self.history.appendleft(password)
        self._refresh_history()

        copy_to_clipboard(password, self)
        self.status_var.set("Password generated and copied to clipboard.")

    def copy_current(self) -> None:
        password = self.password_var.get().strip()
        if not password:
            messagebox.showinfo("Nothing to copy", "Generate a password first.")
            return
        copy_to_clipboard(password, self)
        self.status_var.set("Copied to clipboard.")

    def _refresh_history(self) -> None:
        self.history_list.delete(0, tk.END)
        for item in self.history:
            self.history_list.insert(tk.END, item)

    def _copy_history_item(self) -> None:
        selection = self.history_list.curselection()
        if not selection:
            return
        password = self.history_list.get(selection[0])
        copy_to_clipboard(password, self)
        self.status_var.set("History item copied to clipboard.")


def run_gui() -> None:
    app = PasswordGeneratorApp()
    app.mainloop()


if __name__ == "__main__":
    run_gui()
