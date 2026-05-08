# AGENTS.md

## Project Purpose

This repo mirrors FRED (Federal Reserve Economic Data) time-series via the FRED API,
stores observations as local CSVs, and generates a chart corpus for exploratory
economic research and README publication.

## Reference URLs

- **FRED API documentation:** https://fred.stlouisfed.org/docs/api/fred/
- **API key registration:** https://fred.stlouisfed.org/docs/api/api_key.html
- **Series browser:** https://fred.stlouisfed.org/
- **Release calendar:** https://fred.stlouisfed.org/releases/calendar

## Repo Layout

- `config/series_catalog.toml`: canonical list of FRED series IDs to track, with per-series
  frequency and units settings. Edit this file to add or remove series.
- `refresh.py`: canonical batch workflow for download, validation, plot generation, and
  freshness reporting.
- `explore.ipynb`: example notebook covering keyless data fetching, YoY growth, recession
  shading, inflation vs Fed Funds rate, and yield curve analysis.
- `scripts/make_explore_notebook.py`: regenerates `explore.ipynb` from its embedded cell
  source strings. Run after editing cell content in the script.
- `data/`: downloaded CSV observations, organized by category subdirectory. Generated output,
  large, and kept out of git.
- `viz/`: full regenerated plot set, organized by category. Generated output, kept out of git.
- `config/tachometer/profile.toml`: tachometer profiler manifest for this repo.
- `scripts/run_tachometer_profile.sh`: tachometer runner script.

## Authentication

`refresh.py` works without any credentials by default. When `FRED_API_KEY` is not set it
uses the public `fredgraph.csv` endpoint — no registration required.

Setting `FRED_API_KEY` switches to the full REST API, which supports the `frequency` and
`units` transforms declared per-series in `config/series_catalog.toml`. Register for a free
key at https://fred.stlouisfed.org/docs/api/api_key.html.

```bash
export FRED_API_KEY="your_key_here"   # optional; enables frequency/units transforms
```

Never commit the key. Use a `.env` file excluded by `.gitignore`, or retrieve it from
`./util-repos/auto-pass` if it is stored in KeePassXC.

## Working Rules

- `python refresh.py` works out-of-the-box with no credentials (public CSV endpoint).
- Prefer `python refresh.py --resume` for standard refresh work (skips already-downloaded series).
- Use `python refresh.py --skip-download` when only the plots need to be regenerated.
- Use `python refresh.py --skip-viz` when you only want to test the download path.
- Add new series by appending a `[[series]]` block to `config/series_catalog.toml`.
- Do not commit `data/` or `viz/` unless the user explicitly asks and confirms the storage plan.
- The FRED missing-value sentinel is `"."` — `refresh.py` drops these rows via `pd.to_numeric(errors="coerce")`.
- `frequency` and `units` catalog fields are only applied when `FRED_API_KEY` is set; the CSV endpoint always returns the default release frequency.

## Validation

1. Run `pytest tests/test_refresh.py` after changing catalog loading or fetch logic.
2. Run `python refresh.py --resume` to validate the full pipeline end-to-end.
3. Confirm the `[summary]` and `[latest]` lines look sane.

## Sudo Boundary

Agents will never be able to run `sudo` commands in this environment. If a task requires elevated system changes, make the repo edits and run the validation that can be done without `sudo`, then give the user the exact command(s) to run.

Always require the user to run those commands instead of retrying `sudo`; do not claim a sudo-backed live change was applied until the user shares the result.

## Local CI Verification

Run before every push:

```bash
pre-commit run --all-files
pytest -q
```

Do not push changes that have not passed all checks locally.

## Portfolio Standards Reference

For portfolio-wide repository standards and baseline conventions, consult the control-plane repo at `./util-repos/traction-control` from the portfolio root.

Start with:
- `./util-repos/traction-control/AGENTS.md`
- `./util-repos/traction-control/README.md`
- `./util-repos/traction-control/LESSONSLEARNED.md`

Shared implementation repos available portfolio-wide:
- `./util-repos/archility` for architecture toolchain bootstrap/render orchestration, Graphviz-capable diagram support, deterministic starter scaffolding, agentic architecture authoring, and architecture-documentation drift checks
- `./util-repos/auto-pass` for KeePassXC-backed password management and secret retrieval/update flows
- `./util-repos/nordility` for NordVPN-based VPN switching and connection orchestration
- `./util-repos/shock-relay` for external messaging across supported providers such as Signal, Telegram, Twilio SMS, WhatsApp, and Gmail IMAP
- `./util-repos/snowbridge` for SMB-based private file sharing and phone-accessible fileshare workflows
- `./util-repos/dyno-lab` for unified test bench utilities — fixtures, subprocess/HTTP/env mocks, schema validation, smoke scaffolding, and pytest markers/fixtures
- `./util-repos/short-circuit` for WireGuard VPN setup and configuration, establishing private tunnels with SMB, HTTPS, and SSH access

When another repo needs architecture toolchain bootstrap/rendering, architecture inventory/scaffolding, password management, VPN switching, or external messaging, prefer integrating with these repos instead of re-implementing the capability locally.

## Agent Memory

Use `./LESSONSLEARNED.md` as the tracked durable lessons file for this repo.
Use `./CHATHISTORY.md` as the standard local handoff file for this repo.

- `LESSONSLEARNED.md` is tracked and should capture only reusable lessons.
- `CHATHISTORY.md` is local-only, gitignored, and should capture transient handoff context.
- Read `LESSONSLEARNED.md` and `CHATHISTORY.md` after `AGENTS.md` when resuming work.
- Add durable lessons to `LESSONSLEARNED.md` when they should influence future sessions.
- Keep transient entries concise and focused on refresh status, generated artifacts, blockers, and next steps.
