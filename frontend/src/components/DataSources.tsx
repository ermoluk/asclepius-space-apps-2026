import { useEffect, useState } from "react";
import { getDatasets } from "../api";
import type { DatasetsSummary } from "../types";
import { Modal } from "./ui";
import { ProvBadges } from "./PassportData";

const KIND: Record<string, string> = {
  "real-astronaut": "Real astronaut data", "real-ground": "Real people on Earth", "real-population": "Population survey",
  "real-events": "Real space-weather events", "nasa-evidence": "NASA standards and evidence",
  "synthetic-calibrated": "Published norms (calibrated model)", authored: "Fictional story",
};

export function DataSources({ onClose }: { onClose: () => void }) {
  const [data, setData] = useState<DatasetsSummary | null>(null);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => { getDatasets().then(setData).catch((e) => setErr(e instanceof Error ? e.message : String(e))); }, []);
  const active = data?.sources.filter((s) => s.status === "active") ?? [];
  const planned = data?.sources.filter((s) => s.status !== "active") ?? [];
  const total = Object.values(data?.crew_observations_by_provenance ?? {}).reduce((a, b) => a + b, 0);

  return (
    <Modal title="Data sources" eyebrow="Where every number comes from" onClose={onClose}>
      {err && <div className="banner" role="alert"><div><b>Could not load the data catalogue.</b> {err}</div></div>}
      {!data && !err && <p className="muted"><span className="spinner" />Loading…</p>}
      {data && (
        <div className="ds">
          <p className="pp-lead">
            {data.crew.length} crew passports · {total.toLocaleString()} pre-flight observations:{" "}
            {Object.entries(data.crew_observations_by_provenance).map(([p, n]) => (
              <span key={p} className="ds-prov"><ProvBadges provenance={p} /> <span className="mono">{n.toLocaleString()}</span></span>
            ))}
          </p>
          <h3 className="ds-h">In use</h3>
          <ul className="ds-list">
            {active.map((s) => (
              <li key={s.id}>
                <div className="ds-top">
                  <b>{s.url ? <a href={s.url} target="_blank" rel="noreferrer">{s.title}</a> : s.title}</b>
                  <span className="tag">{KIND[s.kind] ?? s.kind}</span>
                </div>
                <p className="muted ds-meta">
                  <code>{s.id}</code> · {s.license}
                  {Object.keys(s.rows).length > 0 && <> · {Object.entries(s.rows).map(([k, n]) => `${n.toLocaleString()} ${k}`).join(", ")}</>}
                </p>
              </li>
            ))}
          </ul>
          <h3 className="ds-h">Planned next</h3>
          <ul className="ds-list ds-planned">
            {planned.map((s) => (
              <li key={s.id}><a href={s.url} target="_blank" rel="noreferrer">{s.title}</a> <span className="muted">· {s.license}</span></li>
            ))}
          </ul>
          <p className="muted pp-note">No public time series of astronaut vital signs exist; real in-flight data needs a formal NASA LSDA/LSAH request. Until then, those values come from calibrated models and are labelled.</p>
        </div>
      )}
    </Modal>
  );
}
