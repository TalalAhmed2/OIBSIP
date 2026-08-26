"""Shared OpenWeatherMap client used by the CLI and GUI apps."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from config import API_KEY, BASE_URL, ICON_URL, REQUEST_TIMEOUT


class WeatherError(Exception):
    """User-facing weather lookup failure."""


@dataclass
class CurrentWeather:
    city: str
    country: str
    description: str
    icon: str
    temp_c: float
    humidity: int
    wind_ms: float
    timezone_offset: int
    fetched_at: datetime


@dataclass
class HourPoint:
    time: datetime
    temp_c: float
    description: str
    icon: str


@dataclass
class DayPoint:
    date: datetime
    min_c: float
    max_c: float
    description: str
    icon: str


@dataclass
class WeatherBundle:
    current: CurrentWeather
    hourly: list[HourPoint] = field(default_factory=list)
    daily: list[DayPoint] = field(default_factory=list)


def _require_api_key() -> str:
    key = (API_KEY or "").strip()
    if not key or key == "YOUR_API_KEY_HERE":
        raise WeatherError(
            "Invalid API key. Open config.py and paste your OpenWeatherMap key, "
            "or set the OPENWEATHER_API_KEY environment variable."
        )
    return key


def validate_location(raw: str) -> str:
    location = (raw or "").strip()
    if not location:
        raise WeatherError("Please enter a city name or ZIP code.")
    return location


def _location_params(location: str) -> dict[str, str]:
    """Use ZIP lookup for numeric postal codes; otherwise search by city name."""
    compact = location.replace(" ", "")
    if compact.replace(",", "").replace("-", "").isdigit() or (
        "," in compact and compact.split(",")[0].replace("-", "").isdigit()
    ):
        zip_value = compact
        if "," not in zip_value:
            zip_value = f"{zip_value},US"
        return {"zip": zip_value}
    return {"q": location}


def _request(endpoint: str, location: str) -> dict[str, Any]:
    key = _require_api_key()
    params = {
        **_location_params(location),
        "appid": key,
        "units": "metric",
    }
    url = f"{BASE_URL}/{endpoint}"
    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
    except requests.Timeout:
        raise WeatherError("Network timeout. Check your connection and try again.") from None
    except requests.RequestException:
        raise WeatherError("Network error. Could not reach the weather service.") from None

    if response.status_code == 401:
        raise WeatherError("Invalid API key. Check the key in config.py.")
    if response.status_code == 404:
        raise WeatherError("City not found. Try another city name or ZIP code.")
    if response.status_code == 429:
        raise WeatherError("Too many requests. Wait a moment and try again.")
    if not response.ok:
        raise WeatherError(f"Weather service error (HTTP {response.status_code}).")

    try:
        return response.json()
    except ValueError:
        raise WeatherError("Could not parse the weather response.") from None


def c_to_f(temp_c: float) -> float:
    return temp_c * 9 / 5 + 32


def format_temp(temp_c: float, unit: str) -> str:
    if unit.upper() == "F":
        return f"{c_to_f(temp_c):.1f}°F"
    return f"{temp_c:.1f}°C"


def format_wind(wind_ms: float, unit: str) -> str:
    if unit.upper() == "F":
        mph = wind_ms * 2.23694
        return f"{mph:.1f} mph"
    kmh = wind_ms * 3.6
    return f"{kmh:.1f} km/h"


def icon_url(icon_code: str) -> str:
    return ICON_URL.format(icon=icon_code)


def fetch_icon_bytes(icon_code: str) -> bytes:
    try:
        response = requests.get(icon_url(icon_code), timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.content
    except requests.RequestException:
        return b""


def _interpolate(start: float, end: float, fraction: float) -> float:
    return start + (end - start) * fraction


def _build_hourly(forecast_list: list[dict[str, Any]], tzinfo: timezone) -> list[HourPoint]:
    """Build 6 hourly points from the 3-hour forecast by interpolating temperature."""
    points: list[tuple[datetime, float, str, str]] = []
    for item in forecast_list:
        when = datetime.fromtimestamp(item["dt"], tz=tzinfo)
        points.append(
            (
                when,
                float(item["main"]["temp"]),
                str(item["weather"][0]["description"]).title(),
                str(item["weather"][0]["icon"]),
            )
        )
    if not points:
        return []

    now = datetime.now(tzinfo).replace(minute=0, second=0, microsecond=0)
    if datetime.now(tzinfo).minute > 0:
        now += timedelta(hours=1)
    hourly: list[HourPoint] = []
    for hour_offset in range(6):
        target = now + timedelta(hours=hour_offset)
        before = points[0]
        after = points[-1]
        for i, point in enumerate(points):
            if point[0] <= target:
                before = point
                after = points[min(i + 1, len(points) - 1)]
            else:
                after = point
                break
        span = (after[0] - before[0]).total_seconds()
        fraction = 0.0 if span <= 0 else min(1.0, max(0.0, (target - before[0]).total_seconds() / span))
        nearest = before if fraction < 0.5 else after
        hourly.append(
            HourPoint(
                time=target.replace(minute=0, second=0, microsecond=0),
                temp_c=_interpolate(before[1], after[1], fraction),
                description=nearest[2],
                icon=nearest[3],
            )
        )
    return hourly


def _build_daily(forecast_list: list[dict[str, Any]], tzinfo: timezone) -> list[DayPoint]:
    buckets: dict[str, list[dict[str, Any]]] = {}
    for item in forecast_list:
        when = datetime.fromtimestamp(item["dt"], tz=tzinfo)
        key = when.date().isoformat()
        buckets.setdefault(key, []).append(item)

    daily: list[DayPoint] = []
    for key in sorted(buckets)[:5]:
        items = buckets[key]
        temps = [float(i["main"]["temp"]) for i in items]
        # Prefer a midday icon when available.
        midday = min(
            items,
            key=lambda i: abs(datetime.fromtimestamp(i["dt"], tz=tzinfo).hour - 12),
        )
        weather = midday["weather"][0]
        daily.append(
            DayPoint(
                date=datetime.fromisoformat(key).replace(tzinfo=tzinfo),
                min_c=min(temps),
                max_c=max(temps),
                description=str(weather["description"]).title(),
                icon=str(weather["icon"]),
            )
        )
    return daily


def get_weather(location: str) -> WeatherBundle:
    location = validate_location(location)
    current_raw = _request("weather", location)
    forecast_raw = _request("forecast", location)

    weather = current_raw["weather"][0]
    offset = int(current_raw.get("timezone", 0))
    tzinfo = timezone(timedelta(seconds=offset))

    current = CurrentWeather(
        city=str(current_raw.get("name") or location),
        country=str(current_raw.get("sys", {}).get("country", "")),
        description=str(weather.get("description", "Unknown")).title(),
        icon=str(weather.get("icon", "01d")),
        temp_c=float(current_raw["main"]["temp"]),
        humidity=int(current_raw["main"]["humidity"]),
        wind_ms=float(current_raw.get("wind", {}).get("speed", 0.0)),
        timezone_offset=offset,
        fetched_at=datetime.now(tzinfo),
    )

    forecast_list = forecast_raw.get("list", [])
    return WeatherBundle(
        current=current,
        hourly=_build_hourly(forecast_list, tzinfo),
        daily=_build_daily(forecast_list, tzinfo),
    )
