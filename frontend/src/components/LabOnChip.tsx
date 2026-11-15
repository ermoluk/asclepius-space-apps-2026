import { useState } from "react";
import { getBiodosimetry } from "../api";
import type { BiodoseModel } from "../types";

const DOSES = [0, 0.15, 0.3, 1.5];
const BUCKET_TEXT: Record<string, string> = {
  none: "No exposure signal", low: "Low-dose signal (≈0.1-0.35 Gy)", high: "High-dose signal (≥1 Gy) - check dosimeter, tell CMO",
};

/** Lab-on-chip gene-panel demo: replays real, held-out blood samples from NASA OSDR OSD-410. */
export function LabOnChip() {
  const [model, setModel] = useState<BiodoseModel | null>(null);
  const [dose, setDose] = useState(1.5);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const load = async () => {
    setBusy(true); setErr(null);
    try { setModel(await getBiodosimetry()); } catch (e) { setErr(e instanceof Error ? e.message : String(e)); }
    setBusy(false);
  };
  const sample = model?.samples
    .filter((s) => s.dose_gy === dose)
    .sort((a, b) => b.hours - a.hours || a.volunteer - b.volunteer)[0];
  const top = model?.top_genes.slice(0, 6) ?? [];
  const maxAbs = Math.max(1, ...top.map((g) => Math.abs(sample?.fold_changes[g] ?? 0)));
  return (
    <div className="loc">
      <div className="loc-head">
        <p className="eyebrow">Lab-on-chip · blood gene panel (demo)</p>
        {!model && <button type="button" className="btn btn-ghost btn-sm" disabled={busy} onClick={load}>{busy ? "Loading…" : "Run gene-panel test"}</button>}
      </div>
      {err && <p className="muted">Could not load the model: {err}</p>}
      {!model && !err && <p className="muted loc-note">Replays a real blood sample from NASA OSDR OSD-410 through a {20}-gene radiation panel, compared with the person's own unexposed sample.</p>}
      {model && sample && (
        <>
          <div className="yn loc-doses" role="group" aria-label="Sample dose">
            {DOSES.map((d) => <button key={d} type="button" aria-pressed={dose === d} onClick={() => setDose(d)}>{d} Gy</button>)}
          </div>
          <p className={`loc-result loc-${sample.predicted_held_out}`}><b>{BUCKET_TEXT[sample.predicted_held_out]}</b></p>
          <p className="muted loc-note">
            Real sample <code>{sample.sample}</code>: volunteer {sample.volunteer}, {sample.dose_gy} Gy, {sample.hours} h after exposure (ex vivo γ-rays).
            Classified by a model that never saw this volunteer · held-out accuracy {Math.round(model.loocv_accuracy * 100)}%.
          </p>
          <div className="loc-genes">
            {top.map((g) => {
              const v = sample.fold_changes[g] ?? 0;
              return (
                <div key={g} className="loc-gene">
                  <code>{g}</code>
                  <span className="loc-bar"><i style={{ width: `${(Math.abs(v) / maxAbs) * 100}%` }} className={v < 0 ? "neg" : ""} /></span>
                  <span className="mono">{v >= 0 ? "+" : ""}{v.toFixed(2)}</span>
                </div>
              );
            })}
          </div>
          <p className="muted loc-note">log₂ fold change vs the same person's unexposed sample. It can flag exposure; it does not replace the dosimeter.</p>
        </>
      )}
    </div>
  );
}
