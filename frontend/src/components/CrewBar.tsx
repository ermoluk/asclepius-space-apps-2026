import { useEffect, useRef, useState } from "react";
import { assess } from "../api";
import type { CrewMember, DayRecord, Level, Passport } from "../types";
import { LEVEL_WORD, levelRank } from "../levels";
import { Glyph, NoData } from "./ui";

type State = { status: "loading" } | { status: "error" } | { status: "empty" } | { status: "ok"; level: Level };
const TREND_DAYS = 7;

const initials = (name: string) => name.split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]?.toUpperCase() ?? "").join("") || "?";
const shortRole = (p: Passport) => {
  const id = p.astronaut.id;
  if (/^MY-/.test(id)) return p.astronaut.role || "Crew"; // registered in "My crew": the id carries no role
  const m = /-([A-Z0-9]+)$/.exec(id);
  return m ? m[1] : p.astronaut.role;
};

/** Crew roster (CMO view): every member assessed for the selected day, plus a 7-day level strip. */
export function CrewBar({
  members, activeIndex, dayIndex, onSelect, onAdd,
}: { members: CrewMember[]; activeIndex: number; dayIndex: number; onSelect: (i: number) => void; onAdd?: () => void }) {
  const [states, setStates] = useState<State[]>([]);
  const [strips, setStrips] = useState<(Level | null)[][]>([]);
  const [nonce, setNonce] = useState(0);
  // Cache per passport + history object, so a check-in or passport edit re-assesses only that member.
  const cache = useRef(new WeakMap<Passport, WeakMap<DayRecord[], Map<number, Level>>>());

  const cached = (m: CrewMember) => {
    let byHist = cache.current.get(m.passport);
    if (!byHist) { byHist = new WeakMap(); cache.current.set(m.passport, byHist); }
    let byDay = byHist.get(m.history);
    if (!byDay) { byDay = new Map(); byHist.set(m.history, byDay); }
    return byDay;
  };

  useEffect(() => {
    const ctrls = members.map(() => new AbortController());
    setStates(members.map(() => ({ status: "loading" as const })));
    members.forEach((m, i) => {
      if (m.history.length === 0) { setStates((s) => s.map((x, j) => (j === i ? { status: "empty" } : x))); return; }
      const memo = cached(m);
      const d = Math.min(dayIndex, m.history.length - 1);
      const hit = memo.get(d);
      if (hit) { setStates((s) => s.map((x, j) => (j === i ? { status: "ok", level: hit } : x))); return; }
      assess(m.passport, m.history.slice(0, d + 1), ctrls[i].signal)
        .then((a) => { memo.set(d, a.overall_level); setStates((s) => s.map((x, j) => (j === i ? { status: "ok", level: a.overall_level } : x))); })
        .catch(() => {
          if (ctrls[i].signal.aborted) return;
          setStates((s) => s.map((x, j) => (j === i ? { status: "error" } : x)));
        });
    });
    return () => ctrls.forEach((c) => c.abort());
  }, [members, dayIndex, nonce]);

  // 7-day level strip (lower priority: runs after the current-day states, results cached).
  useEffect(() => {
    const ctrl = new AbortController();
    let alive = true;
    (async () => {
      const out: (Level | null)[][] = members.map(() => []);
      for (let i = 0; i < members.length; i++) {
        const m = members[i];
        const memo = cached(m);
        const end = Math.min(dayIndex, m.history.length - 1);
        const days = Array.from({ length: Math.min(TREND_DAYS, end + 1) }, (_, k) => end - Math.min(TREND_DAYS, end + 1) + 1 + k);
        await Promise.all(days.filter((d) => !memo.has(d)).map((d) =>
          assess(m.passport, m.history.slice(0, d + 1), ctrl.signal).then((a) => { memo.set(d, a.overall_level); }).catch(() => undefined)));
        if (!alive) return;
        out[i] = days.map((d) => memo.get(d) ?? null);
        setStrips(out.map((x) => [...x]));
      }
    })();
    return () => { alive = false; ctrl.abort(); };
  }, [members, dayIndex, nonce]);

  return (
    <section aria-label="Crew (CMO view)">
      <h2 className="sr">Crew (CMO view)</h2>
      <ul className="roster">
        {members.map((m, i) => {
          const st = states[i] ?? { status: "loading" };
          const lvText = st.status === "ok" ? LEVEL_WORD[st.level] : st.status === "error" ? "Couldn't load · tap to retry"
            : st.status === "empty" ? "No check-ins yet" : "Assessing…";
          const strip = strips[i] ?? [];
          const selected = i === activeIndex;
          return (
            <li key={m.passport.astronaut.id}>
              <button type="button" className="crew-card" aria-pressed={selected}
                aria-label={`${m.passport.astronaut.name}, ${m.passport.astronaut.role}: ${lvText}${selected ? ", selected" : ""}`}
                onClick={() => { if (st.status === "error") setNonce((n) => n + 1); onSelect(i); }}>
                <span className={`avatar ${st.status === "ok" ? `bg-${st.level.toLowerCase()}` : ""}`} aria-hidden="true">{initials(m.passport.astronaut.name)}</span>
                <span className="cc">
                  <span className="cc-name">{m.passport.astronaut.name}</span>
                  <span className={`cc-lvl ${st.status === "error" ? "err" : ""}`}>
                    {st.status === "loading" && <span className="spinner" style={{ width: 10, height: 10, marginRight: 2 }} />}
                    {st.status === "ok" ? <Glyph level={st.level} /> : st.status === "error" ? null : null}
                    {st.status === "error" ? lvText : `${shortRole(m.passport)} · ${lvText}`}{selected && st.status === "ok" ? " · selected" : ""}
                  </span>
                </span>
                {strip.length > 0 && (
                  <span className="lvbars" aria-hidden="true" title={`Last ${strip.length} days`}>
                    {strip.map((l, k) => <i key={k} className={l ? `l${levelRank(l)}` : "na"} />)}
                  </span>
                )}
                {st.status !== "ok" && strip.length === 0 && st.status !== "loading" && <NoData />}
              </button>
            </li>
          );
        })}
        {onAdd && (
          <li>
            <button type="button" className="crew-card crew-add" onClick={onAdd}>
              <span className="avatar" aria-hidden="true">+</span>
              <span className="cc"><span className="cc-name">Register crew member</span><span className="cc-lvl">One-minute passport</span></span>
            </button>
          </li>
        )}
      </ul>
    </section>
  );
}
