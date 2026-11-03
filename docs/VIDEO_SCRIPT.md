# Video script (10 minutes max)

Record the screen with your voice. Speak plainly. Fill the [..] with your real numbers.

## Part 1: Customer pitch (about 4:30)

**0:00 Problem (30s).** "You buy power one day ahead. Wind output is uncertain, and what you don't buy from wind you must buy from thermal plants. Two questions decide how much: what is the forecast at the moment you decide, and how wrong is it usually?"

**0:30 Decision tab (90s).** Pick a day with a visible miss. "For delivery on [date], here is the forecast you had at [deadline]. Each number is tagged with when it was published, so every figure is traceable." Point to the big margin figure: "Historically the forecast ran too high by more than [X] MW only 10% of the time. Plan for this amber line, or buy [X] MW extra, and you are covered nine times in ten." Show actual wind afterwards: "Here is what happened."

**2:00 Accuracy tab (90s).** "Across January the average miss is [MAE] MW, [pct]% of average wind. Bias is [bias] MW, so forecasts ran [high/low]. On the worst days the miss reached [..]." Show the daily bar chart and name the worst day.

**3:30 Patterns tab (45s).** "Error grows with lead time: [..] MW at 0-6 hours ahead versus [..] MW at 24-30 hours. And it is worse at [time of day / wind level]."

**4:15 Settings and close (15s).** Change the deadline once and show the numbers move. "Every assumption is visible on the left. Past error tells you how much margin to buy tomorrow."

## Part 2: Tech lead review (about 5 min)

**4:30 Architecture (60s).** React frontend (Vite, Recharts), FastAPI backend, pandas analysis. Data is fetched once by `scripts/fetch_data.py` and stored as CSV, so the app never depends on Elexon being up. Docker compose runs both; Vercel hosts the frontend, Render the API.

**5:30 The core logic (90s).** Open `analysis.py`. Walk through `select_decision_forecast`: compute deadline per slot, drop forecasts published after it, keep the latest. "This is the line that prevents leakage: using the newest forecast would flatter the accuracy." Then `day_decision`: the margin uses only slots delivered before the deadline.

**7:00 Metrics and design choices (60s).** Error sign convention and why: over-forecast is the costly side. MAE, RMSE, bias, percentiles. Why a percentile margin rather than a mean error.

**8:00 Tests and practices (45s).** Run pytest. Mention the leakage test, the sign test, and that analysis is pure functions separate from the API.

**8:45 Limits and next steps (45s).** One month of data; flat margin; no prices. Next: scale margin to conditions, probabilistic forecasts, live ingestion on a schedule, cost-weighted evaluation.

**9:30 Wrap.** Point to the README and thank them.
