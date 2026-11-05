"""
How the model's probabilities become a risk level.

A plain Random Forest picks whichever level has the highest probability. For a
flood warning that is too relaxed: a zone with a 35% chance of HIGH and a 50%
chance of MEDIUM would be called MEDIUM, and the warning is missed.

So we use a lower bar for HIGH: if the chance of HIGH reaches
HIGH_ALERT_THRESHOLD (0.30 by default, set in settings.py or .env), the zone is
called HIGH. This catches more real floods and costs some extra false alarms,
the right trade for an early warning system.
"""
import numpy as np

from django.conf import settings


def high_threshold() -> float:
    return float(getattr(settings, 'HIGH_ALERT_THRESHOLD', 0.30))


def decide_levels(classes, probabilities, threshold=None):
    """
    classes: the model's class labels, e.g. ['HIGH', 'LOW', 'MEDIUM']
    probabilities: array shaped (rows, classes)
    Returns (levels, confidences): one label and one probability per row.
    The confidence is the probability of the level that was chosen.
    """
    threshold = high_threshold() if threshold is None else threshold
    classes = list(classes)
    probabilities = np.asarray(probabilities, dtype=float)

    best = probabilities.argmax(axis=1)
    if 'HIGH' in classes:
        high = classes.index('HIGH')
        best = np.where(probabilities[:, high] >= threshold, high, best)

    levels = [classes[i] for i in best]
    confidences = [float(probabilities[row, i]) for row, i in enumerate(best)]
    return levels, confidences
