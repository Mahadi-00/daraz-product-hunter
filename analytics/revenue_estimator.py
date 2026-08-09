"""Calculates estimated revenue from estimated sales and average price.

Always multiplies an *estimate* by a price, so the output is itself labeled
Estimated. If the sales estimate is None (not enough data), revenue is None
too -- we never fabricate a number.
"""
from __future__ import annotations


def estimate_revenue(estimated_sales: int | None, average_price: float | None) -> dict:
    """Multiply estimated sales by average price.

    Returns a dict with ``estimated_revenue`` (or None), the inputs used, and
    the Estimated label. The average price passed in should be the average
    price *across the snapshots used for the estimate*, not today's price
    (see architecture Problem 6).
    """
    if estimated_sales is None or average_price is None:
        return {
            "estimated_revenue": None,
            "estimated_sales": estimated_sales,
            "average_price": average_price,
            "is_estimated": True,
        }
    return {
        "estimated_revenue": int(round(estimated_sales * average_price)),
        "estimated_sales": estimated_sales,
        "average_price": average_price,
        "is_estimated": True,
    }


def calculate_average_price(sellers: list[dict]) -> float | None:
    """Average price across a list of seller records.

    More representative of "what people actually pay" than a single listed
    price. Returns None if there are no usable prices.
    """
    prices = [s.get("price") for s in sellers if s.get("price") is not None]
    if not prices:
        return None
    return sum(prices) / len(prices)
