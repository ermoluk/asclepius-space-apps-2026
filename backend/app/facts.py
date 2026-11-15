"""Turn a passport + daily records into one flat dict of facts for the rule engine."""
from statistics import median

from .data import space_effects
from .news2 import news2

MIN_PRIOR_FOR_BASELINE = 7
DELTA_KEYS = ("pvt_rt", "hr_rest", "body_mass", "lymphocytes_abs")

_STREAKS = {
    "days_sleep_le6": ("sleep_hours", lambda v, f: v <= 6),  # R-SLP-01 restricted sleep: 6 h or less (JONES2022)
    "days_sleep_lt6": ("sleep_hours", lambda v, f: v < 6),  # R-SLP-02 (poor sleeper, PSQI/ISI)
    "days_hr_gt15": (
        "hr_rest",
        lambda v, f: f.get("baseline_hr_rest") is not None and v > f["baseline_hr_rest"] * 1.15,
    ),
    "days_fasting_glu_ge126": ("glucose_fasting", lambda v, f: v >= 126),
    "days_fluid_lt25": ("fluid_intake", lambda v, f: v < 2.5),
    "days_fluid_lt30": ("fluid_intake", lambda v, f: v < 3.0),  # P-02 target
    "days_intake_lt80": ("food_intake_pct", lambda v, f: v < 80),
}

_COUNTS = {
    "count7_mood_le2": ("mood_valence", lambda v: v <= 2),
    "count7_quality_le2": ("sleep_quality", lambda v: v <= 2),
    "count7_cohesion_le2": ("team_cohesion", lambda v: v <= 2),
    "count7_workload_ge8": ("workload", lambda v: v >= 8),
    "count7_exercise_lt90": ("exercise_min", lambda v: v < 90),
}


def _streak(history: list[dict], key: str, pred) -> int:
    n = 0
    for day in reversed(history):
        v = day.get(key)
        if v is None or not pred(v):
            break
        n += 1
    return n


def _bp_ge140_90(day: dict) -> bool:
    return (day.get("bp_sys") or 0) >= 140 or (day.get("bp_dia") or 0) >= 90


def _poor_sleep(day: dict) -> bool:
    hours, quality = day.get("sleep_hours"), day.get("sleep_quality")
    return (hours is not None and hours < 6) or (quality is not None and quality <= 2)


def _day_streak(history: list[dict], pred) -> int:
    n = 0
    for day in reversed(history):
        if not pred(day):
            break
        n += 1
    return n


def _qsofa(cur: dict) -> int:
    score = 0
    if cur.get("resp_rate") is not None and cur["resp_rate"] >= 22:
        score += 1
    if cur.get("confusion"):
        score += 1
    if cur.get("bp_sys") is not None and cur["bp_sys"] <= 100:
        score += 1
    return score


def _passport_data_facts(passport: dict, history: list[dict], cur: dict, facts: dict) -> None:
    """Facts from the six-month passport: personal ranges (p10..p90) and lab reference ranges."""
    for metric, r in (passport.get("personal_ranges") or {}).items():
        lo, hi = r.get("lo"), r.get("hi")
        facts[f"pbase_{metric}_lo"], facts[f"pbase_{metric}_hi"] = lo, hi
        facts[f"pbase_{metric}_ready"] = bool(r.get("ready"))
        if hi is not None:
            facts[f"days_above_pbase_{metric}"] = _streak(history, metric, lambda v, h=hi: v > h)
        if lo is not None:
            facts[f"days_below_pbase_{metric}"] = _streak(history, metric, lambda v, lo_=lo: v < lo_)
    base_hrv = facts.get("baseline_hrv_rmssd")
    if base_hrv:
        facts["days_hrv_lt70"] = _streak(history, "hrv_rmssd", lambda v: v < 0.7 * base_hrv)  # R-CV-17
    for metric, r in (passport.get("lab_ranges") or {}).items():
        lo, hi = r.get("lo"), r.get("hi")
        facts[f"lab_range_min_{metric}"], facts[f"lab_range_max_{metric}"] = lo, hi
        val = cur.get(metric)
        if val is None:
            continue  # unknown, never "normal"
        if lo is not None:
            facts[f"lab_below_{metric}"] = val < lo
        if hi is not None:
            facts[f"lab_above_{metric}"] = val > hi


def _expected_facts(cur: dict, facts: dict) -> None:
    """What NASA evidence says a healthy crew member looks like on this mission day: expected_<m> ramps from the
    personal baseline to the in-flight shift over its onset time; delta_vs_expected_<m> compares today with it."""
    day = cur.get("mission_day")
    if day is None or day < 1:
        return
    for e in space_effects():
        m = e["target"]
        base = facts.get(f"baseline_{m}")
        if base is None:
            continue
        ramp = min(1.0, day / e["onset_days"]) if e["onset_days"] else 1.0
        if e["kind"] == "shift":
            exp = base + e["value"] * ramp
        elif e["kind"] == "shift_pct":
            exp = base * (1 + e["value"] / 100 * ramp)
        else:  # level
            exp = base + (e["value"] - base) * ramp
        facts[f"expected_{m}"] = round(exp, 2)
        if cur.get(m) is not None:
            facts[f"delta_vs_expected_{m}"] = round(cur[m] - exp, 2)


def build_facts(passport: dict, history: list[dict]) -> dict:
    cur = history[-1] if history else {}
    prior = history[:-1]
    facts: dict = dict(cur)

    # Baselines: passport value, or median of prior days once enough data exist.
    for key, value in (passport.get("baselines") or {}).items():
        prior_vals = [d[key] for d in prior if d.get(key) is not None]
        if len(prior_vals) >= MIN_PRIOR_FOR_BASELINE:
            value = median(prior_vals)
        facts[f"baseline_{key}"] = value

    for key in DELTA_KEYS:
        base, val = facts.get(f"baseline_{key}"), cur.get(key)
        if base and val is not None:
            facts[f"delta_pct_{key}"] = (val - base) / base

    for name, (key, pred) in _STREAKS.items():
        facts[name] = _streak(history, key, lambda v, p=pred: p(v, facts))

    facts["days_bp_ge140_90"] = _day_streak(history, _bp_ge140_90)  # R-CV-04
    facts["count14_poor_sleep"] = sum(1 for d in history[-14:] if _poor_sleep(d))  # R-SLP-10

    window = history[-7:]
    for name, (key, pred) in _COUNTS.items():
        facts[name] = sum(1 for d in window if d.get(key) is not None and pred(d[key]))
    for d in window:
        for label in d.get("mood_labels") or []:
            facts[f"count7_label_{label}"] = 0
    for label_key in [k for k in facts if k.startswith("count7_label_")]:
        label = label_key[len("count7_label_"):]
        facts[label_key] = sum(1 for d in window if label in (d.get("mood_labels") or []))

    score = news2(cur)
    facts["news2_total"] = score["total"]
    facts["news2_max"] = score["max"]
    facts["qsofa"] = _qsofa(cur)

    hours = cur.get("hours_since_transition")
    facts["adaptation_window"] = bool(
        (cur.get("mission_day") is not None and cur["mission_day"] <= 3)
        or (hours is not None and hours <= 72)
    )

    _passport_data_facts(passport, history, cur, facts)
    _expected_facts(cur, facts)

    for mod in passport.get("modifiers") or []:
        facts[f"mod_{mod}"] = True

    if cur.get("comm_delay_s") is not None:
        facts["comm_delay_s"] = cur["comm_delay_s"]
    else:
        facts["comm_delay_s"] = (passport.get("mission") or {}).get("comm_delay_s")
    return facts
