"""
Loads the trained model and turns a zone's latest readings into a
risk-level prediction. This is the piece the dashboard's "Run Prediction"
button and the run_flood_predictions management command both call.
"""
import json

import joblib
import pandas as pd

from django.conf import settings

from .dataset import FEATURE_COLUMNS, drainage_quality_to_score, to_model_elevation
from .decision import decide_levels

_model_cache = None
_metadata_cache = None


class ModelNotTrainedError(RuntimeError):
    """Raised when a prediction is requested before train_flood_model has been run."""


def _load_model():
    global _model_cache, _metadata_cache
    if _model_cache is None:
        if not settings.ML_MODEL_PATH.exists():
            raise ModelNotTrainedError(
                "No trained model found. Run `python manage.py train_flood_model` first."
            )
        _model_cache = joblib.load(settings.ML_MODEL_PATH)
        with open(settings.ML_METADATA_PATH) as f:
            _metadata_cache = json.load(f)
    return _model_cache, _metadata_cache


def is_model_trained() -> bool:
    """Cheap check the dashboard uses to decide whether to show a
    'train the model first' notice instead of trying to predict."""
    return settings.ML_MODEL_PATH.exists()


def reset_cache():
    """Call this after retraining so the next prediction loads the new model."""
    global _model_cache, _metadata_cache
    _model_cache = None
    _metadata_cache = None


def predict_risk(rainfall_mm: float, water_level_cm: float, elevation_m: float, drainage_quality: str):
    """
    elevation_m is metres above sea level; it is rescaled for the model here.
    Returns (risk_level: str, confidence_score: float, model_version: str).
    confidence_score is the model's probability for the chosen level. HIGH is
    chosen as soon as its probability reaches the alert threshold (decision.py).
    """
    model, metadata = _load_model()

    features = pd.DataFrame([{
        'rainfall_mm': float(rainfall_mm),
        'water_level_cm': float(water_level_cm),
        'elevation_m': to_model_elevation(elevation_m),
        'drainage_score': drainage_quality_to_score(drainage_quality),
    }], columns=FEATURE_COLUMNS)

    levels, confidences = decide_levels(model.classes_, model.predict_proba(features))

    return levels[0], confidences[0], metadata['model_version']
