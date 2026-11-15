"""NHANES 2011-2012 (CDC/NCHS, public domain): population norms and a pool of astronaut-like exam donors.

Each donor is one real, de-identified survey participant (SEQN). Their one-off exams (anthropometry, blood pressure,
DXA, audiometry, grip strength, PHQ-9, vitamin D, lipids, HSV serostatus, kidney-stone history) fill passport fields
that no wearable or astronaut dataset covers. Population percentiles use the MEC exam weights.
"""
import numpy as np
import pandas as pd

from .common import RAW, age_band

NH = RAW / "nhanes"
SOURCE = "NHANES-2011"


def _read(name: str, cols: list[str]) -> pd.DataFrame:
    path = NH / f"{name}.xpt"
    if not path.exists():
        return pd.DataFrame(columns=["SEQN", *cols])
    df = pd.read_sas(path, format="xport", encoding="latin-1")
    keep = ["SEQN"] + [c for c in cols if c in df.columns]
    df = df[keep].copy()
    num = df.select_dtypes("number").columns
    df[num] = df[num].mask(df[num].abs() < 1e-9, 0.0)  # SAS transport stores exact zero as ~5e-79
    return df


def _mean_cols(df: pd.DataFrame, cols: list[str]) -> pd.Series:
    present = [c for c in cols if c in df.columns]
    return df[present].mean(axis=1, skipna=True) if present else pd.Series(np.nan, index=df.index)


def available() -> bool:
    return (NH / "DEMO_G.xpt").exists()


def load() -> pd.DataFrame:
    """One row per participant with the metrics we use (names match data/metrics.yaml)."""
    demo = _read("DEMO_G", ["RIAGENDR", "RIDAGEYR", "WTMEC2YR"])
    df = demo.rename(columns={"RIAGENDR": "sex_code", "RIDAGEYR": "age", "WTMEC2YR": "weight_mec"})
    df["sex"] = df["sex_code"].map({1.0: "M", 2.0: "F"})

    bmx = _read("BMX_G", ["BMXHT", "BMXWT", "BMXBMI"]).rename(
        columns={"BMXHT": "height", "BMXWT": "body_mass", "BMXBMI": "bmi"})
    bpx = _read("BPX_G", ["BPXPLS", "BPXSY1", "BPXSY2", "BPXSY3", "BPXSY4", "BPXDI1", "BPXDI2", "BPXDI3", "BPXDI4"])
    bp = pd.DataFrame({"SEQN": bpx["SEQN"], "hr_clinic": bpx.get("BPXPLS"),
                       "bp_sys": _mean_cols(bpx, ["BPXSY1", "BPXSY2", "BPXSY3", "BPXSY4"]),
                       # NHANES codes an unmeasurable diastolic as 0; drop those readings
                       "bp_dia": _mean_cols(bpx.replace({c: {0.0: np.nan} for c in ["BPXDI1", "BPXDI2", "BPXDI3", "BPXDI4"]}),
                                            ["BPXDI1", "BPXDI2", "BPXDI3", "BPXDI4"])})
    ghb = _read("GHB_G", ["LBXGH"]).rename(columns={"LBXGH": "hba1c"})
    glu = _read("GLU_G", ["LBXGLU"]).rename(columns={"LBXGLU": "glucose_fasting_lab"})
    vid = _read("VID_G", ["LBXVIDMS"])
    vid["vitd"] = vid["LBXVIDMS"] / 2.496  # nmol/L -> ng/mL
    tc = _read("TCHOL_G", ["LBXTC"]).rename(columns={"LBXTC": "total_chol"})
    hdl = _read("HDL_G", ["LBDHDD"]).rename(columns={"LBDHDD": "hdl"})
    hsv = _read("HSV_G", ["LBXHE1", "LBXHE2"])
    hsv["hsv1_pos"] = hsv["LBXHE1"].map({1.0: 1.0, 2.0: 0.0})
    hsv["hsv2_pos"] = hsv["LBXHE2"].map({1.0: 1.0, 2.0: 0.0})
    dxx = _read("DXX_G", ["DXDTOBMD", "DXDTOPF", "DXDTOLE"]).rename(
        columns={"DXDTOBMD": "bmd_total", "DXDTOPF": "body_fat_pct"})
    dxx["lean_mass"] = dxx.pop("DXDTOLE") / 1000.0 if "DXDTOLE" in dxx else np.nan
    mgx = _read("MGX_G", ["MGDCGSZ"]).rename(columns={"MGDCGSZ": "grip_strength"})
    aux = _read("AUX_G", ["AUXU500R", "AUXU1K1R", "AUXU2KR", "AUXU4KR", "AUXU500L", "AUXU1K1L", "AUXU2KL", "AUXU4KL"])
    aux = aux.replace({666.0: np.nan, 888.0: np.nan})  # no response / could not obtain
    aux["hearing_pta_right"] = _mean_cols(aux, ["AUXU500R", "AUXU1K1R", "AUXU2KR", "AUXU4KR"])
    aux["hearing_pta_left"] = _mean_cols(aux, ["AUXU500L", "AUXU1K1L", "AUXU2KL", "AUXU4KL"])
    dpq_cols = [f"DPQ0{i}0" for i in range(1, 10)]
    dpq = _read("DPQ_G", dpq_cols)
    items = dpq[[c for c in dpq_cols if c in dpq]].where(lambda x: x <= 3)  # 7/9 = refused / don't know
    dpq["phq9"] = items.sum(axis=1, min_count=9)
    dpq["phq9_item9"] = items.get("DPQ090")
    slq = _read("SLQ_G", ["SLD010H"]).rename(columns={"SLD010H": "sleep_hours_reported"})
    kiq = _read("KIQ_U_G", ["KIQ026"])
    kiq["kidney_stone_history"] = kiq["KIQ026"].map({1.0: 1.0, 2.0: 0.0})
    mcq = _read("MCQ_G", ["MCQ010", "MCQ300A"])
    mcq["asthma_ever"] = mcq["MCQ010"].map({1.0: 1.0, 2.0: 0.0})
    mcq["family_early_mi"] = mcq["MCQ300A"].map({1.0: 1.0, 2.0: 0.0})
    smq = _read("SMQ_G", ["SMQ020", "SMQ040"])
    smq["smoker_now"] = smq["SMQ040"].map({1.0: 1.0, 2.0: 1.0, 3.0: 0.0})
    smq.loc[smq["SMQ020"] == 2.0, "smoker_now"] = 0.0
    diq = _read("DIQ_G", ["DIQ010"])
    diq["diabetes"] = diq["DIQ010"].map({1.0: 1.0, 2.0: 0.0, 3.0: 0.0})

    for part in (bmx, bp, ghb, glu, vid[["SEQN", "vitd"]], tc, hdl, hsv[["SEQN", "hsv1_pos", "hsv2_pos"]],
                 dxx, mgx, aux[["SEQN", "hearing_pta_right", "hearing_pta_left"]],
                 dpq[["SEQN", "phq9", "phq9_item9"]], slq, kiq[["SEQN", "kidney_stone_history"]],
                 mcq[["SEQN", "asthma_ever", "family_early_mi"]], smq[["SEQN", "smoker_now"]],
                 diq[["SEQN", "diabetes"]]):
        df = df.merge(part, on="SEQN", how="left")
    df["SEQN"] = df["SEQN"].astype(int)
    return df


# Metrics for population norms: (column, unit)
NORM_METRICS = {
    "hr_clinic": "bpm", "bp_sys": "mmHg", "bp_dia": "mmHg", "height": "cm", "body_mass": "kg", "bmi": "kg/m2",
    "hba1c": "%", "glucose_fasting_lab": "mg/dL", "vitd": "ng/mL", "total_chol": "mg/dL", "hdl": "mg/dL",
    "bmd_total": "g/cm2", "body_fat_pct": "%", "lean_mass": "kg", "grip_strength": "kg",
    "hearing_pta_right": "dB HL", "phq9": "0-27", "sleep_hours_reported": "h",
}
PCTS = (5, 10, 25, 50, 75, 90, 95)


def _wpct(values: np.ndarray, weights: np.ndarray, pcts) -> list[float]:
    order = np.argsort(values)
    v, w = values[order], weights[order]
    cw = np.cumsum(w)
    cw = cw / cw[-1]
    return [float(np.interp(p / 100.0, cw, v)) for p in pcts]


def norms(df: pd.DataFrame) -> list[dict]:
    """Weighted percentiles by sex and 10-year age band, adults 20-69."""
    rows = []
    adults = df[(df["age"] >= 20) & (df["age"] < 70) & df["sex"].notna() & (df["weight_mec"] > 0)].copy()
    adults["age_band"] = adults["age"].apply(age_band)
    for metric, unit in NORM_METRICS.items():
        for (sex, band), g in adults.groupby(["sex", "age_band"]):
            g = g[g[metric].notna()]
            if len(g) < 30:
                continue
            p = _wpct(g[metric].to_numpy(float), g["weight_mec"].to_numpy(float), PCTS)
            rows.append({"metric": metric, "sex": sex, "age_band": band, "n": len(g),
                         **{f"p{q}": round(x, 3) for q, x in zip(PCTS, p)}, "unit": unit, "source_id": SOURCE})
    return sorted(rows, key=lambda r: (r["metric"], r["sex"], r["age_band"]))


DONOR_REQUIRED = ["height", "body_mass", "bp_sys", "bp_dia", "hr_clinic", "bmd_total", "grip_strength",
                  "hearing_pta_right", "phq9", "vitd", "hba1c", "total_chol"]


def astronaut_like(df: pd.DataFrame) -> pd.DataFrame:
    """Healthy adults 30-55, BMI 20-30, no diabetes, not smoking now, with every exam we need."""
    m = (df["age"].between(30, 55) & df["bmi"].between(20, 30) & (df["diabetes"] == 0)
         & (df["smoker_now"] == 0) & (df["phq9"] < 5))
    pool = df[m].dropna(subset=DONOR_REQUIRED)
    return pool.sort_values("SEQN")


def pick_donor(pool: pd.DataFrame, sex: str, age: int, kidney_stone: bool | None = None,
               target_bp: float | None = None) -> pd.Series | None:
    """Deterministic: same sex; prefer a matching kidney-stone history when the story has one; age within 5 years
    when possible; then the blood pressure closest to the story target; then closest age."""
    cand = pool[pool["sex"] == sex].copy()
    if cand.empty:
        return None
    if kidney_stone is not None:
        match = cand[cand["kidney_stone_history"] == (1.0 if kidney_stone else 0.0)]
        if not match.empty:
            cand = match
    cand["gap"] = (cand["age"] - age).abs()
    near = cand[cand["gap"] <= 5].copy()
    if not near.empty:
        cand = near
    cand["bp_gap"] = (cand["bp_sys"] - target_bp).abs() if target_bp is not None else 0.0
    return cand.sort_values(["bp_gap", "gap", "SEQN"]).iloc[0]
