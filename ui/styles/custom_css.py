"""Streamlit CSS overrides for a consistent dashboard look."""
from __future__ import annotations

CUSTOM_CSS = """
<style>
/* Metric cards */
[data-testid="stMetric"] {
    background: #f7f9fc;
    border: 1px solid #e3e8ef;
    border-radius: 10px;
    padding: 12px 16px;
}
/* Demand badge coloring */
.demand-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 999px;
    font-weight: 600;
    font-size: 0.85rem;
    color: #fff;
}
.demand-high { background: #e11d48; }
.demand-good { background: #16a34a; }
.demand-average { background: #d97706; }
.demand-low { background: #dc2626; }

/* Estimate note */
.estimate-note {
    color: #6b7280;
    font-size: 0.8rem;
    font-style: italic;
}
.trend-up { color: #16a34a; font-weight: 600; }
.trend-down { color: #dc2626; font-weight: 600; }
.trend-flat { color: #6b7280; font-weight: 600; }
</style>
"""


def inject_css() -> None:
    """Call from app.py to inject the global stylesheet."""
    import streamlit as st
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
