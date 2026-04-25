#!/usr/bin/env python3
"""Fetch FRED data and write example PNGs to examples/.

Run from the repo root:
    python scripts/generate_examples.py

Requires no API key — uses the public fredgraph.csv endpoint.
Also prints a markdown-ready data summary table to stdout.
"""

import io
import sys
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = ROOT / "examples"
EXAMPLES_DIR.mkdir(exist_ok=True)

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv"

plt.rcParams.update(
    {"figure.dpi": 150, "axes.grid": True, "grid.alpha": 0.3, "axes.axisbelow": True}
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def fetch(series_id: str) -> pd.Series:
    resp = requests.get(FRED_CSV, params={"id": series_id}, timeout=30)
    resp.raise_for_status()
    df = pd.read_csv(io.StringIO(resp.text))
    df.columns = ["date", "value"]
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna().set_index("date")["value"].rename(series_id)


def shade_recessions(ax: plt.Axes, usrec: pd.Series) -> None:
    in_rec, start = False, None
    for date, val in usrec.items():
        if val == 1 and not in_rec:
            in_rec, start = True, date
        elif val == 0 and in_rec:
            ax.axvspan(start, date, alpha=0.12, color="gray", zorder=0)
            in_rec = False
    if in_rec:
        ax.axvspan(start, usrec.index[-1], alpha=0.12, color="gray", zorder=0)


def rec_for(s: pd.Series, usrec: pd.Series) -> pd.Series:
    return usrec.reindex(s.index, method="ffill").fillna(0)


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------

SERIES_META = {
    "GDPC1": ("national_accounts", "Real GDP", "Quarterly", "Bil. Chained 2017 $"),
    "UNRATE": ("labor_market", "Unemployment Rate", "Monthly", "%"),
    "PAYEMS": ("labor_market", "Nonfarm Payrolls", "Monthly", "Thousands"),
    "CPIAUCSL": ("prices", "CPI All Urban Consumers", "Monthly", "Index 1982-84=100"),
    "PCEPI": ("prices", "PCE Chain-type Price Index", "Monthly", "Index 2017=100"),
    "FEDFUNDS": ("interest_rates", "Effective Federal Funds Rate", "Monthly", "%"),
    "T10Y2Y": ("interest_rates", "10Y-2Y Treasury Spread", "Daily", "%"),
    "MORTGAGE30US": ("housing", "30-Year Fixed Mortgage Rate", "Weekly", "%"),
    "HOUST": ("housing", "Housing Starts: Total", "Monthly", "Thousands of Units"),
    "USREC": ("indicators", "NBER Recession Indicator", "Monthly", "0/1"),
}

print("Fetching series from FRED public CSV endpoint (no API key)...\n", file=sys.stderr)

data: dict[str, pd.Series] = {}
for sid in SERIES_META:
    data[sid] = fetch(sid)
    s = data[sid]
    print(
        f"  {sid:12s}  {len(s):>5} obs  {s.index[0].date()} \u2192 {s.index[-1].date()}",
        file=sys.stderr,
    )

gdp = data["GDPC1"]
unrate = data["UNRATE"]
payems = data["PAYEMS"]
cpi = data["CPIAUCSL"]
pce = data["PCEPI"]
fedfunds = data["FEDFUNDS"]
spread = data["T10Y2Y"]
mortgage = data["MORTGAGE30US"]
houst = data["HOUST"]
usrec = data["USREC"]

print("\nAll series fetched.\n", file=sys.stderr)

# ---------------------------------------------------------------------------
# Markdown data summary table (stdout — redirect into EXAMPLES.md if needed)
# ---------------------------------------------------------------------------

print("| Series | Category | Description | Frequency | Unit | Start | End | Observations |")
print("|--------|----------|-------------|-----------|------|-------|-----|-------------|")
for sid, (cat, desc, freq, unit) in SERIES_META.items():
    s = data[sid]
    print(
        f"| `{sid}` | {cat} | {desc} | {freq} | {unit} "
        f"| {s.index[0].date()} | {s.index[-1].date()} | {len(s):,} |"
    )

# ---------------------------------------------------------------------------
# Chart 1 — GDP level + YoY growth
# ---------------------------------------------------------------------------

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), sharex=False)

gdp_t = gdp / 1_000
ax1.plot(gdp_t.index, gdp_t.values, color="#1f77b4", linewidth=1.6)
shade_recessions(ax1, rec_for(gdp, usrec))
ax1.set_title("Real GDP (GDPC1)", fontsize=13, fontweight="bold")
ax1.set_ylabel("Trillions of Chained 2017 USD")
for sp in ["top", "right"]:
    ax1.spines[sp].set_visible(False)

gdp_yoy = gdp.pct_change(4) * 100
gdp_yoy_clean = gdp_yoy.dropna()
bar_colors = ["#d62728" if v < 0 else "#2ca02c" for v in gdp_yoy_clean.values]
ax2.bar(gdp_yoy_clean.index, gdp_yoy_clean.values, width=60, color=bar_colors, alpha=0.85)
ax2.axhline(0, color="black", linewidth=0.9)
shade_recessions(ax2, rec_for(gdp_yoy_clean, usrec))
ax2.set_title("Real GDP \u2014 Year-over-Year Growth (%)", fontsize=13, fontweight="bold")
ax2.set_ylabel("YoY %")
for sp in ["top", "right"]:
    ax2.spines[sp].set_visible(False)

for ax in (ax1, ax2):
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.xaxis.set_major_locator(mdates.YearLocator(10))

fig.tight_layout(pad=2)
fig.savefig(EXAMPLES_DIR / "gdp_analysis.png", bbox_inches="tight")
plt.close(fig)
print(
    f"\nLatest Real GDP: ${gdp_t.iloc[-1]:.2f}T  |  YoY Growth: {gdp_yoy.iloc[-1]:.1f}%",
    file=sys.stderr,
)

# ---------------------------------------------------------------------------
# Chart 2 — Labor market
# ---------------------------------------------------------------------------

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), sharex=False)

ax1.plot(unrate.index, unrate.values, color="#e377c2", linewidth=1.4)
shade_recessions(ax1, rec_for(unrate, usrec))
ax1.set_title("Unemployment Rate (UNRATE)", fontsize=13, fontweight="bold")
ax1.set_ylabel("Percent (%)")
for sp in ["top", "right"]:
    ax1.spines[sp].set_visible(False)

payems_mom = payems.diff().dropna()
bar_colors = ["#d62728" if v < 0 else "#1f77b4" for v in payems_mom.values]
ax2.bar(payems_mom.index, payems_mom.values, width=20, color=bar_colors, alpha=0.85)
ax2.axhline(0, color="black", linewidth=0.9)
shade_recessions(ax2, rec_for(payems_mom, usrec))
ax2.set_title(
    "Nonfarm Payrolls \u2014 Month-over-Month Change (PAYEMS)", fontsize=13, fontweight="bold"
)
ax2.set_ylabel("Change (Thousands)")
for sp in ["top", "right"]:
    ax2.spines[sp].set_visible(False)

for ax in (ax1, ax2):
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.xaxis.set_major_locator(mdates.YearLocator(10))

fig.tight_layout(pad=2)
fig.savefig(EXAMPLES_DIR / "labor_market.png", bbox_inches="tight")
plt.close(fig)
print(
    f"Latest Unemployment: {unrate.iloc[-1]:.1f}%  |  "
    f"Latest Payrolls Change: {payems_mom.iloc[-1]:+,.0f}K",
    file=sys.stderr,
)

# ---------------------------------------------------------------------------
# Chart 3 — CPI inflation vs Fed Funds Rate
# ---------------------------------------------------------------------------

cpi_yoy = cpi.pct_change(12) * 100
common_idx = cpi_yoy.dropna().index.intersection(fedfunds.index)
cpi_c = cpi_yoy.loc[common_idx]
ff_c = fedfunds.loc[common_idx]
rec_c = usrec.reindex(common_idx, method="ffill").fillna(0)

fig, ax1 = plt.subplots(figsize=(12, 5))
ax1.set_title(
    "CPI Inflation (YoY %) vs Effective Federal Funds Rate", fontsize=13, fontweight="bold"
)
ax1.fill_between(
    cpi_c.index,
    cpi_c.values,
    2,
    alpha=0.2,
    where=(cpi_c.values > 2),
    interpolate=True,
    color="#d62728",
    label="CPI above 2% target",
)
ax1.fill_between(
    cpi_c.index,
    cpi_c.values,
    2,
    alpha=0.2,
    where=(cpi_c.values <= 2),
    interpolate=True,
    color="#2ca02c",
    label="CPI at/below 2% target",
)
ax1.plot(cpi_c.index, cpi_c.values, color="#d62728", linewidth=1.6, label="CPI YoY %")
ax1.axhline(2, color="#666", linewidth=0.9, linestyle="--", label="2% Fed target")
ax1.set_ylabel("CPI YoY %", color="#d62728")
ax1.tick_params(axis="y", labelcolor="#d62728")
ax1.spines["top"].set_visible(False)

ax2 = ax1.twinx()
ax2.plot(ff_c.index, ff_c.values, color="#1f77b4", linewidth=1.5, alpha=0.85, label="Fed Funds %")
ax2.set_ylabel("Fed Funds Rate %", color="#1f77b4")
ax2.tick_params(axis="y", labelcolor="#1f77b4")

shade_recessions(ax1, rec_c)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=9)
ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax1.xaxis.set_major_locator(mdates.YearLocator(5))

fig.tight_layout()
fig.savefig(EXAMPLES_DIR / "cpi_vs_fedfunds.png", bbox_inches="tight")
plt.close(fig)
print(
    f"Latest CPI YoY: {cpi_yoy.iloc[-1]:.1f}%  |  Latest Fed Funds: {fedfunds.iloc[-1]:.2f}%",
    file=sys.stderr,
)

# ---------------------------------------------------------------------------
# Chart 4 — Yield curve
# ---------------------------------------------------------------------------

spread_m = spread.resample("MS").mean()
rec_m = usrec.reindex(spread_m.index, method="ffill").fillna(0)

fig, ax = plt.subplots(figsize=(12, 4))
ax.fill_between(
    spread_m.index,
    spread_m.values,
    0,
    where=(spread_m.values >= 0),
    interpolate=True,
    color="#2ca02c",
    alpha=0.45,
    label="Normal (spread \u2265 0)",
)
ax.fill_between(
    spread_m.index,
    spread_m.values,
    0,
    where=(spread_m.values < 0),
    interpolate=True,
    color="#d62728",
    alpha=0.55,
    label="Inverted (spread < 0)",
)
ax.plot(spread_m.index, spread_m.values, color="#333", linewidth=0.9, alpha=0.7)
ax.axhline(0, color="black", linewidth=1.1)
shade_recessions(ax, rec_m)
ax.set_title(
    "Yield Curve: 10-Year minus 2-Year Treasury Spread (T10Y2Y)",
    fontsize=13,
    fontweight="bold",
)
ax.set_ylabel("Spread (%)")
ax.legend(loc="lower left", fontsize=9)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.xaxis.set_major_locator(mdates.YearLocator(5))
for sp in ["top", "right"]:
    ax.spines[sp].set_visible(False)

fig.tight_layout()
fig.savefig(EXAMPLES_DIR / "yield_curve.png", bbox_inches="tight")
plt.close(fig)
current_spread = spread.iloc[-1]
print(
    f"Latest 10Y-2Y Spread: {current_spread:.2f}%  "
    f"({'inverted' if current_spread < 0 else 'normal'})",
    file=sys.stderr,
)

# ---------------------------------------------------------------------------
# Chart 5 — Housing market
# ---------------------------------------------------------------------------

mortgage_m = mortgage.resample("MS").mean()

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), sharex=False)

ax1.plot(mortgage_m.index, mortgage_m.values, color="#ff7f0e", linewidth=1.4)
shade_recessions(ax1, rec_for(mortgage_m, usrec))
ax1.set_title("30-Year Fixed Mortgage Rate (MORTGAGE30US)", fontsize=13, fontweight="bold")
ax1.set_ylabel("Rate (%)")
for sp in ["top", "right"]:
    ax1.spines[sp].set_visible(False)

ax2.plot(houst.index, houst.values / 1_000, color="#9467bd", linewidth=1.3)
shade_recessions(ax2, rec_for(houst, usrec))
ax2.set_title(
    "Housing Starts: Total New Privately Owned Units (HOUST)", fontsize=13, fontweight="bold"
)
ax2.set_ylabel("Millions of Units (Annual Rate)")
for sp in ["top", "right"]:
    ax2.spines[sp].set_visible(False)

for ax in (ax1, ax2):
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.xaxis.set_major_locator(mdates.YearLocator(10))

fig.tight_layout(pad=2)
fig.savefig(EXAMPLES_DIR / "housing_market.png", bbox_inches="tight")
plt.close(fig)
print(
    f"Latest Mortgage Rate: {mortgage.iloc[-1]:.2f}%  |  "
    f"Latest Housing Starts: {houst.iloc[-1] / 1_000:.2f}M",
    file=sys.stderr,
)

# ---------------------------------------------------------------------------
# Chart 6 — CPI vs PCE inflation comparison
# ---------------------------------------------------------------------------

cpi_yoy_full = cpi.pct_change(12) * 100
pce_yoy_full = pce.pct_change(12) * 100

common_idx = cpi_yoy_full.dropna().index.intersection(pce_yoy_full.dropna().index)
cpi_cp = cpi_yoy_full.loc[common_idx]
pce_cp = pce_yoy_full.loc[common_idx]
rec_cp = usrec.reindex(common_idx, method="ffill").fillna(0)

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(cpi_cp.index, cpi_cp.values, color="#d62728", linewidth=1.5, label="CPI YoY %", zorder=3)
ax.plot(pce_cp.index, pce_cp.values, color="#ff7f0e", linewidth=1.5, label="PCE YoY %", zorder=3)
ax.fill_between(
    common_idx,
    cpi_cp.values,
    pce_cp.values,
    alpha=0.18,
    color="#d62728",
    label="CPI \u2212 PCE gap",
)
ax.axhline(2, color="#555", linewidth=0.9, linestyle="--", label="2% Fed target (PCE)")
ax.axhline(0, color="black", linewidth=0.6)
shade_recessions(ax, rec_cp)
ax.set_title("Inflation Measures: CPI vs PCE Year-over-Year (%)", fontsize=13, fontweight="bold")
ax.set_ylabel("YoY %")
ax.legend(loc="upper left", fontsize=9)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.xaxis.set_major_locator(mdates.YearLocator(5))
for sp in ["top", "right"]:
    ax.spines[sp].set_visible(False)

fig.tight_layout()
fig.savefig(EXAMPLES_DIR / "inflation_comparison.png", bbox_inches="tight")
plt.close(fig)
gap = cpi_cp.iloc[-1] - pce_cp.iloc[-1]
print(
    f"Latest CPI YoY: {cpi_cp.iloc[-1]:.1f}%  |  "
    f"Latest PCE YoY: {pce_cp.iloc[-1]:.1f}%  |  Gap: {gap:+.1f}pp",
    file=sys.stderr,
)

# ---------------------------------------------------------------------------
# Chart 7 — Real federal funds rate
# ---------------------------------------------------------------------------

common_idx = fedfunds.index.intersection(cpi_yoy_full.dropna().index)
ff_r = fedfunds.loc[common_idx]
cpi_r = cpi_yoy_full.loc[common_idx]
real_ff = ff_r - cpi_r
rec_r = usrec.reindex(common_idx, method="ffill").fillna(0)

fig, ax = plt.subplots(figsize=(12, 5))
ax.fill_between(
    real_ff.index,
    real_ff.values,
    0,
    where=(real_ff.values >= 0),
    interpolate=True,
    color="#d62728",
    alpha=0.40,
    label="Restrictive (real rate \u2265 0)",
)
ax.fill_between(
    real_ff.index,
    real_ff.values,
    0,
    where=(real_ff.values < 0),
    interpolate=True,
    color="#2ca02c",
    alpha=0.40,
    label="Accommodative (real rate < 0)",
)
ax.plot(real_ff.index, real_ff.values, color="#333", linewidth=1.0, alpha=0.85)
ax.axhline(0, color="black", linewidth=1.1)
shade_recessions(ax, rec_r)
ax.set_title(
    "Real Federal Funds Rate (Nominal Fed Funds \u2212 CPI YoY)",
    fontsize=13,
    fontweight="bold",
)
ax.set_ylabel("Real Rate (%)")
ax.legend(loc="upper right", fontsize=9)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.xaxis.set_major_locator(mdates.YearLocator(5))
for sp in ["top", "right"]:
    ax.spines[sp].set_visible(False)

fig.tight_layout()
fig.savefig(EXAMPLES_DIR / "real_interest_rate.png", bbox_inches="tight")
plt.close(fig)
print(
    f"Latest Real Fed Funds Rate: {real_ff.iloc[-1]:.2f}%  "
    f"({'restrictive' if real_ff.iloc[-1] >= 0 else 'accommodative'})",
    file=sys.stderr,
)

print(f"\nAll charts written to {EXAMPLES_DIR.relative_to(ROOT)}/", file=sys.stderr)
