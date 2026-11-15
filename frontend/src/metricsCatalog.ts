import type { PassportDoc, PassportField, ProvCode } from "./types";
import { CO2_LIMIT_MMHG } from "./levels";

/** Groups for the passport charts tab and the Health dynamics window, in display order. */
export type GroupId = "vitals" | "sleep" | "mind" | "body" | "labs" | "env" | "micro";
export const GROUPS: { id: GroupId; label: string }[] = [
  { id: "vitals", label: "Heart and vitals" },
  { id: "sleep", label: "Sleep and alertness" },
  { id: "mind", label: "Mind and mood" },
  { id: "body", label: "Body and activity" },
  { id: "labs", label: "Blood and labs" },
  { id: "env", label: "Environment and radiation" },
  { id: "micro", label: "Microbiome" },
];

export interface MetricDef {
  /** Day-record key when the metric is recorded in flight, otherwise the passport series key. */
  key: string;
  group: GroupId;
  /** Label/unit for keys the six-month passport does not describe (flight-only keys) or should read like the console. */
  label?: string;
  unit?: string;
  /** Passport daily series key when it differs from `key`. */
  pre?: string;
  /** Passport session value (one-off exams) used when there is no daily series, e.g. clinic blood pressure. */
  session?: string;
  digits?: number;
  /** Display-only context line (not triage). */
  thr?: { value: number; label: string };
  /** Recorded on mission days (scenarios, check-ins). */
  flight?: boolean;
}

/** Every metric the charts know, in display order within each group. */
export const METRICS: MetricDef[] = [
  // heart and vitals
  { key: "hr_rest", group: "vitals", label: "Resting heart rate", unit: "bpm", digits: 0, flight: true },
  { key: "hrv_rmssd", group: "vitals", label: "Heart-rate variability (RMSSD)", unit: "ms", digits: 1, flight: true },
  { key: "bp_sys", group: "vitals", label: "Systolic blood pressure", unit: "mmHg", session: "bp_sys", digits: 0, flight: true },
  { key: "bp_dia", group: "vitals", label: "Diastolic blood pressure", unit: "mmHg", session: "bp_dia", digits: 0, flight: true },
  { key: "spo2", group: "vitals", label: "SpO₂", unit: "%", digits: 0, flight: true },
  { key: "temp", group: "vitals", label: "Body temperature", unit: "°C", session: "temp_oral", digits: 1, flight: true },
  { key: "skin_temp_dev", group: "vitals", digits: 2 },
  // sleep and alertness
  { key: "sleep_hours", group: "sleep", label: "Sleep duration", unit: "h", digits: 1, flight: true, thr: { value: 6, label: "6 h threshold" } },
  { key: "sleep_efficiency", group: "sleep", digits: 0 },
  { key: "sleep_quality", group: "sleep", label: "Sleep quality", unit: "1-5", digits: 0, flight: true },
  { key: "kss", group: "sleep", label: "Sleepiness (KSS)", unit: "1-9", digits: 0, flight: true },
  { key: "fatigue", group: "sleep", label: "Fatigue", unit: "1-7", digits: 0, flight: true },
  { key: "pvt_rt", group: "sleep", label: "Reaction time (PVT)", unit: "ms", digits: 0, flight: true },
  { key: "tap_rt", group: "sleep", label: "Tap reaction test", unit: "ms", digits: 0, flight: true },
  // mind and mood
  { key: "mood_valence", group: "mind", label: "Mood", unit: "1-7", digits: 0, flight: true },
  { key: "workload", group: "mind", label: "Workload", unit: "0-10", digits: 0, flight: true },
  { key: "team_cohesion", group: "mind", label: "Team cohesion", unit: "1-5", digits: 0, flight: true },
  { key: "physical_state", group: "mind", label: "Physical state", unit: "1-7", digits: 0, flight: true },
  { key: "stress_score", group: "mind", digits: 0 },
  { key: "phq9", group: "mind", digits: 0 },
  { key: "gad7", group: "mind", digits: 0 },
  { key: "pss", group: "mind", digits: 0 },
  { key: "who5", group: "mind", digits: 0 },
  { key: "ucla3", group: "mind", digits: 0 },
  { key: "stai_state", group: "mind", digits: 0 },
  // body and activity
  { key: "steps", group: "body", digits: 0 },
  { key: "body_mass", group: "body", label: "Body mass", unit: "kg", digits: 1 },
  { key: "near_acuity_logmar", group: "body", digits: 2 },
  { key: "exercise_min", group: "body", label: "Exercise", unit: "min", digits: 0, flight: true },
  { key: "fluid_intake", group: "body", label: "Fluid intake", unit: "L", digits: 1, flight: true },
  { key: "food_intake_pct", group: "body", label: "Food eaten", unit: "% of plan", digits: 0, flight: true },
  // blood and labs
  { key: "lymphocytes_abs", group: "labs", label: "Lymphocytes (absolute)", unit: "cells/µL", digits: 0, flight: true },
  { key: "hemoglobin", group: "labs", label: "Hemoglobin", unit: "g/dL", digits: 1 },
  { key: "glucose", group: "labs", label: "Glucose", unit: "mg/dL", digits: 0, flight: true },
  { key: "wbc", group: "labs", digits: 1 },
  { key: "neutrophils_abs", group: "labs", digits: 0 },
  { key: "hematocrit", group: "labs", digits: 1 },
  { key: "platelets", group: "labs", digits: 0 },
  { key: "sodium", group: "labs", digits: 0 },
  { key: "potassium", group: "labs", digits: 1 },
  { key: "calcium", group: "labs", digits: 1 },
  { key: "creatinine", group: "labs", digits: 2 },
  { key: "egfr", group: "labs", digits: 0 },
  { key: "bun", group: "labs", digits: 0 },
  { key: "albumin", group: "labs", digits: 1 },
  { key: "alt", group: "labs", digits: 0 },
  { key: "ast", group: "labs", digits: 0 },
  { key: "crp", group: "labs", digits: 2 },
  // environment and radiation (mission days only)
  { key: "co2_1h", group: "env", label: "Cabin CO₂, 1-h average", unit: "mmHg", digits: 1, flight: true,
    thr: { value: CO2_LIMIT_MMHG, label: `${CO2_LIMIT_MMHG.toFixed(1)} mmHg limit (NASA-STD-3001)` } },
  { key: "co2_7d", group: "env", label: "Cabin CO₂, 7-day average", unit: "mmHg", digits: 1, flight: true },
  { key: "dose_today", group: "env", label: "Radiation dose today", unit: "mSv", digits: 2, flight: true },
  { key: "dose_cumulative", group: "env", label: "Career radiation dose", unit: "mSv", digits: 1, flight: true },
  // microbiome
  { key: "microbiome_oral", group: "micro", digits: 2 },
  { key: "microbiome_nasal", group: "micro", digits: 2 },
  { key: "microbiome_skin_arm", group: "micro", digits: 2 },
  { key: "microbiome_skin_forehead", group: "micro", digits: 2 },
];

const BY_KEY = new Map(METRICS.map((m) => [m.key, m]));
/** Passport series key -> metric (e.g. temp_oral -> temp). */
const BY_PRE = new Map(METRICS.map((m) => [m.pre ?? m.session ?? m.key, m]));

export const metricDef = (key: string): MetricDef =>
  BY_KEY.get(key) ?? BY_PRE.get(key) ?? { key, group: "body", digits: 2 };
export const preKey = (m: MetricDef) => m.pre ?? m.key;

/** Passport field describing a metric (label, unit, value, range). Sleep prefers H1 (the daily stream). */
export function fieldFor(doc: PassportDoc | null | undefined, key: string): PassportField | undefined {
  if (!doc) return undefined;
  const rows = doc.fields.filter((f) => f.metric === key && f.readiness !== "missing");
  return rows.find((f) => f.lo !== null && f.hi !== null) ?? rows[0];
}

export function prettyUnit(u: string | undefined | null): string {
  if (!u) return "";
  return u.replace(/\buL\b/g, "µL").replace(/^um$/, "µm").replace("degC", "°C").replace("10^3", "10³")
    .replace("1.73m2", "1.73 m²").replace("g/cm2", "g/cm²").replace(/^(\d+)–(\d+)$/, "$1-$2");
}

export function metricLabel(m: MetricDef, doc?: PassportDoc | null): string {
  const f = fieldFor(doc, preKey(m)) ?? (m.session ? fieldFor(doc, m.session) : undefined);
  return m.label ?? f?.label ?? m.key;
}
export function metricUnit(m: MetricDef, doc?: PassportDoc | null): string {
  const f = fieldFor(doc, preKey(m)) ?? (m.session ? fieldFor(doc, m.session) : undefined);
  return prettyUnit(m.unit ?? f?.unit);
}

/** A unit that is a score range ("1-7") reads as "/ 7" next to a value. */
export function withUnit(v: number | null | undefined, m: MetricDef, unit: string): string {
  if (v === null || v === undefined || !Number.isFinite(v)) return "-";
  const s = v.toFixed(m.digits ?? 2);
  if (!unit) return s;
  const scale = unit.match(/^\d+-(\d+)$/);
  return scale ? `${s} / ${scale[1]}` : `${s} ${unit}`;
}

export const PROV_BY_NAME: Record<string, ProvCode> = {
  "real-astronaut": "RA", "real-ground": "RG", "real-population": "RP", "synthetic-calibrated": "SC", authored: "AU", imported: "IM",
};
/** First provenance of a ";"-joined list; calibrated model when unknown. */
export const provOf = (provenance: string): ProvCode =>
  provenance.split(";").map((p) => PROV_BY_NAME[p]).find(Boolean) ?? "SC";
