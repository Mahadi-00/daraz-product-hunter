"""Search bar component."""
from __future__ import annotations


def render_search_bar() -> str | None:
    """Render the keyword search bar; returns the submitted keyword or None."""
    import streamlit as st

    with st.form("search_form", clear_on_submit=False):
        col1, col2 = st.columns([4, 1])
        keyword = col1.text_input("Search Daraz products", key="search_keyword",
                                  placeholder="e.g. wireless earbuds, led lamp, smart watch")
        submitted = col2.form_submit_button("🔍 Search", use_container_width=True)

    if submitted:
        return keyword.strip()
    return None
