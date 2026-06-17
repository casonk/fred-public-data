import pandas as pd

from refresh import SeriesSpec, fetch_observations, load_catalog


def test_load_catalog_not_empty():
    catalog = load_catalog()
    assert isinstance(catalog, list)
    assert catalog, "series_catalog.toml should define at least one series"


def test_load_catalog_all_have_ids():
    catalog = load_catalog()
    for spec in catalog:
        assert isinstance(spec, SeriesSpec)
        assert spec.id, f"series entry missing id: {spec}"


def test_load_catalog_known_series_present():
    catalog = load_catalog()
    ids = {s.id for s in catalog}
    for expected in ("GDP", "UNRATE", "FEDFUNDS"):
        assert expected in ids, f"expected series {expected!r} not found in catalog"


def test_series_spec_frequency_valid():
    valid_frequencies = {"d", "w", "m", "q", "sa", "a"}
    catalog = load_catalog()
    for spec in catalog:
        msg = f"{spec.id}: unexpected frequency {spec.frequency!r}"
        assert spec.frequency in valid_frequencies, msg


def test_fetch_observations_api_path(monkeypatch):
    mock_payload = {
        "observations": [
            {"date": "2024-01-01", "value": "100.0"},
            {"date": "2024-04-01", "value": "101.5"},
            {"date": "2024-07-01", "value": "."},  # FRED missing-value sentinel
        ]
    }

    class MockResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return mock_payload

    class MockSession:
        def get(self, *args, **kwargs):
            return MockResponse()

    spec = SeriesSpec(id="GDP", title="Gross Domestic Product", category="national_accounts")
    df = fetch_observations(MockSession(), spec, key="test_key")

    assert df is not None
    assert len(df) == 2, "missing-value sentinel '.' should be dropped"
    assert list(df.columns) == ["date", "value"]
    assert pd.api.types.is_datetime64_any_dtype(df["date"])
    assert pd.api.types.is_float_dtype(df["value"])


def test_fetch_observations_csv_path_no_key():
    csv_body = "DATE,GDP\n2024-01-01,100.0\n2024-04-01,101.5\n2024-07-01,.\n"

    class MockResponse:
        text = csv_body

        def raise_for_status(self):
            pass

    class MockSession:
        def get(self, *args, **kwargs):
            return MockResponse()

    spec = SeriesSpec(id="GDP", title="Gross Domestic Product", category="national_accounts")
    df = fetch_observations(MockSession(), spec, key=None)

    assert df is not None
    assert len(df) == 2, "missing-value sentinel '.' should be dropped on CSV path"
    assert list(df.columns) == ["date", "value"]
    assert pd.api.types.is_datetime64_any_dtype(df["date"])
    assert pd.api.types.is_float_dtype(df["value"])
