"""Nutrition Dashboard — Main Streamlit Application.

A professional personal nutrition dashboard that syncs with Google Sheets
and displays daily nutrition metrics, meal breakdowns, insights, and
weekly trends.
"""

from datetime import datetime, timedelta
from typing import Optional

import streamlit as st
import pandas as pd

# Page configuration must be first
st.set_page_config(
    page_title="Nutrition Dashboard",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for professional styling
st.markdown("""
    <style>
    /* Global resets */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #f8fafc;
    }
    [data-testid="stSidebar"] .block-container {
        padding-top: 1.5rem;
    }

    /* Section headers */
    .section-header {
        font-size: 1.25rem;
        font-weight: 700;
        color: #111827;
        margin-top: 2rem;
        margin-bottom: 0.75rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e5e7eb;
    }

    /* Insight cards */
    .insight-positive {
        background-color: #ecfdf5;
        border-left: 4px solid #10b981;
        padding: 0.75rem 1rem;
        border-radius: 0 8px 8px 0;
        margin-bottom: 0.5rem;
        color: #065f46;
    }
    .insight-warning {
        background-color: #fffbeb;
        border-left: 4px solid #f59e0b;
        padding: 0.75rem 1rem;
        border-radius: 0 8px 8px 0;
        margin-bottom: 0.5rem;
        color: #92400e;
    }
    .insight-danger {
        background-color: #fef2f2;
        border-left: 4px solid #ef4444;
        padding: 0.75rem 1rem;
        border-radius: 0 8px 8px 0;
        margin-bottom: 0.5rem;
        color: #991b1b;
    }
    .insight-neutral {
        background-color: #f3f4f6;
        border-left: 4px solid #6b7280;
        padding: 0.75rem 1rem;
        border-radius: 0 8px 8px 0;
        margin-bottom: 0.5rem;
        color: #374151;
    }

    /* Tab styling override */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        padding-left: 16px;
        padding-right: 16px;
        border-radius: 8px 8px 0 0;
        font-weight: 500;
    }
    </style>
""", unsafe_allow_html=True)

from utils.date_utils import get_today_date_india, format_date, format_display_date, parse_date
from services.sheets_service import load_data
from services.nutrition_service import (
    build_targets_map,
    get_daily_summary,
    get_meal_breakdown,
    generate_insights,
    get_weekly_data,
    get_weekly_averages,
)
from components.metric_cards import render_calorie_card, render_macro_cards, render_micro_group
from components.charts import (
    render_weekly_calories_chart,
    render_weekly_protein_chart,
    render_weekly_fiber_chart,
    render_weekly_averages,
)
from components.tables import render_meal_tables
from config.nutrients import VITAMIN_KEYS, MINERAL_KEYS, OTHER_KEYS


def render_sidebar() -> datetime:
    """Render the sidebar and return the selected date.

    Returns:
        The user-selected date (timezone-aware, Asia/Kolkata).
    """
    st.sidebar.title("Nutrition Dashboard")
    st.sidebar.markdown("<p style='color: #6b7280; font-size: 0.875rem;'>Track your daily nutrition with clarity.</p>", unsafe_allow_html=True)
    st.sidebar.divider()

    # Date picker
    today = get_today_date_india()
    min_date = today - timedelta(days=365)

    selected_date = st.sidebar.date_input(
        "Select Date",
        value=today,
        min_value=min_date,
        max_value=today,
        help="Choose a date to view nutrition data. Defaults to today (Asia/Kolkata).",
    )

    # Convert to timezone-aware datetime
    selected_dt = parse_date(format_date(selected_date))

    st.sidebar.markdown(f"<p style='font-size: 0.8rem; color: #9ca3af;'>Asia/Kolkata • {format_display_date(selected_dt)}</p>", unsafe_allow_html=True)
    st.sidebar.divider()

    # Refresh button
    if st.sidebar.button("🔄 Refresh Data", use_container_width=True, help="Clear cache and reload from Google Sheets"):
        st.cache_data.clear()
        st.rerun()

    # Last sync info
    st.sidebar.markdown(f"<p style='font-size: 0.75rem; color: #9ca3af;'>Last sync: {format_display_date(get_today_date_india())} {get_today_date_india().strftime('%H:%M')}</p>", unsafe_allow_html=True)
    st.sidebar.divider()

    # Collapsible daily targets editor
    with st.sidebar.expander("⚙️ Daily Targets"):
        st.markdown("<p style='font-size: 0.8rem; color: #6b7280;'>Targets are read from the <strong>Daily_Targets</strong> sheet. Update the sheet to change values.</p>", unsafe_allow_html=True)

    return selected_dt


def render_insights(insights: list) -> None:
    """Render the daily insights section.

    Args:
        insights: List of insight dicts with 'message' and 'type'.
    """
    st.markdown('<div class="section-header">Daily Insights</div>', unsafe_allow_html=True)

    if not insights:
        st.info("No insights available for the selected date.")
        return

    for insight in insights:
        css_class = f"insight-{insight['type']}"
        st.markdown(f'<div class="{css_class}">{insight["message"]}</div>', unsafe_allow_html=True)


def render_weekly_section(weekly_df: pd.DataFrame, averages: dict) -> None:
    """Render the weekly trends section with charts and averages.

    Args:
        weekly_df: Weekly summary DataFrame.
        averages: Weekly averages dict.
    """
    st.markdown('<div class="section-header">Weekly Trends</div>', unsafe_allow_html=True)

    # Weekly averages row
    render_weekly_averages(averages)

    st.divider()

    # Charts
    col1, col2 = st.columns(2)
    with col1:
        render_weekly_calories_chart(weekly_df)
    with col2:
        render_weekly_protein_chart(weekly_df)

    st.divider()
    render_weekly_fiber_chart(weekly_df)


def main() -> None:
    """Main application entry point."""
    selected_date = render_sidebar()

    # Load data
    try:
        food_log_df, targets_df, is_live = load_data(force_refresh=False)
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        st.stop()

    # Data source indicator
    if not is_live:
        st.info("📊 Running with **demo data**. Configure Google Sheets credentials in `.streamlit/secrets.toml` to sync with your live data.")

    # Build targets map
    targets_map = build_targets_map(targets_df)

    # Daily summary
    daily_summary = get_daily_summary(food_log_df, targets_map, selected_date)

    # Meal breakdown
    meals = get_meal_breakdown(food_log_df, selected_date)

    # Weekly data
    weekly_df = get_weekly_data(food_log_df, targets_map, selected_date)
    weekly_averages = get_weekly_averages(weekly_df)

    # Insights
    insights = generate_insights(daily_summary)

    # ─── TOP DASHBOARD ───
    st.markdown('<div class="section-header">Daily Summary</div>', unsafe_allow_html=True)
    render_calorie_card(daily_summary)

    # ─── MACRONUTRIENTS ───
    st.markdown('<div class="section-header">Macronutrients</div>', unsafe_allow_html=True)
    render_macro_cards(daily_summary)

    # ─── MICRONUTRIENTS ───
    st.markdown('<div class="section-header">Micronutrients</div>', unsafe_allow_html=True)

    vit_tab, min_tab, other_tab = st.tabs(["Vitamins", "Minerals", "Other Nutrients"])

    with vit_tab:
        render_micro_group(daily_summary, VITAMIN_KEYS, "Vitamins")

    with min_tab:
        render_micro_group(daily_summary, MINERAL_KEYS, "Minerals")

    with other_tab:
        render_micro_group(daily_summary, OTHER_KEYS, "Other Nutrients")

    # ─── MEAL BREAKDOWN ───
    st.markdown('<div class="section-header">Meal Breakdown</div>', unsafe_allow_html=True)
    render_meal_tables(meals)

    # ─── INSIGHTS ───
    render_insights(insights)

    # ─── WEEKLY TRENDS ───
    render_weekly_section(weekly_df, weekly_averages)

    # Footer
    st.divider()
    st.markdown("<p style='text-align: center; color: #9ca3af; font-size: 0.75rem;'>Nutrition Dashboard • Built with Streamlit</p>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
