"""Inspiration4 (NASA OSDR OSD-569 / OSD-575): every crew member, every timepoint, every CBC/CMP analyte + CRP.

Rows go to `observations` with the lab reference range in ref_lo/ref_hi. Timepoints: L-92, L-44, L-3 (days before
launch) and R+1, R+45, R+82, R+194 (days after return). Crew codes stay as published (C001-C004); we never try to
re-identify anyone.

The raw files stay untouched; known errors in them are fixed here, in code, and every touched value says so in
`quality` (see README.md, "Inspiration4 corrections"):
  corrected  the value in the file sits in the wrong column; the re-aligned value is used
  derived    the file has no value; computed from the same draw with a standard formula
  suspect    kept as published but flagged as a likely sample-handling artifact (not fed to the rules)
"Not reported" cells ("NA" or blank) are never read as zero: they produce no row.
"""
import collections
import csv
import io
import math
import re
import zipfile

from .common import DATA, REAL_ASTRONAUT

I4 = DATA / "inspiration4"
CBC = I4 / "LSDS-7_Complete_Blood_Count_CBC_TRANSFORMED.csv"
CMP = I4 / "LSDS-8_Comprehensive_Metabolic_Panel_CMP_TRANSFORMED.csv"
EVE_CV = I4 / "LSDS-8_Multiplex_serum_cardiovascular_EvePanel_TRANSFORMED.csv"
ISA_575 = I4 / "OSD-575_metadata_OSD-575-ISA.zip"

# analyte column stem -> (metric name in data/metrics.yaml, unit as published, fixed unit, scale)
CBC_MAP = {
    "white_blood_cell_count": ("wbc", "10^3/uL"),
    "red_blood_cell_count": ("rbc", "10^6/uL"),
    "hemoglobin": ("hemoglobin", "g/dL"),  # published column says "percent" but values are g/dL
    "hematocrit": ("hematocrit", "%"),
    "platelet_count": ("platelets", "10^3/uL"),
    "absolute_neutrophils": ("neutrophils_abs", "cells/uL"),
    "absolute_lymphocytes": ("lymphocytes_abs", "cells/uL"),
    "absolute_monocytes": ("monocytes_abs", "cells/uL"),
    "absolute_eosinophils": ("eosinophils_abs", "cells/uL"),
    "absolute_basophils": ("basophils_abs", "cells/uL"),
    "neutrophils": ("neutrophils_pct", "%"),
    "lymphocytes": ("lymphocytes_pct", "%"),
    "monocytes": ("monocytes_pct", "%"),
    "eosinophils": ("eosinophils_pct", "%"),
    "basophils": ("basophils_pct", "%"),
    "mcv": ("mcv", "fL"),
    "mch": ("mch", "pg"),
    "mchc": ("mchc", "g/dL"),
    "rdw": ("rdw", "%"),
    "mpv": ("mpv", "fL"),
}
CMP_MAP = {
    "glucose": ("glucose", "mg/dL"),
    "sodium": ("sodium", "mmol/L"),
    "potassium": ("potassium", "mmol/L"),
    "chloride": ("chloride", "mmol/L"),
    "carbon_dioxide": ("bicarbonate", "mmol/L"),
    "calcium": ("calcium", "mg/dL"),
    "urea_nitrogen_bun": ("bun", "mg/dL"),
    "creatinine": ("creatinine", "mg/dL"),
    "egfr_non_african_american": ("egfr", "mL/min/1.73m2"),
    "albumin": ("albumin", "g/dL"),
    "globulin": ("globulin", "g/dL"),
    "total_protein": ("total_protein", "g/dL"),
    "alkaline_phosphatase": ("alp", "U/L"),
    "alt": ("alt", "U/L"),
    "ast": ("ast", "U/L"),
    "total_bilirubin": ("bilirubin", "mg/dL"),
}
UNITS = {metric: unit for metric, unit in (*CBC_MAP.values(), *CMP_MAP.values())}

# C003 at L-92 (CBC): the lab file has no MCH for this draw, so every value after MCV sits one analyte to the right
# (same error in the SUBMITTED and TRANSFORMED files; the percentages and reference ranges are not shifted).
# Re-aligned values, checked against the same draw: MCH = Hb/RBC x 10 = 13.2/4.46 x 10 = 29.6;
# MCHC = Hb/Hct x 100 = 13.2/40.7 x 100 = 32.4; absolute counts = differential % x WBC 9,600/uL
# (71.1% -> 6826, 20.8% -> 1997, 6.4% -> 614, 1.3% -> 125). Source: team data review (Crew_Health_Console_review, 2026-11).
C003_L92 = ("I4-C003", "L", -92)
C003_L92_SHIFTED = ("platelets", 12.9)  # applied only while the file still has the shifted value
C003_L92_FIX = {"mch": 29.6, "mchc": 32.4, "rdw": 12.9, "platelets": 330.0, "mpv": 10.1, "neutrophils_abs": 6826.0,
                "lymphocytes_abs": 1997.0, "monocytes_abs": 614.0, "eosinophils_abs": 125.0}
C003_L92_DERIVED = {"basophils_abs": 38.0}  # not in the file once re-aligned: 0.4% x 9,600/uL

# C003 is female (OSD-575 ISA "Characteristics[Sex]"), but the lab report used male reference ranges at L-92, L-44
# and L-3 (Hb 13.2-17.1, creatinine 0.6-1.35, ...); from R+1 it labels her analytes "(FEMALE)". A person's reference
# range does not change between draws, so her own post-flight (female) ranges replace the pre-flight ones.
RANGES_FROM_POSTFLIGHT = ("I4-C003",)

# R+45: glucose 44, 36 and 43 mg/dL in three of the four crew at the same draw, with a normal anion gap and enzymes;
# C004 also reads potassium 5.9 mmol/L at that draw. Low glucose plus high potassium is the pattern of serum left on
# the cells too long before separation (glycolysis, potassium leak). Inference, so the values stay as published.
SUSPECT = {("I4-C002", "R", 45): ("glucose",), ("I4-C003", "R", 45): ("glucose",),
           ("I4-C004", "R", 45): ("glucose", "potassium")}

_SAMPLE = re.compile(r"^(C00\d)_[a-z-]+_([LR][+-]\d+)")
_VALUE_COL = re.compile(r"^(?P<stem>.+?)_value_(?P<unit>.+)$")


def _num(s):
    """Float, or None for blank, "NA" and anything non-numeric or non-finite ("not reported" is never zero)."""
    try:
        v = float(s)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def _timepoint(tp: str) -> tuple[str, int]:
    kind, sign, days = tp[0], tp[1], int(tp[2:])
    return kind, (-days if sign == "-" else days)


def _session(kind: str, t: int) -> str:
    return f"i4-{kind}{'+' if t > 0 else ''}{t}"


def _row(subject, source_id, t_kind, t, metric, value, ref_lo=None, ref_hi=None, quality=""):
    return {"subject_id": subject, "source_id": source_id, "t_kind": t_kind, "t": t, "metric": metric, "value": value,
            "unit": UNITS.get(metric, ""), "ref_lo": ref_lo, "ref_hi": ref_hi, "provenance": REAL_ASTRONAUT,
            "session_id": _session(t_kind, t), "quality": quality}


def _panel(path, mapping, source_id):
    rows = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        stems = {}
        cols = set(reader.fieldnames)
        for col in reader.fieldnames:
            m = _VALUE_COL.match(col)
            if m and m.group("stem") in mapping:
                stem, unit = m.group("stem"), m.group("unit")
                hi = f"{stem}_range_max_{unit}"
                if hi not in cols:  # the CMP file names two of them "alt_max_..." and "ast_max_..."
                    hi = f"{stem}_max_{unit}"
                stems[stem] = (col, f"{stem}_range_min_{unit}", hi)
        for r in reader:
            m = _SAMPLE.match(r["Sample Name"])
            if not m:
                continue
            crew, tp = m.groups()
            t_kind, t = _timepoint(tp)
            for stem, (vcol, locol, hicol) in sorted(stems.items()):
                v = _num(r.get(vcol))
                if v is None:
                    continue
                metric, _unit = mapping[stem]
                rows.append(_row(f"I4-{crew}", source_id, t_kind, t, metric, v, _num(r.get(locol)), _num(r.get(hicol))))
    return rows


def _crp():
    rows = []
    with open(EVE_CV, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            m = _SAMPLE.match(r["Sample Name"])
            v = _num(r.get("crp_concentration_picogram_per_milliliter"))
            if not m or v is None:
                continue
            crew, tp = m.groups()
            t_kind, t = _timepoint(tp)
            row = _row(f"I4-{crew}", "OSD-575-EVE-CV", t_kind, t, "crp", round(v / 1e6, 3))
            rows.append({**row, "unit": "mg/L"})
    return rows


def _draws(rows) -> dict:
    by = collections.defaultdict(dict)
    for r in rows:
        by[(r["subject_id"], r["t_kind"], r["t"])][r["metric"]] = r
    return by


def _own_range(rows, subject, metric):
    """The reference range this person's other draws report for the metric (most common one)."""
    seen = collections.Counter((r["ref_lo"], r["ref_hi"]) for r in rows
                               if r["subject_id"] == subject and r["metric"] == metric and r["ref_lo"] is not None)
    return seen.most_common(1)[0][0] if seen else (None, None)


def _fix_c003_l92(rows):
    draw = _draws(rows).get(C003_L92, {})
    metric, shifted = C003_L92_SHIFTED
    if metric not in draw or draw[metric]["value"] != shifted:
        return  # the file no longer has the shifted row
    for quality, fix in (("corrected", C003_L92_FIX), ("derived", C003_L92_DERIVED)):
        for m, v in fix.items():
            if m in draw:
                draw[m].update(value=v, quality=quality)
            else:
                lo, hi = _own_range(rows, C003_L92[0], m)
                rows.append(_row(C003_L92[0], "OSD-569", C003_L92[1], C003_L92[2], m, v, lo, hi, quality))


# missing red-cell index -> (formula over the same draw, inputs)
_INDICES = {
    "mchc": (lambda d: d["hemoglobin"] / d["hematocrit"] * 100, ("hemoglobin", "hematocrit")),
    "mcv": (lambda d: d["hematocrit"] / d["rbc"] * 10, ("hematocrit", "rbc")),
    "mch": (lambda d: d["hemoglobin"] / d["rbc"] * 10, ("hemoglobin", "rbc")),
}


def _derive_indices(rows):
    """MCHC = Hb/Hct x 100, MCV = Hct/RBC x 10, MCH = Hb/RBC x 10 where the lab left the index blank."""
    for (subject, t_kind, t), draw in sorted(_draws(rows).items()):
        if "rbc" not in draw and "hemoglobin" not in draw:
            continue  # not a CBC draw
        vals = {m: r["value"] for m, r in draw.items()}
        for m, (formula, inputs) in _INDICES.items():
            if m in vals or not all(vals.get(i) for i in inputs):
                continue
            lo, hi = _own_range(rows, subject, m)
            rows.append(_row(subject, "OSD-569", t_kind, t, m, round(formula(vals), 1), lo, hi, "derived"))


def _fix_ranges(rows):
    for subject in RANGES_FROM_POSTFLIGHT:
        post = collections.defaultdict(collections.Counter)
        for r in rows:
            if r["subject_id"] == subject and r["t_kind"] == "R" and r["ref_lo"] is not None:
                post[r["metric"]][(r["ref_lo"], r["ref_hi"])] += 1
        for r in rows:
            if r["subject_id"] == subject and r["t_kind"] == "L" and post.get(r["metric"]):
                r["ref_lo"], r["ref_hi"] = post[r["metric"]].most_common(1)[0][0]


def _flag_suspect(rows):
    for r in rows:
        if r["metric"] in SUSPECT.get((r["subject_id"], r["t_kind"], r["t"]), ()):
            r["quality"] = "suspect"


def observations() -> list[dict]:
    rows = _panel(CBC, CBC_MAP, "OSD-569") + _panel(CMP, CMP_MAP, "OSD-575") + _crp()
    _fix_c003_l92(rows)
    _derive_indices(rows)
    _fix_ranges(rows)
    _flag_suspect(rows)
    return sorted(rows, key=lambda r: (r["subject_id"], r["t_kind"], r["t"], r["metric"]))


def sexes() -> dict[str, str]:
    """Crew code -> "M"/"F" from the OSD-575 study metadata (ISA-Tab sample table, Characteristics[Sex])."""
    with zipfile.ZipFile(ISA_575) as z:
        name = next(n for n in z.namelist() if n.startswith("s_"))
        with z.open(name) as f:
            rows = list(csv.DictReader(io.TextIOWrapper(f, encoding="utf-8"), delimiter="\t"))
    return {f"I4-{r['Source Name']}": {"Male": "M", "Female": "F"}[r["Characteristics[Sex]"]] for r in rows}


def subjects() -> list[dict]:
    sex = sexes()
    return [{"subject_id": f"I4-C00{i}", "source_id": "OSD-569", "kind": "astronaut", "sex": sex.get(f"I4-C00{i}", ""),
             "age_band": "", "note": "Inspiration4 crew code as published; sex from the OSD-575 metadata; age not used"}
            for i in range(1, 5)]
