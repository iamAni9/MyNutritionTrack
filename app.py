"""Nutrition Dashboard — Main Streamlit Application.

A professional personal nutrition dashboard that syncs with Google Sheets
and displays daily nutrition metrics, meal breakdowns, insights, body
composition tracking, and dynamic trend analytics.
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
    /* Fix tab header being hidden behind Streamlit top bar */
    .stApp > header {
        z-index: 999;
    }
    .block-container {
        padding-top: 3rem;
        padding-bottom: 2rem;
    }
    /* Add top margin to tab content so tabs aren't hidden */
    .stTabs {
        margin-top: 1rem;
    }
    [data-testid="stSidebar"] {
        background-color: #f8fafc;
    }
    [data-testid="stSidebar"] .block-container {
        padding-top: 1.5rem;
    }
    .section-header {
        font-size: 1.25rem;
        font-weight: 700;
        color: #111827;
        margin-top: 2.5rem;
        margin-bottom: 0.75rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e5e7eb;
    }
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
    .score-row {
        display: flex;
        gap: 1rem;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

from utils.date_utils import (
    get_today_date_india, format_date, format_display_date, parse_date,
    get_date_range,
)
from services.sheets_service import load_data
from services.nutrition_service import (
    build_targets_map,
    get_daily_summary,
    get_meal_breakdown,
    generate_insights,
    get_trend_data,
    get_trend_averages,
    get_weekly_data,
    get_weekly_averages,
    compute_nutrient_adequacy_score,
    compute_macro_distribution,
    compute_calorie_quality_index,
    get_nutrient_adequacy_heatmap,
)
from services.body_metrics_service import (
    get_latest_body_metrics,
    compute_body_metric_change,
    generate_body_insights,
)
from components.metric_cards import (
    render_calorie_card,
    render_macro_cards,
    render_micro_group,
    render_score_card,
    render_body_metric_card,
)
from components.charts import (
    render_calorie_trend_chart,
    render_protein_trend_chart,
    render_macro_area_chart,
    render_fiber_trend_chart,
    render_macro_pie_chart,
    render_nutrient_heatmap,
    render_body_composition_dashboard,
    render_trend_averages,
)
from components.tables import render_meal_tables
from config.nutrients import VITAMIN_KEYS, MINERAL_KEYS, FAT_DETAIL_KEYS, OTHER_KEYS
from config.body_metrics import BODY_METRIC_KEYS


def render_sidebar() -> tuple:
    """Render the sidebar and return the selected date, time range, and active tab.

    Returns:
        Tuple of (selected_date, trend_days, active_tab).
    """
    st.sidebar.title("🥗 Nutrition Dashboard")
    st.sidebar.markdown("<p style='color: #6b7280; font-size: 0.875rem;'>Professional nutrition & body composition tracking.</p>", unsafe_allow_html=True)
    st.sidebar.divider()

    # ─── Date picker ───
    today = get_today_date_india()
    min_date = today - timedelta(days=365)

    selected_date = st.sidebar.date_input(
        "📅 Select Date",
        value=today,
        min_value=min_date,
        max_value=today,
        help="Choose a date to view nutrition data. Defaults to today (Asia/Kolkata).",
    )
    selected_dt = parse_date(format_date(selected_date))

    st.sidebar.markdown(f"<p style='font-size: 0.8rem; color: #9ca3af;'>Asia/Kolkata • {format_display_date(selected_dt)}</p>", unsafe_allow_html=True)
    st.sidebar.divider()

    # ─── Time Range Selector ───
    st.sidebar.markdown("#### 📊 Trend Range")
    trend_option = st.sidebar.radio(
        "Select trend period",
        options=["7 Days", "30 Days", "90 Days"],
        index=0,
        horizontal=True,
        label_visibility="collapsed",
    )
    trend_days = {"7 Days": 7, "30 Days": 30, "90 Days": 90}[trend_option]

    st.sidebar.divider()

    # ─── Refresh button ───
    if st.sidebar.button("🔄 Refresh Data", use_container_width=True, help="Clear cache and reload from Google Sheets"):
        st.cache_data.clear()
        st.rerun()

    # Last sync info
    st.sidebar.markdown(f"<p style='font-size: 0.75rem; color: #9ca3af;'>Last sync: {format_display_date(get_today_date_india())} {get_today_date_india().strftime('%H:%M')}</p>", unsafe_allow_html=True)
    st.sidebar.divider()

    # ─── Targets info ───
    with st.sidebar.expander("⚙️ Daily Targets"):
        st.markdown("<p style='font-size: 0.8rem; color: #6b7280;'>Targets are read from the <strong>Daily_Targets</strong> sheet. Update the sheet to change values.</p>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 0.8rem; color: #6b7280;'>Body metrics are read from the <strong>Body_Metrics</strong> sheet (optional).</p>", unsafe_allow_html=True)

    return selected_dt, trend_days


def render_insights(insights: list) -> None:
    """Render the daily insights section."""
    st.markdown('<div class="section-header">💡 Daily Insights</div>', unsafe_allow_html=True)

    if not insights:
        st.info("No insights available for the selected date.")
        return

    for insight in insights:
        css_class = f"insight-{insight['type']}"
        st.markdown(f'<div class="{css_class}">{insight["message"]}</div>', unsafe_allow_html=True)


def render_dashboard_tab(
    selected_date: datetime,
    food_log_df: pd.DataFrame,
    targets_map: dict,
    body_metrics_df: Optional[pd.DataFrame],
) -> None:
    """Render the main Dashboard tab."""

    # ─── Daily Summary ───
    st.markdown('<div class="section-header">📋 Daily Summary</div>', unsafe_allow_html=True)
    daily_summary = get_daily_summary(food_log_df, targets_map, selected_date)
    render_calorie_card(daily_summary)

    # ─── Professional Score Cards ───
    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">🎯 Daily Scores</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        adequacy = compute_nutrient_adequacy_score(daily_summary)
        render_score_card("Nutrient Adequacy", adequacy, 100, "%")
    with col2:
        quality = compute_calorie_quality_index(daily_summary)
        render_score_card("Calorie Quality", quality, 100, "")
    with col3:
        macro_dist = compute_macro_distribution(daily_summary)
        protein_pct = macro_dist.get("Protein", 0)
        render_score_card("Protein Ratio", protein_pct, 40, "%")

    # ─── Macronutrients ───
    st.markdown('<div class="section-header">🥩 Macronutrients</div>', unsafe_allow_html=True)
    render_macro_cards(daily_summary)

    # ─── Macro Distribution Pie ───
    st.markdown('<div class="section-header">🍽️ Macro Distribution</div>', unsafe_allow_html=True)
    col1, col2 = st.columns([1, 2])
    with col1:
        render_macro_pie_chart(daily_summary)
    with col2:
        macro_dist = compute_macro_distribution(daily_summary)
        st.markdown("""
            <div style="background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 1.25rem; height: 100%;">
                <div style="font-size: 1rem; font-weight: 600; color: #111827; margin-bottom: 1rem;">Macro Breakdown</div>
        """, unsafe_allow_html=True)
        for macro, pct in macro_dist.items():
            color = {"Protein": "#3b82f6", "Carbs": "#10b981", "Fat": "#f59e0b"}[macro]
            st.markdown(f"""
                <div style="display: flex; align-items: center; margin-bottom: 0.75rem;">
                    <div style="width: 12px; height: 12px; background-color: {color}; border-radius: 3px; margin-right: 0.75rem;"></div>
                    <div style="flex: 1; font-weight: 500; color: #374151;">{macro}</div>
                    <div style="font-weight: 700; color: #111827;">{pct:.1f}%</div>
                </div>
                <div style="width: 100%; height: 6px; background-color: #e5e7eb; border-radius: 3px; margin-bottom: 1rem;">
                    <div style="width: {pct}%; height: 100%; background-color: {color}; border-radius: 3px;"></div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ─── Micronutrients ───
    st.markdown('<div class="section-header">🧬 Micronutrients</div>', unsafe_allow_html=True)
    vit_tab, min_tab, fat_tab, other_tab = st.tabs(["Vitamins", "Minerals", "Fats & Cholesterol", "Other"])

    with vit_tab:
        render_micro_group(daily_summary, VITAMIN_KEYS, "Vitamins")
    with min_tab:
        render_micro_group(daily_summary, MINERAL_KEYS, "Minerals")
    with fat_tab:
        render_micro_group(daily_summary, FAT_DETAIL_KEYS, "Fats & Cholesterol")
    with other_tab:
        render_micro_group(daily_summary, OTHER_KEYS, "Other Nutrients")

    # ─── Meal Breakdown ───
    st.markdown('<div class="section-header">🍱 Meal Breakdown</div>', unsafe_allow_html=True)
    meals = get_meal_breakdown(food_log_df, selected_date)
    render_meal_tables(meals)

    # ─── Insights ───
    insights = generate_insights(daily_summary)
    render_insights(insights)


def render_trends_tab(
    selected_date: datetime,
    food_log_df: pd.DataFrame,
    targets_map: dict,
    trend_days: int,
) -> None:
    """Render the Trends & Analytics tab."""

    trend_df = get_trend_data(food_log_df, targets_map, selected_date, days=trend_days)
    trend_averages = get_trend_averages(trend_df, keys=["Calories_kcal", "Protein_g", "Carbs_g", "Fat_g", "Fiber_g", "Water_ml"])

    # ─── Trend Averages ───
    st.markdown('<div class="section-header">📈 Period Averages</div>', unsafe_allow_html=True)
    render_trend_averages(trend_averages, keys=["Calories_kcal", "Protein_g", "Carbs_g", "Fat_g", "Fiber_g", "Water_ml"])

    st.divider()

    # ─── Calorie & Protein Charts ───
    col1, col2 = st.columns(2)
    with col1:
        render_calorie_trend_chart(trend_df)
    with col2:
        render_protein_trend_chart(trend_df)

    st.divider()

    # ─── Macro Area Chart ───
    render_macro_area_chart(trend_df)

    st.divider()

    # ─── Fiber Chart ───
    render_fiber_trend_chart(trend_df)

    st.divider()

    # ─── Nutrient Adequacy Heatmap (only for 30D or 90D) ───
    if trend_days >= 30:
        st.markdown('<div class="section-header">🔥 Nutrient Adequacy Heatmap</div>', unsafe_allow_html=True)
        heatmap_days = min(trend_days, 30)
        heatmap_df = get_nutrient_adequacy_heatmap(food_log_df, targets_map, selected_date, days=heatmap_days)
        render_nutrient_heatmap(heatmap_df)


def render_body_tab(
    selected_date: datetime,
    body_metrics_df: Optional[pd.DataFrame],
    trend_days: int,
) -> None:
    """Render the Body Composition tab."""

    st.markdown('<div class="section-header">⚖️ Body Composition Overview</div>', unsafe_allow_html=True)

    if body_metrics_df is None or body_metrics_df.empty:
        st.info("""
            📋 **No body composition data found.**

            To track body metrics professionally, add a new sheet tab named **`Body_Metrics`** to your Google Sheet with these columns:

            `Date | Weight_kg | Body_Fat_pct | Muscle_Mass_kg | BMI | Waist_cm | Visceral_Fat | Bone_Mass_kg | Water_pct | BMR_kcal | Subcutaneous_Fat_pct`

            Log your measurements daily or weekly to see trends and insights.
        """)
        return

    # ─── Latest Metrics Cards ───
    latest = get_latest_body_metrics(body_metrics_df)
    if latest:
        cols = st.columns(min(len(BODY_METRIC_KEYS), 5))
        for idx, key in enumerate(BODY_METRIC_KEYS):
            with cols[idx % len(cols)]:
                change = compute_body_metric_change(body_metrics_df, key, days=30)
                render_body_metric_card(key, latest.get(key), change)

    st.divider()

    # ─── Body Insights ───
    body_insights = generate_body_insights(body_metrics_df)
    st.markdown('<div class="section-header">💡 Body Composition Insights</div>', unsafe_allow_html=True)
    for insight in body_insights:
        css_class = f"insight-{insight['type']}"
        st.markdown(f'<div class="{css_class}">{insight["message"]}</div>', unsafe_allow_html=True)

    st.divider()

    # ─── Body Composition Charts ───
    st.markdown('<div class="section-header">📉 Body Composition Trends</div>', unsafe_allow_html=True)
    render_body_composition_dashboard(body_metrics_df, selected_date, days=trend_days)


def render_meals_tab(
    selected_date: datetime,
    food_log_df: pd.DataFrame,
) -> None:
    """Render the detailed Meals tab."""

    st.markdown('<div class="section-header">🍱 Detailed Meal Log</div>', unsafe_allow_html=True)
    meals = get_meal_breakdown(food_log_df, selected_date)

    if not meals:
        st.info("No food entries found for the selected date.")
        return

    render_meal_tables(meals)


def main() -> None:
    """Main application entry point."""
    selected_date, trend_days = render_sidebar()

    # Load data
    try:
        food_log_df, targets_df, body_metrics_df, is_live = load_data(force_refresh=False)
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        st.stop()

    # Data source indicator
    if not is_live:
        st.info("📊 Running with **demo data**. Configure Google Sheets credentials in `.streamlit/secrets.toml` to sync with your live data.")

    # Build targets map
    targets_map = build_targets_map(targets_df)

    # ─── MAIN TABS ───
    dashboard_tab, trends_tab, body_tab, meals_tab = st.tabs([
        "📋 Dashboard",
        "📈 Trends & Analytics",
        "⚖️ Body Composition",
        "🍱 Meal Details",
    ])

    with dashboard_tab:
        render_dashboard_tab(selected_date, food_log_df, targets_map, body_metrics_df)

    with trends_tab:
        render_trends_tab(selected_date, food_log_df, targets_map, trend_days)

    with body_tab:
        render_body_tab(selected_date, body_metrics_df, trend_days)

    with meals_tab:
        render_meals_tab(selected_date, food_log_df)

    # Footer
    st.divider()
    st.markdown("<p style='text-align: center; color: #9ca3af; font-size: 0.75rem;'>Nutrition Dashboard • Built with Streamlit • Professional Health Tracking</p>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()