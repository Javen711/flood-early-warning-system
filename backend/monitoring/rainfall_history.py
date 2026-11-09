"""
Real rainfall history, shaped the way the model sees it.

For every zone and day we keep two numbers, exactly as the live app computes them:
  rainfall_mm         the larger of the day before and that day
  antecedent_rain_mm  total rain on the three days before that (how wet the ground already was)

train_flood_model draws its rainfall inputs from these real pairs, so the model practises on
rainfall that really falls on Nairobi instead of a flat 0-to-N spread. No flood records are involved.
"""
import pandas as pd

from .openmeteo import get_daily_precipitation

COLUMNS = ['zone', 'date', 'rainfall_mm', 'antecedent_rain_mm']


def conditions_for_day(series, i):
    """series: daily mm, oldest first. Conditions on day i (needs i >= 4): (rainfall_mm, antecedent_rain_mm)."""
    return max(series[i - 1], series[i]), sum(series[i - 4:i - 1])


def history_rows(zone_name, start, series):
    """One row per day from the 5th day on. start: the date of series[0]."""
    from datetime import timedelta
    rows = []
    for i in range(4, len(series)):
        rain, antecedent = conditions_for_day(series, i)
        rows.append((zone_name, (start + timedelta(days=i)).isoformat(), round(rain, 2), round(antecedent, 2)))
    return rows


def build_history(zones, start, end, fetch=get_daily_precipitation):
    """Returns (DataFrame of COLUMNS, list of the raw daily series, one per zone)."""
    rows, all_series = [], []
    for zone in zones:
        if not zone.has_coordinates:
            continue
        series = fetch(zone.latitude, zone.longitude, start, end)
        all_series.append(series)
        rows.extend(history_rows(zone.zone_name, start, series))
    return pd.DataFrame(rows, columns=COLUMNS), all_series


def load_history(path=None):
    """The saved history as a DataFrame, or None if it has not been built yet."""
    from django.conf import settings
    path = path or settings.RAINFALL_HISTORY_PATH
    try:
        df = pd.read_csv(path)
    except (OSError, ValueError):
        return None
    if df.empty or not {'rainfall_mm', 'antecedent_rain_mm'} <= set(df.columns):
        return None
    return df
