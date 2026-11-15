"""Data pipeline entry point.

    pipeline/.venv/bin/python -m pipeline fetch      # download raw sources (NHANES, LifeSnaps, DONKI)
    pipeline/.venv/bin/python -m pipeline build      # transform + passports -> data/warehouse, data/passports
    pipeline/.venv/bin/python -m pipeline all        # both

Raw files live in data/raw/ (git-ignored); everything under data/warehouse and data/passports is derived and
reproducible. See README.md, "Data".
"""
import csv
import json
import sys

import yaml

from . import extras, fetch, inspiration4, lifesnaps, nhanes, passport
from .common import DATA, EVIDENCE, SPACE_WEATHER, write_table


def _csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# What each evidence value is (mean change, observed range, maximum, proportion, team threshold, ...), its spread,
# events / denominator, timepoint, population and method. Optional in the source CSVs; see README.md, "Data".
EVIDENCE_DETAIL = ["value_type", "uncertainty", "uncertainty_type", "events", "denominator", "denominator_unit",
                   "timepoint", "comparison", "population", "method", "detail", "variant"]


def _detail(r: dict) -> dict:
    return {c: r.get(c) or "" for c in EVIDENCE_DETAIL}


def evidence_rows() -> list[dict]:
    rows = []
    for r in _csv(EVIDENCE / "limits.csv"):
        rows.append({"key": r["key"], "kind": "limit", "target": r["target"], "op": r["op"], "value": r["value"],
                     "lo": r["lo"], "hi": r["hi"], "unit": r["unit"], "onset_days": "", "ref_key": r["ref_key"],
                     "note": r["note"], **_detail(r)})
    for r in _csv(EVIDENCE / "space_effects.csv"):
        rows.append({"key": r["key"], "kind": "space_effect", "target": r["target"], "op": r["kind"],
                     "value": r["value"], "lo": r["lo"], "hi": r["hi"], "unit": r["unit"],
                     "onset_days": r["onset_days"], "ref_key": r["ref_key"], "note": r["note"], **_detail(r)})
    for r in _csv(EVIDENCE / "imm_incidence.csv"):
        variant = r.get("variant") or ""
        rows.append({"key": f"incidence_{r['condition_id']}" + (f"_{variant}" if variant else ""), "kind": "incidence",
                     "target": r["condition_id"], "op": "eq", "value": r["value"], "lo": r["lo"], "hi": r["hi"],
                     "unit": r["unit"], "onset_days": "", "ref_key": r["ref_key"],
                     "note": f"{r['name']}. {r['note']}".strip(), **_detail(r)})
    for r in _csv(EVIDENCE / "norms.csv"):
        rows.append({"key": f"norm_{r['metric']}", "kind": "norm", "target": r["metric"].split(":")[0], "op": "dist",
                     "value": r["mean"], "lo": r["lo"], "hi": r["hi"], "unit": r["unit"], "onset_days": "",
                     "ref_key": r["ref_key"], "note": f"sd={r['sd']}; {r['note']}", **_detail(r)})
    return rows


def event_rows() -> list[dict]:
    path = SPACE_WEATHER / "donki_sep.json"
    if not path.exists():
        return []
    doc = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for e in doc["events"]:
        inst = "; ".join(i.get("displayName", "") for i in e.get("instruments") or [])
        rows.append({"event_id": e["sepID"], "type": "SEP", "t_start": e["eventTime"], "t_end": "",
                     "magnitude": "", "source_id": "DONKI", "ext_ref": e.get("link", ""), "note": inst})
    for e in extras.noaa_events():
        rows.append({**e, "t_end": "", "source_id": "NOAA-SEP", "ext_ref": "https://umbra.nascom.nasa.gov/SEP/",
                     "note": f">10 MeV peak {e['magnitude']:g} pfu ({extras.s_scale(e['magnitude'])})"})
    return sorted(rows, key=lambda r: (r["source_id"], r["t_start"], r["event_id"]))


def environment_rows() -> list[dict]:
    src = {"ZEITLIN2013": "MSL-RAD", "HASSLER2014": "MSL-RAD", "ZHANG2020": "CE4-LND"}
    return [{"profile": r["profile"], "metric": r["metric"], "value": r["value"], "lo": r["lo"], "hi": r["hi"],
             "unit": r["unit"], "source_id": src.get(r["ref_key"], ""), "ref_key": r["ref_key"], "note": r["note"]}
            for r in extras.dose_rates()]


def source_rows() -> list[dict]:
    cat = yaml.safe_load((DATA / "catalog.yaml").read_text(encoding="utf-8"))["sources"]
    return [{"source_id": s["id"], "title": s.get("title", ""), "url": s.get("url", ""), "license": s.get("license", ""),
             "access": s.get("access", ""), "kind": s.get("kind", ""), "citation": s.get("citation", "")} for s in cat]


def build():
    subjects = inspiration4.subjects()
    i4 = inspiration4.observations()
    print(f"inspiration4: {len(i4)} observations")
    if not nhanes.available():
        print("! NHANES raw files missing: run `python -m pipeline fetch` (exam donors will be empty)")
    if not lifesnaps.available():
        print("! LifeSnaps raw files missing: run `python -m pipeline fetch` (daily donors will be empty)")
    pp = passport.build(i4, subjects)
    norms = nhanes.norms(nhanes.load()) if nhanes.available() else []
    write_table("sources", source_rows())
    write_table("subjects", sorted(subjects, key=lambda r: r["subject_id"]))
    write_table("observations", i4 + pp["observations"])
    write_table("crew_donors", pp["crew_donors"])
    write_table("sessions", pp["sessions"])
    write_table("passport_fields", pp["passport_fields"])
    write_table("events", event_rows())
    write_table("evidence", evidence_rows())
    write_table("population_norms", norms)
    write_table("environment", environment_rows())
    bio = extras.biodosimetry()
    if bio:
        (DATA / "warehouse" / "biodosimetry_model.json").write_text(json.dumps(bio, indent=1), encoding="utf-8")
        print(f"biodosimetry: {len(bio['genes'])} genes, {bio['n_samples']} samples, LOVO accuracy {bio['loocv_accuracy']}")
    print(f"passports: {len({r['crew_id'] for r in pp['passport_fields']})} crew, "
          f"{len(pp['observations'])} observations, {len(pp['passport_fields'])} fields; "
          f"population norms: {len(norms)} rows")


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "all"
    if cmd in ("fetch", "all"):
        fetch.run()
    if cmd in ("build", "all"):
        build()
    if cmd not in ("fetch", "build", "all"):
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
