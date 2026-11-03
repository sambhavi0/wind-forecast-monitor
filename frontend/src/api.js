import { useEffect, useState } from "react";

const BASE = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");

export async function apiGet(path, params = {}) {
  const qs = new URLSearchParams(
    Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== "")
  ).toString();
  const res = await fetch(`${BASE}${path}${qs ? `?${qs}` : ""}`);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail || detail;
    } catch {}
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return res.json();
}

/** Fetch on mount and whenever path/params change. Ignores stale responses. */
export function useApi(path, params, enabled = true) {
  const [state, setState] = useState({ data: null, error: null, loading: enabled });
  const key = JSON.stringify([path, params]);
  useEffect(() => {
    if (!enabled) return;
    let live = true;
    setState((s) => ({ ...s, loading: true, error: null }));
    apiGet(path, params)
      .then((data) => live && setState({ data, error: null, loading: false }))
      .catch((error) => live && setState({ data: null, error, loading: false }));
    return () => {
      live = false;
    };
  }, [key, enabled]);
  return state;
}
