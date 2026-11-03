import React from "react";
import {
  Bar, BarChart, CartesianGrid, ComposedChart, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { useApi } from "../api.js";
import { COLORS, Section, Stat, Status } from "../components/Bits.jsx";
import { dateTime, dayMonth, mw, num } from "../format.js";

export default function Accuracy({ range, cutoff, quantile }) {
  const params = { start: range.start, end: range.end, cutoff, quantile };
  const metrics = useApi("/api/metrics", params);
  const series = useApi("/api/series", { start: range.start, end: range.end, cutoff });
  const s = metrics.data?.summary;
  const pct = Math.round(quantile * 100);
  const points = (series.data || []).map((r) => ({ ...r, t: new Date(r.startTime).getTime() }));

  return (
    <>
      <Status state={metrics}>
        {s && s.n > 0 && (
          <div className="stats">
            <Stat label="Average miss (MAE)" value={mw(s.mae_mw)} note={`${num(s.mae_pct_of_mean_actual, 1)}% of average actual wind`} />
            <Stat label="Typical large miss (RMSE)" value={mw(s.rmse_mw)} note="Penalises big misses more" />
            <Stat label="Bias" value={mw(s.bias_mw)} note="Positive means forecasts ran high" />
            <Stat label={`Safety margin (${pct}th percentile)`} value={mw(s.overforecast_buffer_mw)} note={`Forecast too high by more than this in ${100 - pct}% of half-hours`} />
            <Stat label="Median miss" value={mw(s.median_abs_error_mw)} />
            <Stat label="90th percentile miss" value={mw(s.p90_abs_error_mw)} note={`95th: ${mw(s.p95_abs_error_mw)}`} />
            <Stat label="Forecast too high" value={`${num(s.share_overforecast_pct, 1)}%`} note="Share of half-hours" />
            <Stat label="Half-hours compared" value={num(s.n)} />
          </div>
        )}
      </Status>

      <Section title="Forecast against actual" hint="The forecast shown for each half-hour is the one available at the decision deadline.">
        <Status state={series}>
          <div className="chart tall">
            <ResponsiveContainer>
              <ComposedChart data={points} margin={{ top: 8, right: 16, bottom: 4, left: 8 }}>
                <CartesianGrid stroke={COLORS.grid} vertical={false} />
                <XAxis dataKey="t" type="number" scale="time" domain={["dataMin", "dataMax"]} tickFormatter={dayMonth} minTickGap={40} />
                <YAxis tickFormatter={(v) => num(v)} width={64} label={{ value: "MW", angle: -90, position: "insideLeft", offset: 8 }} />
                <Tooltip labelFormatter={(t) => dateTime(new Date(t).toISOString())} formatter={(v, n) => [mw(v), n]} />
                <Legend />
                <Line name="Actual" dataKey="actual_mw" stroke={COLORS.actual} strokeWidth={1.5} dot={false} isAnimationActive={false} />
                <Line name="Forecast at deadline" dataKey="forecast_mw" stroke={COLORS.forecast} strokeWidth={1.5} dot={false} isAnimationActive={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </Status>
      </Section>

      <Section title="Average miss by day" hint="Days with the biggest misses are where a safety margin matters most.">
        <Status state={metrics}>
          <div className="chart">
            <ResponsiveContainer>
              <BarChart data={metrics.data?.daily || []} margin={{ top: 8, right: 16, bottom: 4, left: 8 }}>
                <CartesianGrid stroke={COLORS.grid} vertical={false} />
                <XAxis dataKey="date" tickFormatter={(d) => d.slice(8) + " Jan"} minTickGap={16} />
                <YAxis tickFormatter={(v) => num(v)} width={64} />
                <Tooltip formatter={(v, n) => [mw(v), n]} />
                <Bar name="Average miss" dataKey="mae_mw" fill={COLORS.forecast} isAnimationActive={false} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Status>
      </Section>
    </>
  );
}
