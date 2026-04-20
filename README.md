# fred-public-data

This repository mirrors FRED (Federal Reserve Economic Data) time-series locally via the
FRED REST API and regenerates a chart corpus for exploratory economic research.

## Data Source

- **API documentation:** https://fred.stlouisfed.org/docs/api/fred/
- **API key registration:** https://fred.stlouisfed.org/docs/api/api_key.html
- **Series browser:** https://fred.stlouisfed.org/

All data is sourced from the Federal Reserve Bank of St. Louis and is free for public use
with attribution per the [FRED Terms of Use](https://fred.stlouisfed.org/legal/).

## Overview

- `config/series_catalog.toml` is the canonical list of FRED series IDs to track. Edit it
  to add or remove series — no code changes needed.
- `refresh.py` is the operator entrypoint. It reads the catalog, fetches observations from
  the FRED API, writes CSVs into `data/`, regenerates charts into `viz/`, and reports the
  newest observation date per series.
- `data/` holds downloaded CSVs organized by category (e.g. `data/labor_market/UNRATE.csv`).
- `viz/` contains PNG charts organized by category.
- `tests/test_refresh.py` is the regression surface for catalog loading and observation parsing.
- See `docs/ARCHITECTURE.md` for a description of the download → visualization pipeline.

## Prerequisites

Register for a free FRED API key at https://fred.stlouisfed.org/docs/api/api_key.html, then
set the environment variable before running:

```bash
export FRED_API_KEY="your_key_here"
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the refresh

```bash
# Full refresh — download all series and regenerate all plots
python refresh.py

# Resume — skip series already downloaded
python refresh.py --resume

# Plots only — regenerate charts from existing data/ CSVs without re-downloading
python refresh.py --skip-download

# Download only — fetch data without generating any charts
python refresh.py --skip-viz
```

Both commands print `[summary]` counters and `[latest]` timestamps so you can confirm
the run touched all expected series and see the newest observation date.

## Series catalog

Edit `config/series_catalog.toml` to track different or additional FRED series. Each entry
requires at minimum an `id` field; `title`, `category`, `frequency`, and `units` are optional
and fall back to the `[defaults]` block.

Example entry:

```toml
[[series]]
id = "INDPRO"
title = "Industrial Production Index"
category = "production"
frequency = "m"
units = "lin"
```

## Directory layout

```
fred-public-data/
├── config/
│   ├── series_catalog.toml   ← series list (edit to add/remove series)
│   └── tachometer/
│       └── profile.toml
├── data/                     ← generated; gitignored
│   ├── national_accounts/
│   ├── labor_market/
│   ├── prices/
│   ├── interest_rates/
│   ├── housing/
│   ├── markets/
│   └── commodities/
├── docs/
│   └── ARCHITECTURE.md
├── scripts/
│   └── run_tachometer_profile.sh
├── tests/
│   └── test_refresh.py
├── viz/                      ← generated; gitignored
├── refresh.py
├── requirements.txt
└── pyproject.toml
```
