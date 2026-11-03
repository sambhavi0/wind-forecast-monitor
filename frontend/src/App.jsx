import React, { useEffect, useState } from "react";
import { useApi } from "./api.js";
import Accuracy from "./views/Accuracy.jsx";
import Assumptions from "./views/Assumptions.jsx";
import Decision from "./views/Decision.jsx";
import Patterns from "./views/Patterns.jsx";

const TABS = [
  { id: "decision", label: "Decision" },
  { id: "accuracy", label: "Accuracy" },
  { id: "patterns", label: "Patterns" },
  { id: "assumptions", label: "Assumptions" },
];

function addDays(iso, n) {
  const d = new Date(iso + "T00:00:00Z");
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
}

export default function App() {
  const [tab, setTab] = useState("decision");
  const [cutoff, setCutoff] = useState("09:00");
  const [quantile, setQuantile] = useState(0.9);
  const [date, setDate] = useState("");
  const [range, setRange] = useState({ start: "", end: "" });

  const metaState = useApi("/api/meta", {});
  const meta = metaState.data;

  useEffect(() => {
    if (!meta?.first_day) return;
    setDate((d) => d || addDays(meta.first_day, 14));
    setRange((r) => (r.start ? r : { start: meta.first_day, end: meta.last_day }));
  }, [meta]);

  return (
    <div className="app">
      <aside className="side">
        <h1>Wind Forecast Monitor</h1>
        <p className="side-sub">Day-ahead purchasing, Great Britain</p>

        <div className="side-block">
          <h2>Decision settings</h2>
          <label>
            Decision deadline (UTC, day before delivery)
            <input type="time" value={cutoff} onChange={(e) => e.target.value && setCutoff(e.target.value)} />
          </label>
          <label>
            Safety margin percentile
            <select value={quantile} onChange={(e) => setQuantile(Number(e.target.value))}>
              <option value={0.8}>80th</option>
              <option value={0.9}>90th</option>
              <option value={0.95}>95th</option>
            </select>
          </label>
          <p className="side-note">
            Only forecasts published before the deadline are used. A later deadline gives a newer, usually more
            accurate forecast.
          </p>
        </div>

        <div className="side-block">
          <h2>Review period</h2>
          <label>
            From
            <input type="date" value={range.start} min={meta?.first_day} max={range.end || meta?.last_day} onChange={(e) => e.target.value && setRange((r) => ({ ...r, start: e.target.value }))} />
          </label>
          <label>
            To
            <input type="date" value={range.end} min={range.start || meta?.first_day} max={meta?.last_day} onChange={(e) => e.target.value && setRange((r) => ({ ...r, end: e.target.value }))} />
          </label>
          <p className="side-note">Applies to the Accuracy and Patterns tabs.</p>
        </div>

        <p className="side-foot">Source: Elexon BMRS, national wind, January 2026.</p>
      </aside>

      <main className="main">
        <nav className="tabs" role="tablist">
          {TABS.map((t) => (
            <button key={t.id} role="tab" aria-selected={tab === t.id} className={tab === t.id ? "active" : ""} onClick={() => setTab(t.id)}>
              {t.label}
            </button>
          ))}
        </nav>

        {metaState.error && (
          <p className="status error" role="alert">
            Could not reach the data service: {metaState.error.message}
          </p>
        )}

        {meta && date && range.start && (
          <div className="panel">
            {tab === "decision" && <Decision date={date} setDate={setDate} bounds={meta} cutoff={cutoff} quantile={quantile} />}
            {tab === "accuracy" && <Accuracy range={range} cutoff={cutoff} quantile={quantile} />}
            {tab === "patterns" && <Patterns range={range} cutoff={cutoff} />}
            {tab === "assumptions" && <Assumptions meta={meta} cutoff={cutoff} quantile={quantile} />}
          </div>
        )}
        {!meta && !metaState.error && <p className="status">Loading…</p>}
      </main>
    </div>
  );
}
