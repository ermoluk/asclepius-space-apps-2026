import type { DayRecord, Passport, PassportDoc, ProvCode } from "./types";
import { fieldFor, preKey, provOf, type MetricDef } from "./metricsCatalog";

/** One time axis for the whole record: t < 0 = days before launch (L-t), t = mission day after launch. */
export interface PrePoint { t: number; v: number; p: ProvCode }
export interface FlightPoint { t: number; v: number }

const isNum = (v: unknown): v is number => typeof v === "number" && Number.isFinite(v);

/** Six-month passport values for a metric: the daily series, else one-off exam values from the sessions. */
export function preflightPoints(m: MetricDef, doc: PassportDoc | null | undefined): PrePoint[] {
  if (!doc) return [];
  const series = doc.series[preKey(m)];
  if (series?.length) return series.map(([t, v, p]) => ({ t, v, p }));
  const key = m.session;
  if (!key) return [];
  return doc.sessions
    .filter((s) => s.status === "done" && isNum(s.values[key]))
    .map((s) => ({ t: s.t, v: s.values[key] as number, p: provOf(s.provenance) }))
    .sort((a, b) => a.t - b.t);
}

/** Mission-day values (the history is already cut at the selected day). */
export function flightPoints(m: MetricDef, history: DayRecord[]): FlightPoint[] {
  const out: FlightPoint[] = [];
  for (const d of history) { const v = d[m.key]; if (isNum(v)) out.push({ t: d.mission_day, v }); }
  return out;
}

/** Trailing 7-day mean at each point (days with no data are skipped, not counted as zero). */
export function rolling7<T extends { t: number; v: number }>(pts: T[]): FlightPoint[] {
  return pts.map((p) => {
    const win = pts.filter((q) => q.t > p.t - 7 && q.t <= p.t);
    return { t: p.t, v: win.reduce((s, q) => s + q.v, 0) / win.length };
  });
}

export interface Band { lo: number; hi: number; kind: "personal" | "lab" }
export interface MetricStats {
  baseline: number | null;
  band: Band | null;
  /** Mean of the last 30 pre-flight days. */
  pre30: number | null;
  latest: { t: number; v: number; flight: boolean } | null;
  delta: number | null;
  deltaPct: number | null;
  flightMin: number | null;
  flightMax: number | null;
  /** Mission days outside the personal/lab range. */
  outside: number;
  nReal: number;
  nModel: number;
  nFlight: number;
}

/** Baseline the rule engine uses (passport), else the six-month passport field value. */
export function baselineOf(m: MetricDef, passport: Passport | null | undefined, doc: PassportDoc | null | undefined): number | null {
  const b = passport?.baselines?.[m.key];
  if (isNum(b)) return b;
  const f = fieldFor(doc, preKey(m)) ?? (m.session ? fieldFor(doc, m.session) : undefined);
  return f && isNum(f.value) ? f.value : null;
}

/** Personal range (p10-p90 of the six-month passport) or the lab reference range. */
export function bandOf(m: MetricDef, passport: Passport | null | undefined, doc: PassportDoc | null | undefined): Band | null {
  const kind = m.group === "labs" ? "lab" : "personal";
  const r = passport?.personal_ranges?.[m.key] ?? passport?.lab_ranges?.[m.key];
  if (r && isNum(r.lo) && isNum(r.hi)) return { lo: r.lo, hi: r.hi, kind };
  const f = fieldFor(doc, preKey(m));
  if (f && isNum(f.lo) && isNum(f.hi)) return { lo: f.lo, hi: f.hi, kind };
  return null;
}

export function metricStats(m: MetricDef, passport: Passport | null | undefined, doc: PassportDoc | null | undefined,
  pre: PrePoint[], flight: FlightPoint[]): MetricStats {
  const baseline = baselineOf(m, passport, doc);
  const band = bandOf(m, passport, doc);
  const last30 = pre.filter((p) => p.t >= -30);
  const pre30 = last30.length ? last30.reduce((s, p) => s + p.v, 0) / last30.length : null;
  const lf = flight[flight.length - 1];
  const lp = pre[pre.length - 1];
  const latest = lf ? { t: lf.t, v: lf.v, flight: true } : lp ? { t: lp.t, v: lp.v, flight: false } : null;
  const delta = latest && baseline !== null ? latest.v - baseline : null;
  const fv = flight.map((p) => p.v);
  return {
    baseline, band, pre30, latest, delta,
    deltaPct: delta !== null && baseline ? (delta / Math.abs(baseline)) * 100 : null,
    flightMin: fv.length ? Math.min(...fv) : null,
    flightMax: fv.length ? Math.max(...fv) : null,
    outside: band ? fv.filter((v) => v < band.lo || v > band.hi).length : 0,
    nReal: pre.filter((p) => p.p !== "SC").length,
    nModel: pre.filter((p) => p.p === "SC").length,
    nFlight: flight.length,
  };
}

export type RangeId = "all" | "30" | "flight";
export const RANGES: { id: RangeId; label: string }[] = [
  { id: "all", label: "6 months + flight" },
  { id: "30", label: "Last 30 days + flight" },
  { id: "flight", label: "Flight only" },
];

/** X domain for a range preset. `lastT` is the selected mission day (0 when there is no flight data yet). */
export function domainFor(range: RangeId, firstPre: number | null, firstFlight: number | null, lastT: number): [number, number] {
  const end = Math.max(lastT, 0) + 1;
  // Mission-only metrics (cabin CO2, dose) have no pre-flight months to show.
  if ((range === "flight" || firstPre === null) && firstFlight !== null) return [firstFlight - 1, end];
  if (range === "30" || range === "flight") return [-30, end];
  return [Math.min(firstPre ?? -180, -1), end];
}

/** Ticks: launch plus a step that fits the span; L-x before launch, MD x after. */
export function ticksFor([a, b]: [number, number]): number[] {
  const span = b - a;
  const step = span > 150 ? 30 : span > 70 ? 14 : span > 30 ? 7 : span > 12 ? 2 : 1;
  const out = new Set<number>();
  for (let t = Math.ceil(a / step) * step; t <= b; t += step) out.add(t);
  if (a <= 0 && b >= 0) out.add(0);
  return [...out].sort((x, y) => x - y);
}
export const dayLabel = (t: number) => (t === 0 ? "Launch" : t < 0 ? `L${t}` : `MD ${t}`);

/** Round axis ticks (1, 2, 2.5, 5 x 10^n steps) covering [lo, hi]. */
export function niceTicks(lo: number, hi: number, count = 5): { domain: [number, number]; ticks: number[]; digits: number } {
  const span = hi - lo || Math.abs(hi) || 1;
  const raw = span / count;
  const mag = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 2.5, 5, 10].map((f) => f * mag).find((st) => st >= raw) ?? 10 * mag;
  const a = Math.floor(lo / step) * step, b = Math.ceil(hi / step) * step;
  const ticks: number[] = [];
  for (let t = a; t <= b + step / 2; t += step) ticks.push(Number(t.toFixed(10)));
  const digits = Math.max(0, -Math.floor(Math.log10(step) + 1e-9) + (step / mag === 2.5 ? 1 : 0));
  return { domain: [a, b], ticks, digits };
}
