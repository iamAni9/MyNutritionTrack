"""Streamlit table components for meal breakdowns and food logs.

Provides styled data tables for food items grouped by meal.
"""

from typing import Dict
import pandas as pd
import streamlit as st

from config.nutrients import MEAL_ORDER


def render_meal_tables(meals: Dict[str, pd.DataFrame]) -> None:
    """Render expandable meal sections with food-item tables.

    Args:
        meals: Dict mapping meal name -> DataFrame of food items.
    """
    if not meals:
        st.info("No food entries found for the selected date.")
        return

    # Sort meals according to MEAL_ORDER
    ordered_meals = []
    for meal in MEAL_ORDER:
        if meal in meals:
            ordered_meals.append(meal)
    for meal in meals:
        if meal not in ordered_meals:
            ordered_meals.append(meal)

    for meal in ordered_meals:
        df = meals[meal]

        # Calculate meal totals
        totals = {}
        for col in ["Calories_kcal", "Protein_g", "Carbs_g", "Fat_g", "Fiber_g", "Sugar_g", "Added_Sugar_g"]:
            if col in df.columns:
                val = df[col].sum()
                totals[col] = val if not pd.isna(val) else 0.0
            else:
                totals[col] = 0.0

        with st.expander(f"**{meal}** — {totals.get('Calories_kcal', 0):.0f} kcal"):
            # Meal summary row
            st.markdown(f"""<div style="display: flex; gap: 1.5rem; margin-bottom: 0.75rem; padding: 0.5rem 0; border-bottom: 1px solid #e5e7eb;">
                <div><span style="color: #6b7280; font-size: 0.8rem;">Protein</span><br><strong>{totals.get("Protein_g", 0):.1f} g</strong></div>
                <div><span style="color: #6b7280; font-size: 0.8rem;">Carbs</span><br><strong>{totals.get("Carbs_g", 0):.1f} g</strong></div>
                <div><span style="color: #6b7280; font-size: 0.8rem;">Fat</span><br><strong>{totals.get("Fat_g", 0):.1f} g</strong></div>
                <div><span style="color: #6b7280; font-size: 0.8rem;">Fiber</span><br><strong>{totals.get("Fiber_g", 0):.1f} g</strong></div>
                <div><span style="color: #6b7280; font-size: 0.8rem;">Sugar</span><br><strong>{totals.get("Sugar_g", 0):.1f} g</strong></div>
                <div><span style="color: #6b7280; font-size: 0.8rem;">Added Sugar</span><br><strong>{totals.get("Added_Sugar_g", 0):.1f} g</strong></div>
            </div>""", unsafe_allow_html=True)

            # Prepare display columns
            display_cols = ["Food", "Quantity_g", "Calories_kcal", "Protein_g", "Carbs_g", "Fat_g", "Fiber_g", "Sugar_g", "Added_Sugar_g"]
            available_cols = [c for c in display_cols if c in df.columns]

            if not available_cols:
                st.write("No detailed data available.")
                continue

            display_df = df[available_cols].copy()

            rename_map = {
                "Food": "Food",
                "Quantity_g": "Qty (g)",
                "Calories_kcal": "Calories",
                "Protein_g": "Protein (g)",
                "Carbs_g": "Carbs (g)",
                "Fat_g": "Fat (g)",
                "Fiber_g": "Fiber (g)",
                "Sugar_g": "Sugar (g)",
                "Added_Sugar_g": "Added Sugar (g)",
            }
            display_df.rename(columns={k: rename_map.get(k, k) for k in available_cols}, inplace=True)

            for col in display_df.columns:
                if col != "Food":
                    display_df[col] = display_df[col].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "0.0")

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={"Food": st.column_config.TextColumn("Food", width="large")},
            )