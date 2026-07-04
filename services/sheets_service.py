"""Google Sheets integration service.

Handles authentication, reading data from the Food_Log and Daily_Targets tabs,
renames columns to match internal keys, and provides fallback mock data
when credentials are unavailable.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json

import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from gspread.exceptions import APIError, SpreadsheetNotFound

from config.nutrients import (
    FOOD_LOG_COLUMN_MAP,
    REQUIRED_INTERNAL_COLUMNS,
    DAILY_TARGETS_COLUMNS,
)
from utils.date_utils import format_date

# Google Sheets scope
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]

# Cache TTL in seconds (5 minutes)
CACHE_TTL = 300


def _get_credentials() -> Optional[Credentials]:
    """Load service account credentials from Streamlit secrets.

    Returns:
        Credentials object or None if secrets are not configured.
    """
    try:
        secrets = st.secrets.get("google_sheets", {})
        if not secrets:
            return None

        # gspread expects a dict with specific keys; Streamlit secrets
        # are parsed as a nested dict. We reconstruct the service-account JSON.
        creds_info = dict(secrets)
        # Ensure private_key has proper newlines
        if "private_key" in creds_info:
            creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")

        return Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    except Exception as e:
        st.error(f"Error loading Google Sheets credentials: {e}")
        return None


def _get_sheet_id() -> Optional[str]:
    """Return the Google Sheet ID from Streamlit secrets."""
    try:
        return st.secrets.get("google_sheets", {}).get("sheet_id")
    except Exception:
        return None


@st.cache_data(ttl=CACHE_TTL, show_spinner="Fetching data from Google Sheets...")
def _fetch_sheet_data(sheet_id: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Fetch Food_Log and Daily_Targets data from Google Sheets.

    Args:
        sheet_id: The Google Sheet document ID.

    Returns:
        Tuple of (food_log_df, daily_targets_df).

    Raises:
        Exception: If the sheet cannot be accessed or parsed.
    """
    creds = _get_credentials()
    if not creds:
        raise ConnectionError("Google Sheets credentials not configured.")

    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(sheet_id)

    # Read Food_Log
    food_log_ws = spreadsheet.worksheet("Food_Log")
    food_log_data = food_log_ws.get_all_records()
    food_log_df = pd.DataFrame(food_log_data)

    # Rename user columns to internal keys
    food_log_df.rename(columns=FOOD_LOG_COLUMN_MAP, inplace=True)

    # Add any missing nutrient columns with 0
    for col in REQUIRED_INTERNAL_COLUMNS:
        if col not in food_log_df.columns:
            food_log_df[col] = 0.0

    # Validate only truly required columns (Date, Meal, Food, Quantity_g)
    missing_required = [col for col in ["Date", "Meal", "Food", "Quantity_g"] if col not in food_log_df.columns]
    if missing_required:
        raise ValueError(f"Food_Log sheet missing required columns after mapping: {missing_required}. "
                         f"Please check your column headers match the expected format.")

    # Convert numeric columns to float
    numeric_cols = [c for c in REQUIRED_INTERNAL_COLUMNS if c not in ["Date", "Meal", "Food"]]
    for col in numeric_cols:
        food_log_df[col] = pd.to_numeric(food_log_df[col], errors="coerce").fillna(0.0)

    # Read Daily_Targets
    targets_ws = spreadsheet.worksheet("Daily_Targets")
    targets_data = targets_ws.get_all_records()
    targets_df = pd.DataFrame(targets_data)

    missing_targets = [col for col in DAILY_TARGETS_COLUMNS if col not in targets_df.columns]
    if missing_targets:
        raise ValueError(f"Daily_Targets sheet missing columns: {missing_targets}")

    return food_log_df, targets_df


def _generate_mock_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Generate realistic mock data for local development / demo.

    Returns:
        Tuple of (food_log_df, daily_targets_df).
    """
    from datetime import timedelta
    from utils.date_utils import get_today_date_india
    from config.nutrients import DEFAULT_NUTRIENTS

    today = get_today_date_india()

    # Mock food log for today and past 6 days
    mock_entries = []
    meals = ["Breakfast", "Lunch", "Snacks", "Dinner", "Other"]

    foods = {
        "Breakfast": [
            ("Oatmeal with berries", 250, 150, 5, 27, 3, 4, 8, 1, 0, 0, 2, 10, 1, 30, 0.5, 0, 0, 0, 0, 5, 0, 0.5, 1, 20, 0.1, 200),
            ("Boiled eggs", 100, 140, 12, 1, 10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 50),
        ],
        "Lunch": [
            ("Grilled chicken breast", 150, 248, 46, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
            ("Brown rice", 200, 248, 5, 52, 2, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
            ("Mixed vegetables", 150, 80, 3, 15, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
        ],
        "Snacks": [
            ("Greek yogurt", 150, 100, 15, 6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
            ("Almonds", 30, 180, 6, 6, 15, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
        ],
        "Dinner": [
            ("Salmon fillet", 150, 350, 35, 0, 20, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
            ("Quinoa", 150, 180, 6, 30, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
            ("Steamed broccoli", 100, 55, 4, 11, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
        ],
    }

    for day_offset in range(7):
        date = today - timedelta(days=day_offset)
        date_str = format_date(date)
        for meal, food_list in foods.items():
            for food_tuple in food_list:
                mock_entries.append({
                    "Date": date_str,
                    "Meal": meal,
                    "Food": food_tuple[0],
                    "Quantity_g": food_tuple[1],
                    "Calories_kcal": food_tuple[2] + (day_offset * 10),
                    "Protein_g": food_tuple[3],
                    "Carbs_g": food_tuple[4],
                    "Fat_g": food_tuple[5],
                    "Fiber_g": food_tuple[6],
                    "Sugar_g": food_tuple[7],
                    "Saturated_Fat_g": food_tuple[8],
                    "Cholesterol_mg": food_tuple[9],
                    "Sodium_mg": food_tuple[10],
                    "Calcium_mg": food_tuple[11],
                    "Iron_mg": food_tuple[12],
                    "Magnesium_mg": food_tuple[13],
                    "Potassium_mg": food_tuple[14],
                    "Zinc_mg": food_tuple[15],
                    "Vitamin_A_mcg": food_tuple[16],
                    "Vitamin_B12_mcg": food_tuple[17],
                    "Vitamin_C_mg": food_tuple[18],
                    "Vitamin_D_mcg": food_tuple[19],
                    "Vitamin_E_mg": food_tuple[20],
                    "Vitamin_K_mcg": food_tuple[21],
                    "Folate_mcg": food_tuple[22],
                    "Omega_3_g": food_tuple[23],
                    "Water_ml": food_tuple[24],
                })

    food_log_df = pd.DataFrame(mock_entries)

    # Mock daily targets
    targets_data = []
    for key, config in DEFAULT_NUTRIENTS.items():
        targets_data.append({
            "Nutrient": key,
            "Target": config.default_target,
            "Unit": config.unit,
            "Type": config.nutrient_type,
        })
    targets_df = pd.DataFrame(targets_data)

    return food_log_df, targets_df


def load_data(force_refresh: bool = False) -> Tuple[pd.DataFrame, pd.DataFrame, bool]:
    """Load nutrition data from Google Sheets or fall back to mock data.

    Args:
        force_refresh: If True, clears cache and re-fetches from Google Sheets.

    Returns:
        Tuple of (food_log_df, daily_targets_df, is_live).
        is_live is True if data came from Google Sheets, False if mock.
    """
    if force_refresh:
        _fetch_sheet_data.clear()

    sheet_id = _get_sheet_id()
    creds = _get_credentials()

    if sheet_id and creds:
        try:
            food_log_df, targets_df = _fetch_sheet_data(sheet_id)
            return food_log_df, targets_df, True
        except Exception as e:
            st.warning(f"Could not load Google Sheets data: {e}. Using mock data instead.")
            mock_df, mock_targets = _generate_mock_data()
            return mock_df, mock_targets, False
    else:
        mock_df, mock_targets = _generate_mock_data()
        return mock_df, mock_targets, False
