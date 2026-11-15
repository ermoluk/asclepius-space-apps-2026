import type { Assessment, DayRecord, Escalation, Hypothesis, Level, Passport } from "../types";
import { LEVEL_WORD, REGIONS, regionLevel } from "../levels";
import { latestValue } from "../findings";
import { Chevron, Glyph } from "./ui";

export type RailPanel = "measure" | "systems" | "trends" | "passport";

const TREND_SUMMARY: [string, string, string, number][] = [
  ["sleep_hours", "Sleep", "h", 1], ["hr_rest", "Resting HR", "bpm", 0], ["co2_1h", "Cabin CO2", "mmHg", 1], ["mood_valence", "Mood", "/ 7", 0],
];

function Row({ title, sub, onClick, label }: { title: string; sub: React.ReactNode; onClick: () => void; label?: string }) {
  return (
    <li>
      <button type="button" className="rail-btn" onClick={onClick} aria-label={label}>
        <b>{title}</b>
        <span>{sub}</span>
        <Chevron dir="right" />
      </button>
    </li>
  );
}

export function Rail({ assessment, restHyps, restEscs, history, passport, onOpen, onOtherFindings }: {
  assessment: Assessment | null; restHyps: Hypothesis[]; restEscs: Escalation[]; history: DayRecord[]; passport: Passport;
  onOpen: (p: RailPanel) => void; onOtherFindings: () => void;
}) {
  const a = assessment;
  const others: { level: Level; name: string }[] = [
    ...restEscs.map((e) => ({ level: e.level, name: e.label })),
    ...restHyps.map((h) => ({ level: h.level, name: h.name })),
  ];
  const levels = REGIONS.map((r) => regionLevel(a, r));
  const withFindings = levels.filter(Boolean).length;
  const trend = TREND_SUMMARY.map(([k, label, unit, d]) => ({ label, unit, d, lv: latestValue(history, k) })).find((t) => t.lv);
  const pending = a?.pending.length ?? 0;
  const mods = passport.modifiers.length;

  return (
    <nav aria-label="More about today">
      <ul className="rail">
        <Row title="Other findings" onClick={onOtherFindings}
          sub={!a ? "Assessing…" : others.length === 0 ? "None" : <>
            {others.slice(0, 3).map((o, i) => (
              <span key={i} className="lvtxt"><Glyph level={o.level} />{LEVEL_WORD[o.level]} · {o.name}</span>
            ))}{others.length > 3 && <span className="lvtxt">+{others.length - 3} more</span>}</>} />
        <Row title="Measure next" onClick={() => onOpen("measure")}
          sub={!a ? "Assessing…" : `${a.next_measurement ? a.next_measurement.label : "Nothing specific"}${pending ? ` · ${pending} waiting for data` : ""}`} />
        <Row title="Body systems" onClick={() => onOpen("systems")}
          sub={!a ? "Assessing…" : `${withFindings} with findings · ${REGIONS.length - withFindings} not assessed`} />
        <Row title="Trends" onClick={() => onOpen("trends")} label="Trends: open Health dynamics charts"
          sub={`${trend?.lv ? `${trend.label} ${trend.lv.v.toFixed(trend.d)} ${trend.unit} latest · ` : ""}${passport.passport_ref ? "six months + flight" : "all check-ins"}`} />
        <Row title="Passport" onClick={() => onOpen("passport")} label="Passport: open the full six-month passport"
          sub={`${mods} modifier${mods === 1 ? "" : "s"}${passport.passport_ref ? " · six-month data" : ""}`} />
      </ul>
    </nav>
  );
}
