# Do these in order

1. **Get real data.** `cd backend && pip install -r requirements.txt && python scripts/fetch_data.py`
   - Expect about 1,488 actual rows. If the script errors on a column or parameter name, open the Elexon API docs links from the task and adjust the field names in `fetch_data.py` (this script was written without live API access and is the one untested part).
2. **Check the numbers.** `python -m pytest -q`, then run the app and open the Accuracy tab. If MAE or bias looks absurd, check units and the join before recording.
3. **Confirm the decision deadline.** Look up the GB day-ahead auction gate closure and set `DEFAULT_CUTOFF_UTC` (backend/app/main.py) and the default in frontend/src/App.jsx to match. Update the README assumption.
4. **Run locally** with `docker compose up --build`. Click every tab and change the deadline once.
5. **Create the GitHub repo** with a random name (e.g. `kjhwr`), public. Push everything including `backend/data/*.csv`. No personal name in the repo name, README or commit author if you want it anonymous.
6. **Deploy backend** on Render, then **frontend** on Vercel (see README). Set `VITE_API_URL`, then `CORS_ORIGINS`.
7. **Fill the three links in README** (live app, API, video) and push again.
8. **Record the video** using `docs/VIDEO_SCRIPT.md`. Max 10 minutes. Upload to YouTube as **Unlisted**.
9. **Open every URL in an incognito window**: repo, live app, video. Load the live app twice, since free hosting sleeps.
10. **Submit the form.**

Before recording, fill in the real numbers in the script (marked [..]) from your Accuracy tab.
