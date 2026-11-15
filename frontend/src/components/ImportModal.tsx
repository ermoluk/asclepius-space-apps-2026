import { useRef, useState } from "react";
import { derivePassport, isLocalRef, localRef, parseImport, setLocalPassport } from "../api";
import { mergeBackup, nextCrewId, parseBackup, registerDocs, rekey } from "../myCrew";
import type { CrewMember, DayRecord, ImportResult } from "../types";
import { Modal } from "./ui";

const MAX_BYTES = 3_000_000;
const TEMPLATES: [string, string][] = [
  ["passport-daily.csv", "Six-month daily data (wide)"],
  ["labs-long.csv", "Labs with reference ranges (long)"],
  ["checkins.csv", "Check-in history (mission days)"],
  ["example-passport-HY-CDR.csv", "Example: six months of real-donor data"],
];

export interface ImportOutcome { members: CrewMember[]; select: number; message: string }

type Parsed =
  | { kind: "import"; file: string; text: string; result: ImportResult }
  | { kind: "backup"; file: string; members: CrewMember[]; rejected: number };

const days = (first: number, last: number, target: string) =>
  target === "passport" ? (first === last ? `L${first}` : `L${first} → L${last}`) : (first === last ? `MD ${first}` : `MD ${first} → ${last}`);

/** Join imported check-in days into a history by mission day (an imported value replaces the same item that day). */
export function mergeHistory(old: DayRecord[], add: DayRecord[]): { history: DayRecord[]; added: number; updated: number } {
  const byDay = new Map(old.map((d) => [d.mission_day, d]));
  let added = 0, updated = 0;
  for (const d of add) {
    const prev = byDay.get(d.mission_day);
    if (prev) updated += 1; else added += 1;
    byDay.set(d.mission_day, { ...prev, ...d });
  }
  return { history: [...byDay.values()].sort((a, b) => a.mission_day - b.mission_day), added, updated };
}

/** "My crew" import: a CSV table, a six-month passport JSON or a crew backup -> preview -> apply. */
export function ImportModal({ members, target, onClose, onApply }: {
  members: CrewMember[]; target: number | null; onClose: () => void; onApply: (o: ImportOutcome) => void;
}) {
  const [launch, setLaunch] = useState("");
  const [parsed, setParsed] = useState<Parsed | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [into, setInto] = useState<number | "new">(target ?? "new");
  const [name, setName] = useState("");
  const [drag, setDrag] = useState(false);
  const input = useRef<HTMLInputElement>(null);

  const read = async (file: string, text: string, launchDate: string) => {
    setBusy(true); setErr(null);
    try {
      const backup = parseBackup(text);
      if (backup) { setParsed({ kind: "backup", file, ...backup }); return; }
      const result = await parseImport({ filename: file, content: text, launch_date: launchDate || undefined });
      setParsed({ kind: "import", file, text, result });
      setName((n) => n || result.name);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally { setBusy(false); }
  };

  const pick = async (f: File | undefined) => {
    if (!f) return;
    if (f.size > MAX_BYTES) { setErr(`${f.name} is ${(f.size / 1e6).toFixed(1)} MB: the limit is 3 MB. Split the file or keep the last 180 days.`); return; }
    setParsed(null); setName("");
    await read(f.name, await f.text(), launch);
  };

  const applyImport = async (p: Extract<Parsed, { kind: "import" }>) => {
    const r = p.result;
    let crew = [...members];
    let idx = into === "new" ? crew.length : into;
    let m: CrewMember;
    if (into === "new") {
      const id = nextCrewId(crew);
      const derived = await derivePassport({ id, name: name.trim() || r.name, role: r.role || undefined, new_member: true,
        baselines: r.engine?.baselines });
      m = { passport: { ...derived, astronaut: { ...derived.astronaut, ...(r.sex ? { sex: r.sex } : {}), ...(r.age ? { age: r.age } : {}) },
        modifiers: [...new Set([...derived.modifiers, ...r.modifiers])] }, history: [] };
      crew.push(m);
    } else {
      m = crew[idx];
    }
    const parts: string[] = [];
    if (r.engine && r.passport_doc) {
      const old = m.passport.passport_ref;
      if (isLocalRef(old)) setLocalPassport(old, null);
      const ref = localRef(m.passport.astronaut.id);
      setLocalPassport(ref, r.passport_doc);
      m = { ...m, passport_doc: r.passport_doc, passport: { ...m.passport, baselines: { ...m.passport.baselines, ...r.engine.baselines },
        personal_ranges: r.engine.personal_ranges, lab_ranges: r.engine.lab_ranges, baselines_source: r.engine.baselines_source, passport_ref: ref } };
      parts.push(`six-month passport (${r.report.metrics.filter((x) => x.target === "passport").length} metrics)`);
    }
    if (r.history.length > 0) {
      const h = mergeHistory(m.history, r.history);
      m = { ...m, history: h.history };
      parts.push(`${h.added} new check-in day${h.added === 1 ? "" : "s"}${h.updated ? `, ${h.updated} updated` : ""}`);
    }
    crew = crew.map((x, i) => (i === idx ? m : x));
    idx = Math.min(idx, crew.length - 1);
    onApply({ members: crew, select: idx, message: `Imported ${p.file} into ${m.passport.astronaut.name}: ${parts.join(" and ")}.` });
  };

  const applyBackup = (p: Extract<Parsed, { kind: "backup" }>, replace: boolean) => {
    if (replace && members.length > 0 && !window.confirm(`Replace all ${members.length} crew member${members.length === 1 ? "" : "s"} in this browser with the ${p.members.length} from ${p.file}? This cannot be undone.`)) return;
    let crew: CrewMember[];
    if (replace) {
      crew = p.members.map((m) => rekey(m, m.passport.astronaut.id));
      registerDocs(crew);
    } else crew = mergeBackup(members, p.members);
    onApply({ members: crew, select: replace ? 0 : members.length,
      message: `Restored ${p.members.length} crew member${p.members.length === 1 ? "" : "s"} from ${p.file}${p.rejected ? ` (${p.rejected} unreadable entr${p.rejected === 1 ? "y" : "ies"} skipped)` : ""}.` });
  };

  const apply = async (replace = false) => {
    if (!parsed) return;
    if (parsed.kind === "import" && into !== "new" && parsed.result.passport_doc && members[into]?.passport.passport_ref
      && !window.confirm(`Replace ${members[into].passport.astronaut.name}'s six-month data with ${parsed.file}?`)) return;
    setBusy(true); setErr(null);
    try {
      if (parsed.kind === "backup") applyBackup(parsed, replace); else await applyImport(parsed);
    } catch (e) { setErr(e instanceof Error ? e.message : String(e)); }
    setBusy(false);
  };

  const r = parsed?.kind === "import" ? parsed.result : null;
  const rep = r?.report;
  const target_name = into === "new" ? (name.trim() || r?.name || "new member") : members[into]?.passport.astronaut.name;
  const hasPassport = !!r?.passport_doc;
  const nPassport = rep?.metrics.filter((x) => x.target === "passport").length ?? 0;

  return (
    <Modal title="Import data" eyebrow="My crew · stored only in this browser" wide onClose={onClose}
      subtitle={parsed ? `${parsed.file} · ${parsed.kind === "backup" ? "crew backup" : r?.kind === "passport" ? "six-month passport file" : `${rep?.layout} table`}` : "CSV table, six-month passport JSON or a crew backup"}
      footer={parsed ? (
        <><button type="button" className="btn btn-secondary" onClick={() => { setParsed(null); setErr(null); }}>Back</button>
          <span className="right">
            {parsed.kind === "backup" ? (
              <>
                {members.length > 0 && <button type="button" className="btn btn-secondary" disabled={busy || parsed.members.length === 0} onClick={() => apply(true)}>Replace crew</button>}
                <button type="button" className="btn btn-primary" disabled={busy || parsed.members.length === 0} onClick={() => apply(false)}>{members.length > 0 ? "Add to crew" : "Restore crew"}</button>
              </>
            ) : (
              <button type="button" className="btn btn-primary" disabled={busy || (into === "new" && !(name.trim() || r?.name))} onClick={() => apply()}>
                {busy ? "Importing…" : into === "new" ? "Add to crew" : `Import into ${target_name}`}</button>
            )}
          </span></>
      ) : (
        <><span className="note">Every imported value is labelled “Imported”. Nothing leaves this browser except for reading the file.</span>
          <span className="right"><button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button></span></>
      )}>
      {err && <div className="banner" role="alert"><div><b>Could not import.</b> {err}</div></div>}
      {!parsed && (
        <div className="step">
          <div className={`dropzone ${drag ? "drag" : ""}`}
            onDragOver={(e) => { e.preventDefault(); setDrag(true); }} onDragLeave={() => setDrag(false)}
            onDrop={(e) => { e.preventDefault(); setDrag(false); void pick(e.dataTransfer.files[0]); }}>
            <b>{busy ? "Reading…" : "Drop a file here"}</b>
            <span className="muted">.csv or .json, up to 3 MB</span>
            <button type="button" className="btn btn-primary" disabled={busy} onClick={() => input.current?.click()}>Choose file</button>
            <input ref={input} type="file" accept=".csv,.json,.txt,text/csv,application/json" hidden aria-label="Data file"
              onChange={(e) => { void pick(e.target.files?.[0]); e.target.value = ""; }} />
          </div>
          <div className="field-row">
            <label className="field"><span>Launch date <small className="muted">(only for files with calendar dates)</small></span>
              <input className="txt" type="date" value={launch} onChange={(e) => setLaunch(e.target.value)} /></label>
            <p className="hint imp-hint">Without it, the day after the last date counts as launch, so the whole file becomes the
              six-month passport. Rows on or after launch become check-ins.</p>
          </div>
          <div className="q"><h3>What the file can hold</h3>
            <ul className="imp-list">
              <li><b>Wide table</b> - a <code>day</code> (−180…−1 before launch, 1, 2… in flight) or <code>date</code> column, then one column per metric: <code>hr_rest, hrv_rmssd, sleep_hours, spo2, steps, body_mass, pvt_rt, mood_valence…</code></li>
              <li><b>Long table</b> - <code>day, metric, value, unit, ref_lo, ref_hi</code>: one value per row, for labs with their reference range.</li>
              <li><b>Passport JSON</b> - the six-month passport format of <code>data/passports/*.json</code>. <b>Crew backup</b> - a file from Export.</li>
            </ul>
            <p className="hint">Units are converted where known (°F, lb, minutes of sleep, glucose mmol/L, g/L, 10³/µL). Values outside a plausible range are skipped, never clipped. <code>;</code> separators with decimal commas work.</p>
            <div className="chips">
              {TEMPLATES.map(([f, l]) => <a key={f} className="btn btn-sm btn-secondary" href={`/import-templates/${f}`} download>{l}</a>)}
            </div>
          </div>
        </div>
      )}
      {parsed?.kind === "backup" && (
        <div className="step">
          <div className="q"><h3>{parsed.members.length} crew member{parsed.members.length === 1 ? "" : "s"} in this backup</h3>
            {parsed.rejected > 0 && <p className="hint">{parsed.rejected} entr{parsed.rejected === 1 ? "y is" : "ies are"} unreadable and will be skipped.</p>}
            <table className="imp-table">
              <thead><tr><th>Name</th><th>Id</th><th>Check-ins</th><th>Six-month data</th></tr></thead>
              <tbody>{parsed.members.map((m, i) => (
                <tr key={i}><td>{m.passport.astronaut.name}</td><td className="mono">{m.passport.astronaut.id}</td>
                  <td className="mono">{m.history.length}</td><td>{m.passport_doc ? "imported" : "none"}</td></tr>
              ))}</tbody>
            </table>
            <p className="hint">Add to crew keeps everyone already here (clashing ids get the next free MY-n). Replace crew removes them first.</p>
          </div>
        </div>
      )}
      {r && rep && (
        <div className="step">
          <div className="q"><h3>Import into</h3>
            <div className="field-row">
              <label className="field"><span>Crew member</span>
                <select value={String(into)} onChange={(e) => setInto(e.target.value === "new" ? "new" : Number(e.target.value))}>
                  <option value="new">New crew member</option>
                  {members.map((m, i) => <option key={m.passport.astronaut.id} value={i}>{m.passport.astronaut.name} · {m.passport.astronaut.id}</option>)}
                </select></label>
              {into === "new" && <label className="field"><span>Name (required)</span><input className="txt" value={name} maxLength={100} onChange={(e) => setName(e.target.value)} /></label>}
            </div>
            {into !== "new" && hasPassport && members[into]?.passport.passport_ref && <p className="hint">Replaces {target_name}'s current six-month data. Check-ins stay.</p>}
            {into !== "new" && r.history.length > 0 && <p className="hint">{(() => { const h = mergeHistory(members[into]?.history ?? [], r.history); return `${h.added} new day${h.added === 1 ? "" : "s"}, ${h.updated} existing day${h.updated === 1 ? "" : "s"} updated (imported values replace the same item).`; })()}</p>}
          </div>
          {rep.dates && (
            <div className="q"><h3>Launch date</h3>
              <div className="field-row">
                <label className="field"><span>Rows before it form the passport; rows on or after it become check-ins</span>
                  <input className="txt" type="date" value={launch || rep.launch_date || ""} onChange={(e) => setLaunch(e.target.value)} /></label>
                <span className="field"><span>&nbsp;</span><button type="button" className="btn btn-secondary" disabled={busy || !launch || launch === rep.launch_date}
                  onClick={() => void read(parsed!.file, (parsed as Extract<Parsed, { kind: "import" }>).text, launch)}>Re-read with this date</button></span>
              </div>
            </div>
          )}
          <div className="q"><h3>{rep.used} value{rep.used === 1 ? "" : "s"} found{nPassport ? ` · ${nPassport} passport metric${nPassport === 1 ? "" : "s"}` : ""}{rep.history_days ? ` · ${rep.history_days} check-in day${rep.history_days === 1 ? "" : "s"}` : ""}</h3>
            <table className="imp-table">
              <thead><tr><th>Metric</th><th>Values</th><th>Days</th><th>Goes to</th></tr></thead>
              <tbody>{rep.metrics.map((x) => (
                <tr key={`${x.target}-${x.metric}`}><td>{x.label} <span className="muted mono">{x.metric}{x.unit ? ` · ${x.unit}` : ""}</span></td>
                  <td className="mono">{x.n}</td><td className="mono">{days(x.first, x.last, x.target)}</td>
                  <td>{x.target === "passport" ? "Six-month passport" : "Check-ins"}</td></tr>
              ))}</tbody>
            </table>
            {r.engine && <p className="hint">Baselines: {r.engine.baselines_source}. Personal ranges (p10-p90): {Object.keys(r.engine.personal_ranges).join(", ") || "none - need daily data"}.</p>}
          </div>
          {(rep.converted.length > 0 || rep.unknown.length > 0 || rep.outside_window > 0 || rep.duplicates > 0 || rep.history_truncated) && (
            <div className="q"><h3>Notes</h3>
              <ul className="imp-list">
                {rep.converted.length > 0 && <li>Units converted: {rep.converted.join("; ")}.</li>}
                {rep.unknown.length > 0 && <li>Not recognised, ignored: <code>{rep.unknown.join(", ")}</code>.</li>}
                {rep.outside_window > 0 && <li>{rep.outside_window} value{rep.outside_window === 1 ? "" : "s"} older than L-180 left out (the passport covers the last 180 days before launch).</li>}
                {rep.duplicates > 0 && <li>{rep.duplicates} repeated value{rep.duplicates === 1 ? "" : "s"} for the same day: passport values averaged, check-ins keep the last.</li>}
                {rep.history_truncated ? <li>Only the latest 400 check-in days kept ({rep.history_truncated} older left out).</li> : null}
              </ul>
            </div>
          )}
          {rep.skipped_count > 0 && (
            <details className="q imp-skipped"><summary><b>{rep.skipped_count} value{rep.skipped_count === 1 ? "" : "s"} skipped</b> <span className="muted">- see why</span></summary>
              <ul className="imp-list">
                {rep.skipped.map((s, i) => <li key={i}><span className="mono">line {s.line}</span> {s.reason}</li>)}
                {rep.skipped_count > rep.skipped.length && <li className="muted">… and {rep.skipped_count - rep.skipped.length} more</li>}
              </ul>
            </details>
          )}
        </div>
      )}
    </Modal>
  );
}
