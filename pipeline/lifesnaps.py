"""LifeSnaps (Zenodo 7229547, CC BY 4.0): real daily Fitbit Sense streams, EMA mood and scored surveys.

Each participant can donate up to 180 days to a crew member's passport. We pick, per participant, the 180-day
window with the most resting-HR days, and map its last day to L-1. Real gaps stay gaps.
"""
import pandas as pd

from .common import RAW

CSV = RAW / "lifesnaps" / "csv"
DAILY = CSV / "daily_fitbit_sema_df_unprocessed.csv"
WINDOW = 180
MIN_DAYS = 60

# metric -> (column, transform)
COLUMNS = {
    "hr_rest": ("resting_hr", None),
    "hrv_rmssd": ("rmssd", None),
    "sleep_hours": ("minutesAsleep", lambda v: v / 60.0),
    "sleep_efficiency": ("sleep_efficiency", None),
    "steps": ("steps", None),
    "spo2": ("spo2", None),
    "skin_temp_dev": ("daily_temperature_variation", None),
    "stress_score": ("stress_score", None),
}
POS, NEG = ("HAPPY", "RESTED/RELAXED"), ("SAD", "TENSE/ANXIOUS")


def available() -> bool:
    return DAILY.exists()


def _mood(row) -> float | None:
    labels = POS + NEG + ("TIRED", "ALERT", "NEUTRAL")
    vals = {k: row.get(k) for k in labels}
    if all(pd.isna(v) for v in vals.values()):
        return None
    pos = sum(vals[k] or 0 for k in POS) + 0.5 * (vals["ALERT"] or 0)
    neg = sum(vals[k] or 0 for k in NEG) + 0.5 * (vals["TIRED"] or 0)
    total = pos + neg + (vals["NEUTRAL"] or 0)
    if total == 0:
        return None
    return round(min(7, max(1, 4 + 3 * (pos - neg) / total)))


def _fatigue(row) -> float | None:
    if pd.isna(row.get("TIRED")) and pd.isna(row.get("RESTED/RELAXED")):
        return None
    if row.get("TIRED"):
        return 5
    return 2 if row.get("RESTED/RELAXED") else 3


def donors() -> list[dict]:
    if not available():
        return []
    d = pd.read_csv(DAILY, low_memory=False)
    d["date"] = pd.to_datetime(d["date"])
    pers = _scored("personality.csv")
    stai = _scored("stai.csv")
    out = []
    for pid, g in d.groupby("id"):
        g = g.sort_values("date")
        hr_days = g.loc[g["resting_hr"].notna(), "date"]
        if len(hr_days) < MIN_DAYS:
            continue
        # window end that maximises resting-HR coverage
        best_end, best_n = None, -1
        for end in hr_days:
            n = int(((hr_days > end - pd.Timedelta(days=WINDOW)) & (hr_days <= end)).sum())
            if n > best_n:
                best_end, best_n = end, n
        w = g[(g["date"] > best_end - pd.Timedelta(days=WINDOW)) & (g["date"] <= best_end)]
        t_of = {dt: -1 - int((best_end - dt).days) for dt in w["date"]}
        series: dict[str, dict] = {}
        for metric, (col, fn) in COLUMNS.items():
            s = {}
            for dt, v in zip(w["date"], w[col]):
                if pd.notna(v):
                    val = float(fn(v) if fn else v)
                    if metric == "sleep_hours" and val < 3:
                        continue  # a nap, not a night's sleep
                    s[t_of[dt]] = val
            if s:
                series[metric] = s
        mood = {t_of[r["date"]]: m for _, r in w.iterrows() if (m := _mood(r)) is not None}
        fat = {t_of[r["date"]]: f for _, r in w.iterrows() if (f := _fatigue(r)) is not None}
        if mood:
            series["mood_valence"] = mood
        if fat:
            series["fatigue"] = fat
        sex = {"MALE": "M", "FEMALE": "F"}.get(str(g["gender"].dropna().iloc[0]) if g["gender"].notna().any() else "", "")
        age = g["age"].dropna().iloc[0] if g["age"].notna().any() else ""
        stai_pts = {}
        for _, r in stai.get(pid, pd.DataFrame()).iterrows():
            dt = pd.to_datetime(r["submitdate"])
            if best_end - pd.Timedelta(days=WINDOW) < dt <= best_end:
                stai_pts[-1 - int((best_end - dt).days)] = float(r["stai_stress"])
        if stai_pts:
            series["stai_state"] = stai_pts
        p = pers.get(pid)
        personality = None
        if p is not None and not p.empty:
            r = p.iloc[0]
            personality = {k: float(r[k]) for k in ("extraversion", "agreeableness", "conscientiousness",
                                                     "stability", "intellect") if pd.notna(r.get(k))}
        vo2 = g["filteredDemographicVO2Max"].dropna()
        out.append({
            "subject_id": f"LS-{pid[-6:]}", "raw_id": pid, "sex": sex,
            "age_band": {"<30": "18-29", ">=30": "30+"}.get(str(age), ""),
            "real_days": len(series.get("hr_rest", {})),
            "hr_median": float(pd.Series(list(series["hr_rest"].values())).median()),
            "vo2_est": float(vo2.median()) if len(vo2) else None,
            "series": series, "personality": personality,
        })
    return sorted(out, key=lambda x: x["subject_id"])


def _scored(name: str) -> dict:
    path = CSV / name
    if not path.exists():
        return {}
    s = pd.read_csv(path)
    return {uid: grp for uid, grp in s.groupby("user_id")}


def pick(pool: list[dict], sex: str, target_hr: float | None, exclude: set) -> dict | None:
    """Same sex (unknown sex only as a fallback) with usable coverage (>= 40 nights of sleep, >= 30 HRV days);
    prefer age 30+; then resting HR within a few bpm of the story target; then richer data (SpO2, EMA mood,
    personality); deterministic."""
    def n(p, m):
        return len(p["series"].get(m, {}))

    cand = [p for p in pool if p["subject_id"] not in exclude and n(p, "sleep_hours") >= 40 and n(p, "hrv_rmssd") >= 30]
    same = [p for p in cand if p["sex"] == sex] or [p for p in cand if not p["sex"]]
    if not same:
        return None
    older = [p for p in same if p["age_band"] == "30+"]
    pool2 = older or same
    target = target_hr if target_hr is not None else 60

    def quality(p):
        return (n(p, "spo2") >= 30) + (n(p, "mood_valence") >= 20) + bool(p["personality"])

    return sorted(pool2, key=lambda p: (round(abs(p["hr_median"] - target) / 2.5), -quality(p), -p["real_days"],
                                        p["subject_id"]))[0]
