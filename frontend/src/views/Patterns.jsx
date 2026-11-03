import React from "react";
import {
  Bar, CartesianGrid, ComposedChart, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { useApi } from "../api.js";
import { COLORS, Section, Status } from "../components/Bits.jsx";
import { mw, num } from "../format.js";

function PatternChart({ data, xKey, xFormatter, bars, line }) {
  return (
    <div className="chart">
      <ResponsiveContainer>
        <ComposedChart data={data} margin={{ top: 8, right: 16, bottom: 4, left: 8 }}>
          <CartesianGrid stroke={COLORS.grid} vertical={false} />
          <XAxis dataKey={xKey} tickFormatter={xFormatter} />
          <YAxis tickFormatter={(v) => num(v)} width={64} />
          <Tooltip formatter={(v, n) => [mw(v), n]} labelFormatter={xFormatter} />
          <Legend />
          <Bar name={bars.name} dataKey={bars.key} fill={COLORS.forecast} isAnimationActive={false} />
          <Line name={line.name} dataKey={line.key} stroke={line.color} strokeWidth={2} dot={false} isAnimationActive={false} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

export default function Patterns({ range, cutoff }) {
  const state = useApi("/api/patterns", { start: range.start, end: range.end, cutoff });
  const d = state.data;
  return (
    <Status state={state}>
      {d && (
        <>
          <Section title="How far ahead the forecast was made" hint="Error grows as the forecast is made further ahead. This uses every published forecast, not only the one at the deadline.">
            <PatternChart
              data={d.by_horizon}
              xKey="lead_from_h"
              xFormatter={(h) => `${h}–${h + 6} h`}
              bars={{ key: "mae_mw", name: "Average miss" }}
              line={{ key: "bias_mw", name: "Bias", color: COLORS.bias }}
            />
          </Section>

          <Section title="Time of day" hint="Hour of the target half-hour, UTC. Shows whether the forecast is weaker at certain times of day.">
            <PatternChart
              data={d.by_hour}
              xKey="hour"
              xFormatter={(h) => `${String(h).padStart(2, "0")}:00`}
              bars={{ key: "mae_mw", name: "Average miss" }}
              line={{ key: "bias_mw", name: "Bias", color: COLORS.bias }}
            />
          </Section>

          {d.by_level.length > 0 && (
            <Section title="Wind level" hint="Half-hours grouped into four equal-size bands by actual wind output.">
              <PatternChart
                data={d.by_level}
                xKey="label"
                xFormatter={(l) => l}
                bars={{ key: "mae_mw", name: "Average miss" }}
                line={{ key: "bias_mw", name: "Bias", color: COLORS.bias }}
              />
            </Section>
          )}
        </>
      )}
    </Status>
  );
}
