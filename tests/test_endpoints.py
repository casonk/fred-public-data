"""Integration tests for the FRED public CSV endpoint.

Each series declared in config/series_catalog.toml is fetched from
https://fred.stlouisfed.org/graph/fredgraph.csv and validated for
structure, parseability, and basic freshness.

These tests require a live internet connection and are skipped by
default.  Run them explicitly with:

    pytest -m integration
    pytest -m integration -v          # one line per series
    pytest -m integration --tb=short  # compact tracebacks on failure
"""

import sys
from pathlib import Path

import pandas as pd
import pytest
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from refresh import SeriesSpec, fetch_observations, load_catalog

CATALOG = load_catalog()


# ---------------------------------------------------------------------------
# Keyless CSV endpoint — one test per catalog series
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.parametrize("spec", CATALOG, ids=[s.id for s in CATALOG])
def test_series_csv_returns_data(spec: SeriesSpec) -> None:
    """Series must return a non-empty DataFrame via the public CSV path."""
    with requests.Session() as session:
        df = fetch_observations(session, spec, key=None)

    assert df is not None, f"{spec.id}: fetch returned None"
    assert not df.empty, f"{spec.id}: returned empty DataFrame"


@pytest.mark.integration
@pytest.mark.parametrize("spec", CATALOG, ids=[s.id for s in CATALOG])
def test_series_csv_schema(spec: SeriesSpec) -> None:
    """DataFrame must have exactly ['date', 'value'] columns with correct dtypes."""
    with requests.Session() as session:
        df = fetch_observations(session, spec, key=None)

    assert df is not None, f"{spec.id}: fetch returned None"
    cols_msg = f"{spec.id}: unexpected columns {list(df.columns)}"
    assert list(df.columns) == ["date", "value"], cols_msg
    date_msg = f"{spec.id}: 'date' column is not datetime64"
    assert pd.api.types.is_datetime64_any_dtype(df["date"]), date_msg
    numeric_msg = f"{spec.id}: 'value' column is not numeric (got {df['value'].dtype})"
    assert pd.api.types.is_numeric_dtype(df["value"]), numeric_msg


@pytest.mark.integration
@pytest.mark.parametrize("spec", CATALOG, ids=[s.id for s in CATALOG])
def test_series_csv_min_observations(spec: SeriesSpec) -> None:
    """Each series must have at least 12 non-null observations."""
    with requests.Session() as session:
        df = fetch_observations(session, spec, key=None)

    assert df is not None, f"{spec.id}: fetch returned None"
    n = df["value"].notna().sum()
    assert n >= 12, f"{spec.id}: only {n} non-null observations (expected >= 12)"


@pytest.mark.integration
@pytest.mark.parametrize("spec", CATALOG, ids=[s.id for s in CATALOG])
def test_series_csv_freshness(spec: SeriesSpec) -> None:
    """Latest observation must be on or after 2020-01-01."""
    with requests.Session() as session:
        df = fetch_observations(session, spec, key=None)

    assert df is not None, f"{spec.id}: fetch returned None"
    latest = df["date"].max()
    fresh_msg = f"{spec.id}: latest date {latest.date()} predates 2020-01-01"
    assert latest >= pd.Timestamp("2020-01-01"), fresh_msg


@pytest.mark.integration
@pytest.mark.parametrize("spec", CATALOG, ids=[s.id for s in CATALOG])
def test_series_csv_no_all_nan(spec: SeriesSpec) -> None:
    """Value column must contain at least one finite number."""
    with requests.Session() as session:
        df = fetch_observations(session, spec, key=None)

    assert df is not None, f"{spec.id}: fetch returned None"
    assert df["value"].notna().any(), f"{spec.id}: all values are NaN or missing"


# ---------------------------------------------------------------------------
# API endpoint — skipped when FRED_API_KEY is absent
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.parametrize("spec", CATALOG, ids=[s.id for s in CATALOG])
def test_series_api_returns_data(spec: SeriesSpec) -> None:
    """Series must also be fetchable via the API path (requires FRED_API_KEY)."""
    import os

    key = os.environ.get("FRED_API_KEY", "").strip()
    if not key:
        pytest.skip("FRED_API_KEY not set")

    with requests.Session() as session:
        df = fetch_observations(session, spec, key=key)

    assert df is not None, f"{spec.id}: API fetch returned None"
    assert not df.empty, f"{spec.id}: API returned empty DataFrame"
    api_cols_msg = f"{spec.id}: unexpected API columns {list(df.columns)}"
    assert list(df.columns) == ["date", "value"], api_cols_msg
