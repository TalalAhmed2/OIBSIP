"""Beginner tier: command-line weather app."""

from weather_service import WeatherError, format_temp, format_wind, get_weather


def main() -> None:
    print("=" * 44)
    print("  Basic Weather App  -  Command Line")
    print("=" * 44)

    try:
        location = input("Enter a city name or ZIP code: ")
        bundle = get_weather(location)
    except WeatherError as exc:
        print(f"\nError: {exc}")
        return
    except KeyboardInterrupt:
        print("\nCancelled.")
        return

    current = bundle.current
    place = f"{current.city}, {current.country}".strip().rstrip(",")
    print(f"\nWeather for {place}")
    print("-" * 44)
    print(f"Temperature : {format_temp(current.temp_c, 'C')}  /  {format_temp(current.temp_c, 'F')}")
    print(f"Humidity    : {current.humidity}%")
    print(f"Condition   : {current.description}")
    print(f"Wind speed  : {format_wind(current.wind_ms, 'C')}  ({format_wind(current.wind_ms, 'F')})")
    print("-" * 44)


if __name__ == "__main__":
    main()
