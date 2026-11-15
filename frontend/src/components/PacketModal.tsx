import { useEffect, useRef, useState } from "react";
import type { Assessment, DayRecord, Level, Passport } from "../types";
import { DISCLAIMER, LEVEL_MEANING, LEVEL_WORD, bgClass, formatDelay, isGroundOnly, levelRank, ownerLabel } from "../levels";
import { num, type Urgent } from "../findings";
import { Glyph, Modal } from "./ui";

const VITALS: { key: string; label: string; unit: string; d?: number }[] = [
  { key: "hr_rest", label: "Resting HR", unit: "bpm" },
  { key: "bp", label: "BP", unit: "mmHg" },
  { key: "temp", label: "Temp", unit: "°C", d: 1 },
  { key: "spo2", label: "SpO2", unit: "%" },
  { key: "resp_rate", label: "Resp. rate", unit: "/min" },
];
const EXTRA: { key: string; label: string; unit: string; d?: number }[] = [
  { key: "lymphocytes_abs", label: "Lymphocytes", unit: "/µL" },
  { key: "glucose", label: "Glucose", unit: "mg/dL" },
  { key: "pain_score", label: "Pain", unit: "/ 10" },
];

function vitalValue(day: DayRecord | undefined, key: string, unit: string, d = 0): string | null {
  if (!day) return null;
  if (key === "bp") {
    const s = num(day.bp_sys), di = num(day.bp_dia);
    return s !== null && di !== null ? `${s}/${di} ${unit}` : null;
  }
  const v = num(day[key]);
  return v === null ? null : `${d ? v.toFixed(d) : Math.round(v).toLocaleString("en-US")} ${unit}`;
}

/** Escalate: flight-surgeon packet (structured + plain text for downlink), queued at loss of signal, or "no urgent packet". */
export function PacketModal({ assessment, day, passport, top, onClose }: {
  assessment: Assessment; day: DayRecord | undefined; passport: Passport; top: Urgent | null; onClose: () => void;
}) {
  const a = assessment;
  const noLink = day?.comm_los === true;
  const [view, setView] = useState<"structured" | "plain">("structured");
  const [copied, setCopied] = useState<"" | "ok" | "fail">("");
  const [sent, setSent] = useState(false);
  const timer = useRef<number | undefined>(undefined);
  useEffect(() => () => window.clearTimeout(timer.current), []);
  const delay = num(day?.comm_delay_s) ?? passport.mission.comm_delay_s;
  const delayText = noLink ? "no link (far side)" : `${delay != null && delay < 1 ? "< 1 s" : formatDelay(delay)} one-way`;
  const md = day?.mission_day ?? "-";
  const role = passport.astronaut.role;

  const copy = async () => {
    try { await navigator.clipboard.writeText(a.packet ?? ""); setCopied("ok"); }
    catch { setCopied("fail"); }
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => setCopied(""), 2200);
  };

  if (!a.packet) {
    const orange: { key: string; text: string; level: Level; pct: number | null }[] = [
      ...a.hypotheses.filter((h) => h.level === "ORANGE").map((h) => ({ key: h.id, text: h.name, level: h.level, pct: Math.round(h.cf * 100) })),
      ...a.escalations.filter((e) => e.level === "ORANGE").map((e) => ({ key: e.rule, text: e.label, level: e.level, pct: null })),
    ];
    return (
      <Modal title="No urgent packet" subtitle={`Mission day ${md} · ${role}`} onClose={onClose}
        footer={<><span className="note">Simulated data</span><span className="right"><button type="button" className="btn btn-secondary" onClick={onClose}>Close</button></span></>}>
        <div className="step" style={{ gap: 16 }}>
          <p>No urgent packet. Orange items are added to today's medical downlink.</p>
          {orange.length > 0 ? (
            <section className="dr-sec">
              <h3 className="eyebrow" style={{ textTransform: "none", letterSpacing: 0, fontSize: 14 }}>Going down with today's medical downlink</h3>
              <ul className="downlink-list">
                {orange.map((o) => (
                  <li key={o.key}><Glyph level={o.level} /><span>{o.text}</span>{o.pct !== null && <small>{o.pct}% confidence</small>}</li>
                ))}
              </ul>
            </section>
          ) : <p className="muted">There are no ORANGE items right now.</p>}
          <p className="pk-note">{DISCLAIMER}</p>
        </div>
      </Modal>
    );
  }

  const level: Level = top ? (levelRank(top.level) > levelRank(a.overall_level) ? top.level : a.overall_level) : a.overall_level;
  const onboard = top?.actions.filter((x) => !isGroundOnly(x.who)) ?? [];
  const ground = top?.actions.filter((x) => isGroundOnly(x.who)) ?? [];
  const vitals = [...VITALS, ...EXTRA.filter((v) => num(day?.[v.key]) !== null)];

  return (
    <Modal title={noLink ? "Flight-surgeon packet (queued)" : "Flight-surgeon packet"} level={level}
      subtitle={`Mission day ${md} · ${role} · ${delayText} - onboard steps first`} onClose={onClose}
      footer={<>
        <span className="note">Simulated data{sent ? " · marked as sent; nothing leaves this demo" : ""}</span>
        <span className="right">
          <button type="button" className="btn btn-secondary" onClick={onClose}>Close</button>
          {noLink
            ? <button type="button" className="btn btn-crit" disabled>Waiting for signal</button>
            : <button type="button" className="btn btn-crit" disabled={sent} onClick={() => { setSent(true); void copy(); }}>{sent ? "Sent (simulated)" : "Send to flight surgeon"}</button>}
        </span>
      </>}>
      {noLink && (
        <div className="queued-note" role="status">
          <b>Queued - sends at acquisition of signal.</b>
          <span className="muted">Do the onboard steps now; don't wait for Earth.</span>
        </div>
      )}
      <div className="pk-bar">
        <div className="tabs" role="tablist" aria-label="Packet view">
          <button type="button" role="tab" className="tab" aria-selected={view === "structured"} onClick={() => setView("structured")}>Structured</button>
          <button type="button" role="tab" className="tab" aria-selected={view === "plain"} onClick={() => setView("plain")}>Plain text for downlink</button>
        </div>
        <button type="button" className="btn btn-secondary btn-sm" onClick={() => void copy()} aria-live="polite">
          {copied === "ok" ? "Copied" : copied === "fail" ? "Copy failed - select the text" : "Copy for downlink"}
        </button>
      </div>
      {view === "plain" ? (
        <div className="packet-wrap"><pre className="packet">{a.packet}</pre></div>
      ) : (
        <div className="pk">
          <div className="pk-row">
            <h3>Status</h3>
            <div>
              <span className={`badge ${bgClass(level)}`} style={{ justifySelf: "start" }}><Glyph level={level} />{LEVEL_WORD[level]} · {LEVEL_MEANING[level]}</span>
              {top && <p className="pk-status">{top.name}{top.cf != null ? ` · ${Math.round(top.cf * 100)}% confidence` : ""}</p>}
              {top?.esc && top.hyp && <p className="pk-flag">{top.esc.level === "RED" ? "Red flag" : `${LEVEL_WORD[top.esc.level]} flag`}: {top.esc.label}</p>}
            </div>
          </div>
          <div className="pk-row">
            <h3>Context</h3>
            <div className="pk-ctx">
              <div><span>Crew</span><b>{role}</b></div>
              <div><span>Mission day</span><b>MD {md}</b></div>
              <div><span>One-way delay</span><b>{noLink ? "No link (far side)" : delay != null && delay < 1 ? "< 1 s" : formatDelay(delay)}</b></div>
            </div>
          </div>
          <div className="pk-row">
            <h3>Vitals · NEWS2 {a.news2.total}{a.news2.max ? ` / ${a.news2.max}` : ""}</h3>
            <div className="pk-vitals">
              {vitals.map((v) => {
                const val = vitalValue(day, v.key, v.unit, v.d);
                return <div key={v.key} className={`pk-v ${val ? "" : "miss"}`}><span>{v.label}</span><b>{val ?? "missing"}</b></div>;
              })}
            </div>
          </div>
          {onboard.length > 0 && (
            <div className="pk-row">
              <h3>Onboard first</h3>
              <ul className="pk-list">{onboard.map((x) => <li key={x.id || x.text}>{x.text}<small>{ownerLabel(x.who)}</small></li>)}</ul>
            </div>
          )}
          {ground.length > 0 && (
            <div className="pk-row">
              <h3>Asks for ground</h3>
              <ul className="pk-list">{ground.map((x) => <li key={x.id || x.text}>{x.text}</li>)}</ul>
            </div>
          )}
          <p className="pk-note">{DISCLAIMER} No drug doses are included.</p>
        </div>
      )}
    </Modal>
  );
}
