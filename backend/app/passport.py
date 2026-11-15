"""Passport baselines (Inspiration4 C001 pre-flight labs) and passport derivation from onboarding answers."""
import csv
import logging
from functools import lru_cache
from pathlib import Path

from .data import crew_ids, passport_baselines

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "inspiration4"
CBC = DATA_DIR / "LSDS-7_Complete_Blood_Count_CBC_TRANSFORMED.csv"
CMP = DATA_DIR / "LSDS-8_Comprehensive_Metabolic_Panel_CMP_TRANSFORMED.csv"
TIMEPOINTS = ("L-92", "L-44", "L-3")
BASELINES_SOURCE = "NASA OSDR OSD-569/OSD-575 Inspiration4 crew C001 pre-flight"
DEFAULT_CREW = "CM-2"  # passport used for the single-person scenarios and the onboarding quiz defaults
log = logging.getLogger(__name__)

# Fallback if the dataset is not available (the means of the C001 values at L-92, L-44, L-3).
_FALLBACK = {"lymphocytes_abs": 2256, "hemoglobin": 14.6, "glucose": 77.3}

# Quiz key -> (one-way comm delay s, vehicle, profile shown in the header). Generic names, no real missions.
_MISSION = {
    "leo": (2.0, "Orbital station", "Low Earth orbit"),
    "lunar": (1.3, "Lunar orbit / surface", "Lunar"),
    "mars": (760.0, "Mars transit vehicle", "Mars transit"),
}
_MODIFIER_ANSWERS = {
    "prior_motion_sickness": "P-01",
    "kidney_stone": "P-02",
    "sans_risk_or_vision_change": "P-03",
    "migraine": "P-05",
    "poor_sleeper": "P-10",
}
_PERSONAL_DEFAULTS = {"hr_rest": 58, "bp_sys": 116, "spo2": 98, "temp": 36.6, "pvt_rt": 262,
                      "body_mass": 72.0, "sleep_hours": 7.0}


def _s(id, when, what, how, feeds, source):
    return {"id": id, "when": when, "what": what, "how": how, "feeds": feeds, "source": source}


# Pre-flight data-collection timeline: NASA reference schedules (L-XX = days before launch); real timings vary by
# mission. Sources: LHS-TB (OCHMO longitudinal health surveillance brief), STDMEAS (Spaceflight Standard Measures,
# ISS design 2018), SPACEPHYS-2024 (HRP IWS poster), HSP-A2 (Artemis II Health Stabilization Program).
PREFLIGHT_TIMELINE: list[dict] = [
    _s("eye-exam", "L-21/18 months and/or L-9/6 months",
       "Comprehensive eye examination", "MRI; acuity (distance and near); refraction; visual fields; Amsler grid; contrast sensitivity; "
       "fundoscopy and retinal photography; tonometry; high-resolution OCT; optical biometry; 2-D ultrasound",
       ["G1 near/far acuity", "G2 OCT, IOP, fundus", "G4 eye exam set", "P-03", "P-13"], "LHS-TB"),
    _s("ultrasound", "before L-365 d (or as indicated)", "Ultrasound imaging",
       "Abdominal and retroperitoneal for all; pelvic for females", ["C18 ultrasound", "P-02"], "LHS-TB"),
    _s("medical-core", "Pre-mission (timing set per mission)",
       "Physical exam, ECG, neurological assessment, hearing, nutrition, dental exam with orthopantomogram, "
       "H. pylori and tuberculosis testing, MRSA nasal screen",
       "Flight-surgeon exam; gaze, finger-to-nose, Romberg, tandem-walk checks; audiogram; panoramic dental X-ray; lab tests; nasal swab",
       ["B11 ECG", "C14 neuro exam", "C16 audiogram", "C17 dental", "C18 ultrasound", "C19 H. pylori/TB", "C20 MRSA screen", "P-24", "P-26"], "LHS-TB"),
    _s("personality", "Any time pre-flight", "Personality profile",
       "IPIP-NEO questionnaire (paper); BFI-2 may stay as an alternative", ["J1 personality (tone only, never triage)"], "STDMEAS"),
    _s("actigraphy", "L-270 and L-180 (two 2-week sessions)", "Actigraphy and sleep logs",
       "Wrist actigraph on the non-dominant wrist (activity, light exposure) plus a brief daily post-sleep survey",
       ["baselines.sleep_hours", "H2 chronotype", "H7 actigraphy 2x2 weeks", "P-09", "P-10"], "STDMEAS"),
    _s("cellular", "L-270 and L-90", "Cellular profile",
       "Blood (2 tubes, 10 mL) and one saliva sample the same morning: stress hormones, viral shedding, proteins, blood counts, cell types",
       ["D1 CBC baseline", "D7 cellular profile", "P-04", "P-23"], "STDMEAS"),
    _s("strength-fitness", "L-270/180 and L-90/30", "Isokinetic strength and functional fitness",
       "Isokinetic dynamometry and functional fitness assessment", ["F6 strength baseline", "P-12"], "SPACEPHYS-2024"),
    _s("sensorimotor-fam", "L-225", "Sensorimotor familiarisation",
       "Practice run of the sensorimotor battery (not used as the baseline)", ["sensorimotor learning effect"], "STDMEAS"),
    _s("biochem", "L-180", "Biochemical markers",
       "Early-morning blood (3 tubes, 15.7 mL): CBC, comprehensive metabolic panel, chemistry; 24-hour urine; exercise log",
       ["D8 biochemical markers", "D9 24-h urine", "baselines.lymphocytes_abs", "baselines.hemoglobin", "baselines.glucose"], "STDMEAS"),
    _s("cimt", "L-180", "Carotid intima-media thickness",
       "Ultrasound of the carotid wall plus a short exercise, diet and sleep survey", ["B12 carotid IMT", "P-17"], "STDMEAS"),
    _s("vo2peak", "L-180 and L-60", "Aerobic capacity (VO2peak)",
       "Graded exercise test with gas exchange", ["F5 VO2peak"], "SPACEPHYS-2024"),
    _s("dxa", "L-180/30", "Bone mineral density and body composition",
       "DXA scan", ["F7 BMD and body composition", "baselines.body_mass", "P-12"], "SPACEPHYS-2024"),
    _s("muscle-quality", "L-180 and L-60", "Muscle quality", "Muscle imaging", ["F8 muscle quality"], "SPACEPHYS-2024"),
    _s("cognition", "L-120 (familiarisation) and L-90 (baseline)", "Cognition battery",
       "10-test computerised battery (memory, attention, abstraction, spatial orientation, emotion recognition, reasoning, "
       "visual tracking, risk decisions, sensorimotor, vigilant attention); use L-90 as the baseline",
       ["K3 cognition battery", "baselines.pvt_rt"], "STDMEAS"),
    _s("sensorimotor", "L-90", "Sensorimotor baseline",
       "Sit-to-stand; tandem walk eyes closed and open; recovery from prone and 3-minute stand; motion-sickness questionnaire",
       ["I3 sensorimotor battery", "P-01", "P-25"], "STDMEAS"),
    _s("posturography", "L-90/30", "Neurovestibular platform test (dynamic posturography)",
       "Platform posturography", ["C15 posturography", "P-25"], "LHS-TB"),
    _s("microbiome", "L-90", "Microbiome baseline",
       "Body swabs (forearm, forehead, nostril, control), saliva samples over 7 days, stool kit and a short hygiene survey",
       ["D10 microbiome", "P-24"], "STDMEAS"),
    _s("medical-labs", "L-90/30", "Laboratory testing, short eye exam, strength and diet",
       "Lab panel; less comprehensive eye exam; isometric mid-thigh pull; dietary and supplement intake",
       ["D8 biochemical markers", "G4 eye exam set", "F6 strength baseline", "L5 nutrition log"], "LHS-TB"),
    _s("hsp", "L-14 d", "Health Stabilization Program quarantine",
       "Crew quarantine in Houston; mission simulations and medical checkouts continue; masks and distancing; "
       "can exit and re-enter 14 days before any new launch date",
       ["final vitals re-baseline (last 14 days)", "infection exposure control"], "HSP-A2"),
    _s("ksc", "L-6 d", "Move to the launch site", "Crew flies to the Kennedy Space Center; checkouts continue",
       ["final vitals re-baseline (last 14 days)"], "HSP-A2"),
]


def _mean(path: Path, column: str) -> float:
    with open(path, encoding="utf-8-sig", newline="") as f:
        vals = [float(r[column]) for r in csv.DictReader(f)
                if r["Sample Name"].startswith("C001_") and any(f"_{t}_" in r["Sample Name"] + "_" for t in TIMEPOINTS)]
    if not vals:
        raise ValueError(f"no C001 pre-flight rows in {path.name}")
    return sum(vals) / len(vals)


@lru_cache(maxsize=1)
def inspiration4_baselines() -> dict:
    try:
        return {
            "lymphocytes_abs": round(_mean(CBC, "absolute_lymphocytes_value_cells_per_microliter")),
            "hemoglobin": round(_mean(CBC, "hemoglobin_value_percent"), 1),  # g/dL despite the column name
            "glucose": round(_mean(CMP, "glucose_value_milligram_per_deciliter"), 1),
        }
    except (OSError, KeyError, ValueError) as e:
        log.warning("Inspiration4 CSV unavailable (%s); using built-in fallback baselines", e)
        return dict(_FALLBACK)


def population_baselines() -> dict:
    """Baselines for a crew member without a six-month passport: Inspiration4 pre-flight labs plus typical resting
    vitals. The engine replaces each with the member's own median once 7 prior days exist (facts.py)."""
    return {**inspiration4_baselines(), **_PERSONAL_DEFAULTS}


def default_baselines(crew_id: str = DEFAULT_CREW) -> dict:
    """Baselines from the crew member's six-month passport (data/passports); constants only fill gaps."""
    return {**population_baselines(), **(passport_baselines(crew_id).get("baselines") or {})}


def passport_data(crew_id: str = DEFAULT_CREW) -> dict:
    """Engine inputs from the six-month passport: personal ranges, lab reference ranges, source line."""
    d = passport_baselines(crew_id)
    return {"personal_ranges": d.get("personal_ranges", {}), "lab_ranges": d.get("lab_ranges", {}),
            "baselines_source": d.get("baselines_source") or BASELINES_SOURCE, "passport_ref": crew_id}


def preflight_timeline() -> list[dict]:
    return [{**s, "feeds": list(s["feeds"])} for s in PREFLIGHT_TIMELINE]


POPULATION_SOURCE = ("Population defaults (NASA OSDR Inspiration4 pre-flight labs, typical resting vitals) "
                     "until 7 days of own check-ins")


def _baseline_block(a: dict) -> tuple[dict, dict]:
    """(baselines, passport data) for the derived passport.

    new_member -> no six-month passport: population baselines, no personal or lab ranges, no passport_ref.
    passport_ref of a known crew member -> that member's six-month passport.
    Neither -> the default crew passport (CM-2), as for the single-astronaut demo scenarios."""
    if a.get("new_member"):
        return population_baselines(), {"personal_ranges": {}, "lab_ranges": {},
                                        "baselines_source": POPULATION_SOURCE, "passport_ref": None}
    ref = a.get("passport_ref")
    if ref is not None:
        if ref in crew_ids():
            return default_baselines(ref), passport_data(ref)
        return population_baselines(), {"personal_ranges": {}, "lab_ranges": {},
                                        "baselines_source": POPULATION_SOURCE, "passport_ref": None}
    return default_baselines(), passport_data()


def derive_passport(answers: dict | None) -> dict:
    a = answers or {}
    profile = a.get("mission_profile")
    delay, vehicle, profile_name = _MISSION[profile if profile in _MISSION else "mars"]
    modifiers = [code for key, code in _MODIFIER_ANSWERS.items() if a.get(key)]
    baselines, pdata = _baseline_block(a)
    return {
        "astronaut": {"id": a.get("id") or "CM-1", "name": a.get("name") or "Crew member",
                      "role": a.get("role") or "Mission Specialist"},
        "mission": {"profile": profile_name, "vehicle": vehicle, "comm_delay_s": delay},
        "baselines": {**baselines, **(a.get("baselines") or {})},
        **pdata,
        "modifiers": modifiers,
        "countermeasures": list(a.get("helpers") or []),
        "preflight": preflight_timeline(),
    }
