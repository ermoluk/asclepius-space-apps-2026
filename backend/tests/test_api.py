"""API tests (FastAPI TestClient)."""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _hyp(a, cid):
    return next((h for h in a["hypotheses"] if h["id"] == cid), None)


def _assess_scenario(sid):
    sc = client.get(f"/api/scenarios/{sid}").json()
    r = client.post("/api/assess", json={"passport": sc["passport"], "history": sc["history"]})
    assert r.status_code == 200, r.text
    return sc, r.json()


def test_health():
    assert client.get("/api/health").json() == {"status": "ok"}


def test_knowledge():
    k = client.get("/api/knowledge").json()
    assert set(k) == {"counts", "conditions", "actions", "references"}
    assert k["counts"]["rules"] >= 78 and k["counts"]["conditions"] > 0


def test_scenarios_list():
    items = client.get("/api/scenarios").json()
    assert [(s["id"], s["days"], s["crew_size"]) for s in items] == [("hygieia-flyby", 10, 4)]
    assert all(s["title"] and s["description"] for s in items)


def test_assess_scenario_last_day():
    _, a = _assess_scenario("hygieia-flyby")  # MS-2 at splashdown
    assert a["overall_level"] == "RED"


def test_assess_rejects_bad_values():
    sc = client.get("/api/scenarios/hygieia-flyby").json()
    bad = dict(sc["history"][-1], spo2=150)
    r = client.post("/api/assess", json={"passport": sc["passport"], "history": [bad]})
    assert r.status_code == 422


def test_derive_passport_modifiers():
    r = client.post("/api/passport/derive", json={"answers": {
        "prior_motion_sickness": True, "kidney_stone": True}})
    assert r.status_code == 200
    assert {"P-01", "P-02"} <= set(r.json()["modifiers"])


def test_derive_passport_defaults():
    p = client.post("/api/passport/derive", json={"answers": {
        "name": "A", "mission_profile": "lunar", "helpers": ["x"]}}).json()
    assert p["mission"]["comm_delay_s"] == 1.3 and p["countermeasures"] == ["x"]
    for k in ("lymphocytes_abs", "hemoglobin", "glucose", "hr_rest", "bp_sys", "spo2", "temp",
              "pvt_rt", "body_mass", "sleep_hours"):
        assert k in p["baselines"]
    from app.data import passport_baselines
    expected = passport_baselines("CM-2")
    assert p["baselines"]["hr_rest"] == expected["baselines"]["hr_rest"]
    assert "Inspiration4" in p["baselines_source"] and "LifeSnaps" in p["baselines_source"]
    assert p["personal_ranges"]["hr_rest"]["lo"] < p["baselines"]["hr_rest"] < p["personal_ranges"]["hr_rest"]["hi"]
    assert p["lab_ranges"]["hemoglobin"]["lo"] == 13.2 and p["passport_ref"] == "CM-2"


def test_scenarios_are_deterministic_and_shaped():
    a, b = client.get("/api/scenarios/hygieia-flyby").json(), client.get("/api/scenarios/hygieia-flyby").json()
    assert a == b and len(a["history"]) == 10
    assert a["passport"]["astronaut"]["id"] == "HY-MS2"


def test_unknown_scenario_404():
    assert client.get("/api/scenarios/nope").status_code == 404


def test_sym_extra_must_be_bool():
    sc = client.get("/api/scenarios/hygieia-flyby").json()
    p = sc["passport"]
    ok = client.post("/api/assess", json={"passport": p, "history": [{"mission_day": 1, "sym_cough": True}]})
    assert ok.status_code == 200
    bad = client.post("/api/assess", json={"passport": p, "history": [{"mission_day": 1, "sym_cough": "yes"}]})
    assert bad.status_code == 422


def test_history_empty_422():
    sc = client.get("/api/scenarios/hygieia-flyby").json()
    r = client.post("/api/assess", json={"passport": sc["passport"], "history": []})
    assert r.status_code == 422


# --- fix round 1: validation of passport/derive input, real CSV baselines ---------------------

@pytest.mark.parametrize("answers", [
    {"baselines": "x"}, {"helpers": 5}, {"mission_profile": ["a"]}, {"mission_profile": "venus"},
    {"kidney_stone": "maybe"}, {"baselines": {"hr_rest": "abc"}}, {"baselines": {"hr_rest": None}},
    {"name": 5},
])
def test_derive_rejects_malformed_answers(answers):
    assert client.post("/api/passport/derive", json={"answers": answers}).status_code == 422


@pytest.mark.parametrize("baselines", [{"hr_rest": "abc", "glucose": "x"}, {"hr_rest": None}, "x"])
def test_assess_rejects_bad_baselines(baselines):
    sc = client.get("/api/scenarios/hygieia-flyby").json()
    pp = dict(sc["passport"], baselines=baselines)
    r = client.post("/api/assess", json={"passport": pp, "history": sc["history"]})
    assert r.status_code == 422


@pytest.mark.parametrize("patch", [{"sleep_hours": -1}, {"hr_rest": "fast"}, {"temp": 50},
                                   {"mood_valence": 0}, {"kss": 10}, {"glucose": 5}])
def test_assess_rejects_garbage_day_values(patch):
    sc = client.get("/api/scenarios/hygieia-flyby").json()
    day = dict(sc["history"][-1], **patch)
    r = client.post("/api/assess", json={"passport": sc["passport"], "history": [day]})
    assert r.status_code == 422


def test_baselines_come_from_inspiration4_csv(monkeypatch):
    import csv
    from app import passport as pp

    def mean(path, col):
        with open(path, encoding="utf-8-sig") as fh:
            v = [float(r[col]) for r in csv.DictReader(fh) if r["Sample Name"].startswith("C001_")
                 and any(f"_{t}_" in r["Sample Name"] + "_" for t in ("L-92", "L-44", "L-3"))]
        assert len(v) == 3
        return sum(v) / 3

    # Poison the fallback: values can only come from the CSVs.
    monkeypatch.setattr(pp, "_FALLBACK", {"lymphocytes_abs": -1, "hemoglobin": -1, "glucose": -1})
    pp.inspiration4_baselines.cache_clear()
    try:
        b = pp.inspiration4_baselines()
        assert b["lymphocytes_abs"] == round(mean(pp.CBC, "absolute_lymphocytes_value_cells_per_microliter")) == 2256
        assert b["hemoglobin"] == round(mean(pp.CBC, "hemoglobin_value_percent"), 1) == 14.6
        assert b["glucose"] == round(mean(pp.CMP, "glucose_value_milligram_per_deciliter"), 1) == 77.3

        # Missing dataset falls back (and only then).
        monkeypatch.setattr(pp, "CBC", pp.DATA_DIR / "missing.csv")
        pp.inspiration4_baselines.cache_clear()
        assert pp.inspiration4_baselines()["glucose"] == -1
    finally:
        monkeypatch.undo()
        pp.inspiration4_baselines.cache_clear()


# ---- Hygieia I lunar flyby (fictional mission and crew), told day by day ----

def _demo():
    return client.get("/api/scenarios/hygieia-flyby").json()


def _assess_member(member, day):
    r = client.post("/api/assess", json={"passport": member["passport"], "history": member["history"][:day]})
    assert r.status_code == 200, r.text
    return r.json()


def _crew():
    return {m["passport"]["astronaut"]["id"]: m for m in _demo()["crew"]}


# Overall level of each crew member on each flight day (the story, plan table).
LEVELS = {
    "HY-CDR": "G G G O G G Y Y O G",
    "HY-PLT": "Y Y G O G G Y G G G",
    "HY-MS1": "G G G O R G Y G G G",
    "HY-MS2": "G G Y O G R Y G G R",
}
_LEVEL = {"G": "GREEN", "Y": "YELLOW", "O": "ORANGE", "R": "RED"}

# Morning and evening check-in answers every crew member has on every day.
CHECKIN_KEYS = {"sleep_hours", "sleep_quality", "kss", "physical_state", "hr_rest", "bp_sys", "bp_dia", "temp",
                "spo2", "pvt_rt", "mood_valence", "mood_labels", "team_cohesion", "workload", "fatigue",
                "exercise_min", "fluid_intake", "food_intake_pct"}


def test_demo_shape_and_ms2_top_level():
    sc = _demo()
    assert [m["passport"]["astronaut"]["id"] for m in sc["crew"]] == ["HY-CDR", "HY-PLT", "HY-MS1", "HY-MS2"]
    assert sc["passport"] == sc["crew"][3]["passport"] and sc["history"] == sc["crew"][3]["history"]
    assert all(len(m["history"]) == 10 for m in sc["crew"])
    assert all([d["mission_day"] for d in m["history"]] == list(range(1, 11)) for m in sc["crew"])
    assert "fictional" in sc["description"].lower() and "illustrative" in sc["description"].lower()


def test_demo_story_one_event_per_day():
    sc = _demo()
    story = sc["story"]
    assert [s["mission_day"] for s in story] == list(range(1, 11))
    ids = {m["passport"]["astronaut"]["id"] for m in sc["crew"]}
    for s in story:
        assert s["title"] and s["detail"] and s["crew"] and set(s["crew"]) <= ids
    assert "adaptation" in story[1]["title"].lower() and "solar" in story[3]["title"].lower()


def test_demo_level_matrix():
    crew = _crew()
    for cid, row in LEVELS.items():
        got = [_assess_member(crew[cid], d)["overall_level"] for d in range(1, 11)]
        assert got == [_LEVEL[c] for c in row.split()], (cid, got)


def test_demo_daily_checkins_filled_every_day():
    for m in _demo()["crew"]:
        for d in m["history"]:
            missing = CHECKIN_KEYS - set(d)
            assert not missing, (m["passport"]["astronaut"]["id"], d["mission_day"], missing)
            assert 1 <= d["sleep_quality"] <= 5 and 1 <= d["physical_state"] <= 7 and 1 <= d["fatigue"] <= 7
            assert 1 <= d["team_cohesion"] <= 5 and 1 <= d["mood_valence"] <= 7 and d["mood_labels"]
            assert "glucose" not in d and "lymphocytes_abs" not in d and "hemoglobin" not in d  # no blood drawn in flight


def test_demo_day2_space_adaptation_is_fixture_s4a():
    plt = _crew()["HY-PLT"]
    day = plt["history"][1]
    assert all(day.get(k) is True for k in ("sym_headache", "sym_nasal_congestion", "sym_nausea", "sym_back_pain"))
    a = _assess_member(plt, 2)
    assert _hyp(a, "C089")["level"] == "YELLOW" and _hyp(a, "C089")["cf"] == pytest.approx(0.95, abs=0.01)
    for cid in ("C053", "C069", "C022"):
        assert _hyp(a, cid)["level"] == "GREEN" and _hyp(a, cid)["expected"] is True
    assert _hyp(_assess_member(plt, 1), "C089")["cf"] == pytest.approx(0.95, abs=0.01)
    a = _assess_member(_crew()["HY-MS1"], 1)  # MS-1 headache + congestion: expected adaptation
    assert a["overall_level"] == "GREEN"


def test_demo_day4_solar_event_shelters_everyone():
    for m in _demo()["crew"]:
        day = m["history"][3]
        assert day["spe_alert"] is True and day["hours_since_spe"] == 2
        a = _assess_member(m, 4)
        assert any(e["rule"] == "R-RAD-01" and e["level"] == "ORANGE" for e in a["escalations"])
        assert m["history"][3]["dose_today"] > max(d["dose_today"] for d in m["history"][4:])


def test_demo_day5_possible_radiation_sickness_from_symptoms_only():
    crew = _crew()
    ms1 = crew["HY-MS1"]
    assert ms1["history"][4]["hours_since_spe"] <= 48
    a = _assess_member(ms1, 5)
    c011 = _hyp(a, "C011")
    assert c011["level"] == "RED" and c011["cf"] == pytest.approx(0.6, abs=0.01)
    assert a["next_measurement"]["fact"] == "lymphocytes_abs" and a["packet"]
    # Elena's nausea on day 6 is 50 h after the flare: a kidney stone, not radiation sickness
    a6 = _assess_member(crew["HY-MS2"], 6)
    assert crew["HY-MS2"]["history"][5]["hours_since_spe"] > 48 and _hyp(a6, "C011") is None


def test_demo_ms2_red_on_flyby():
    ms2 = _demo()["crew"][3]
    a = _assess_member(ms2, 6)
    assert a["overall_level"] == "RED"
    assert _hyp(a, "C070")["level"] == "RED"
    assert "QUEUED" in a["packet"]


def test_demo_other_crew_green_on_flyby():
    for m in _demo()["crew"][:3]:
        assert m["history"][5]["comm_los"] is True
        assert _assess_member(m, 6)["overall_level"] == "GREEN"


def test_demo_ms2_hydration_day3_and_day7():
    ms2 = _demo()["crew"][3]
    a3 = _assess_member(ms2, 3)
    assert a3["overall_level"] == "YELLOW" and _hyp(a3, "X08")["level"] == "YELLOW"
    assert _hyp(_assess_member(ms2, 7), "X08")["level"] == "YELLOW"
    assert _hyp(_assess_member(ms2, 8), "X08") is None


def test_demo_day7_cabin_co2_spike():
    crew = _crew()
    assert all(m["history"][6]["co2_1h"] == 3.4 for m in crew.values())
    assert all(d["co2_1h"] < 3.0 for m in crew.values() for i, d in enumerate(m["history"]) if i != 6)
    a = _assess_member(crew["HY-PLT"], 7)
    c051 = _hyp(a, "C051")
    assert c051["level"] == "YELLOW" and "R-NEU-01" in {t["rule"] for t in c051["trace"]}


def test_demo_days8_9_commander_sleep_debt_is_fixture_s1():
    cdr = _crew()["HY-CDR"]
    assert [d["sleep_hours"] for d in cdr["history"][4:9]] == [7.2, 5.5, 5.2, 5.8, 5.4]
    assert [d["workload"] for d in cdr["history"][4:9]] == [5, 6, 8, 9, 8]
    a8 = _assess_member(cdr, 8)
    assert _hyp(a8, "X01")["level"] == "YELLOW" and _hyp(a8, "X02") is None
    a9 = _assess_member(cdr, 9)
    x02 = _hyp(a9, "X02")
    assert x02["level"] == "ORANGE" and x02["cf"] == pytest.approx(0.95, abs=0.01)
    assert {t["rule"] for t in x02["trace"]} == {"R-SLP-04", "R-SLP-05", "R-SLP-08"}


def test_demo_passports():
    crew = _demo()["crew"]
    assert [m["passport"]["modifiers"] for m in crew] == [[], ["P-01"], ["P-05", "P-10"], ["P-02", "P-15"]]
    assert [m["passport"]["astronaut"]["sex"] for m in crew] == ["M", "M", "M", "F"]
    # baselines come from each member's six-month passport (real donors), not hand-typed constants
    from app.data import passport_baselines
    for m in crew:
        cid = m["passport"]["astronaut"]["id"]
        assert m["passport"]["baselines"]["hr_rest"] == passport_baselines(cid)["baselines"]["hr_rest"]
        assert m["passport"]["passport_ref"] == cid and m["passport"]["personal_ranges"]["hr_rest"]["ready"]
    assert crew[3]["passport"]["lab_ranges"]["hemoglobin"] == {"lo": 11.7, "hi": 15.5}  # I4-C002 lab range


def test_demo_plausibility_dose_co2_sleep():
    days = [m["history"] for m in _demo()["crew"]]
    for h in days:
        assert 8 <= h[9]["dose_cumulative"] <= 14
        assert abs(sum(d["dose_today"] for d in h) - h[9]["dose_cumulative"]) < 0.15
        assert h[1]["dose_today"] > h[0]["dose_today"] > h[2]["dose_today"]
        assert all(1.5 <= d["co2_7d"] <= 2.5 for d in h)
        assert all(5.0 <= d["sleep_hours"] <= 6.6 for d in h[:2])
        assert all(5.0 <= d["sleep_hours"] <= 7.6 for d in h)
    # one cabin: environment and dose are the same for the whole crew
    for k in ("co2_1h", "co2_7d", "dose_today", "dose_cumulative"):
        assert all(len({h[i][k] for h in days}) == 1 for i in range(10)), k


def test_demo_landing_orthostatic():
    crew = _demo()["crew"]
    a = _assess_member(crew[3], 10)
    assert _hyp(a, "X03")["level"] == "ORANGE"  # R-CV-06; overall is RED because NEWS2 bp_sys<=90 scores 3
    assert all(m["history"][9]["phase"] == "landing" for m in crew)
    for m in crew[:3]:
        assert _assess_member(m, 10)["overall_level"] in ("GREEN", "YELLOW")


def test_demo_has_no_real_names():
    """The demo flight and crew are fictional: no real astronauts and no real mission or spacecraft names in
    anything the demo shows about itself (data-source citations are not part of this)."""
    import re
    sc = _demo()
    shown = [sc["title"], sc["description"], *(f"{s['title']} {s['detail']}" for s in sc["story"])]
    for m in sc["crew"]:
        a, mission = m["passport"]["astronaut"], m["passport"]["mission"]
        shown += [a["id"], a["name"], a["role"], mission["profile"], mission["vehicle"]]
    blob = " ".join(shown).lower()
    for real in ("wiseman", "glover", "koch", "hansen", "ortega"):
        assert real not in blob
    for real in (r"artemis", r"orion", r"apollo", r"gateway", r"inspiration4", r"\biss\b", r"\ba2-"):
        assert not re.search(real, blob), real


def test_comm_los_must_be_bool():
    sc = _demo()
    h = [dict(sc["history"][0], comm_los="yes")]
    assert client.post("/api/assess", json={"passport": sc["passport"], "history": h}).status_code == 422


@pytest.mark.parametrize("bad", ["NaN", "Infinity", "-Infinity"])
def test_nan_inf_rejected_as_422(bad):
    sc = client.get("/api/scenarios/hygieia-flyby").json()
    body = '{"passport": %s, "history": [{"mission_day": 2, "temp": %s}]}' % (
        __import__("json").dumps(sc["passport"]), bad)
    r = client.post("/api/assess", content=body, headers={"content-type": "application/json"})
    assert r.status_code == 422
    r = client.post("/api/passport/derive", content='{"answers": {"baselines": {"hr_rest": %s}}}' % bad,
                    headers={"content-type": "application/json"})
    assert r.status_code == 422
    sc["passport"]["baselines"]["hr_rest"] = 60
    body = __import__("json").dumps(sc["passport"]).replace('"hr_rest": 60', '"hr_rest": %s' % bad)
    r = client.post("/api/assess", content='{"passport": %s, "history": [{"mission_day": 2}]}' % body,
                    headers={"content-type": "application/json"})
    assert r.status_code == 422


def test_derive_keeps_given_id():
    r = client.post("/api/passport/derive", json={"answers": {"id": "CM-2", "name": "B"}})
    assert r.json()["astronaut"]["id"] == "CM-2"


# --- Task 10: pre-flight data-collection timeline in the passport ------------------------------
_PREFLIGHT_KEYS = {"id", "when", "what", "how", "feeds", "source"}


def _check_preflight(pf):
    assert isinstance(pf, list) and 15 <= len(pf) <= 22
    assert all(set(s) == _PREFLIGHT_KEYS for s in pf)
    assert all(s["feeds"] and all(isinstance(f, str) for f in s["feeds"]) for s in pf)
    assert len({s["id"] for s in pf}) == len(pf)
    whens = [s["when"] for s in pf]
    assert any(w.startswith("L-270") for w in whens) and any(w.startswith("L-90") for w in whens)
    assert any(w.startswith("L-14") for w in whens)
    assert any(s["id"] == "actigraphy" and s["when"].startswith("L-270") for s in pf)
    assert any(s["id"] == "cognition" and "L-90" in s["when"] for s in pf)
    assert any(s["id"] == "biochem" and s["when"].startswith("L-180") for s in pf)
    assert any(s["id"] == "hsp" and s["source"] == "HSP-A2" for s in pf)


def test_derive_passport_has_preflight_copy():
    p = client.post("/api/passport/derive", json={"answers": {}}).json()
    _check_preflight(p["preflight"])
    from app.passport import PREFLIGHT_TIMELINE
    assert p["preflight"] == PREFLIGHT_TIMELINE


def test_preflight_is_a_copy_not_the_template():
    from app.passport import PREFLIGHT_TIMELINE, derive_passport
    p = derive_passport({})
    p["preflight"][0]["what"] = "mutated"
    p["preflight"][0]["feeds"].append("x")
    assert PREFLIGHT_TIMELINE[0]["what"] != "mutated" and "x" not in PREFLIGHT_TIMELINE[0]["feeds"]


def test_every_scenario_passport_has_preflight():
    sc = client.get("/api/scenarios/hygieia-flyby").json()
    _check_preflight(sc["passport"]["preflight"])
    for m in sc.get("crew") or []:
        _check_preflight(m["passport"]["preflight"])


def test_assess_accepts_passport_with_preflight_and_rejects_bad_entries():
    sc = client.get("/api/scenarios/hygieia-flyby").json()
    assert "preflight" in sc["passport"]
    r = client.post("/api/assess", json={"passport": sc["passport"], "history": sc["history"]})
    assert r.status_code == 200, r.text
    bad = dict(sc["passport"], preflight=[{"id": "x", "when": "L-1"}])
    assert client.post("/api/assess", json={"passport": bad, "history": sc["history"]}).status_code == 422
    extra = dict(sc["passport"], preflight=[dict(sc["passport"]["preflight"][0], junk=1)])
    assert client.post("/api/assess", json={"passport": extra, "history": sc["history"]}).status_code == 422


# --- My crew mode: registering new crew members, keeping a member's own passport on edit ----------
def test_scenarios_list_starts_with_demo_crew():
    assert client.get("/api/scenarios").json()[0]["id"] == "hygieia-flyby"


def test_derive_new_member_has_no_six_month_passport():
    from app.passport import population_baselines
    p = client.post("/api/passport/derive", json={"answers": {
        "new_member": True, "id": "MY-1", "name": "Anna K", "kidney_stone": True}}).json()
    assert p["astronaut"] == {"id": "MY-1", "name": "Anna K", "role": "Mission Specialist"}
    assert p["passport_ref"] is None and p["personal_ranges"] == {} and p["lab_ranges"] == {}
    assert p["baselines"] == population_baselines()
    assert "Population defaults" in p["baselines_source"] and "7 days" in p["baselines_source"]
    assert p["modifiers"] == ["P-02"]
    # the derived passport is accepted by the engine with a first-day record
    r = client.post("/api/assess", json={"passport": p, "history": [{"mission_day": 1, "temp": 38.6, "hr_rest": 112}]})
    assert r.status_code == 200, r.text


def test_derive_with_passport_ref_keeps_that_members_passport():
    from app.data import passport_baselines
    p = client.post("/api/passport/derive", json={"answers": {"passport_ref": "HY-MS2", "name": "Elena"}}).json()
    own = passport_baselines("HY-MS2")
    assert p["passport_ref"] == "HY-MS2"
    assert p["personal_ranges"] == own["personal_ranges"] and p["lab_ranges"] == own["lab_ranges"]
    assert p["baselines"]["hr_rest"] == own["baselines"]["hr_rest"]


def test_derive_with_unknown_passport_ref_falls_back_to_population():
    p = client.post("/api/passport/derive", json={"answers": {"passport_ref": "NOPE"}}).json()
    assert p["passport_ref"] is None and p["personal_ranges"] == {}


@pytest.mark.parametrize("answers", [{"new_member": "yes"}, {"passport_ref": "x" * 51}])
def test_derive_rejects_bad_new_member_fields(answers):
    assert client.post("/api/passport/derive", json={"answers": answers}).status_code == 422
