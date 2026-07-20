"""Body composition and biometrics configuration.

Defines body metric metadata, default targets, and units for
professional-grade body composition tracking.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class BodyMetricConfig:
    """Configuration for a single body metric."""
    name: str
    unit: str
    default_target: float
    direction: str  # 'lower', 'higher', 'range'
    healthy_min: float
    healthy_max: float
    display_precision: int = 1


# Default body metric targets / healthy ranges.
# Adjust these to your personal goals in the Body_Metrics sheet.
DEFAULT_BODY_METRICS: Dict[str, BodyMetricConfig] = {
    "Weight_kg": BodyMetricConfig(
        "Weight", "kg", 70.0, "range", 50.0, 120.0, 1
    ),
    "Body_Fat_pct": BodyMetricConfig(
        "Body Fat %", "%", 15.0, "lower", 10.0, 25.0, 1
    ),
    "Muscle_Mass_kg": BodyMetricConfig(
        "Muscle Mass", "kg", 55.0, "higher", 40.0, 80.0, 1
    ),
    "BMI": BodyMetricConfig(
        "BMI", "", 22.0, "range", 18.5, 24.9, 1
    ),
    "Waist_cm": BodyMetricConfig(
        "Waist", "cm", 80.0, "lower", 60.0, 102.0, 1
    ),
    "Visceral_Fat": BodyMetricConfig(
        "Visceral Fat", "", 8.0, "lower", 1.0, 12.0, 0
    ),
    "Bone_Mass_kg": BodyMetricConfig(
        "Bone Mass", "kg", 3.0, "range", 2.0, 5.0, 1
    ),
    "Water_pct": BodyMetricConfig(
        "Body Water %", "%", 55.0, "range", 45.0, 65.0, 1
    ),
    "BMR_kcal": BodyMetricConfig(
        "BMR", "kcal", 1700.0, "range", 1200.0, 2500.0, 0
    ),
    "Subcutaneous_Fat_pct": BodyMetricConfig(
        "Subcutaneous Fat %", "%", 12.0, "lower", 8.0, 20.0, 1
    ),
}

# Body_Metrics sheet expected columns
BODY_METRICS_COLUMNS = ["Date"] + list(DEFAULT_BODY_METRICS.keys())

# Keys ordered for display
BODY_METRIC_KEYS = list(DEFAULT_BODY_METRICS.keys())


def get_body_metric_label(key: str) -> str:
    """Return human-readable label for a body metric key."""
    config = DEFAULT_BODY_METRICS.get(key)
    return config.name if config else key


def get_body_metric_unit(key: str) -> str:
    """Return unit for a body metric key."""
    config = DEFAULT_BODY_METRICS.get(key)
    return config.unit if config else ""


def get_body_metric_precision(key: str) -> int:
    """Return display precision for a body metric key."""
    config = DEFAULT_BODY_METRICS.get(key)
    return config.display_precision if config else 1