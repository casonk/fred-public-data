# Contributor Architecture

This document traces the download → validation → visualization pipeline implemented by
`refresh.py`, and separates that runtime path from any manual publish steps.

## Visual diagrams

- `docs/diagrams/repo-architecture.puml`: PlantUML source for the core workflow. Run
  `plantuml docs/diagrams/repo-architecture.puml` to regenerate PNG/SVG renders when
  the data-flow changes.
- `docs/diagrams/repo-architecture.drawio`: Draw.io project (zipped XML). Open it in
  `https://app.diagrams.net` or `drawio` desktop to make tweaks and export artwork as needed.

Both sources are portfolio-standard layout files. Use `./util-repos/archility` to
regenerate or drift-check the starter layout.

## Key Components

- `config/series_catalog.toml`: declarative list of FRED series IDs to track. Each entry
  carries an `id`, `title`, `category`, `frequency`, and `units`. `refresh.py` reads this at
  startup — add or remove series here without touching Python.
- `refresh.py`: the central workflow. It:
  1. parses operator flags and ensures `data/` and `viz/` exist,
  2. loads `config/series_catalog.toml` via `load_catalog`,
  3. resolves the `FRED_API_KEY` environment variable,
  4. fetches observations for each series from the FRED REST API via `fetch_observations`,
  5. writes per-series CSVs into `data/<category>/<SERIES_ID>.csv`,
  6. regenerates time-series line charts into `viz/<category>/<SERIES_ID>.png` via `plot_all`,
  7. reports the newest observation date per series with `latest_dates`.
- `data/`: final download output grouped by category (e.g. `data/labor_market/UNRATE.csv`).
- `viz/`: every generated PNG, one per series. The full local render corpus.
- `tests/test_refresh.py`: offline checks for catalog loading, spec validation, and
  observation parsing (including the FRED missing-value sentinel `"."`).

## Data Flow

1. `refresh.py --resume` reads `series_catalog.toml` and builds the full series list. When
   `--resume` is set, series whose CSV already exists and is non-empty are skipped.
2. For each series, the script calls `GET /fred/series/observations` with the configured
   `frequency` and `units` parameters. The FRED API returns JSON.
3. Observations are parsed into a two-column DataFrame (`date`, `value`). Rows where `value`
   is the FRED sentinel `"."` are dropped via `pd.to_numeric(errors="coerce")`.
4. The cleaned DataFrame is written to `data/<category>/<SERIES_ID>.csv`.
5. Once the download pass finishes (or when `--skip-download` is used), `plot_all` iterates
   the catalog and generates a line chart for each series whose CSV is present.
6. The command prints `[summary]` counters and `[latest]` timestamps so the operator can
   verify what was refreshed.

## Fetch Strategy

`fetch_observations` dispatches based on whether `FRED_API_KEY` is set:

- **No key (default):** `_fetch_via_csv` — calls `https://fred.stlouisfed.org/graph/fredgraph.csv?id=<ID>`.
  No credentials required. Returns the default release frequency; `frequency` and `units`
  catalog fields are ignored.
- **Key present:** `_fetch_via_api` — calls `GET /fred/series/observations` with the
  configured `frequency` and `units` parameters, enabling aggregation and unit transforms.

Both paths normalize output to a two-column DataFrame (`date`, `value`) and drop rows where
`value` is the FRED missing-value sentinel `"."`.

## Authentication Boundary

`FRED_API_KEY` is optional. When set it is resolved exclusively from the environment variable
and is never written to disk, logged, or included in any committed file. Use a shell profile,
`.env` (gitignored), or `./util-repos/auto-pass` for key retrieval.
