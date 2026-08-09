"""Single product detail card (used on the detail page header)."""
from __future__ import annotations

from pathlib import Path

from ui.components.demand_badge import render_demand_badge
from utils import formatters

# Local fallback image shown when a product has no usable/loadable thumbnail.
_PLACEHOLDER = Path(__file__).resolve().parent.parent / "assets" / "placeholder.png"


def render_product_card(product: dict, demand: dict, trend: dict,
                        competition: dict) -> None:
    """Render the header card for a product detail page."""
    import streamlit as st

    st.markdown(f"## {product.get('name')}")

    cols = st.columns([1, 2, 2, 2])
    with cols[0]:
        _render_thumbnail(st, product)

    cols[1].metric("Price", formatters.format_price(product.get("current_price")))
    cols[2].metric("Rating", formatters.format_rating(product.get("rating")))
    cols[3].metric("Reviews", formatters.format_number(product.get("review_count")))

    st.markdown("---")
    c = st.columns(4)
    with c[0]:
        st.markdown("**Demand**")
        render_demand_badge(demand["classification"]["key"],
                            demand["classification"]["label"],
                            demand["classification"]["emoji"],
                            partial=(demand.get("confidence") == "partial"))
        st.caption(f"Score: {demand.get('score', 0):.0f}/100")
    with c[1]:
        st.metric("Competition", f"{competition['competition_score']:.0f}/100")
    with c[2]:
        st.metric("Sellers", competition.get("seller_count", 0))
    with c[3]:
        st.markdown(f"**Trend** {_trend_arrow(trend.get('direction'))}")
        st.caption(formatters.format_percent(trend.get("percent_change")))


def _render_thumbnail(st, product: dict) -> None:
    """Render a product thumbnail, falling back to a local placeholder.

    Only renders a remote image if the URL is present and looks valid; any
    empty/invalid/missing thumbnail falls back to the bundled placeholder so
    we never render a broken-image icon.
    """
    url = product.get("thumbnail_url")
    if isinstance(url, str) and url.startswith(("http://", "https://")):
        try:
            st.image(url, width=120)
            return
        except Exception:  # noqa: BLE001 - unreachable/missing URL
            pass
    # Fallback: local placeholder (works offline and in sandboxed previews).
    if _PLACEHOLDER.exists():
        st.image(str(_PLACEHOLDER), width=120)
    else:
        st.markdown("**🛒**")


def _trend_arrow(direction: str) -> str:
    return {"up": "🔼", "down": "🔽", "flat": "➖"}.get(direction or "flat", "➖")
