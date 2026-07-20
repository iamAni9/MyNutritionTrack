"""Nutrition calculation service.

Aggregates food log data, computes daily totals, compares against targets,
generates insights, and computes professional-grade analytics.
All business logic lives here to keep app.py clean.
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
    FAT_DETAIL_KEYS,
    OTHER_KEYS,
    get_nutrient_label,
    get_nutrient_unit,
    get_nutrient_type,
    get_default_target,
    get_display_precision,
)
from utils.date_utils import format_date, get_date_range


def _safe_div(numerator: float, denominator: float) -> float:
    """Divide safely, returning 0.0 if denominator is zero or NaN."""
    if denominator == 0 or math.isnan(denominator):
        return 0.0
    return numerator / denominator


def build_targets_map(targets_df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """Build a lookup dictionary from the Daily_Targets DataFrame."""
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

    for key, config in DEFAULT_NUTRIENTS.items():
        if key not in targets_map:
            targets_map[key] = {
                "target": config.default_target,
                "unit": config.unit,
                "type": config.nutrient_type,
            }

    return targets_map


def get_daily_totals(food_log_df: pd.DataFrame, date: datetime) -> Dict[str, float]:
    """Sum all nutrient values for a given date."""
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
    """Group food entries by meal for a given date."""
    date_str = format_date(date)
    day_df = food_log_df[food_log_df["Date"] == date_str].copy()

    if day_df.empty or "Meal" not in day_df.columns:
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
    """Compute status metrics for a single nutrient."""
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
    """Get full daily summary for all nutrients."""
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


def compute_nutrient_adequacy_score(summary: Dict[str, Dict[str, Any]]) -> float:
    """Compute an overall nutrient adequacy score (0-100).

    Based on percentage of target nutrients that met >= 80% of their target
    and limit nutrients that stayed below their limit.
    """
    if not summary:
        return 0.0

    scores = []
    for key, data in summary.items():
        if key == "Calories_kcal":
            continue  # Exclude calories from micronutrient score
        pct = data.get("percentage", 0)
        ntype = data.get("type", "target")

        if ntype == "limit":
            # For limits, lower is better. Score 100 if <= 100%, else penalize
            if pct <= 100:
                scores.append(100.0)
            else:
                scores.append(max(0, 200 - pct))
        else:
            # For targets, score based on closeness to 100% (not exceeding by too much)
            if pct >= 80:
                scores.append(min(pct, 120))  # Cap at 120 to avoid over-rewarding
            else:
                scores.append(pct)

    return round(np.mean(scores), 1) if scores else 0.0


def compute_macro_distribution(summary: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
    """Compute calorie contribution percentage from each macronutrient."""
    cal = summary.get("Calories_kcal", {}).get("consumed", 0)
    if cal == 0:
        return {"Protein": 0, "Carbs": 0, "Fat": 0}

    protein_cal = summary.get("Protein_g", {}).get("consumed", 0) * 4
    carbs_cal = summary.get("Carbs_g", {}).get("consumed", 0) * 4
    fat_cal = summary.get("Fat_g", {}).get("consumed", 0) * 9

    total_macro_cal = protein_cal + carbs_cal + fat_cal
    if total_macro_cal == 0:
        return {"Protein": 0, "Carbs": 0, "Fat": 0}

    return {
        "Protein": round(protein_cal / total_macro_cal * 100, 1),
        "Carbs": round(carbs_cal / total_macro_cal * 100, 1),
        "Fat": round(fat_cal / total_macro_cal * 100, 1),
    }


def compute_calorie_quality_index(summary: Dict[str, Dict[str, Any]]) -> float:
    """Compute a calorie quality index (0-100) based on protein and fiber density."""
    cal = summary.get("Calories_kcal", {}).get("consumed", 0)
    if cal == 0:
        return 0.0

    protein = summary.get("Protein_g", {}).get("consumed", 0)
    fiber = summary.get("Fiber_g", {}).get("consumed", 0)

    # Protein density: g per 100 kcal (target ~10g/100kcal = excellent)
    protein_score = min((protein / cal * 100) / 10 * 50, 50)
    # Fiber density: g per 1000 kcal (target ~15g/1000kcal = excellent)
    fiber_score = min((fiber / cal * 1000) / 15 * 50, 50)

    return round(protein_score + fiber_score, 1)


def generate_insights(summary: Dict[str, Dict[str, Any]]) -> List[Dict[str, str]]:
    """Generate rule-based insights from daily summary."""
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

    # Added Sugar limit
    added_sugar = summary.get("Added_Sugar_g", {})
    if added_sugar:
        if added_sugar["status"] == "Exceeded":
            over = added_sugar["consumed"] - added_sugar["target"]
            insights.append({"message": f"You exceeded your added sugar limit by {over:.1f} g.", "type": "danger"})
        elif added_sugar["status"] == "Near Limit":
            insights.append({"message": "You are close to your added sugar limit.", "type": "warning"})

    # Sugar limit
    sugar = summary.get("Sugar_g", {})
    if sugar:
        if sugar["status"] == "Exceeded":
            over = sugar["consumed"] - sugar["target"]
            insights.append({"message": f"You exceeded your total sugar limit by {over:.1f} g.", "type": "danger"})
        elif sugar["status"] == "Near Limit":
            insights.append({"message": "You are close to your total sugar limit.", "type": "warning"})

    # Sodium limit
    sod = summary.get("Sodium_mg", {})
    if sod:
        if sod["status"] == "Exceeded":
            over = sod["consumed"] - sod["target"]
            insights.append({"message": f"You exceeded your sodium limit by {over:.0f} mg.", "type": "danger"})
        elif sod["status"] == "Near Limit":
            insights.append({"message": "You are close to your sodium limit.", "type": "warning"})

    # Trans fat
    trans = summary.get("Trans_Fat_g", {})
    if trans and trans["consumed"] > 0:
        insights.append({"message": f"Trans fat detected ({trans['consumed']:.1f} g). Minimize intake for heart health.", "type": "warning"})

    # Water
    water = summary.get("Water_ml", {})
    if water and water["percentage"] >= 100:
        insights.append({"message": "You have met your daily water intake goal. Well done!", "type": "positive"})
    elif water and water["percentage"] < 50:
        insights.append({"message": f"You are at {water['percentage']:.0f}% of your water goal. Drink more water!", "type": "warning"})

    # Nutrient adequacy
    adequacy = compute_nutrient_adequacy_score(summary)
    if adequacy >= 90:
        insights.append({"message": f"Outstanding! Your nutrient adequacy score is {adequacy:.0f}/100.", "type": "positive"})
    elif adequacy >= 70:
        insights.append({"message": f"Good work! Your nutrient adequacy score is {adequacy:.0f}/100.", "type": "positive"})
    elif adequacy < 50:
        insights.append({"message": f"Your nutrient adequacy score is {adequacy:.0f}/100. Focus on diverse whole foods.", "type": "warning"})

    if not insights:
        insights.append({"message": "Keep tracking your nutrition to see personalized insights.", "type": "neutral"})

    return insights


def get_trend_data(
    food_log_df: pd.DataFrame,
    targets_map: Dict[str, Dict[str, Any]],
    end_date: datetime,
    days: int = 7,
) -> pd.DataFrame:
    """Build a trend summary DataFrame ending on end_date.

    Args:
        food_log_df: Full food log DataFrame.
        targets_map: Target lookup.
        end_date: The last day of the range (inclusive).
        days: Number of days to include.

    Returns:
        DataFrame with daily totals and target reference columns.
    """
    date_range = get_date_range(end_date, days)
    rows = []

    for date in date_range:
        totals = get_daily_totals(food_log_df, date)
        row = {
            "Date": format_date(date),
            "Display": date.strftime("%a %d"),
            "SortDate": date,
        }
        for key in DEFAULT_NUTRIENTS.keys():
            row[key] = totals.get(key, 0.0)
        rows.append(row)

    trend_df = pd.DataFrame(rows)

    for key in DEFAULT_NUTRIENTS.keys():
        target_info = targets_map.get(key, {})
        target_val = target_info.get("target", get_default_target(key))
        trend_df[f"{key}_target"] = target_val

    # Add moving averages for key metrics
    for key in ["Calories_kcal", "Protein_g", "Carbs_g", "Fat_g", "Fiber_g"]:
        if key in trend_df.columns and len(trend_df) >= 7:
            trend_df[f"{key}_ma7"] = trend_df[key].rolling(window=7, min_periods=1).mean()

    return trend_df


def get_trend_averages(trend_df: pd.DataFrame, keys: List[str]) -> Dict[str, float]:
    """Compute averages for specified nutrients over the trend period.

    Args:
        trend_df: Output from get_trend_data.
        keys: List of nutrient keys to average.

    Returns:
        Dict mapping nutrient key -> average.
    """
    averages = {}
    for key in keys:
        if key in trend_df.columns:
            avg = trend_df[key].mean()
            averages[key] = float(avg) if not pd.isna(avg) else 0.0
    return averages


def get_weekly_data(
    food_log_df: pd.DataFrame,
    targets_map: Dict[str, Dict[str, Any]],
    end_date: datetime,
) -> pd.DataFrame:
    """Backward-compatible wrapper for 7-day trend data."""
    return get_trend_data(food_log_df, targets_map, end_date, days=7)


def get_weekly_averages(weekly_df: pd.DataFrame) -> Dict[str, float]:
    """Backward-compatible wrapper for weekly averages."""
    return get_trend_averages(weekly_df, ["Calories_kcal", "Protein_g", "Fiber_g", "Water_ml"])


def get_nutrient_adequacy_heatmap(
    food_log_df: pd.DataFrame,
    targets_map: Dict[str, Dict[str, Any]],
    end_date: datetime,
    days: int = 30,
) -> pd.DataFrame:
    """Build a nutrient adequacy heatmap DataFrame.

    Returns a DataFrame where rows = dates, columns = key nutrients,
    values = 0-100 percentage of target met.
    """
    date_range = get_date_range(end_date, days)
    rows = []
    nutrient_keys = ["Protein_g", "Fiber_g", "Vitamin_C_mg", "Vitamin_D_mcg",
                     "Calcium_mg", "Iron_mg", "Magnesium_mg", "Potassium_mg",
                     "Zinc_mg", "Omega_3_g", "Water_ml"]

    for date in date_range:
        totals = get_daily_totals(food_log_df, date)
        row = {"Date": date.strftime("%b %d")}
        for key in nutrient_keys:
            target_info = targets_map.get(key, {})
            target = target_info.get("target", get_default_target(key))
            consumed = totals.get(key, 0)
            if target > 0:
                row[key] = min((consumed / target) * 100, 150)
            else:
                row[key] = 0
        rows.append(row)

    return pd.DataFrame(rows)