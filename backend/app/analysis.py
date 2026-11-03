"""Core analysis: which forecast was available at decision time, and how wrong was it?

Conventions
-----------
* All timestamps are UTC (in January, UK local time == UTC).
* error = forecast - actual (MW). Positive = wind came in BELOW forecast, so the
  buyer under-procured thermal power. This is the costly direction, so buffers
  are sized on the positive tail of this error.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

MIN_HISTORY_SLOTS = 48  # one day of half-hours before a buffer is trusted


def parse_cutoff(value: str) -> tuple[int, int]:
    hours, minutes = value.split(":")
    h, m = int(hours), int(minutes)
    if not (0 <= h < 24 and 0 <= m < 60):
        raise ValueError(f"Invalid cutoff time: {value}")
    return h, m


def add_cutoff(df: pd.DataFrame, cutoff: str) -> pd.DataFrame:
    """Decision deadline for each target slot: cutoff time on the day BEFORE delivery."""
    h, m = parse_cutoff(cutoff)
    out = df.copy()
    delivery_day = out["startTime"].dt.normalize()
    out["cutoff"] = delivery_day - pd.Timedelta(days=1) + pd.Timedelta(hours=h, minutes=m)
    return out


def select_decision_forecast(forecasts: pd.DataFrame, cutoff: str) -> pd.DataFrame:
    """For each target slot keep the latest forecast published at or before the deadline.

    Forecasts published after the deadline are ignored: the buyer could not have seen them.
    """
    fc = add_cutoff(forecasts, cutoff)
    fc = fc[fc["publishTime"] <= fc["cutoff"]]
    fc = fc.sort_values(["startTime", "publishTime"])
    return fc.drop_duplicates(subset="startTime", keep="last").reset_index(drop=True)


def build_backtest(actuals: pd.DataFrame, forecasts: pd.DataFrame, cutoff: str) -> pd.DataFrame:
    chosen = select_decision_forecast(forecasts, cutoff)
    df = chosen.rename(columns={"generation": "forecast"}).merge(
        actuals.rename(columns={"generation": "actual"}), on="startTime", how="inner"
    )
    df["error"] = df["forecast"] - df["actual"]
    df["abs_error"] = df["error"].abs()
    df["lead_hours"] = (df["startTime"] - df["publishTime"]).dt.total_seconds() / 3600
    return df.sort_values("startTime").reset_index(drop=True)


def _num(x):
    if x is None:
        return None
    x = float(x)
    return None if np.isnan(x) or np.isinf(x) else round(x, 2)


def summary_metrics(df: pd.DataFrame, quantile: float = 0.9) -> dict:
    if df.empty:
        return {"n": 0}
    err = df["error"]
    mean_actual = df["actual"].mean()
    mae = df["abs_error"].mean()
    return {
        "n": int(len(df)),
        "mean_actual_mw": _num(mean_actual),
        "mean_forecast_mw": _num(df["forecast"].mean()),
        "bias_mw": _num(err.mean()),
        "mae_mw": _num(mae),
        "rmse_mw": _num(np.sqrt((err**2).mean())),
        "mae_pct_of_mean_actual": _num(100 * mae / mean_actual) if mean_actual else None,
        "median_abs_error_mw": _num(df["abs_error"].median()),
        "p90_abs_error_mw": _num(df["abs_error"].quantile(0.90)),
        "p95_abs_error_mw": _num(df["abs_error"].quantile(0.95)),
        "overforecast_quantile": quantile,
        "overforecast_buffer_mw": _num(max(err.quantile(quantile), 0)),
        "share_overforecast_pct": _num(100 * (err > 0).mean()),
    }


def by_hour(df: pd.DataFrame) -> list[dict]:
    g = df.groupby(df["startTime"].dt.hour)
    out = g.agg(mae=("abs_error", "mean"), bias=("error", "mean"), n=("error", "size")).reset_index()
    return [
        {"hour": int(r.startTime), "mae_mw": _num(r.mae), "bias_mw": _num(r.bias), "n": int(r.n)}
        for r in out.itertuples()
    ]


def by_level(df: pd.DataFrame, bins: int = 4) -> list[dict]:
    if len(df) < bins * 10:
        return []
    levels = pd.qcut(df["actual"], q=bins, duplicates="drop")
    out = df.groupby(levels, observed=True).agg(
        mae=("abs_error", "mean"), bias=("error", "mean"), n=("error", "size")
    )
    return [
        {
            "label": f"{int(iv.left)}-{int(iv.right)} MW",
            "mae_mw": _num(r.mae),
            "bias_mw": _num(r.bias),
            "n": int(r.n),
        }
        for iv, r in zip(out.index, out.itertuples())
    ]


def daily(df: pd.DataFrame) -> list[dict]:
    g = df.groupby(df["startTime"].dt.strftime("%Y-%m-%d"))
    out = g.agg(mae=("abs_error", "mean"), bias=("error", "mean"), actual=("actual", "mean")).reset_index()
    return [
        {"date": r.startTime, "mae_mw": _num(r.mae), "bias_mw": _num(r.bias), "mean_actual_mw": _num(r.actual)}
        for r in out.itertuples()
    ]


def by_horizon(actuals: pd.DataFrame, forecasts: pd.DataFrame, bin_hours: int = 6) -> list[dict]:
    """Error against how far ahead the forecast was made (uses every published forecast)."""
    df = forecasts.rename(columns={"generation": "forecast"}).merge(
        actuals.rename(columns={"generation": "actual"}), on="startTime", how="inner"
    )
    df["lead_hours"] = (df["startTime"] - df["publishTime"]).dt.total_seconds() / 3600
    df = df[df["lead_hours"] >= 0].copy()
    if df.empty:
        return []
    df["error"] = df["forecast"] - df["actual"]
    df["bin"] = (df["lead_hours"] // bin_hours * bin_hours).astype(int)
    out = df.groupby("bin").agg(
        mae=("error", lambda s: s.abs().mean()),
        rmse=("error", lambda s: np.sqrt((s**2).mean())),
        bias=("error", "mean"),
        n=("error", "size"),
    ).reset_index()
    return [
        {
            "lead_from_h": int(r.bin),
            "lead_to_h": int(r.bin) + bin_hours,
            "mae_mw": _num(r.mae),
            "rmse_mw": _num(r.rmse),
            "bias_mw": _num(r.bias),
            "n": int(r.n),
        }
        for r in out.itertuples()
    ]


def day_decision(backtest: pd.DataFrame, day: str, cutoff: str, quantile: float = 0.9) -> dict:
    """What the buyer would have seen on day D-1 for delivery day D.

    The safety buffer only uses errors from slots that had already been delivered at the
    decision deadline, so the backtest does not peek into the future.
    """
    day_start = pd.Timestamp(day, tz="UTC").normalize()
    day_end = day_start + pd.Timedelta(days=1)
    rows = backtest[(backtest["startTime"] >= day_start) & (backtest["startTime"] < day_end)]
    h, m = parse_cutoff(cutoff)
    deadline = day_start - pd.Timedelta(days=1) + pd.Timedelta(hours=h, minutes=m)
    if rows.empty:
        return {"date": day, "decision_deadline": deadline.isoformat(), "rows": [],
                "buffer_mw": None, "history_slots": 0}

    history = backtest[backtest["startTime"] < deadline]
    buffer_mw = None
    if len(history) >= MIN_HISTORY_SLOTS:
        buffer_mw = _num(max(history["error"].quantile(quantile), 0))

    out_rows = []
    for r in rows.itertuples():
        conservative = None if buffer_mw is None else _num(max(r.forecast - buffer_mw, 0))
        out_rows.append(
            {
                "startTime": r.startTime.isoformat(),
                "forecast_mw": _num(r.forecast),
                "published_at": r.publishTime.isoformat(),
                "conservative_mw": conservative,
                "actual_mw": _num(r.actual),
                "error_mw": _num(r.error),
            }
        )
    return {
        "date": day,
        "decision_deadline": deadline.isoformat(),
        "buffer_mw": buffer_mw,
        "buffer_quantile": quantile,
        "history_slots": int(len(history)),
        "summary": summary_metrics(rows, quantile),
        "rows": out_rows,
    }


def series(df: pd.DataFrame) -> list[dict]:
    return [
        {
            "startTime": r.startTime.isoformat(),
            "forecast_mw": _num(r.forecast),
            "actual_mw": _num(r.actual),
            "error_mw": _num(r.error),
        }
        for r in df.itertuples()
    ]
