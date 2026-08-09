"""Input validation helpers.

Validation happens *before* any expensive or external work is triggered so we
fail fast with a friendly message instead of making pointless requests.
"""
from __future__ import annotations

import re

# Maximum length of a search keyword before we reject it.
MAX_KEYWORD_LENGTH = 100
# A keyword made only of these characters is considered meaningless.
ONLY_SPECIAL_RE = re.compile(r"^[^a-zA-Z0-9\u0600-\u06FF]+$")  # allows latin + arabic/urdu


class ValidationError(ValueError):
    """Raised when user-supplied input fails validation."""


def validate_keyword(keyword: str | None) -> str:
    """Validate and clean a search keyword.

    Raises :class:`ValidationError` with a user-facing message when invalid.
    Returns the cleaned keyword string on success.
    """
    if not keyword:
        raise ValidationError("Please enter a search term.")

    cleaned = str(keyword).strip()

    if len(cleaned) > MAX_KEYWORD_LENGTH:
        raise ValidationError(
            f"Search term is too long (max {MAX_KEYWORD_LENGTH} characters)."
        )

    if ONLY_SPECIAL_RE.match(cleaned):
        raise ValidationError("Search term cannot contain only special characters.")

    if not re.search(r"[a-zA-Z0-9\u0600-\u06FF]", cleaned):
        raise ValidationError("Search term must contain at least one letter or digit.")

    return cleaned


def validate_price_range(min_price, max_price) -> tuple[float | None, float | None]:
    """Validate an optional price range.

    Returns ``(min_price, max_price)`` with empty values coerced to None.
    Raises :class:`ValidationError` if min > max.
    """
    lo = _to_float_or_none(min_price)
    hi = _to_float_or_none(max_price)
    if lo is not None and hi is not None and lo > hi:
        raise ValidationError("Minimum price cannot be greater than maximum price.")
    return lo, hi


def validate_rating(rating) -> float | None:
    """Validate an optional minimum-rating filter (must be 0-5)."""
    r = _to_float_or_none(rating)
    if r is not None and not (0.0 <= r <= 5.0):
        raise ValidationError("Minimum rating must be between 0 and 5.")
    return r


def _to_float_or_none(value) -> float | None:
    if value in (None, "", "None"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
