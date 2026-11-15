import type { AppMode, Assessment, DayRecord, Level, Passport } from "../types";
import { CAREER_DOSE_LIMIT_MSV, CAREER_DOSE_WATCH_FRACTION, CO2_LIMIT_MMHG, LEVEL_WORD, formatDelay, lvClass, worst } from "../levels";
import { num } from "../findings";
import { Glyph } from "./ui";

export function Header({
  passport, day, assessment, theme, onToggleTheme, mode, onMode,
}: {
  passport: Passport | null; day: DayRecord | undefined; assessment: Assessment | null; theme: "light" | "dark"; onToggleTheme: () => void;
  mode: AppMode; onMode: (m: AppMode) => void;
}) {
  const co2 = num(day?.co2_1h);
  const dose = num(day?.dose_today);
  const cum = num(day?.dose_cumulative);
  const noLink = day?.comm_los === true;
  const delay = num(day?.comm_delay_s) ?? passport?.mission.comm_delay_s ?? null;
  const co2High = co2 != null && co2 > CO2_LIMIT_MMHG;
  const doseWatch = cum != null && cum / CAREER_DOSE_LIMIT_MSV >= CAREER_DOSE_WATCH_FRACTION;
  const envLevels: Level[] = [
    ...(assessment?.hypotheses.filter((h) => h.system === "ENV").map((h) => h.level) ?? []),
    ...(assessment?.escalations.filter((e) => e.system === "ENV").map((e) => e.level) ?? []),
  ];
  const envLevel = envLevels.length ? worst(envLevels) : null;
  const missing = assessment?.news2.missing ?? [];
  const phase = typeof day?.phase === "string" ? day.phase : null;

  return (
    <header className="hdr">
      <div className="wrap">
        <div className="hdr-id">
          <div className="brand">
            <img className="brand-mark" src={`/brand/mark-${theme}.png`} alt="" width={48} height={36} />
            <span className="brand-txt">
              <span className="brand-name">Asclepius</span>
              <span className="brand-sub">Astronaut Medical Program</span>
            </span>
          </div>
          {passport && (
            <div className="who-blk">
              <b>{passport.astronaut.name}</b>
              <span>{passport.astronaut.role} · {passport.astronaut.id}</span>
            </div>
          )}
        </div>
        {passport && (
          <ul className="tele" aria-label="Mission telemetry">
            <li>
              <span className="k">{passport.mission.vehicle}{passport.mission.profile ? ` · ${passport.mission.profile}` : ""}</span>
              <span className="v">MD {day?.mission_day ?? "-"}{phase ? ` · ${phase}` : ""}</span>
            </li>
            {noLink ? (
              <li>
                <span className="k">Far-side LOS · ~40 min</span>
                <span className="v"><span className="nolink-pill" role="status" aria-label="No link with Earth: far-side loss of signal, about 40 minutes">NO LINK</span></span>
              </li>
            ) : (
              <li>
                <span className="k">Earth comm · RT {formatDelay(delay == null ? null : delay * 2)}</span>
                <span className="v">{delay != null && delay < 1 ? "< 1 s" : formatDelay(delay)} one-way</span>
              </li>
            )}
            <li title={co2 == null ? "No reading" : `${co2High ? "Above" : "Within"} ${CO2_LIMIT_MMHG.toFixed(1)} mmHg limit (NASA-STD-3001)`}>
              <span className="k">Cabin CO2 1-h</span>
              <span className={`v ${co2High ? lvClass("ORANGE") : ""}`}>
                {co2High && <Glyph level="ORANGE" />}{co2 == null ? "-" : `${co2.toFixed(1)} mmHg`}
                <span className="sr">{co2 == null ? "no reading" : `${co2High ? "above" : "within"} the ${CO2_LIMIT_MMHG.toFixed(1)} mmHg limit, NASA-STD-3001`}</span>
              </span>
            </li>
            <li title={`Career dose ${cum == null ? "-" : cum.toFixed(1)} of ${CAREER_DOSE_LIMIT_MSV} mSv (NASA-STD-3001 Vol. 1)`}>
              <span className="k">Dose today · career {cum == null ? "-" : (cum < 10 ? cum.toFixed(1) : Math.round(cum))}/{CAREER_DOSE_LIMIT_MSV}</span>
              <span className={`v ${doseWatch ? lvClass("ORANGE") : ""}`}>{doseWatch && <Glyph level="ORANGE" />}{dose == null ? "-" : `${dose.toFixed(2)} mSv`}</span>
              {cum != null && <span className="bar2" aria-hidden="true"><i className={doseWatch ? "watch" : ""} style={{ width: `${Math.min(100, (cum / CAREER_DOSE_LIMIT_MSV) * 100)}%` }} /></span>}
            </li>
            <li>
              <span className="k">NEWS2 · {missing.length ? `${missing.length} vital${missing.length === 1 ? "" : "s"} missing` : assessment ? "All vitals present" : "…"}</span>
              <span className="v">{assessment ? assessment.news2.total : "-"}{assessment?.news2.max ? ` / ${assessment.news2.max}` : ""}</span>
            </li>
          </ul>
        )}
        <div className="hdr-right">
          {envLevel && <span className={`badge bg-${envLevel.toLowerCase()}`}><Glyph level={envLevel} />Environment · {LEVEL_WORD[envLevel]}</span>}
          <div className="mode-seg" role="group" aria-label="Data mode">
            <button type="button" aria-pressed={mode === "demo"} onClick={() => onMode("demo")}>Demo</button>
            <button type="button" aria-pressed={mode === "crew"} onClick={() => onMode("crew")}>My crew</button>
          </div>
          {mode === "demo" ? <span className="chip-demo">Simulated data</span>
            : <span className="chip-demo chip-own" title="Entered by you, stored only in this browser">Your entries</span>}
          <button type="button" className="icon-btn" onClick={onToggleTheme} aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`} title="Toggle theme">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              {theme === "dark"
                ? <><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></>
                : <path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5Z" />}
            </svg>
          </button>
        </div>
      </div>
    </header>
  );
}
