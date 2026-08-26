"""Tkinter BMI calculator with multi-user history and trend charts."""

from __future__ import annotations

import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from bmi_core import CATEGORY_COLORS, BMIValidationError, calculate_from_text
from storage import BMIStorage, StorageError


class BMICalculatorApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("BMI Calculator")
        self.geometry("980x720")
        self.minsize(860, 640)
        self.configure(bg="#F4F6F8")

        try:
            self.storage = BMIStorage()
        except StorageError as exc:
            messagebox.showerror("Database error", str(exc))
            self.storage = None

        self._last_result = None
        self._build_style()
        self._build_layout()
        self._refresh_users()
        self._refresh_history()

    def _build_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background="#F4F6F8")
        style.configure("Card.TFrame", background="#FFFFFF")
        style.configure("TLabel", background="#F4F6F8", font=("Segoe UI", 10))
        style.configure("Card.TLabel", background="#FFFFFF", font=("Segoe UI", 10))
        style.configure("Title.TLabel", background="#F4F6F8", font=("Segoe UI", 18, "bold"))
        style.configure("Result.TLabel", background="#FFFFFF", font=("Segoe UI", 16, "bold"))
        style.configure("TButton", font=("Segoe UI", 10), padding=6)
        style.configure("TLabelframe", background="#FFFFFF")
        style.configure("TLabelframe.Label", background="#FFFFFF", font=("Segoe UI", 10, "bold"))

    def _build_layout(self) -> None:
        header = ttk.Label(self, text="BMI Calculator", style="Title.TLabel")
        header.pack(anchor="w", padx=20, pady=(16, 4))
        ttk.Label(
            self,
            text="Calculate BMI, save records for named users, and view BMI trends over time.",
        ).pack(anchor="w", padx=20, pady=(0, 8))

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, padx=16, pady=8)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        left = ttk.Frame(body, style="Card.TFrame")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        right = ttk.Frame(body)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        form = ttk.LabelFrame(left, text="New measurement", padding=12)
        form.pack(fill="x", padx=12, pady=12)

        ttk.Label(form, text="User name", style="Card.TLabel").grid(row=0, column=0, sticky="w", pady=4)
        self.user_var = tk.StringVar()
        self.user_combo = ttk.Combobox(form, textvariable=self.user_var, width=28)
        self.user_combo.grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(form, text="Weight (kg)", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=4)
        self.weight_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.weight_var, width=30).grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(form, text="Height (m)", style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=4)
        self.height_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.height_var, width=30).grid(row=2, column=1, sticky="ew", pady=4)

        form.columnconfigure(1, weight=1)

        buttons = ttk.Frame(form, style="Card.TFrame")
        buttons.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        ttk.Button(buttons, text="Calculate", command=self.calculate).pack(side="left")
        ttk.Button(buttons, text="Save record", command=self.save_record).pack(side="left", padx=8)

        result_box = ttk.LabelFrame(left, text="Result", padding=12)
        result_box.pack(fill="x", padx=12, pady=(0, 12))
        self.result_label = ttk.Label(
            result_box,
            text="Enter weight and height, then click Calculate.",
            style="Result.TLabel",
            wraplength=320,
        )
        self.result_label.pack(anchor="w")
        self.detail_label = ttk.Label(result_box, text="", style="Card.TLabel")
        self.detail_label.pack(anchor="w", pady=(8, 0))

        categories = ttk.LabelFrame(left, text="BMI categories", padding=12)
        categories.pack(fill="x", padx=12, pady=(0, 12))
        for name, rule in (
            ("Underweight", "< 18.5"),
            ("Normal", "18.5 – 24.9"),
            ("Overweight", "25.0 – 29.9"),
            ("Obese", "≥ 30.0"),
        ):
            row = ttk.Frame(categories, style="Card.TFrame")
            row.pack(fill="x", pady=2)
            swatch = tk.Canvas(row, width=14, height=14, highlightthickness=0, bg="#FFFFFF")
            swatch.pack(side="left", padx=(0, 8))
            swatch.create_rectangle(0, 0, 14, 14, fill=CATEGORY_COLORS[name], outline=CATEGORY_COLORS[name])
            ttk.Label(row, text=f"{name}: {rule}", style="Card.TLabel").pack(side="left")

        history_frame = ttk.LabelFrame(right, text="Saved records", padding=8)
        history_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        history_frame.columnconfigure(0, weight=1)

        filter_row = ttk.Frame(history_frame)
        filter_row.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ttk.Label(filter_row, text="Show history for:").pack(side="left")
        self.filter_var = tk.StringVar(value="All users")
        self.filter_combo = ttk.Combobox(filter_row, textvariable=self.filter_var, state="readonly", width=24)
        self.filter_combo.pack(side="left", padx=8)
        self.filter_combo.bind("<<ComboboxSelected>>", lambda _e: self._refresh_history())
        ttk.Button(filter_row, text="Show trend graph", command=self.show_trend).pack(side="right")

        columns = ("user", "date", "weight", "height", "bmi", "category")
        self.tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=8)
        headings = {
            "user": "User",
            "date": "Date",
            "weight": "Weight (kg)",
            "height": "Height (m)",
            "bmi": "BMI",
            "category": "Category",
        }
        widths = {"user": 110, "date": 160, "weight": 90, "height": 90, "bmi": 70, "category": 110}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="center")
        self.tree.grid(row=1, column=0, sticky="nsew")
        history_frame.rowconfigure(1, weight=1)
        scroll = ttk.Scrollbar(history_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.grid(row=1, column=1, sticky="ns")

        chart_frame = ttk.LabelFrame(right, text="BMI trend", padding=8)
        chart_frame.grid(row=1, column=0, sticky="nsew")
        chart_frame.columnconfigure(0, weight=1)
        chart_frame.rowconfigure(0, weight=1)

        self.figure = Figure(figsize=(6.4, 3.2), dpi=100)
        self.axes = self.figure.add_subplot(111)
        self.axes.set_title("Select a user and click Show trend graph")
        self.axes.set_ylabel("BMI")
        self.figure.tight_layout()
        self.canvas = FigureCanvasTkAgg(self.figure, master=chart_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

    def _require_storage(self) -> BMIStorage | None:
        if self.storage is None:
            messagebox.showerror(
                "Database error",
                "The BMI database is not available. Restart the app after fixing file permissions.",
            )
            return None
        return self.storage

    def calculate(self) -> None:
        try:
            result = calculate_from_text(self.weight_var.get(), self.height_var.get())
        except BMIValidationError as exc:
            self._last_result = None
            self.result_label.configure(text=str(exc), foreground="#C62828")
            self.detail_label.configure(text="")
            return

        self._last_result = result
        self.result_label.configure(
            text=f"BMI: {result.bmi:.2f}  ·  {result.category}",
            foreground=result.color,
        )
        self.detail_label.configure(
            text=f"Weight {result.weight:g} kg  ·  Height {result.height:g} m"
        )

    def save_record(self) -> None:
        storage = self._require_storage()
        if storage is None:
            return

        if self._last_result is None:
            self.calculate()
        if self._last_result is None:
            return

        name = self.user_var.get().strip()
        if not name:
            messagebox.showerror("Missing user name", "Enter a user name before saving a record.")
            return

        try:
            storage.save_record(
                user_name=name,
                weight=self._last_result.weight,
                height=self._last_result.height,
                bmi=self._last_result.bmi,
                category=self._last_result.category,
            )
        except StorageError as exc:
            messagebox.showerror("Database error", str(exc))
            return

        self._refresh_users(select_name=name)
        self._refresh_history()
        messagebox.showinfo("Saved", f"BMI record saved for {name}.")

    def show_trend(self) -> None:
        storage = self._require_storage()
        if storage is None:
            return

        selected = self.filter_var.get()
        users = {name: user_id for user_id, name in self._safe_users()}
        if selected == "All users" or selected not in users:
            name = self.user_var.get().strip()
            if name in users:
                selected = name
            elif len(users) == 1:
                selected = next(iter(users))
            else:
                messagebox.showinfo(
                    "Choose a user",
                    "Select a named user in the history filter (not 'All users') to view a BMI trend.",
                )
                return

        try:
            records = storage.records_for_user(users[selected])
        except StorageError as exc:
            messagebox.showerror("Database error", str(exc))
            return

        self.axes.clear()
        if not records:
            self.axes.set_title(f"No saved records for {selected}")
            self.axes.set_ylabel("BMI")
            self.canvas.draw_idle()
            return

        dates = [self._parse_date(record.recorded_at) for record in records]
        values = [record.bmi for record in records]
        self.axes.plot(dates, values, marker="o", color="#1565C0", linewidth=2)
        self.axes.axhline(18.5, color="#1565C0", linestyle="--", linewidth=0.8, alpha=0.6)
        self.axes.axhline(25.0, color="#2E7D32", linestyle="--", linewidth=0.8, alpha=0.6)
        self.axes.axhline(30.0, color="#C62828", linestyle="--", linewidth=0.8, alpha=0.6)
        self.axes.set_title(f"BMI trend for {selected}")
        self.axes.set_ylabel("BMI")
        self.axes.grid(True, alpha=0.3)
        self.figure.autofmt_xdate()
        self.figure.tight_layout()
        self.canvas.draw_idle()

    def _safe_users(self) -> list[tuple[int, str]]:
        if self.storage is None:
            return []
        try:
            return self.storage.list_users()
        except StorageError as exc:
            messagebox.showerror("Database error", str(exc))
            return []

    def _refresh_users(self, select_name: str | None = None) -> None:
        names = [name for _user_id, name in self._safe_users()]
        self.user_combo["values"] = names
        filter_values = ["All users", *names]
        self.filter_combo["values"] = filter_values
        if select_name:
            self.user_var.set(select_name)
            self.filter_var.set(select_name)
        elif self.filter_var.get() not in filter_values:
            self.filter_var.set("All users")

    def _refresh_history(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        if self.storage is None:
            return
        try:
            users = {name: user_id for user_id, name in self.storage.list_users()}
            selected = self.filter_var.get()
            if selected != "All users" and selected in users:
                records = self.storage.records_for_user(users[selected])
            else:
                records = self.storage.all_records()
        except StorageError as exc:
            messagebox.showerror("Database error", str(exc))
            return

        for record in records:
            self.tree.insert(
                "",
                "end",
                values=(
                    record.user_name,
                    self._display_date(record.recorded_at),
                    f"{record.weight:g}",
                    f"{record.height:g}",
                    f"{record.bmi:.2f}",
                    record.category,
                ),
            )

    @staticmethod
    def _parse_date(value: str) -> datetime:
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return datetime.now()

    @staticmethod
    def _display_date(value: str) -> str:
        try:
            return datetime.fromisoformat(value).strftime("%Y-%m-%d %H:%M")
        except ValueError:
            return value


def run_gui() -> None:
    app = BMICalculatorApp()
    app.mainloop()
