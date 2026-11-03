import React from "react";
import { Section } from "../components/Bits.jsx";

export default function Assumptions({ meta, cutoff, quantile }) {
  const pct = Math.round(quantile * 100);
  return (
    <>
      <Section title="What this tool answers">
        <ol className="prose">
          <li>Which wind forecast could the buyer see when the day-ahead decision had to be made?</li>
          <li>How wrong are those forecasts, and how much safety margin does that error justify?</li>
        </ol>
      </Section>

      <Section title="Assumptions">
        <ul className="prose">
          <li>
            <strong>Decision deadline:</strong> {cutoff} UTC on the day before delivery. This is a setting; change it in
            the left panel. Please confirm it against the actual day-ahead market gate closure.
          </li>
          <li>
            <strong>Forecast used:</strong> for each half-hour, the latest forecast published at or before the deadline.
            Later forecasts are ignored because the buyer could not have seen them.
          </li>
          <li>
            <strong>Error definition:</strong> forecast minus actual. Positive error means wind came in below forecast,
            which is the costly direction because extra thermal power must be bought.
          </li>
          <li>
            <strong>Safety margin:</strong> the {pct}th percentile of positive error over all half-hours already
            delivered before the deadline. It never uses information from after the decision.
          </li>
          <li>
            <strong>Time zone:</strong> everything is UTC, which equals UK local time throughout January.
          </li>
          <li>
            <strong>Scope:</strong> national wind only, January 2026 delivery days. No other data sources.
          </li>
        </ul>
      </Section>

      <Section title="Data">
        <ul className="prose">
          <li>Actuals: Elexon BMRS FUELHH, fuel type WIND (30-minute resolution).</li>
          <li>Forecasts: Elexon BMRS WINDFOR, with the publish time kept for every forecast.</li>
          {meta && (
            <li>
              Loaded {meta.slots?.toLocaleString("en-GB")} half-hours from {meta.first_day} to {meta.last_day}.
            </li>
          )}
        </ul>
      </Section>

      <Section title="Limitations">
        <ul className="prose">
          <li>A single month is a small sample. Margins will move with more data.</li>
          <li>The margin is one fixed number per day, not scaled to expected wind or weather conditions.</li>
          <li>The tool does not know prices, so it cannot say what the margin costs.</li>
        </ul>
      </Section>
    </>
  );
}
