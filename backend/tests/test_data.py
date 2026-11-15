"""Data warehouse and six-month passports built by the pipeline (`python -m pipeline all`)."""
import csv
import json
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from app import data as wh
from app.engine import assess
from app.main import app
from app.scenarios import SOLAR_EVENT_ID, get_scenario

DATA = Path(__file__).resolve().parents[2] / "data"
CREW = ["HY-CDR", "HY-MS1", "HY-MS2", "HY-PLT", "CM-2"]
PROV = {"real-astronaut", "real-ground", "real-population", "synthetic-calibrated", "authored"}
client = TestClient(app)


def test_every_crew_member_has_a_six_month_passport():
    assert wh.crew_ids() == CREW
    for cid in CREW:
        doc = wh.crew_passport(cid)
        assert doc["window"] == {"start": -180, "end": -1}
        groups = {d["field_group"] for d in doc["donors"]}
        assert {"labs", "exams", "daily", "ecg", "orthostatic"} <= groups, groups
        assert ("hormones" in groups) == (doc["sex"] == "M")  # MMASH has no female participants
        for metric in ("hr_rest", "hrv_rmssd", "sleep_hours", "mood_valence", "pvt_rt", "body_mass", "phq9"):
            pts = doc["series"][metric]
            assert pts and all(-180 <= t <= -1 for t, _, _ in pts), (cid, metric)
        modules = {f["field_id"][0] for f in doc["fields"]}
        assert set("ABCDFGHIJK") <= modules, (cid, sorted(modules))
        for f in doc["fields"]:
            assert f["readiness"] in ("ready", "partial", "missing"), f
            if f["readiness"] != "missing":
                assert set(f["provenance"].split(";")) <= PROV, f


def test_passport_has_real_daily_data_and_marks_the_fill():
    for cid in CREW:
        codes = [p for _, _, p in wh.crew_passport(cid)["series"]["hr_rest"]]
        assert codes.count("RG") >= 40, cid  # real LifeSnaps days
        assert set(codes) <= {"RG", "SC"}


def test_lifesnaps_and_nhanes_donors_are_not_shared():
    donors = [r for r in csv.DictReader(open(DATA / "warehouse" / "crew_donors.csv"))]
    for group in ("daily", "exams"):
        ids = [d["donor_subject_id"] for d in donors if d["field_group"] == group]
        assert len(ids) == len(set(ids)) == 5, group


def _i4(subject, metric, t):
    with open(DATA / "inspiration4" / "LSDS-7_Complete_Blood_Count_CBC_TRANSFORMED.csv", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r["Sample Name"] == f"{subject}_whole-blood_L-{t}_cbc":
                return float(r[f"{metric}_value_percent"]), float(r[f"{metric}_range_min_percent"])
    raise KeyError


def test_real_inspiration4_draws_sit_exactly_on_their_days():
    ms2 = wh.crew_passport("HY-MS2")
    hb = {t: (v, p) for t, v, p in ms2["series"]["hemoglobin"]}
    for t in (92, 44, 3):
        value, _ = _i4("C002", "hemoglobin", t)
        assert hb[-t] == (value, "RA")
    assert hb[-180][1] == "SC"  # L-180 draw is modelled, and says so
    f = next(f for f in ms2["fields"] if f["metric"] == "hemoglobin")
    assert (f["lo"], f["hi"]) == (11.7, 15.5)


def test_pvt_baseline_is_the_l90_run():
    for cid in CREW:
        doc = wh.crew_passport(cid)
        f = next(f for f in doc["fields"] if f["metric"] == "pvt_rt")
        l90 = next(s for s in doc["sessions"] if s["session_id"] == "cognition")["values"]["pvt_rt"]
        assert f["value"] == l90


def test_evidence_tables_cite_known_references():
    refs = yaml.safe_load(open(Path(__file__).resolve().parents[1] / "knowledge" / "references.yaml"))
    rows = list(csv.DictReader(open(DATA / "warehouse" / "evidence.csv")))
    assert {r["kind"] for r in rows} == {"limit", "space_effect", "incidence", "norm"}
    for r in rows:
        for key in filter(None, r["ref_key"].split(";")):
            assert key in refs, (r["key"], key)


def test_catalog_lists_every_source_used_in_the_warehouse():
    cat = {s["id"] for s in wh.catalog()}
    obs_sources = {s for r in wh.table("observations") for s in r["source_id"].split(";")}
    assert obs_sources <= cat, obs_sources - cat


def test_solar_event_day_replays_a_real_donki_event():
    sc = get_scenario("hygieia-flyby")
    assert sc["event"]["sep_id"] == SOLAR_EVENT_ID and "ccmc.gsfc.nasa.gov" in sc["event"]["link"]
    for m in sc["crew"]:
        assert [d["mission_day"] for d in m["history"] if d.get("spe_event_id") == SOLAR_EVENT_ID] == [4]
    assert len(wh.sep_events()) > 50


def test_datasets_endpoint():
    body = client.get("/api/datasets").json()
    rows = {s["id"]: s["rows"] for s in body["sources"]}
    assert rows["OSD-569"]["real-astronaut"] > 500 and rows["LIFESNAPS"]["real-ground"] > 500
    assert rows["NHANES-2011"]["real-population"] > 50 and rows["DONKI"]["real-events"] > 50
    assert body["crew"] == CREW and set(body["crew_observations_by_provenance"]) <= PROV


def test_crew_passport_endpoint():
    assert client.get("/api/crew").json()[3]["crew_id"] == "HY-PLT"
    doc = client.get("/api/crew/HY-MS2/passport").json()
    assert doc["name"] == "Elena Kovach" and doc["series"]["hr_rest"]
    assert client.get("/api/crew/nobody/passport").status_code == 404


def _ms2_passport():
    return get_scenario("hygieia-flyby")["crew"][3]["passport"]


def test_space_anemia_uses_the_personal_lab_range():
    pp = _ms2_passport()
    fired = assess(pp, [{"mission_day": 20, "hemoglobin": 11.0, "sym_fatigue": True}])
    assert any(h["id"] == "X15" and h["level"] == "ORANGE" for h in fired["hypotheses"])
    normal = assess(pp, [{"mission_day": 20, "hemoglobin": 13.0, "sym_fatigue": True}])
    assert not any(h["id"] == "X15" for h in normal["hypotheses"])
    waiting = assess(pp, [{"mission_day": 20, "sym_fatigue": True}])
    assert any(p["rule"] == "R-CV-16" and "hemoglobin" in p["missing"] for p in waiting["pending"])


def test_sodium_rule():
    a = assess(_ms2_passport(), [{"mission_day": 20, "sodium": 147}])
    assert any(h["id"] == "X08" and h["level"] == "ORANGE" for h in a["hypotheses"])


def test_hrv_below_personal_baseline_three_mornings():
    pp = _ms2_passport()
    low = pp["baselines"]["hrv_rmssd"] * 0.6
    hist = [{"mission_day": d, "hrv_rmssd": low, "temp": 36.6} for d in (20, 21, 22)]
    a = assess(pp, hist)
    assert any(h["id"] == "X02" and h["level"] == "YELLOW" for h in a["hypotheses"])
    assert not any(h["id"] == "X02" for h in assess(pp, hist[:2])["hypotheses"])


def test_personal_range_facts():
    from app.facts import build_facts
    pp = _ms2_passport()
    hi = pp["personal_ranges"]["hr_rest"]["hi"]
    f = build_facts(pp, [{"mission_day": d, "hr_rest": hi + 5} for d in (1, 2, 3)])
    assert f["days_above_pbase_hr_rest"] == 3 and f["pbase_hr_rest_ready"] is True
    assert f["lab_range_min_hemoglobin"] == 11.7 and "lab_below_hemoglobin" not in f  # no draw today = unknown


def test_more_real_donors_fill_ecg_orthostatic_and_hormones():
    cdr = wh.crew_passport("HY-CDR")
    by = {(f["field_id"], f["metric"]): f for f in cdr["fields"]}
    assert 120 <= by[("B11", "ecg_pr")]["value"] <= 200 and "real-ground" in by[("B11", "ecg_qtc")]["provenance"]
    assert ("B5", "ortho_dhr") in by and ("D7", "cortisol_wake") in by and ("H3", "psqi") in by
    ms2 = {f["field_id"]: f for f in wh.crew_passport("HY-MS2")["fields"]}
    assert ms2["D7"]["readiness"] == "missing"  # no female donor: stays honest, not "normal"


def test_mars_dose_rate_from_msl_rad():
    assert wh.environment("mars-transit")["value"] == 1.84


def test_hypotheses_carry_in_flight_frequency():
    plt = get_scenario("hygieia-flyby")["crew"][1]  # day 2: space adaptation, motion-sickness history
    a = assess(plt["passport"], plt["history"][:2])
    sms = next(h for h in a["hypotheses"] if h["id"] == "C089")
    assert sms["incidence"]["value"] == 0.67 and sms["incidence"]["ref"] == "SMS-SHUTTLE"  # first flight, 57 of 85


def test_biodosimetry_model_and_noaa_events():
    bio = wh.biodosimetry_model()
    assert bio["n_samples"] == 100 and bio["loocv_accuracy"] > 0.5 and "CDKN1A" in bio["genes"]
    assert sum(1 for e in wh.table("events") if e["source_id"] == "NOAA-SEP") > 200


def test_microbiome_comes_from_the_same_inspiration4_person_as_the_labs():
    doc = wh.crew_passport("HY-MS2")
    lab_donor = next(d["donor_subject_id"] for d in doc["donors"] if d["field_group"] == "labs")
    assert lab_donor == "I4-C002"
    oral = doc["series"]["microbiome_oral"]
    assert {t for t, _, _ in oral} <= {-92, -44, -3} and all(p == "RA" for _, _, p in oral)
    f = next(f for f in doc["fields"] if f["metric"] == "microbiome_oral")
    assert f["field_id"] == "D10" and "OSD-572" in f["source_ids"]


def test_balance_test_fills_c15():
    for cid in CREW:
        by = {f["metric"]: f for f in wh.crew_passport(cid)["fields"]}
        assert by["balance_conditions_passed"]["field_id"] == "C15"
        assert by["balance_conditions_passed"]["provenance"] == "real-population"


def test_expected_in_flight_adaptation_facts():
    from app.facts import build_facts
    pp = {"baselines": {"bp_sys": 116, "sleep_hours": 7.0}, "modifiers": [], "mission": {"comm_delay_s": 2}}
    f = build_facts(pp, [{"mission_day": 30, "bp_sys": 106, "sleep_hours": 6.1}])
    assert f["expected_bp_sys"] == 108.0 and f["delta_vs_expected_bp_sys"] == -2.0  # -8 mmHg after 14 days (NORSK2015)
    assert f["expected_sleep_hours"] == 6.0  # ISS average sleep
    early = build_facts(pp, [{"mission_day": 7, "bp_sys": 116}])
    assert early["expected_bp_sys"] == 112.0  # half of the shift after half the onset time


def test_biodosimetry_endpoints():
    bio = client.get("/api/biodosimetry").json()
    assert len(bio["samples"]) == 100 and {"none", "low", "high"} == set(bio["centroids"])
    high = bio["centroids"]["high"]
    r = client.post("/api/biodosimetry/classify", json={"fold_changes": high}).json()
    assert r["bucket"] == "high" and len(r["genes_used"]) == len(bio["genes"])
    assert client.post("/api/biodosimetry/classify", json={"fold_changes": {"CDKN1A": 1.0}}).status_code == 422


def test_flight_days_continue_the_passport_series():
    sc = get_scenario("hygieia-flyby")
    for m in sc["crew"]:
        hist = m["history"]
        assert all("hrv_rmssd" in d for d in hist)  # every donor here has HRV
        lo, hi = m["passport"]["personal_ranges"]["hr_rest"]["lo"], m["passport"]["personal_ranges"]["hr_rest"]["hi"]
        inside = sum(lo - 3 <= d["hr_rest"] <= hi + 3 for d in hist)
        assert inside >= 8, (m["passport"]["astronaut"]["id"], [d["hr_rest"] for d in hist], lo, hi)


# ---- Inspiration4 loader corrections (pipeline/inspiration4.py) --------------------------------------------------
def _i4_obs():
    return [r for r in wh.table("observations") if r["subject_id"].startswith("I4-")]


def _i4_value(subject, t_kind, t, metric):
    return next(r for r in _i4_obs()
                if (r["subject_id"], r["t_kind"], int(r["t"]), r["metric"]) == (subject, t_kind, t, metric))


def test_c003_l92_cbc_shift_is_realigned_in_warehouse_and_passport():
    fix = {"mch": 29.6, "mchc": 32.4, "rdw": 12.9, "platelets": 330, "mpv": 10.1, "neutrophils_abs": 6826,
           "lymphocytes_abs": 1997, "monocytes_abs": 614, "eosinophils_abs": 125}
    for metric, value in fix.items():
        r = _i4_value("I4-C003", "L", -92, metric)
        assert float(r["value"]) == value and r["quality"] == "corrected", metric
    baso = _i4_value("I4-C003", "L", -92, "basophils_abs")
    assert float(baso["value"]) == 38 and baso["quality"] == "derived"  # 0.4% x 9,600/uL
    plt = wh.crew_passport("HY-PLT")["series"]
    assert [-92, 330.0, "RA"] in plt["platelets"] and [-92, 1997.0, "RA"] in plt["lymphocytes_abs"]


def test_missing_red_cell_indices_are_derived_and_tagged():
    def v(s, k, t, m):
        return float(_i4_value(s, k, t, m)["value"])
    mchc = _i4_value("I4-C002", "L", -92, "mchc")
    assert mchc["quality"] == "derived"
    assert float(mchc["value"]) == round(v("I4-C002", "L", -92, "hemoglobin") / v("I4-C002", "L", -92, "hematocrit") * 100, 1)
    mcv = _i4_value("I4-C002", "R", 194, "mcv")
    assert mcv["quality"] == "derived"
    assert float(mcv["value"]) == round(v("I4-C002", "R", 194, "hematocrit") / v("I4-C002", "R", 194, "rbc") * 10, 1)
    mch = _i4_value("I4-C004", "L", -92, "mch")
    assert mch["quality"] == "derived"
    assert float(mch["value"]) == round(v("I4-C004", "L", -92, "hemoglobin") / v("I4-C004", "L", -92, "rbc") * 10, 1)
    assert {r["quality"] for r in _i4_obs()} <= {"", "corrected", "derived", "suspect"}


def test_reference_ranges_follow_sex_per_person():
    sex = {r["subject_id"]: r["sex"] for r in wh.table("subjects") if r["subject_id"].startswith("I4-")}
    assert sex == {"I4-C001": "M", "I4-C002": "F", "I4-C003": "F", "I4-C004": "M"}  # OSD-575 ISA metadata
    ranges = {}
    for r in _i4_obs():
        if r["ref_lo"]:
            ranges.setdefault((r["subject_id"], r["metric"]), set()).add((r["ref_lo"], r["ref_hi"]))
    assert all(len(v) == 1 for v in ranges.values()), {k: v for k, v in ranges.items() if len(v) > 1}
    hb = _i4_value("I4-C003", "L", -92, "hemoglobin")
    assert (float(hb["ref_lo"]), float(hb["ref_hi"])) == (11.7, 15.5)
    alt = _i4_value("I4-C001", "L", -3, "alt")
    assert (float(alt["ref_lo"]), float(alt["ref_hi"])) == (9, 46)  # upper limit sits in "alt_max_..." in the CMP file
    # HY-PLT (male) carries a female donor's labs, with the lab's male ranges
    f = next(f for f in wh.crew_passport("HY-PLT")["fields"] if f["metric"] == "hemoglobin")
    assert (f["lo"], f["hi"]) == (13.2, 17.1)


def test_r45_handling_artifacts_are_flagged_not_changed():
    flagged = {(r["subject_id"], r["metric"]): float(r["value"]) for r in _i4_obs() if r["quality"] == "suspect"}
    assert flagged == {("I4-C002", "glucose"): 44, ("I4-C003", "glucose"): 36, ("I4-C004", "glucose"): 43,
                       ("I4-C004", "potassium"): 5.9}
    assert all(r["t_kind"] == "R" and r["t"] == "45" for r in _i4_obs() if r["quality"] == "suspect")


def test_not_reported_cells_never_become_values():
    import math
    for r in _i4_obs():
        assert r["value"] not in ("", "NA") and math.isfinite(float(r["value"])), r
    assert not any(r["metric"] == "bilirubin" and float(r["value"]) == 0 for r in _i4_obs())


def test_crp_has_no_instrument_ceiling():
    crp = [float(r["value"]) for r in _i4_obs() if r["metric"] == "crp"]
    assert len(crp) == 28 and crp.count(max(crp)) == 1  # unlike haptoglobin (17,907,000 in 7 samples), not loaded


# ---- evidence tables after the Document 1 review (data/evidence/*.csv) -------------------------------------------
def _evidence():
    return {r["key"]: r for r in wh.table("evidence")}


def test_limits_separate_nasa_requirements_from_team_thresholds():
    ev = _evidence()
    assert ev["career_dose_limit"]["op"] == "lt" and ev["career_dose_limit"]["value_type"] == "requirement"
    assert ev["career_dose_watch"]["value_type"] == "team_threshold" and "[T]" in ev["career_dose_watch"]["note"]
    assert ev["sleep_restricted"]["op"] == "lte" and "JONES2022" in ev["sleep_restricted"]["ref_key"]


def test_restricted_sleep_rule_counts_six_hours():
    pp = {"baselines": {}, "modifiers": [], "mission": {"comm_delay_s": 2}}
    hist = [{"mission_day": d, "sleep_hours": 6.0} for d in (10, 11, 12)]
    assert any(h["id"] == "X01" for h in assess(pp, hist)["hypotheses"])


def test_incidence_main_rows_and_variants():
    inc = wh.incidence()
    assert inc["C089"]["value"] == 0.67
    assert "C056" not in inc  # 0.3/flight-year is cold sores (HSV), not herpes zoster
    assert inc["C077"] == {"value": 0.97, "unit": "events per flight-year", "ref": "CRUCIAN2016",
                           "name": "Upper respiratory symptoms"}
    assert inc["C086"]["value"] == 1.12
    rows = [r for r in wh.table("evidence") if r["kind"] == "incidence"]
    assert len({r["key"] for r in rows}) == len(rows)
    for r in rows:  # value = events / denominator (to the value's printed precision) wherever both are given
        if r["events"] and r["denominator"] and r["value"]:
            places = len(r["value"].split(".")[1]) if "." in r["value"] else 0
            assert round(float(r["events"]) / float(r["denominator"]), places) == float(r["value"]), r["key"]


def test_space_effects_keep_types_apart():
    ev = _evidence()
    assert ev["bp_sys_inflight"]["value"] == "-8" and ev["bp_dia_inflight"]["value"] == "-9"
    assert ev["bp_sys_inflight"]["uncertainty_type"] == "SE"
    effects = {e["target"]: e for e in wh.space_effects()}
    assert set(effects) == {"bp_sys", "bp_dia", "sleep_hours"}  # only single values with an onset drive expectations
    assert not any(r["target"] == "temp" for r in ev.values() if r["kind"] == "space_effect")  # core temp is not oral
    for r in ev.values():
        if r["value_type"] == "observed_range":
            assert r["value"] == "" and float(r["lo"]) < float(r["hi"]), r["key"]
