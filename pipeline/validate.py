"""First validation pass: run the real rule engine on real data and report how often it alarms.

1. LifeSnaps (healthy people, real Fitbit days + EMA mood): each participant's first 40 recorded days form a
   personal passport (median + p10..p90); every later day is assessed with a 14-day rolling history.
   Any non-GREEN result on these healthy days is a false alarm candidate.
2. Inspiration4 (real astronauts): each real pre- and post-flight lab draw is assessed on its own.
Writes data/validation.md. Run: pipeline/.venv/bin/python -m pipeline.validate
"""
import collections
import statistics
import sys

import pandas as pd

import json

from .common import DATA, RAW, ROOT
from . import extras, inspiration4

sys.path.insert(0, str(ROOT / "backend"))
from app.engine import assess  # noqa: E402

DAILY = DATA / "raw" / "lifesnaps" / "csv" / "daily_fitbit_sema_df_unprocessed.csv"
METRICS = {"hr_rest": "resting_hr", "hrv_rmssd": "rmssd", "sleep_hours": "minutesAsleep"}


def _mood(r):
    pos = (r.get("HAPPY") or 0) + (r.get("RESTED/RELAXED") or 0)
    neg = (r.get("SAD") or 0) + (r.get("TENSE/ANXIOUS") or 0)
    tot = pos + neg + (r.get("NEUTRAL") or 0) + (r.get("TIRED") or 0) + (r.get("ALERT") or 0)
    return None if not tot else round(min(7, max(1, 4 + 3 * (pos - neg) / tot)))


def lifesnaps_backtest():
    d = pd.read_csv(DAILY, low_memory=False)
    d["date"] = pd.to_datetime(d["date"])
    levels, rules, people, days = collections.Counter(), collections.Counter(), 0, 0
    for _, g in d.groupby("id"):
        g = g.sort_values("date").reset_index(drop=True)
        recs = []
        for _, r in g.iterrows():
            rec = {}
            for m, col in METRICS.items():
                v = r[col]
                if pd.notna(v):
                    v = float(v) / 60 if m == "sleep_hours" else float(v)
                    if m == "sleep_hours" and v < 3:
                        continue  # nap
                    rec[m] = round(v, 2)
            mood = _mood({k: (r[k] if pd.notna(r[k]) else 0) for k in
                          ("HAPPY", "RESTED/RELAXED", "SAD", "TENSE/ANXIOUS", "NEUTRAL", "TIRED", "ALERT")})
            if mood is not None:
                rec["mood_valence"] = mood
            recs.append(rec)
        with_hr = [i for i, r in enumerate(recs) if "hr_rest" in r]
        if len(with_hr) < 70:
            continue
        cut = with_hr[39]
        base_days = recs[:cut + 1]
        baselines, ranges = {}, {}
        for m in ("hr_rest", "hrv_rmssd", "sleep_hours"):
            vals = sorted(r[m] for r in base_days if m in r)
            if len(vals) >= 20:
                baselines[m] = statistics.median(vals)
                ranges[m] = {"lo": vals[int(0.1 * (len(vals) - 1))], "hi": vals[int(0.9 * (len(vals) - 1))],
                             "n": len(vals), "ready": True}
        passport = {"baselines": baselines, "personal_ranges": ranges, "modifiers": [],
                    "mission": {"comm_delay_s": 2}}
        people += 1
        test = recs[cut + 1:]
        for i, rec in enumerate(test):
            if not rec:
                continue
            hist = [dict(r, mission_day=30 + j) for j, r in enumerate(test[max(0, i - 13):i + 1])]
            a = assess(passport, hist)
            days += 1
            levels[a["overall_level"]] += 1
            for h in a["hypotheses"]:
                for t in h["trace"]:
                    rules[(t["rule"], h["level"], h["name"])] += 1
    return people, days, levels, rules


def i4_labs():
    """Each Inspiration4 draw assessed alone. Values flagged `suspect` by the loader (likely sample handling) are shown
    but not fed to the rules. Returns (subject, draw, glucose, sodium, findings, flagged metrics)."""
    rows = inspiration4.observations()
    by_draw = collections.defaultdict(dict)
    suspect = collections.defaultdict(set)
    for r in rows:
        by_draw[(r["subject_id"], r["t_kind"], r["t"])][r["metric"]] = r["value"]
        if r.get("quality") == "suspect":
            suspect[(r["subject_id"], r["t_kind"], r["t"])].add(r["metric"])
    out = []
    for key, labs in sorted(by_draw.items()):
        subj, kind, t = key
        day = {"mission_day": 30, **{k: labs[k] for k in ("glucose", "sodium", "lymphocytes_abs", "hemoglobin")
                                     if k in labs and k not in suspect[key]}}
        a = assess({"baselines": {}, "modifiers": [], "mission": {"comm_delay_s": 2}}, [day])
        flags = [(h["name"], h["level"]) for h in a["hypotheses"]]
        out.append((subj, f"{kind}{'+' if t > 0 else ''}{t}", labs.get("glucose"), labs.get("sodium"), flags,
                    sorted(suspect[key])))
    return out


def mimic_ed():
    """MIMIC-IV-ED demo: triage vitals of real emergency patients vs the nurse's ESI acuity (1 = most urgent)."""
    path = RAW / "mimic-ed" / "triage.csv.gz"
    if not path.exists():
        return None
    t = pd.read_csv(path, compression="gzip")
    rows = []
    for _, r in t.iterrows():
        if pd.isna(r["acuity"]):
            continue
        day = {"mission_day": 30}
        if pd.notna(r["temperature"]) and 90 <= r["temperature"] <= 110:
            day["temp"] = round((float(r["temperature"]) - 32) * 5 / 9, 1)  # MIMIC-ED records Fahrenheit
        for src, dst, lo, hi in (("heartrate", "hr_rest", 20, 250), ("resprate", "resp_rate", 4, 80),
                                 ("o2sat", "spo2", 50, 100), ("sbp", "bp_sys", 40, 300), ("dbp", "bp_dia", 40, 300)):
            if pd.notna(r[src]) and lo <= float(r[src]) <= hi:
                day[dst] = float(r[src])
        if len(day) < 4:
            continue
        a = assess({"baselines": {}, "modifiers": [], "mission": {"comm_delay_s": 2}}, [day])
        rows.append((int(r["acuity"]), a["overall_level"], a["news2"]["total"]))
    return rows


def bigideas():
    """BIG IDEAs Lab: Dexcom G6 readings of 16 adults (HbA1c 5.2-6.4%) vs the glucose rules' bands."""
    files = sorted((RAW / "bigideas").glob("Dexcom_*.csv"))
    if not files:
        return None
    per = []
    for f in files:
        d = pd.read_csv(f)
        g = pd.to_numeric(d.loc[d["Event Type"] == "EGV", "Glucose Value (mg/dL)"], errors="coerce").dropna()
        ts = pd.to_datetime(d.loc[d["Event Type"] == "EGV", "Timestamp (YYYY-MM-DDThh:mm:ss)"], errors="coerce")
        if g.empty:
            continue
        days = ts.dt.date.nunique()
        low_days = ts[g.values < 70].dt.date.nunique()
        per.append({"n": len(g), "lt70": float((g < 70).mean()), "lt54": float((g < 54).mean()),
                    "days": days, "low_days": low_days})
    return per


def tilt_criteria():
    """KB orthostatic criteria (SBP drop >= 20 or DBP drop >= 10 -> hypotension; HR rise >= 30 -> tachycardia)
    on healthy controls of the PhysioNet head-up tilt study."""
    c = extras.tilt_controls()
    oh = sum(1 for x in c if x["ortho_dsbp"] <= -20 or x["ortho_ddbp"] <= -10)
    tach = sum(1 for x in c if x["ortho_dhr"] >= 30)
    return len(c), oh, tach, (statistics.median(x["ortho_dsbp"] for x in c) if c else None), \
        (statistics.median(x["ortho_dhr"] for x in c) if c else None)


def _bio_reading(conf: dict) -> str:
    n = lambda t, p: conf.get(f"{t}->{p}", 0)  # noqa: E731
    none_tot = sum(v for k, v in conf.items() if k.startswith("none->"))
    exp_tot = sum(v for k, v in conf.items() if not k.startswith("none->"))
    detected = exp_tot - n("low", "none") - n("high", "none")
    high_tot = sum(v for k, v in conf.items() if k.startswith("high->"))
    return (f"Reading: unexposed samples are recognised in {n('none', 'none')} of {none_tot}; exposure (0.15–1.5 Gy) is"
            f" detected in {detected} of {exp_tot} ({detected / exp_tot:.0%}), but the dose level is often wrong"
            f" (high recognised as high in {n('high', 'high')} of {high_tot}). As a lab-on-chip it can say 'exposed, check"
            " the dosimeter', not give a dose; a better dose estimate needs a time-aware model or more genes."
            " Model: `data/warehouse/biodosimetry_model.json`.")


def _reading(levels, rules, days) -> str:
    sleep = sum(n for (r, _, _), n in rules.items() if r.startswith("R-SLP"))
    mood = sum(n for (r, _, _), n in rules.items() if r.startswith("R-BEH"))
    parts = [f"Reading: on these healthy volunteers {levels['RED']} day(s) reached RED and {levels['ORANGE']} reached ORANGE."]
    parts.append(f"Sleep rules fired on {sleep} rule-days: real people often sleep < 6 h, or poorly on most nights of a"
                 " fortnight; that matches NASA's own threshold (< 6 h = restricted sleep), so it works as a self-care"
                 " nudge rather than a medical alarm.")
    if mood:
        parts.append(f"Mood rules fired on {mood} rule-days. LifeSnaps has no 1-7 mood scale: we derive one from EMA labels"
                     " (a day tagged only TENSE/ANXIOUS or SAD maps to 1/7), which is harsher than a real rating, so these"
                     " alarms say more about the mapping than about R-BEH-01. A real pre-flight mood check-in is needed"
                     " before judging that rule.")
    parts.append("The personal-baseline HRV rule (R-CV-17) fires rarely.")
    return " ".join(parts)


def main():
    people, days, levels, rules = lifesnaps_backtest()
    labs = i4_labs()
    non_green = days - levels["GREEN"]
    lines = [
        "# Validation — first pass on real data",
        "",
        "Generated by `pipeline/.venv/bin/python -m pipeline.validate` (rule engine from `backend/app`).",
        "This is a first, automatic check, not a clinical validation.",
        "",
        "## 1. False alarms on healthy people (LifeSnaps, real Fitbit days + EMA mood)",
        "",
        f"Participants with ≥ 70 resting-HR days: **{people}**. Personal passport = first 40 recorded days;"
        f" assessed days after that: **{days}** (14-day rolling history, mission day ≥ 30 so no adaptation window).",
        "",
        "| Overall level | Days | Share |",
        "|---|---|---|",
    ]
    for lvl in ("GREEN", "YELLOW", "ORANGE", "RED"):
        lines.append(f"| {lvl} | {levels[lvl]} | {levels[lvl] / days:.1%} |" if days else f"| {lvl} | 0 | — |")
    lines += ["", f"Non-GREEN on healthy days: **{non_green / days:.1%}**." if days else "", "",
              "Rules that fired (rule · level · hypothesis · days):", "", "| Rule | Level | Hypothesis | Days |",
              "|---|---|---|---|"]
    for (rule, lvl, name), n in rules.most_common(12):
        lines.append(f"| {rule} | {lvl} | {name} | {n} |")
    lines += [
        "",
        _reading(levels, rules, days),
        "",
        "## 2. Real astronaut lab draws (Inspiration4, NASA OSDR OSD-569/575)",
        "",
        "Each draw assessed alone (glucose, sodium, lymphocytes, hemoglobin; no symptoms).",
        "",
        "| Crew | Draw | Glucose mg/dL | Sodium mmol/L | Findings |",
        "|---|---|---|---|---|",
    ]
    hypo, flagged = 0, []
    for subj, draw, glu, na, flags, sus in labs:
        if any("Hypoglycemia" in f for f, _ in flags):
            hypo += 1
        if sus:
            flagged.append((subj, draw, sus))
        glu_s = "—" if glu is None else f"{glu}{' (flagged)' if 'glucose' in sus else ''}"
        note = [f"{f} ({lv})" for f, lv in flags]
        if sus:
            note.append(f"flagged, not assessed: {', '.join(sus)} (suspected sample handling)")
        lines.append(f"| {subj} | {draw} | {glu_s} | {na if na is not None else '—'} | {'; '.join(note) or '—'} |")
    n_glu = sum(1 for *_, sus in flagged if "glucose" in sus)
    lines += [
        "",
        f"**Finding:** {hypo} of {len(labs)} real draws from healthy astronauts trigger the glucose rules"
        " (R-NUT-02 54–69 mg/dL → YELLOW, R-NUT-01 < 54 → RED). These are serum values from routine draws, not"
        " symptomatic hypoglycemia. The ADA bands are written for people on glucose-lowering treatment; for healthy"
        " crew the rule should probably require symptoms (or compare with the personal baseline). Flagged for review"
        " by a flight surgeon; the rule is unchanged for now. The demo flight crew carries no glucose readings"
        " (no blood is drawn in flight), so the demo is not affected.",
        "",
        f"**Excluded as suspected sample handling ({len(flagged)} draws):** {n_glu} of the four crew read 36–44 mg/dL"
        " glucose at the same draw (R+45) with a normal anion gap and enzymes, and one of them also reads potassium"
        " 5.9 mmol/L there. Low glucose with high potassium is the pattern of serum left on the cells too long"
        " (glycolysis, potassium leak). The values stay in the warehouse as published, with `quality = suspect`"
        " (`pipeline/inspiration4.py`), and are not fed to the rules.",
        "",
    ]
    ed = mimic_ed()
    if ed:
        hi = [lv for acu, lv, _ in ed if acu <= 2]
        lo = [lv for acu, lv, _ in ed if acu >= 4]
        mid = [lv for acu, lv, _ in ed if acu == 3]
        alarm = lambda xs: sum(1 for x in xs if x in ("ORANGE", "RED"))  # noqa: E731
        lines += [
            "## 3. Red flags on real emergency patients (MIMIC-IV-ED demo, triage vitals only)",
            "",
            f"{len(ed)} ED stays with triage vitals (temperature, HR, respiratory rate, SpO₂, BP); no symptoms were"
            " given to the engine. ESI acuity is the triage nurse's urgency (1 = most urgent).",
            "",
            "| ESI acuity | Stays | Engine ORANGE/RED | Share |",
            "|---|---|---|---|",
            f"| 1–2 (urgent) | {len(hi)} | {alarm(hi)} | {alarm(hi) / len(hi):.0%} |" if hi else "| 1–2 | 0 | — | — |",
            f"| 3 | {len(mid)} | {alarm(mid)} | {alarm(mid) / len(mid):.0%} |" if mid else "| 3 | 0 | — | — |",
            f"| 4–5 (non-urgent) | {len(lo)} | {alarm(lo)} | {alarm(lo) / len(lo):.0%} |" if lo else "| 4–5 | 0 | — | — |",
            "",
            "Reading: from vitals alone the engine escalates only patients with abnormal vital signs; most urgent ED"
            " patients are urgent because of symptoms (chest pain, stroke signs, trauma), which the crew would enter"
            " through the symptom check-in. The demo has almost no non-urgent stays, so it cannot measure false alarms;"
            " the LifeSnaps section above covers that side.",
            "",
        ]
    cgm = bigideas()
    if cgm:
        n = sum(p["n"] for p in cgm)
        lt70 = sum(p["lt70"] * p["n"] for p in cgm) / n
        lt54 = sum(p["lt54"] * p["n"] for p in cgm) / n
        dd = sum(p["days"] for p in cgm)
        ld = sum(p["low_days"] for p in cgm)
        lines += [
            "## 4. Glucose bands on continuous glucose monitoring (BIG IDEAs Lab, Dexcom G6)",
            "",
            f"{len(cgm)} adults without diabetes (HbA1c 5.2–6.4%), {n:,} CGM readings over {dd} participant-days.",
            "",
            f"- readings < 70 mg/dL (R-NUT-02 band): **{lt70:.1%}**; readings < 54 mg/dL (R-NUT-01): **{lt54:.1%}**",
            f"- days with at least one reading < 70 mg/dL: **{ld} of {dd} ({ld / dd:.0%})**;"
            f" people with such a day: **{sum(1 for p in cgm if p['low_days'])} of {len(cgm)}**",
            "",
            f"Reading: low readings are rare ({lt70:.1%} of all readings) but appear on {ld / dd:.0%} of days, so a rule"
            " that fires on any single value below 70 mg/dL would alarm about once a week per crew member on a CGM."
            " Together with the Inspiration4 draws above, this supports gating R-NUT-01/02 on symptoms or on repeated"
            " low readings before using them with continuous monitors in flight.",
            "",
        ]
    n_t, oh, tach, med_dsbp, med_dhr = tilt_criteria()
    if n_t:
        lines += [
            "## 5. Orthostatic criteria on healthy controls (PhysioNet head-up tilt, 55–75 y)",
            "",
            f"{n_t} controls: median systolic change on tilt {med_dsbp:+.1f} mmHg, median HR change {med_dhr:+.1f} bpm."
            f" Meet the hypotension criterion (SBP ≤ −20 or DBP ≤ −10): **{oh}**; the tachycardia criterion"
            f" (HR ≥ +30): **{tach}**.",
            "",
            "Reading: the knowledge-base criteria stay quiet on healthy controls, so a positive test on landing day"
            " is meaningful (NASA reports 66% of ISS crew failing a 10-minute tilt on landing day).",
            "",
        ]
    bal = extras.balance_pool()
    if not bal.empty:
        g = bal[(bal["age"] >= 30) & (bal["age"] <= 55)]
        lines += [
            "## 7. Balance baseline (NHANES 2003–2004 modified Romberg, adults 30–55)",
            "",
            f"{len(g)} adults: pass all 4 conditions **{(g['balance_conditions_passed'] == 4).mean():.0%}**;"
            f" pass foam + eyes closed (the vestibular condition) **{g['balance_foam_eyes_closed'].mean():.0%}**.",
            "",
            f"Reading: {1 - g['balance_foam_eyes_closed'].mean():.0%} of healthy adults fail the foam/eyes-closed condition"
            " on Earth, so a single pre-flight fail is not a red flag; what matters is the change against the crew"
            " member's own pre-flight result after landing.",
            "",
        ]
    bio_path = DATA / "warehouse" / "biodosimetry_model.json"
    if bio_path.exists():
        bio = json.loads(bio_path.read_text(encoding="utf-8"))
        lines += [
            "## 6. Biodosimetry from blood gene expression (NASA OSDR OSD-410 / GEO GSE63952)",
            "",
            f"{bio['n_samples']} samples from {bio['volunteers']} volunteers (ex vivo gamma rays, 0 / 0.15 / 0.3 / 1.5 Gy,"
            f" 1–6 h). Panel of {len(bio['genes'])} radiation-responsive genes, fold change vs the same person's"
            " unexposed sample, nearest-centroid classifier, leave-one-volunteer-out.",
            "",
            f"- accuracy for none / low (0.15–0.3 Gy) / high (1.5 Gy): **{bio['loocv_accuracy']:.0%}** (chance 33%)",
            f"- strongest genes: {', '.join(bio['top_genes'])}",
            f"- confusion (true->predicted: n): {', '.join(f'{k}: {v}' for k, v in bio['confusion'].items())}",
            "",
            _bio_reading(bio["confusion"]),
            "",
        ]
    out = ROOT / "data" / "validation.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"validation: {people} people, {days} days, non-green {non_green}; I4 draws {len(labs)}, glucose flags {hypo}"
          f" -> {out}")


if __name__ == "__main__":
    main()
