import { useMemo, useRef, useState, type ReactElement } from "react";
import { Brush, CartesianGrid, Line, LineChart, ReferenceArea, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { AppMode, CrewMember, DayRecord, PassportDoc } from "../types";
import { GROUPS, METRICS, metricLabel, metricUnit, withUnit, type MetricDef } from "../metricsCatalog";
import {
  RANGES, dayLabel, domainFor, flightPoints, metricStats, niceTicks, preflightPoints, rolling7, ticksFor,
  type FlightPoint, type MetricStats, type PrePoint, type RangeId,
} from "../timeline";
import { usePassportDocs } from "../usePassportDocs";
import { Modal } from "./ui";

/** Crew comparison: one fixed colour and dash per crew slot (validated palette; dashes keep identity off colour alone). */
const SERIES = ["var(--series-1)", "var(--series-2)", "var(--series-3)", "var(--series-4)"];
const DASH = ["", "7 3", "2 3", "9 3 2 3"];

interface MemberData {
  name: string; initials: string; doc: PassportDoc | null; history: DayRecord[];
}
interface MetricView { m: MetricDef; label: string; unit: string; pre: PrePoint[]; flight: FlightPoint[]; stats: MetricStats }
type Row = { t: number } & Record<string, number | undefined>;

const initialsOf = (name: string) => name.split(/\s+/).filter(Boolean).map((w) => w[0]).join("").slice(0, 2).toUpperCase();

function view(m: MetricDef, d: MemberData, passport: CrewMember["passport"]): MetricView {
  const pre = preflightPoints(m, d.doc);
  const flight = flightPoints(m, d.history);
  return { m, label: metricLabel(m, d.doc), unit: metricUnit(m, d.doc), pre, flight, stats: metricStats(m, passport, d.doc, pre, flight) };
}

function deltaText(s: MetricStats, v: MetricView): string {
  if (s.delta === null) return "";
  const sign = s.delta > 0 ? "+" : s.delta < 0 ? "−" : "±";
  const pct = s.deltaPct !== null && Number.isFinite(s.deltaPct) ? ` (${sign}${Math.abs(s.deltaPct).toFixed(0)}%)` : "";
  // Never show a non-zero change as "0": add decimals until it reads.
  let digits = v.m.digits ?? 1;
  while (digits < 3 && s.delta !== 0 && Number(Math.abs(s.delta).toFixed(digits)) === 0) digits++;
  return `${sign}${Math.abs(s.delta).toFixed(digits)}${pct}`;
}

/** Split points into runs with no gap longer than `maxGap` days (gaps are shown, not bridged). */
function runs<T extends { t: number }>(pts: T[], maxGap: number): T[][] {
  const out: T[][] = [];
  for (const p of pts) {
    const run = out[out.length - 1];
    if (run && p.t - run[run.length - 1].t <= maxGap) run.push(p); else out.push([p]);
  }
  return out;
}

/** Small multiple: same time window as the main chart, no axes. */
function Mini({ v, dom }: { v: MetricView; dom: [number, number] }) {
  const pre = v.pre.filter((p) => p.t >= dom[0] && p.t <= dom[1]);
  const fl = v.flight.filter((p) => p.t >= dom[0] && p.t <= dom[1]);
  const { band, baseline } = v.stats;
  const vals = [...pre.map((p) => p.v), ...fl.map((p) => p.v), ...(band ? [band.lo, band.hi] : []), ...(baseline !== null ? [baseline] : [])];
  if (!vals.length) return <svg className="mini" viewBox="0 0 240 64" aria-hidden="true"><text x="120" y="36" className="mini-empty">no data in this window</text></svg>;
  const lo = Math.min(...vals), hi = Math.max(...vals), pad = (hi - lo) * 0.1 || Math.abs(hi) * 0.05 || 1;
  const x = (t: number) => ((t - dom[0]) / (dom[1] - dom[0])) * 236 + 2;
  const y = (val: number) => 60 - ((val - (lo - pad)) / (hi - lo + 2 * pad)) * 56;
  const poly = (pts: { t: number; v: number }[]) => pts.map((p) => `${x(p.t).toFixed(1)},${y(p.v).toFixed(1)}`).join(" ");
  const sparse = v.pre.length <= 30;
  return (
    <svg className="mini" viewBox="0 0 240 64" aria-hidden="true">
      {band && <rect className="spark-band" x={0} width={240} y={y(band.hi)} height={Math.max(1, y(band.lo) - y(band.hi))} />}
      {baseline !== null && <line className="spark-base" x1={0} x2={240} y1={y(baseline)} y2={y(baseline)} />}
      {dom[0] < 0 && dom[1] > 0 && <line className="mini-launch" x1={x(0)} x2={x(0)} y1={0} y2={64} />}
      {runs(pre, sparse ? 999 : 2).map((r, i) => (r.length > 1 ? <polyline key={i} className="mini-pre" points={poly(r)} /> : <circle key={i} className="mini-pre-dot" cx={x(r[0].t)} cy={y(r[0].v)} r={1.6} />))}
      {runs(fl, 1).map((r, i) => (r.length > 1 ? <polyline key={i} className="mini-fl" points={poly(r)} /> : null))}
      {fl.map((p, i) => <circle key={i} className="mini-fl-dot" cx={x(p.t)} cy={y(p.v)} r={2.4} />)}
    </svg>
  );
}

function endLabel(lastIdx: number, text: string, color: string) {
  return (p: { x?: number | string; y?: number | string; index?: number }): ReactElement<SVGElement> =>
    p.index === lastIdx && typeof p.x === "number" && typeof p.y === "number"
      ? <text x={p.x + 7} y={p.y + 4} className="cw-endlabel" style={{ fill: color }}>{text}</text>
      : <g />;
}

/** Full-screen Health dynamics: every metric on one time axis, six-month passport -> launch -> mission day. */
export function ChartsWindow({ members, active, dayIndex, mode, initialMetric, onMember, onDay, onClose }: {
  members: CrewMember[]; active: number; dayIndex: number; mode: AppMode; initialMetric?: string;
  onMember: (i: number) => void; onDay: (i: number) => void; onClose: () => void;
}) {
  const docs = usePassportDocs(members.map((m) => m.passport.passport_ref));
  const me = members[active] ?? members[0];
  const activeHistory = me?.history ?? [];
  const selDay = activeHistory[dayIndex]?.mission_day ?? null;
  const data: MemberData[] = useMemo(() => members.map((mb, i) => {
    const ref = mb.passport.passport_ref;
    const history = i === active ? mb.history.slice(0, dayIndex + 1)
      : selDay === null ? mb.history : mb.history.filter((d) => d.mission_day <= selDay);
    return { name: mb.passport.astronaut.name, initials: initialsOf(mb.passport.astronaut.name), doc: ref ? docs[ref] ?? null : null, history };
  }), [members, active, dayIndex, selDay, docs]);
  const mine = data[active] ?? data[0];

  const views = useMemo(() => (mine && me ? METRICS.map((m) => view(m, mine, me.passport)).filter((v) => v.pre.length || v.flight.length) : []), [mine, me]);
  const [metric, setMetric] = useState(initialMetric ?? "sleep_hours");
  const [range, setRange] = useState<RangeId>("all");
  const [smooth, setSmooth] = useState(false);
  const [compare, setCompare] = useState(false);
  const mainRef = useRef<HTMLDivElement>(null);
  const cur = views.find((v) => v.m.key === metric) ?? views.find((v) => v.m.key === "sleep_hours") ?? views[0];
  const canCompare = members.length > 1;
  const comparing = compare && canCompare;
  const loadingDoc = !!me?.passport.passport_ref && !mine?.doc;
  const flightName = mode === "crew" ? "Mission days · your check-ins" : "Mission days · scenario (simulated)";

  // Time window
  const firstPre = cur?.pre[0]?.t ?? null;
  const firstFlight = cur?.flight[0]?.t ?? activeHistory[0]?.mission_day ?? null;
  const lastT = selDay ?? 0;
  const dom = domainFor(range, firstPre, firstFlight, lastT);
  const ticks = ticksFor(dom);

  const chart = useMemo(() => {
    if (!cur || !mine) return null;
    const m = cur.m;
    const series: Record<string, { t: number; v: number }[]> = {};
    const sparse = cur.pre.length > 0 && cur.pre.length <= 30;
    const last: Record<string, number> = {};
    if (comparing) {
      data.forEach((d, i) => {
        const pre = preflightPoints(m, d.doc);
        series[`pre${i}`] = sparse ? pre : rolling7(pre);
        series[`fl${i}`] = flightPoints(m, d.history);
      });
    } else {
      series.pre = cur.pre;
      series.real = cur.pre.filter((p) => p.p !== "SC");
      series.model = cur.pre.filter((p) => p.p === "SC");
      series.flight = cur.flight;
      if (smooth) { series.preAvg = rolling7(cur.pre); series.flightAvg = rolling7(cur.flight); }
    }
    // A row for every day in the window keeps real gaps visible (a line never bridges a day with no data).
    const rows = new Map<number, Row>();
    const start = Math.max(dom[0], firstPre ?? 0);
    for (let t = Math.ceil(start); t < 0; t++) rows.set(t, { t });
    for (const d of activeHistory) if (d.mission_day <= lastT && d.mission_day >= dom[0]) rows.set(d.mission_day, { t: d.mission_day });
    for (const [k, pts] of Object.entries(series)) {
      for (const p of pts) {
        if (p.t < dom[0] || p.t > dom[1]) continue;
        const r = rows.get(p.t) ?? { t: p.t };
        r[k] = p.v;
        rows.set(p.t, r);
      }
    }
    const list = [...rows.values()].sort((a, b) => a.t - b.t);
    for (const k of Object.keys(series)) {
      for (let i = list.length - 1; i >= 0; i--) if (list[i][k] !== undefined) { last[k] = i; break; }
    }
    const vals = list.flatMap((r) => Object.entries(r).filter(([k]) => k !== "t").map(([, v]) => v as number));
    const s = cur.stats;
    const refs = [s.baseline, s.band?.lo, s.band?.hi, m.thr?.value].filter((v): v is number => typeof v === "number");
    const all = [...vals, ...refs];
    const lo = all.length ? Math.min(...all) : 0, hi = all.length ? Math.max(...all) : 1;
    const pad = (hi - lo) * 0.04 || Math.abs(hi) * 0.05 || 1;
    const nice = niceTicks(lo - pad, hi + pad);
    return { rows: list, last, sparse, y: nice.domain, yTicks: nice.ticks, digits: nice.digits, hasValues: vals.length > 0 };
  }, [cur, mine, data, comparing, smooth, dom[0], dom[1], firstPre, activeHistory, lastT]); // eslint-disable-line react-hooks/exhaustive-deps

  const groups = GROUPS.map((g) => ({ ...g, views: views.filter((v) => v.m.group === g.id) })).filter((g) => g.views.length);
  const pick = (key: string, scroll = false) => {
    setMetric(key);
    if (scroll) mainRef.current?.scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
  };
  const nameOf = (k: string): string => {
    if (k === "real") return "Pre-flight · real";
    if (k === "model") return "Pre-flight · calibrated model";
    if (k === "flight") return flightName.split(" · ")[0];
    if (k === "preAvg" || k === "flightAvg") return "7-day mean";
    const i = Number(k.replace(/\D/g, ""));
    return `${data[i]?.name ?? k}${k.startsWith("pre") && !chart?.sparse ? " · 7-day mean" : ""}`;
  };
  const s = cur?.stats;
  const u = cur?.unit ?? "";
  const fmtV = (v: number | null | undefined) => (cur ? withUnit(v, cur.m, u) : "-");
  const inDom = (t: number) => t >= dom[0] && t <= dom[1];

  return (
    <Modal variant="full" title={`Health dynamics · ${me?.passport.astronaut.name ?? ""}`}
      eyebrow={`${me?.passport.passport_ref ? "Six-month passport → " : "Check-ins → "}${selDay !== null ? `mission day ${selDay}` : "launch"} · ${mode === "crew" ? "your check-ins" : "simulated scenario"}`}
      onClose={onClose} className="cw-dlg">
      {views.length === 0 ? (
        <div className="cw-empty">
          {loadingDoc ? <p className="updating"><span className="spinner" />Loading six-month data…</p>
            : <p className="muted">No readings yet. Each daily check-in adds a point here; a six-month passport adds the pre-flight months.</p>}
        </div>
      ) : (
        <div className="cw">
          <nav className="cw-side" aria-label="Metrics">
            {groups.map((g) => (
              <section key={g.id}>
                <h3>{g.label}</h3>
                <ul>
                  {g.views.map((v) => (
                    <li key={v.m.key}>
                      <button type="button" className="cw-metric" aria-pressed={cur?.m.key === v.m.key} onClick={() => pick(v.m.key)}>
                        <span className="l">{v.label}</span>
                        <span className="v mono">{withUnit(v.stats.latest?.v, v.m, v.unit)}</span>
                        <small>{v.flight.length ? (deltaText(v.stats, v) ? `${deltaText(v.stats, v)} vs baseline` : `${v.flight.length} mission day${v.flight.length === 1 ? "" : "s"}`) : "pre-flight only"}</small>
                      </button>
                    </li>
                  ))}
                </ul>
              </section>
            ))}
          </nav>

          <div className="cw-main" ref={mainRef}>
            <div className="cw-bar">
              <label className="cw-select">
                <span className="sr">Metric</span>
                <select value={cur?.m.key} onChange={(e) => pick(e.target.value)}>
                  {groups.map((g) => (
                    <optgroup key={g.id} label={g.label}>
                      {g.views.map((v) => <option key={v.m.key} value={v.m.key}>{v.label}</option>)}
                    </optgroup>
                  ))}
                </select>
              </label>
              {canCompare && (
                <div className="cw-crew" role="group" aria-label="Crew member">
                  {members.map((mb, i) => (
                    <button key={mb.passport.astronaut.id} type="button" aria-pressed={i === active} onClick={() => onMember(i)}>
                      {comparing && <i className="cw-sw" style={{ background: SERIES[i % SERIES.length] }} aria-hidden="true" />}
                      {mb.passport.astronaut.name}
                    </button>
                  ))}
                </div>
              )}
              {activeHistory.length > 1 && (
                <label className="cw-day">
                  <span className="md">MD {selDay ?? "-"}</span>
                  <input className="slider" type="range" min={0} max={activeHistory.length - 1} value={Math.max(0, dayIndex)}
                    onChange={(e) => onDay(Number(e.target.value))} aria-label="Mission day"
                    aria-valuetext={`Mission day ${selDay ?? ""}, ${dayIndex + 1} of ${activeHistory.length}`} />
                  <small>{dayIndex + 1} of {activeHistory.length}</small>
                </label>
              )}
            </div>

            {cur && chart && (
              <section className="cw-chart-card" aria-labelledby="cwTitle">
                <div className="cw-head">
                  <div>
                    <p className="eyebrow">{GROUPS.find((g) => g.id === cur.m.group)?.label}</p>
                    <h3 id="cwTitle">{cur.label}{u ? <span className="muted"> · {u}</span> : null}</h3>
                  </div>
                  <div className="cw-controls">
                    <div className="tabs" role="tablist" aria-label="Time window">
                      {RANGES.map((r) => (
                        <button key={r.id} role="tab" type="button" className="tab" aria-selected={range === r.id} onClick={() => setRange(r.id)}>{r.label}</button>
                      ))}
                    </div>
                    <div className="cw-toggles">
                      {!comparing && <label><input type="checkbox" checked={smooth} onChange={(e) => setSmooth(e.target.checked)} /> 7-day mean</label>}
                      {canCompare && <label><input type="checkbox" checked={compare} onChange={(e) => setCompare(e.target.checked)} /> Compare crew</label>}
                    </div>
                  </div>
                </div>
                {loadingDoc && <p className="updating"><span className="spinner" />Loading six-month data…</p>}
                <div className="cw-box">
                  {!chart.hasValues ? <p className="muted cw-none">No {cur.label.toLowerCase()} readings in this time window.</p> : (
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart key={`${cur.m.key}-${range}-${comparing}-${smooth}`} data={chart.rows} margin={{ top: 22, right: comparing ? 40 : 18, bottom: 4, left: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                        <XAxis dataKey="t" type="number" domain={dom} ticks={ticks} tickFormatter={dayLabel} allowDataOverflow />
                        <YAxis domain={chart.y} ticks={chart.yTicks} width={56} allowDataOverflow interval={0}
                          tickFormatter={(v: number) => (Math.abs(v) >= 10000 ? `${(v / 1000).toFixed(0)}k` : v.toFixed(chart.digits))} />
                        {s?.band && <ReferenceArea y1={s.band.lo} y2={s.band.hi} className="band" ifOverflow="hidden" />}
                        {firstFlight !== null && firstFlight > 1 && inDom(0) && (
                          <ReferenceArea x1={0} x2={Math.min(firstFlight, dom[1])} className="cw-gap" ifOverflow="hidden"
                            label={{ value: `no records before MD ${firstFlight}`, position: "insideTop", className: "cw-gap-label" }} />
                        )}
                        {s?.baseline != null && <ReferenceLine y={s.baseline} className="base" ifOverflow="hidden"
                          label={{ value: `baseline ${fmtV(s.baseline)}`, position: "insideTopLeft", className: "cw-ref-label" }} />}
                        {cur.m.thr && <ReferenceLine y={cur.m.thr.value} className="thr" ifOverflow="hidden"
                          label={{ value: cur.m.thr.label, position: "insideBottomLeft", className: "cw-ref-label" }} />}
                        {inDom(0) && <ReferenceLine x={0} className="cw-launch" />}
                        {selDay !== null && inDom(selDay) && <ReferenceLine x={selDay} className="cw-sel"
                          label={{ value: `MD ${selDay}`, position: "top", className: "cw-ref-label strong" }} />}
                        <Tooltip cursor={{ stroke: "var(--line-strong)", strokeWidth: 1 }} isAnimationActive={false}
                          content={({ active: on, payload, label }) => {
                            const items = (payload ?? []).filter((p) => p.value != null && p.dataKey !== "pre");
                            if (!on || !items.length) return null;
                            return (
                              <div className="trend-tip cw-tip">
                                <p className="cw-tip-h">{dayLabel(Number(label))}</p>
                                {items.map((p) => (
                                  <p key={String(p.dataKey)}><b>{fmtV(Number(p.value))}</b> <span className="muted">{nameOf(String(p.dataKey))}</span></p>
                                ))}
                              </div>
                            );
                          }} />
                        {comparing ? data.flatMap((d, i) => {
                          const color = SERIES[i % SERIES.length];
                          const strong = i === active;
                          const lastIdx = Math.max(chart.last[`fl${i}`] ?? -1, chart.last[`pre${i}`] ?? -1);
                          const endOnFlight = (chart.last[`fl${i}`] ?? -1) === lastIdx;
                          return [
                            <Line key={`pre${i}`} dataKey={`pre${i}`} name={d.name} stroke={color} strokeWidth={strong ? 2.2 : 1.4}
                              strokeOpacity={strong ? 1 : 0.8} strokeDasharray={DASH[i % DASH.length]} dot={chart.sparse ? { r: 3.5, fill: color, stroke: "var(--surface)", strokeWidth: 2 } : false}
                              connectNulls isAnimationActive={false} label={endOnFlight ? undefined : endLabel(lastIdx, d.initials, color)} />,
                            <Line key={`fl${i}`} dataKey={`fl${i}`} name={d.name} stroke={color} strokeWidth={strong ? 2.6 : 1.8}
                              strokeDasharray={DASH[i % DASH.length]} dot={{ r: strong ? 4 : 3.2, fill: color, stroke: "var(--surface)", strokeWidth: 2 }}
                              activeDot={{ r: 6 }} connectNulls={false} isAnimationActive={false} label={endOnFlight ? endLabel(lastIdx, d.initials, color) : undefined} />,
                          ];
                        }) : [
                          <Line key="pre" dataKey="pre" className="cw-pre" dot={false} activeDot={false} connectNulls={chart.sparse} isAnimationActive={false} />,
                          <Line key="model" dataKey="model" stroke="none" dot={{ r: chart.sparse ? 4 : 2, className: "dot-model" }} activeDot={false} isAnimationActive={false} />,
                          <Line key="real" dataKey="real" stroke="none" dot={{ r: chart.sparse ? 4.5 : 2.4, className: "dot-real" }} activeDot={{ r: 5 }} isAnimationActive={false} />,
                          ...(smooth ? [
                            <Line key="preAvg" dataKey="preAvg" className="cw-avg" dot={false} activeDot={false} connectNulls isAnimationActive={false} />,
                            <Line key="flightAvg" dataKey="flightAvg" className="cw-avg" dot={false} activeDot={false} connectNulls isAnimationActive={false} />,
                          ] : []),
                          <Line key="flight" dataKey="flight" className="cw-flight" connectNulls={false} isAnimationActive={false}
                            dot={{ r: 4, className: "cw-flight-dot" }} activeDot={{ r: 6, className: "cw-flight-dot" }} />,
                        ]}
                        {chart.rows.length > 20 && (
                          <Brush dataKey="t" height={26} travellerWidth={10} tickFormatter={(t: number) => dayLabel(t)} className="cw-brush"
                            stroke="var(--line-strong)" fill="var(--surface-2)" />
                        )}
                      </LineChart>
                    </ResponsiveContainer>
                  )}
                </div>
                <div className="key">
                  {comparing ? data.map((d, i) => (
                    <span key={i}><svg className="cw-key-line" viewBox="0 0 24 10" aria-hidden="true"><line x1="0" x2="24" y1="5" y2="5" style={{ stroke: SERIES[i % SERIES.length] }} strokeDasharray={DASH[i % DASH.length]} /></svg>
                      {d.name}{i === active ? " (selected)" : ""}{d.doc ? "" : " · no six-month passport"}</span>
                  )) : <>
                    {cur.pre.some((p) => p.p !== "SC") && <span><i className="sw dot real" />{cur.pre.every((p) => p.p === "IM" || p.p === "SC") ? "Pre-flight · imported" : "Pre-flight · real"}</span>}
                    {cur.pre.some((p) => p.p === "SC") && <span><i className="sw dot model" />Pre-flight · calibrated model</span>}
                    {cur.flight.length > 0 && <span><i className="sw flight" />{flightName}</span>}
                    {smooth && <span><i className="sw avg" />7-day mean</span>}
                  </>}
                  {s?.baseline != null && <span><i className="sw base" />Personal baseline</span>}
                  {s?.band && <span><i className="sw band" />{s.band.kind === "lab" ? "Lab reference range" : "Personal range (p10-p90, six-month passport)"}</span>}
                  {cur.m.thr && <span><i className="sw thr" />{cur.m.thr.label}</span>}
                </div>
                <p className="trend-cap">
                  {comparing ? (chart.sparse ? "Each crew member's own values; band and baseline are the selected member's. " : "Pre-flight lines are 7-day means; mission days are daily values. Band and baseline are the selected member's. ")
                    : "Missing days are shown as gaps, not zeros. "}
                  Drag the handles under the chart to zoom. Mission days are shown up to the selected day.
                </p>
                {s && (
                  <dl className="cw-stats">
                    <div><dt>Baseline</dt><dd>{fmtV(s.baseline)}</dd></div>
                    <div><dt>{s.band?.kind === "lab" ? "Lab range" : "Personal range"}</dt><dd>{s.band ? `${s.band.lo.toFixed(cur.m.digits ?? 1)}${s.band.lo < 0 || s.band.hi < 0 ? " to " : "-"}${fmtV(s.band.hi)}` : "-"}</dd></div>
                    <div><dt>Last 30 days before launch</dt><dd>{s.pre30 !== null ? `${fmtV(s.pre30)} mean` : "-"}</dd></div>
                    <div><dt>Latest</dt><dd>{s.latest ? `${fmtV(s.latest.v)} · ${dayLabel(s.latest.t)}` : "-"}</dd></div>
                    <div><dt>Change vs baseline</dt><dd>{deltaText(s, cur) || "-"}</dd></div>
                    <div><dt>In flight, min-max</dt><dd>{s.flightMin !== null && s.flightMax !== null ? `${s.flightMin.toFixed(cur.m.digits ?? 1)}${s.flightMin < 0 ? " to " : "-"}${fmtV(s.flightMax)}` : "-"}</dd></div>
                    <div><dt>Mission days outside range</dt><dd>{s.band && s.nFlight ? `${s.outside} of ${s.nFlight}` : "-"}</dd></div>
                    <div><dt>Data points</dt><dd>{s.nReal} real · {s.nModel} modelled · {s.nFlight} mission</dd></div>
                  </dl>
                )}
              </section>
            )}

            <section className="cw-all" aria-labelledby="cwAll">
              <h3 id="cwAll">All metrics <span className="muted">· {views.length} · {RANGES.find((r) => r.id === range)?.label.toLowerCase()}</span></h3>
              {groups.map((g) => (
                <div key={g.id} className="cw-all-g">
                  <p className="eyebrow">{g.label}</p>
                  <div className="cw-grid">
                    {g.views.map((v) => (
                      <button key={v.m.key} type="button" className="cw-card" aria-pressed={cur?.m.key === v.m.key} onClick={() => pick(v.m.key, true)}>
                        <span className="cw-card-h"><span>{v.label}</span><b className="mono">{withUnit(v.stats.latest?.v, v.m, v.unit)}</b></span>
                        <Mini v={v} dom={domainFor(range, v.pre[0]?.t ?? null, v.flight[0]?.t ?? firstFlight, lastT)} />
                        <small className="muted">{v.flight.length ? `${deltaText(v.stats, v) || "no baseline"}${deltaText(v.stats, v) ? " vs baseline" : ""}` : "pre-flight only"}</small>
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </section>
          </div>
        </div>
      )}
    </Modal>
  );
}

