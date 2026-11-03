import React from "react";
import {
  CartesianGrid, ComposedChart, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { useApi } from "../api.js";
import { COLORS, Section, Stat, Status } from "../components/Bits.jsx";
import { dateTime, hhmm, mw, num } from "../format.js";

export default function Decision({ date, setDate, bounds, cutoff, quantile }) {
  const state = useApi("/api/decision", { date, cutoff, quantile });
  const d = state.data;
  const rows = (d?.rows || []).map((r) => ({ ...r, t: new Date(r.startTime).getTime() }));
  const hasBuffer = d?.buffer_mw !== null && d?.buffer_mw !== undefined;
  const pct = Math.round(quantile * 100);

  return (
    <>
      <div className="toolbar">
        <label>
          Delivery day
          <input
            type="date"
            value={date}
            min={bounds?.first_day}
            max={bounds?.last_day}
            onChange={(e) => e.target.value && setDate(e.target.value)}
          />
        </label>
        {d?.decision_deadline && (
          <p className="inline-note">
            Purchase decision made by <strong>{dateTime(d.decision_deadline)}</strong>, the day before.
          </p>
        )}
      </div>

      <Status state={state}>
        {d && d.rows.length === 0 && <p className="status">No data for this day.</p>}
        {d && d.rows.length > 0 && (
          <>
            <div className="lead">
              {hasBuffer ? (
                <>
                  <div className="lead-number">{num(d.buffer_mw)} MW</div>
                  <p>
                    Safety margin for this day. In past delivered half-hours, the forecast was too high by more
                    than this only {100 - pct}% of the time. Buy this much extra thermal power, or plan for the
                    amber line instead of the blue one.
                  </p>
                </>
              ) : (
                <p>
                  Not enough delivered history before this deadline to size a safety margin (needs at least one
                  full day). The forecast is shown without a margin.
                </p>
              )}
            </div>

            <div className="stats">
              <Stat label="Forecast wind, daily average" value={mw(d.summary.mean_forecast_mw)} note="Latest forecast before the deadline" />
              <Stat label="Wind after safety margin" value={hasBuffer ? mw(Math.max(d.summary.mean_forecast_mw - d.buffer_mw, 0)) : "–"} note={`Margin from history at the ${pct}th percentile`} />
              <Stat label="Actual wind, daily average" value={mw(d.summary.mean_actual_mw)} note="Shown for review only; unknown at decision time" />
              <Stat label="Forecast error, daily average" value={mw(d.summary.bias_mw)} note="Positive means wind came in below forecast" />
            </div>

            <Section title="Forecast available at the deadline" hint="Each point is the latest forecast published before the deadline. Hover to see the values.">
              <div className="chart tall">
                <ResponsiveContainer>
                  <ComposedChart data={rows} margin={{ top: 8, right: 16, bottom: 4, left: 8 }}>
                    <CartesianGrid stroke={COLORS.grid} vertical={false} />
                    <XAxis dataKey="t" type="number" scale="time" domain={["dataMin", "dataMax"]} tickFormatter={(t) => hhmm(new Date(t).toISOString())} minTickGap={32} />
                    <YAxis tickFormatter={(v) => num(v)} width={64} label={{ value: "MW", angle: -90, position: "insideLeft", offset: 8 }} />
                    <Tooltip labelFormatter={(t) => hhmm(new Date(t).toISOString()) + " UTC"} formatter={(v, n) => [mw(v), n]} />
                    <Legend />
                    <Line name="Forecast" dataKey="forecast_mw" stroke={COLORS.forecast} strokeWidth={2} dot={false} isAnimationActive={false} />
                    {hasBuffer && <Line name="Forecast minus safety margin" dataKey="conservative_mw" stroke={COLORS.conservative} strokeWidth={2} strokeDasharray="6 4" dot={false} isAnimationActive={false} />}
                    <Line name="Actual (review only)" dataKey="actual_mw" stroke={COLORS.actual} strokeWidth={1.5} dot={false} isAnimationActive={false} />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </Section>

            <Section title="Half-hourly detail" hint="The 'Forecast made at' column shows which forecast version each number came from.">
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Time (UTC)</th>
                      <th className="r">Forecast (MW)</th>
                      <th>Forecast made at</th>
                      <th className="r">After margin (MW)</th>
                      <th className="r">Actual (MW)</th>
                      <th className="r">Error (MW)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {d.rows.map((r) => (
                      <tr key={r.startTime}>
                        <td>{hhmm(r.startTime)}</td>
                        <td className="r">{num(r.forecast_mw)}</td>
                        <td>{dateTime(r.published_at)}</td>
                        <td className="r">{num(r.conservative_mw)}</td>
                        <td className="r">{num(r.actual_mw)}</td>
                        <td className={`r ${r.error_mw > 0 ? "pos" : ""}`}>{num(r.error_mw)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Section>
          </>
        )}
      </Status>
    </>
  );
}
