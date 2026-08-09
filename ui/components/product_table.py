"""Renders the products results table."""
from __future__ import annotations

import pandas as pd

from utils import formatters


def to_dataframe(products: list[dict]) -> pd.DataFrame:
    """Convert enriched product dicts into a display-ready DataFrame."""
    rows = []
    for p in products:
        rows.append({
            "Product": p.get("name"),
            "Price": formatters.format_price(p.get("current_price")),
            "Rating": formatters.format_rating(p.get("rating")),
            "Reviews": formatters.format_number(p.get("review_count")),
            "Demand": f"{p.get('demand_emoji','')} {p.get('demand_label','')}",
            "Est. Sales (7D)": formatters.format_estimated_sales(p.get("estimate_7d_sales")),
            "Est. Revenue (7D)": formatters.format_price(p.get("revenue_7d")),
            "Sellers": p.get("seller_count") or 0,
            "Trend": _trend_symbol(p.get("trend_direction")),
            "_id": p.get("id"),
        })
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df = df.set_index("Product")
    df.drop(columns=["_id"], inplace=True)
    return df


def render_product_table(products: list[dict]) -> None:
    """Render the results table plus per-row estimate/confidence footnotes."""
    import streamlit as st
    if not products:
        st.info("No products found. Try a different keyword or relax your filters.")
        return

    df = to_dataframe(products)
    st.dataframe(df, use_container_width=True, height=min(60 + 35 * len(df), 600))

    # Honesty footnote explaining estimates.
    n_low = sum(1 for p in products if p.get("confidence") == "low")
    note = "Sales figures are *estimates* based on available signals. "
    note += f"{n_low} product(s) currently lack enough history for confident estimates."
    st.markdown(f"<div class='estimate-note'>{note}</div>", unsafe_allow_html=True)


def _trend_symbol(direction: str | None) -> str:
    return {
        "up": "▲",
        "down": "▼",
        "flat": "―",
    }.get(direction or "flat", "―")
