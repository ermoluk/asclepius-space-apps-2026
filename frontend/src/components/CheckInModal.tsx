import { useState } from "react";
import type { AppMode, DayRecord } from "../types";
import { Modal } from "./ui";
import { ReactionGame } from "./ReactionGame";

const CARRY = ["co2_1h", "co2_7d", "pio2", "cabin_temp", "dose_today", "dose_cumulative", "comm_delay_s", "phase"];

const SYMPTOM_GROUPS: [string, [string, string][]][] = [
  ["Head and senses", [["sym_headache", "Headache"], ["sym_dizziness", "Dizziness"], ["sym_blurred_near_vision", "Blurred near vision"],
    ["sym_nasal_congestion", "Nasal congestion"], ["sym_sore_throat", "Sore throat"]]],
  ["Chest", [["sym_cough", "Cough"], ["sym_palpitations", "Palpitations"], ["sym_shortness_of_breath", "Shortness of breath"]]],
  ["Belly and back", [["sym_nausea", "Nausea"], ["sym_diarrhea", "Diarrhea"], ["sym_back_pain", "Back pain"], ["sym_flank_pain", "Flank pain"]]],
  ["Whole body", [["sym_fatigue", "Fatigue"], ["sym_joint_pain", "Joint pain"], ["sym_rash", "Rash"], ["sym_fever_chills", "Fever or chills"]]],
];
const SYM_KEYS = SYMPTOM_GROUPS.flatMap(([, items]) => items.map(([k]) => k));
const MOODS = ["calm", "content", "energetic", "anxious", "irritable", "lonely", "homesick", "sad", "bored"];

const VITALS: { key: string; label: string; unit: string; how: string; sm?: boolean }[] = [
  { key: "hr_rest", label: "Resting heart rate", unit: "bpm", how: "Sit still for 5 min, count the pulse at the wrist for 30 s and double it." },
  { key: "bp_sys", label: "Blood pressure, systolic", unit: "mmHg", how: "Seated, arm at heart level, cuff on bare upper arm; top number." },
  { key: "bp_dia", label: "Blood pressure, diastolic", unit: "mmHg", how: "Same reading as above; bottom number." },
  { key: "temp", label: "Temperature", unit: "°C", how: "Oral or ear thermometer, at rest, not right after exercise or a hot drink.", sm: true },
  { key: "spo2", label: "Oxygen saturation (SpO₂)", unit: "%", how: "Pulse oximeter on a warm fingertip; hold still until it stabilises." },
  { key: "glucose_fasting", label: "Fasting glucose", unit: "mg/dL", how: "Glucometer after at least 8 h without food, first finger-prick drop." },
];

/** Mirrors the backend DayRecord ranges (backend/app/main.py). */
const RANGES: Record<string, [number, number, string]> = {
  sleep_hours: [0, 24, "h"], hr_rest: [20, 250, "bpm"], bp_sys: [40, 300, "mmHg"], bp_dia: [40, 300, "mmHg"],
  temp: [30, 43, "°C - not °F"], spo2: [50, 100, "%"], glucose_fasting: [20, 600, "mg/dL"],
  exercise_min: [0, 600, "min"], fluid_intake: [0, 10, "L"], food_intake_pct: [0, 200, "%"], pvt_rt: [100, 2000, "ms"],
};
const rangeError = (k: string, raw: string | undefined): string | null => {
  if (raw === undefined || raw === "" || !RANGES[k]) return null;
  const [lo, hi, unit] = RANGES[k];
  const n = Number(raw);
  return Number.isFinite(n) && n >= lo && n <= hi ? null : `Enter a value from ${lo} to ${hi} (${unit}).`;
};

type Form = Record<string, string | boolean | string[] | undefined>;

const MORNING_SCALES = ["sleep_quality", "kss", "physical_state"];
const EVENING_SCALES = ["mood_valence", "team_cohesion", "workload", "fatigue"];
const EVENING_NUMS = ["exercise_min", "fluid_intake", "food_intake_pct"];
/** Every answer the form can hold (the onboard PVT only when the day has one). */
const FORM_KEYS = ["sleep_hours", ...MORNING_SCALES, ...VITALS.map((v) => v.key), "pvt_rt", ...EVENING_SCALES, ...EVENING_NUMS];

const num = (v: unknown): number | null => (typeof v === "number" && Number.isFinite(v) ? v : null);

/** A filed day's answers, loaded back into the form. */
function formFrom(rec: DayRecord | undefined) {
  const f: Form = {};
  if (!rec) return { f, syms: [] as string[], moods: [] as string[], tap: null as number | null };
  for (const k of FORM_KEYS) { const v = num(rec[k]); if (v !== null) f[k] = String(v); }
  const labels = Array.isArray(rec.mood_labels) ? rec.mood_labels : [];
  return { f, syms: SYM_KEYS.filter((k) => rec[k] === true), moods: labels.filter((m) => MOODS.includes(m)), tap: num(rec.tap_rt) };
}

function Scale({ min, max, value, onChange, lo, hi, label }: {
  min: number; max: number; value: string | undefined; onChange: (v: string | undefined) => void; lo?: string; hi?: string; label: string;
}) {
  const items = Array.from({ length: max - min + 1 }, (_, i) => min + i);
  return (
    <div className="q" role="group" aria-label={label}>
      <div className={`seg n${max - min + 1}`} style={{ gridTemplateColumns: `repeat(${items.length},minmax(0,1fr))` }}>
        {items.map((n) => (
          <button key={n} type="button" aria-pressed={value === String(n)} onClick={() => onChange(value === String(n) ? undefined : String(n))}>{n}</button>
        ))}
      </div>
      {(lo || hi) && <div className="scale-ends"><span>{lo}</span><span>{hi}</span></div>}
    </div>
  );
}

function Chips({ items, selected, onToggle }: { items: [string, string][]; selected: string[]; onToggle: (k: string) => void }) {
  return (
    <div className="chips">
      {items.map(([k, l]) => (
        <button key={k} type="button" aria-pressed={selected.includes(k)} onClick={() => onToggle(k)}>{l}</button>
      ))}
    </div>
  );
}

function SymptomGroups({ selected, onToggle }: { selected: string[]; onToggle: (k: string) => void }) {
  return (
    <div style={{ display: "grid", gap: 14 }}>
      {SYMPTOM_GROUPS.map(([g, items]) => (
        <div className="chip-group" key={g} role="group" aria-label={g}>
          <span>{g}</span>
          <Chips items={items} selected={selected} onToggle={onToggle} />
        </div>
      ))}
    </div>
  );
}

function NumField({ label, unit, value, onChange, step, error, min, max }: { label: string; unit: string; value: string | undefined; onChange: (v: string) => void; step?: string; error?: string | null; min?: number; max?: number }) {
  return (
    <label className="vfield narrow">
      <b>{label}</b>
      <span className="vbox"><input type="number" inputMode="decimal" step={step ?? "any"} min={min} max={max} aria-invalid={!!error} value={value ?? ""} onChange={(e) => onChange(e.target.value)} /><span className="unit">{unit}</span></span>
      {error && <span className="field-err" role="alert">{error}</span>}
    </label>
  );
}

/** Daily check-in. "report": the answers already filed for the selected day, editable. "new": the next day's
 *  check-in (morning adds a day, evening completes the last one). */
export function CheckInModal({ history, dayIndex, mode, who, onSubmit, onClose }: {
  history: DayRecord[]; dayIndex: number; mode: AppMode; who?: string;
  onSubmit: (history: DayRecord[], dayIndex: number) => void; onClose: () => void;
}) {
  const lastIdx = history.length - 1;
  const sel = dayIndex >= 0 && dayIndex <= lastIdx ? dayIndex : lastIdx;
  const record = sel >= 0 ? history[sel] : undefined;
  // Demo days are already filed: open the selected day's report. My crew: a past day opens its report, the
  // latest day starts the next check-in.
  const [kind, setKind] = useState<"report" | "new">(record && (mode === "demo" || sel < lastIdx) ? "report" : "new");
  const report = kind === "report" && !!record;
  const init = report ? formFrom(record) : formFrom(undefined);
  const [tab, setTab] = useState<"morning" | "evening">("morning");
  const [f, setF] = useState<Form>(init.f);
  const [syms, setSyms] = useState<string[]>(init.syms);
  const [moods, setMoods] = useState<string[]>(init.moods);
  const [pvt, setPvt] = useState<number | null>(init.tap);
  const set = (k: string) => (v: string | undefined) => setF((p) => ({ ...p, [k]: v }));
  const toggle = (arr: string[], k: string) => (arr.includes(k) ? arr.filter((x) => x !== k) : [...arr, k]);
  const s = (k: string) => f[k] as string | undefined;
  const switchKind = (k: "report" | "new") => {
    const next = k === "report" ? formFrom(record) : formFrom(undefined);
    setKind(k); setTab("morning"); setF(next.f); setSyms(next.syms); setMoods(next.moods); setPvt(next.tap);
  };
  const hasPvt = report && num(record?.pvt_rt) !== null;

  const collect = (keys: string[]): Record<string, number | boolean | string[]> => {
    const out: Record<string, number | boolean | string[]> = {};
    for (const k of keys) {
      const raw = s(k);
      if (raw === undefined || raw === "") continue;
      const n = Number(raw);
      if (Number.isFinite(n)) out[k] = n;
    }
    return out;
  };

  const saveReport = () => {
    if (!record) return;
    // Replace this day's answers with the form; keep everything the form does not show (cabin, dose, phase…).
    const next: DayRecord = { ...record };
    for (const k of [...FORM_KEYS, ...SYM_KEYS, "tap_rt", "mood_labels"]) delete next[k];
    if (num(record.glucose_fasting) !== null) delete next.glucose;
    const entered = collect(FORM_KEYS);
    if (entered.glucose_fasting !== undefined) entered.glucose = entered.glucose_fasting;
    Object.assign(next, entered);
    for (const k of syms) next[k] = true;
    const other = (Array.isArray(record.mood_labels) ? record.mood_labels : []).filter((m) => !MOODS.includes(m));
    if (other.length + moods.length > 0) next.mood_labels = [...other, ...moods];
    if (pvt !== null) next.tap_rt = pvt;
    onSubmit(history.map((d, i) => (i === sel ? next : d)), sel);
  };

  const submit = () => {
    if (report) { saveReport(); return; }
    const last = history[history.length - 1];
    if (tab === "morning") {
      const entered: Record<string, number | boolean | string[]> = collect(["sleep_hours", "sleep_quality", "kss", "physical_state", ...VITALS.map((v) => v.key)]);
      if (entered.glucose_fasting !== undefined) entered.glucose = entered.glucose_fasting;
      for (const k of syms) entered[k] = true;
      if (pvt !== null) entered.tap_rt = pvt;
      const carried: Record<string, unknown> = {};
      for (const k of CARRY) if (last && last[k] !== undefined) carried[k] = last[k];
      const rec = { ...carried, ...entered, mission_day: (last?.mission_day ?? 0) + 1 } as DayRecord;
      onSubmit([...history, rec], history.length);
    } else {
      const entered: Record<string, number | boolean | string[]> = collect(["mood_valence", "team_cohesion", "workload", "fatigue", "exercise_min", "fluid_intake", "food_intake_pct"]);
      if (moods.length) entered.mood_labels = moods;
      for (const k of syms) entered[k] = true;
      // No day yet (a newly registered crew member): the evening answers start mission day 1.
      if (!last) { onSubmit([{ ...entered, mission_day: 1 } as DayRecord], 0); return; }
      onSubmit([...history.slice(0, -1), { ...last, ...entered } as DayRecord], history.length - 1);
    }
  };

  const morningNums = ["sleep_hours", ...VITALS.map((v) => v.key), ...(hasPvt ? ["pvt_rt"] : [])];
  // A report edits both parts of the day at once, so it checks and counts both tabs.
  const numericKeys = report ? [...morningNums, ...EVENING_NUMS] : tab === "morning" ? morningNums : EVENING_NUMS;
  const hasError = numericKeys.some((k) => rangeError(k, s(k)));
  const scaleKeys = report ? [...MORNING_SCALES, ...EVENING_SCALES] : tab === "morning" ? MORNING_SCALES : EVENING_SCALES;
  const extras = report ? (pvt !== null ? 1 : 0) + (moods.length > 0 ? 1 : 0) : tab === "morning" ? (pvt !== null ? 1 : 0) : (moods.length > 0 ? 1 : 0);
  const answered = [...numericKeys, ...scaleKeys].filter((k) => s(k) !== undefined && s(k) !== "").length + syms.length + extras;
  const hasInput = answered > 0;
  const canSubmit = (report || hasInput) && !hasError;
  const nextDay = (history[history.length - 1]?.mission_day ?? 0) + 1;
  const md = record?.mission_day;
  const note = report
    ? <>Mission day {md} as filed. Saving replaces that day's answers.{hasInput && <> · <b>{answered} answered</b></>}</>
    : <>{tab === "morning" || history.length === 0 ? `Adds mission day ${nextDay}` : `Updates mission day ${nextDay - 1}`}. Blank fields are not sent.{!hasInput ? " Enter at least one answer to submit." : <> · <b>{answered} answered</b></>}</>;
  const switcher = record && (
    <span className="ci-switch">
      {report ? "Already filed. " : ""}
      <button type="button" className="linkbtn" onClick={() => switchKind(report ? "new" : "report")}>
        {report ? `Start new day · MD ${nextDay}` : `Open MD ${md} report`}
      </button>
    </span>
  );
  return (
    <Modal title={report ? `Daily report · MD ${md}${who ? ` · ${who}` : ""}` : who ? `Daily check-in · ${who}` : "Daily check-in"}
      subtitle={<>{report ? "Morning and evening answers for this day. Change anything and save." : "About 2 minutes. Skip anything you can't measure."} {switcher}</>}
      onClose={onClose}
      footer={<>
        <span className="note">{note}</span>
        <span className="right"><button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button type="button" className="btn btn-primary" disabled={!canSubmit} onClick={submit}>{report ? "Save day" : "Submit"}</button></span>
      </>}>
      <div className="tabs" role="tablist" aria-label="Check-in part" style={{ marginBottom: 20 }}>
        <button role="tab" type="button" className="tab" aria-selected={tab === "morning"} onClick={() => { setTab("morning"); if (!report) setSyms([]); }}>Morning · body and sleep</button>
        <button role="tab" type="button" className="tab" aria-selected={tab === "evening"} onClick={() => { setTab("evening"); if (!report) setSyms([]); }}>Evening · mind and day</button>
      </div>

      {tab === "morning" ? (
        <div className="step">
          <div className="q"><h3 className="sr">Hours of sleep last night</h3>
            <NumField label="Hours of sleep" unit="h" value={s("sleep_hours")} onChange={set("sleep_hours")} step="0.1" min={0} max={24} error={rangeError("sleep_hours", s("sleep_hours"))} /></div>
          <div className="q"><h3>Sleep quality</h3>
            <Scale label="Sleep quality" min={1} max={5} value={s("sleep_quality")} onChange={set("sleep_quality")} lo="1 Very poor" hi="5 Very good" /></div>
          <div className="q"><h3>Sleepiness right now (KSS)</h3>
            <Scale label="Karolinska sleepiness" min={1} max={9} value={s("kss")} onChange={set("kss")} lo="1 Very alert" hi="9 Fighting sleep" /></div>
          <div className="q"><h3>How does your body feel?</h3>
            <Scale label="Physical state" min={1} max={7} value={s("physical_state")} onChange={set("physical_state")} lo="1 Very unwell" hi="7 Great" /></div>
          <div className="q"><h3>Any symptoms? <small>Tap all that apply</small></h3>
            <SymptomGroups selected={syms} onToggle={(k) => setSyms(toggle(syms, k))} /></div>
          <div className="q"><h3>Vitals <small>Enter only what you measured</small></h3>
            <div className="vgrid">
              {VITALS.filter((v) => v.key !== "bp_dia").map((v) => {
                if (v.key === "bp_sys") {
                  const err = rangeError("bp_sys", s("bp_sys")) ?? rangeError("bp_dia", s("bp_dia"));
                  return (
                    <div className="vfield" key="bp" role="group" aria-label="Blood pressure">
                      <b>Blood pressure</b>
                      <span className="vbox">
                        <input type="number" inputMode="decimal" step="any" aria-label="Systolic" placeholder="sys" min={RANGES.bp_sys[0]} max={RANGES.bp_sys[1]} aria-invalid={!!rangeError("bp_sys", s("bp_sys"))} value={s("bp_sys") ?? ""} onChange={(e) => set("bp_sys")(e.target.value)} />
                        <span className="slash">/</span>
                        <input type="number" inputMode="decimal" step="any" aria-label="Diastolic" placeholder="dia" min={RANGES.bp_dia[0]} max={RANGES.bp_dia[1]} aria-invalid={!!rangeError("bp_dia", s("bp_dia"))} value={s("bp_dia") ?? ""} onChange={(e) => set("bp_dia")(e.target.value)} />
                        <span className="unit">mmHg</span>
                      </span>
                      {err && <span className="field-err" role="alert">{err}</span>}
                      <span className="how">How: {v.how.replace("; top number.", ".")}</span>
                    </div>
                  );
                }
                const err = rangeError(v.key, s(v.key));
                return (
                  <label className="vfield" key={v.key}>
                    <b>{v.label}</b>
                    <span className="vbox"><input type="number" inputMode="decimal" step="any" min={RANGES[v.key][0]} max={RANGES[v.key][1]} aria-invalid={!!err} value={s(v.key) ?? ""} onChange={(e) => set(v.key)(e.target.value)} /><span className="unit">{v.unit}</span></span>
                    {err && <span className="field-err" role="alert">{v.key === "temp" ? "Temperature is in °C: enter 30 to 43 (98.6 °F is 37 °C)." : err}</span>}
                    <span className="how">How: {v.how}</span>
                  </label>
                );
              })}
            </div></div>
          {hasPvt && (
            <div className="q"><h3>Reaction time (onboard PVT)</h3>
              <NumField label="Mean reaction time" unit="ms" value={s("pvt_rt")} onChange={set("pvt_rt")} min={100} max={2000} error={rangeError("pvt_rt", s("pvt_rt"))} /></div>
          )}
          <ReactionGame result={pvt} onDone={setPvt} />
        </div>
      ) : (
        <div className="step">
          <div className="q"><h3>How have you felt overall today?</h3>
            <Scale label="Mood" min={1} max={7} value={s("mood_valence")} onChange={set("mood_valence")} lo="1 Very unpleasant" hi="7 Very pleasant" /></div>
          <div className="q"><h3>Mood words</h3>
            <Chips items={MOODS.map((m) => [m, m[0].toUpperCase() + m.slice(1)] as [string, string])} selected={moods} onToggle={(k) => setMoods(toggle(moods, k))} /></div>
          <div className="q"><h3>Team cohesion</h3>
            <Scale label="Team cohesion" min={1} max={5} value={s("team_cohesion")} onChange={set("team_cohesion")} lo="1 Strained" hi="5 Close" /></div>
          <div className="q"><h3>Workload today</h3>
            <Scale label="Workload" min={1} max={10} value={s("workload")} onChange={set("workload")} lo="1 Light" hi="10 Overwhelming" /></div>
          <div className="q"><h3>Fatigue</h3>
            <Scale label="Fatigue" min={1} max={7} value={s("fatigue")} onChange={set("fatigue")} lo="1 None" hi="7 Exhausted" /></div>
          <div className="q"><h3>Activity and intake</h3>
            <div className="vgrid">
            <NumField label="Exercise" unit="min" value={s("exercise_min")} onChange={set("exercise_min")} min={0} max={600} error={rangeError("exercise_min", s("exercise_min"))} />
            <NumField label="Fluid intake" unit="L" value={s("fluid_intake")} onChange={set("fluid_intake")} step="0.1" min={0} max={10} error={rangeError("fluid_intake", s("fluid_intake"))} />
            <NumField label="Food eaten" unit="% of plan" value={s("food_intake_pct")} onChange={set("food_intake_pct")} min={0} max={200} error={rangeError("food_intake_pct", s("food_intake_pct"))} /></div></div>
          <div className="q"><h3>{report ? "Symptoms" : "New symptoms"} <small>Tap all that apply</small></h3>
            <SymptomGroups selected={syms} onToggle={(k) => setSyms(toggle(syms, k))} /></div>
        </div>
      )}
    </Modal>
  );
}
