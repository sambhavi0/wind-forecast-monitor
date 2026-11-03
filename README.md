# Wind Forecast Monitor

A web app for a GB energy utility's day-ahead purchasing team. It answers two questions about national wind generation (Elexon BMRS data, January 2026 delivery days):

1. **What was the latest wind forecast available when the day-ahead purchase decision had to be made?**
2. **How accurate are those forecasts, and how large a safety margin does the error justify?**

**Live app:** https://wind-forecast-monitor-swart.vercel.app
**API:** https://wind-forecast-monitor-xnfd.onrender.com
**Demo video:** `<ADD UNLISTED YOUTUBE URL HERE>`

> **AI tools disclosure:** This project was built with assistance from Claude (Anthropic) for code generation and drafting. I reviewed, ran and tested the result.

## Key idea

A forecast for a half-hour can be published many times. The buyer decides on the day before delivery, so for each half-hour the app uses **the latest forecast published at or before a decision deadline** (default 09:00 UTC on the day before, configurable in the UI). Forecasts published after the deadline are ignored, because the buyer could not have seen them.

Error is `forecast - actual`. Positive error means wind came in below forecast, which is the costly direction because extra thermal power must be bought. The safety margin is a percentile of that positive error, computed only from half-hours already delivered before the deadline, so the backtest never uses future information.

## Files and directories

```
backend/
  app/analysis.py        Decision-time forecast selection, metrics, margin logic (pure pandas)
  app/data.py            Loads the prefetched CSVs
  app/main.py            FastAPI endpoints
  scripts/fetch_data.py  Downloads Jan 2026 data from Elexon into backend/data/
  scripts/make_sample_data.py  SYNTHETIC data for local testing only
  tests/test_analysis.py Unit tests (leakage, sign convention, metrics, horizon bins)
  data/                  wind_actuals.csv, wind_forecasts.csv (produced by fetch_data.py)
  Dockerfile
frontend/
  src/App.jsx            Layout, settings panel, tabs
  src/views/             Decision, Accuracy, Patterns, Assumptions
  src/api.js             Fetch hook
  Dockerfile, nginx.conf, vercel.json
docker-compose.yml       Runs both services locally
render.yaml              Backend deployment config (Render)
docs/                    Video script and submission checklist
```

## Start the application

### 1. Get the data (once)

```bash
cd backend
pip install -r requirements.txt
python scripts/fetch_data.py        # writes backend/data/wind_actuals.csv and wind_forecasts.csv
```

The app never calls Elexon at runtime; it reads these files. Commit them so deployments work.

### 2a. With Docker

```bash
docker compose up --build
# app: http://localhost:3000    api docs: http://localhost:8000/docs
```

### 2b. Without Docker

```bash
# terminal 1
cd backend && uvicorn app.main:app --reload
# terminal 2
cd frontend && npm install && npm run dev      # http://localhost:5173
```

### Tests

```bash
cd backend && python -m pytest -q
```

## API

| Endpoint | Purpose |
|---|---|
| `GET /api/decision?date=&cutoff=&quantile=` | Forecast at the deadline for one delivery day, with safety margin |
| `GET /api/metrics?start=&end=&cutoff=&quantile=` | Summary error metrics and daily error |
| `GET /api/series?start=&end=&cutoff=` | Forecast vs actual time series |
| `GET /api/patterns?start=&end=&cutoff=` | Error by horizon, hour of day, wind level |
| `GET /api/meta`, `GET /api/health` | Data range, health check |

## Deployment

- **Backend (Render, Docker):** new Web Service from this repo using `render.yaml`. Note the free tier sleeps; open the URL before demoing.
- **Frontend (Vercel):** import the repo, set root directory to `frontend`, and add environment variable `VITE_API_URL` = the Render URL (no trailing slash). Then set `CORS_ORIGINS` on Render to the Vercel URL.

## Assumptions and limitations

- Decision deadline defaults to 09:00 UTC on the day before delivery (an assumption; adjustable).
- UTC throughout, which equals UK local time in January.
- Forecasts kept only when made 0-48 hours before the target half-hour.
- One month is a small sample; the margin is a single number per day, not scaled to conditions; no price data is used.
