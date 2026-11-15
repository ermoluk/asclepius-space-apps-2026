import { isLocalRef, localRef, setLocalPassport } from "./api";
import type { AppMode, CrewBackup, CrewMember, PassportDoc } from "./types";

/** "My crew" mode: crew members you register yourself, kept only in this browser (localStorage). */
const CREW_KEY = "chc.myCrew.v1";
const MODE_KEY = "chc.mode";
const BACKUP_FORMAT = "asclepius-crew";

const isDoc = (d: unknown): d is PassportDoc => {
  const x = d as PassportDoc | null;
  return !!x && typeof x === "object" && Array.isArray(x.fields) && !!x.series && typeof x.series === "object"
    && !!x.window && Array.isArray(x.sessions);
};

const isMember = (m: unknown): m is CrewMember => {
  const x = m as CrewMember | null;
  return !!x && typeof x === "object" && !!x.passport && typeof x.passport === "object"
    && typeof x.passport.astronaut?.id === "string" && typeof x.passport.astronaut?.name === "string"
    && !!x.passport.mission && typeof x.passport.baselines === "object" && Array.isArray(x.passport.modifiers)
    && Array.isArray(x.passport.countermeasures) && Array.isArray(x.history)
    && x.history.every((d) => !!d && typeof d === "object" && typeof d.mission_day === "number")
    && (x.passport_doc === undefined || isDoc(x.passport_doc));
};

/** Make imported six-month data reachable through passport_ref (PassportWindow, Health dynamics, roster). */
export function registerDocs(members: CrewMember[]): void {
  for (const m of members) {
    const ref = m.passport.passport_ref;
    if (isLocalRef(ref) && m.passport_doc) setLocalPassport(ref, m.passport_doc);
  }
}

export function loadCrew(): CrewMember[] {
  try {
    const raw = localStorage.getItem(CREW_KEY);
    if (!raw) return [];
    const data: unknown = JSON.parse(raw);
    const ms = Array.isArray(data) ? data.filter(isMember) : [];
    registerDocs(ms);
    return ms;
  } catch {
    return [];
  }
}

/** false when the browser refused to store the crew (storage blocked or full). */
export function saveCrew(members: CrewMember[]): boolean {
  try { localStorage.setItem(CREW_KEY, JSON.stringify(members)); return true; } catch { return false; }
}

/** Next free id: MY-1, MY-2, … (never reuses an id still on the crew). */
export function nextCrewId(members: CrewMember[]): string {
  const used = new Set(members.map((m) => m.passport.astronaut.id));
  let n = members.length + 1;
  while (used.has(`MY-${n}`)) n += 1;
  return `MY-${n}`;
}

export function loadMode(): AppMode {
  try { return localStorage.getItem(MODE_KEY) === "crew" ? "crew" : "demo"; } catch { return "demo"; }
}

export function saveMode(mode: AppMode): void {
  try { localStorage.setItem(MODE_KEY, mode); } catch { /* ignore */ }
}

/** Download the whole crew (passports, check-ins, imported six-month data) as one JSON file. */
export function exportCrew(members: CrewMember[]): void {
  const backup: CrewBackup = { format: BACKUP_FORMAT, version: 1, exported_at: new Date().toISOString(), members };
  const blob = new Blob([JSON.stringify(backup)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `asclepius-crew-${new Date().toISOString().slice(0, 10)}.json`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** A crew backup file, or null when the text is not one. */
export function parseBackup(text: string): { members: CrewMember[]; rejected: number } | null {
  let data: unknown;
  try { data = JSON.parse(text); } catch { return null; }
  const b = data as Partial<CrewBackup> | null;
  if (!b || typeof b !== "object" || b.format !== BACKUP_FORMAT || !Array.isArray(b.members)) return null;
  const members = b.members.filter(isMember);
  return { members, rejected: b.members.length - members.length };
}

/** Members from a backup joined to the crew: clashing ids get the next free MY-n, imported data a new local ref. */
export function mergeBackup(crew: CrewMember[], incoming: CrewMember[]): CrewMember[] {
  const out = [...crew];
  for (const m of incoming) {
    const clash = out.some((o) => o.passport.astronaut.id === m.passport.astronaut.id);
    const id = clash ? nextCrewId(out) : m.passport.astronaut.id;
    out.push(rekey(m, id));
  }
  return out;
}

/** Same member under a (possibly new) id; imported six-month data gets a fresh local ref. */
export function rekey(m: CrewMember, id: string): CrewMember {
  const ref = m.passport_doc ? localRef(id) : isLocalRef(m.passport.passport_ref) ? null : m.passport.passport_ref ?? null;
  const passport = { ...m.passport, astronaut: { ...m.passport.astronaut, id }, passport_ref: ref };
  if (ref && m.passport_doc) setLocalPassport(ref, m.passport_doc);
  return { ...m, passport };
}
