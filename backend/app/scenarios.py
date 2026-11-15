"""Demo scenario: Hygieia I, a fictional ten-day lunar flyby with a fictional crew of four, told day by day.

Every mission day has a story event (STORY). The events reuse the engine's worked examples (09-worked-examples
S1-S4A) on a 10-day flight: space adaptation on day 2 (S4A), a real solar particle event replayed on day 4 and
possible radiation sickness on day 5 (S3, symptoms only: no blood is drawn in flight), a kidney stone during
far-side loss of signal on day 6, a cabin CO2 spike on day 7 (S2 without SANS, which needs 30+ days), sleep debt on
days 8-9 (S1) and orthostatic intolerance at splashdown. Every crew member has a filled morning and evening
check-in for every day. Deterministic (seeded per crew member).
"""
import random

from .data import sep_event, series_stats
from .passport import default_baselines, passport_data, preflight_timeline

# Real solar energetic particle event replayed on flight day 4 (NASA DONKI snapshot, GOES >10 MeV protons).
SOLAR_EVENT_ID = "2024-05-10T13:35:00-SEP-001"
SPE_DAY = 4

# Fictional mission and spacecraft (no real mission names in the demo).
MISSION_NAME = "Hygieia I"
_MISSION = {"profile": f"Lunar flyby ({MISSION_NAME})", "vehicle": "Panacea", "comm_delay_s": 1.3}
# Fictional crew. (id, name, role, sex, age, modifiers, countermeasures, seed). Resting HR, HRV, blood pressure,
# reaction-time and temperature baselines come from each member's six-month passport (data/passports/<id>.json).
_CREW = (
    ("HY-CDR", "Daniel Arenas", "Commander", "M", 48, [], ["music", "exercise"], 4711),
    ("HY-PLT", "Marcus Bell", "Pilot", "M", 42, ["P-01"], ["call to family"], 4712),
    ("HY-MS1", "Thomas Rein", "Mission Specialist 1", "M", 39, ["P-05", "P-10"], ["photos of Earth"], 4713),
    ("HY-MS2", "Elena Kovach", "Mission Specialist 2", "F", 44, ["P-02", "P-15"],
     ["journal", "talking with a crewmate"], 4714),
)
CREW_IDS = tuple(c[0] for c in _CREW)
SCENARIO_ID = "hygieia-flyby"

# Illustrative, scaled from published lunar-flight dosimetry: belt passes on days 1-2, GCR-only days after (mSv/day).
_DOSE = [1.0, 2.5, 0.7, 0.6, 0.6, 0.7, 0.6, 0.7, 0.6, 0.8]
_SPE_DOSE = 3.0  # extra dose on the event day, crew inside the storm shelter (illustrative)
# Cabin CO2, 1-hour average (mmHg): one cabin, the same for the whole crew. Day 7: CO2 removal glitch (fictional).
_CO2_1H = [2.1, 1.9, 2.0, 1.8, 2.2, 2.0, 3.4, 2.4, 2.1, 1.9]
# Wrist actigraphy nightly sleep: short first nights, ~6.5-7.5 h later; MS-1 is an owl.
_SLEEP = [6.3, 6.4, 7.0, 7.2, 7.3, 6.8, 7.1, 7.2, 7.3, 6.8]
_SLEEP_OFFSET = {"HY-CDR": 0.1, "HY-PLT": -0.1, "HY-MS1": -0.4, "HY-MS2": 0.0}
# MS-2 fluid (L/day): low on days 2-3 (P-02 target 3.0 L), again on days 6-7, recovered from day 8.
_MS2_FLUID = [3.2, 2.8, 1.9, 3.3, 3.4, 2.8, 2.7, 3.2, 3.4, 3.1]
_MOOD_WORDS = {"HY-CDR": ["calm"], "HY-PLT": ["energetic"], "HY-MS1": ["content"], "HY-MS2": ["calm", "content"]}

# Story days: (mission day, dock caption, what happens, crew members involved).
STORY = (
    (1, "Launch · Van Allen belt pass",
     "Launch and passes through the Van Allen belts. Marcus, who was motion-sick on an earlier flight, is "
     "nauseous; Thomas has the usual headache and stuffy nose of the first hours.", ["HY-PLT", "HY-MS1"]),
    (2, "Space adaptation syndrome",
     "Fluid shift and vestibular adaptation. Marcus: headache, congestion, nausea and back pain, no fever. "
     "Daniel: back pain. Expected on day 2: reassurance, plus motion-sickness care for Marcus.",
     ["HY-PLT", "HY-CDR", "HY-MS1"]),
    (3, "Low fluid intake",
     "Elena, with a kidney-stone history, drank 2.8 L and then 1.9 L (her target is 3 L). "
     "The console asks her to drink more before the stone risk grows.", ["HY-MS2"]),
    (4, "Solar particle event · shelter",
     "Replay of a real solar particle event from NASA DONKI (GOES >10 MeV protons, 10 May 2024), shifted to "
     "flight day 4. The crew builds the storm shelter in Panacea; the day's dose jumps (illustrative).",
     list(CREW_IDS)),
    (5, "Possible radiation sickness",
     "About 26 h after the flare Thomas reports nausea and fatigue. Symptoms plus timing raise a RED possible "
     "acute radiation syndrome; the console asks for a lymphocyte count and prepares a packet for the ground.",
     ["HY-MS1"]),
    (6, "Far side · kidney stone during loss of signal",
     "Closest approach to the Moon and about 40 min without a link. Elena reports colicky flank pain and nausea: "
     "RED kidney stone. Onboard steps first; the packet waits in the queue.", ["HY-MS2"]),
    (7, "Cabin CO₂ spike",
     "Cabin CO₂ reaches 3.4 mmHg for an hour (CO₂ removal glitch, fictional). Marcus gets a headache; the whole "
     "crew gets the CO₂ check. Elena's fluid intake is low again.", list(CREW_IDS)),
    (8, "Sleep debt builds",
     "Daniel has covered the night watches since Elena's emergency: a third night under 6 h. "
     "Sleep deficit flagged.", ["HY-CDR"]),
    (9, "Fatigue before re-entry",
     "Fourth short night, heavy re-entry preparation, sleepiness 7 of 9 and a 312 ms reaction test: fatigue "
     "impairing performance. Critical re-entry tasks should go to a rested crewmate.", ["HY-CDR"]),
    (10, "Re-entry and splashdown",
     "Splashdown after about 10 days. Back in gravity Elena's blood pressure drops to 88/56 with dizziness on "
     "standing: orthostatic intolerance.", ["HY-MS2"]),
)

# What each member reports on their story days (overrides the ordinary check-in of that day).
_EVENTS: dict[str, dict[int, dict]] = {
    "HY-CDR": {
        1: {"sleep_quality": 3, "kss": 4, "workload": 7},
        2: {"sym_back_pain": True, "physical_state": 5},
        4: {"workload": 7},
        # fixture S1 on days 5-9: sleep 7.2, 5.5, 5.2, 5.8, 5.4 h; workload 5, 6, 8, 9, 8
        5: {"sleep_hours": 7.2, "workload": 5},
        6: {"sleep_hours": 5.5, "workload": 6, "sleep_quality": 3, "kss": 4},
        7: {"sleep_hours": 5.2, "workload": 8, "sleep_quality": 2, "kss": 5, "pvt_rt": 278, "fatigue": 4},
        8: {"sleep_hours": 5.8, "workload": 9, "sleep_quality": 2, "kss": 6, "pvt_rt": 289, "fatigue": 4,
            "mood_valence": 4, "physical_state": 4},
        9: {"sleep_hours": 5.4, "workload": 8, "sleep_quality": 2, "kss": 7, "pvt_rt": 312, "mood_valence": 3,
            "fatigue": 5, "physical_state": 4, "mood_labels": ["irritable"], "hrv_rmssd": 52.0},
        10: {"sleep_hours": 6.2, "kss": 5, "workload": 7, "fatigue": 4},
    },
    "HY-PLT": {
        1: {"sym_nausea": True, "food_intake_pct": 70, "physical_state": 4, "sleep_quality": 2, "mood_valence": 4,
            "fatigue": 3},
        # fixture S4A: headache, congestion, nausea, back pain, no fever
        2: {"sym_headache": True, "sym_nasal_congestion": True, "sym_nausea": True, "sym_back_pain": True,
            "temp": 36.8, "food_intake_pct": 75, "physical_state": 3, "sleep_quality": 3, "mood_valence": 4},
        4: {"workload": 7},
        7: {"sym_headache": True, "physical_state": 5},
        8: {"mood_labels": ["homesick"]},
    },
    "HY-MS1": {
        1: {"sym_headache": True, "sym_nasal_congestion": True, "sleep_quality": 3},
        2: {"sym_headache": True, "sym_nasal_congestion": True, "physical_state": 5},
        4: {"workload": 7, "mood_valence": 4, "mood_labels": ["anxious"]},
        # fixture S3 symptoms (no lymphocyte count: none on board)
        5: {"sym_nausea": True, "sym_fatigue": True, "hr_rest": 74, "hrv_rmssd": 31.5, "temp": 36.9,
            "physical_state": 3,
            "food_intake_pct": 60, "kss": 5, "fatigue": 5, "mood_valence": 3, "mood_labels": ["anxious"],
            "workload": 3, "exercise_min": 0, "sleep_quality": 2},
        6: {"physical_state": 5, "fatigue": 3},
    },
    "HY-MS2": {
        4: {"workload": 7, "mood_valence": 4, "mood_labels": ["anxious"]},
        6: {"sym_flank_pain": True, "sym_nausea": True, "hr_rest": 92, "hrv_rmssd": 17.0, "physical_state": 2,
            "food_intake_pct": 50,
            "mood_valence": 3, "mood_labels": ["anxious"], "fatigue": 5, "workload": 3, "exercise_min": 0,
            "kss": 4},
        7: {"food_intake_pct": 82, "physical_state": 4, "mood_valence": 4},
        10: {"bp_sys": 88, "bp_dia": 56, "sym_dizziness": True, "physical_state": 3, "mood_valence": 4, "fatigue": 4},
    },
}


class _Continue:
    """Continue a crew member's real pre-flight passport series into flight (AR(1) on the donor's own median, SD
    and day-to-day autocorrelation), so the trend has no seam at launch."""

    def __init__(self, crew_id: str, metric: str, rng: random.Random, decimals: int = 0):
        self.st = series_stats(crew_id, metric)
        self.rng, self.dec = rng, decimals
        self.x = self.st["last"] if self.st else None

    def next(self, fallback: float) -> float:
        if not self.st:
            return fallback
        st = self.st
        self.x = st["median"] + st["phi"] * (self.x - st["median"]) + \
            self.rng.gauss(0, st["sd"] * (1 - st["phi"] ** 2) ** 0.5)
        v = round(self.x, self.dec)
        return int(v) if self.dec == 0 else v


def _passport(cid: str, name: str, role: str, sex: str, age: int, modifiers, countermeasures) -> dict:
    """Baselines, personal ranges and lab ranges come from the crew member's six-month pre-flight passport
    built by the data pipeline (data/passports/<crew_id>.json)."""
    return {
        "astronaut": {"id": cid, "name": name, "role": role, "sex": sex, "age": age},
        "mission": dict(_MISSION),
        "baselines": default_baselines(cid),
        **passport_data(cid),
        "modifiers": list(modifiers),
        "countermeasures": list(countermeasures),
        "preflight": preflight_timeline(),
    }


def _ordinary_day(rng: random.Random, d: int, cid: str, base: dict, hr: _Continue, hrv: _Continue) -> dict:
    """A normal day's morning and evening check-in (vitals, sleep, reaction test, mood, intake, exercise)."""
    day = {
        "mission_day": d,
        # morning: body and sleep
        "sleep_hours": round(_SLEEP[d - 1] + _SLEEP_OFFSET[cid], 1),
        "sleep_quality": 3 if d <= 2 else rng.choice([3, 4, 4, 5]),
        "kss": rng.randint(2, 4),
        "physical_state": rng.choice([5, 6, 6]),
        "hr_rest": hr.next(rng.randint(55, 62)),
        "bp_sys": round(base["bp_sys"]) + rng.randint(-3, 3),
        "bp_dia": round(base.get("bp_dia", 75)) + rng.randint(-3, 3),
        "temp": round(base.get("temp", 36.6) + rng.uniform(-0.2, 0.2), 1),
        "spo2": rng.randint(96, 99),
        "pvt_rt": round(base.get("pvt_rt", 262)) + rng.randint(-12, 12),
        # evening: mind and day
        "mood_valence": rng.choice([5, 5, 6]),
        "mood_labels": list(_MOOD_WORDS[cid]),
        "team_cohesion": rng.choice([4, 5, 5]),
        "workload": rng.randint(4, 6),
        "fatigue": rng.choice([2, 2, 3]),
        # flywheel sessions of about 30 min; none on launch and re-entry days
        "exercise_min": 0 if d in (1, 10) else rng.randint(25, 35),
        "fluid_intake": _MS2_FLUID[d - 1] if cid == "HY-MS2" else round(rng.uniform(2.6, 3.4), 1),
        "food_intake_pct": rng.randint(85, 100),
    }
    if hrv.st:
        day["hrv_rmssd"] = hrv.next(0)
    return day


def _environment(d: int, cum_before: float) -> dict:
    """Cabin and radiation context of the day (the same for the whole crew)."""
    dose = _DOSE[d - 1] + (_SPE_DOSE if d == SPE_DAY else 0)
    co2_7d = _CO2_1H[max(0, d - 7):d]
    env = {"co2_1h": _CO2_1H[d - 1], "co2_7d": round(sum(co2_7d) / len(co2_7d), 1),
           "dose_today": round(dose, 1), "dose_cumulative": round(cum_before + dose, 1)}
    if d >= SPE_DAY:
        env["hours_since_spe"] = 2 + 24 * (d - SPE_DAY)
    if d == SPE_DAY:
        env["spe_alert"] = True
        if sep_event(SOLAR_EVENT_ID):
            env["spe_event_id"] = SOLAR_EVENT_ID
    if d == 6:
        env["comm_los"] = True  # far-side loss of signal
    if d == 10:
        env["phase"] = "landing"
    return env


def _member(cid, name, role, sex, age, modifiers, countermeasures, seed) -> dict:
    rng = random.Random(seed)
    passport = _passport(cid, name, role, sex, age, modifiers, countermeasures)
    base = passport["baselines"]
    # own streams, so the passport continuation does not shift when check-in fields are added or changed
    hr = _Continue(cid, "hr_rest", random.Random(seed * 10 + 1))
    hrv = _Continue(cid, "hrv_rmssd", random.Random(seed * 10 + 2), 1)
    history, cum = [], 0.0
    for d in range(1, 11):
        day = _ordinary_day(rng, d, cid, base, hr, hrv)
        env = _environment(d, cum)
        cum = env["dose_cumulative"]
        day.update(env)
        day.update(_EVENTS[cid].get(d, {}))
        history.append(day)
    return {"passport": passport, "history": history}


def _hygieia_flyby() -> dict:
    crew = [_member(*c) for c in _CREW]
    ev = sep_event(SOLAR_EVENT_ID)
    return {
        "id": SCENARIO_ID,
        "title": f"{MISSION_NAME} - lunar flyby (fictional mission and crew)",
        "description": f"{MISSION_NAME}: a ten-day free-return lunar flyby aboard the Panacea capsule (closest "
                       "approach on flight day 6, splashdown about day 10), told day by day. The mission and crew "
                       "are fictional and all values are illustrative: daily check-ins as the crew would file them, "
                       "sleep as from wrist actigraphy, personal-dosimeter dose scaled from published lunar-flight "
                       "dosimetry "
                       "(belt passes on days 1-2), no in-flight blood labs. Day 2 space adaptation; day 4 a solar "
                       "particle event"
                       + (f" (replay of the real event {SOLAR_EVENT_ID} from NASA DONKI, shifted in time)"
                          if ev else "")
                       + "; day 5 possible radiation sickness; day 6 far-side loss of signal while Mission "
                         "Specialist 2, with a kidney-stone history, reports flank pain; day 7 a cabin CO₂ spike; "
                         "days 8-9 the commander's sleep debt; day 10 splashdown.",
        "passport": crew[3]["passport"],
        "history": crew[3]["history"],
        "crew": crew,
        "story": [{"mission_day": d, "title": t, "detail": text, "crew": list(who)} for d, t, text, who in STORY],
        **({"event": ev} if ev else {}),
    }


_BUILDERS = {SCENARIO_ID: _hygieia_flyby}


def get_scenario(scenario_id: str) -> dict:
    return _BUILDERS[scenario_id]()  # KeyError for unknown ids


def list_scenarios() -> list[dict]:
    out = []
    for sid in _BUILDERS:
        s = get_scenario(sid)
        out.append({"id": s["id"], "title": s["title"], "description": s["description"],
                    "days": len(s["history"]), "crew_size": len(s.get("crew", [None]))})
    return out
