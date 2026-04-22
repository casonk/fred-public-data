# Contributor Architecture Blueprint

This document is a concise map of how `fred-public-data` expands its series
catalog, refreshes downloaded observations from FRED, regenerates the chart
corpus, and then reports freshness to the operator.

## High-Level Layers

1. Catalog and configuration layer (`config/series_catalog.toml`, `load_catalog`)
   - The tracked TOML catalog is the source of truth for which FRED series the
     repo mirrors.
   - Each series entry carries its identifier plus optional category,
     frequency, and units overrides.
2. Download and normalization layer (`refresh.py`, `fetch_observations`, `data/`)
   - `refresh.py` resolves the `FRED_API_KEY`, calls the FRED observations API,
     and writes per-series CSVs under `data/<category>/`.
   - Missing-value rows using the FRED `"."` sentinel are dropped during numeric
     coercion so downstream charts stay numeric.
3. Visualization layer (`plot_all`, `viz/`)
   - The refresh workflow regenerates one PNG chart per series under `viz/`,
     grouped by category.
   - `--skip-download` reuses existing CSVs when only visualization logic needs
     to be refreshed.
4. Reporting and operator feedback layer (`[summary]`, `[latest]`)
   - Each refresh prints aggregate counters plus the newest observation date per
     series so the operator can confirm data freshness after a run.
5. Test and documentation layer (`tests/test_refresh.py`, `docs/`)
   - `tests/test_refresh.py` keeps catalog validation and parsing behavior
     stable without making live API calls.
   - `docs/ARCHITECTURE.md` and `docs/diagrams/` should describe the same
     refresh pipeline and artifact boundaries as the code.

## Key Entry Points

- `python refresh.py --resume`
- `python refresh.py --skip-download`
- `python refresh.py --skip-viz`
- `pytest tests/test_refresh.py`
- `.github/workflows/ci.yml`

## Validation

```bash
pytest tests/test_refresh.py
python refresh.py --resume
python refresh.py --skip-download
```

After a real refresh, confirm the `[summary]` and `[latest]` lines still look
plausible for the tracked series set and that no local-only data artifacts were
accidentally staged.
