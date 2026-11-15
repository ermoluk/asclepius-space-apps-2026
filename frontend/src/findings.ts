import type { Action, Assessment, DayRecord, Escalation, Hypothesis, Level, Passport } from "./types";
import { LONG_DELAY_S, isGroundOnly, levelRank } from "./levels";

export const num = (v: unknown): number | null => (typeof v === "number" && Number.isFinite(v) ? v : null);

/** The most urgent finding shown at the top of the page, with the steps to do now. */
export interface Urgent {
  level: Level; name: string; system: string; cf: number | null; expected: boolean;
  hyp?: Hypothesis; esc?: Escalation; actions: Action[];
}

const sortHyps = (hs: Hypothesis[]) => [...hs].sort((a, b) => levelRank(b.level) - levelRank(a.level) || b.cf - a.cf);
const sortEscs = (es: Escalation[]) => [...es].sort((a, b) => levelRank(b.level) - levelRank(a.level));

/** Onboard steps come first when Earth is far away or out of contact (backend packet.py convention). */
export function onboardFirst(passport: Passport | null, day: DayRecord | undefined): boolean {
  if (day?.comm_los === true) return true;
  const delay = num(day?.comm_delay_s) ?? passport?.mission.comm_delay_s ?? 0;
  return delay >= LONG_DELAY_S;
}

export function mergeActions(lists: Action[][], groundLast: boolean): Action[] {
  const seen = new Set<string>();
  const out: Action[] = [];
  for (const a of lists.flat()) {
    const k = a.id || a.text;
    if (seen.has(k)) continue;
    seen.add(k); out.push(a);
  }
  return groundLast ? [...out.filter((a) => !isGroundOnly(a.who)), ...out.filter((a) => isGroundOnly(a.who))] : out;
}

export function splitFindings(a: Assessment | null, groundLast: boolean): { top: Urgent | null; restHyps: Hypothesis[]; restEscs: Escalation[] } {
  if (!a) return { top: null, restHyps: [], restEscs: [] };
  const hyps = sortHyps(a.hypotheses);
  const escs = sortEscs(a.escalations);
  let hyp: Hypothesis | undefined;
  let esc: Escalation | undefined;
  if (hyps.length) {
    const topEsc = escs[0];
    if (topEsc && levelRank(topEsc.level) > levelRank(hyps[0].level)) {
      esc = topEsc;
      hyp = hyps.find((h) => h.system === topEsc.system);
    } else {
      hyp = hyps[0];
      esc = escs.find((e) => e.system === hyp!.system);
    }
  } else if (escs.length) {
    esc = escs[0];
  }
  if (!hyp && !esc) return { top: null, restHyps: [], restEscs: [] };
  const level: Level = hyp && esc ? (levelRank(esc.level) > levelRank(hyp.level) ? esc.level : hyp.level) : (hyp?.level ?? esc!.level);
  const top: Urgent = {
    level,
    name: hyp?.name ?? esc!.label,
    system: hyp?.system ?? esc!.system,
    cf: hyp ? hyp.cf : null,
    expected: !!hyp?.expected,
    hyp, esc,
    actions: mergeActions([hyp?.actions ?? [], esc?.actions ?? []], groundLast),
  };
  return { top, restHyps: hyps.filter((h) => h !== hyp), restEscs: escs.filter((e) => e !== esc) };
}

export const findingCount = (a: Assessment | null) => (a ? a.hypotheses.length + a.escalations.length : 0);

/** Latest numeric value of a day-record field up to the selected day, with its mission day. */
export function latestValue(history: DayRecord[], key: string): { v: number; md: number } | null {
  for (let i = history.length - 1; i >= 0; i--) {
    const v = num(history[i][key]);
    if (v !== null) return { v, md: history[i].mission_day };
  }
  return null;
}
