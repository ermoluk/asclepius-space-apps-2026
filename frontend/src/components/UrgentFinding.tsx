import { useState } from "react";
import type { Action, Assessment, Escalation, Hypothesis, TraceEntry } from "../types";
import { LEVEL_WORD, bgClass, lvClass, ownerIcon, ownerLabel } from "../levels";
import { mergeActions, type Urgent } from "../findings";
import { Chevron, Glyph } from "./ui";
import { LabOnChip } from "./LabOnChip";

const fmtFact = (v: unknown) =>
  typeof v === "number" ? (Number.isInteger(v) ? String(v) : v.toFixed(2)) : String(v);
const MAX_STEPS = 4;

function Incidence({ h }: { h: Hypothesis }) {
  if (!h.incidence) return null;
  return (
    <p className="incid" title={`NASA in-flight frequency · ${h.incidence.ref}`}>
      How common in flight: <b>{/share/.test(h.incidence.unit)
        ? `${Math.round(h.incidence.value * 100)}% of astronauts`
        : `${h.incidence.value} ${h.incidence.unit}`}</b> <span className="muted">· {h.incidence.ref.split(";")[0]}</span>
    </p>
  );
}

/** Rule trace: rule ID, condition, certainty factor, facts and source. */
export function Trace({ trace }: { trace: TraceEntry[] }) {
  return (
    <div className="why">
      <ul className="rules">
        {trace.map((t, i) => (
          <li className="rule" key={`${t.rule}-${i}`}>
            <code>{t.rule}</code>
            <span className="logic">{t.label}</span>
            <span className="cf">CF {t.cf.toFixed(2)}</span>
            <span className="facts">
              {Object.entries(t.facts).map(([k, v]) => <span key={k} className="fv">{k} = {fmtFact(v)}; </span>)}
            </span>
            <span className="src">{t.source.url
              ? <a href={t.source.url} target="_blank" rel="noreferrer noopener">{t.source.title || t.source.key}</a>
              : (t.source.title || t.source.key)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

/** Action steps with who does them (icon + text label for screen readers). */
export function ActionList({ actions }: { actions: Action[] }) {
  if (!actions?.length) return null;
  return (
    <ul className="act-list">
      {actions.map((a) => (
        <li key={a.id || a.text}>
          <span className="ow" aria-hidden="true">{ownerIcon(a.who)}</span>
          <span className="tx">{a.text}<small>{ownerLabel(a.who)}</small></span>
        </li>
      ))}
    </ul>
  );
}

export function UrgentFinding({ top, groundLast }: { top: Urgent; groundLast: boolean }) {
  const [why, setWhy] = useState(false);
  const [all, setAll] = useState(false);
  const trace = top.hyp?.trace ?? [];
  const steps = all ? top.actions : top.actions.slice(0, MAX_STEPS);
  const more = top.actions.length - MAX_STEPS;
  const pct = top.cf != null ? Math.round(top.cf * 100) : null;
  return (
    <section className="urgent" aria-labelledby="urgentTitle">
      <div className="urgent-top">
        <p className="eyebrow">Most urgent finding</p>
        <p className="sys">{top.system} · {top.hyp ? "suspected" : "escalation rule"}{top.expected ? " · expected space adaptation" : ""}</p>
      </div>
      <div className="urgent-title">
        <Glyph level={top.level} />
        <h2 id="urgentTitle">{top.name}</h2>
      </div>
      <p className="meta">
        <b className={lvClass(top.level)}>{top.level}</b>{pct != null ? ` · ${pct}% confidence` : ""}{top.expected ? " · Expected space adaptation" : ""}
      </p>
      {top.hyp && <Incidence h={top.hyp} />}
      {top.esc && top.hyp && (
        <p className="redflag"><b className={lvClass(top.esc.level)}>{top.esc.level === "RED" ? "Red flag" : `${LEVEL_WORD[top.esc.level]} flag`}</b> · {top.esc.label}</p>
      )}
      <div className="donow">
        <p className="eyebrow">Do now{groundLast ? " · onboard first" : ""}</p>
        {top.actions.length === 0 ? <p className="muted" style={{ padding: "10px 0" }}>No action steps for this finding.</p> : (
          <ol className="steps">
            {steps.map((a, i) => (
              <li key={a.id || a.text}>
                <span className="n">{String(i + 1).padStart(2, "0")}</span>
                <span className="t">{a.text}</span>
                <span className="o">{ownerLabel(a.who)}</span>
              </li>
            ))}
          </ol>
        )}
      </div>
      {(trace.length > 0 || more > 0) && (
        <div className="urgent-foot">
          {trace.length > 0 && (
            <button type="button" className="why-btn" aria-expanded={why} onClick={() => setWhy(!why)}>
              Why? <span className="sub">{trace.length} rule{trace.length === 1 ? "" : "s"} and sources</span>
              <svg viewBox="0 0 14 14" aria-hidden="true"><path d="M2 5l5 5 5-5" /></svg>
            </button>
          )}
          {more > 0 && (
            <button type="button" className="why-btn" aria-expanded={all} onClick={() => setAll(!all)}>
              <span className="sub">{all ? "Show fewer steps" : `${more} more step${more === 1 ? "" : "s"}`}</span>
            </button>
          )}
        </div>
      )}
      {why && trace.length > 0 && <Trace trace={trace} />}
    </section>
  );
}

function Finding({ h, groundLast }: { h: Hypothesis; groundLast: boolean }) {
  const [open, setOpen] = useState(false);
  const [why, setWhy] = useState(false);
  const pct = Math.round(h.cf * 100);
  return (
    <li className="finding" id={`f-${h.id}`}>
      <button type="button" className="finding-head" aria-expanded={open} onClick={() => setOpen(!open)}>
        <Glyph level={h.level} />
        <span className="nm">{h.name}<small>{h.system}</small></span>
        <Chevron />
        <span className={`conf ${lvClass(h.level)}`}>
          <span className="lw">{LEVEL_WORD[h.level]}</span>
          <span className="bar" role="img" aria-label={`Confidence ${pct}%`}><i style={{ ["--w" as string]: `${pct}%` }} /></span>
          <b>{pct}%</b>
        </span>
      </button>
      {open && (
        <div className="finding-body">
          <div className="finding-tags">
            <span className={`badge ${bgClass(h.level)}`}><Glyph level={h.level} />{LEVEL_WORD[h.level]}</span>
            <span className="tag">{h.system}</span>
            {h.expected && <span className="tag exp">Expected space adaptation</span>}
          </div>
          <Incidence h={h} />
          <ActionList actions={mergeActions([h.actions], groundLast)} />
          {h.trace.length > 0 && (
            <>
              <button type="button" className="why-btn" aria-expanded={why} onClick={() => setWhy(!why)}>
                Why? <span className="sub">{h.trace.length} rule{h.trace.length === 1 ? "" : "s"} · {h.system}</span>
                <svg viewBox="0 0 14 14" aria-hidden="true"><path d="M2 5l5 5 5-5" /></svg>
              </button>
              {why && <Trace trace={h.trace} />}
            </>
          )}
        </div>
      )}
    </li>
  );
}

function EscBox({ e, groundLast }: { e: Escalation; groundLast: boolean }) {
  return (
    <div className={`esc-box ${bgClass(e.level)}`}>
      <div className="finding-tags">
        <span className={`badge ${bgClass(e.level)}`}><Glyph level={e.level} />Escalation · {LEVEL_WORD[e.level]}</span>
        <span className="tag">{e.system}</span>
      </div>
      <p className="esc-t">{e.label}</p>
      <ActionList actions={mergeActions([e.actions], groundLast)} />
    </div>
  );
}

/** Everything besides the most urgent finding, plus measurement, lab-on-chip and the escalate row. */
export function AllFindings({ assessment, restHyps, restEscs, groundLast, loading, flash, onEscalate }: {
  assessment: Assessment | null; restHyps: Hypothesis[]; restEscs: Escalation[]; groundLast: boolean;
  loading: boolean; flash: boolean; onEscalate: () => void;
}) {
  const a = assessment;
  if (!a) return null;
  const none = a.hypotheses.length === 0 && a.escalations.length === 0;
  const showLoc = !!(a.systems.RAD || a.hypotheses.some((h) => h.system === "RAD"));
  return (
    <>
      {none && (
        <div className="empty-note"><b>No findings</b>Missing measurements are not treated as normal - a daily check-in adds data for more rules.</div>
      )}
      {(restHyps.length > 0 || restEscs.length > 0) && (
        <section id="all-findings" className={`findings-wrap ${flash ? "flash" : ""}`} aria-labelledby="otherTitle">
          <div className="sec-h">
            <h2 className="eyebrow" id="otherTitle">Other findings</h2>
            <span className="updating">{loading ? <><span className="spinner" />Updating</> : "Ranked by triage level, then confidence"}</span>
          </div>
          <div style={{ display: "grid", gap: 8 }}>
            {restEscs.map((e) => <EscBox key={e.rule} e={e} groundLast={groundLast} />)}
            {restHyps.length > 0 && <ul className="findings">{restHyps.map((h) => <Finding key={h.id} h={h} groundLast={groundLast} />)}</ul>}
          </div>
        </section>
      )}
      {showLoc && <LabOnChip />}
      {a.next_measurement && <NextMeasurement a={a} />}
      <div className="escalate">
        <p><b>Need to escalate?</b>
          {a.packet ? "A flight-surgeon packet is ready to send." : "No urgent packet. ORANGE items are added to today's medical downlink."}</p>
        <button type="button" className={`btn ${a.packet ? "btn-crit" : "btn-secondary"}`} onClick={onEscalate}>Escalate</button>
      </div>
    </>
  );
}

export function NextMeasurement({ a }: { a: Assessment }) {
  if (!a.next_measurement) return null;
  return (
    <div className="nbm">
      <div className="nbm-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12Z" /><circle cx="12" cy="12" r="3" /></svg></div>
      <p className="eyebrow">Next best measurement</p>
      <h3>{a.next_measurement.label}</h3>
      <p>Helps decide: {a.next_measurement.reason}</p>
      {a.pending.length > 0 && <p className="pending-note">{a.pending.length} check{a.pending.length === 1 ? "" : "s"} waiting for data</p>}
    </div>
  );
}
