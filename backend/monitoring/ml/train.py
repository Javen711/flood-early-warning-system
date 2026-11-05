"""
Trains the Random Forest flood-risk classifier and saves it to disk.

Run via: python manage.py train_flood_model
"""
import json
from datetime import datetime, timezone

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

from django.conf import settings

from .dataset import FEATURE_COLUMNS, generate_synthetic_dataset
from .decision import decide_levels, high_threshold


def train_and_save_model(n_samples: int = 1200, random_state: int = 42) -> dict:
    """
    Trains the model and writes two files:
      - ML_MODEL_PATH: the serialized RandomForestClassifier (joblib)
      - ML_METADATA_PATH: JSON with the feature list, version, and evaluation
        metrics, so the rest of the app (and your report) can reference them
        without re-running training.

    Returns the metadata dict.
    """
    df = generate_synthetic_dataset(n_samples=n_samples, random_state=random_state)

    X = df[FEATURE_COLUMNS]
    y = df['risk_level']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_state, stratify=y,
    )

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        random_state=random_state,
        class_weight='balanced',
    )
    model.fit(X_train, y_train)

    labels = sorted(y.unique())
    probabilities = model.predict_proba(X_test)

    # Plain "highest probability wins" ...
    y_plain = model.predict(X_test)
    plain_accuracy = accuracy_score(y_test, y_plain)
    plain_report = classification_report(y_test, y_plain, output_dict=True)

    # ... versus what the app really does: HIGH once its probability reaches the threshold.
    threshold = high_threshold()
    y_pred, _ = decide_levels(model.classes_, probabilities, threshold)
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, output_dict=True)
    matrix = confusion_matrix(y_test, y_pred, labels=labels).tolist()

    settings.ML_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, settings.ML_MODEL_PATH)

    metadata = {
        'model_version': datetime.now(timezone.utc).strftime('rf-%Y%m%d-%H%M%S'),
        'trained_at': datetime.now(timezone.utc).isoformat(),
        'feature_columns': FEATURE_COLUMNS,
        'labels': labels,
        'n_samples': n_samples,
        'high_alert_threshold': threshold,
        'accuracy': accuracy,
        'classification_report': report,
        'confusion_matrix': matrix,
        'plain_accuracy': plain_accuracy,
        'plain_classification_report': plain_report,
    }
    with open(settings.ML_METADATA_PATH, 'w') as f:
        json.dump(metadata, f, indent=2)

    return metadata
