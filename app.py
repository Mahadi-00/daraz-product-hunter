"""Daraz Product Hunter — Streamlit entry point.

Run with:  streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

# --- Page config must come before any other st call -----------------------
st.set_page_config(
    page_title="Daraz Product Hunter",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

from ui.styles.custom_css import inject_css  # noqa: E402
from ui.pages import home_page, product_detail_page  # noqa: E402

inject_css()

# --- State seeding ---------------------------------------------------------
st.session_state.setdefault("results", [])
st.session_state.setdefault("last_keyword", None)
st.session_state.setdefault("detail_product_id", None)
st.session_state.setdefault("detail_triggered", False)


def main() -> None:
    detail_id = st.session_state.get("detail_product_id")
    if detail_id is not None:
        product_detail_page.render_product_detail_page(detail_id)
    else:
        home_page.render_home_page()


if __name__ == "__main__":
    main()
