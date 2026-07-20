"""Plotly chart components for the nutrition dashboard.

Generates interactive, responsive charts for trends, nutrient comparisons,
body composition, and professional analytics.
"""

from typing import Dict, List, Optional, Any
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime
from config.nutrients import get_nutrient_label
from config.body_metrics import get_body_metric_label, get_body_metric_unit


# ─── Shared styling ───
_COLOR_PRIMARY = "#3b82f6"
_COLOR_SECONDARY = "#8b5cf6"
_COLOR_SUCCESS = "#10b981"
_COLOR_WARNING = "#f59e0b"
_COLOR_DANGER = "#ef4444"
_COLOR_NEUTRAL = "#6b7280"
_BG_COLOR = "#f9fafb"
_GRID_COLOR = "#e5e7eb"
_TEXT_COLOR = "#111827"


def _base_layout(fig: go.Figure, title: str, height: int = 350) -> go.Figure:
    """Apply shared layout settings."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color=_TEXT_COLOR)),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=60, b=40, l=50, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=_BG_COLOR,
        height=height,
        font=dict(family="Arial, sans-serif", color=_TEXT_COLOR),
    )
    fig.update_xaxes(showgrid=False, gridcolor=_GRID_COLOR)
    fig.update_yaxes(showgrid=True, gridcolor=_GRID_COLOR, zeroline=False)
    return fig


# ─── Calorie Trend ───
def render_calorie_trend_chart(trend_df: pd.DataFrame) -> None:
    """Render a line chart of daily calories vs target with 7-day MA."""
    if trend_df.empty or "Calories_kcal" not in trend_df.columns:
        st.info("No calorie trend data available.")
        return

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=trend_df["Display"],
        y=trend_df["Calories_kcal"],
        mode="lines+markers",
        name="Calories",
        line=dict(color=_COLOR_PRIMARY, width=2),
        marker=dict(size=6, color=_COLOR_PRIMARY),
        hovertemplate="%{x}<br>Calories: %{y:.0f} kcal<extra></extra>",
    ))

    if "Calories_kcal_ma7" in trend_df.columns and len(trend_df) >= 7:
        fig.add_trace(go.Scatter(
            x=trend_df["Display"],
            y=trend_df["Calories_kcal_ma7"],
            mode="lines",
            name="7-Day Avg",
            line=dict(color=_COLOR_SECONDARY, width=2, dash="dot"),
            hovertemplate="%{x}<br>7-Day Avg: %{y:.0f} kcal<extra></extra>",
        ))

    fig.add_trace(go.Scatter(
        x=trend_df["Display"],
        y=trend_df["Calories_kcal_target"],
        mode="lines",
        name="Target",
        line=dict(color=_COLOR_SUCCESS, width=2, dash="dash"),
        hovertemplate="%{x}<br>Target: %{y:.0f} kcal<extra></extra>",
    ))

    fig = _base_layout(fig, "Calorie Trend")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ─── Protein Trend ───
def render_protein_trend_chart(trend_df: pd.DataFrame) -> None:
    """Render a bar chart of daily protein vs target."""
    if trend_df.empty or "Protein_g" not in trend_df.columns:
        st.info("No protein trend data available.")
        return

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=trend_df["Display"],
        y=trend_df["Protein_g"],
        name="Protein",
        marker_color=_COLOR_PRIMARY,
        hovertemplate="%{x}<br>Protein: %{y:.1f} g<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=trend_df["Display"],
        y=trend_df["Protein_g_target"],
        mode="lines",
        name="Target",
        line=dict(color=_COLOR_SUCCESS, width=2, dash="dash"),
        hovertemplate="%{x}<br>Target: %{y:.1f} g<extra></extra>",
    ))

    fig = _base_layout(fig, "Protein Trend")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ─── Macro Distribution Over Time (Stacked Area) ───
def render_macro_area_chart(trend_df: pd.DataFrame) -> None:
    """Render a stacked area chart of macro calories over time."""
    if trend_df.empty or "Protein_g" not in trend_df.columns:
        st.info("No macro data available.")
        return

    trend_df = trend_df.copy()
    trend_df["Protein_kcal"] = trend_df["Protein_g"] * 4
    trend_df["Carbs_kcal"] = trend_df["Carbs_g"] * 4
    trend_df["Fat_kcal"] = trend_df["Fat_g"] * 9

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=trend_df["Display"],
        y=trend_df["Protein_kcal"],
        mode="lines",
        stackgroup="one",
        name="Protein",
        line=dict(width=0.5, color="#3b82f6"),
        fillcolor="rgba(59,130,246,0.7)",
        hovertemplate="%{x}<br>Protein: %{y:.0f} kcal<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=trend_df["Display"],
        y=trend_df["Carbs_kcal"],
        mode="lines",
        stackgroup="one",
        name="Carbs",
        line=dict(width=0.5, color="#10b981"),
        fillcolor="rgba(16,185,129,0.7)",
        hovertemplate="%{x}<br>Carbs: %{y:.0f} kcal<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=trend_df["Display"],
        y=trend_df["Fat_kcal"],
        mode="lines",
        stackgroup="one",
        name="Fat",
        line=dict(width=0.5, color="#f59e0b"),
        fillcolor="rgba(245,158,11,0.7)",
        hovertemplate="%{x}<br>Fat: %{y:.0f} kcal<extra></extra>",
    ))

    fig = _base_layout(fig, "Macro Energy Distribution")
    fig.update_layout(yaxis_title="kcal")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ─── Fiber Trend ───
def render_fiber_trend_chart(trend_df: pd.DataFrame) -> None:
    """Render a line chart for daily fiber trend."""
    if trend_df.empty or "Fiber_g" not in trend_df.columns:
        st.info("No fiber trend data available.")
        return

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=trend_df["Display"],
        y=trend_df["Fiber_g"],
        mode="lines+markers+text",
        name="Fiber",
        line=dict(color=_COLOR_SECONDARY, width=3),
        marker=dict(size=8, color=_COLOR_SECONDARY),
        text=trend_df["Fiber_g"].apply(lambda x: f"{x:.0f}"),
        textposition="top center",
        textfont=dict(size=10, color=_COLOR_NEUTRAL),
        hovertemplate="%{x}<br>Fiber: %{y:.1f} g<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=trend_df["Display"],
        y=trend_df["Fiber_g_target"],
        mode="lines",
        name="Target",
        line=dict(color=_COLOR_SUCCESS, width=2, dash="dash"),
        hovertemplate="%{x}<br>Target: %{y:.1f} g<extra></extra>",
    ))

    fig = _base_layout(fig, "Fiber Trend")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ─── Macro Distribution Pie (Single Day) ───
def render_macro_pie_chart(summary: Dict[str, Any]) -> None:
    """Render a donut chart showing today's macro calorie distribution."""
    cal = summary.get("Calories_kcal", {}).get("consumed", 0)
    if cal == 0:
        st.info("No calorie data for macro distribution.")
        return

    protein_cal = summary.get("Protein_g", {}).get("consumed", 0) * 4
    carbs_cal = summary.get("Carbs_g", {}).get("consumed", 0) * 4
    fat_cal = summary.get("Fat_g", {}).get("consumed", 0) * 9

    labels = ["Protein", "Carbs", "Fat"]
    values = [protein_cal, carbs_cal, fat_cal]
    colors = ["#3b82f6", "#10b981", "#f59e0b"]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker_colors=colors,
        textinfo="percent",
        textfont_size=14,
        hovertemplate="%{label}: %{value:.0f} kcal (%{percent})<extra></extra>",
    )])

    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
        margin=dict(t=20, b=20, l=20, r=20),
        height=300,
        paper_bgcolor="rgba(0,0,0,0)",
        annotations=[dict(
            text="Macros",
            x=0.5, y=0.5,
            font_size=16,
            showarrow=False,
            font_color=_TEXT_COLOR,
        )],
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ─── Nutrient Adequacy Heatmap ───
def render_nutrient_heatmap(heatmap_df: pd.DataFrame) -> None:
    """Render a heatmap of nutrient adequacy over time."""
    if heatmap_df.empty:
        st.info("No data for nutrient heatmap.")
        return

    # Prepare data: rows = dates, columns = nutrients
    dates = heatmap_df["Date"].tolist()
    nutrients = [c for c in heatmap_df.columns if c != "Date"]
    z_values = heatmap_df[nutrients].values

    # Rename columns to labels
    nutrient_labels = [get_nutrient_label(k) for k in nutrients]

    fig = go.Figure(data=go.Heatmap(
        z=z_values,
        x=nutrient_labels,
        y=dates,
        colorscale=[
            [0, "#fef2f2"],
            [0.5, "#fef3c7"],
            [0.8, "#d1fae5"],
            [1, "#059669"],
        ],
        zmin=0,
        zmax=120,
        hovertemplate="%{y}<br>%{x}: %{z:.0f}%<extra></extra>",
        colorbar=dict(title="% Target", thickness=15),
    ))

    fig.update_layout(
        title=dict(text="Nutrient Adequacy Heatmap (30 Days)", font=dict(size=16, color=_TEXT_COLOR)),
        margin=dict(t=60, b=80, l=80, r=20),
        height=max(350, len(dates) * 18),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(autorange="reversed"),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ─── Body Metric Trend ───
def render_body_metric_chart(
    trend_df: pd.DataFrame,
    metric_key: str,
    title: Optional[str] = None,
    show_ma: bool = True,
) -> None:
    """Render a line chart for a body metric trend."""
    if trend_df.empty or metric_key not in trend_df.columns:
        st.info(f"No data for {metric_key}.")
        return

    label = title or get_body_metric_label(metric_key)
    unit = get_body_metric_unit(metric_key)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=trend_df["Date"],
        y=trend_df[metric_key],
        mode="lines+markers",
        name=label,
        line=dict(color=_COLOR_PRIMARY, width=2.5),
        marker=dict(size=6, color=_COLOR_PRIMARY),
        hovertemplate=f"%{{x}}<br>{label}: %{{y:.1f}} {unit}<extra></extra>",
    ))

    # 7-day moving average
    if show_ma and len(trend_df) >= 7:
        ma = trend_df[metric_key].rolling(window=7, min_periods=1).mean()
        fig.add_trace(go.Scatter(
            x=trend_df["Date"],
            y=ma,
            mode="lines",
            name="7-Day Avg",
            line=dict(color=_COLOR_SECONDARY, width=2, dash="dot"),
            hovertemplate=f"%{{x}}<br>7-Day Avg: %{{y:.1f}} {unit}<extra></extra>",
        ))

    fig = _base_layout(fig, label, height=320)
    fig.update_layout(xaxis_title="Date", yaxis_title=unit)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ─── Body Composition Multi-Chart ───
def render_body_composition_dashboard(
    body_metrics_df: pd.DataFrame,
    end_date: datetime,
    days: int = 90,
) -> None:
    """Render a 2x2 grid of body composition charts."""
    if body_metrics_df is None or body_metrics_df.empty:
        st.info("No body composition data available.")
        return

    from services.body_metrics_service import get_body_metric_trend

    col1, col2 = st.columns(2)

    with col1:
        weight_df = get_body_metric_trend(body_metrics_df, "Weight_kg", end_date, days)
        render_body_metric_chart(weight_df, "Weight_kg", "Weight Trend")

    with col2:
        bf_df = get_body_metric_trend(body_metrics_df, "Body_Fat_pct", end_date, days)
        render_body_metric_chart(bf_df, "Body_Fat_pct", "Body Fat %")

    col3, col4 = st.columns(2)

    with col3:
        muscle_df = get_body_metric_trend(body_metrics_df, "Muscle_Mass_kg", end_date, days)
        render_body_metric_chart(muscle_df, "Muscle_Mass_kg", "Muscle Mass")

    with col4:
        waist_df = get_body_metric_trend(body_metrics_df, "Waist_cm", end_date, days)
        render_body_metric_chart(waist_df, "Waist_cm", "Waist Circumference")


# ─── Weekly Averages Cards ───
def render_trend_averages(averages: Dict[str, float], keys: List[str] = None) -> None:
    """Display trend average metrics in a clean row."""
    if keys is None:
        keys = ["Calories_kcal", "Protein_g", "Fiber_g", "Water_ml"]

    labels = {
        "Calories_kcal": ("Avg Calories", "kcal", 0),
        "Protein_g": ("Avg Protein", "g", 1),
        "Fiber_g": ("Avg Fiber", "g", 1),
        "Water_ml": ("Avg Water", "ml", 0),
        "Carbs_g": ("Avg Carbs", "g", 1),
        "Fat_g": ("Avg Fat", "g", 1),
        "Sugar_g": ("Avg Sugar", "g", 1),
    }

    display_keys = [k for k in keys if k in averages]
    if not display_keys:
        return

    cols = st.columns(len(display_keys))
    for idx, key in enumerate(display_keys):
        label, unit, precision = labels.get(key, (key, "", 1))
        val = averages.get(key, 0.0)
        fmt = f"{{:.{precision}f}}"
        with cols[idx]:
            st.markdown(f"""
                <div style="
                    background-color: #ffffff;
                    border: 1px solid #e5e7eb;
                    border-radius: 10px;
                    padding: 1rem;
                    text-align: center;
                    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
                ">
                    <div style="font-size: 0.8rem; color: #6b7280; font-weight: 500; margin-bottom: 0.25rem;">{label}</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: #111827;">{fmt.format(val)}</div>
                    <div style="font-size: 0.75rem; color: #9ca3af;">{unit}</div>
                </div>
            """, unsafe_allow_html=True)


# ─── Backward compatibility wrappers ───
def render_weekly_calories_chart(weekly_df: pd.DataFrame) -> None:
    """Backward-compatible wrapper."""
    render_calorie_trend_chart(weekly_df)


def render_weekly_protein_chart(weekly_df: pd.DataFrame) -> None:
    """Backward-compatible wrapper."""
    render_protein_trend_chart(weekly_df)


def render_weekly_fiber_chart(weekly_df: pd.DataFrame) -> None:
    """Backward-compatible wrapper."""
    render_fiber_trend_chart(weekly_df)


def render_weekly_averages(averages: Dict[str, float]) -> None:
    """Backward-compatible wrapper."""
    render_trend_averages(averages)