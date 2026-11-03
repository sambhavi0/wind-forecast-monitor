import pandas as pd
import pytest

from app import analysis


def ts(s):
    return pd.Timestamp(s, tz="UTC")


def make_forecasts():
    # target: 2026-01-10 12:00. Deadline with cutoff 09:00 is 2026-01-09 09:00.
    return pd.DataFrame(
        {
            "startTime": [ts("2026-01-10 12:00")] * 4,
            "publishTime": [
                ts("2026-01-08 21:00"),
                ts("2026-01-09 09:00"),  # exactly at deadline: allowed
                ts("2026-01-09 12:00"),  # after deadline: must be ignored
                ts("2026-01-10 06:00"),  # after deadline: must be ignored
            ],
            "generation": [1000.0, 1100.0, 5000.0, 9000.0],
        }
    )


def test_picks_latest_forecast_before_deadline():
    chosen = analysis.select_decision_forecast(make_forecasts(), "09:00")
    assert len(chosen) == 1
    assert chosen.loc[0, "generation"] == 1100.0
    assert chosen.loc[0, "publishTime"] == ts("2026-01-09 09:00")


def test_later_cutoff_sees_later_forecast():
    chosen = analysis.select_decision_forecast(make_forecasts(), "12:00")
    assert chosen.loc[0, "generation"] == 5000.0


def test_slot_with_no_forecast_before_deadline_is_dropped():
    fc = make_forecasts().iloc[2:]  # only post-deadline forecasts
    assert analysis.select_decision_forecast(fc, "09:00").empty


def test_invalid_cutoff_rejected():
    with pytest.raises(ValueError):
        analysis.parse_cutoff("25:00")


def make_backtest():
    slots = pd.date_range("2026-01-01", periods=96, freq="30min", tz="UTC")
    actuals = pd.DataFrame({"startTime": slots, "generation": [1000.0] * 96})
    fc = pd.DataFrame(
        {
            "startTime": slots,
            "publishTime": slots.normalize() - pd.Timedelta(hours=18),  # day before, 06:00: before any 09:00 deadline
            "generation": [1100.0] * 96,  # always over-forecasts by 100
        }
    )
    return analysis.build_backtest(actuals, fc, "09:00")


def test_error_sign_and_metrics():
    bt = make_backtest()
    assert (bt["error"] == 100.0).all()  # forecast - actual
    m = analysis.summary_metrics(bt, 0.9)
    assert m["bias_mw"] == 100.0
    assert m["mae_mw"] == 100.0
    assert m["rmse_mw"] == 100.0
    assert m["share_overforecast_pct"] == 100.0
    assert m["overforecast_buffer_mw"] == 100.0


def test_buffer_never_negative():
    bt = make_backtest()
    bt["error"] = -50.0
    assert analysis.summary_metrics(bt, 0.9)["overforecast_buffer_mw"] == 0.0


def test_day_decision_buffer_uses_only_history_before_deadline():
    bt = make_backtest()  # Jan 1-2
    d1 = analysis.day_decision(bt, "2026-01-01", "09:00")
    assert d1["buffer_mw"] is None  # no history before deadline on Dec 31
    d2 = analysis.day_decision(bt, "2026-01-02", "09:00")
    # deadline 2026-01-01 09:00 -> only 18 slots (00:00-08:30) of history: below minimum
    assert d2["history_slots"] == 18
    assert d2["buffer_mw"] is None
    assert len(d2["rows"]) == 48


def test_by_horizon_bins_lead_time():
    slots = pd.date_range("2026-01-02", periods=4, freq="30min", tz="UTC")
    actuals = pd.DataFrame({"startTime": slots, "generation": [1000.0] * 4})
    fc = pd.DataFrame(
        {
            "startTime": list(slots) * 2,
            "publishTime": list(slots - pd.Timedelta(hours=3)) + list(slots - pd.Timedelta(hours=20)),
            "generation": [1010.0] * 4 + [1200.0] * 4,
        }
    )
    out = {r["lead_from_h"]: r for r in analysis.by_horizon(actuals, fc)}
    assert out[0]["mae_mw"] == 10.0
    assert out[18]["mae_mw"] == 200.0
