"""Plotly chart components for the nutrition dashboard.

Generates interactive, responsive charts for weekly trends and
nutrient comparisons.
"""

from typing import Dict, List
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from config.nutrients import get_nutrient_label


def render_weekly_calories_chart(weekly_df: pd.DataFrame) -> None:
    """Render a line chart of daily calories vs target over the week.

    Args:
        weekly_df: Weekly summary DataFrame from nutrition_service.
    """
    if weekly_df.empty or "Calories_kcal" not in weekly_df.columns:
        st.info("No weekly calorie data available.")
        return

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=weekly_df["Display"],
            y=weekly_df["Calories_kcal"],
            mode="lines+markers",
            name="Calories",
            line=dict(color="#3b82f6", width=3),
            marker=dict(size=8, color="#3b82f6"),
            hovertemplate="%{x}<br>Calories: %{y:.0f} kcal<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=weekly_df["Display"],
            y=weekly_df["Calories_kcal_target"],
            mode="lines",
            name="Target",
            line=dict(color="#10b981", width=2, dash="dash"),
            hovertemplate="%{x}<br>Target: %{y:.0f} kcal<extra></extra>",
        )
    )

    fig.update_layout(
        title=dict(text="Daily Calories vs Target", font=dict(size=16, color="#111827")),
        xaxis_title="Day",
        yaxis_title="kcal",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=60, b=40, l=50, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#f9fafb",
        height=350,
    )
    fig.update_xaxes(showgrid=False, gridcolor="#e5e7eb")
    fig.update_yaxes(showgrid=True, gridcolor="#e5e7eb", zeroline=False)

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_weekly_protein_chart(weekly_df: pd.DataFrame) -> None:
    """Render a bar chart of daily protein vs target.

    Args:
        weekly_df: Weekly summary DataFrame.
    """
    if weekly_df.empty or "Protein_g" not in weekly_df.columns:
        st.info("No weekly protein data available.")
        return

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=weekly_df["Display"],
            y=weekly_df["Protein_g"],
            name="Protein",
            marker_color="#3b82f6",
            hovertemplate="%{x}<br>Protein: %{y:.1f} g<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=weekly_df["Display"],
            y=weekly_df["Protein_g_target"],
            mode="lines",
            name="Target",
            line=dict(color="#10b981", width=2, dash="dash"),
            hovertemplate="%{x}<br>Target: %{y:.1f} g<extra></extra>",
        )
    )

    fig.update_layout(
        title=dict(text="Daily Protein vs Target", font=dict(size=16, color="#111827")),
        xaxis_title="Day",
        yaxis_title="g",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=60, b=40, l=50, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#f9fafb",
        barmode="group",
        height=350,
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#e5e7eb", zeroline=False)

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_weekly_fiber_chart(weekly_df: pd.DataFrame) -> None:
    """Render a line chart for daily fiber trend.

    Args:
        weekly_df: Weekly summary DataFrame.
    """
    if weekly_df.empty or "Fiber_g" not in weekly_df.columns:
        st.info("No weekly fiber data available.")
        return

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=weekly_df["Display"],
            y=weekly_df["Fiber_g"],
            mode="lines+markers+text",
            name="Fiber",
            line=dict(color="#8b5cf6", width=3),
            marker=dict(size=8, color="#8b5cf6"),
            text=weekly_df["Fiber_g"].apply(lambda x: f"{x:.0f}"),
            textposition="top center",
            textfont=dict(size=10, color="#6b7280"),
            hovertemplate="%{x}<br>Fiber: %{y:.1f} g<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=weekly_df["Display"],
            y=weekly_df["Fiber_g_target"],
            mode="lines",
            name="Target",
            line=dict(color="#10b981", width=2, dash="dash"),
            hovertemplate="%{x}<br>Target: %{y:.1f} g<extra></extra>",
        )
    )

    fig.update_layout(
        title=dict(text="Daily Fiber Trend", font=dict(size=16, color="#111827")),
        xaxis_title="Day",
        yaxis_title="g",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=60, b=40, l=50, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#f9fafb",
        height=350,
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#e5e7eb", zeroline=False)

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_weekly_averages(averages: Dict[str, float]) -> None:
    """Display weekly average metrics in a clean row.

    Args:
        averages: Dict from get_weekly_averages.
    """
    labels = {
        "Calories_kcal": ("Avg Calories", "kcal", 0),
        "Protein_g": ("Avg Protein", "g", 1),
        "Fiber_g": ("Avg Fiber", "g", 1),
        "Water_ml": ("Avg Water", "ml", 0),
    }

    cols = st.columns(len(labels))
    for idx, (key, (label, unit, precision)) in enumerate(labels.items()):
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
