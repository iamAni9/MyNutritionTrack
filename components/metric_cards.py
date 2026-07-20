"""Streamlit UI components for metric and nutrient cards.

Provides reusable card layouts for calories, macronutrients, micronutrients,
body composition metrics, and professional analytics with consistent styling.
"""

from typing import Dict, List, Any, Optional
import streamlit as st
import plotly.graph_objects as go

from config.nutrients import get_display_precision
from config.body_metrics import get_body_metric_label, get_body_metric_unit, get_body_metric_precision


def _html(raw: str) -> str:
    """Minify HTML string to prevent Streamlit from treating it as a code block."""
    return " ".join(raw.split())


def _status_badge(status_color: str, label: str) -> str:
    """Return an HTML badge string for a status label."""
    colors = {
        "good": "#10b981",
        "warning": "#f59e0b",
        "danger": "#ef4444",
        "neutral": "#6b7280",
        "improving": "#10b981",
        "worsening": "#ef4444",
        "stable": "#6b7280",
        "healthy": "#10b981",
        "attention": "#f59e0b",
    }
    bg = colors.get(status_color, "#6b7280")
    return _html(f"""
    <span style="background-color: {bg}20; color: {bg}; padding: 2px 10px;
    border-radius: 12px; font-size: 0.75rem; font-weight: 600;
    letter-spacing: 0.02em;">{label}</span>
    """)


def _card_container(content: str) -> str:
    """Wrap content in a styled card container."""
    return _html(f"""
    <div style="background-color: #ffffff; border: 1px solid #e5e7eb;
    border-radius: 12px; padding: 1.25rem; margin-bottom: 0.75rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);">{content}</div>
    """)


def render_score_card(title: str, score: float, max_score: float = 100.0, unit: str = "") -> None:
    """Render a professional score card with circular indicator."""
    pct = min(score / max_score * 100, 100)
    if pct >= 80:
        color = "#10b981"
        status = "Excellent"
    elif pct >= 60:
        color = "#3b82f6"
        status = "Good"
    elif pct >= 40:
        color = "#f59e0b"
        status = "Fair"
    else:
        color = "#ef4444"
        status = "Needs Work"

    fig = go.Figure(data=[go.Pie(
        values=[pct, 100 - pct],
        labels=["Score", ""],
        hole=0.75,
        marker_colors=[color, "#e5e7eb"],
        textinfo="none",
        hoverinfo="none",
        showlegend=False,
    )])

    fig.update_layout(
        margin=dict(t=10, b=0, l=0, r=0),
        height=140,
        annotations=[dict(
            text=f"<b>{score:.0f}</b>",
            x=0.5, y=0.55,
            font_size=22,
            showarrow=False,
            font_color="#111827",
        ), dict(
            text=status,
            x=0.5, y=0.35,
            font_size=11,
            showarrow=False,
            font_color=color,
        )],
        paper_bgcolor="rgba(0,0,0,0)",
    )

    st.markdown(_html(f"""
        <div style="background-color: #ffffff; border: 1px solid #e5e7eb;
        border-radius: 12px; padding: 1rem; text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
            <div style="font-size: 0.85rem; color: #6b7280; font-weight: 600; margin-bottom: 0.5rem;">{title}</div>
    """), unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)


def render_calorie_card(summary: Dict[str, Any]) -> None:
    """Render the prominent calorie summary card with donut chart."""
    cal = summary.get("Calories_kcal", {})
    if not cal:
        st.warning("No calorie data available.")
        return

    consumed = cal["consumed"]
    target = cal["target"]
    remaining = cal["remaining"]
    percentage = cal["percentage"]
    status = cal["status"]
    status_color = cal["status_color"]

    col1, col2 = st.columns([1, 1])

    with col1:
        html_content = _card_container(_html(f"""
            <div style="margin-bottom: 0.5rem;">
                <span style="font-size: 0.875rem; color: #6b7280; font-weight: 500;">Calories</span>
            </div>
            <div style="font-size: 2.5rem; font-weight: 700; color: #111827; line-height: 1.1;">
                {consumed:.0f}
                <span style="font-size: 1rem; color: #6b7280; font-weight: 500;"> / {target:.0f} kcal</span>
            </div>
            <div style="margin-top: 0.75rem; display: flex; gap: 1rem; align-items: center;">
                {_status_badge(status_color, status)}
                <span style="font-size: 0.875rem; color: #4b5563;">{remaining:.0f} kcal remaining</span>
            </div>
        """))
        st.markdown(html_content, unsafe_allow_html=True)

    with col2:
        fig = go.Figure(
            data=[
                go.Pie(
                    values=[min(consumed, target), max(target - consumed, 0)],
                    labels=["Consumed", "Remaining"],
                    hole=0.65,
                    marker_colors=["#3b82f6", "#e5e7eb"],
                    textinfo="none",
                    hoverinfo="label+value",
                    hovertemplate="%{label}: %{value:.0f} kcal<extra></extra>",
                )
            ]
        )
        fig.update_layout(
            showlegend=False,
            margin=dict(t=0, b=0, l=0, r=0),
            height=180,
            annotations=[
                dict(
                    text=f"{percentage:.0f}%",
                    x=0.5, y=0.5,
                    font_size=20,
                    showarrow=False,
                    font_color="#111827",
                    font_family="Arial, sans-serif",
                )
            ],
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_macro_card(key: str, summary: Dict[str, Any]) -> None:
    """Render a single macronutrient card with progress bar."""
    data = summary.get(key, {})
    if not data:
        return

    label = data.get("label", key)
    unit = data.get("unit", "g")
    consumed = data["consumed"]
    target = data["target"]
    remaining = data["remaining"]
    percentage = data["percentage"]
    status = data["status"]
    status_color = data["status_color"]
    precision = data.get("precision", 1)

    is_limit = "limit" in data.get("type", "target")
    remaining_label = "Remaining Limit" if is_limit else "Remaining Target"

    bar_color = {
        "good": "#10b981",
        "warning": "#f59e0b",
        "danger": "#ef4444",
        "neutral": "#6b7280",
    }.get(status_color, "#3b82f6")

    bar_pct = min(percentage, 100)
    fmt = f"{{:.{precision}f}}"
    consumed_str = fmt.format(consumed)
    target_str = fmt.format(target)
    remaining_str = fmt.format(remaining)

    html_content = _card_container(_html(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <span style="font-size: 1rem; font-weight: 600; color: #111827;">{label}</span>
            {_status_badge(status_color, status)}
        </div>
        <div style="font-size: 1.75rem; font-weight: 700; color: #111827; margin-bottom: 0.25rem;">
            {consumed_str}
            <span style="font-size: 0.875rem; color: #6b7280; font-weight: 500;"> / {target_str} {unit}</span>
        </div>
        <div style="width: 100%; height: 8px; background-color: #e5e7eb; border-radius: 4px; overflow: hidden; margin: 0.5rem 0;">
            <div style="width: {bar_pct:.1f}%; height: 100%; background-color: {bar_color}; border-radius: 4px;"></div>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: #6b7280;">
            <span>{percentage:.0f}%</span>
            <span>{remaining_label}: {remaining_str} {unit}</span>
        </div>
    """))
    st.markdown(html_content, unsafe_allow_html=True)


def render_macro_cards(summary: Dict[str, Any]) -> None:
    """Render all macronutrient cards in a grid."""
    from config.nutrients import MACRO_KEYS
    macro_keys = [k for k in MACRO_KEYS if k != "Calories_kcal"]
    cols = st.columns(min(len(macro_keys), 6))
    for idx, key in enumerate(macro_keys):
        with cols[idx % len(cols)]:
            render_macro_card(key, summary)


def render_micro_progress(key: str, summary: Dict[str, Any]) -> None:
    """Render a horizontal progress bar for a micronutrient."""
    data = summary.get(key, {})
    if not data:
        return

    label = data.get("label", key)
    unit = data.get("unit", "")
    consumed = data["consumed"]
    target = data["target"]
    remaining = data["remaining"]
    percentage = data["percentage"]
    status = data["status"]
    status_color = data["status_color"]
    precision = data.get("precision", 1)

    is_limit = "limit" in data.get("type", "target")
    remaining_label = "Remaining Limit" if is_limit else "Remaining"

    bar_color = {
        "good": "#10b981",
        "warning": "#f59e0b",
        "danger": "#ef4444",
        "neutral": "#6b7280",
    }.get(status_color, "#3b82f6")

    bar_pct = min(percentage, 100)
    fmt = f"{{:.{precision}f}}"

    html_content = _card_container(_html(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
            <span style="font-size: 0.95rem; font-weight: 600; color: #111827;">{label}</span>
            {_status_badge(status_color, status)}
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: #4b5563; margin-bottom: 0.35rem;">
            <span>{fmt.format(consumed)} {unit}</span>
            <span>{remaining_label}: {fmt.format(remaining)} {unit}</span>
        </div>
        <div style="width: 100%; height: 6px; background-color: #e5e7eb; border-radius: 3px; overflow: hidden;">
            <div style="width: {bar_pct:.1f}%; height: 100%; background-color: {bar_color}; border-radius: 3px;"></div>
        </div>
        <div style="text-align: right; font-size: 0.75rem; color: #9ca3af; margin-top: 0.25rem;">{percentage:.0f}%</div>
    """))
    st.markdown(html_content, unsafe_allow_html=True)


def render_micro_group(summary: Dict[str, Any], keys: List[str], title: str) -> None:
    """Render a group of micronutrient progress bars."""
    st.markdown(_html(f"""
        <div style="font-size: 1.1rem; font-weight: 700; color: #111827; margin: 1.5rem 0 0.75rem 0;">{title}</div>
    """), unsafe_allow_html=True)

    for key in keys:
        render_micro_progress(key, summary)


def render_body_metric_card(
    metric_key: str,
    value: Optional[float],
    change_data: Optional[Dict[str, Any]] = None,
) -> None:
    """Render a body metric card with value and trend indicator."""
    label = get_body_metric_label(metric_key)
    unit = get_body_metric_unit(metric_key)
    precision = get_body_metric_precision(metric_key)
    fmt = f"{{:.{precision}f}}"

    if value is None or (isinstance(value, float) and (value != value)):  # NaN check
        value_str = "—"
        trend_html = ""
    else:
        value_str = fmt.format(value)
        if change_data:
            change_abs = change_data["change_abs"]
            change_pct = change_data["change_pct"]
            trend = change_data["trend"]
            arrow = "↑" if change_abs > 0 else "↓" if change_abs < 0 else "→"
            color = {
                "improving": "#10b981",
                "worsening": "#ef4444",
                "stable": "#6b7280",
                "healthy": "#10b981",
                "attention": "#f59e0b",
            }.get(trend, "#6b7280")
            trend_html = _html(f"""
                <div style="font-size: 0.8rem; color: {color}; margin-top: 0.25rem; font-weight: 500;">
                    {arrow} {abs(change_abs):.{precision}f} {unit} ({abs(change_pct):.1f}%) · {trend.title()}
                </div>
            """)
        else:
            trend_html = ""

    st.markdown(_html(f"""
        <div style="background-color: #ffffff; border: 1px solid #e5e7eb;
        border-radius: 12px; padding: 1.25rem; text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04); margin-bottom: 0.75rem;">
            <div style="font-size: 0.8rem; color: #6b7280; font-weight: 500; margin-bottom: 0.25rem;">{label}</div>
            <div style="font-size: 2rem; font-weight: 700; color: #111827;">{value_str}</div>
            <div style="font-size: 0.75rem; color: #9ca3af;">{unit}</div>
            {trend_html}
        </div>
    """), unsafe_allow_html=True)