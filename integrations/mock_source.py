"""Realistic fake Daraz data source for development.

Daraz does not expose a public API for research tools (architecture Problem 1),
so this module generates deterministic, realistic-looking raw data that looks
exactly like what a Daraz endpoint would return. ``daraz_client`` serves this
data when ``DARAZ_SOURCE_MODE=mock``. The raw shape here intentionally mimics
messy external data (strings like "Rs. 2,499", ``priceRaw``, ``ratingStar``)
so the normalizer is exercised for real.

Deterministic: the same keyword always produces the same products, so
snapshots across repeated searches form a meaningful time series.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import random

# Product name templates per category so search results feel real.
_CATALOG = [
    ("Wireless Earbuds Pro", "Electronics", ["Bluetooth 5.3", "Noise cancelling", "IPX5"]),
    ("Bluetooth Earbuds TWS", "Electronics", ["Touch control", "LED case"]),
    ("Airbuds X9", "Electronics", ["Gaming mode", "Low latency"]),
    ("Wireless Earbuds Sport", "Electronics", ["Ear hook", "Sweat proof"]),
    ("LED Desk Lamp", "Home & Living", ["Dimmable", "USB port"]),
    ("USB-C Fast Charger 65W", "Electronics", ["GaN", "Foldable plug"]),
    ("Smart Watch Series 5", "Electronics", ["AMOLED", "GPS"]),
    ("Mechanical Keyboard 87", "Computer & Accessories", ["RGB", "Hot-swap"]),
    ("Yoga Mat Premium", "Sports & Outdoors", ["Non-slip", "Eco"]),
    ("Water Bottle 1L", "Home & Living", ["Stainless steel", "Insulated"]),
    ("Running Shoes Light", "Fashion & Apparel", ["Breathable", "Cushioned"]),
    ("Stainless Steel Cookware Set", "Home & Living", ["5 piece", "Induction"]),
    ("Portable Bluetooth Speaker", "Electronics", ["Bass boost", "Waterproof"]),
    ("Digital Kitchen Scale", "Home & Living", ["0.1g accuracy", "LCD"]),
    ("Gaming Mouse RGB", "Computer & Accessories", ["16000 DPI", "Ergonomic"]),
    ("Wireless Mouse Silent", "Computer & Accessories", ["2.4G", "Quiet clicks"]),
]

_BRANDS = ["Anker", "Haylou", "Baseus", "Soundcore", "Samsung", "Xiaomi", "Lenovo",
           "Acer", "LocalPlus", "NiceTech", "Urban", "Cockpit", "Arrow", "Daxen"]
_LOCATIONS = ["Lahore", "Karachi", "Multan", "Islamabad", "Sialkot", "Gujranwala"]

# A per-keyword seed so results are deterministic.
_DAILY_JITTER = 0.04  # ±4% day-to-day variation to make time series meaningful


def _seed_for(keyword: str) -> int:
    return int(hashlib.sha256(keyword.lower().encode("utf-8")).hexdigest()[:8], 16)


def _matches(keyword: str, name: str) -> bool:
    return keyword.lower() in name.lower() or _overlap(keyword, name)


def _overlap(a: str, b: str) -> bool:
    wa = set(w for w in a.lower().split() if len(w) > 2)
    wb = set(w for w in b.lower().split() if len(w) > 2)
    return bool(wa & wb)


def search_products(keyword: str, page: int = 1, page_size: int = 20) -> dict:
    """Return a raw Daraz-style search response dict for the keyword."""
    rng = random.Random(_seed_for(keyword) + page * 1_000_003)
    today = dt.date.today()

    candidates = [c for c in _CATALOG if _matches(keyword, c[0])]
    if not candidates:
        # Fall back to generic matches so almost any keyword returns results.
        candidates = [c for c in _CATALOG if rng.random() < 0.35]

    # Vary the order per day so the "featured" product changes slightly.
    rng.shuffle(candidates)

    start = (page - 1) * page_size
    products = []
    for idx, (name, category, features) in enumerate(candidates[start:start + page_size]):
        item_id = f"daraz-{_seed_for(name):08d}"
        base = 300 + (rng.random() * 9000)
        price = int(base // 10) * 10 + 99
        # Deterministic-ish "sales" that grow slowly over time to give trends.
        day_index = (today - dt.date(2024, 1, 1)).days
        growth = 1 + day_index * 0.002 + (rng.random() - 0.5) * _DAILY_JITTER * 10
        sold = int(max(50, (500 + rng.random() * 4000) * growth))
        reviews = int(max(5, sold * (0.25 + rng.random() * 0.5)))
        rating = round(min(5.0, 3.6 + rng.random() * 1.4), 1)
        old_price = int(price * (1.15 + rng.random() * 0.35))

        products.append({
            "item_id": item_id,
            "name": f"{name} ({rng.choice(features)})",
            "priceRaw": f"Rs. {price:,}",
            "originalPriceRaw": f"Rs. {old_price:,}",
            "ratingStar": str(rating),
            "reviewCount": str(reviews),
            "itemSold": str(sold),
            "category": category,
            "brand": rng.choice(_BRANDS),
            # Mock mode has no real product images, so leave the thumbnail empty;
            # the UI falls back to a bundled placeholder. A real integration
            # would provide an actual image URL here.
            "thumbnail": "",
            "itemUrl": f"https://www.daraz.pk/products/{item_id}.html",
            "sellerName": rng.choice(_LOCATIONS) + " Store",
            "sellerRating": str(round(min(5.0, 3.8 + rng.random() * 1.1), 1)),
            "official": rng.random() < 0.15,
        })

    return {
        "success": True,
        "keyword": keyword,
        "page": page,
        "page_size": page_size,
        "total_products": len(candidates),
        "data": products,
    }


def get_product_sellers(item_id: str) -> list[dict]:
    """Return mock seller records for a product id."""
    rng = random.Random(_seed_for(item_id) + 77)
    n = 1 + rng.randint(0, 8)
    sellers = []
    base_price = 500 + rng.random() * 4000
    for _ in range(n):
        price = int(base_price * (0.85 + rng.random() * 0.4))
        sellers.append({
            "seller_id": f"seller-{rng.randint(1000, 99999)}",
            "seller_name": rng.choice(_LOCATIONS) + " Traders",
            "price": price,
            "rating": round(min(5.0, 3.7 + rng.random() * 1.2), 1),
            "location": rng.choice(_LOCATIONS),
            "official": rng.random() < 0.1,
        })
    return sellers
