"""Product drill-down page."""
from __future__ import annotations

import streamlit as st

from services import analytics_service, product_service, snapshot_service
from ui.components import product_card, sales_chart, seller_table
from utils import formatters
from utils.logger import get_logger

log = get_logger("ui.product_detail")


def render_product_detail_page(product_id: int) -> None:
    """Render the full detail view for a product."""
    product = product_service.get_product(product_id)
    if product is None:
        st.error("Product not found.")
        if st.button("← Back to results"):
            _back()
        return

    full = analytics_service.get_full_product_analytics(product)

    product_card.render_product_card(
        product, full["demand"], full["trend"], full["competition"])

    st.markdown("---")
    st.subheader("📈 Sales trend")
    sales_chart.render_sales_chart(
        [s for s in _history(product_id) if s.get("timestamp")])

    st.markdown("### 💰 Estimated sales")
    _render_estimates(full)

    st.markdown("### 🏪 Sellers")
    seller_table.render_seller_table(full["sellers"])

    if st.button("← Back to results"):
        _back()


def _render_estimates(full: dict) -> None:
    for period, label in (("7d", "7 days"), ("30d", "30 days")):
        est = full["estimates"][period]
        rev = full["revenue"][period]
        c = st.columns(2)
        c[0].metric(
            f"Est. sales ({label})",
            formatters.format_estimated_sales(est["estimated_sales"]))
        c[1].metric(
            f"Est. revenue ({label})",
            formatters.format_price(rev["estimated_revenue"]))
        conf = est["confidence"]
        extra = " — extrapolated from limited data" if est.get("is_extrapolated") else ""
        st.caption(f"Confidence: {conf.upper()}{extra} · "
                   f"{est.get('snapshot_count',0)} snapshots covering ~{est.get('days_covered',0)} days")
    st.markdown(
        "<div class='estimate-note'>All sales and revenue figures are estimates "
        "based on available signals, not verified facts.</div>",
        unsafe_allow_html=True)


def _history(product_id: int):
    return snapshot_service.get_history(product_id, 120)


def _back() -> None:
    st.session_state["detail_product_id"] = None
    st.session_state["detail_triggered"] = False
    st.rerun()
