import type { Passport } from "../types";
import { DISCLAIMER } from "../levels";
import { NoData } from "./ui";

const STEPS: [string, string][] = [
  ["Register each crew member", "A one-minute passport: name, mission, five risk questions and what helps on a hard day."],
  ["Log a daily check-in for each", "Sleep, symptoms, vitals and a reaction test in the morning; mood and intake in the evening."],
  ["Watch the whole crew at once", "The roster shows every member's level for the selected day, with a 7-day strip."],
];

/** "My crew" mode with nobody registered yet. */
export function CrewSetup({ onAdd, onImport }: { onAdd: () => void; onImport: () => void }) {
  return (
    <div className="layout">
      <div className="area-hero">
        <section className="hero" aria-labelledby="setupTitle">
          <p className="hero-eyebrow"><span>My crew</span><span>Stored only in this browser</span></p>
          <h1 id="setupTitle">Register your crew</h1>
          <p className="sub">Add every crew member yourself, then run their daily check-ins. The same rule engine as the demo
            assesses each person and the roster shows the whole crew.</p>
          <ol className="setup-steps">
            {STEPS.map(([t, d], i) => (
              <li key={t}><span className="mono">{String(i + 1).padStart(2, "0")}</span><div><b>{t}</b><span>{d}</span></div></li>
            ))}
          </ol>
          <p className="disclaimer"><b>{DISCLAIMER}</b></p>
        </section>
      </div>
      <div className="area-cta">
        <button type="button" className="cta cta-primary" onClick={onAdd}>
          <b>Register first crew member</b><span>About a minute per person</span>
        </button>
        <button type="button" className="btn btn-secondary cta-2" onClick={onImport}>Import from file · passport, check-ins or a crew backup</button>
        <p className="muted setup-note">New members have no six-month passport: rules compare with population baselines until
          7 days of their own check-ins exist, then with their own median.</p>
      </div>
    </div>
  );
}

/** A registered crew member with no check-in yet: nothing to assess, so say so and offer the first check-in. */
export function FirstCheckIn({ passport, onCheckIn, onPassport, onImport }: { passport: Passport; onCheckIn: () => void; onPassport: () => void; onImport?: () => void }) {
  const name = passport.astronaut.name;
  return (
    <div className="layout">
      <div className="area-hero">
        <section className="hero" aria-labelledby="firstTitle">
          <p className="hero-eyebrow">
            <span className="lvword lv-na"><NoData />Not assessed · no data yet</span>
            <span>{passport.astronaut.role} · {passport.astronaut.id}</span>
          </p>
          <h1 id="firstTitle">No check-ins yet for {name}</h1>
          <p className="sub">Start {name}'s first daily check-in. {passport.passport_ref
            ? `The rules compare with ${name}'s six-month passport baselines, then with the median of the check-ins once 7 days exist.`
            : `Until 7 days exist the rules compare with population baselines, then with ${name}'s own median.`}</p>
          <p className="disclaimer"><b>{DISCLAIMER}</b></p>
        </section>
      </div>
      <div className="area-cta">
        <button type="button" className="cta cta-primary" onClick={onCheckIn}>
          <b>Start first daily check-in</b><span>2 minutes · morning and evening</span>
        </button>
        <button type="button" className="btn btn-secondary cta-2" onClick={onPassport}>Passport · {passport.modifiers.length} modifier{passport.modifiers.length === 1 ? "" : "s"}</button>
        {onImport && <button type="button" className="btn btn-secondary cta-2" onClick={onImport}>Import check-in history or six-month data</button>}
      </div>
    </div>
  );
}
