"""Loads the pre-fetched Elexon data (see scripts/fetch_data.py). No live API calls at runtime."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import pandas as pd

DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).resolve().parent.parent / "data"))


class DataMissing(RuntimeError):
    pass


def expand_hourly_to_half_hours(forecasts: pd.DataFrame) -> pd.DataFrame:
    """WINDFOR is published hourly, actuals are half-hourly.

    If every forecast target is on the hour, apply each hourly value to both half-hours
    of that hour (the :00 and :30 slots), so all 1,488 January slots can be compared.
    Forecasts that already include :30 targets are left untouched.
    """
    if (forecasts["startTime"].dt.minute == 30).any():
        return forecasts
    second_half = forecasts.copy()
    second_half["startTime"] = second_half["startTime"] + pd.Timedelta(minutes=30)
    return pd.concat([forecasts, second_half], ignore_index=True)


@lru_cache(maxsize=1)
def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    a_path, f_path = DATA_DIR / "wind_actuals.csv", DATA_DIR / "wind_forecasts.csv"
    if not a_path.exists() or not f_path.exists():
        raise DataMissing(
            f"Data files not found in {DATA_DIR}. Run `python scripts/fetch_data.py` first."
        )
    actuals = pd.read_csv(a_path)
    forecasts = pd.read_csv(f_path)
    actuals["startTime"] = pd.to_datetime(actuals["startTime"], utc=True)
    forecasts["startTime"] = pd.to_datetime(forecasts["startTime"], utc=True)
    forecasts["publishTime"] = pd.to_datetime(forecasts["publishTime"], utc=True)
    forecasts = expand_hourly_to_half_hours(forecasts)
    actuals = actuals.drop_duplicates("startTime").sort_values("startTime")
    forecasts = forecasts.drop_duplicates(["startTime", "publishTime"]).sort_values(
        ["startTime", "publishTime"]
    )
    return actuals.reset_index(drop=True), forecasts.reset_index(drop=True) 