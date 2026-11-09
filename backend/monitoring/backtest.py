"""
Back-test: does the model raise the alarm on days Nairobi really flooded?

Rainfall for each date is REAL (Open-Meteo's historical archive). Two things are
not available for past dates and are handled openly rather than invented:

  * River level. Nobody recorded it per sub-county, so each case is run at
    three river levels (low / moderate / high) and all three are reported.
  * Exact flood extent. A zone only counts as "flooded" if the news source
    names it. Zones the source does not mention are shown as "not reported",
    never as "dry".

Only fetch_conditions() touches the network (through openmeteo.py), so tests can swap it for a fake.
"""
from datetime import date, timedelta

from .openmeteo import OpenMeteoError, get_daily_precipitation
from .rainfall_history import conditions_for_day

# river level assumptions, in cm (the model was trained on 0-150)
RIVER_LEVELS = [('low', 20), ('moderate', 60), ('high', 110)]

# Each event: what happened, where, and where we read it.
EVENTS = [
    {
        'label': '15 March 2018, Mukuru floods',
        'date': date(2018, 3, 15),
        'kind': 'flood',
        'zones': ['Embakasi South Sub-County'],
        'what': 'The Ngong River burst its banks in the Mukuru informal settlements; schools were cut off and about 9 Nairobi schools closed.',
        'source': 'FloodList, 18 Mar 2018: https://floodlist.com/africa/kenya-floods-mid-march-2018',
        'gauge_mm': 59,   # Nairobi recorded 59 mm in the 24 hours to 15 March, per the same article
        'note': 'Mukuru kwa Njenga and kwa Reuben fall in Embakasi South. Please check this mapping.',
    },
    {
        'label': '13 May 2021, Kibra and South C floods',
        'date': date(2021, 5, 13),
        'kind': 'flood',
        'zones': ['Kibra Sub-County', "Lang'ata Sub-County"],
        'what': 'Torrential rain on the evening of 13 May flooded Kibra (four people died), Nairobi West and South C; over 400 homes destroyed.',
        'source': 'FloodList (Kenya Red Cross figures): https://floodlist.com/africa/kenya-floods-may-2021',
        'note': 'Nairobi West and South C fall in Lang\'ata. Please check this mapping.',
    },
    {
        'label': '24 April 2024, Mathare floods',
        'date': date(2024, 4, 24),
        'kind': 'flood',
        'zones': ['Mathare Sub-County'],
        'what': 'The Nairobi River broke its banks; at least four people died in Mathare.',
        'source': 'Africanews, 25 Apr 2024: https://www.africanews.com/2024/04/25/kenya-floods-nairobi-residents-grapple-with-aftermath/',
    },
    {
        'label': '6 May 2024, Mathare River overflow',
        'date': date(2024, 5, 6),
        'kind': 'flood',
        'zones': ['Mathare Sub-County'],
        'what': 'Homes near the Mathare River were swept away in a Monday-night flood; about 15 people were reported killed overnight.',
        'source': 'The Star, 7 May 2024: https://www.the-star.co.ke/news/realtime/2024-05-07-3-dead-as-excavator-evicting-mukuru-flood-victims-damaged/',
        'note': 'The article says "Monday night" without a date; 6 May 2024 was the Monday before it was published.',
    },
    {
        'label': '6-7 March 2026, Nairobi flash floods',
        'date': date(2026, 3, 7),
        'kind': 'flood',
        'zones': [
            'Starehe Sub-County', 'Kamukunji Sub-County', 'Kibra Sub-County',
            'Dagoretti North Sub-County', 'Westlands Sub-County',
            'Embakasi North Sub-County', 'Embakasi West Sub-County',
            'Embakasi South Sub-County', 'Makadara Sub-County',
        ],
        'what': 'Rivers burst their banks overnight; the Star names Starehe, Kamukunji, Kibra, Kawangware, '
                'Parklands, Dandora, Kariobangi, Umoja, Kware and Viwandani among the places hit.',
        'source': 'The Star, 7 Mar 2026: https://www.the-star.co.ke/news/2026-03-07-flood-death-toll-rises-to-25-as-raging-rivers-wreak-havoc-in-nairobi',
    },
    # Control days: ordinary dry-season dates. Whatever rain the archive reports is shown as is.
    {
        'label': 'Control: 15 August 2025 (dry season)',
        'date': date(2025, 8, 15), 'kind': 'control', 'zones': None, 'what': 'No flood expected.', 'source': '',
    },
    {
        'label': 'Control: 25 January 2026 (dry season)',
        'date': date(2026, 1, 25), 'kind': 'control', 'zones': None, 'what': 'No flood expected.', 'source': '',
    },
]


BacktestError = OpenMeteoError


def fetch_conditions(latitude, longitude, day):
    """
    Rain inputs for a date, worked out exactly as the live app does:
    (rainfall_mm, antecedent_rain_mm) = (the larger of the day before and that day, total of the 3 days before that).
    """
    series = get_daily_precipitation(latitude, longitude, day - timedelta(days=4), day)
    return conditions_for_day(series, 4)


def run_backtest(zones, events, fetch, predict):
    """
    zones: Zone objects.  fetch(lat, lon, day) -> (rain mm, antecedent rain mm).
    predict(rain, water, elevation, drainage, antecedent) -> (level, confidence, version).
    Returns one result per event with a row for every zone.
    """
    results = []
    for event in events:
        reported = set(event['zones'] or [])
        rows = []
        for zone in zones:
            if not zone.has_coordinates:
                continue
            rain, antecedent = fetch(zone.latitude, zone.longitude, event['date'])
            levels = {}
            for name, cm in RIVER_LEVELS:
                level, confidence, _ = predict(rain, cm, zone.elevation_m, zone.drainage_quality, antecedent)
                levels[name] = level
            rows.append({
                'zone': zone.zone_name,
                'rain_mm': rain,
                'antecedent_mm': antecedent,
                'levels': levels,
                'reported': zone.zone_name in reported,
            })
        results.append({'event': event, 'rows': rows})
    return results


def summarise(result, river='moderate'):
    """Counts for one event at one river level: how many reported zones were flagged, how many other zones were."""
    rows = result['rows']
    reported = [r for r in rows if r['reported']]
    flagged = lambda r: r['levels'][river] in ('MEDIUM', 'HIGH')
    return {
        'reported_total': len(reported),
        'reported_flagged': sum(1 for r in reported if flagged(r)),
        'reported_high': sum(1 for r in reported if r['levels'][river] == 'HIGH'),
        'others_total': len(rows) - len(reported),
        'others_flagged': sum(1 for r in rows if not r['reported'] and flagged(r)),
        'max_rain_mm': max((r['rain_mm'] for r in rows), default=0),
    }
