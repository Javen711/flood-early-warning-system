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
import numpy as np
import pandas as pd

FEATURE_COLUMNS = ['rainfall_mm', 'water_level_cm', 'elevation_m', 'drainage_score']

DRAINAGE_SCORE_MAP = {
    'POOR': 0,
    'MODERATE': 1,
    'GOOD': 2,
}


def drainage_quality_to_score(drainage_quality: str) -> int:
    return DRAINAGE_SCORE_MAP.get(drainage_quality, 1)


def _label_from_features(rainfall_mm, water_level_cm, elevation_m, drainage_score, rng):
    """
    The "ground truth" rule the synthetic data follows:
    higher rainfall + higher water level + lower elevation + worse drainage
    -> higher flood risk. A bit of noise is added so the relationship isn't
    perfectly linear, which is more realistic and stops the model from
    trivially memorising a formula.
    """
    risk_score = (
        0.5 * (rainfall_mm / 150)
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


def generate_synthetic_dataset(n_samples: int = 1200, random_state: int = 42) -> pd.DataFrame:
    """Builds a labelled DataFrame with FEATURE_COLUMNS + 'risk_level'."""
    rng = np.random.default_rng(random_state)

    rainfall_mm = rng.uniform(0, 200, n_samples)
    water_level_cm = rng.uniform(0, 150, n_samples)
    elevation_m = rng.uniform(5, 60, n_samples)
    drainage_score = rng.integers(0, 3, n_samples)  # 0=poor, 1=moderate, 2=good

    labels = [
        _label_from_features(r, w, e, d, rng)
        for r, w, e, d in zip(rainfall_mm, water_level_cm, elevation_m, drainage_score)
    ]

    return pd.DataFrame({
        'rainfall_mm': rainfall_mm.round(2),
        'water_level_cm': water_level_cm.round(2),
        'elevation_m': elevation_m.round(2),
        'drainage_score': drainage_score,
        'risk_level': labels,
    })
