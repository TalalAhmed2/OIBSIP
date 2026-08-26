"""OpenWeatherMap API settings.

Get a free key at: https://home.openweathermap.org/users/sign_up
Then paste it below, or set the OPENWEATHER_API_KEY environment variable.
"""

import os

API_KEY = os.environ.get("OPENWEATHER_API_KEY", "Your API Key")
BASE_URL = "https://api.openweathermap.org/data/2.5"
ICON_URL = "https://openweathermap.org/img/wn/{icon}@2x.png"
REQUEST_TIMEOUT = 10
