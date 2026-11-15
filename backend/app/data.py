"""Read-only access to what the data pipeline builds (see README.md, "Data", and `python -m pipeline all`).

data/passports/<crew>.json  six-month pre-flight passport per crew member (fields, sessions, daily series)
data/warehouse/*.csv        long-format tables (observations, evidence, population norms, ...)
data/space_weather/*.json   NASA DONKI snapshot
data/catalog.yaml           every source: URL, licence, status
Nothing here touches the network; a missing file just means "no data".
"""
import csv
import json
import logging
from functools import lru_cache
from pathlib import Path

import yaml

DATA = Path(__file__).resolve().parents[2] / "data"
log = logging.getLogger(__name__)

# engine baseline key -> (passport field metric, how to read it)
BASELINE_KEYS = {
    "lymphocytes_abs": "lymphocytes_abs", "hemoglobin": "hemoglobin", "glucose": "glucose",
    "hr_rest": "hr_rest", "bp_sys": "bp_sys", "bp_dia": "bp_dia", "spo2": "spo2", "temp": "temp_oral",
    "pvt_rt": "pvt_rt", "body_mass": "body_mass", "sleep_hours": "sleep_hours", "hrv_rmssd": "hrv_rmssd",
}
PERSONAL_RANGE_METRICS = ("hr_rest", "hrv_rmssd", "sleep_hours", "spo2", "steps", "skin_temp_dev")
LAB_RANGE_METRICS = ("wbc", "lymphocytes_abs", "neutrophils_abs", "hemoglobin", "hematocrit", "platelets",
                     "glucose", "sodium", "potassium", "calcium", "creatinine", "egfr", "bun", "albumin",
                     "alt", "ast")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


@lru_cache(maxsize=None)
def crew_passport(crew_id: str) -> dict | None:
    path = DATA / "passports" / f"{crew_id}.json"
    if not path.is_file():
        log.warning("no passport data for %s (run `python -m pipeline all`)", crew_id)
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def crew_ids() -> list[str]:
    """Demo flight crew first, then CM-2 (the single-person passport), as the pipeline builds them."""
    folder = DATA / "passports"
    ids = (p.stem for p in folder.glob("*.json")) if folder.is_dir() else ()
    return sorted(ids, key=lambda c: (c == "CM-2", c))


def _field(doc: dict, metric: str, field_id: str | None = None) -> dict | None:
    rows = [f for f in doc["fields"] if f["metric"] == metric and (field_id is None or f["field_id"] == field_id)]
    return rows[0] if rows else None


def passport_baselines(crew_id: str) -> dict:
    """What the rule engine needs from a crew member's passport (data/passports)."""
    doc = crew_passport(crew_id)
    return engine_inputs(doc) if doc else {}


def engine_inputs(doc: dict) -> dict:
    """What the rule engine needs from a passport document: baselines, personal ranges, lab reference ranges.
    Used for the pipeline passports and for passports imported in the "My crew" mode."""
    baselines, ranges, labs = {}, {}, {}
    for key, metric in BASELINE_KEYS.items():
        f = _field(doc, metric, "H1" if metric == "sleep_hours" else None)
        v = _num(f.get("value")) if f else None
        if v is not None and f.get("readiness") != "missing":
            baselines[key] = round(v, 2)
    for metric in PERSONAL_RANGE_METRICS:
        f = _field(doc, metric)
        if f and _num(f.get("lo")) is not None:
            ranges[metric] = {"lo": _num(f["lo"]), "hi": _num(f.get("hi")), "n": int(_num(f.get("n")) or 0),
                              "ready": f.get("readiness") == "ready", "rebase14": _num(f.get("rebase14"))}
    for metric in LAB_RANGE_METRICS:
        f = _field(doc, metric)
        if f and (_num(f.get("lo")) is not None or _num(f.get("hi")) is not None):
            labs[metric] = {"lo": _num(f.get("lo")), "hi": _num(f.get("hi"))}
    return {"baselines": baselines, "personal_ranges": ranges, "lab_ranges": labs,
            "baselines_source": source_line(doc)}


def source_line(doc: dict) -> str:
    imp = doc.get("import")
    if imp:
        line = f"Imported file {imp.get('filename', '')}: {imp.get('used', 0)} values, L{imp.get('first')}..L{imp.get('last')}"
        if imp.get("lab_ref_fallback"):
            line += "; lab reference ranges not in the file: standard ranges from the Inspiration4 lab report"
        return line
    names = {"labs": "labs: NASA OSDR Inspiration4", "exams": "exams: NHANES 2011-2012", "daily": "daily: LifeSnaps"}
    parts = [f"{names[d['field_group']]} {d.get('donor_subject_id', '')}".rstrip()
             for d in doc.get("donors") or [] if d.get("field_group") in names]
    return "Six-month passport (L-180..L-1)" + (" - " + "; ".join(parts) if parts else "")


@lru_cache(maxsize=None)
def table(name: str) -> tuple[dict, ...]:
    path = DATA / "warehouse" / f"{name}.csv"
    if not path.is_file():
        return ()
    with open(path, newline="", encoding="utf-8") as f:
        return tuple(csv.DictReader(f))


@lru_cache(maxsize=1)
def catalog() -> list[dict]:
    path = DATA / "catalog.yaml"
    if not path.is_file():
        return []
    return yaml.safe_load(path.read_text(encoding="utf-8")).get("sources", [])


@lru_cache(maxsize=1)
def sep_events() -> tuple[dict, ...]:
    path = DATA / "space_weather" / "donki_sep.json"
    if not path.is_file():
        return ()
    doc = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for e in doc.get("events", []):
        out.append({"sep_id": e.get("sepID"), "time": e.get("eventTime"), "link": e.get("link"),
                    "instruments": [i.get("displayName") for i in e.get("instruments") or []],
                    "linked": [x.get("activityID") for x in e.get("linkedEvents") or []]})
    return tuple(out)


@lru_cache(maxsize=1)
def biodosimetry_model() -> dict | None:
    path = DATA / "warehouse" / "biodosimetry_model.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def sep_event(sep_id: str) -> dict | None:
    return next((e for e in sep_events() if e["sep_id"] == sep_id), None)


def environment(profile: str, metric: str = "dose_equivalent_rate") -> dict | None:
    """Published radiation dose rate for a mission profile (MSL RAD, Chang'e-4 LND)."""
    for r in table("environment"):
        if r["profile"] == profile and r["metric"] == metric:
            return {**r, "value": float(r["value"])}
    return None


@lru_cache(maxsize=1)
def incidence() -> dict:
    """In-flight frequency per condition (NASA IMM / ISS clinical events, as summarised in the knowledge base)."""
    out = {}
    for r in table("evidence"):
        # one main row per condition; rows with a `variant` (another cohort, repeat flight, ...) are reference only
        if r["kind"] == "incidence" and not r.get("variant") and _num(r["value"]) is not None:
            note = r["note"].split(". ")[0].rstrip(".")
            out.setdefault(r["target"], {"value": float(r["value"]), "unit": r["unit"], "ref": r["ref_key"], "name": note})
    return out


@lru_cache(maxsize=1)
def space_effects() -> tuple[dict, ...]:
    """In-flight shifts (HRP evidence reports): target metric, kind (shift / shift_pct / level), value, onset days."""
    out = []
    for r in table("evidence"):
        # only rows with a single value and an onset time drive the expected-today facts (ranges, maxima, profiles
        # without an onset are reference only)
        if (r["kind"] == "space_effect" and r["op"] in ("shift", "shift_pct", "level") and r["onset_days"]
                and _num(r["value"]) is not None):
            out.append({"key": r["key"], "target": r["target"], "kind": r["op"], "value": float(r["value"]),
                        "onset_days": float(r["onset_days"]), "ref": r["ref_key"]})
    return tuple(out)


def series_stats(crew_id: str, metric: str) -> dict | None:
    """Last value, median, SD and lag-1 autocorrelation of a passport daily series (for continuing it into flight)."""
    doc = crew_passport(crew_id)
    pts = [v for _, v, _ in (doc or {}).get("series", {}).get(metric, [])]
    if len(pts) < 10:
        return None
    med = sorted(pts)[len(pts) // 2]
    mu = sum(pts) / len(pts)
    var = sum((x - mu) ** 2 for x in pts) / len(pts)
    num = sum((a - mu) * (b - mu) for a, b in zip(pts, pts[1:]))
    phi = max(0.0, min(0.9, num / (var * len(pts)))) if var else 0.3
    return {"last": pts[-1], "median": med, "sd": var ** 0.5, "phi": phi}


def biodose_classify(fold_changes: dict) -> dict | None:
    """Nearest-centroid dose bucket from gene fold changes (log2 vs the person's own unexposed sample)."""
    bio = biodosimetry_model()
    if not bio:
        return None
    genes = [g for g in bio["genes"] if g in fold_changes]
    if len(genes) < 5:
        return {"error": f"need at least 5 of the panel genes, got {len(genes)}", "panel": bio["genes"]}
    dist = {k: sum((fold_changes[g] - c[g]) ** 2 for g in genes) ** 0.5 for k, c in bio["centroids"].items()}
    best = min(dist, key=dist.get)
    return {"bucket": best, "distances": {k: round(v, 3) for k, v in dist.items()}, "genes_used": genes,
            "buckets_gy": bio["buckets"], "model_accuracy_held_out": bio["loocv_accuracy"]}


def datasets_summary() -> dict:
    """Per source: catalog entry + how many warehouse rows it contributes, by provenance."""
    counts: dict[str, dict] = {}
    for r in table("observations"):
        for src in r["source_id"].split(";"):
            c = counts.setdefault(src, {})
            c[r["provenance"]] = c.get(r["provenance"], 0) + 1
    sources = []
    for s in catalog():
        sid = s.get("id")
        rows = counts.get(sid, {})
        if sid == "DONKI":
            rows = {"real-events": len(sep_events())}
        if sid == "NHANES-2011":
            rows = {**rows, "population-norm-rows": len(table("population_norms"))}
        if sid == "NOAA-SEP":
            rows = {"real-events": sum(1 for e in table("events") if e["source_id"] == "NOAA-SEP")}
        if sid in ("MSL-RAD", "CE4-LND"):
            rows = {"dose-rate-rows": sum(1 for e in table("environment") if e["source_id"] == sid)}
        if sid == "OSD-410":
            bio = biodosimetry_model()
            rows = {"samples": bio["n_samples"], "genes": len(bio["genes"])} if bio else {}
        if sid == "OSD-572":
            rows = {"real-astronaut": sum(1 for r in table("observations") if r["source_id"] == "OSD-572")}
        if sid in ("BIGIDEAS", "MIMIC-DEMO"):
            rows = {"used-for": "validation (data/validation.md)"}
        if sid in ("IMM", "NASA-LIMITS", "HRP-EFFECTS"):
            kind = {"IMM": "incidence", "NASA-LIMITS": "limit", "HRP-EFFECTS": "space_effect"}[sid]
            rows = {"evidence-rows": sum(1 for e in table("evidence") if e["kind"] == kind)}
        sources.append({**{k: s.get(k) for k in ("id", "title", "url", "license", "access", "kind", "status",
                                                 "citation")}, "rows": rows})
    prov: dict[str, int] = {}
    for r in table("observations"):
        if r["subject_id"] in crew_ids():
            prov[r["provenance"]] = prov.get(r["provenance"], 0) + 1
    return {"sources": sources, "crew": crew_ids(), "crew_observations_by_provenance": prov}
