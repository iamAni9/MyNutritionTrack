"""Nutrition calculation service.

Aggregates food log data, computes daily totals, compares against targets,
and generates insights. All business logic lives here to keep app.py clean.
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import math

import pandas as pd
import numpy as np

from config.nutrients import (
    DEFAULT_NUTRIENTS,
    MACRO_KEYS,
    VITAMIN_KEYS,
    MINERAL_KEYS,
    OTHER_KEYS,
    get_nutrient_label,
    get_nutrient_unit,
    get_nutrient_type,
    get_default_target,
    get_display_precision,
)
from utils.date_utils import format_date, get_week_range


def _safe_div(numerator: float, denominator: float) -> float:
    """Divide safely, returning 0.0 if denominator is zero or NaN."""
    if denominator == 0 or math.isnan(denominator):
        return 0.0
    return numerator / denominator


def build_targets_map(targets_df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """Build a lookup dictionary from the Daily_Targets DataFrame.

    Args:
        targets_df: DataFrame with columns Nutrient, Target, Unit, Type.

    Returns:
        Dict mapping nutrient key -> {target, unit, type}.
    """
    targets_map = {}
    for _, row in targets_df.iterrows():
        key = str(row.get("Nutrient", "")).strip()
        if not key:
            continue
        try:
            target_val = float(row.get("Target", 0))
        except (ValueError, TypeError):
            target_val = 0.0
        targets_map[key] = {
            "target": target_val,
            "unit": str(row.get("Unit", get_nutrient_unit(key))),
            "type": str(row.get("Type", get_nutrient_type(key))).lower().strip(),
        }

    # Fallback for any nutrients missing from the sheet
    for key, config in DEFAULT_NUTRIENTS.items():
        if key not in targets_map:
            targets_map[key] = {
                "target": config.default_target,
                "unit": config.unit,
                "type": config.nutrient_type,
            }

    return targets_map


def get_daily_totals(food_log_df: pd.DataFrame, date: datetime) -> Dict[str, float]:
    """Sum all nutrient values for a given date.

    Args:
        food_log_df: Full food log DataFrame.
        date: The date to filter on.

    Returns:
        Dict mapping nutrient key -> total consumed.
    """
    date_str = format_date(date)
    day_df = food_log_df[food_log_df["Date"] == date_str]

    totals = {}
    for key in DEFAULT_NUTRIENTS.keys():
        if key in day_df.columns:
            val = day_df[key].sum()
            totals[key] = float(val) if not pd.isna(val) else 0.0
        else:
            totals[key] = 0.0

    return totals


def get_meal_breakdown(food_log_df: pd.DataFrame, date: datetime) -> Dict[str, pd.DataFrame]:
    """Group food entries by meal for a given date.

    Args:
        food_log_df: Full food log DataFrame.
        date: The date to filter on.

    Returns:
        Dict mapping meal name -> DataFrame of food items.
    """
    date_str = format_date(date)
    day_df = food_log_df[food_log_df["Date"] == date_str].copy()

    if day_df.empty:
        return {}

    # Ensure Meal column exists
    if "Meal" not in day_df.columns:
        return {}

    meals = {}
    for meal_name, group in day_df.groupby("Meal"):
        meals[meal_name] = group.sort_values("Food")

    return meals


def compute_nutrient_status(
    consumed: float,
    target: float,
    nutrient_type: str,
) -> Dict[str, Any]:
    """Compute status metrics for a single nutrient.

    Args:
        consumed: Amount consumed.
        target: Target or limit value.
        nutrient_type: 'target' or 'limit'.

    Returns:
        Dict with consumed, target, remaining, percentage, status_label.
    """
    if nutrient_type == "limit":
        remaining = max(target - consumed, 0)
        percentage = _safe_div(consumed, target) * 100

        if consumed > target:
            status = "Exceeded"
            status_color = "danger"
        elif percentage >= 80:
            status = "Near Limit"
            status_color = "warning"
        else:
            status = "On Track"
            status_color = "good"
    else:
        remaining = max(target - consumed, 0)
        percentage = _safe_div(consumed, target) * 100

        if percentage >= 100:
            status = "On Track"
            status_color = "good"
        elif percentage >= 80:
            status = "Near Target"
            status_color = "warning"
        elif percentage >= 50:
            status = "Low Intake"
            status_color = "neutral"
        else:
            status = "Low Intake"
            status_color = "danger"

    return {
        "consumed": consumed,
        "target": target,
        "remaining": remaining,
        "percentage": percentage,
        "status": status,
        "status_color": status_color,
    }


def get_daily_summary(
    food_log_df: pd.DataFrame,
    targets_map: Dict[str, Dict[str, Any]],
    date: datetime,
) -> Dict[str, Dict[str, Any]]:
    """Get full daily summary for all nutrients.

    Args:
        food_log_df: Full food log DataFrame.
        targets_map: Target lookup from build_targets_map.
        date: The date to summarize.

    Returns:
        Dict mapping nutrient key -> status dict.
    """
    totals = get_daily_totals(food_log_df, date)
    summary = {}

    for key, consumed in totals.items():
        target_info = targets_map.get(key, {})
        target = target_info.get("target", get_default_target(key))
        ntype = target_info.get("type", get_nutrient_type(key))
        summary[key] = compute_nutrient_status(consumed, target, ntype)
        summary[key]["label"] = get_nutrient_label(key)
        summary[key]["unit"] = target_info.get("unit", get_nutrient_unit(key))
        summary[key]["precision"] = get_display_precision(key)

    return summary


def generate_insights(summary: Dict[str, Dict[str, Any]]) -> List[Dict[str, str]]:
    """Generate rule-based insights from daily summary.

    Args:
        summary: Output from get_daily_summary.

    Returns:
        List of insight dicts with 'message' and 'type' (positive, warning, danger).
    """
    insights = []

    # Calorie insight
    cal = summary.get("Calories_kcal", {})
    if cal:
        if cal["status"] == "On Track":
            insights.append({"message": "You are on track with your calorie goal.", "type": "positive"})
        elif cal["status"] == "Near Target":
            insights.append({"message": f"You are near your calorie target ({cal['remaining']:.0f} kcal remaining).", "type": "warning"})
        elif cal["status"] == "Low Intake":
            insights.append({"message": f"You need {cal['remaining']:.0f} kcal more to reach today's calorie goal.", "type": "warning"})
        elif cal["status"] == "Exceeded":
            over = cal["consumed"] - cal["target"]
            insights.append({"message": f"You exceeded your calorie target by {over:.0f} kcal.", "type": "danger"})

    # Protein insight
    prot = summary.get("Protein_g", {})
    if prot and prot["percentage"] < 100:
        insights.append({"message": f"You need {prot['remaining']:.1f} g more protein to reach today's goal.", "type": "warning"})
    elif prot and prot["percentage"] >= 100:
        insights.append({"message": "Great job! You have reached your protein target.", "type": "positive"})

    # Fiber insight
    fib = summary.get("Fiber_g", {})
    if fib:
        if fib["percentage"] < 60:
            insights.append({"message": f"Fiber intake is below 60% of your daily target ({fib['percentage']:.0f}%).", "type": "warning"})
        elif fib["percentage"] >= 100:
            insights.append({"message": "Excellent! You have met your fiber target.", "type": "positive"})

    # Sugar limit
    sugar = summary.get("Sugar_g", {})
    if sugar:
        if sugar["status"] == "Exceeded":
            over = sugar["consumed"] - sugar["target"]
            insights.append({"message": f"You exceeded your sugar limit by {over:.1f} g.", "type": "danger"})
        elif sugar["status"] == "Near Limit":
            insights.append({"message": "You are close to your sugar limit.", "type": "warning"})

    # Sodium limit
    sod = summary.get("Sodium_mg", {})
    if sod:
        if sod["status"] == "Exceeded":
            over = sod["consumed"] - sod["target"]
            insights.append({"message": f"You exceeded your sodium limit by {over:.0f} mg.", "type": "danger"})
        elif sod["status"] == "Near Limit":
            insights.append({"message": "You are close to your sodium limit.", "type": "warning"})

    # Water
    water = summary.get("Water_ml", {})
    if water and water["percentage"] >= 100:
        insights.append({"message": "You have met your daily water intake goal. Well done!", "type": "positive"})
    elif water and water["percentage"] < 50:
        insights.append({"message": f"You are at {water['percentage']:.0f}% of your water goal. Drink more water!", "type": "warning"})

    # Positive catch-all if nothing else
    if not insights:
        insights.append({"message": "Keep tracking your nutrition to see personalized insights.", "type": "neutral"})

    return insights


def get_weekly_data(
    food_log_df: pd.DataFrame,
    targets_map: Dict[str, Dict[str, Any]],
    end_date: datetime,
) -> pd.DataFrame:
    """Build a weekly summary DataFrame ending on end_date.

    Args:
        food_log_df: Full food log DataFrame.
        targets_map: Target lookup.
        end_date: The last day of the week (inclusive).

    Returns:
        DataFrame with columns: Date, Calories, Protein, Fiber, Water, etc.
    """
    week_dates = get_week_range(end_date)
    rows = []

    for date in week_dates:
        totals = get_daily_totals(food_log_df, date)
        row = {"Date": format_date(date), "Display": date.strftime("%a %d")}
        for key in DEFAULT_NUTRIENTS.keys():
            row[key] = totals.get(key, 0.0)
        rows.append(row)

    weekly_df = pd.DataFrame(rows)

    # Add target columns for chart reference lines
    for key in DEFAULT_NUTRIENTS.keys():
        target_info = targets_map.get(key, {})
        target_val = target_info.get("target", get_default_target(key))
        weekly_df[f"{key}_target"] = target_val

    return weekly_df


def get_weekly_averages(weekly_df: pd.DataFrame) -> Dict[str, float]:
    """Compute weekly averages for key nutrients.

    Args:
        weekly_df: Output from get_weekly_data.

    Returns:
        Dict mapping nutrient key -> 7-day average.
    """
    averages = {}
    for key in ["Calories_kcal", "Protein_g", "Fiber_g", "Water_ml"]:
        if key in weekly_df.columns:
            avg = weekly_df[key].mean()
            averages[key] = float(avg) if not pd.isna(avg) else 0.0
    return averages
