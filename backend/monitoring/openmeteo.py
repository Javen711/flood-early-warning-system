"""
One gentle way to ask Open-Meteo's history service for daily rainfall.

Used by the back-test and the rainfall-climatology command. It pauses between
requests, remembers answers it already has, and retries with waiting when the
free service drops the connection (it does that when asked too fast).
"""
import json
import time
import urllib.parse
import urllib.request

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
TIMEOUT_SECONDS = 30
RETRIES = 4              # tries per request before giving up
PAUSE_SECONDS = 0.4      # gap before each request

_cache = {}


class OpenMeteoError(RuntimeError):
    pass


def get_daily_precipitation(latitude, longitude, start, end):
    """Daily rainfall totals in mm from start to end (dates, inclusive), oldest first."""
    key = (round(float(latitude), 4), round(float(longitude), 4), start, end)
    if key in _cache:
        return _cache[key]

    query = urllib.parse.urlencode({
        'latitude': float(latitude), 'longitude': float(longitude),
        'start_date': start.isoformat(), 'end_date': end.isoformat(),
        'daily': 'precipitation_sum', 'timezone': 'Africa/Nairobi',
    })
    last_error = None
    for attempt in range(RETRIES):
        time.sleep(PAUSE_SECONDS if attempt == 0 else 2 ** attempt)   # 0.4s, then 2s, 4s, 8s
        try:
            with urllib.request.urlopen(f"{ARCHIVE_URL}?{query}", timeout=TIMEOUT_SECONDS) as response:
                values = json.load(response)['daily']['precipitation_sum']
            break
        except Exception as exc:
            last_error = exc
    else:
        raise OpenMeteoError(f"Could not get rainfall for {start} to {end}: {last_error}") from last_error

    values = [0.0 if v is None else float(v) for v in values]
    if not values:
        raise OpenMeteoError(f"No rainfall data returned for {start} to {end}.")
    _cache[key] = values
    return values
