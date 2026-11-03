from __future__ import annotations

import os
from functools import lru_cache

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import analysis, data

DEFAULT_CUTOFF = os.environ.get("DEFAULT_CUTOFF_UTC", "09:00")

app = FastAPI(title="Wind Forecast Monitor API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["GET"],
    allow_headers=["*"],
)


@lru_cache(maxsize=32)
def _backtest(cutoff: str) -> pd.DataFrame:
    actuals, forecasts = data.load()
    return analysis.build_backtest(actuals, forecasts, cutoff)


def _bt(cutoff: str) -> pd.DataFrame:
    try:
        analysis.parse_cutoff(cutoff)
        return _backtest(cutoff)
    except data.DataMissing as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


def _range(df: pd.DataFrame, start: str | None, end: str | None) -> pd.DataFrame:
    if start:
        df = df[df["startTime"] >= pd.Timestamp(start, tz="UTC")]
    if end:
        df = df[df["startTime"] < pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)]
    return df


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/meta")
def meta(cutoff: str = DEFAULT_CUTOFF):
    df = _bt(cutoff)
    return {
        "default_cutoff_utc": DEFAULT_CUTOFF,
        "first_day": df["startTime"].min().strftime("%Y-%m-%d") if len(df) else None,
        "last_day": df["startTime"].max().strftime("%Y-%m-%d") if len(df) else None,
        "slots": int(len(df)),
        "timezone": "UTC (equals UK local time in January)",
        "sources": {
            "actuals": "Elexon BMRS FUELHH, fuelType=WIND",
            "forecasts": "Elexon BMRS WINDFOR",
        },
    }


@app.get("/api/decision")
def decision(
    date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
    cutoff: str = DEFAULT_CUTOFF,
    quantile: float = Query(0.9, ge=0.5, le=0.99),
):
    return analysis.day_decision(_bt(cutoff), date, cutoff, quantile)


@app.get("/api/series")
def series(start: str | None = None, end: str | None = None, cutoff: str = DEFAULT_CUTOFF):
    return analysis.series(_range(_bt(cutoff), start, end))


@app.get("/api/metrics")
def metrics(
    start: str | None = None,
    end: str | None = None,
    cutoff: str = DEFAULT_CUTOFF,
    quantile: float = Query(0.9, ge=0.5, le=0.99),
):
    df = _range(_bt(cutoff), start, end)
    return {"summary": analysis.summary_metrics(df, quantile), "daily": analysis.daily(df)}


@app.get("/api/patterns")
def patterns(start: str | None = None, end: str | None = None, cutoff: str = DEFAULT_CUTOFF):
    df = _range(_bt(cutoff), start, end)
    try:
        actuals, forecasts = data.load()
    except data.DataMissing as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {
        "by_hour": analysis.by_hour(df),
        "by_level": analysis.by_level(df),
        "by_horizon": analysis.by_horizon(_range(actuals, start, end), _range(forecasts, start, end)),
    }
