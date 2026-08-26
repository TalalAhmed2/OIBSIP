# Weather App

A simple Python weather application built on the OpenWeatherMap API, available in two flavors:

- **CLI** (`cli_weather.py`) — a lightweight command-line tool for a quick weather check.
- **GUI** (`gui_weather.py`) — a Tkinter desktop app with current conditions, an hourly forecast strip, and a 5-day forecast, complete with weather icons.

Both apps share a common client (`weather_service.py`) that handles API requests, error handling, and unit conversion.

## Features

- Search by city name or ZIP code
- Current temperature, humidity, wind speed, and conditions
- Celsius/Fahrenheit toggle (GUI) and dual display (CLI)
- Hourly forecast (next 6 hours) and daily forecast (next 5 days) in the GUI
- Weather icons fetched directly from OpenWeatherMap (GUI)
- Friendly, user-facing error messages for invalid cities, network issues, and API key problems

## Project Structure

```
.
├── cli_weather.py       # Command-line weather app
├── gui_weather.py       # Tkinter GUI weather app
├── weather_service.py   # Shared OpenWeatherMap API client
├── config.py            # API key and endpoint configuration
├── requirements.txt     # Python dependencies
└── .gitignore
```

## Requirements

- Python 3.10+
- A free [OpenWeatherMap](https://home.openweathermap.org/users/sign_up) API key

## Setup

1. **Clone the repository**

   ```bash
   git clone <your-repo-url>
   cd <your-repo-folder>
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set your API key**

   Set it as an environment variable (recommended):

   ```bash
   # macOS / Linux
   export OPENWEATHER_API_KEY=your_key_here

   # Windows (PowerShell)
   setx OPENWEATHER_API_KEY "your_key_here"
   ```

   Or open `config.py` and paste your key directly in place of the default value.

   > ⚠️ **Security note:** `config.py` currently ships with a hardcoded default API key. Before pushing to GitHub, replace it with a placeholder (e.g. `"YOUR_API_KEY_HERE"`) and rely on the `OPENWEATHER_API_KEY` environment variable instead — otherwise your key will be publicly visible in your commit history.

## Usage

### CLI

```bash
python cli_weather.py
```

You'll be prompted to enter a city name or ZIP code, then the current conditions will be printed to the terminal.

### GUI

```bash
python gui_weather.py
```

Enter a city or ZIP code and click **Get Weather** (or press Enter) to see current conditions, an hourly forecast, and a 5-day forecast. Use the °C | °F button to toggle units.

## Dependencies

- [`requests`](https://pypi.org/project/requests/) — HTTP client for API calls
- [`Pillow`](https://pypi.org/project/Pillow/) — image handling for weather icons (GUI only)

## License

Add a license of your choice (e.g. MIT) here.
