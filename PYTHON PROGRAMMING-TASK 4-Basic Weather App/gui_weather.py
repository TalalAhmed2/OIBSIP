"""Advanced tier: graphical weather app with forecasts and icons."""

from __future__ import annotations

import io
import threading
import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk

from weather_service import (
    WeatherBundle,
    WeatherError,
    fetch_icon_bytes,
    format_temp,
    format_wind,
    get_weather,
)

BG = "#0b1d36"
CARD = "#123056"
ACCENT = "#3d8bfd"
TEXT = "#f4f7fb"
MUTED = "#9db0c9"
DANGER = "#ff8a8a"


class WeatherApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Weather App")
        self.geometry("820x720")
        self.minsize(720, 640)
        self.configure(bg=BG)

        self.unit = "C"
        self.bundle: WeatherBundle | None = None
        self._icon_cache: dict[str, ImageTk.PhotoImage] = {}
        self._busy = False

        self._build_styles()
        self._build_layout()
        self.city_var.set("London")

    def _build_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=BG)
        style.configure("Card.TFrame", background=CARD)
        style.configure("TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 11))
        style.configure("Muted.TLabel", background=BG, foreground=MUTED, font=("Segoe UI", 10))
        style.configure("Card.TLabel", background=CARD, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("CardMuted.TLabel", background=CARD, foreground=MUTED, font=("Segoe UI", 9))
        style.configure("Title.TLabel", background=BG, foreground=TEXT, font=("Segoe UI Semibold", 22))
        style.configure("Temp.TLabel", background=BG, foreground=TEXT, font=("Segoe UI Semibold", 42))
        style.configure("Error.TLabel", background=BG, foreground=DANGER, font=("Segoe UI", 10))
        style.configure(
            "Accent.TButton",
            background=ACCENT,
            foreground="#ffffff",
            font=("Segoe UI Semibold", 11),
            padding=(14, 8),
            borderwidth=0,
        )
        style.map("Accent.TButton", background=[("active", "#5aa0ff"), ("disabled", "#33527a")])
        style.configure(
            "Toggle.TButton",
            background=CARD,
            foreground=TEXT,
            font=("Segoe UI Semibold", 10),
            padding=(10, 6),
            borderwidth=0,
        )
        style.map("Toggle.TButton", background=[("active", "#1b4270")])
        style.configure(
            "Search.TEntry",
            fieldbackground="#0f2748",
            foreground=TEXT,
            insertcolor=TEXT,
            bordercolor=ACCENT,
            lightcolor=ACCENT,
            darkcolor=ACCENT,
            padding=8,
        )

    def _build_layout(self) -> None:
        root = ttk.Frame(self, style="TFrame")
        root.pack(fill="both", expand=True, padx=24, pady=20)

        header = ttk.Frame(root, style="TFrame")
        header.pack(fill="x")
        ttk.Label(header, text="Weather", style="Title.TLabel").pack(side="left")
        self.toggle_btn = ttk.Button(
            header,
            text="°C  |  °F",
            style="Toggle.TButton",
            command=self.toggle_units,
        )
        self.toggle_btn.pack(side="right")

        search = ttk.Frame(root, style="TFrame")
        search.pack(fill="x", pady=(16, 8))
        self.city_var = tk.StringVar()
        entry = ttk.Entry(search, textvariable=self.city_var, style="Search.TEntry", font=("Segoe UI", 12))
        entry.pack(side="left", fill="x", expand=True, ipady=4)
        entry.bind("<Return>", lambda _event: self.on_search())
        ttk.Button(search, text="Get Weather", style="Accent.TButton", command=self.on_search).pack(
            side="left", padx=(10, 0)
        )

        self.error_var = tk.StringVar()
        ttk.Label(root, textvariable=self.error_var, style="Error.TLabel").pack(anchor="w", pady=(0, 8))

        current = ttk.Frame(root, style="TFrame")
        current.pack(fill="x", pady=(4, 16))

        self.icon_label = ttk.Label(current, style="TLabel")
        self.icon_label.pack(side="left", padx=(0, 16))

        details = ttk.Frame(current, style="TFrame")
        details.pack(side="left", fill="x", expand=True)
        self.place_var = tk.StringVar(value="Search for a city to begin")
        self.desc_var = tk.StringVar(value="")
        self.temp_var = tk.StringVar(value="--")
        self.meta_var = tk.StringVar(value="")
        ttk.Label(details, textvariable=self.place_var, style="TLabel", font=("Segoe UI Semibold", 16)).pack(anchor="w")
        ttk.Label(details, textvariable=self.desc_var, style="Muted.TLabel").pack(anchor="w")
        ttk.Label(details, textvariable=self.temp_var, style="Temp.TLabel").pack(anchor="w")
        ttk.Label(details, textvariable=self.meta_var, style="Muted.TLabel").pack(anchor="w")

        ttk.Label(root, text="Next 6 hours", style="TLabel").pack(anchor="w")
        self.hourly_frame = ttk.Frame(root, style="TFrame")
        self.hourly_frame.pack(fill="x", pady=(8, 16))

        ttk.Label(root, text="Next 5 days", style="TLabel").pack(anchor="w")
        self.daily_frame = ttk.Frame(root, style="TFrame")
        self.daily_frame.pack(fill="both", expand=True, pady=(8, 0))

        self.status_var = tk.StringVar(value="Enter a city or ZIP code, then click Get Weather.")
        ttk.Label(root, textvariable=self.status_var, style="Muted.TLabel").pack(anchor="w", pady=(12, 0))

    def toggle_units(self) -> None:
        self.unit = "F" if self.unit == "C" else "C"
        other = "C" if self.unit == "F" else "F"
        self.toggle_btn.configure(text=f"°{self.unit}  |  °{other}")
        if self.bundle:
            self._render(self.bundle)

    def on_search(self) -> None:
        if self._busy:
            return
        city = self.city_var.get()
        self.error_var.set("")
        self.status_var.set("Fetching weather...")
        self._busy = True
        threading.Thread(target=self._load_weather, args=(city,), daemon=True).start()

    def _load_weather(self, city: str) -> None:
        try:
            bundle = get_weather(city)
            icons = {bundle.current.icon}
            icons.update(point.icon for point in bundle.hourly)
            icons.update(point.icon for point in bundle.daily)
            images = {code: fetch_icon_bytes(code) for code in icons}
            self.after(0, lambda: self._on_success(bundle, images))
        except WeatherError as exc:
            message = str(exc)
            self.after(0, lambda: self._on_error(message))
        except Exception:
            self.after(0, lambda: self._on_error("Something went wrong. Please try again."))

    def _on_error(self, message: str) -> None:
        self._busy = False
        self.error_var.set(message)
        self.status_var.set("Could not load weather.")

    def _on_success(self, bundle: WeatherBundle, images: dict[str, bytes]) -> None:
        self._busy = False
        self.bundle = bundle
        for code, payload in images.items():
            large = self._to_photo(payload, 84)
            small = self._to_photo(payload, 48)
            if large is not None:
                self._icon_cache[f"{code}_lg"] = large
            if small is not None:
                self._icon_cache[f"{code}_sm"] = small
        self._render(bundle)
        self.status_var.set(f"Updated {bundle.current.fetched_at.strftime('%I:%M %p')}")

    def _to_photo(self, payload: bytes, size: int) -> ImageTk.PhotoImage | None:
        if not payload:
            return None
        image = Image.open(io.BytesIO(payload)).convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(image)

    def _render(self, bundle: WeatherBundle) -> None:
        current = bundle.current
        place = f"{current.city}, {current.country}".strip().rstrip(",")
        self.place_var.set(place)
        self.desc_var.set(current.description)
        both = f"{format_temp(current.temp_c, 'C')}   /   {format_temp(current.temp_c, 'F')}"
        self.temp_var.set(format_temp(current.temp_c, self.unit))
        self.meta_var.set(
            f"Humidity {current.humidity}%    ·    Wind {format_wind(current.wind_ms, self.unit)}    ·    {both}"
        )
        icon = self._icon_cache.get(f"{current.icon}_lg")
        self.icon_label.configure(image=icon if icon else "", text="" if icon else "☁")

        for child in self.hourly_frame.winfo_children():
            child.destroy()
        for point in bundle.hourly:
            card = tk.Frame(self.hourly_frame, bg=CARD, padx=10, pady=10)
            card.pack(side="left", fill="both", expand=True, padx=(0, 8))
            tk.Label(card, text=point.time.strftime("%I %p").lstrip("0"), bg=CARD, fg=MUTED, font=("Segoe UI", 9)).pack()
            small = self._icon_cache.get(f"{point.icon}_sm")
            tk.Label(card, image=small if small else "", text="" if small else "·", bg=CARD, fg=TEXT).pack()
            tk.Label(
                card,
                text=format_temp(point.temp_c, self.unit),
                bg=CARD,
                fg=TEXT,
                font=("Segoe UI Semibold", 11),
            ).pack()
            tk.Label(card, text=point.description, bg=CARD, fg=MUTED, font=("Segoe UI", 8), wraplength=90).pack()

        for child in self.daily_frame.winfo_children():
            child.destroy()
        for point in bundle.daily:
            row = tk.Frame(self.daily_frame, bg=CARD, padx=12, pady=10)
            row.pack(fill="x", pady=(0, 8))
            tk.Label(
                row,
                text=point.date.strftime("%A"),
                bg=CARD,
                fg=TEXT,
                font=("Segoe UI Semibold", 11),
                width=12,
                anchor="w",
            ).pack(side="left")
            small = self._icon_cache.get(f"{point.icon}_sm")
            tk.Label(row, image=small if small else "", text="" if small else "·", bg=CARD, fg=TEXT).pack(side="left", padx=8)
            tk.Label(row, text=point.description, bg=CARD, fg=MUTED, font=("Segoe UI", 10), anchor="w").pack(
                side="left", fill="x", expand=True
            )
            temps = f"{format_temp(point.max_c, self.unit)}   {format_temp(point.min_c, self.unit)}"
            tk.Label(row, text=temps, bg=CARD, fg=TEXT, font=("Segoe UI", 11)).pack(side="right")


def main() -> None:
    app = WeatherApp()
    app.mainloop()


if __name__ == "__main__":
    main()
