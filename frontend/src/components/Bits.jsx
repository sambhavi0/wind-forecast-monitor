import React from "react";

export function Stat({ label, value, note }) {
  return (
    <div className="stat">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      {note && <div className="stat-note">{note}</div>}
    </div>
  );
}

export function Section({ title, hint, children }) {
  return (
    <section className="section">
      <h2>{title}</h2>
      {hint && <p className="hint">{hint}</p>}
      {children}
    </section>
  );
}

export function Status({ state, children }) {
  if (state.loading && !state.data) return <p className="status">Loading…</p>;
  if (state.error)
    return (
      <p className="status error" role="alert">
        Could not load data: {state.error.message}
      </p>
    );
  return children;
}

export const COLORS = {
  forecast: "#1f5fbf",
  actual: "#172b36",
  conservative: "#c77700",
  bias: "#b42318",
  grid: "#d9e0e4",
};
