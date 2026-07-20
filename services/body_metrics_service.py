"""Body composition calculation service.

Processes body metrics data, computes trends, rates of change,
and generates professional body composition insights.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

import pandas as pd
import numpy as np

from config.body_metrics import (
    DEFAULT_BODY_METRICS,
    BODY_METRIC_KEYS,
    get_body_metric_label,
    get_body_metric_unit,
    get_body_metric_precision,
)
from utils.date_utils import format_date, get_date_range


def get_latest_body_metrics(body_metrics_df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """Get the most recent body metrics entry.

    Returns:
        Dict of metric key -> value, or None if no data.
    """
    if body_metrics_df is None or body_metrics_df.empty:
        return None

    # Sort by date descending and take first row
    df = body_metrics_df.copy()
    df["_sort"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.sort_values("_sort", ascending=False)

    if df.empty:
        return None

    latest = df.iloc[0]
    result = {}
    for key in BODY_METRIC_KEYS:
        if key in latest.index:
            val = latest[key]
            result[key] = float(val) if pd.notna(val) else None
        else:
            result[key] = None
    result["Date"] = latest.get("Date", "")
    return result


def get_body_metric_trend(
    body_metrics_df: pd.DataFrame,
    metric_key: str,
    end_date: datetime,
    days: int = 90,
) -> pd.DataFrame:
    """Get trend data for a specific body metric.

    Args:
        body_metrics_df: Body metrics DataFrame.
        metric_key: The metric to extract.
        end_date: End date of the range.
        days: Number of days to include.

    Returns:
        DataFrame with Date and the metric value.
    """
    if body_metrics_df is None or body_metrics_df.empty:
        return pd.DataFrame(columns=["Date", metric_key])

    df = body_metrics_df.copy()
    df["_sort"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["_sort"])

    # Filter to date range
    start_date = end_date - pd.Timedelta(days=days - 1)
    df = df[(df["_sort"] >= pd.Timestamp(start_date)) & (df["_sort"] <= pd.Timestamp(end_date))]
    df = df.sort_values("_sort")

    if df.empty:
        return pd.DataFrame(columns=["Date", metric_key])

    return df[["Date", metric_key]].copy()


def compute_body_metric_change(
    body_metrics_df: pd.DataFrame,
    metric_key: str,
    days: int = 30,
) -> Optional[Dict[str, Any]]:
    """Compute change in a body metric over the specified period.

    Returns:
        Dict with current, previous, change_abs, change_pct, trend_direction.
    """
    if body_metrics_df is None or body_metrics_df.empty:
        return None

    df = body_metrics_df.copy()
    df["_sort"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["_sort", metric_key])
    df = df.sort_values("_sort")

    if len(df) < 2:
        return None

    current = df.iloc[-1][metric_key]
    # Find the closest record to `days` ago
    cutoff = df["_sort"].max() - pd.Timedelta(days=days)
    past_df = df[df["_sort"] <= cutoff]

    if past_df.empty:
        past = df.iloc[0][metric_key]
    else:
        past = past_df.iloc[-1][metric_key]

    change_abs = float(current - past)
    change_pct = float((change_abs / past) * 100) if past != 0 else 0.0

    config = DEFAULT_BODY_METRICS.get(metric_key)
    direction = config.direction if config else "range"

    if direction == "lower":
        trend = "improving" if change_abs < 0 else "worsening" if change_abs > 0 else "stable"
    elif direction == "higher":
        trend = "improving" if change_abs > 0 else "worsening" if change_abs < 0 else "stable"
    else:
        # For range, check if within healthy range
        if config:
            in_range = config.healthy_min <= current <= config.healthy_max
            trend = "healthy" if in_range else "attention"
        else:
            trend = "stable"

    return {
        "current": float(current),
        "previous": float(past),
        "change_abs": round(change_abs, 2),
        "change_pct": round(change_pct, 2),
        "trend": trend,
        "direction": direction,
    }


def generate_body_insights(body_metrics_df: pd.DataFrame) -> List[Dict[str, str]]:
    """Generate insights based on body composition trends."""
    insights = []

    if body_metrics_df is None or body_metrics_df.empty:
        insights.append({
            "message": "No body composition data available. Add a 'Body_Metrics' sheet to track weight, body fat %, and more.",
            "type": "neutral"
        })
        return insights

    # Weight insight
    weight_change = compute_body_metric_change(body_metrics_df, "Weight_kg", days=30)
    if weight_change:
        if weight_change["change_abs"] < -0.5:
            insights.append({
                "message": f"Weight down {abs(weight_change['change_abs']):.1f} kg over 30 days. Keep it sustainable!",
                "type": "positive"
            })
        elif weight_change["change_abs"] > 1.0:
            insights.append({
                "message": f"Weight up {weight_change['change_abs']:.1f} kg over 30 days. Review calorie balance.",
                "type": "warning"
            })

    # Body fat insight
    bf_change = compute_body_metric_change(body_metrics_df, "Body_Fat_pct", days=30)
    if bf_change:
        if bf_change["change_abs"] < -0.5:
            insights.append({
                "message": f"Body fat down {abs(bf_change['change_abs']):.1f}% over 30 days. Excellent progress!",
                "type": "positive"
            })
        elif bf_change["change_abs"] > 0.5:
            insights.append({
                "message": f"Body fat up {bf_change['change_abs']:.1f}% over 30 days. Consider adjusting macros.",
                "type": "warning"
            })

    # BMI insight
    latest = get_latest_body_metrics(body_metrics_df)
    if latest and latest.get("BMI") is not None:
        bmi = latest["BMI"]
        if bmi < 18.5:
            insights.append({"message": f"BMI is {bmi:.1f} (underweight). Consider increasing calorie intake.", "type": "warning"})
        elif bmi > 30:
            insights.append({"message": f"BMI is {bmi:.1f} (obese). Consider a structured plan.", "type": "danger"})
        elif 25 <= bmi <= 30:
            insights.append({"message": f"BMI is {bmi:.1f} (overweight). Small sustained changes make a difference.", "type": "warning"})
        else:
            insights.append({"message": f"BMI is {bmi:.1f} (healthy range). Great job maintaining!", "type": "positive"})

    # Visceral fat
    if latest and latest.get("Visceral_Fat") is not None:
        vf = latest["Visceral_Fat"]
        if vf > 12:
            insights.append({"message": f"Visceral fat is elevated ({vf:.0f}). Focus on fiber, protein, and activity.", "type": "danger"})
        elif vf <= 8:
            insights.append({"message": f"Visceral fat is in a healthy range ({vf:.0f}).", "type": "positive"})

    # Waist
    if latest and latest.get("Waist_cm") is not None:
        waist = latest["Waist_cm"]
        if waist > 102:
            insights.append({"message": f"Waist circumference is {waist:.0f} cm. Elevated risk zone.", "type": "danger"})
        elif waist > 94:
            insights.append({"message": f"Waist circumference is {waist:.0f} cm. Approaching risk threshold.", "type": "warning"})

    if not insights:
        insights.append({"message": "Body metrics are being tracked. Keep logging daily for trend insights.", "type": "neutral"})

    return insights