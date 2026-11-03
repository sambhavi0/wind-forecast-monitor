"""Download January 2026 wind data from Elexon BMRS and save it as CSV.

Usage:  python scripts/fetch_data.py [--out data]

Actuals   : FUELHH stream, fuelType=WIND, settlement dates 2026-01-01..2026-01-31
Forecasts : WINDFOR stream, published 2025-12-30..2026-01-31, kept only if the target
            slot is in January 2026 and the forecast was made 0-48h before the slot.
The runtime app reads these CSVs; it never calls Elexon.
"""
from __future__ import annotations

import argparse
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

BASE = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
TARGET_START = pd.Timestamp("2026-01-01", tz="UTC")
TARGET_END = pd.Timestamp("2026-02-01", tz="UTC")  # exclusive
MAX_LEAD_HOURS = 48


def get_json(url: str, params: dict, retries: int = 5) -> list[dict]:
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, timeout=60, headers={"Accept": "application/json"})
            if r.status_code == 200:
                payload = r.json()
                return payload["data"] if isinstance(payload, dict) and "data" in payload else payload
            print(f"  HTTP {r.status_code} for {r.url}", file=sys.stderr)
        except requests.RequestException as e:
            print(f"  request error: {e}", file=sys.stderr)
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Failed after {retries} attempts: {url} {params}")


def daterange_chunks(start: date, end: date, days: int):
    cur = start
    while cur <= end:
        nxt = min(cur + timedelta(days=days - 1), end)
        yield cur, nxt
        cur = nxt + timedelta(days=1)


def fetch_actuals() -> pd.DataFrame:
    rows: list[dict] = []
    for a, b in daterange_chunks(date(2026, 1, 1), date(2026, 1, 31), 7):
        print(f"FUELHH {a}..{b}")
        rows += get_json(
            f"{BASE}/FUELHH/stream",
            {"settlementDateFrom": a.isoformat(), "settlementDateTo": b.isoformat(), "fuelType": "WIND"},
        )
    df = pd.DataFrame(rows)
    df = df[df["fuelType"] == "WIND"]
    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    df = df[(df["startTime"] >= TARGET_START) & (df["startTime"] < TARGET_END)]
    return (
        df[["startTime", "generation"]]
        .drop_duplicates("startTime")
        .sort_values("startTime")
        .reset_index(drop=True)
    )


def fetch_forecasts() -> pd.DataFrame:
    rows: list[dict] = []
    for a, b in daterange_chunks(date(2025, 12, 30), date(2026, 1, 31), 1):
        start = datetime(a.year, a.month, a.day, tzinfo=timezone.utc)
        end = start + timedelta(days=1)
        print(f"WINDFOR published {a}")
        rows += get_json(
            f"{BASE}/WINDFOR/stream",
            {
                "publishDateTimeFrom": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "publishDateTimeTo": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
        )
    df = pd.DataFrame(rows)
    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    df["publishTime"] = pd.to_datetime(df["publishTime"], utc=True)
    df = df[(df["startTime"] >= TARGET_START) & (df["startTime"] < TARGET_END)]
    lead = (df["startTime"] - df["publishTime"]).dt.total_seconds() / 3600
    df = df[(lead >= 0) & (lead <= MAX_LEAD_HOURS)]
    return (
        df[["startTime", "publishTime", "generation"]]
        .drop_duplicates(["startTime", "publishTime"])
        .sort_values(["startTime", "publishTime"])
        .reset_index(drop=True)
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "data"))
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    actuals = fetch_actuals()
    forecasts = fetch_forecasts()
    actuals.to_csv(out / "wind_actuals.csv", index=False)
    forecasts.to_csv(out / "wind_forecasts.csv", index=False)

    print(f"\nactuals   : {len(actuals)} rows, {actuals.startTime.min()} -> {actuals.startTime.max()}")
    print(f"forecasts : {len(forecasts)} rows, {forecasts.publishTime.min()} -> {forecasts.publishTime.max()}")
    print(f"expected January half-hour slots: 1488, actual rows: {len(actuals)}")


if __name__ == "__main__":
    main()
