export const mw = (v, digits = 0) =>
  v === null || v === undefined ? "–" : `${Number(v).toLocaleString("en-GB", { maximumFractionDigits: digits, minimumFractionDigits: digits })} MW`;

export const num = (v, digits = 0) =>
  v === null || v === undefined ? "–" : Number(v).toLocaleString("en-GB", { maximumFractionDigits: digits, minimumFractionDigits: digits });

const pad = (n) => String(n).padStart(2, "0");

export const hhmm = (iso) => {
  const d = new Date(iso);
  return `${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}`;
};

export const dayMonth = (ms) => {
  const d = new Date(ms);
  return `${pad(d.getUTCDate())} Jan`;
};

export const dateTime = (iso) => {
  const d = new Date(iso);
  return `${pad(d.getUTCDate())} Jan ${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())} UTC`;
};
