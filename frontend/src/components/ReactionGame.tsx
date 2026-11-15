import { useEffect, useRef, useState } from "react";

const TRIALS = 10;

/** 10-tap reaction test. Calls onDone with the mean reaction time in ms. */
export function ReactionGame({ onDone, result }: { onDone: (meanMs: number) => void; result: number | null }) {
  const [phase, setPhase] = useState<"idle" | "wait" | "go">("idle");
  const [open, setOpen] = useState(false);
  const [times, setTimes] = useState<number[]>([]);
  const [early, setEarly] = useState(false);
  const [pos, setPos] = useState({ x: 50, y: 50 });
  const timer = useRef<number | undefined>(undefined);
  const t0 = useRef(0);
  useEffect(() => () => window.clearTimeout(timer.current), []);

  const arm = () => {
    setPhase("wait");
    setEarly(false);
    timer.current = window.setTimeout(() => {
      setPos({ x: 15 + Math.random() * 70, y: 20 + Math.random() * 60 });
      t0.current = performance.now();
      setPhase("go");
    }, 800 + Math.random() * 2200);
  };

  const tap = () => {
    if (phase === "idle") { setTimes([]); arm(); return; }
    if (phase === "wait") { window.clearTimeout(timer.current); setEarly(true); arm(); return; }
    const rt = Math.round(performance.now() - t0.current);
    const next = [...times, rt];
    setTimes(next);
    if (next.length >= TRIALS) {
      setPhase("idle");
      onDone(Math.round(next.reduce((a, b) => a + b, 0) / next.length));
    } else arm();
  };

  const start = () => { setOpen(true); setTimes([]); arm(); };
  return (
    <div className="rt-card">
      <div className="rt-card-h">
        <div>
          <b>Tap reaction test</b>
          <span>{result ? `Mean ${result} ms · ` : ""}30 seconds · tap as soon as the dot appears · {TRIALS} tries</span>
        </div>
        {(!open || phase === "idle") && <button type="button" className="btn btn-sm" onClick={start}>{result ? "Repeat" : "Start"}</button>}
      </div>
      <p className="rt-hint">Approximate - not a calibrated PVT. Optional. Saved for your check-in summary only; it does not trigger sleep-deficit rules.</p>
      {open && <>
      <button type="button" className={`rt-area ${phase === "go" ? "go" : ""}`} onClick={tap} aria-label="Reaction test area">
        {phase === "go" && <span className="rt-dot" style={{ left: `${pos.x}%`, top: `${pos.y}%` }} />}
        <span className="rt-msg">
          {phase === "idle" && (result ? <>Mean {result} ms<small>Tap to repeat</small></> : <>Tap to start<small>{TRIALS} trials</small></>)}
          {phase === "wait" && <>Wait for the dot…{early && <small>Too early, try again</small>}</>}
          {phase === "go" && <>Tap!</>}
        </span>
      </button>
      {times.length > 0 && <div className="rt-tries">{times.map((t, i) => <span key={i}>{t} ms</span>)}</div>}
      </>}
    </div>
  );
}
