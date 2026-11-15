import type { Assessment, Level } from "./types";

export const LEVEL_ORDER: Level[] = ["GREEN", "YELLOW", "ORANGE", "RED"];
export const levelRank = (l: Level) => LEVEL_ORDER.indexOf(l);
export const worst = (levels: Level[]): Level =>
  levels.reduce<Level>((a, b) => (levelRank(b) > levelRank(a) ? b : a), "GREEN");
export const lvClass = (l: Level) => `lv-${l.toLowerCase()}`;
export const bgClass = (l: Level) => `bg-${l.toLowerCase()}`;

export const LEVEL_MEANING: Record<Level, string> = {
  GREEN: "Nominal",
  YELLOW: "Self-care",
  ORANGE: "Re-measure · tell CMO",
  RED: "Call flight surgeon",
};
export const LEVEL_ADVICE: Record<Level, string> = {
  GREEN: "No action needed for the findings shown",
  YELLOW: "Self-care actions suggested",
  ORANGE: "Tell the crew medical officer",
  RED: "Contact the flight surgeon now",
};

export type RegionId =
  | "cardio" | "msk" | "neuro_ocular" | "vestibular" | "immune"
  | "behavioral" | "sleep" | "nutrition" | "radiation";

export interface Region {
  id: RegionId;
  name: string;
  fn: string;
  systems: string[];
  /** marker position on the 400x500 body figure and the callout side/y */
  mx: number; my: number; side: "L" | "R"; cy: number;
}

export const REGIONS: Region[] = [
  { id: "vestibular", name: "Vestibular", fn: "Balance and spatial orientation (inner ear).", systems: ["VEST"], mx: 172, my: 62, side: "L", cy: 60 },
  { id: "sleep", name: "Sleep", fn: "Sleep duration, quality and alertness.", systems: ["SLEEP"], mx: 184, my: 100, side: "L", cy: 112 },
  { id: "cardio", name: "Heart and lungs", fn: "Heart, blood pressure, breathing and oxygenation.", systems: ["CV", "RESP"], mx: 188, my: 150, side: "L", cy: 160 },
  { id: "nutrition", name: "Nutrition and GI", fn: "Food, fluids, digestion and kidneys/urinary tract.", systems: ["NUTR", "GI", "GU"], mx: 200, my: 238, side: "L", cy: 250 },
  { id: "msk", name: "Musculoskeletal", fn: "Muscles, bones, joints, injuries and EVA strain.", systems: ["MSK", "TRAUMA", "EVA"], mx: 177, my: 350, side: "L", cy: 350 },
  { id: "neuro_ocular", name: "Neuro and senses", fn: "Brain, vision, ears and teeth.", systems: ["NEURO", "EYE", "ENT", "DENT"], mx: 200, my: 40, side: "R", cy: 40 },
  { id: "behavioral", name: "Mind and mood", fn: "Mood, stress, cohesion and cognitive workload.", systems: ["BEHAV"], mx: 214, my: 72, side: "R", cy: 90 },
  { id: "immune", name: "Immune and skin", fn: "Infection defence, allergy, skin and wounds.", systems: ["IMMUNE", "SKIN"], mx: 228, my: 128, side: "R", cy: 140 },
  { id: "radiation", name: "Radiation", fn: "Cumulative dose and solar particle events.", systems: ["RAD"], mx: 212, my: 205, side: "R", cy: 205 },
];

/** Level of a region, or null when the engine returned nothing for it (not assessed / still loading). */
export function regionLevel(a: Assessment | null, r: Region): Level | null {
  if (!a) return null;
  const levels = r.systems.map((s) => a.systems[s]).filter((l): l is Level => !!l);
  return levels.length ? worst(levels) : null;
}

export const DISCLAIMER = "Decision support for crew self-assessment - not a medical diagnosis.";
export const NO_FINDINGS = "No findings from today's data";
export const NO_RULE_FIRED = "No rule fired on today's data";

export const MODIFIER_TEXT: Record<string, string> = {
  "P-01": "Motion sickness confidence +15%",
  "P-02": "Flank pain escalates to RED",
  "P-03": "Earlier near-vision checks, SANS confidence +10%",
  "P-05": "Personal migraine plan",
  "P-10": "Sleep deficit after 2 nights",
};

export function formatDelay(s: number | undefined | null): string {
  if (s == null || Number.isNaN(s)) return "n/a";
  if (s < 60) return `${Number.isInteger(s) ? s : s.toFixed(1)} s`;
  const m = Math.floor(s / 60);
  const r = Math.round(s - m * 60);
  return r ? `${m} min ${r} s` : `${m} min`;
}

// Display-only context thresholds (not triage; triage comes from the rule engine).
/** Cabin CO2 1-h average limit, mmHg: NASA-STD-3001 Vol 2 / OCHMO TB-004. */
export const CO2_LIMIT_MMHG = 3.0;
/** Career radiation dose limit, mSv: NASA-STD-3001 Vol 1. */
export const CAREER_DOSE_LIMIT_MSV = 600;
/** Fraction of the career limit at which the dose tile shows a watch flag: NASA-STD-3001 Vol 1. */
export const CAREER_DOSE_WATCH_FRACTION = 0.8;

/** Title-case level word for badges ("Red"), per design system v4. */
export const LEVEL_WORD: Record<Level, string> = { GREEN: "Green", YELLOW: "Yellow", ORANGE: "Orange", RED: "Red" };

/** Who does an action step. The knowledge base stores owners as emoji (actions.yaml `who`). */
export const OWNER: Record<string, string> = {
  "🧑‍🚀": "You", "👥": "Crewmate", "🩺": "Crew medical officer", "🌍": "Ground",
};
const OWNER_ORDER = ["🧑‍🚀", "👥", "🩺", "🌍"];
const ownerParts = (who: string) => who.trim().split(/\s+/).filter(Boolean);
export const ownerLabel = (who: string) => ownerParts(who).map((w) => OWNER[w] ?? w).join(" · ") || "-";
/** First owner glyph, for the small owner tile. */
export const ownerIcon = (who: string) => ownerParts(who)[0] ?? "";
/** Steps handled on board (anyone but Ground alone). */
export const isGroundOnly = (who: string) => { const p = ownerParts(who); return p.length > 0 && p.every((w) => w === "🌍"); };
export const ownerRank = (who: string) => { const i = OWNER_ORDER.indexOf(ownerParts(who)[0] ?? ""); return i < 0 ? 9 : i; };

/** One-way delay (s) above which onboard steps come first (backend packet.py LONG_DELAY_S). */
export const LONG_DELAY_S = 300;

/** Day-record fields shown as "Today vs your baseline" in a body-system drawer. Rows render only when the field exists in the history. */
export interface RegionMetric { key: string; label: string; unit: string; digits?: number }
export const REGION_METRICS: Record<RegionId, RegionMetric[]> = {
  radiation: [
    { key: "dose_today", label: "Dose today", unit: "mSv", digits: 2 },
    { key: "lymphocytes_abs", label: "Lymphocytes", unit: "/µL" },
    { key: "dose_cumulative", label: "Career dose", unit: "mSv", digits: 1 },
  ],
  cardio: [
    { key: "hr_rest", label: "Resting heart rate", unit: "bpm" },
    { key: "bp_sys", label: "Systolic blood pressure", unit: "mmHg" },
    { key: "spo2", label: "SpO2", unit: "%" },
    { key: "hrv_rmssd", label: "Heart-rate variability", unit: "ms" },
  ],
  sleep: [
    { key: "sleep_hours", label: "Sleep", unit: "h", digits: 1 },
    { key: "kss", label: "Sleepiness (KSS)", unit: "/ 9" },
    { key: "sleep_quality", label: "Sleep quality", unit: "/ 5" },
  ],
  behavioral: [
    { key: "mood_valence", label: "Mood", unit: "/ 7" },
    { key: "workload", label: "Workload", unit: "/ 10" },
    { key: "team_cohesion", label: "Team cohesion", unit: "/ 5" },
  ],
  vestibular: [
    { key: "pvt_rt", label: "Reaction time (PVT)", unit: "ms" },
    { key: "tap_rt", label: "Tap reaction test", unit: "ms" },
  ],
  neuro_ocular: [
    { key: "co2_1h", label: "Cabin CO2 1-h", unit: "mmHg", digits: 1 },
    { key: "co2_7d", label: "Cabin CO2 7-day", unit: "mmHg", digits: 1 },
  ],
  nutrition: [
    { key: "glucose", label: "Glucose", unit: "mg/dL" },
    { key: "fluid_intake", label: "Fluid intake", unit: "L", digits: 1 },
    { key: "food_intake_pct", label: "Food eaten", unit: "% of plan" },
  ],
  immune: [
    { key: "temp", label: "Temperature", unit: "°C", digits: 1 },
  ],
  msk: [
    { key: "exercise_min", label: "Exercise", unit: "min" },
  ],
};
