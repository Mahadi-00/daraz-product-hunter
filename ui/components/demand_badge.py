"""Renders the demand indicator badge (🔥/🟢/🟡/🔴) for a product row."""
from __future__ import annotations


def render_demand_badge(demand_key: str, label: str | None = None,
                        emoji: str | None = None, partial: bool = False) -> None:
    """Render a colored demand badge via st.markdown.

    ``partial`` indicates the score was computed without sales history, so a
    small "provisional" marker is appended.
    """
    import streamlit as st

    cls = {
        "high": "demand-high",
        "good": "demand-good",
        "average": "demand-average",
        "low": "demand-low",
    }.get(demand_key, "demand-low")

    text = f"{emoji or ''} {label or demand_key.title()}"
    suffix = " (provisional)" if partial else ""
    st.markdown(
        f"<span class='demand-badge {cls}'>{text}</span>{suffix}",
        unsafe_allow_html=True,
    )
