"""Tests for integrations/data_normalizer.py."""
from __future__ import annotations

from integrations.data_normalizer import (normalize_product, normalize_search_results,
                                          extract_sales_signal, normalize_seller)


def test_normalize_product_converts_price_string():
    raw = {
        "item_id": "abc123",
        "name": "Earbuds X",
        "priceRaw": "Rs. 2,499",
        "ratingStar": "4.7",
        "reviewCount": "2341",
        "itemSold": "1000",
    }
    norm = normalize_product(raw)
    assert norm["daraz_product_id"] == "abc123"
    assert norm["current_price"] == 2499
    assert norm["rating"] == 4.7
    assert norm["review_count"] == 2341
    assert norm["sales_signal"] == 1000


def test_normalize_product_safe_defaults_for_missing_fields():
    norm = normalize_product({"item_id": "x", "name": "P"})
    assert norm["current_price"] is None
    assert norm["rating"] is None
    assert norm["review_count"] == 0
    assert norm["sales_signal"] is None


def test_normalize_search_results_extracts_list():
    resp = {"success": True, "data": [
        {"item_id": "1", "name": "A", "priceRaw": "Rs. 100"},
        {"item_id": "2", "name": "B", "priceRaw": "Rs. 200"},
    ]}
    results = normalize_search_results(resp)
    assert len(results) == 2
    assert results[1]["current_price"] == 200


def test_normalize_search_results_handles_bad_data():
    assert normalize_search_results({"data": "not a list"}) == []
    assert normalize_search_results({}) == []


def test_extract_sales_signal_returns_none_when_missing():
    assert extract_sales_signal({"name": "x"}) is None
    assert extract_sales_signal({"itemSold": "42"}) == 42


def test_normalize_seller():
    seller = normalize_seller(
        {"seller_id": "s1", "sellerName": "Karachi Store", "price": 1500,
         "rating": "4.5", "location": "Karachi", "official": True},
        "pid")
    assert seller["daraz_seller_id"] == "s1"
    assert seller["price"] == 1500
    assert seller["is_official"] is True
    assert seller["product_daraz_id"] == "pid"
