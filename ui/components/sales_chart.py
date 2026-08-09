"""Chart rendering for the product detail page (uses Plotly)."""
from __future__ import annotations


def render_sales_chart(snapshots: list[dict]) -> None:
    """Render the sales-signal trend chart from snapshot history."""
    import plotly.graph_objects as go
    import streamlit as st

    if not snapshots:
        st.info("No snapshot history yet. Data will appear after repeated searches.")
        return

    timestamps = [s.get("timestamp") for s in snapshots]
    signals = [s.get("sales_signal") for s in snapshots]
    prices = [s.get("price") for s in snapshots]

    fig = go.Figure()
    if any(v is not None for v in signals):
        fig.add_trace(go.Scatter(
            x=timestamps, y=signals, mode="lines+markers",
            name="Cumulative sales signal", line=dict(width=2)))
    if any(v is not None for v in prices):
        fig.add_trace(go.Scatter(
            x=timestamps, y=prices, mode="lines+markers",
            name="Price (Rs.)", yaxis="y2", line=dict(dash="dash")))

    fig.update_layout(
        height=320, margin=dict(l=20, r=20, t=30, b=20),
        yaxis=dict(title="Units sold"),
        yaxis2=dict(title="Price (Rs.)", overlaying="y", side="right"),
        legend=dict(orientation="h"),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)
