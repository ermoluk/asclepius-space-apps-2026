import { useCallback, useEffect, useRef, useState } from "react";
import { assess, getKnowledgeCounts, getScenario, getScenarios } from "./api";
import type { AppMode, Assessment, CrewMember, DayRecord, KnowledgeCounts, Passport, ScenarioInfo, StoryDay } from "./types";
import { DISCLAIMER } from "./levels";
import { ApiError } from "./api";
import { GlyphDefs, Modal } from "./components/ui";
import { Header } from "./components/Header";
import { Hero, HeroActions } from "./components/Hero";
import { UrgentFinding, AllFindings, NextMeasurement } from "./components/UrgentFinding";
import { Rail, type RailPanel } from "./components/Rail";
import { BodySystemsDrawer } from "./components/BodyMap";
import { PacketModal } from "./components/PacketModal";
import { DemoDock } from "./components/DemoDock";
import { CrewBar } from "./components/CrewBar";
import { onboardFirst, splitFindings } from "./findings";
import { CheckInModal } from "./components/CheckInModal";
import { PassportQuiz } from "./components/PassportQuiz";
import { PassportWindow } from "./components/PassportData";
import { ChartsWindow } from "./components/ChartsWindow";
import { DataSources } from "./components/DataSources";
import { CrewSetup, FirstCheckIn } from "./components/MyCrew";
import { ImportModal, type ImportOutcome } from "./components/ImportModal";
import { exportCrew, loadCrew, loadMode, nextCrewId, saveCrew, saveMode } from "./myCrew";
import { dismissSplash } from "./splash";
import { Starfield } from "./components/Starfield";

/** The demo is the crew story of Hygieia I, a fictional lunar flyby, told day by day; it opens on flight day 1. */
const DEFAULT_SCENARIO = "hygieia-flyby";
const pickScenario = (list: ScenarioInfo[]) => (list.find((s) => s.id === DEFAULT_SCENARIO) ?? list[0])?.id;
/** CrewBar day for the other members while the active one has no check-in yet: everyone's latest day. */
const LATEST = Number.MAX_SAFE_INTEGER;

type Theme = "light" | "dark";
const initialTheme = (): Theme => {
  try { const t = localStorage.getItem("theme"); if (t === "light" || t === "dark") return t; } catch { /* ignore */ }
  return "dark"; // design system v4: dark is the default in the cabin

};

export default function App() {
  // "demo": ready-made scenarios. "crew": crew members you register yourself, kept in this browser.
  const [mode, setMode] = useState<AppMode>(loadMode);
  const initialMode = useRef(mode);
  const [scenarios, setScenarios] = useState<ScenarioInfo[]>([]);
  const [scenarioId, setScenarioId] = useState<string>("");
  // What happens on each mission day of the demo story (dock caption).
  const [story, setStory] = useState<StoryDay[]>([]);
  // Members: one entry for a single-astronaut scenario, several for a crew scenario or "My crew".
  // Loaded lazily so the first save in "My crew" mode never overwrites the stored crew with an empty list.
  const [members, setMembers] = useState<CrewMember[]>(() => (initialMode.current === "crew" ? loadCrew() : []));
  const [isCrew, setIsCrew] = useState(initialMode.current === "crew");
  const [activeMember, setActiveMember] = useState(0);
  const [dayIndex, setDayIndex] = useState(() => Math.max(0, (members[0]?.history.length ?? 1) - 1));
  const [adding, setAdding] = useState(false);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [loading, setLoading] = useState(initialMode.current === "demo");
  const [error, setError] = useState<string | null>(null);
  const [counts, setCounts] = useState<KnowledgeCounts | null>(null);
  const [checkIn, setCheckIn] = useState(false);
  const [quiz, setQuiz] = useState(false);
  // Full-screen windows: the six-month passport, and Health dynamics (value = metric in focus).
  const [ppOpen, setPpOpen] = useState(false);
  const [charts, setCharts] = useState<string | null>(null);
  const [sources, setSources] = useState(false);
  const [theme, setTheme] = useState<Theme>(initialTheme);
  const [notice, setNotice] = useState<string | null>(null);
  // Result of an import, or a storage warning ("My crew").
  const [info, setInfo] = useState<string | null>(null);
  // Import window: target = the member to import into (null = let the user choose).
  const [importFor, setImportFor] = useState<{ target: number | null } | null>(null);
  const [panel, setPanel] = useState<RailPanel | null>(null);
  const [packetOpen, setPacketOpen] = useState(false);
  const [flash, setFlash] = useState(false);
  const [retry, setRetry] = useState(0);
  const reqId = useRef(0);
  // The last check-in submit, so a rejected (422) record can be rolled back.
  const lastSubmit = useRef<{ member: number; prev: DayRecord[]; prevDay: number; next: DayRecord[] } | null>(null);

  const active: CrewMember | undefined = members[activeMember] ?? members[0];
  const passport: Passport | null = active?.passport ?? null;
  const history: DayRecord[] = active?.history ?? [];
  const setHistory = useCallback((h: DayRecord[]) =>
    setMembers((ms) => ms.map((m, i) => (i === activeMember ? { ...m, history: h } : m))), [activeMember]);
  const setPassport = useCallback((p: Passport) =>
    setMembers((ms) => ms.map((m, i) => (i === activeMember ? { ...m, passport: p } : m))), [activeMember]);

  // The loading splash (index.html) leaves once the first scenario is assessed, or right away in "My crew" / on error.
  useEffect(() => { if (!loading) dismissSplash(); }, [loading]);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem("theme", theme); } catch { /* ignore */ }
  }, [theme]);

  const loadScenario = useCallback(async (id: string) => {
    const my = ++reqId.current;
    setLoading(true); setError(null);
    try {
      const sc = await getScenario(id);
      if (my !== reqId.current) return;
      setScenarioId(id);
      const crew = sc.crew && sc.crew.length > 0 ? sc.crew : null;
      const ms = crew ?? [{ passport: sc.passport, history: sc.history }];
      const idx = crew ? Math.max(0, crew.findIndex((m) => m.passport.astronaut.id === sc.passport.astronaut.id)) : 0;
      setMembers(ms);
      setIsCrew(!!crew);
      setActiveMember(idx);
      setStory(sc.story ?? []);
      setDayIndex(0); // the story starts at launch; the slider moves through the days
    } catch (e) {
      if (my === reqId.current) { setError(e instanceof Error ? e.message : String(e)); setLoading(false); }
    }
  }, []);

  useEffect(() => {
    getKnowledgeCounts().then(setCounts).catch(() => undefined);
    getScenarios()
      .then((list) => {
        setScenarios(list);
        if (initialMode.current !== "demo") return;
        const id = pickScenario(list);
        if (id) void loadScenario(id); else setLoading(false);
      })
      .catch((e) => { if (initialMode.current === "demo") { setError(e instanceof Error ? e.message : String(e)); setLoading(false); } });
  }, [loadScenario]);

  // "My crew": every change (register, check-in, passport edit, remove) is saved in this browser.
  useEffect(() => {
    if (mode === "crew" && !saveCrew(members))
      setInfo("This browser could not store the crew (storage full or blocked). Changes stay until the page is closed: use Export to keep a copy.");
  }, [mode, members]);

  const enterCrew = useCallback(() => {
    ++reqId.current; // drop a scenario still loading
    const ms = loadCrew();
    setMembers(ms); setIsCrew(true); setActiveMember(0);
    setDayIndex(Math.max(0, (ms[0]?.history.length ?? 1) - 1));
    setAssessment(null); setError(null); setNotice(null); setInfo(null); setPanel(null); setLoading(false);
  }, []);

  const switchMode = (m: AppMode) => {
    if (m === mode) return;
    setMode(m); saveMode(m);
    lastSubmit.current = null;
    if (m === "crew") { enterCrew(); return; }
    setAssessment(null); setMembers([]); setNotice(null); setInfo(null); setPanel(null); setImportFor(null);
    const id = scenarioId || pickScenario(scenarios);
    if (id) { void loadScenario(id); return; }
    // Scenario list never arrived (backend was down at start): fetch it now.
    setLoading(true);
    getScenarios()
      .then((list) => { setScenarios(list); const first = pickScenario(list); if (first) void loadScenario(first); else setLoading(false); })
      .catch((e) => { setError(e instanceof Error ? e.message : String(e)); setLoading(false); });
  };

  const addMember = (p: Passport) => {
    setMembers([...members, { passport: p, history: [] }]);
    setActiveMember(members.length); setDayIndex(-1); setAssessment(null); setAdding(false);
  };
  const removeMember = (i: number) => {
    const m = members[i];
    if (!m || !window.confirm(`Remove ${m.passport.astronaut.name} and all their check-ins from this browser? This cannot be undone.`)) return;
    const next = members.filter((_, j) => j !== i);
    const active = i < activeMember ? activeMember - 1 : i === activeMember ? 0 : activeMember;
    setMembers(next); setActiveMember(active);
    setDayIndex(Math.max(0, (next[active]?.history.length ?? 1) - 1));
    setAssessment(null); setPanel(null); lastSubmit.current = null;
  };
  const applyImport = (o: ImportOutcome) => {
    const h = o.members[o.select]?.history ?? [];
    setMembers(o.members); setActiveMember(o.select); setDayIndex(h.length ? h.length - 1 : -1);
    setAssessment(null); setPanel(null); setImportFor(null); setInfo(o.message); lastSubmit.current = null;
  };
  const resetCrew = () => {
    const who = members.length === 1 ? members[0].passport.astronaut.name : `all ${members.length} crew members`;
    if (!window.confirm(`Remove ${who} and every check-in from this browser? This cannot be undone.`)) return;
    setMembers([]); setActiveMember(0); setDayIndex(0); setAssessment(null); setPanel(null); lastSubmit.current = null;
  };

  // Re-assess whenever passport, history or selected day change.
  useEffect(() => {
    if (!passport) return;
    if (history.length === 0) { setAssessment(null); setLoading(false); return; } // registered, no check-in yet
    const ctrl = new AbortController();
    setLoading(true);
    assess(passport, history.slice(0, dayIndex + 1), ctrl.signal)
      .then((a) => {
        setAssessment(a); setError(null); setLoading(false);
        if (lastSubmit.current?.next === history) lastSubmit.current = null;
      })
      .catch((e) => {
        if (ctrl.signal.aborted) return;
        const sub = lastSubmit.current;
        if (e instanceof ApiError && e.status === 422 && sub && sub.next === history) {
          // The server rejected the record just added: undo it so later assessments keep working.
          lastSubmit.current = null;
          setMembers((ms) => ms.map((m, i) => (i === sub.member ? { ...m, history: sub.prev } : m)));
          setDayIndex(sub.prevDay);
          setNotice(`Check-in not saved. ${e.message}`);
          return;
        }
        setAssessment(null);
        setError(e instanceof Error ? e.message : String(e));
        setLoading(false);
      });
    return () => ctrl.abort();
  }, [passport, history, dayIndex, retry]);

  const switchMember = useCallback((i: number) => {
    setActiveMember(i);
    setDayIndex((d) => { const last = members[i].history.length - 1; return d < 0 ? last : Math.min(d, last); });
  }, [members]);
  const closeCheckIn = useCallback(() => setCheckIn(false), []);
  const closeQuiz = useCallback(() => setQuiz(false), []);
  const day = history[dayIndex];
  const crewDayIndex = history.length === 0 ? LATEST : Math.min(dayIndex, history.length - 1);
  const shown = history.slice(0, dayIndex + 1);
  const groundLast = onboardFirst(passport, day);
  const { top, restHyps, restEscs } = splitFindings(assessment, groundLast);
  const scenarioInfo = scenarios.find((x) => x.id === scenarioId);
  const closePanel = useCallback(() => setPanel(null), []);
  // Rail "Trends" and "Passport" open the full-screen windows; the rest open drawers.
  const openPanel = useCallback((p: RailPanel) => {
    if (p === "trends") setCharts("sleep_hours");
    else if (p === "passport") setPpOpen(true);
    else setPanel(p);
  }, []);
  const closeCharts = useCallback(() => setCharts(null), []);
  const closePassport = useCallback(() => setPpOpen(false), []);
  // One full-screen window at a time (Esc would otherwise close both).
  const passportToCharts = (metric?: string) => { setPpOpen(false); setCharts(metric ?? "sleep_hours"); };
  const showOtherFindings = () => {
    const el = document.getElementById("all-findings");
    if (!el) { setPanel("systems"); return; }
    el.scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
    setFlash(true); window.setTimeout(() => setFlash(false), 1200);
  };
  const retryLoad = () => {
    setError(null);
    if (passport) { setRetry((n) => n + 1); return; }
    const id = scenarioId || scenarios[0]?.id;
    if (id) void loadScenario(id); else window.location.reload();
  };

  return (
    <>
      {theme === "dark" && <Starfield />}
      <GlyphDefs />
      <Header passport={passport} day={day} assessment={assessment} theme={theme}
        onToggleTheme={() => setTheme(theme === "dark" ? "light" : "dark")} mode={mode} onMode={switchMode} />
      <main className="page wrap">
        {(mode === "crew" ? members.length > 0 : isCrew && members.length > 1) && (
          <CrewBar members={members} activeIndex={activeMember} dayIndex={crewDayIndex} onSelect={switchMember}
            onAdd={mode === "crew" ? () => setAdding(true) : undefined} />
        )}
        {day?.comm_los === true && (
          <div className="banner" role="status">
            <div><b>No link - far-side loss of signal (~40 min)</b>Onboard steps first. Packets wait in the queue.</div>
          </div>
        )}
        {notice && (
          <div className="banner notice" role="alert">
            <div><b>Check-in not saved.</b>{notice.replace(/^Check-in not saved\.\s*/, "")}</div>
            <button type="button" className="btn btn-sm" onClick={() => setNotice(null)}>Dismiss</button>
          </div>
        )}
        {info && (
          <div className="banner neutral" role="status">
            <div><b>My crew.</b>{info}</div>
            <button type="button" className="btn btn-sm" onClick={() => setInfo(null)}>Dismiss</button>
          </div>
        )}
        {error && (
          <div className="banner" role="alert">
            <div><b>Something went wrong.</b>{error} Your data is safe - try again.</div>
            <button type="button" className="btn btn-sm" onClick={retryLoad}>Retry</button>
          </div>
        )}
        {mode === "crew" && members.length === 0 && <CrewSetup onAdd={() => setAdding(true)} onImport={() => setImportFor({ target: null })} />}
        {passport && history.length === 0 && (
          <FirstCheckIn passport={passport} onCheckIn={() => setCheckIn(true)} onPassport={() => setPpOpen(true)}
            onImport={mode === "crew" ? () => setImportFor({ target: activeMember }) : undefined} />
        )}
        {mode === "demo" && !passport && !error && (
          <div className="layout"><div className="area-hero"><p className="updating"><span className="spinner" />Loading mission data…</p><div className="skel" aria-hidden="true"><i /><i /><i /></div></div></div>
        )}
        {passport && history.length > 0 && (
          <div className={`layout ${error ? "stale" : ""}`}>
            <div className="area-hero">
              <Hero assessment={assessment} day={day} passport={passport} top={top} groundLast={groundLast} />
            </div>
            <div className="area-cta">
              <HeroActions assessment={assessment} day={day} onCheckIn={() => setCheckIn(true)} onEscalate={() => setPacketOpen(true)}
                filed={mode === "demo" || dayIndex < history.length - 1} />
            </div>
            <div className={`area-main ${loading && assessment ? "loading" : ""}`} aria-busy={loading}>
              {!assessment && <div className="skel" aria-label="Assessing…"><p className="updating"><span className="spinner" />Assessing…</p><i /><i /><i /></div>}
              {top && <UrgentFinding top={top} groundLast={groundLast} />}
              <AllFindings assessment={assessment} restHyps={restHyps} restEscs={restEscs} groundLast={groundLast}
                loading={loading} flash={flash} onEscalate={() => setPacketOpen(true)} />
            </div>
            <aside className="area-rail">
              <Rail assessment={assessment} restHyps={restHyps} restEscs={restEscs} history={shown} passport={passport}
                onOpen={openPanel} onOtherFindings={showOtherFindings} />
            </aside>
          </div>
        )}
      </main>
      <footer className="foot">
        <div className="wrap">
          <p><b>{DISCLAIMER}</b></p>
          <p className="r">Sources: NASA OSDR Inspiration4 (OSD-569/575), NASA DONKI, NASA HRP, NASA-STD-3001, NASA IMM, NHANES 2011-2012, LifeSnaps ·{" "}
            <button type="button" className="linkbtn" onClick={() => setSources(true)}>All data sources</button></p>
          {counts && <p>{counts.conditions} conditions · {counts.rules} rules · {counts.actions} actions · {counts.references} references</p>}
          {mode === "demo" && scenarioInfo && <p className="r">Scenario: {scenarioInfo.description}</p>}
          {mode === "crew" && <p className="r">My crew: {members.length} member{members.length === 1 ? "" : "s"} registered by you · stored only in this browser.</p>}
          <p className="team">Made by team <a href="https://www.spaceappschallenge.org/2026/find-a-team/bubliki/" target="_blank" rel="noopener noreferrer"><b>Bubliki</b></a> · NASA Space Apps Challenge 2026</p>
        </div>
      </footer>
      {(scenarios.length > 0 || mode === "crew") && (
        <DemoDock mode={mode} story={mode === "demo" ? story : []}
          history={history} dayIndex={Math.max(0, dayIndex)} onDay={setDayIndex}
          onCheckIn={() => setCheckIn(true)} onPassport={() => setPpOpen(true)} onCharts={() => setCharts("sleep_hours")}
          crewSize={members.length} onRegister={() => setAdding(true)} onReset={resetCrew}
          onImport={() => setImportFor({ target: null })} onExport={() => exportCrew(members)} />
      )}
      {panel === "systems" && passport && (
        <BodySystemsDrawer assessment={assessment} history={shown} passport={passport} groundLast={groundLast} onClose={closePanel} />
      )}
      {charts !== null && members.length > 0 && (
        <ChartsWindow members={members} active={Math.min(activeMember, members.length - 1)} dayIndex={dayIndex} mode={mode}
          initialMetric={charts} onMember={switchMember} onDay={setDayIndex} onClose={closeCharts} />
      )}
      {panel === "measure" && assessment && (
        <Modal variant="drawer" title="Measure next" eyebrow="Fills gaps in today's data" onClose={closePanel}>
          {assessment.next_measurement ? <NextMeasurement a={assessment} /> : <p className="muted">No single measurement would change today's ranking.</p>}
          <section className="dr-sec">
            <h3>Checks waiting for data</h3>
            {assessment.pending.length === 0 ? <p className="muted">None - every rule had the facts it needed.</p> : (
              <ul className="pending-list">
                {assessment.pending.map((p) => (
                  <li key={p.rule}><code>{p.rule}</code><span className="muted">Missing: <span className="mono">{p.missing.join(", ")}</span></span></li>
                ))}
              </ul>
            )}
          </section>
          <button type="button" className="btn btn-primary" onClick={() => { setPanel(null); setCheckIn(true); }}>Start daily check-in</button>
        </Modal>
      )}
      {packetOpen && assessment && passport && (
        <PacketModal assessment={assessment} day={day} passport={passport} top={top} onClose={() => setPacketOpen(false)} />
      )}
      {checkIn && (
        <CheckInModal history={history} dayIndex={dayIndex} mode={mode} who={isCrew ? passport?.astronaut.name : undefined}
          onClose={closeCheckIn}
          onSubmit={(h, day) => {
            lastSubmit.current = { member: activeMember, prev: history, prevDay: dayIndex, next: h };
            setNotice(null); setHistory(h); setDayIndex(day); setCheckIn(false);
          }} />
      )}
      {ppOpen && passport && (
        <PassportWindow passport={passport} onClose={closePassport} onCharts={passportToCharts}
          onEdit={() => { setPpOpen(false); setQuiz(true); }}
          onRemove={mode === "crew" ? () => { setPpOpen(false); removeMember(activeMember); } : undefined}
          onImport={mode === "crew" ? () => { setPpOpen(false); setImportFor({ target: activeMember }); } : undefined} />
      )}
      {sources && <DataSources onClose={() => setSources(false)} />}
      {quiz && passport && (
        <PassportQuiz passport={passport} onClose={closeQuiz} onDone={(p) => { setPassport(p); setQuiz(false); }} />
      )}
      {importFor && mode === "crew" && (
        <ImportModal members={members} target={importFor.target} onClose={() => setImportFor(null)} onApply={applyImport} />
      )}
      {adding && (
        <PassportQuiz mode="add" passport={members[0]?.passport ?? null} newId={nextCrewId(members)}
          onClose={() => setAdding(false)} onDone={addMember} />
      )}
    </>
  );
}
