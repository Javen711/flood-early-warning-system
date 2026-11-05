"""
Geometry for the dashboard's "bloom": one petal per zone, arranged in a circle.

The model stores a risk level and how sure it was, not a single risk number,
so we turn the two into one 0-100 score just for drawing:

    Low     0 - 35   (the surer the model is it is Low, the shorter the petal)
    Medium  40 - 60
    High    62 - 100

The two dashed rings on the page sit at 40 and 62, where Medium and High begin.
"""
import math

INNER = 84            # px: radius of the centre disc
LABEL_RADIUS = 278    # px: how far out the zone names sit
MIN_LEN, MAX_LEN = 18, 156

COLORS = {'HIGH': '#e0505c', 'MEDIUM': '#f2a33a', 'LOW': '#6fcf97', 'UNKNOWN': '#7f99a3'}


def risk_score(level, confidence):
    """A 0-100 number for drawing. No prediction at all scores 0."""
    c = max(0.0, min(1.0, float(confidence or 0)))
    if level == 'HIGH':
        return 62 + c * 38
    if level == 'MEDIUM':
        return 40 + c * 20
    if level == 'LOW':
        return (1 - c) * 35
    return 0.0


def petal_length(score):
    return round(MIN_LEN + (score / 100.0) * (MAX_LEN - MIN_LEN))


def short_name(zone_name):
    return zone_name.replace(' Sub-County', '')


def bloom_petals(zone_rows):
    """
    zone_rows: [{'zone': Zone, 'prediction': FloodPrediction or None}, ...]
    Returns petals sorted from highest risk to lowest, each with ready-made
    inline styles, so the template only has to print them.
    """
    items = []
    for row in zone_rows:
        prediction = row['prediction']
        level = prediction.risk_level if prediction else 'UNKNOWN'
        confidence = prediction.confidence_score if prediction else 0
        items.append({
            'zone': row['zone'],
            'prediction': prediction,
            'level': level,
            'score': risk_score(level, confidence),
        })
    items.sort(key=lambda item: (-item['score'], item['zone'].zone_name))

    step = 360.0 / len(items) if items else 0
    petals = []
    for index, item in enumerate(items):
        theta = round(index * step + 6, 2)
        length = petal_length(item['score'])
        high = item['level'] == 'HIGH'
        petals.append({
            **item,
            'name': short_name(item['zone'].zone_name),
            'label_text': item['level'].title() if item['level'] != 'UNKNOWN' else 'No data',
            'petal_style': (
                f"height:{length}px; background:{COLORS[item['level']]}; "
                f"transform:rotate({theta + 180}deg) translateY({INNER}px);"
            ),
            'anchor_style': (
                f"transform:rotate({theta}deg) translateY(-{LABEL_RADIUS}px) rotate(-{theta}deg);"
            ),
            'label_class': 'hot' if high else '',
        })
    return petals


def ring_diameter(score):
    """Diameter of the dashed ring that marks a score (used for 40 and 62)."""
    return 2 * (INNER + petal_length(score))
