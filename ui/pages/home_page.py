"""Main search + results page."""
from __future__ import annotations

import streamlit as st

from utils import validators
from utils.logger import get_logger

log = get_logger("ui.home_page")


def render_home_page() -> None:
    """Top-level home page: search bar, metrics, results table, navigation."""
    from ui.components import search_bar, product_table, filters_panel
    from services import search_service

    st.title("🛒 Daraz Product Hunter")
    st.caption("Discover high-demand products. Sales & revenue figures are "
               "**estimates** based on available signals, not facts.")

    keyword = search_bar.render_search_bar()

    # Run the search when the user submits.
    if keyword:
        try:
            cleaned = validators.validate_keyword(keyword)
        except validators.ValidationError as exc:
            st.error(str(exc))
            cleaned = None
        if cleaned:
            with st.spinner(f"Analyzing '{cleaned}'…"):
                try:
                    results = search_service.execute_search(cleaned, use_cache=True)
                    st.session_state["results"] = results
                    st.session_state["last_keyword"] = cleaned
                except Exception as exc:  # noqa: BLE001
                    log.error("Search failed: %s", exc)
                    st.error("Search failed. Please try again later.")
                    st.session_state["results"] = []

    # If we have cached results in this session, show them.
    results = st.session_state.get("results", [])

    if results:
        render_summary_metrics(results)

        # Use cached results + live filters (no re-fetch, architecture Problem 9).
        filters = filters_panel.render_filters_panel()
        filtered = search_service.apply_filters(results, filters)
        sorted_results = search_service.sort_results(filtered, filters.get("sort_by", "demand"))

        st.subheader(f"Results for '{st.session_state.get('last_keyword')}'")
        product_table.render_product_table(sorted_results)

        # Navigation: clicking a product opens its detail page.
        _render_navigation(sorted_results)
    elif keyword:
        st.info("No results to display.")
    else:
        st.info("Enter a keyword above to begin hunting for products.")


def render_summary_metrics(results: list[dict]) -> None:
    """Display the summary metric boxes at the top."""
    total = len(results)
    high_demand = sum(1 for p in results if p.get("demand_class_key") == "high")
    avg_rating = _avg([p.get("rating") for p in results if p.get("rating") is not None])

    c1, c2, c3 = st.columns(3)
    c1.metric("Products found", total)
    c2.metric("🔥 High-demand", high_demand)
    c3.metric("Avg rating", f"{avg_rating:.2f}" if avg_rating else "—")


def _render_navigation(results: list[dict]) -> None:
    """Provide a selectbox/dropdown to open a product detail page."""
    if not results:
        return
    labels = {f"{p.get('name')} — {p.get('demand_emoji','')} {p.get('demand_label','')}": p.get("id")
              for p in results}
    if st.session_state.get("detail_triggered"):
        return
    choice = st.selectbox("🔎 Inspect a product", list(labels.keys()))
    if st.button("View product details", use_container_width=True):
        st.session_state["detail_product_id"] = labels.get(choice)
        st.session_state["detail_triggered"] = True
        st.rerun()


def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0
