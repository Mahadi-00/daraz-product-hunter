"""Sidebar filters component."""
from __future__ import annotations

from config import constants


def render_filters_panel(default_filters: dict | None = None) -> dict:
    """Render sidebar filters and return the selected filter dict."""
    import streamlit as st

    default_filters = default_filters or {}
    st.sidebar.header("⚙️ Filters")

    min_rating = st.sidebar.slider(
        "Minimum rating", 0.0, 5.0, float(default_filters.get("min_rating", 0.0)), 0.1)
    max_price = st.sidebar.number_input(
        "Maximum price (Rs.)", min_value=0, value=int(default_filters.get("max_price", 50000)),
        step=500)

    demand_options = [
        (constants.DEMAND_LABELS[k]["label"], k) for k in constants.DEMAND_ORDER
    ]
    selected_labels = st.sidebar.multiselect(
        "Demand classification",
        options=[lbl for lbl, _ in demand_options],
        default=[lbl for lbl, _ in demand_options],
    )
    selected_keys = [k for lbl, k in demand_options if lbl in selected_labels]

    sort_by = st.sidebar.selectbox(
        "Sort by",
        options=["demand", "price", "reviews", "sales"],
        index=0,
    )

    return {
        "min_rating": min_rating or None,
        "max_price": max_price if max_price > 0 else None,
        "demand": selected_keys,
        "sort_by": sort_by,
    }
