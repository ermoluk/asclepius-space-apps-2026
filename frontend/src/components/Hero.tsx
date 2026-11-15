import type { Assessment, DayRecord, Passport } from "../types";
import { DISCLAIMER, LEVEL_ADVICE, LEVEL_MEANING, NO_FINDINGS, NO_RULE_FIRED, formatDelay, lvClass } from "../levels";
import { findingCount, num, type Urgent } from "../findings";

/** Status headline: level, what to do, the suspected condition and the comm situation. */
export function Hero({ assessment, day, passport, top, groundLast }: {
  assessment: Assessment | null; day: DayRecord | undefined; passport: Passport; top: Urgent | null; groundLast: boolean;
}) {
  const a = assessment;
  const n = findingCount(a);
  const level = n > 0 && a ? a.overall_level : null;
  const noLink = day?.comm_los === true;
  const delay = num(day?.comm_delay_s) ?? passport.mission.comm_delay_s;
  const delayNote = noLink ? "no link to Earth - onboard steps first"
    : groundLast ? `${formatDelay(delay)} delay - onboard steps first` : null;
  const pending = a?.pending.length ?? 0;
  const counts = a && n > 0
    ? [`${n} ${a.hypotheses.length === 0 ? "alert" : a.escalations.length === 0 ? "finding" : "finding/alert"}${n === 1 ? "" : "s"}`,
      pending > 0 ? `${pending} check${pending === 1 ? "" : "s"} waiting for data` : "",
      a.packet ? "flight-surgeon packet ready" : ""].filter(Boolean).join(" · ")
    : "";

  return (
    <section className="hero" aria-live="polite" aria-labelledby="heroTitle">
      <p className="hero-eyebrow">
        {level ? (
          <span className={`lvword ${lvClass(level)}`}>{level} · {LEVEL_MEANING[level]}</span>
        ) : (
          <span className="lvword lv-na">{a ? "Not assessed · no finding" : "Assessing"}</span>
        )}
        <span>Today · MD {day?.mission_day ?? "-"}</span>
      </p>
      <h1 id="heroTitle">{!a ? "Assessing…" : level ? LEVEL_ADVICE[level] : NO_RULE_FIRED}</h1>
      <p className="sub">
        {!a ? "Running the rule engine…"
          : top ? <>{top.name}{top.hyp ? " suspected" : ""}{delayNote ? ` · ${delayNote}` : ""}</>
          : <>{NO_FINDINGS}{delayNote ? ` · ${delayNote}` : ""}</>}
      </p>
      {counts && <p className="count">{counts}</p>}
      <p className="disclaimer"><b>{DISCLAIMER}</b></p>
    </section>
  );
}

/** The one call to action that fits the level, plus the daily check-in (or the day's filed report). */
export function HeroActions({ assessment, day, onCheckIn, onEscalate, filed = false }: {
  assessment: Assessment | null; day: DayRecord | undefined; onCheckIn: () => void; onEscalate: () => void;
  /** The selected day's check-in is already filed: the button opens that report. */
  filed?: boolean;
}) {
  const a = assessment;
  const second = filed ? `Daily report · MD ${day?.mission_day ?? ""}` : "Daily check-in · 2 min";
  const noLink = day?.comm_los === true;
  const orange = !!a && !a.packet && a.overall_level === "ORANGE" && findingCount(a) > 0;
  if (a?.packet) {
    return (
      <>
        <button type="button" className="cta cta-crit" onClick={onEscalate}>
          {noLink ? <><b>Packet queued</b><span>Sends at acquisition of signal · act onboard now</span></>
            : <><b>Contact flight surgeon</b><span>Packet ready · onboard steps first</span></>}
        </button>
        <button type="button" className="btn btn-secondary cta-2" onClick={onCheckIn}>{second}</button>
      </>
    );
  }
  if (orange) {
    return (
      <>
        <button type="button" className="cta cta-alert" onClick={onEscalate}>
          <b>Tell the CMO</b><span>Orange items join today's medical downlink</span>
        </button>
        <button type="button" className="btn btn-secondary cta-2" onClick={onCheckIn}>{second}</button>
      </>
    );
  }
  return (
    <button type="button" className="cta cta-primary" onClick={onCheckIn}>
      {filed ? <><b>Daily report · MD {day?.mission_day}</b><span>Filed · morning and evening answers</span></>
        : <><b>Start daily check-in</b><span>2 minutes · morning and evening</span></>}
    </button>
  );
}
