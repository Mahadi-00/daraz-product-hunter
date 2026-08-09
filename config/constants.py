"""Business-rule constants.

These values encode the *product logic* of the application: demand thresholds,
scoring weights and the classification labels/emojis. They are separated from
``settings.py`` because settings may change per environment while these define
the meaning of the output and only change when the product logic changes.
"""
from __future__ import annotations

# --------------------------------------------------------------------------
# Demand score thresholds (score is 0-100)
# --------------------------------------------------------------------------
DEMAND_THRESHOLD_HIGH = 80   # score >= 80 -> High Demand
DEMAND_THRESHOLD_GOOD = 60   # 60 <= score < 80 -> Good
DEMAND_THRESHOLD_AVERAGE = 40  # 40 <= score < 60 -> Average
# score < 40 -> Low Demand

# --------------------------------------------------------------------------
# Scoring weights (must sum to 100)
# --------------------------------------------------------------------------
WEIGHT_SALES_VELOCITY = 0.40
WEIGHT_REVIEW_COUNT = 0.20
WEIGHT_RATING = 0.10
WEIGHT_COMPETITION = 0.20
WEIGHT_PRICE = 0.10

# --------------------------------------------------------------------------
# Demand classification labels and emoji
# --------------------------------------------------------------------------
DEMAND_LABELS = {
    "high": {"label": "High Demand", "emoji": "🔥", "min": DEMAND_THRESHOLD_HIGH, "max": 100},
    "good": {"label": "Good", "emoji": "🟢", "min": DEMAND_THRESHOLD_GOOD, "max": DEMAND_THRESHOLD_HIGH},
    "average": {"label": "Average", "emoji": "🟡", "min": DEMAND_THRESHOLD_AVERAGE, "max": DEMAND_THRESHOLD_GOOD},
    "low": {"label": "Low Demand", "emoji": "🔴", "min": 0, "max": DEMAND_THRESHOLD_AVERAGE},
}

# Canonical order used for filtering dropdowns.
DEMAND_ORDER = ["high", "good", "average", "low"]

# --------------------------------------------------------------------------
# Normalization scale ceilings (used to map raw metrics to a 0-100 score)
# --------------------------------------------------------------------------
MAX_REVIEWS_FOR_FULL_SCORE = 10_000   # >= this many reviews -> review score of 100
MIN_RATING_FOR_FULL_SCORE = 4.9       # >= this rating -> rating score of 100
MAX_COMPETITION_FOR_FULL_SCORE = 20   # >= this many sellers -> full competition score

# --------------------------------------------------------------------------
# Confidence levels for estimates
# --------------------------------------------------------------------------
CONFIDENCE_LEVELS = ("high", "medium", "low")

MIN_SNAPSHOTS_HIGH_CONFIDENCE = 7    # at least a week of daily snapshots
MIN_SNAPSHOTS_MEDIUM_CONFIDENCE = 3

# A sales estimate derived from fewer than this many days is flagged as weak.
MIN_DAYS_FOR_RELIABLE_ESTIMATE = 7

# --------------------------------------------------------------------------
# Sales / revenue estimation
# --------------------------------------------------------------------------
ESTIMATE_PERIODS = (7, 30)   # days for the 7D and 30D windows

# --------------------------------------------------------------------------
# Trend categories
# --------------------------------------------------------------------------
TREND_FLAT_TOLERANCE_PERCENT = 2.0   # changes within +/-2% are "flat"
