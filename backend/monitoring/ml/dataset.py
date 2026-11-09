"""
Synthetic training data for the flood-risk model.

Why synthetic data at all: your final year project proposal calls for a
Random Forest model trained on rainfall, drainage, elevation and historical
flood records. A real historical dataset for Nairobi's informal settlements
may not be available or accessible in time for a working demo, so this
module generates a *labelled, physically-plausible* dataset from a simple
rule + random noise, which is enough to:

  1. Prove the whole pipeline works end to end (data -> features -> model
     -> prediction -> stored FloodPrediction -> triggered Alert).
  2. Give you real accuracy/precision/recall numbers to report on, even
     though they describe how well the model learned the synthetic rule
     rather than real-world flooding.

Swap this out for a real dataset later by keeping the same column names
(FEATURE_COLUMNS + 'risk_level') and pointing train.py at a CSV instead.
"""
import json

import numpy as np
import pandas as pd

FEATURE_COLUMNS = ['rainfall_mm', 'antecedent_rain_mm', 'water_level_cm', 'elevation_m', 'drainage_score']

DRAINAGE_SCORE_MAP = {
    'POOR': 0,
    'MODERATE': 1,
    'GOOD': 2,
}


# The model learned from a 5-60 "relative elevation" scale (see
# generate_synthetic_dataset). Zones store real elevation above sea level, and
# Nairobi's sub-counties only span about 1,600-1,800 m, so real values must be
# rescaled onto the model's scale first. Otherwise every zone would look like
# the highest ground and be predicted LOW.
NAIROBI_LOW_M = 1600
NAIROBI_HIGH_M = 1800
MODEL_ELEVATION_MIN = 5
MODEL_ELEVATION_MAX = 60


def to_model_elevation(elevation_m) -> float:
    """Maps elevation above sea level (1,600-1,800 m) to the model's 5-60 scale."""
    fraction = (float(elevation_m) - NAIROBI_LOW_M) / (NAIROBI_HIGH_M - NAIROBI_LOW_M)
    fraction = min(1.0, max(0.0, fraction))
    return MODEL_ELEVATION_MIN + fraction * (MODEL_ELEVATION_MAX - MODEL_ELEVATION_MIN)


# What counts as "very heavy rain" in the synthetic world, in mm. The original
# guess was 150 mm, far above what Nairobi ever records on a normal heavy day.
# `manage.py compute_rainfall_climatology` replaces it with a figure measured
# from years of real rainfall (the 99th percentile). Flood records are NOT used.
DEFAULT_HEAVY_RAIN_MM = 150.0
HEAVY_RAIN_MIN_MM = 20.0


def heavy_rain_mm() -> float:
    """The measured heavy-rain level if the climatology file exists, otherwise the original 150 mm."""
    from django.conf import settings
    path = settings.RAINFALL_CLIMATOLOGY_PATH
    try:
        with open(path) as f:
            value = float(json.load(f)['heavy_rain_mm'])
    except (OSError, ValueError, KeyError):
        return DEFAULT_HEAVY_RAIN_MM
    return min(DEFAULT_HEAVY_RAIN_MM, max(HEAVY_RAIN_MIN_MM, value))


def drainage_quality_to_score(drainage_quality: str) -> int:
    return DRAINAGE_SCORE_MAP.get(drainage_quality, 1)


def _label_from_features(rainfall_mm, water_level_cm, elevation_m, drainage_score, rng,
                         heavy_rain=DEFAULT_HEAVY_RAIN_MM, antecedent_mm=0.0):
    """
    The "ground truth" rule the synthetic data follows:
    higher rainfall + higher water level + lower elevation + worse drainage
    -> higher flood risk. A bit of noise is added so the relationship isn't
    perfectly linear, which is more realistic and stops the model from
    trivially memorising a formula.

    Rain that fell on the three days before (antecedent_mm) also pushes the
    risk up: saturated ground and full drains turn an ordinary storm into a
    flood. Three heavy days in a row (2 x the heavy-rain level) add 0.2.
    """
    risk_score = (
        0.5 * (rainfall_mm / heavy_rain)
        + 0.2 * min(antecedent_mm / (2 * heavy_rain), 1.5)
        + 0.3 * (water_level_cm / 100)
        - 0.4 * (elevation_m / 50)
        - 0.2 * (drainage_score / 2)
        + rng.normal(0, 0.12)
    )
    if risk_score < 0.25:
        return 'LOW'
    if risk_score < 0.55:
        return 'MEDIUM'
    return 'HIGH'


# How the rainfall inputs are drawn from real history. The rest (45%) are real days with 1 mm or more.
# Floods are rare, so heavy days are deliberately over-sampled; with a true-to-life mix the model
# would see almost no HIGH examples to learn from.
SHARE_DRY_DAYS = 0.10        # real days with under 1 mm
SHARE_EXTRAPOLATED = 0.45    # the heaviest real days (top 10%), scaled up 1x to 2x: storms bigger than any on record
EXTRAPOLATION_MAX_SCALE = 2.0


def sample_rainfall(rng, n_samples, heavy_rain, history=None):
    """
    Returns (rainfall_mm, antecedent_rain_mm, source_text).

    With real history: rain and the 3 days before it come as real pairs. Real days are mostly dry, so
    wet and heavy days are over-sampled (otherwise the model would barely see a storm), and a share of
    the heaviest days is scaled up to cover storms rarer than the 11 years on record.
    Without it: a flat spread, as before.
    """
    if history is None or len(history) < 100:
        rain = rng.uniform(0, heavy_rain * 200 / DEFAULT_HEAVY_RAIN_MM, n_samples)
        antecedent = rng.uniform(0, 1.5 * heavy_rain, n_samples)
        return rain, antecedent, 'uniform random spread (no real rainfall history found)'

    rain_all = history['rainfall_mm'].to_numpy(dtype=float)
    ante_all = history['antecedent_rain_mm'].to_numpy(dtype=float)
    dry = np.flatnonzero(rain_all < 1.0)
    wet = np.flatnonzero(rain_all >= 1.0)
    heavy = np.flatnonzero(rain_all >= np.percentile(rain_all, 90))
    if len(dry) == 0 or len(wet) == 0 or len(heavy) == 0:
        return sample_rainfall(rng, n_samples, heavy_rain, None)

    n_dry = int(round(n_samples * SHARE_DRY_DAYS))
    n_heavy = int(round(n_samples * SHARE_EXTRAPOLATED))
    n_wet = n_samples - n_dry - n_heavy
    picks = np.concatenate([rng.choice(dry, n_dry), rng.choice(wet, n_wet), rng.choice(heavy, n_heavy)])
    scale = np.concatenate([
        np.ones(n_dry + n_wet),
        rng.uniform(1.0, EXTRAPOLATION_MAX_SCALE, n_heavy),
    ])
    order = rng.permutation(n_samples)
    rain = (rain_all[picks] * scale)[order]
    antecedent = (ante_all[picks] * scale)[order]
    source = (
        f"real Nairobi rainfall ({len(history):,} zone-days); wet days over-sampled, "
        f"{int(SHARE_EXTRAPOLATED * 100)}% heavy days scaled up to {EXTRAPOLATION_MAX_SCALE:.0f}x to cover rarer storms"
    )
    return rain, antecedent, source


def generate_synthetic_dataset(n_samples: int = 1200, random_state: int = 42, heavy_rain=None, history=None) -> pd.DataFrame:
    """
    Builds a labelled DataFrame with FEATURE_COLUMNS + 'risk_level'.
    history: real rainfall pairs (see rainfall_history.py). Rainfall and the 3 days before it come from
    there when given; river level, elevation and drainage are still random, and labels follow the rule.
    The text describing where the rainfall came from is kept in df.attrs['rainfall_source'].
    """
    rng = np.random.default_rng(random_state)
    heavy_rain = heavy_rain_mm() if heavy_rain is None else float(heavy_rain)

    rainfall_mm, antecedent_mm, source = sample_rainfall(rng, n_samples, heavy_rain, history)
    water_level_cm = rng.uniform(0, 150, n_samples)
    elevation_m = rng.uniform(5, 60, n_samples)
    drainage_score = rng.integers(0, 3, n_samples)  # 0=poor, 1=moderate, 2=good

    labels = [
        _label_from_features(r, w, e, d, rng, heavy_rain, antecedent_mm=a)
        for r, a, w, e, d in zip(rainfall_mm, antecedent_mm, water_level_cm, elevation_m, drainage_score)
    ]

    df = pd.DataFrame({
        'rainfall_mm': rainfall_mm.round(2),
        'antecedent_rain_mm': antecedent_mm.round(2),
        'water_level_cm': water_level_cm.round(2),
        'elevation_m': elevation_m.round(2),
        'drainage_score': drainage_score,
        'risk_level': labels,
    })
    df.attrs['rainfall_source'] = source
    return df
