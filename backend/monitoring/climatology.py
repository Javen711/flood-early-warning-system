"""
Measures how much rain Nairobi really gets, so the model's idea of "heavy rain"
comes from data and not from a guess.

For every zone and day we use the same rainfall number the live app uses (the
larger of yesterday's and today's total), pool all zones and years, and take
percentiles. The 99th percentile becomes the "heavy rain" level used in
training. No flood records are involved, so the back-test stays an independent check.
"""
from datetime import date

import numpy as np

from .openmeteo import get_daily_precipitation

PERCENTILES = [50, 90, 95, 99, 99.9]


def two_day_max(series):
    return [max(series[i - 1], series[i]) for i in range(1, len(series))]


def summarise_climatology(series_list, start, end):
    """series_list: one list of daily mm per zone. Returns a JSON-ready summary."""
    values = np.array([v for series in series_list for v in two_day_max(series)], dtype=float)
    if values.size == 0:
        raise ValueError("No rainfall values to summarise.")
    wet = values[values >= 1.0]
    percentiles = {str(p): round(float(np.percentile(values, p)), 1) for p in PERCENTILES}
    return {
        'heavy_rain_mm': percentiles['99'],
        'percentiles_mm': percentiles,
        'wet_day_share': round(float(wet.size / values.size), 3),
        'median_wet_day_mm': round(float(np.median(wet)), 1) if wet.size else 0.0,
        'max_mm': round(float(values.max()), 1),
        'days_per_zone': len(series_list[0]) - 1,
        'zones': len(series_list),
        'start': start.isoformat(),
        'end': end.isoformat(),
        'source': 'Open-Meteo historical archive, daily precipitation_sum',
    }


def measure_climatology(zones, start=date(2015, 1, 1), end=date(2025, 12, 31), fetch=get_daily_precipitation):
    series_list = [
        fetch(zone.latitude, zone.longitude, start, end)
        for zone in zones if zone.has_coordinates
    ]
    return summarise_climatology(series_list, start, end)
