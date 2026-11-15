import { useState } from "react";
import type { Passport, QuizAnswers } from "../types";
import { MODIFIER_TEXT } from "../levels";
import { derivePassport, isLocalRef } from "../api";
import { Modal } from "./ui";

/** Modifiers the quiz asks about (backend passport.py _MODIFIER_ANSWERS). */
const QUIZ_MODIFIERS = ["P-01", "P-02", "P-03", "P-05", "P-10"];
const HELPERS = ["music", "exercise", "call family", "journaling", "Earth photos", "plants / gardening", "time alone", "talk to a crewmate"];

export function ModifierList({ passport }: { passport: Passport }) {
  if (!passport.modifiers.length) return <p className="muted">No personal modifiers active.</p>;
  return (
    <ul className="mods">
      {passport.modifiers.map((m) => <li key={m}><code>{m}</code>{MODIFIER_TEXT[m] ?? "Personal rule adjustment"}</li>)}
    </ul>
  );
}

/** NASA reference schedule of pre-flight baseline sessions (what each one feeds in the passport). */
export function PreflightTimeline({ passport }: { passport: Passport }) {
  if (!passport.preflight?.length) return null;
  return (
    <details className="preflight">
      <summary>Pre-flight baseline timeline ({passport.preflight.length} sessions)</summary>
      <p className="muted" style={{ fontSize: 12.5, margin: "6px 0" }}>NASA reference schedule; timings vary by mission.</p>
      <ol>
        {passport.preflight.map((s) => (
          <li key={s.id}>
            <b>{s.when}</b> → {s.what}
            <span className="muted"> → feeds: {s.feeds.join(", ")} · <code>{s.source}</code></span>
          </li>
        ))}
      </ol>
    </details>
  );
}

function YesNo({ title, hint, value, onChange }: { title: string; hint?: string; value: boolean; onChange: (v: boolean) => void }) {
  return (
    <div className="q"><h3>{title}</h3>{hint && <p className="hint">{hint}</p>}
      <div className="yn" role="group" aria-label={title}>
        <button type="button" aria-pressed={value} onClick={() => onChange(true)}>Yes</button>
        <button type="button" aria-pressed={!value} onClick={() => onChange(false)}>No</button>
      </div></div>
  );
}

/**
 * Passport quiz. "edit" changes the given member and keeps their own six-month passport (passport_ref);
 * "add" registers a new crew member ("My crew" mode) with no six-month passport yet.
 * In "add" mode `passport` is a template (another crew member) whose mission the new member shares.
 */
export function PassportQuiz({ passport, mode = "edit", newId, onDone, onClose }: {
  passport: Passport | null; mode?: "edit" | "add"; newId?: string; onDone: (p: Passport) => void; onClose: () => void;
}) {
  const adding = mode === "add";
  const where = passport ? passport.mission.profile + passport.mission.vehicle : "";
  // "low earth" also matches crews saved before the generic names (vehicle "… (low Earth orbit)").
  const initialProfile: "leo" | "lunar" | "mars" = !passport ? "leo" : /low earth|orbital station/i.test(where) ? "leo" : /lun/i.test(where) ? "lunar" : "mars";
  const has = (code: string) => !adding && !!passport?.modifiers.includes(code);
  const [a, setA] = useState<QuizAnswers>({
    id: adding ? newId : passport?.astronaut.id, baselines: adding ? undefined : passport?.baselines,
    name: adding ? "" : passport?.astronaut.name, role: adding ? "" : passport?.astronaut.role, mission_profile: initialProfile,
    prior_motion_sickness: has("P-01"), kidney_stone: has("P-02"),
    sans_risk_or_vision_change: has("P-03"), migraine: has("P-05"),
    poor_sleeper: has("P-10"), helpers: adding ? [] : passport?.countermeasures ?? [],
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [preview, setPreview] = useState<Passport | null>(null);
  const up = (p: Partial<QuizAnswers>) => setA((x) => ({ ...x, ...p }));
  const helpers = a.helpers ?? [];
  const nameMissing = adding && !(a.name ?? "").trim();

  const submit = async () => {
    setBusy(true); setErr(null);
    try {
      // Members without a six-month passport (registered here) stay that way; others keep their own passport.
      // Imported six-month data lives in this browser only: the server derives population defaults and the
      // member's own ranges are put back below.
      const imported = !adding && isLocalRef(passport?.passport_ref);
      const own = adding || imported || !passport?.passport_ref ? { new_member: true } : { passport_ref: passport.passport_ref };
      const derived = await derivePassport({ ...a, name: (a.name ?? "").trim() || undefined, ...own });
      const astronaut = !adding && passport ? { ...passport.astronaut, ...derived.astronaut } : derived.astronaut;
      // The quiz asks about five modifiers only; an edit keeps the member's other modifiers (e.g. P-15).
      const kept = !adding && passport ? passport.modifiers.filter((m) => !QUIZ_MODIFIERS.includes(m)) : [];
      const keepImport = imported && passport ? { personal_ranges: passport.personal_ranges, lab_ranges: passport.lab_ranges,
        baselines_source: passport.baselines_source, passport_ref: passport.passport_ref } : {};
      const merged = { ...derived, ...keepImport, astronaut, modifiers: [...derived.modifiers, ...kept] };
      // Keep the crew's own mission block when the profile was not changed.
      setPreview(passport && a.mission_profile === initialProfile ? { ...merged, mission: passport.mission } : merged);
    } catch (e) { setErr(e instanceof Error ? e.message : String(e)); }
    setBusy(false);
  };

  return (
    <Modal title={preview ? "Passport preview" : adding ? "Register crew member" : "Personal passport"}
      subtitle={preview ? "Check the modifiers, then apply." : adding ? "Six questions, about a minute. No six-month passport yet: baselines learn from 7 days of check-ins." : "Six questions, about a minute"} onClose={onClose}
      footer={preview ? (
        <><button type="button" className="btn btn-secondary" onClick={() => setPreview(null)}>Back</button>
          <span className="right"><button type="button" className="btn btn-primary" onClick={() => onDone(preview)}>{adding ? "Add to crew" : "Apply passport"}</button></span></>
      ) : (
        <><span className="note">{nameMissing ? "Enter a name to continue · " : ""}{[a.prior_motion_sickness, a.kidney_stone, a.migraine, a.poor_sleeper, a.sans_risk_or_vision_change].filter(Boolean).length} of 5 risk questions answered “yes” · {helpers.length} helper{helpers.length === 1 ? "" : "s"}</span>
          <span className="right"><button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
            <button type="button" className="btn btn-primary" disabled={busy || nameMissing} onClick={submit}>{busy ? "Working…" : "Build passport"}</button></span></>
      )}>
      {err && <div className="banner" role="alert"><div><b>Could not derive passport.</b> {err}</div></div>}
      {preview ? (
        <div className="step">
          <div className="q"><h3>{preview.astronaut.name} · {preview.astronaut.role}</h3>
            <p className="hint">{preview.mission.vehicle}{adding ? ` · ${preview.astronaut.id}` : ""}</p></div>
          {adding && <div className="q"><h3>Baselines</h3><p className="hint">{preview.baselines_source}</p></div>}
          <div className="q"><h3>Active modifiers</h3><ModifierList passport={preview} /></div>
        </div>
      ) : (
        <div className="step">
          <div className="q"><h3>1. Who are you and where are you flying?</h3>
            <div className="field-row">
              <label className="field"><span>Name{adding ? " (required)" : ""}</span><input className="txt" value={a.name ?? ""} maxLength={100} autoFocus={adding} aria-required={adding} onChange={(e) => up({ name: e.target.value })} /></label>
              <label className="field"><span>Role</span><input className="txt" value={a.role ?? ""} maxLength={100} placeholder={adding ? "Mission Specialist" : undefined} onChange={(e) => up({ role: e.target.value })} /></label>
            </div>
            <span className="field"><span>Mission profile</span></span>
            <div className="yn" role="group" aria-label="Mission profile">
              {([["leo", "Low Earth orbit"], ["lunar", "Lunar"], ["mars", "Mars"]] as const).map(([k, l]) => (
                <button key={k} type="button" aria-pressed={a.mission_profile === k} onClick={() => up({ mission_profile: k })}>{l}</button>
              ))}
            </div></div>
          <YesNo title="2. Have you had motion sickness (car, sea, flight)?" value={!!a.prior_motion_sickness} onChange={(v) => up({ prior_motion_sickness: v })} />
          <YesNo title="3. Have you ever had a kidney stone?" value={!!a.kidney_stone} onChange={(v) => up({ kidney_stone: v })} />
          <YesNo title="4. Do you get migraines?" value={!!a.migraine} onChange={(v) => up({ migraine: v })} />
          <YesNo title="5. Would you call yourself a poor sleeper?" value={!!a.poor_sleeper} onChange={(v) => up({ poor_sleeper: v })} />
          <YesNo title="6. Any vision change before, or a SANS risk flag?" value={!!a.sans_risk_or_vision_change} onChange={(v) => up({ sans_risk_or_vision_change: v })} />
          <div className="q"><h3>What helps you on a hard day? <small>Optional</small></h3>
            <div className="chips">
              {HELPERS.map((h) => (
                <button key={h} type="button" aria-pressed={helpers.includes(h)}
                  onClick={() => up({ helpers: helpers.includes(h) ? helpers.filter((x) => x !== h) : [...helpers, h] })}>{h}</button>
              ))}
            </div></div>
        </div>
      )}
    </Modal>
  );
}
