"""Nutrient configuration and defaults.

Defines nutrient metadata, default targets, units, and classification
(target vs limit) for the nutrition dashboard.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class NutrientConfig:
    """Configuration for a single nutrient."""
    name: str
    unit: str
    default_target: float
    nutrient_type: str  # 'target' or 'limit'
    category: str       # 'macro', 'vitamin', 'mineral', 'other'
    display_precision: int = 1


# Default daily targets / limits when Google Sheet is unavailable.
DEFAULT_NUTRIENTS: Dict[str, NutrientConfig] = {
    # Macronutrients
    "Calories_kcal": NutrientConfig("Calories", "kcal", 2200.0, "target", "macro", 0),
    "Protein_g": NutrientConfig("Protein", "g", 120.0, "target", "macro", 1),
    "Carbs_g": NutrientConfig("Carbohydrates", "g", 250.0, "target", "macro", 1),
    "Fat_g": NutrientConfig("Fat", "g", 70.0, "target", "macro", 1),
    "Fiber_g": NutrientConfig("Fiber", "g", 35.0, "target", "macro", 1),
    "Sugar_g": NutrientConfig("Sugar", "g", 50.0, "limit", "macro", 1),

    # Vitamins
    "Vitamin_A_mcg": NutrientConfig("Vitamin A", "mcg", 900.0, "target", "vitamin", 1),
    "Vitamin_B12_mcg": NutrientConfig("Vitamin B12", "mcg", 2.4, "target", "vitamin", 1),
    "Vitamin_C_mg": NutrientConfig("Vitamin C", "mg", 90.0, "target", "vitamin", 1),
    "Vitamin_D_mcg": NutrientConfig("Vitamin D", "mcg", 20.0, "target", "vitamin", 1),
    "Vitamin_E_mg": NutrientConfig("Vitamin E", "mg", 15.0, "target", "vitamin", 1),
    "Vitamin_K_mcg": NutrientConfig("Vitamin K", "mcg", 120.0, "target", "vitamin", 1),
    "Folate_mcg": NutrientConfig("Folate", "mcg", 400.0, "target", "vitamin", 1),

    # Minerals
    "Calcium_mg": NutrientConfig("Calcium", "mg", 1000.0, "target", "mineral", 0),
    "Iron_mg": NutrientConfig("Iron", "mg", 18.0, "target", "mineral", 1),
    "Magnesium_mg": NutrientConfig("Magnesium", "mg", 400.0, "target", "mineral", 0),
    "Potassium_mg": NutrientConfig("Potassium", "mg", 3500.0, "target", "mineral", 0),
    "Zinc_mg": NutrientConfig("Zinc", "mg", 11.0, "target", "mineral", 1),
    "Sodium_mg": NutrientConfig("Sodium", "mg", 2300.0, "limit", "mineral", 0),

    # Other
    "Saturated_Fat_g": NutrientConfig("Saturated Fat", "g", 20.0, "limit", "other", 1),
    "Cholesterol_mg": NutrientConfig("Cholesterol", "mg", 300.0, "limit", "other", 0),
    "Omega_3_g": NutrientConfig("Omega-3", "g", 2.0, "target", "other", 1),
    "Water_ml": NutrientConfig("Water", "ml", 2500.0, "target", "other", 0),
}

# Map user's actual Google Sheet column names to our internal keys.
# Keys = user's column headers, Values = our internal keys.
# Columns not listed here are ignored. Missing mapped columns default to 0.
FOOD_LOG_COLUMN_MAP = {
    "Date": "Date",
    "Meal": "Meal",
    "Food / Drink": "Food",
    "Serving Size (g)": "Quantity_g",
    "Calories (kcal)": "Calories_kcal",
    "Protein (g)": "Protein_g",
    "Carbs (g)": "Carbs_g",
    "Fiber (g)": "Fiber_g",
    "Total Sugar (g)": "Sugar_g",
    "Fat (g)": "Fat_g",
    "Saturated Fat (g)": "Saturated_Fat_g",
    "Cholesterol (mg)": "Cholesterol_mg",
    "Sodium (mg)": "Sodium_mg",
    "Potassium (mg)": "Potassium_mg",
    "Calcium (mg)": "Calcium_mg",
    "Iron (mg)": "Iron_mg",
    "Magnesium (mg)": "Magnesium_mg",
    "Zinc (mg)": "Zinc_mg",
    "Vitamin A (mcg RAE)": "Vitamin_A_mcg",
    "Vitamin C (mg)": "Vitamin_C_mg",
    "Vitamin D (mcg)": "Vitamin_D_mcg",
    "Vitamin E (mg)": "Vitamin_E_mg",
    "Vitamin K (mcg)": "Vitamin_K_mcg",
    "Folate B9 (mcg DFE)": "Folate_mcg",
    "Vitamin B12 (mcg)": "Vitamin_B12_mcg",
    "Omega-3 (g)": "Omega_3_g",
    "Water (ml)": "Water_ml",
}

# Internal columns we need for the app to function
REQUIRED_INTERNAL_COLUMNS = ["Date", "Meal", "Food", "Quantity_g"] + list(DEFAULT_NUTRIENTS.keys())

# Daily_Targets sheet columns
DAILY_TARGETS_COLUMNS = ["Nutrient", "Target", "Unit", "Type"]

# Meal order for display
MEAL_ORDER = ["Breakfast", "Lunch", "Snacks", "Dinner", "Other"]

# Nutrient categories for grouping display
VITAMIN_KEYS = [k for k, v in DEFAULT_NUTRIENTS.items() if v.category == "vitamin"]
MINERAL_KEYS = [k for k, v in DEFAULT_NUTRIENTS.items() if v.category == "mineral"]
OTHER_KEYS = [k for k, v in DEFAULT_NUTRIENTS.items() if v.category == "other"]
MACRO_KEYS = [k for k, v in DEFAULT_NUTRIENTS.items() if v.category == "macro"]


def get_nutrient_label(key: str) -> str:
    """Return human-readable label for a nutrient key."""
    config = DEFAULT_NUTRIENTS.get(key)
    return config.name if config else key


def get_nutrient_unit(key: str) -> str:
    """Return unit for a nutrient key."""
    config = DEFAULT_NUTRIENTS.get(key)
    return config.unit if config else ""


def get_nutrient_type(key: str) -> str:
    """Return 'target' or 'limit' for a nutrient key."""
    config = DEFAULT_NUTRIENTS.get(key)
    return config.nutrient_type if config else "target"


def get_default_target(key: str) -> float:
    """Return default target value for a nutrient key."""
    config = DEFAULT_NUTRIENTS.get(key)
    return config.default_target if config else 0.0


def get_display_precision(key: str) -> int:
    """Return display precision for a nutrient key."""
    config = DEFAULT_NUTRIENTS.get(key)
    return config.display_precision if config else 1
