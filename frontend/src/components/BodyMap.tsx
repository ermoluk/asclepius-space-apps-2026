import { useState } from "react";
import type { Assessment, DayRecord, Level, Passport } from "../types";
import { LEVEL_ADVICE, LEVEL_MEANING, LEVEL_WORD, NO_RULE_FIRED, REGIONS, REGION_METRICS, bgClass, levelRank, lvClass, regionLevel, type Region } from "../levels";
import { mergeActions, num } from "../findings";
import { Chevron, Glyph, Modal, NoData } from "./ui";
import { ActionList } from "./UrgentFinding";

/** SVG body figure with one marker per system (halo on Orange/Red). */
function BodyFigure({ assessment, active, onPick }: { assessment: Assessment | null; active: Region | null; onPick: (r: Region) => void }) {
  const lvl = (r: Region): Level | null => regionLevel(assessment, r);
  return (
    <div className="bodymap">
      <svg viewBox="0 0 400 500" role="group" aria-label="Body systems map" className="map-svg">
        <g aria-hidden="true">
          <line className="fig-axis" x1="200" y1="4" x2="200" y2="496" />
          <path className="fig-limb" strokeWidth="30" d="M184 250 Q177 318 177 372 Q177 428 173 472" />
          <path className="fig-limb" strokeWidth="30" d="M216 250 Q223 318 223 372 Q223 428 227 472" />
          <path className="fig-limb" strokeWidth="22" d="M160 122 Q138 160 138 196 Q138 232 130 256" />
          <path className="fig-limb" strokeWidth="22" d="M240 122 Q262 160 262 196 Q262 232 270 256" />
          <rect className="fig" x="189" y="80" width="22" height="28" rx="6" />
          <path className="fig" d="M160 104 Q200 95 240 104 Q257 110 255 130 L245 244 Q243 266 222 268 L178 268 Q157 266 155 244 L145 130 Q143 110 160 104 Z" />
          <circle className="fig" cx="200" cy="58" r="32" />
          <ellipse className="fig" cx="167" cy="484" rx="16" ry="7" />
          <ellipse className="fig" cx="233" cy="484" rx="16" ry="7" />
        </g>
        <g className="callouts">
          {REGIONS.map((r) => {
            const l = lvl(r);
            const x = r.side === "L" ? 4 : 278;
            const ex = r.side === "L" ? x + 118 : x;
            return (
              <g key={r.id} className={`callout ${active?.id === r.id ? "active" : ""}`} tabIndex={0} role="button"
                aria-label={`${r.name}: ${l ? LEVEL_WORD[l] : "not assessed"}. Open details.`}
                onClick={() => onPick(r)} onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onPick(r); } }}>
                <line className="leader" x1={r.mx} y1={r.my} x2={ex} y2={r.cy} />
                <circle className="leader-dot" cx={r.mx} cy={r.my} r="2.5" />
                <rect className="chip-bg" x={x} y={r.cy - 20} width="118" height="40" rx="8" />
                <text className="chip-name" x={x + 10} y={r.cy - 3}>{r.name.length > 17 ? r.name.slice(0, 16) + "…" : r.name}</text>
                <text className="chip-lvl" x={x + 28} y={r.cy + 13}>{l ?? "NOT ASSESSED"}</text>
                {l ? <svg x={x + 9} y={r.cy + 2} width="14" height="14" viewBox="0 0 20 20" className={lvClass(l)}><use href={`#g-${l.toLowerCase()}`} /></svg>
                  : <svg x={x + 9} y={r.cy + 2} width="14" height="14" viewBox="0 0 20 20" style={{ color: "var(--na)" }}><circle cx="10" cy="10" r="8" fill="none" stroke="currentColor" strokeWidth="1.8" strokeDasharray="3 2.5" /></svg>}
              </g>
            );
          })}
        </g>
        <g>
          {REGIONS.map((r) => {
            const l = lvl(r);
            return (
              <g key={r.id} className={`marker ${active?.id === r.id ? "active" : ""}`} onClick={() => onPick(r)}>
                {l && levelRank(l) >= 2 && <circle className={`halo ${lvClass(l)}`} cx={r.mx} cy={r.my} r="11" />}
                <circle className="mk-ring" cx={r.mx} cy={r.my} r="13" />
                {l ? <svg x={r.mx - 9} y={r.my - 9} width="18" height="18" viewBox="0 0 20 20" className={lvClass(l)}><use href={`#g-${l.toLowerCase()}`} /></svg>
                  : <svg x={r.mx - 9} y={r.my - 9} width="18" height="18" viewBox="0 0 20 20" style={{ color: "var(--na)" }}><circle cx="10" cy="10" r="8" fill="none" stroke="currentColor" strokeWidth="1.8" strokeDasharray="3 2.5" /></svg>}
                <circle className="hit" cx={r.mx} cy={r.my} r="20" />
              </g>
            );
          })}
        </g>
      </svg>
    </div>
  );
}

/** Rail → "Body systems": legend, body map and system list; a system opens its detail in the same drawer. */
export function BodySystemsDrawer({ assessment, history, passport, groundLast, onClose }: {
  assessment: Assessment | null; history: DayRecord[]; passport: Passport; groundLast: boolean; onClose: () => void;
}) {
  const [region, setRegion] = useState<Region | null>(null);
  const lvl = (r: Region): Level | null => regionLevel(assessment, r);
  if (region) {
    const level = lvl(region);
    return (
      <Modal variant="drawer" title={region.name} eyebrow="Body system" level={level ?? undefined} onClose={onClose}>
        <button type="button" className="back-btn" onClick={() => setRegion(null)}><Chevron dir="left" className="" />All body systems</button>
        <RegionDetail region={region} level={level} assessment={assessment} history={history} passport={passport} groundLast={groundLast} />
      </Modal>
    );
  }
  return (
    <Modal variant="drawer" title="Body systems" eyebrow="Select a system" onClose={onClose}>
      <ul className="legend" aria-label="Status legend">
        {(["GREEN", "YELLOW", "ORANGE", "RED"] as Level[]).map((l) => (
          <li key={l}><Glyph level={l} />{LEVEL_MEANING[l]}</li>
        ))}
        <li><NoData />Not assessed (no finding)</li>
      </ul>
      <BodyFigure assessment={assessment} active={null} onPick={setRegion} />
      <p className="map-hint">Each label opens what the system does, today's findings and what to do.</p>
      <ul className="sys-list" aria-label="Body systems">
        {REGIONS.map((r) => {
          const l = lvl(r);
          return (
            <li key={r.id}>
              <button type="button" className="sys-btn" onClick={() => setRegion(r)}>
                {l ? <Glyph level={l} /> : <NoData />}
                <span><b>{r.name}</b><br /><small>{l ? `${LEVEL_WORD[l]} · ${LEVEL_MEANING[l]}` : "Not assessed · no finding or no data today"}</small></span>
                <Chevron dir="right" />
              </button>
            </li>
          );
        })}
      </ul>
    </Modal>
  );
}

function Spark({ values, level }: { values: (number | null)[]; level: Level | null }) {
  const pts = values.map((v, i) => ({ v, i })).filter((p): p is { v: number; i: number } => p.v !== null);
  if (pts.length < 2) return <svg className="spk" viewBox="0 0 88 28" aria-hidden="true" />;
  const lo = Math.min(...pts.map((p) => p.v)), hi = Math.max(...pts.map((p) => p.v));
  const span = hi - lo || 1;
  const n = Math.max(values.length - 1, 1);
  const xy = (p: { v: number; i: number }) => `${(p.i / n) * 84 + 2},${24 - ((p.v - lo) / span) * 20 + 0}`;
  const last = pts[pts.length - 1];
  return (
    <svg className={`spk ${level ? lvClass(level) : "faint"}`} viewBox="0 0 88 28" aria-hidden="true" preserveAspectRatio="none">
      <polyline points={pts.map(xy).join(" ")} />
      <circle cx={xy(last).split(",")[0]} cy={xy(last).split(",")[1]} r="2" />
    </svg>
  );
}

const fmt = (v: number, d = 0) => (d ? v.toFixed(d) : Math.round(v).toLocaleString("en-US"));

function RegionDetail({ region, level, assessment, history, passport, groundLast }: {
  region: Region; level: Level | null; assessment: Assessment | null; history: DayRecord[]; passport: Passport; groundLast: boolean;
}) {
  const hyps = assessment?.hypotheses.filter((h) => region.systems.includes(h.system)) ?? [];
  const escs = assessment?.escalations.filter((e) => region.systems.includes(e.system)) ?? [];
  const today = history[history.length - 1];
  const recent = history.slice(-14);
  const rows = REGION_METRICS[region.id].filter((m) => history.some((d) => num(d[m.key]) !== null));
  return (
    <>
      <p className="space-note">{region.fn}</p>
      {level ? (
        <div className={`status-box ${bgClass(level)}`}>
          <b><Glyph level={level} />{LEVEL_WORD[level]} · {LEVEL_MEANING[level]}</b>
          <span>{LEVEL_ADVICE[level]}</span>
        </div>
      ) : (
        <div className="dr-status nodata"><NoData />Not assessed · {assessment ? NO_RULE_FIRED : "Assessing…"}</div>
      )}
      <section className="dr-sec">
        <h3>Today vs your baseline</h3>
        {rows.length === 0 ? <p className="muted">No readings for this system in the mission log yet.</p> : (
          <div className="basel">
            {rows.map((m) => {
              const v = num(today?.[m.key]);
              const base = num(passport.baselines[m.key]);
              return (
                <div className="basel-row" key={m.key}>
                  <b>{m.label}</b>
                  <small>{base !== null ? `Baseline ${fmt(base, m.digits)} ${m.unit}` : "No personal baseline"}</small>
                  <Spark values={recent.map((d) => num(d[m.key]))} level={level} />
                  <span className="val">{v !== null ? <>{fmt(v, m.digits)} <small>{m.unit}</small></> : <small>No reading today</small>}</span>
                </div>
              );
            })}
          </div>
        )}
      </section>
      <section className="dr-sec">
        <h3>What may be going on</h3>
        {hyps.length === 0 && escs.length === 0 && <p className="muted">{assessment ? "No finding for this system from today's data." : "Assessing…"}</p>}
        {hyps.map((h) => (
          <div className="goingon" key={h.id}>
            <div className="goingon-h">
              <b><Glyph level={h.level} /> {h.name}{h.expected && <small className="muted"> · expected space adaptation</small>}</b>
              <span className={lvClass(h.level)}>{LEVEL_WORD[h.level]} · {Math.round(h.cf * 100)}%</span>
            </div>
            <ActionList actions={mergeActions([h.actions], groundLast)} />
          </div>
        ))}
      </section>
      {escs.map((e) => (
        <div key={e.rule} className={`esc-box ${bgClass(e.level)}`}>
          <p className="esc-t"><span className={lvClass(e.level)}>Escalation · {e.level}</span> - {e.label}</p>
          <ActionList actions={mergeActions([e.actions], groundLast)} />
        </div>
      ))}
    </>
  );
}
