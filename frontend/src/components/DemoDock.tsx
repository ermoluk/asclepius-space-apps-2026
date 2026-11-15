import { useEffect, useRef } from "react";
import type { AppMode, DayRecord, StoryDay } from "../types";

/** The demo flight (fictional, like its crew). */
const MISSION = "Hygieia I";

/** Floating controls. Demo: the day's story event, mission day, check-in, charts and passport. My crew: register,
 *  mission day, check-in, charts, passport, import, export and reset. */
export function DemoDock({
  mode, story, history, dayIndex, onDay, onCheckIn, onPassport, onCharts, crewSize = 0, onRegister, onReset, onImport, onExport,
}: {
  mode: AppMode; story: StoryDay[];
  history: DayRecord[]; dayIndex: number; onDay: (i: number) => void;
  onCheckIn: () => void; onPassport: () => void; onCharts: () => void;
  crewSize?: number; onRegister?: () => void; onReset?: () => void;
  /** My crew: import a file (CSV, passport JSON, crew backup) and download the crew as a backup. */
  onImport?: () => void; onExport?: () => void;
}) {
  const crew = mode === "crew";
  const day = history[dayIndex];
  const event = story.find((s) => s.mission_day === day?.mission_day);
  const hasMember = !crew || crewSize > 0;

  // Publish the dock's height as --dock-h: on phones it is pinned to the bottom edge and the page end must clear it.
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const root = document.documentElement;
    const publish = () => root.style.setProperty("--dock-h", `${Math.ceil(el.getBoundingClientRect().height)}px`);
    publish();
    const ro = new ResizeObserver(publish);
    ro.observe(el);
    return () => { ro.disconnect(); root.style.removeProperty("--dock-h"); };
  }, []);

  return (
    <div ref={ref} className={`dock ${crew ? "dock-crew" : ""}`} role="region" aria-label={crew ? "My crew controls" : "Demo controls"}>
      <span className="demo" aria-hidden="true">{crew ? "My crew" : "Demo"}</span>
      {crew ? (
        <span className="crew-count">{crewSize} member{crewSize === 1 ? "" : "s"}</span>
      ) : (
        <span className="story" title={event?.detail} aria-live="polite">
          {event ? event.title : day ? `${MISSION} · added day` : MISSION}
        </span>
      )}
      {hasMember && history.length > 0 && (
        <>
          <span className="md">MD {day?.mission_day ?? "-"}</span>
          <label className="day">
            <span className="sr">Mission day</span>
            <input className="slider" type="range" min={0} max={Math.max(0, history.length - 1)} value={dayIndex}
              onChange={(e) => onDay(Number(e.target.value))}
              aria-valuetext={`Mission day ${day?.mission_day ?? ""}, ${dayIndex + 1} of ${history.length}${event ? `: ${event.title}` : ""}`} disabled={history.length < 2} />
            <small>{dayIndex + 1} of {history.length}</small>
          </label>
        </>
      )}
      <span className="acts">
        {crew && onRegister && <button className="btn btn-sm" type="button" onClick={onRegister}>Register</button>}
        {hasMember && <button className="btn btn-sm" type="button" onClick={onCheckIn}>Check-in</button>}
        {hasMember && <button className="btn btn-sm" type="button" onClick={onCharts}>Charts</button>}
        {hasMember && <button className="btn btn-sm" type="button" onClick={onPassport}>Passport</button>}
        {crew && onImport && <button className="btn btn-sm" type="button" onClick={onImport}>Import</button>}
        {crew && onExport && crewSize > 0 && <button className="btn btn-sm" type="button" onClick={onExport} title="Download the whole crew as one JSON file">Export</button>}
        {crew && onReset && crewSize > 0 && <button className="btn btn-sm" type="button" onClick={onReset}>Reset</button>}
      </span>
    </div>
  );
}
