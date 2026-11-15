export type Level = "GREEN" | "YELLOW" | "ORANGE" | "RED";

export interface ScenarioInfo { id: string; title: string; description: string; days: number; crew_size?: number }

export type DayRecord = { mission_day: number; [key: string]: number | string | boolean | string[] | null | undefined; comm_los?: boolean };

export interface PreflightSession { id: string; when: string; what: string; how: string; feeds: string[]; source: string }

export interface Range { lo: number | null; hi: number | null; n?: number; ready?: boolean; rebase14?: number | null }

export interface Passport {
  astronaut: { id: string; name: string; role: string; sex?: string; age?: number };
  mission: { profile: string; vehicle: string; comm_delay_s: number };
  baselines: Record<string, number>;
  baselines_source?: string;
  personal_ranges?: Record<string, Range>;
  lab_ranges?: Record<string, Range>;
  passport_ref?: string | null;
  modifiers: string[];
  countermeasures: string[];
  preflight?: PreflightSession[];
}

/** passport_doc: six-month data imported from a file ("My crew"); its passport_ref is "local:<id>@<stamp>". */
export interface CrewMember { passport: Passport; history: DayRecord[]; passport_doc?: PassportDoc }
/** What happens on one mission day of the demo story (dock caption). */
export interface StoryDay { mission_day: number; title: string; detail: string; crew: string[] }
export interface Scenario extends ScenarioInfo { passport: Passport; history: DayRecord[]; crew?: CrewMember[]; story?: StoryDay[] }

export interface Action { id: string; text: string; who: string }
export interface TraceEntry {
  rule: string;
  label: string;
  facts: Record<string, unknown>;
  cf: number;
  source: { key: string; title: string; url: string | null };
}
export interface Hypothesis {
  id: string;
  name: string;
  system: string;
  cf: number;
  level: Level;
  expected: boolean;
  trace: TraceEntry[];
  actions: Action[];
  incidence?: { value: number; unit: string; ref: string; name: string } | null;
}
export interface Escalation { rule: string; label: string; level: Level; system: string; actions: Action[] }
export interface Assessment {
  overall_level: Level;
  systems: Record<string, Level>;
  hypotheses: Hypothesis[];
  escalations: Escalation[];
  pending: { rule: string; missing: string[] }[];
  next_measurement: { fact: string; label: string; reason: string } | null;
  news2: { total: number; params: Record<string, unknown>; max: number; missing: string[] };
  packet: string | null;
}

export interface KnowledgeCounts { conditions: number; actions: number; references: number; rules: number }

export interface QuizAnswers {
  id?: string;
  name?: string;
  role?: string;
  mission_profile?: "leo" | "lunar" | "mars";
  prior_motion_sickness?: boolean;
  kidney_stone?: boolean;
  sans_risk_or_vision_change?: boolean;
  migraine?: boolean;
  poor_sleeper?: boolean;
  helpers?: string[];
  baselines?: Record<string, number>;
  /** Registered in the "My crew" mode: no six-month passport, population baselines. */
  new_member?: boolean;
  /** Keep this member's six-month passport when the quiz edits an existing member. */
  passport_ref?: string | null;
}

export type AppMode = "demo" | "crew";

/* ---- six-month passport and data catalogue (data pipeline) ---- */
export type ProvCode = "RA" | "RG" | "RP" | "SC" | "AU" | "IM";
export interface PassportField {
  field_id: string; field_label: string; metric: string; label: string; value: number | string | null; unit: string;
  lo: number | null; hi: number | null; n: number; completeness: number | null; readiness: "ready" | "partial" | "missing";
  rebase14: number | null; trend_per_30d: number | null; method: string; provenance: string; source_ids: string;
}
export interface PassportSession {
  session_id: string; t: number; title: string; status: string; provenance: string; source_ids: string;
  values: Record<string, number | string>;
}
export interface PassportDoc {
  crew_id: string; name: string; role: string; sex: string; age: number | null; modifiers: string[];
  window: { start: number; end: number };
  provenance_codes: Partial<Record<ProvCode, string>>;
  donors: { field_group: string; donor_subject_id: string; source_id: string; note: string }[];
  fields: PassportField[];
  sessions: PassportSession[];
  series: Record<string, [number, number, ProvCode][]>;
  /** Set when the passport was imported from a file. */
  import?: { filename: string; used: number; first: number; last: number; launch_date: string | null; lab_ref_fallback: string[] };
}

/* ---- import into "My crew" (POST /api/import/parse) ---- */
export interface EngineInputs {
  baselines: Record<string, number>; personal_ranges: Record<string, Range>; lab_ranges: Record<string, Range>;
  baselines_source: string;
}
export interface ImportReport {
  rows: number; used: number; skipped: { line: number; reason: string }[]; skipped_count: number;
  metrics: { metric: string; label: string; unit: string; n: number; first: number; last: number; target: "passport" | "check-ins" }[];
  unknown: string[]; converted: string[]; outside_window: number; duplicates: number; history_days: number;
  history_truncated?: number; layout: string; dates: boolean; launch_date: string | null;
}
export interface ImportResult {
  kind: "table" | "passport";
  name: string; role: string; sex: string; age: number | null; modifiers: string[];
  passport_doc: PassportDoc | null; engine: EngineInputs | null; history: DayRecord[]; report: ImportReport;
}
export interface CrewBackup { format: "asclepius-crew"; version: 1; exported_at: string; members: CrewMember[] }
export interface DataSource {
  id: string; title: string; url: string; license: string; access: string; kind: string; status: string;
  citation?: string; rows: Record<string, number>;
}
export interface DatasetsSummary {
  sources: DataSource[]; crew: string[]; crew_observations_by_provenance: Record<string, number>;
}

export interface BiodoseSample {
  sample: string; volunteer: number; dose_gy: number; hours: number; bucket: string; predicted_held_out: string;
  fold_changes: Record<string, number>;
}
export interface BiodoseModel {
  genes: string[]; top_genes: string[]; n_samples: number; volunteers: number; loocv_accuracy: number;
  confusion: Record<string, number>; samples: BiodoseSample[];
}
