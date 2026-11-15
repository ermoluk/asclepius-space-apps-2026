"""More real sources: MMASH (saliva hormones, PSQI, MEQ), PTB-XL+ (12-lead ECG intervals), PhysioNet head-up tilt
(orthostatic response), NOAA solar proton events (peak flux), published radiation dose rates, and an OSD-410
biodosimetry model. Each loader returns plain rows; missing raw files simply give nothing.
"""
import csv
import gzip
import io
import json
import math
import re
import statistics
import zipfile

import pandas as pd

from .common import EVIDENCE, RAW

# ---------------------------------------------------------------------------------------------- MMASH
MMASH_ZIP = RAW / "mmash" / "MMASH.zip"


def mmash_donors() -> list[dict]:
    """22 healthy young men, 24 h each: saliva cortisol/melatonin (normalised units), PSQI, MEQ, STAI."""
    if not MMASH_ZIP.exists():
        return []
    out = []
    with zipfile.ZipFile(MMASH_ZIP) as z:
        users = sorted({m.group(1) for n in z.namelist() if (m := re.match(r"DataPaper/(user_\d+)/", n))},
                       key=lambda u: int(u.split("_")[1]))
        for u in users:
            def read(name):
                path = f"DataPaper/{u}/{name}"
                if path not in z.namelist():
                    return None
                return pd.read_csv(io.BytesIO(z.read(path)))
            info, q, sal = read("user_info.csv"), read("questionnaire.csv"), read("saliva.csv")
            if info is None or q is None or sal is None or len(sal) < 2:
                continue
            row = {"subject_id": f"MMASH-{u.split('_')[1]}", "sex": str(info["Gender"].iloc[0]).strip(),
                   "age": float(info["Age"].iloc[0]) if pd.notna(info["Age"].iloc[0]) else None,
                   "psqi": float(q["Pittsburgh"].iloc[0]), "meq": float(q["MEQ"].iloc[0])}
            for _, s in sal.iterrows():
                when = "bed" if "before" in str(s["SAMPLES"]) else "wake"
                row[f"cortisol_{when}"] = float(s["Cortisol NORM"])
                row[f"melatonin_{when}"] = float(s["Melatonin NORM"])
            if all(k in row for k in ("cortisol_bed", "cortisol_wake", "melatonin_bed", "melatonin_wake")):
                out.append(row)
    return out


def pick_mmash(pool, sex, used, poor_sleeper=False):
    cand = [p for p in pool if p["sex"] == sex and p["subject_id"] not in used]
    if not cand:
        return None
    # story consistency: a poor sleeper (P-10) gets a donor with PSQI > 5 when one exists
    if poor_sleeper and any(p["psqi"] > 5 for p in cand):
        cand = [p for p in cand if p["psqi"] > 5]
    elif not poor_sleeper and any(p["psqi"] <= 5 for p in cand):
        cand = [p for p in cand if p["psqi"] <= 5]
    return sorted(cand, key=lambda p: p["subject_id"])[0]


# ---------------------------------------------------------------------------------------------- PTB-XL
PTBXL_DB = RAW / "ptbxl" / "ptbxl_database.csv"
PTBXL_FEAT = RAW / "ptbxl" / "12sl_features.csv"
ECG_COLS = {"HR_Ventr_Global": "ecg_hr", "PR_Int_Global": "ecg_pr", "QRS_Dur_Global": "ecg_qrs",
            "QT_Int_Global": "ecg_qt", "QT_IntBazett_Global": "ecg_qtc"}


def ptbxl_normals() -> pd.DataFrame:
    """Cardiologist-validated normal sinus-rhythm ECGs with 12SL interval measurements (PTB-XL + PTB-XL+)."""
    if not (PTBXL_DB.exists() and PTBXL_FEAT.exists()):
        return pd.DataFrame()
    db = pd.read_csv(PTBXL_DB, usecols=["ecg_id", "age", "sex", "scp_codes", "validated_by_human", "baseline_drift",
                                        "static_noise", "burst_noise", "electrodes_problems", "pacemaker"])
    norm = db["scp_codes"].str.contains(r"'NORM': 100\.0") & db["scp_codes"].str.contains(r"'SR'")
    clean = db[["baseline_drift", "static_noise", "burst_noise", "electrodes_problems", "pacemaker"]].isna().all(axis=1)
    db = db[norm & clean & db["validated_by_human"]]
    feat = pd.read_csv(PTBXL_FEAT, usecols=["ecg_id", *ECG_COLS])
    df = db.merge(feat, on="ecg_id").dropna(subset=list(ECG_COLS)).rename(columns=ECG_COLS)
    df["sex"] = df["sex"].map({0: "M", 1: "F"})
    return df.sort_values("ecg_id")


def pick_ecg(df, sex, age, used):
    cand = df[(df["sex"] == sex) & (~df["ecg_id"].isin(used)) & df["ecg_pr"].between(120, 200)
              & df["ecg_qrs"].between(70, 110) & df["ecg_qtc"].between(360, 450)].copy()
    if cand.empty:
        return None
    cand["gap"] = (cand["age"] - age).abs()
    return cand.sort_values(["gap", "ecg_id"]).iloc[0]


# ---------------------------------------------------------------------------------------------- head-up tilt
TILT = RAW / "tilt" / "GE-71_Data_Summary_Table.csv"


def tilt_controls() -> list[dict]:
    """Healthy controls (55-75 y): supine baseline vs head-up tilt average (SBP, DBP, HR)."""
    if not TILT.exists():
        return []
    d = pd.read_csv(TILT, encoding="latin-1")
    d = d[d["Group"] == "Control"]
    out = []
    for i, r in d.reset_index(drop=True).iterrows():
        vals = [r.get(c) for c in ("SBP TILT Baseline", "DBP TILT Baseline", "HR TILT BASELINE", "TILT AVE1",
                                   "TILT AVE2", "TILT AVE")]
        if any(pd.isna(v) for v in vals):
            continue
        sbp0, dbp0, hr0, sbp1, dbp1, hr1 = map(float, vals)
        out.append({"subject_id": f"TILT-C{i + 1:02d}", "sex": str(r["Gender"]).strip(), "age": float(r["Age"]),
                    "ortho_sbp_supine": sbp0, "ortho_dbp_supine": dbp0, "ortho_hr_supine": round(hr0, 1),
                    "ortho_dsbp": round(sbp1 - sbp0, 1), "ortho_ddbp": round(dbp1 - dbp0, 1),
                    "ortho_dhr": round(hr1 - hr0, 1)})
    return out


def pick_tilt(pool, sex, used):
    cand = [p for p in pool if p["sex"] == sex and p["subject_id"] not in used] or \
           [p for p in pool if p["subject_id"] not in used]
    return sorted(cand, key=lambda p: (p["age"], p["subject_id"]))[0] if cand else None


# ---------------------------------------------------------------------------------------------- NOAA solar proton events
NOAA_SEP = RAW / "noaa-sep" / "sep_list.html"


def noaa_events() -> list[dict]:
    """NOAA SWPC list of solar proton events affecting the Earth environment (>10 MeV, peak flux in pfu), 1976-2017."""
    if not NOAA_SEP.exists():
        return []
    html = NOAA_SEP.read_text(encoding="latin-1")
    out, year = [], None
    for row in re.findall(r"<tr>(.*?)(?=<tr>|</table>)", html, re.S):
        cells = [re.sub(r"<[^>]+>|&nbsp;", " ", c).strip() for c in re.split(r"<td[^>]*>", row)[1:]]
        y = re.search(r"<strong>(\d{4})</strong>", row)
        if y:
            year = int(y.group(1))
            continue
        if year is None or len(cells) < 3:
            continue
        m_start = re.match(r"([A-Z][a-z]{2})\s+(\d{1,2})/(\d{4})", re.sub(r"\s+", " ", cells[0]))
        flux = re.sub(r"[^\d.]", "", cells[2])
        if not m_start or not flux:
            continue
        mon, day, hhmm = m_start.groups()
        out.append({"event_id": f"NOAA-{year}-{mon}{int(day):02d}-{hhmm}", "type": "SEP", "magnitude": float(flux),
                    "t_start": f"{year}-{mon}-{int(day):02d} {hhmm[:2]}:{hhmm[2:]}Z"})
    return out


def s_scale(pfu: float) -> str:
    return "S5" if pfu >= 1e5 else "S4" if pfu >= 1e4 else "S3" if pfu >= 1e3 else "S2" if pfu >= 100 else "S1"


# ---------------------------------------------------------------------------------------------- radiation dose rates
def dose_rates() -> list[dict]:
    with open(EVIDENCE / "dose_rates.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------------------------- OSD-410 biodosimetry
OSD410_MATRIX = RAW.parent / "osd-410" / "GSE63952_normalized_data_with_controls.txt.gz"
GPL = RAW / "osd410" / "GPL15207.txt"
# Radiation-responsive blood genes from the biodosimetry literature (p53 targets used by gene-expression dosimeters)
PANEL = ["CDKN1A", "GADD45A", "DDB2", "XPC", "FDXR", "AEN", "PHPT1", "CCNG1", "BBC3", "SESN1", "TNFRSF10B",
         "ZMAT3", "MDM2", "BAX", "TRIAP1", "RPS27L", "PCNA", "POLH", "ASCC3", "TIGAR"]
BUCKETS = (("none", 0.0, 0.0), ("low", 0.1, 0.35), ("high", 1.0, 2.0))


def biodosimetry() -> dict | None:
    """Fold change vs the same volunteer's 0 Gy sample at the same time point (the passport idea: compare a person
    with themselves). Nearest-centroid classifier on the panel genes; leave-one-volunteer-out accuracy."""
    if not (OSD410_MATRIX.exists() and GPL.exists()):
        return None
    probes = {}
    with open(GPL, encoding="utf-8", errors="replace") as f:
        header = None
        for line in f:
            if line.startswith(("#", "^", "!")):
                continue
            parts = line.rstrip("\n").split("\t")
            if header is None:
                header = parts
                i_id, i_sym = header.index("ID"), header.index("Gene Symbol")
                continue
            if len(parts) > i_sym:
                sym = parts[i_sym].split(" /// ")[0].strip()
                if sym in PANEL:
                    probes[parts[i_id]] = sym
    m = pd.read_csv(OSD410_MATRIX, sep="\t", index_col=0, compression="gzip")
    m = m.loc[m.index.intersection(list(probes))]
    m = m[[c for c in m.columns if c.startswith("SAMPLE_")]].apply(pd.to_numeric, errors="coerce")
    genes = m.groupby(m.index.map(probes)).mean()  # mean of probes per gene (log2)
    meta = []
    for c in genes.columns:
        mm = re.match(r"SAMPLE_([\d.]+)Gy_(\d+)h-(\d+)", c)
        if mm:
            meta.append((c, float(mm.group(1)), int(mm.group(2)), int(mm.group(3))))
    feats = {}
    for c, dose, hours, vol in meta:
        if dose == 0:
            # an unexposed sample is compared with the same volunteer's unexposed sample at another time point,
            # so the "none" class carries real day-to-day noise instead of an all-zero vector
            ctrl = next((cc for cc, d, h, v in sorted(meta, key=lambda x: abs(x[2] - hours))
                         if d == 0 and v == vol and h != hours), None)
        else:
            ctrl = next((cc for cc, d, h, v in meta if d == 0 and h == hours and v == vol), None)
        if ctrl is None:
            continue
        feats[c] = (genes[c] - genes[ctrl]).to_dict(), dose, hours, vol

    def bucket(d):
        return next(name for name, lo, hi in BUCKETS if lo <= d <= hi)

    def centroids(items):
        cents = {}
        for name, _, _ in BUCKETS:
            rows = [it[0] for it in items if bucket(it[1]) == name]
            if rows:
                cents[name] = {g: statistics.fmean(r[g] for r in rows) for g in genes.index}
        return cents

    def classify(cents, f):
        return min(cents, key=lambda k: math.dist([f[g] for g in genes.index], [cents[k][g] for g in genes.index]))

    items = [(*v, k) for k, v in feats.items()]
    vols = sorted({it[3] for it in items})
    hits = total = 0
    confusion = {}
    samples = []
    for v in vols:
        train = [it for it in items if it[3] != v]
        cents = centroids(train)
        for f, d, h, vv, name in (it for it in items if it[3] == v):
            pred, true = classify(cents, f), bucket(d)
            confusion[(true, pred)] = confusion.get((true, pred), 0) + 1
            hits += pred == true
            total += 1
            samples.append({"sample": name, "volunteer": vv, "dose_gy": d, "hours": h, "bucket": true,
                            "predicted_held_out": pred, "fold_changes": {g: round(f[g], 3) for g in genes.index}})
    final = centroids(items)
    ranked = sorted(genes.index, key=lambda g: -abs(final["high"][g] - final["none"][g]))
    return {"genes": list(genes.index), "top_genes": ranked[:8], "n_samples": total, "volunteers": len(vols),
            "loocv_accuracy": round(hits / total, 3) if total else None,
            "confusion": {f"{t}->{p}": n for (t, p), n in sorted(confusion.items())},
            "centroids": {k: {g: round(v, 4) for g, v in c.items()} for k, c in final.items()},
            "buckets": {name: [lo, hi] for name, lo, hi in BUCKETS},
            "samples": samples,
            "note": "Fold change (log2) vs the same volunteer's 0 Gy sample at the same time; ex vivo gamma rays."}



# ---------------------------------------------------------------------------------------------- microbiome (OSD-572)
METAPHLAN = RAW / "osdr" / "metaphlan_osd572.tsv"
MICRO_SITES = {"ORC": "microbiome_oral", "NAC": "microbiome_nasal", "ARM": "microbiome_skin_arm",
               "TZO": "microbiome_skin_forehead"}


def microbiome() -> dict:
    """Shannon diversity (species level, MetaPhlAn) per Inspiration4 crew code, timepoint and body site."""
    if not METAPHLAN.exists():
        return {}
    m = pd.read_csv(METAPHLAN, sep="\t", skiprows=1, index_col=0)
    sp = m[m.index.str.contains(r"\|s__") & ~m.index.str.contains(r"\|t__")]
    out = {}
    for col in sp.columns:
        mm = re.match(r"(C00\d)_([LR][+-]\d+|FD\d)_([A-Z0-9]+)$", col)
        if not mm or mm.group(3) not in MICRO_SITES:
            continue
        p = pd.to_numeric(sp[col], errors="coerce").fillna(0.0)
        p = p[p > 0]
        if p.empty:
            continue  # sample with no species-level reads (e.g. low biomass)
        p = p / p.sum()
        h = float(-(p * p.map(math.log)).sum())
        out.setdefault(f"I4-{mm.group(1)}", {}).setdefault(mm.group(2), {})[MICRO_SITES[mm.group(3)]] = \
            {"shannon": round(h, 3) if h is not None else None, "species": int((sp[col] > 0).sum())}
    return out


# ---------------------------------------------------------------------------------------------- balance (NHANES 2003-04)
BAX = RAW / "nhanes2003" / "BAX_C.xpt"
DEMO_C = RAW / "nhanes2003" / "DEMO_C.xpt"


def balance_pool() -> pd.DataFrame:
    """Modified Romberg test: 4 conditions (eyes open/closed, firm floor/foam), 30 s each; first trial, retried once."""
    if not (BAX.exists() and DEMO_C.exists()):
        return pd.DataFrame()
    b = pd.read_sas(BAX, format="xport", encoding="latin-1")
    d = pd.read_sas(DEMO_C, format="xport", encoding="latin-1")[["SEQN", "RIAGENDR", "RIDAGEYR"]]
    b = b[b["BAAEXSTS"] == 1].merge(d, on="SEQN")
    def cond(r, k):
        p1, p2 = r.get(f"BAXPFC{k}1"), r.get(f"BAXPFC{k}2")
        return 1.0 if p1 == 1 or p2 == 1 else (0.0 if p1 == 2 else math.nan)
    rows = []
    for _, r in b.iterrows():
        c = [cond(r, k) for k in (1, 2, 3, 4)]
        if any(math.isnan(x) for x in c):
            continue
        rows.append({"SEQN": int(r["SEQN"]), "sex": {1.0: "M", 2.0: "F"}.get(r["RIAGENDR"]), "age": float(r["RIDAGEYR"]),
                     "balance_conditions_passed": int(sum(c)), "balance_foam_eyes_closed": int(c[3])})
    return pd.DataFrame(rows).sort_values("SEQN")


def pick_balance(pool, sex, age, used):
    if pool.empty:
        return None
    cand = pool[(pool["sex"] == sex) & (~pool["SEQN"].isin(used))].copy()
    cand["gap"] = (cand["age"] - age).abs()
    return cand.sort_values(["gap", "SEQN"]).iloc[0] if not cand.empty else None
