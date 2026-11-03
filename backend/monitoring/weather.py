"""
Fetches live rainfall for a zone from Open-Meteo (free, no API key).

Only fetch_daily_rainfall() touches the network, so tests can replace it
with a fake. Rainfall is the larger of yesterday's and today's total
(daily precipitation_sum, in mm), because heavy rain that fell yesterday
still floods a zone today.
"""
import json
import urllib.error
import urllib.parse
import urllib.request

API_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT_SECONDS = 10


class WeatherError(RuntimeError):
    """Raised when live weather could not be fetched or understood."""


def fetch_daily_rainfall(latitude, longitude):
    """Returns a list of daily rainfall totals in mm: [yesterday, today]."""
    query = urllib.parse.urlencode({
        'latitude': float(latitude),
        'longitude': float(longitude),
        'daily': 'precipitation_sum',
        'past_days': 1,
        'forecast_days': 1,
        'timezone': 'Africa/Nairobi',
    })
    try:
        with urllib.request.urlopen(f"{API_URL}?{query}", timeout=TIMEOUT_SECONDS) as response:
            payload = json.load(response)
        values = payload['daily']['precipitation_sum']
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as exc:
        raise WeatherError(f"Could not get live weather: {exc}") from exc
    return [0.0 if v is None else float(v) for v in values]


def get_recent_rainfall_mm(latitude, longitude):
    totals = fetch_daily_rainfall(latitude, longitude)
    if not totals:
        raise WeatherError("The weather service returned no rainfall data.")
    return max(totals)
