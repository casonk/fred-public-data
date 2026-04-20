import argparse
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import requests

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
VIZ_DIR = ROOT / "viz"
CATALOG_PATH = ROOT / "config" / "series_catalog.toml"

FRED_API_BASE = "https://api.stlouisfed.org/fred"


@dataclass
class SeriesSpec:
    id: str
    title: str
    category: str
    frequency: str = "m"
    units: str = "lin"


@dataclass
class DownloadStats:
    downloaded: int = 0
    skipped: int = 0
    failed: int = 0
    empty: int = 0
    series: list[str] = field(default_factory=list)


def load_catalog() -> list[SeriesSpec]:
    with CATALOG_PATH.open("rb") as fh:
        raw = tomllib.load(fh)
    defaults = raw.get("defaults", {})
    return [
        SeriesSpec(
            id=entry["id"],
            title=entry.get("title", entry["id"]),
            category=entry.get("category", "misc"),
            frequency=entry.get("frequency", defaults.get("frequency", "m")),
            units=entry.get("units", defaults.get("units", "lin")),
        )
        for entry in raw.get("series", [])
    ]


def ensure_dirs() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    VIZ_DIR.mkdir(exist_ok=True)


def api_key() -> str:
    key = os.environ.get("FRED_API_KEY", "").strip()
    if not key:
        raise SystemExit(
            "FRED_API_KEY environment variable is not set.\n"
            "Register for a free key at https://fred.stlouisfed.org/docs/api/api_key.html"
        )
    return key


def fetch_observations(
    session: requests.Session,
    spec: SeriesSpec,
    key: str,
) -> pd.DataFrame | None:
    url = f"{FRED_API_BASE}/series/observations"
    params = {
        "series_id": spec.id,
        "api_key": key,
        "file_type": "json",
        "frequency": spec.frequency,
        "units": spec.units,
    }
    try:
        resp = session.get(url, params=params, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"  [error] {spec.id}: {exc}")
        return None

    payload = resp.json()
    observations = payload.get("observations", [])
    if not observations:
        return None

    df = pd.DataFrame(observations)[["date", "value"]]
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna(subset=["value"]).reset_index(drop=True)


def download_all(
    catalog: list[SeriesSpec],
    session: requests.Session,
    key: str,
    resume: bool = False,
) -> DownloadStats:
    stats = DownloadStats()
    total = len(catalog)
    for idx, spec in enumerate(catalog, start=1):
        category_dir = DATA_DIR / spec.category
        category_dir.mkdir(parents=True, exist_ok=True)
        target = category_dir / f"{spec.id}.csv"

        print(f"[{idx}/{total}] {spec.id} — {spec.title}")

        if resume and target.exists() and target.stat().st_size > 0:
            stats.skipped += 1
            print(f"  skipped (exists)")
            stats.series.append(spec.id)
            continue

        df = fetch_observations(session, spec, key)
        if df is None or df.empty:
            stats.empty += 1
            print(f"  empty or unavailable")
            continue

        df.to_csv(target, index=False)
        stats.downloaded += 1
        stats.series.append(spec.id)
        print(f"  {len(df)} observations → {target.relative_to(ROOT)}")

    return stats


def plot_series(spec: SeriesSpec) -> None:
    import matplotlib.pyplot as plt

    category_dir = DATA_DIR / spec.category
    src = category_dir / f"{spec.id}.csv"
    if not src.exists():
        return

    df = pd.read_csv(src, parse_dates=["date"])
    df = df.dropna(subset=["value"])
    if df.empty:
        return

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(df["date"], df["value"], linewidth=1.2)
    ax.set_title(spec.title)
    ax.set_xlabel("Date")
    ax.set_ylabel(f"Value ({spec.units})")
    fig.tight_layout()

    out_dir = VIZ_DIR / spec.category
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / f"{spec.id}.png", dpi=120)
    plt.close(fig)


def plot_all(catalog: list[SeriesSpec]) -> None:
    total = len(catalog)
    for idx, spec in enumerate(catalog, start=1):
        print(f"  [{idx}/{total}] plotting {spec.id}")
        try:
            plot_series(spec)
        except Exception as exc:
            print(f"    [warn] {spec.id}: {exc}")


def latest_dates(catalog: list[SeriesSpec]) -> None:
    for spec in catalog:
        src = DATA_DIR / spec.category / f"{spec.id}.csv"
        if not src.exists():
            continue
        try:
            df = pd.read_csv(src, parse_dates=["date"])
            latest = df["date"].max()
            print(f"  [latest] {spec.id}: {latest.date()}")
        except Exception:
            pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh FRED series data and visualizations.")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip series whose CSV already exists and is non-empty.",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip downloading; regenerate plots from existing data/ CSVs only.",
    )
    parser.add_argument(
        "--skip-viz",
        action="store_true",
        help="Skip plot generation; only download data.",
    )
    args = parser.parse_args()

    ensure_dirs()
    catalog = load_catalog()
    print(f"[catalog] {len(catalog)} series loaded from {CATALOG_PATH.relative_to(ROOT)}")

    if not args.skip_download:
        key = api_key()
        with requests.Session() as session:
            stats = download_all(catalog, session, key, resume=args.resume)
        print(
            f"[summary] downloaded={stats.downloaded} skipped={stats.skipped} "
            f"empty={stats.empty} failed={stats.failed}"
        )
    else:
        print("[summary] --skip-download: using existing data/")

    if not args.skip_viz:
        print("[viz] generating plots …")
        plot_all(catalog)
        print("[viz] done")

    latest_dates(catalog)


if __name__ == "__main__":
    main()
