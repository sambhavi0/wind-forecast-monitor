"""SYNTHETIC data for local testing only. Never submit results built from this.

Usage: python scripts/make_sample_data.py --out /tmp/sample_data
Then:  DATA_DIR=/tmp/sample_data uvicorn app.main:app
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="/tmp/sample_data")
out = Path(ap.parse_args().out)
out.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(7)
slots = pd.date_range("2026-01-01", "2026-01-31 23:30", freq="30min", tz="UTC")
x = np.zeros(len(slots))
for i in range(1, len(x)):  # slow AR(1) "weather"
    x[i] = 0.995 * x[i - 1] + rng.normal(0, 0.06)
actual = np.clip(8000 + 5500 * x / x.std() + 800 * np.sin(np.arange(len(x)) / 48 * 2 * np.pi), 200, 20000)
actuals = pd.DataFrame({"startTime": slots, "generation": actual.round(0)})

rows = []
for pub in pd.date_range("2025-12-30", "2026-01-31 12:00", freq="3h", tz="UTC"):
    for t, a in zip(slots, actual):
        lead = (t - pub).total_seconds() / 3600
        if 0 <= lead <= 48:
            noise = rng.normal(0.02 * a, (150 + 55 * lead) )
            rows.append((t, pub, max(a + noise, 0)))
forecasts = pd.DataFrame(rows, columns=["startTime", "publishTime", "generation"]).round(0)

actuals.to_csv(out / "wind_actuals.csv", index=False)
forecasts.to_csv(out / "wind_forecasts.csv", index=False)
print(len(actuals), len(forecasts))
