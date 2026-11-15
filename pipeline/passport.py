"""Six-month pre-flight physiological passport (L-180 -> L-1) for every crew member.

Each fictional crew member is assembled from real donors, and every value keeps its provenance:
  labs      <- Inspiration4 crew code (real astronaut, NASA OSDR) at L-92 / L-44 / L-3
  exams     <- one astronaut-like NHANES 2011-2012 participant (real population record) at L-180
  daily     <- one LifeSnaps participant (real person, Fitbit Sense); days before their record starts are filled
               by an AR(1) model fitted on the same person (synthetic-calibrated); real gaps stay gaps
  no open data (PVT, OCT, CIMT, VO2peak, most questionnaires) <- published norms (synthetic-calibrated)
  history, preferences <- the character's story (authored)
Baselines follow knowledge-base/01-physiological-passport.md "Baseline derivation".
"""
import collections
import csv
import hashlib
import json
import math
import random
import statistics

import yaml

from . import extras
from . import inspiration4 as i4
from . import lifesnaps, nhanes
from .common import (AUTHORED, CREW, DATA, EVIDENCE, PASSPORTS, REAL_ASTRONAUT, REAL_GROUND, REAL_POPULATION,
                     SYNTH_CAL)

WINDOW = 180  # days L-180 .. L-1
METRICS = yaml.safe_load((DATA / "metrics.yaml").read_text(encoding="utf-8"))["metrics"]

SESSIONS = [  # (session_id, t, title) - NASA reference schedule inside the six-month window
    ("eye-exam", -180, "Comprehensive eye examination (L-9/6 months slot)"),
    ("personality", -180, "Personality profile (IPIP Big Five)"),
    ("medical-core", -180, "Core medical exam: anthropometry, blood pressure, hearing, history"),
    ("biochem", -180, "Biochemical markers: CBC, CMP"),
    ("cimt", -180, "Carotid intima-media thickness"),
    ("vo2peak", -180, "Aerobic capacity (VO2peak)"),
    ("dxa", -180, "DXA: bone density and body composition"),
    ("strength-fitness", -180, "Strength and functional fitness"),
    ("actigraphy", -180, "Actigraphy and sleep log, 2 weeks (L-180..L-167)"),
    ("cognition-fam", -120, "Cognition battery: familiarisation run"),
    ("i4-L-92", -92, "Pre-flight labs (Inspiration4 draw L-92, in the L-90 slot)"),
    ("cognition", -90, "Cognition battery: baseline run"),
    ("cellular", -90, "Cellular profile: saliva stress hormones"),
    ("sensorimotor", -90, "Sensorimotor baseline (planned source)"),
    ("microbiome", -90, "Microbiome baseline (swabs at the Inspiration4 draws)"),
    ("posturography", -90, "Balance test (modified Romberg; stands in for platform posturography)"),
    ("medical-labs", -90, "Medical labs: blood pressure re-check"),
    ("orthostatic", -90, "Orthostatic test: supine to head-up tilt"),
    ("vo2peak-2", -60, "VO2peak repeat"),
    ("i4-L-44", -44, "Pre-flight labs (Inspiration4 draw L-44, in the L-30 slot)"),
    ("medical-labs-2", -30, "Medical labs, light eye exam, strength re-check"),
    ("dxa-2", -30, "DXA repeat"),
    ("hsp", -14, "Health Stabilization Program quarantine: vitals re-baseline"),
    ("ksc", -6, "Move to Kennedy Space Center"),
    ("i4-L-3", -3, "Pre-flight labs (Inspiration4 draw L-3)"),
]
LAB_METRICS = ["wbc", "lymphocytes_abs", "neutrophils_abs", "hemoglobin", "hematocrit", "platelets", "glucose",
               "sodium", "potassium", "calcium", "creatinine", "egfr", "bun", "albumin", "alt", "ast", "crp"]
DAILY_WEARABLE = ["hr_rest", "hrv_rmssd", "sleep_hours", "sleep_efficiency", "steps", "spo2", "skin_temp_dev",
                  "stress_score"]
CHECKIN = ["mood_valence", "fatigue", "kss", "workload", "team_cohesion"]
NHANES_EXAM = ["height", "body_mass", "bp_sys", "bp_dia", "hr_clinic", "hba1c", "vitd", "total_chol", "hdl",
               "hsv1_pos", "hsv2_pos", "bmd_total", "body_fat_pct", "lean_mass", "grip_strength",
               "hearing_pta_right", "hearing_pta_left", "phq9", "sleep_hours_reported", "kidney_stone_history",
               "family_early_mi", "asthma_ever"]
DECIMALS = {"steps": 0, "hr_rest": 0, "hrv_rmssd": 1, "sleep_hours": 2, "sleep_efficiency": 0, "spo2": 1,
            "skin_temp_dev": 2, "stress_score": 0, "body_mass": 1, "pvt_rt": 0, "near_acuity_logmar": 2}


def _seed(*parts) -> int:
    return int(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:12], 16)


def _norms() -> dict:
    with open(EVIDENCE / "norms.csv", newline="", encoding="utf-8") as f:
        return {r["metric"]: {k: float(r[k]) for k in ("mean", "sd", "lo", "hi")} for r in csv.DictReader(f)}


def _clip(m: str, v: float) -> float:
    rng = (METRICS.get(m) or {}).get("range")
    if rng:
        v = min(max(v, rng[0]), rng[1])
    d = DECIMALS.get(m)
    return round(v, d) if d is not None else round(v, 3)


class Builder:
    def __init__(self, crew: dict, ctx: dict):
        self.c = crew
        self.id = crew["id"]
        self.rng = random.Random(crew.get("seed") or _seed("passport", self.id))  # crew yaml may pin the seed
        self.ctx = ctx
        self.obs: list[dict] = []
        self.donors: list[dict] = []
        self.session_rows: list[dict] = []

    # ---- observations ------------------------------------------------------------------------------------
    def add(self, t, metric, value, prov, source, session="", ref=(None, None)):
        unit = (METRICS.get(metric) or {}).get("unit", "")
        self.obs.append({"subject_id": self.id, "source_id": source, "t_kind": "L", "t": int(t), "metric": metric,
                         "value": value, "unit": unit, "ref_lo": ref[0], "ref_hi": ref[1], "provenance": prov,
                         "session_id": session})

    # ---- labs: Inspiration4 ------------------------------------------------------------------------------
    def labs(self):
        donor = self.c["lab_donor"]
        rows = [r for r in self.ctx["i4"] if r["subject_id"] == donor and r["t_kind"] == "L"]
        donor_sex = self.ctx["i4_sex"].get(donor, "")
        # Reference ranges follow the crew member's sex. When the donor's sex differs, the Inspiration4 lab's range for
        # the crew member's sex (from the other crew codes of that sex) replaces the donor's own.
        swap = bool(donor_sex) and donor_sex != self.c["sex"]
        note = "Inspiration4 pre-flight draws L-92, L-44, L-3"
        if swap:
            note += f"; {'male' if self.c['sex'] == 'M' else 'female'} reference ranges"
        self.donors.append({"crew_id": self.id, "field_group": "labs", "donor_subject_id": donor,
                            "source_id": "OSD-569;OSD-575", "note": note})

        def ref(r):
            if swap and (self.c["sex"], r["metric"]) in self.ctx["i4_sex_ranges"]:
                return self.ctx["i4_sex_ranges"][(self.c["sex"], r["metric"])]
            return r["ref_lo"], r["ref_hi"]

        by_metric = {}
        for r in rows:
            if r["metric"] not in LAB_METRICS:
                continue
            self.add(r["t"], r["metric"], r["value"], REAL_ASTRONAUT, r["source_id"], f"i4-L{r['t']}", ref(r))
            by_metric.setdefault(r["metric"], []).append(r)
        # L-180 biochemical-markers draw is not in the dataset: model it from this person's own three draws.
        for m, rs in sorted(by_metric.items()):
            vals = [r["value"] for r in rs]
            mu = statistics.fmean(vals)
            sd = statistics.pstdev(vals) or abs(mu) * 0.03
            v = round(mu + self.rng.gauss(0, sd), 3)
            self.add(-180, m, max(v, 0.0), SYNTH_CAL, rs[0]["source_id"], "biochem", ref(rs[-1]))

    # ---- one-off exams: NHANES -----------------------------------------------------------------------------
    def exams(self):
        pool = self.ctx["nhanes_pool"]
        if pool is None or pool.empty:
            return
        used = self.ctx["used_nhanes"]
        cand = pool[~pool["SEQN"].isin(used)]
        target_bp = (self.c.get("story_targets") or {}).get("bp_sys")
        ks = True if self.c.get("prefer_kidney_stone_donor") else None
        d = nhanes.pick_donor(cand, self.c["sex"], self.c["age"], kidney_stone=ks, target_bp=target_bp)
        if d is None:
            return
        used.add(int(d["SEQN"]))
        sid = f"NH-{int(d['SEQN'])}"
        self.donors.append({"crew_id": self.id, "field_group": "exams", "donor_subject_id": sid,
                            "source_id": nhanes.SOURCE,
                            "note": f"NHANES 2011-2012 participant, {self.c['sex']}, age {int(d['age'])}"})
        self.ctx["subjects"].append({"subject_id": sid, "source_id": nhanes.SOURCE, "kind": "population",
                                     "sex": d["sex"], "age_band": f"{int(d['age']) // 10 * 10}-{int(d['age']) // 10 * 10 + 9}",
                                     "note": "astronaut-like exam donor"})
        session_of = {"bmd_total": "dxa", "body_fat_pct": "dxa", "lean_mass": "dxa", "grip_strength": "strength-fitness",
                      "hba1c": "biochem", "vitd": "biochem", "total_chol": "biochem", "hdl": "biochem",
                      "hsv1_pos": "biochem", "hsv2_pos": "biochem"}
        self.exam = {}
        for m in NHANES_EXAM:
            v = d.get(m)
            if v is None or (isinstance(v, float) and math.isnan(v)):
                continue
            v = round(float(v), 3)
            self.exam[m] = v
            self.add(-180, m, v, REAL_POPULATION, nhanes.SOURCE, session_of.get(m, "medical-core"))
        # re-checks inside the window, modelled around the real exam (within-person variability [T])
        for t, sess in ((-90, "medical-labs"), (-30, "medical-labs-2")):
            for m, sd in (("bp_sys", 4.0), ("bp_dia", 3.0)):
                if m in self.exam:
                    self.add(t, m, round(self.exam[m] + self.rng.gauss(0, sd), 1), SYNTH_CAL, nhanes.SOURCE, sess)
        for m, rel in (("bmd_total", 0.004), ("body_fat_pct", 0.02), ("lean_mass", 0.01)):
            if m in self.exam:
                self.add(-30, m, round(self.exam[m] * (1 + self.rng.gauss(0, rel)), 3), SYNTH_CAL, nhanes.SOURCE, "dxa-2")
        if "grip_strength" in self.exam:
            self.add(-30, "grip_strength", round(self.exam["grip_strength"] * (1 + self.rng.gauss(0, 0.03)), 1),
                     SYNTH_CAL, nhanes.SOURCE, "medical-labs-2")

    # ---- daily streams: LifeSnaps --------------------------------------------------------------------------
    def daily(self):
        donor = lifesnaps.pick(self.ctx["ls_donors"], self.c["sex"], (self.c.get("story_targets") or {}).get("hr_rest"),
                               exclude=self.ctx["used_ls"])
        if donor is not None:
            self.ctx["used_ls"].add(donor["subject_id"])
            self.donors.append({"crew_id": self.id, "field_group": "daily", "donor_subject_id": donor["subject_id"],
                                "source_id": "LIFESNAPS",
                                "note": f"LifeSnaps participant, {donor['real_days']} real days mapped to the end of the window"})
            self.ctx["subjects"].append({"subject_id": donor["subject_id"], "source_id": "LIFESNAPS", "kind": "ground",
                                         "sex": donor.get("sex", ""), "age_band": donor.get("age_band", ""),
                                         "note": "daily wearable donor"})
            series = donor["series"]  # {metric: {t: value}} with t in -180..-1
        else:
            series = {}
        self.ls = donor or {}
        self.ls_series = series
        for m in DAILY_WEARABLE:
            real = series.get(m, {})
            for t, v in sorted(real.items()):
                self.add(t, m, _clip(m, v), REAL_GROUND, "LIFESNAPS")
            if len(real) < 20:
                continue  # too little real data to model this person's metric; leave the gap honest
            first = min(real)
            vals = [real[t] for t in sorted(real)]
            mu, sd = statistics.median(vals), (statistics.pstdev(vals) or 1.0)
            phi = _lag1(vals)
            miss = 1 - len(real) / max(1, (max(real) - first + 1))
            x = mu
            for t in range(-WINDOW, first):
                x = mu + phi * (x - mu) + self.rng.gauss(0, sd * math.sqrt(max(1e-6, 1 - phi * phi)))
                if self.rng.random() < miss:
                    continue
                self.add(t, m, _clip(m, x), SYNTH_CAL, "LIFESNAPS")
        self.sleep_by_t = {o["t"]: o["value"] for o in self.obs if o["metric"] == "sleep_hours"}

    # ---- daily check-in, weekly tests, monthly questionnaires (norms) ---------------------------------------
    def checkins(self):
        n = self.ctx["norms"]
        person = {m: self.rng.gauss(0, 0.5) for m in CHECKIN}
        for t in range(-WINDOW, 0):
            if self.rng.random() < 0.15:  # people skip some check-ins
                continue
            short = max(0.0, 7.0 - (self.sleep_by_t.get(t) or 7.0))
            real = {m: self.ls_series.get(m, {}).get(t) for m in ("mood_valence", "fatigue")}
            vals = {
                "kss": n["kss"]["mean"] + person["kss"] + 0.8 * short + self.rng.gauss(0, 0.8),
                "fatigue": 3.0 + person["fatigue"] + 0.6 * short + self.rng.gauss(0, 0.8),
                "mood_valence": 5.0 + person["mood_valence"] - 0.3 * short + self.rng.gauss(0, 0.7),
                "workload": n["workload"]["mean"] + person["workload"] + self.rng.gauss(0, n["workload"]["sd"]),
                "team_cohesion": n["team_cohesion"]["mean"] + person["team_cohesion"] + self.rng.gauss(0, 0.5),
            }
            for m, v in vals.items():
                lo, hi = METRICS[m]["range"]
                if real.get(m) is not None:  # LifeSnaps EMA mood labels for this day (real person)
                    self.add(t, m, int(real[m]), REAL_GROUND, "LIFESNAPS")
                    continue
                self.add(t, m, int(min(max(round(v), lo), hi)), SYNTH_CAL, "NORMS")
        # weekly: body mass around the real NHANES mass, PVT and near acuity from norms
        mass0 = getattr(self, "exam", {}).get("body_mass")
        pvt_person = self.rng.gauss(0, n["pvt_rt"]["sd"] * 0.6)
        acu_person = self.rng.gauss(0, n["near_acuity_logmar"]["sd"])
        for t in range(-WINDOW + 7, 0, 7):
            if mass0:
                self.add(t, "body_mass", _clip("body_mass", mass0 + self.rng.gauss(0, 0.4)), SYNTH_CAL, nhanes.SOURCE)
            learn = 1.04 if t < -90 else 1.0  # PVT learning effect before the L-90 baseline [T]
            self.add(t, "pvt_rt", _clip("pvt_rt", (n["pvt_rt"]["mean"] + pvt_person) * learn + self.rng.gauss(0, 9)),
                     SYNTH_CAL, "NORMS")
            self.add(t, "near_acuity_logmar", _clip("near_acuity_logmar", acu_person + self.rng.gauss(0, 0.02)),
                     SYNTH_CAL, "NORMS")
        self.add(-120, "pvt_rt", _clip("pvt_rt", (n["pvt_rt"]["mean"] + pvt_person) * 1.06), SYNTH_CAL, "NORMS", "cognition-fam")
        self.add(-90, "pvt_rt", _clip("pvt_rt", n["pvt_rt"]["mean"] + pvt_person), SYNTH_CAL, "NORMS", "cognition")
        # monthly questionnaires
        phq0 = getattr(self, "exam", {}).get("phq9")
        q_person = {m: self.rng.gauss(0, n[m]["sd"] * 0.5) for m in ("gad7", "pss", "who5", "ucla3")}
        for k, t in enumerate(range(-WINDOW, 0, 30)):
            if phq0 is not None and k > 0:
                self.add(t, "phq9", int(min(27, max(0, round(phq0 + self.rng.gauss(0, 1))))), SYNTH_CAL, nhanes.SOURCE)
            for m in ("gad7", "pss", "who5", "ucla3"):
                lo, hi = METRICS[m]["range"]
                v = n[m]["mean"] + q_person[m] + self.rng.gauss(0, n[m]["sd"] * 0.4)
                self.add(t, m, int(min(max(round(v), lo), hi)), SYNTH_CAL, "NORMS")
        # session exams with no open data
        sexkey = f"vo2peak:{self.c['sex']}"
        est = self.ls.get("vo2_est")
        if est:  # graded test modelled around the donor's own Fitbit cardio-fitness estimate
            vo2, src = est + self.rng.gauss(0, 1.5), "LIFESNAPS"
        else:
            vo2, src = n[sexkey]["mean"] + self.rng.gauss(0, n[sexkey]["sd"] * 0.6), "NORMS"
        self.add(-180, "vo2peak", round(vo2, 1), SYNTH_CAL, src, "vo2peak")
        self.add(-60, "vo2peak", round(vo2 * (1 + self.rng.gauss(0.01, 0.02)), 1), SYNTH_CAL, src, "vo2peak-2")
        # personality (IPIP Big Five, NASA's instrument family) and state anxiety from the same LifeSnaps person
        for trait, v in sorted((self.ls.get("personality") or {}).items()):
            self.add(-180, f"ipip_{trait}", v, REAL_GROUND, "LIFESNAPS", "personality")
        stai = self.ls_series.get("stai_state", {})
        for t, v in sorted(stai.items()):
            self.add(t, "stai_state", v, REAL_GROUND, "LIFESNAPS")
        if not stai:
            for t in range(-WINDOW, 0, 30):
                self.add(t, "stai_state", int(round(n["stai_state"]["mean"] + self.rng.gauss(0, n["stai_state"]["sd"] * 0.5))),
                         SYNTH_CAL, "NORMS")
        for m, sess in (("cimt", "cimt"), ("oct_rnfl", "eye-exam"), ("iop", "eye-exam"), ("resp_rate", "medical-core"),
                        ("temp_oral", "medical-core")):
            v = n[m]["mean"] + self.rng.gauss(0, n[m]["sd"] * 0.6)
            self.add(-180, m, round(min(max(v, n[m]["lo"]), n[m]["hi"]), 2), SYNTH_CAL, "NORMS", sess)
        for t, sess in ((-90, "medical-labs"), (-14, "hsp")):
            self.add(t, "temp_oral", round(n["temp_oral"]["mean"] + self.rng.gauss(0, 0.15), 1), SYNTH_CAL, "NORMS", sess)
            self.add(t, "resp_rate", int(round(n["resp_rate"]["mean"] + self.rng.gauss(0, 1.5))), SYNTH_CAL, "NORMS", sess)
        isi = 15 if "P-10" in self.c.get("modifiers", []) else max(0, round(n["isi"]["mean"] + self.rng.gauss(0, 2)))
        self.add(-180, "isi", int(isi), SYNTH_CAL, "NORMS", "medical-core")

    # ---- more real donors: MMASH (hormones, PSQI, MEQ), PTB-XL+ (ECG), head-up tilt (orthostatic) --------
    def more_donors(self):
        mm = extras.pick_mmash(self.ctx["mmash"], self.c["sex"], self.ctx["used_mmash"],
                               poor_sleeper="P-10" in self.c.get("modifiers", []))
        if mm:
            self.ctx["used_mmash"].add(mm["subject_id"])
            self.donors.append({"crew_id": self.id, "field_group": "hormones", "donor_subject_id": mm["subject_id"],
                                "source_id": "MMASH", "note": f"MMASH participant (healthy man, {int(mm['age'] or 0)} y): saliva hormones, PSQI, MEQ"})
            for m in ("cortisol_wake", "cortisol_bed", "melatonin_wake", "melatonin_bed"):
                self.add(-90, m, round(mm[m], 12), REAL_GROUND, "MMASH", "cellular")
            self.add(-180, "psqi", mm["psqi"], REAL_GROUND, "MMASH", "medical-core")
            self.add(-180, "meq", mm["meq"], REAL_GROUND, "MMASH", "medical-core")
        ecg = extras.pick_ecg(self.ctx["ecg"], self.c["sex"], self.c["age"], self.ctx["used_ecg"]) \
            if not self.ctx["ecg"].empty else None
        if ecg is not None:
            self.ctx["used_ecg"].add(int(ecg["ecg_id"]))
            self.donors.append({"crew_id": self.id, "field_group": "ecg", "donor_subject_id": f"PTBXL-{int(ecg['ecg_id'])}",
                                "source_id": "PTB-XL", "note": f"PTB-XL normal 12-lead ECG, {ecg['sex']}, {int(ecg['age'])} y (cardiologist-validated)"})
            for m in extras.ECG_COLS.values():
                self.add(-180, m, float(ecg[m]), REAL_GROUND, "PTB-XL", "medical-core")
        # microbiome: the same Inspiration4 person as the labs (OSD-572 MetaPhlAn), pre-flight swabs
        micro = self.ctx["micro"].get(self.c["lab_donor"], {})
        for tp in ("L-92", "L-44", "L-3"):
            for metric, v in sorted((micro.get(tp) or {}).items()):
                if v["shannon"] is not None:
                    self.add(-int(tp[2:]), metric, v["shannon"], REAL_ASTRONAUT, "OSD-572", f"i4-{tp}")
        bal = extras.pick_balance(self.ctx["balance"], self.c["sex"], self.c["age"], self.ctx["used_balance"])
        if bal is not None:
            self.ctx["used_balance"].add(int(bal["SEQN"]))
            self.donors.append({"crew_id": self.id, "field_group": "balance", "donor_subject_id": f"NH03-{int(bal['SEQN'])}",
                                "source_id": "NHANES-2003", "note": f"NHANES 2003-2004 balance exam, {bal['sex']}, {int(bal['age'])} y"})
            for m in ("balance_conditions_passed", "balance_foam_eyes_closed"):
                self.add(-90, m, int(bal[m]), REAL_POPULATION, "NHANES-2003", "posturography")
        tilt = extras.pick_tilt(self.ctx["tilt"], self.c["sex"], self.ctx["used_tilt"])
        if tilt:
            self.ctx["used_tilt"].add(tilt["subject_id"])
            self.donors.append({"crew_id": self.id, "field_group": "orthostatic", "donor_subject_id": tilt["subject_id"],
                                "source_id": "TILT", "note": f"PhysioNet head-up tilt control, {tilt['sex']}, {int(tilt['age'])} y (older than the crew)"})
            for m in ("ortho_sbp_supine", "ortho_dbp_supine", "ortho_hr_supine", "ortho_dsbp", "ortho_ddbp", "ortho_dhr"):
                self.add(-90, m, tilt[m], REAL_GROUND, "TILT", "orthostatic")

    # ---- sessions ------------------------------------------------------------------------------------------
    def sessions(self):
        for sid, t, title in SESSIONS:
            obs = [o for o in self.obs if o["session_id"] == sid]
            provs = sorted({o["provenance"] for o in obs})
            srcs = sorted({o["source_id"] for o in obs})
            status = "done" if obs else ("planned-source" if "planned" in title else "done")
            self.session_rows.append({"crew_id": self.id, "session_id": sid, "t": t, "title": title, "status": status,
                                      "provenance": ";".join(provs), "source_ids": ";".join(srcs)})


def _lag1(vals: list[float]) -> float:
    if len(vals) < 10:
        return 0.3
    mu = statistics.fmean(vals)
    num = sum((a - mu) * (b - mu) for a, b in zip(vals, vals[1:]))
    den = sum((a - mu) ** 2 for a in vals)
    return min(0.9, max(0.0, num / den)) if den else 0.3


# ---- baselines -----------------------------------------------------------------------------------------------
FIELD_ORDER = "ABCDEFGHIJKLM"


def _pct(sorted_vals, p):
    if not sorted_vals:
        return None
    k = (len(sorted_vals) - 1) * p
    lo, hi = math.floor(k), math.ceil(k)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo)


def _trend(points):
    """Least-squares slope per 30 days."""
    if len(points) < 10:
        return None
    xs, ys = zip(*points)
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    den = sum((x - mx) ** 2 for x in xs)
    return round(sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den * 30, 4) if den else None


def fields(b: Builder) -> list[dict]:
    out = []
    by_metric = {}
    for o in b.obs:
        by_metric.setdefault(o["metric"], []).append(o)

    def row(metric, value, method, obs, lo=None, hi=None, rebase=None, trend=None, readiness=None, field=None):
        meta = METRICS.get(metric, {})
        n = len(obs)
        expected = {"daily": WINDOW, "weekly": WINDOW // 7, "monthly": WINDOW // 30}.get(meta.get("freq"), 1)
        if readiness is None:
            need = {"daily": 28, "weekly": 4, "monthly": 2}.get(meta.get("freq"), 1)
            readiness = "ready" if n >= need else ("partial" if n else "missing")
        out.append({"crew_id": b.id, "field_id": field or meta.get("field") or "CHECKIN", "metric": metric,
                    "value": value, "lo": lo, "hi": hi, "n": n,
                    "completeness": round(min(1.0, n / expected), 3) if expected else None,
                    "readiness": readiness, "rebase14": rebase, "trend_per_30d": trend, "method": method,
                    "unit": meta.get("unit", ""), "provenance": ";".join(sorted({o["provenance"] for o in obs})),
                    "source_ids": ";".join(sorted({o["source_id"] for o in obs}))})

    for m, obs in sorted(by_metric.items()):
        freq = METRICS.get(m, {}).get("freq")
        vals = sorted(o["value"] for o in obs if isinstance(o["value"], (int, float)))
        if not vals:
            continue
        if m in LAB_METRICS:
            last = max(obs, key=lambda o: o["t"])
            row(m, round(statistics.fmean(vals), 3), "mean of pre-flight draws (L-180 model + real L-92/L-44/L-3)",
                obs, last["ref_lo"], last["ref_hi"],
                readiness="ready" if sum(o["provenance"] == REAL_ASTRONAUT for o in obs) >= 3 else "partial")
        elif m == "pvt_rt":
            base = [o for o in obs if o["session_id"] == "cognition"]
            row(m, base[0]["value"] if base else statistics.median(vals),
                "L-90 cognition session (not the L-120 familiarisation run)", obs,
                _pct(vals, 0.1), _pct(vals, 0.9), readiness="ready" if base else "partial")
        elif m == "sleep_hours":
            act = [o["value"] for o in obs if -180 <= o["t"] <= -167]
            row(m, round(statistics.median(vals), 2),
                "median of all nights (actigraphy L-180..L-167 shown separately as rebase14 is the HSP window)", obs,
                round(_pct(vals, 0.1), 2), round(_pct(vals, 0.9), 2),
                rebase=_rebase(obs), trend=_trend([(o["t"], o["value"]) for o in obs]))
            if act:
                row(m, round(statistics.median(act), 2), "median of the 2-week actigraphy session (L-180..L-167)",
                    [o for o in obs if -180 <= o["t"] <= -167], field="H7", readiness="ready" if len(act) >= 7 else "partial")
        elif m == "body_mass":
            last3 = sorted(obs, key=lambda o: o["t"])[-3:]
            row(m, round(statistics.fmean(o["value"] for o in last3), 1), "mean of the last 3 measurements (KB B2)", obs,
                round(vals[0], 1), round(vals[-1], 1), trend=_trend([(o["t"], o["value"]) for o in obs]))
        elif m in ("bp_sys", "bp_dia"):
            row(m, round(statistics.fmean(vals), 1), "mean of exam sessions (each a mean of 3 readings)", obs,
                round(vals[0], 1), round(vals[-1], 1))
        elif freq == "daily":
            row(m, round(statistics.median(vals), 2), "median of 180 days; personal range = p10..p90", obs,
                round(_pct(vals, 0.1), 2), round(_pct(vals, 0.9), 2), rebase=_rebase(obs),
                trend=_trend([(o["t"], o["value"]) for o in obs]))
        elif freq in ("weekly", "monthly"):
            row(m, round(statistics.median(vals), 2), f"median of {freq} measurements", obs,
                round(_pct(vals, 0.1), 2), round(_pct(vals, 0.9), 2), trend=_trend([(o["t"], o["value"]) for o in obs]))
        else:
            latest = max(obs, key=lambda o: o["t"])
            row(m, latest["value"] if len(obs) == 1 else round(statistics.fmean(vals), 3),
                "single exam" if len(obs) == 1 else "mean of exam sessions", obs)
    # planned sources: honest "missing" rows
    have = {f["field_id"] for f in out}
    planned = [("I3", "sensorimotor battery (no open data)", "planned")]
    for fid, label, src in (("B5", "orthostatic test", "TILT"), ("B11", "12-lead ECG", "PTB-XL"),
                            ("D7", "stress hormones (no female donor in MMASH)", "MMASH"),
                            ("D10", "microbiome", "OSD-572"), ("C15", "balance test", "NHANES-2003")):
        if fid not in have:
            planned.append((fid, label, src))
    for fid, label, src in planned:
        out.append({"crew_id": b.id, "field_id": fid, "metric": "", "value": f"not yet loaded: {label}", "lo": None,
                    "hi": None, "n": 0, "completeness": 0, "readiness": "missing", "rebase14": None,
                    "trend_per_30d": None, "method": "source planned in data/catalog.yaml", "unit": "",
                    "provenance": "", "source_ids": src})
    for fid, spec in sorted((b.c.get("authored") or {}).items()):
        out.append({"crew_id": b.id, "field_id": fid, "metric": "", "value": spec.get("value"), "lo": None, "hi": None,
                    "n": 1, "completeness": 1, "readiness": "ready", "rebase14": None, "trend_per_30d": None,
                    "method": "character story", "unit": spec.get("unit", ""), "provenance": AUTHORED,
                    "source_ids": "AUTHORED"})
    def order(r):
        fid = r["field_id"]
        num = int(fid[1:]) if fid[1:].isdigit() else 0
        return (FIELD_ORDER.find(fid[0]) if fid[0] in FIELD_ORDER and fid[1:].isdigit() else 99, num, r["metric"])
    out.sort(key=order)
    return out


def _rebase(obs):
    last = [o["value"] for o in obs if -14 <= o["t"] <= -1]
    return round(statistics.median(last), 2) if len(last) >= 5 else None


# ---- orchestration -------------------------------------------------------------------------------------------
def load_crew() -> list[dict]:
    return [yaml.safe_load(p.read_text(encoding="utf-8")) for p in sorted(CREW.glob("*.yaml"))]


def _sex_ranges(i4_rows: list[dict], sex: dict[str, str]) -> dict:
    """(sex, metric) -> the Inspiration4 lab's reference range for that sex (most common across that sex's draws)."""
    seen: dict = {}
    for r in i4_rows:
        s = sex.get(r["subject_id"])
        if s and r["ref_lo"] is not None and r["ref_hi"] is not None:
            seen.setdefault((s, r["metric"]), collections.Counter())[(r["ref_lo"], r["ref_hi"])] += 1
    return {k: sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] for k, c in seen.items()}


def build(i4_rows: list[dict], subjects: list[dict]) -> dict:
    df = nhanes.load() if nhanes.available() else None
    i4_sex = {s["subject_id"]: s["sex"] for s in subjects if s["subject_id"].startswith("I4-") and s["sex"]}
    ctx = {"i4": i4_rows, "i4_sex": i4_sex, "i4_sex_ranges": _sex_ranges(i4_rows, i4_sex), "norms": _norms(), "nhanes_pool": nhanes.astronaut_like(df) if df is not None else None,
           "used_nhanes": set(), "ls_donors": lifesnaps.donors(), "used_ls": set(), "subjects": subjects,
           "mmash": extras.mmash_donors(), "used_mmash": set(), "ecg": extras.ptbxl_normals(), "used_ecg": set(),
           "tilt": extras.tilt_controls(), "used_tilt": set(), "micro": extras.microbiome(),
           "balance": extras.balance_pool(), "used_balance": set()}
    out = {"observations": [], "crew_donors": [], "sessions": [], "passport_fields": []}
    PASSPORTS.mkdir(parents=True, exist_ok=True)
    # Build CM-2 last so the demo flight crew gets first pick of donors closest to their story targets.
    crew_list = sorted(load_crew(), key=lambda c: (c["id"] == "CM-2", c["id"]))
    for crew in crew_list:
        b = Builder(crew, ctx)
        b.labs()
        b.exams()
        b.daily()
        b.checkins()
        b.more_donors()
        b.sessions()
        f = fields(b)
        out["observations"] += sorted(b.obs, key=lambda r: (r["t"], r["metric"], r["session_id"]))
        out["crew_donors"] += b.donors
        out["sessions"] += b.session_rows
        out["passport_fields"] += f
        _write_json(crew, b, f)
    return out


PROV_CODE = {REAL_ASTRONAUT: "RA", REAL_GROUND: "RG", REAL_POPULATION: "RP", SYNTH_CAL: "SC", AUTHORED: "AU"}
KB_PASSPORT = DATA.parent / "knowledge-base" / "01-physiological-passport.md"


def _field_labels() -> dict:
    """Passport field names (A1..M5) from the knowledge base tables."""
    import re
    out = {}
    if KB_PASSPORT.exists():
        for line in KB_PASSPORT.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^\|\s*([A-M]\d{1,2})\s*\|\s*([^|]+?)\s*\|", line)
            if m and m.group(1) not in out:
                label = re.sub(r"[`*]|\s+[—–-]\s+.*$", "", m.group(2)).strip()
                label = re.sub("[\U0001F9D1\U0001FA7A\u231A\u200D\U0001F680\uFE0F]", "", label).strip()
                out[m.group(1)] = label[:90]
    out["CHECKIN"] = "Daily check-in (practised pre-flight)"
    return out


def _write_json(crew, b: Builder, f: list[dict]):
    series = {}
    for o in sorted(b.obs, key=lambda o: o["t"]):
        if (METRICS.get(o["metric"]) or {}).get("freq") in ("daily", "weekly", "monthly") or o["metric"] in LAB_METRICS \
                or o["metric"].startswith("microbiome_"):
            series.setdefault(o["metric"], []).append([o["t"], o["value"], PROV_CODE[o["provenance"]]])
    sessions = []
    for s in b.session_rows:
        vals = {o["metric"]: o["value"] for o in b.obs if o["session_id"] == s["session_id"]}
        sessions.append({**{k: s[k] for k in ("session_id", "t", "title", "status", "provenance", "source_ids")},
                         "values": vals})
    labels = _field_labels()
    f = [{**r, "label": (METRICS.get(r["metric"]) or {}).get("label") or labels.get(r["field_id"], r["field_id"]),
          "field_label": labels.get(r["field_id"], r["field_id"])} for r in f]
    doc = {
        "crew_id": crew["id"], "name": crew["name"], "role": crew["role"], "sex": crew["sex"], "age": crew["age"],
        "modifiers": crew.get("modifiers", []), "window": {"start": -WINDOW, "end": -1},
        "provenance_codes": {v: k for k, v in PROV_CODE.items()},
        "donors": b.donors, "fields": f, "sessions": sessions, "series": series,
    }
    (PASSPORTS / f"{crew['id']}.json").write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")),
                                                  encoding="utf-8")
