"""Seller comparison table component."""
from __future__ import annotations

import pandas as pd

from utils import formatters


def render_seller_table(sellers: list[dict]) -> None:
    """Render a table comparing the sellers of a product."""
    import streamlit as st

    if not sellers:
        st.info("No seller data available for this product.")
        return

    rows = [{
        "Seller": s.get("seller_name"),
        "Price": formatters.format_price(s.get("price")),
        "Rating": formatters.format_rating(s.get("rating")),
        "Location": s.get("location") or "—",
        "Official": "✅" if s.get("is_official") else "—",
    } for s in sellers]
    df = pd.DataFrame(rows)
    df = df.set_index("Seller")
    st.dataframe(df, use_container_width=True)
