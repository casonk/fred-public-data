#!/usr/bin/env python3
"""Generate explore.ipynb from embedded cell source strings.

Run once (or whenever cells change) to rebuild the notebook:
    python scripts/make_explore_notebook.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def code_cell(cell_id: str, source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "id": cell_id,
        "metadata": {},
        "outputs": [],
        "source": source,
    }


def md_cell(cell_id: str, source: str) -> dict:
    return {"cell_type": "markdown", "id": cell_id, "metadata": {}, "source": source}


# ---------------------------------------------------------------------------
# Cell source strings — written as plain Python, json.dump handles escaping
# ---------------------------------------------------------------------------

SETUP = """\
import io
import warnings
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import requests

warnings.filterwarnings("ignore", category=FutureWarning)

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv"
VIZ_DIR = Path("viz")
VIZ_DIR.mkdir(exist_ok=True)

plt.rcParams.update({"figure.dpi": 120, "axes.grid": True, "grid.alpha": 0.3, "axes.axisbelow": True})


def fetch(series_id: str) -> pd.Series:
    \"\"\"Fetch a FRED series as a date-indexed Series (public CSV endpoint — no API key).\"\"\"
    resp = requests.get(FRED_CSV, params={"id": series_id}, timeout=30)
    resp.raise_for_status()
    df = pd.read_csv(io.StringIO(resp.text))
    df.columns = ["date", "value"]
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna().set_index("date")["value"].rename(series_id)


def shade_recessions(ax: plt.Axes, usrec: pd.Series) -> None:
    \"\"\"Shade NBER recession periods gray on the given axes.\"\"\"
    in_rec, start = False, None
    for date, val in usrec.items():
        if val == 1 and not in_rec:
            in_rec, start = True, date
        elif val == 0 and in_rec:
            ax.axvspan(start, date, alpha=0.12, color="gray", zorder=0)
            in_rec = False
    if in_rec:
        ax.axvspan(start, usrec.index[-1], alpha=0.12, color="gray", zorder=0)
"""

FETCH = """\
print("Fetching series from FRED public CSV endpoint (no API key required)...\\n")

series_meta = {
    "GDPC1":    "Real GDP (Quarterly, Bil. Chained 2017 $)",
    "UNRATE":   "Unemployment Rate (%)",
    "PAYEMS":   "Nonfarm Payrolls (Thousands)",
    "CPIAUCSL": "CPI All Urban Consumers (Index 1982-84=100)",
    "FEDFUNDS": "Effective Federal Funds Rate (%)",
    "T10Y2Y":   "10-Year minus 2-Year Treasury Spread (%)",
    "USREC":    "NBER Recession Indicator (0/1)",
}

data = {}
for sid, desc in series_meta.items():
    data[sid] = fetch(sid)
    latest = data[sid].index[-1].date()
    print(f"  {sid:12s}  {len(data[sid]):>5} obs  latest: {latest}  \u2014 {desc}")

gdp      = data["GDPC1"]
unrate   = data["UNRATE"]
payems   = data["PAYEMS"]
cpi      = data["CPIAUCSL"]
fedfunds = data["FEDFUNDS"]
spread   = data["T10Y2Y"]
usrec    = data["USREC"]

print("\\nAll series fetched.")
"""

GDP_CHART = """\
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), sharex=False)

# --- Level ---
gdp_t = gdp / 1_000
ax1.plot(gdp_t.index, gdp_t.values, color="#1f77b4", linewidth=1.5)
shade_recessions(ax1, usrec.reindex(gdp.index, method="ffill").fillna(0))
ax1.set_title("Real GDP (GDPC1)", fontsize=12, fontweight="bold")
ax1.set_ylabel("Trillions of Chained 2017 USD")
for spine in ["top", "right"]:
    ax1.spines[spine].set_visible(False)

# --- YoY growth rate (4 quarters = 1 year) ---
gdp_yoy = gdp.pct_change(4) * 100
gdp_yoy_clean = gdp_yoy.dropna()
bar_colors = ["#d62728" if v < 0 else "#2ca02c" for v in gdp_yoy_clean.values]
ax2.bar(gdp_yoy_clean.index, gdp_yoy_clean.values, width=60, color=bar_colors, alpha=0.85)
ax2.axhline(0, color="black", linewidth=0.8)
shade_recessions(ax2, usrec.reindex(gdp_yoy_clean.index, method="ffill").fillna(0))
ax2.set_title("Real GDP \u2014 Year-over-Year Growth (%)", fontsize=12, fontweight="bold")
ax2.set_ylabel("YoY %")
for spine in ["top", "right"]:
    ax2.spines[spine].set_visible(False)

for ax in (ax1, ax2):
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.xaxis.set_major_locator(mdates.YearLocator(10))

fig.tight_layout(pad=2)
fig.savefig(VIZ_DIR / "gdp_analysis.png", bbox_inches="tight")
plt.show()
print(f"Latest Real GDP: ${gdp_t.iloc[-1]:.2f}T  |  YoY Growth: {gdp_yoy.iloc[-1]:.1f}%")
"""

LABOR_CHART = """\
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), sharex=False)

# --- Unemployment rate ---
ax1.plot(unrate.index, unrate.values, color="#e377c2", linewidth=1.3)
shade_recessions(ax1, usrec.reindex(unrate.index, method="ffill").fillna(0))
ax1.set_title("Unemployment Rate (UNRATE)", fontsize=12, fontweight="bold")
ax1.set_ylabel("Percent (%)")
for spine in ["top", "right"]:
    ax1.spines[spine].set_visible(False)

# --- Nonfarm payrolls month-over-month change ---
payems_mom = payems.diff().dropna()
bar_colors = ["#d62728" if v < 0 else "#1f77b4" for v in payems_mom.values]
ax2.bar(payems_mom.index, payems_mom.values, width=20, color=bar_colors, alpha=0.85)
ax2.axhline(0, color="black", linewidth=0.8)
shade_recessions(ax2, usrec.reindex(payems_mom.index, method="ffill").fillna(0))
ax2.set_title("Nonfarm Payrolls \u2014 Month-over-Month Change (PAYEMS)", fontsize=12, fontweight="bold")
ax2.set_ylabel("Change (Thousands)")
for spine in ["top", "right"]:
    ax2.spines[spine].set_visible(False)

for ax in (ax1, ax2):
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.xaxis.set_major_locator(mdates.YearLocator(10))

fig.tight_layout(pad=2)
fig.savefig(VIZ_DIR / "labor_market.png", bbox_inches="tight")
plt.show()
print(f"Latest Unemployment: {unrate.iloc[-1]:.1f}%  |  Latest Payrolls Change: {payems_mom.iloc[-1]:+,.0f}K")
"""

INFLATION_CHART = """\
cpi_yoy = cpi.pct_change(12) * 100

common_idx = cpi_yoy.dropna().index.intersection(fedfunds.index)
cpi_c = cpi_yoy.loc[common_idx]
ff_c  = fedfunds.loc[common_idx]
rec_c = usrec.reindex(common_idx, method="ffill").fillna(0)

fig, ax1 = plt.subplots(figsize=(12, 5))
ax1.set_title("CPI Inflation (YoY %) vs Effective Federal Funds Rate", fontsize=12, fontweight="bold")

ax1.fill_between(cpi_c.index, cpi_c.values, 2, alpha=0.2,
                 where=(cpi_c.values > 2), interpolate=True,
                 color="#d62728", label="CPI above 2% target")
ax1.fill_between(cpi_c.index, cpi_c.values, 2, alpha=0.2,
                 where=(cpi_c.values <= 2), interpolate=True,
                 color="#2ca02c", label="CPI at/below 2% target")
ax1.plot(cpi_c.index, cpi_c.values, color="#d62728", linewidth=1.5, label="CPI YoY %")
ax1.axhline(2, color="#666", linewidth=0.8, linestyle="--", label="2% Fed target")
ax1.set_ylabel("CPI YoY %", color="#d62728")
ax1.tick_params(axis="y", labelcolor="#d62728")
ax1.spines["top"].set_visible(False)

ax2 = ax1.twinx()
ax2.plot(ff_c.index, ff_c.values, color="#1f77b4", linewidth=1.4, alpha=0.85, label="Fed Funds Rate %")
ax2.set_ylabel("Fed Funds Rate %", color="#1f77b4")
ax2.tick_params(axis="y", labelcolor="#1f77b4")

shade_recessions(ax1, rec_c)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=9)
ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax1.xaxis.set_major_locator(mdates.YearLocator(5))

fig.tight_layout()
fig.savefig(VIZ_DIR / "cpi_vs_fedfunds.png", bbox_inches="tight")
plt.show()
print(f"Latest CPI YoY: {cpi_yoy.iloc[-1]:.1f}%  |  Latest Fed Funds: {fedfunds.iloc[-1]:.2f}%")
"""

YIELD_CHART = """\
spread_m = spread.resample("MS").mean()
rec_m = usrec.reindex(spread_m.index, method="ffill").fillna(0)

fig, ax = plt.subplots(figsize=(12, 4))
ax.fill_between(
    spread_m.index, spread_m.values, 0,
    where=(spread_m.values >= 0), interpolate=True,
    color="#2ca02c", alpha=0.45, label="Normal (spread \u2265 0)",
)
ax.fill_between(
    spread_m.index, spread_m.values, 0,
    where=(spread_m.values < 0), interpolate=True,
    color="#d62728", alpha=0.55, label="Inverted (spread < 0)",
)
ax.plot(spread_m.index, spread_m.values, color="#333", linewidth=0.8, alpha=0.7)
ax.axhline(0, color="black", linewidth=1.0)
shade_recessions(ax, rec_m)
ax.set_title(
    "Yield Curve: 10-Year minus 2-Year Treasury Spread (T10Y2Y)", fontsize=12, fontweight="bold"
)
ax.set_ylabel("Spread (%)")
ax.legend(loc="lower left", fontsize=9)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.xaxis.set_major_locator(mdates.YearLocator(5))
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)

fig.tight_layout()
fig.savefig(VIZ_DIR / "yield_curve.png", bbox_inches="tight")
plt.show()
current = spread.iloc[-1]
print(
    f"Latest 10Y-2Y Spread: {current:.2f}%  "
    f"({'inverted' if current < 0 else 'normal'})"
    f"  |  Data range: {spread.index[0].date()} \u2192 {spread.index[-1].date()}"
)
"""

SUMMARY = """\
rows = []
for sid, s in data.items():
    if sid == "USREC":
        continue
    rows.append({
        "Series": sid,
        "Start": str(s.index[0].date()),
        "End": str(s.index[-1].date()),
        "Obs": len(s),
        "Min": round(float(s.min()), 2),
        "Max": round(float(s.max()), 2),
        "Mean": round(float(s.mean()), 2),
        "Latest": round(float(s.iloc[-1]), 2),
    })

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 120)
summary = pd.DataFrame(rows).set_index("Series")
print(summary.to_string())
"""

# ---------------------------------------------------------------------------
# Assemble notebook
# ---------------------------------------------------------------------------

cells = [
    md_cell(
        "intro",
        "# FRED Public Data \u2014 Example Analysis\n\n"
        "Demonstrates basic FRED data fetching, crunching, and visualization using the "
        "**public `fredgraph.csv` endpoint \u2014 no API key required**.\n\n"
        "Series covered:\n"
        "- **GDPC1** \u2014 Real GDP (quarterly)\n"
        "- **UNRATE** \u2014 Unemployment Rate (monthly)\n"
        "- **PAYEMS** \u2014 Nonfarm Payrolls (monthly)\n"
        "- **CPIAUCSL** \u2014 CPI All Urban Consumers (monthly)\n"
        "- **FEDFUNDS** \u2014 Effective Federal Funds Rate (monthly)\n"
        "- **T10Y2Y** \u2014 10-Year minus 2-Year Treasury Spread (daily)\n"
        "- **USREC** \u2014 NBER Recession Indicator (monthly)\n\n"
        "Gray bands on charts mark NBER-defined recession periods.",
    ),
    code_cell("setup", SETUP),
    md_cell("fetch-header", "## Fetch Series Data"),
    code_cell("fetch", FETCH),
    md_cell(
        "gdp-header",
        "## GDP: Level and Year-over-Year Growth\n\n"
        "Real GDP is the inflation-adjusted value of all goods and services produced. "
        "The year-over-year growth rate (current quarter vs same quarter one year prior) "
        "highlights cyclical expansions and contractions.",
    ),
    code_cell("gdp-chart", GDP_CHART),
    md_cell(
        "labor-header",
        "## Labor Market: Unemployment and Payrolls\n\n"
        "The unemployment rate measures the share of the labor force actively seeking work. "
        "Nonfarm payrolls track the month-over-month change in total employed workers, "
        "a leading indicator of economic momentum.",
    ),
    code_cell("labor-chart", LABOR_CHART),
    md_cell(
        "inflation-header",
        "## Inflation vs Federal Funds Rate\n\n"
        "Year-over-year CPI change vs the Fed\u2019s policy rate. "
        "The Fed typically hikes rates when inflation runs above its 2% target "
        "and cuts when the economy needs stimulus.",
    ),
    code_cell("inflation-chart", INFLATION_CHART),
    md_cell(
        "yield-header",
        "## Yield Curve: 10-Year minus 2-Year Treasury Spread\n\n"
        "An inverted yield curve (spread < 0) has historically preceded most U.S. recessions "
        "by 6\u201324 months. The daily spread is resampled to monthly averages for display.",
    ),
    code_cell("yield-chart", YIELD_CHART),
    md_cell("summary-header", "## Summary Statistics"),
    code_cell("summary", SUMMARY),
]

notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.10.0"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

out = ROOT / "explore.ipynb"
with out.open("w", encoding="utf-8") as fh:
    json.dump(notebook, fh, indent=1, ensure_ascii=False)
    fh.write("\n")

print(f"Written: {out}")
