# 🛒 Daraz Product Hunter

A Streamlit-based product research tool that searches the Daraz catalog, stores
history in SQLite, and produces **honest estimates** of sales, revenue,
competition and demand — always labeled as estimates, never presented as fact.

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env        # defaults are fine for local dev (mock data)
streamlit run app.py
```

The app starts in **mock mode** (`DARAZ_SOURCE_MODE=mock`), which serves
deterministic, realistic fake data so you can explore the whole pipeline with
no network and no risk. To wire a real data source later, implement the
requests inside `integrations/daraz_client.py` and set `DARAZ_SOURCE_MODE=http`.

## Project layout

```
daraz_product_hunter/
├── app.py                 # Streamlit entry point
├── config/                # settings (env) + constants (business rules)
├── database/              # the ONLY place that touches SQL
├── integrations/          # the ONLY place that touches external data
├── analytics/             # pure calculation, no I/O
├── services/              # the ONLY place that orchestrates modules
├── ui/                    # the ONLY place that touches Streamlit
├── utils/                 # tiny shared helpers
├── tests/                 # pytest unit tests
├── data/                  # SQLite database (auto-created)
└── requirements.txt
```

## Key design ideas

- **Layered architecture** — each layer only knows its immediate neighbor.
- **Repository pattern** — all SQL lives in `database/*_repository.py`, so
  switching from SQLite to PostgreSQL only touches those files.
- **Normalizer boundary** — raw Daraz JSON never reaches business logic; if the
  source changes field names, only `integrations/data_normalizer.py` changes.
- **Honest estimation** — sales/revenue are always estimates with a confidence
  level (high/medium/low). No data → "Not enough data yet", never a fake number.
- **Graceful degradation** — one bad product never kills a whole search.

## How estimation works

Snapshots record a product's price/rating/reviews/cumulative-sold signal each
time it is searched. `sales_estimator` takes the *difference* in the sold
signal between an early and a recent snapshot to measure units sold in that
window, extrapolating to 7/30 days when needed and flagging the extrapolation.
Confidence is derived from snapshot count and time coverage. See
`integrations/data_normalizer.py` for the documented meaning of the sales signal.

## Tests

```bash
python -m pytest -q
```

Covers unit logic (normalizer, sales estimator, demand scorer, competition,
revenue, trend) plus end-to-end service flows **and** a Streamlit UI smoke test
(`tests/test_ui_pages.py`) that actually renders both the home page and the
product detail page so page-level runtime errors are caught automatically.

## Notes / caveats

- Daraz has no public research API. The default mock source is safe for
  development; building a scraped/unofficial integration is at your own risk
  and should be isolated behind `integrations/daraz_client.py`.
- First-run has no history, so estimates show "Not enough data yet" until
  snapshots accumulate over a few days.
# daraz-product-hunter
# daraz-product-hunter
# Daraz-product-hunter
