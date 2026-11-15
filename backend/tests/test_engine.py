"""Engine acceptance tests. Inputs and expected values come from knowledge-base/09-worked-examples.md."""
import pytest

from app.engine import MODIFIER_RULES, assess, evaluate
from app.kb import load_kb
from app.packet import build_packet

CF_TOL = 0.01
ASSESSMENT_KEYS = {
    "overall_level", "systems", "hypotheses", "escalations", "pending",
    "next_measurement", "news2", "packet",
}

# Rule IDs the Task 3 brief requires (05-rules.md).
BRIEF_RULE_IDS = [
    f"R-{x}" for x in (
        "SLP-01 SLP-02 SLP-04 SLP-05 SLP-07 SLP-08 SLP-09 SLP-10 "
        "BEH-01 BEH-02 BEH-04 BEH-06 BEH-07 BEH-09 BEH-10 BEH-12 "
        "NEU-01 NEU-02 NEU-03 NEU-04 NEU-05 NEU-07 NEU-08 NEU-12 NEU-13 "
        "EYE-01 EYE-02 EYE-03 EYE-05 EYE-09 EYE-12 "
        "ENT-01 ENT-03 ENT-05 ENT-09 "
        "CV-01 CV-02 CV-03 CV-04 CV-06 CV-08 CV-09 CV-10 CV-13 "
        "RES-01 RES-02 RES-03 RES-05 RES-06 "
        "VES-01 VES-02 "
        "GI-01 GI-02 GI-05 GI-07 "
        "GU-01 GU-04 GU-11 "
        "MSK-01 MSK-22 MSK-26 "
        "SKN-01 SKN-02 SKN-04 "
        "IMM-01 IMM-02 IMM-04 "
        "NUT-01 NUT-02 NUT-06 NUT-07 "
        "RAD-01 RAD-02 RAD-05 RAD-06 "
        "ENV-01 ENV-02 ENV-05 "
        "EVA-01"
    ).split()
]
SYSTEMS = set("SLEEP BEHAV NEURO EYE ENT DENT CV RESP VEST GI GU MSK SKIN IMMUNE NUTR RAD ENV EVA".split())
LEVELS = {"GREEN", "YELLOW", "ORANGE", "RED"}
OPS = {"eq", "ne", "gt", "gte", "lt", "lte", "between", "in", "true"}


def passport(modifiers=(), delay=760, profile="Mars transit"):
    return {
        "astronaut": {"id": "A2", "name": "Test Crew", "role": "CM-2"},
        "mission": {"profile": profile, "comm_delay_s": delay},
        "baselines": {"hr_rest": 58, "pvt_rt": 262, "body_mass": 75, "sleep_hours": 7.5,
                      "lymphocytes_abs": 2000},
        "modifiers": list(modifiers),
        "countermeasures": [],
    }


def hyp(assessment, cid):
    return next((h for h in assessment["hypotheses"] if h["id"] == cid), None)


# --- Scenario inputs (09-worked-examples) -------------------------------------------------

def scenario1_history():
    """Sleep < 6 h for the last 4 nights, workload >= 8 on the last 3 evenings, PVT 312 ms, KSS 7, mood 3."""
    sleep = [7.2, 5.5, 5.2, 5.8, 5.4]
    workload = [5, 6, 8, 9, 8]
    hist = [{"mission_day": 43 + i, "sleep_hours": s, "workload": w}
            for i, (s, w) in enumerate(zip(sleep, workload))]
    hist[-1].update({"pvt_rt": 312, "kss": 7, "mood_valence": 3})
    return hist


def scenario2_day(**extra):
    """Headache + near blur on day 47, CO2 3.4 / 2.7 mmHg, near-acuity not measured.

    The routine AM blood pressure is included: without it, R-NEU-13 (headache + BP crisis, RED)
    is pending and the BP cuff would outrank the eye test as next measurement.
    """
    day = {"mission_day": 47, "sym_headache": True, "sym_blurred_near_vision": True,
           "co2_1h": 3.4, "co2_7d": 2.7, "bp_sys": 118, "bp_dia": 76}
    day.update(extra)
    return day


def scenario3_day():
    """T0 + 20 h after an SPE: nausea + fatigue, lymphocytes 55% below the passport baseline."""
    return {"mission_day": 112, "hours_since_spe": 20, "sym_nausea": True, "sym_fatigue": True,
            "lymphocytes_abs": 900, "hr_rest": 96, "bp_sys": 118, "bp_dia": 76, "spo2": 98,
            "temp": 37.4, "dose_cumulative": 109}


def scenario4_day(**extra):
    """Day 2: headache, nasal congestion, nausea, back pain, no fever (temperature measured)."""
    day = {"mission_day": 2, "sym_headache": True, "sym_nasal_congestion": True,
           "sym_nausea": True, "sym_back_pain": True, "temp": 36.8}
    day.update(extra)
    return day


# --- Evaluator ------------------------------------------------------------------------------

def test_evaluate_tristate():
    facts = {"a": 5, "flag": True, "off": False, "phase": "landing", "labels": ["anxious"]}
    t = {"fact": "a", "op": "gt", "value": 3}
    f = {"fact": "a", "op": "lt", "value": 3}
    u = {"fact": "missing", "op": "gt", "value": 3}
    assert evaluate(t, facts) is True and evaluate(f, facts) is False and evaluate(u, facts) is None
    assert evaluate({"all": [t, u]}, facts) is None
    assert evaluate({"all": [f, u]}, facts) is False
    assert evaluate({"all": [t, t]}, facts) is True
    assert evaluate({"any": [f, u]}, facts) is None
    assert evaluate({"any": [t, u]}, facts) is True
    assert evaluate({"any": [f, f]}, facts) is False
    assert evaluate({"not": t}, facts) is False
    assert evaluate({"not": u}, facts) is None
    assert evaluate({"fact": "a", "op": "between", "value": [5, 6]}, facts) is True
    assert evaluate({"fact": "phase", "op": "in", "value": ["landing", "post-landing"]}, facts) is True
    assert evaluate({"fact": "labels", "op": "in", "value": ["anxious", "overwhelmed"]}, facts) is True
    assert evaluate({"fact": "flag", "op": "true"}, facts) is True
    assert evaluate({"fact": "off", "op": "true"}, facts) is False
    assert evaluate({"fact": "missing", "op": "true"}, facts) is None
    assert evaluate({"fact": "a", "op": "eq", "value": 5}, facts) is True
    assert evaluate({"fact": "a", "op": "ne", "value": 5}, facts) is False


# --- Acceptance scenarios -----------------------------------------------------------------

def test_scenario1_fatigue():
    a = assess(passport(), scenario1_history())
    assert set(a) == ASSESSMENT_KEYS
    x02, x01 = hyp(a, "X02"), hyp(a, "X01")
    assert x02["cf"] == pytest.approx(0.95, abs=CF_TOL) and x02["level"] == "ORANGE"
    assert x01["cf"] == pytest.approx(0.80, abs=CF_TOL) and x01["level"] == "YELLOW"
    assert {t["rule"] for t in x02["trace"]} == {"R-SLP-04", "R-SLP-05", "R-SLP-08"}
    assert hyp(a, "C038") is None  # R-BEH-10 not fired: mood 3 > 2
    assert a["overall_level"] == "ORANGE" and a["systems"]["SLEEP"] == "ORANGE"
    assert a["hypotheses"][0]["id"] == "X02"  # sorted by level, then CF
    assert a["packet"] is None
    step = x02["trace"][0]
    assert set(step) == {"rule", "label", "facts", "cf", "source"}
    assert set(step["source"]) == {"key", "title", "url"}
    assert {"A-GEN-08", "A-SLP-04", "A-GEN-02"} <= {act["id"] for act in x02["actions"]}
    assert set(a["news2"]) == {"total", "params", "max", "missing"}


def test_chaining_needs_sleep_deficit():
    """R-SLP-05 uses X01: a slow PVT alone (good sleep) does not fire it."""
    hist = [{"mission_day": 47, "sleep_hours": 7.5, "pvt_rt": 312}]
    a = assess(passport(), hist)
    assert hyp(a, "X02") is None and hyp(a, "X01") is None


def test_scenario2_co2_and_sans():
    pp = passport(modifiers=["P-03"])
    before = assess(pp, [scenario2_day()])
    c051, c098 = hyp(before, "C051"), hyp(before, "C098")
    assert c051["cf"] == pytest.approx(0.90, abs=CF_TOL) and c051["level"] == "YELLOW"
    assert c051["system"] == "ENV"
    assert c098["cf"] == pytest.approx(0.70, abs=CF_TOL) and c098["level"] == "ORANGE"
    eye01 = next(t for t in c098["trace"] if t["rule"] == "R-EYE-01")
    assert eye01["cf"] == pytest.approx(0.70, abs=CF_TOL)
    assert "P-03" in eye01["label"] and "R-EYE-03" in eye01["label"]
    assert before["next_measurement"]["fact"] == "near_acuity_decline"

    after = assess(pp, [scenario2_day(near_acuity_decline=1)])
    c098 = hyp(after, "C098")
    assert c098["cf"] == pytest.approx(0.85, abs=CF_TOL) and c098["level"] == "ORANGE"
    assert hyp(after, "C051")["cf"] == pytest.approx(0.90, abs=CF_TOL)
    assert after["overall_level"] == "ORANGE"


def test_scenario3_ars():
    a = assess(passport(delay=760), [scenario3_day()])
    c011 = hyp(a, "C011")
    assert c011["cf"] == pytest.approx(0.94, abs=CF_TOL) and c011["level"] == "RED"
    assert [t["rule"] for t in c011["trace"]] == ["R-RAD-05", "R-RAD-06"]
    assert a["overall_level"] == "RED" and a["systems"]["RAD"] == "RED"
    assert a["news2"]["total"] == 1
    assert isinstance(a["packet"], str) and "Acute radiation syndrome" in a["packet"]


def test_scenario4_reassure():
    a = assess(passport(modifiers=["P-01"], delay=2, profile="Low Earth orbit"), [scenario4_day()])
    for cid in ("C053", "C069", "C022"):
        h = hyp(a, cid)
        assert h is not None, cid
        assert h["level"] == "GREEN" and h["expected"] is True
        assert h["cf"] == pytest.approx(0.70, abs=CF_TOL)
    c089 = hyp(a, "C089")
    assert c089["cf"] == pytest.approx(0.95, abs=CF_TOL) and c089["level"] == "YELLOW"
    assert c089["expected"] is False
    assert "P-01" in c089["trace"][0]["label"] and "R-VES-02" in c089["trace"][0]["label"]
    assert a["overall_level"] == "YELLOW"


def test_guard_blocks_expected_on_red_flag():
    day = scenario4_day(sym_headache_red_flag=True, sym_vomiting=True)
    a = assess(passport(modifiers=["P-01"], delay=2, profile="Low Earth orbit"), [day])
    assert a["overall_level"] == "RED"
    assert hyp(a, "C053") is None  # R-NEU-03 blocked: red flag in NEURO
    neu05 = next(e for e in a["escalations"] if e["rule"] == "R-NEU-05")
    assert neu05["level"] == "RED" and neu05["system"] == "NEURO"
    assert "A-NEU-01" in {x["id"] for x in neu05["actions"]}  # BE-FAST
    assert a["systems"]["NEURO"] == "RED"
    assert hyp(a, "C069") is not None and hyp(a, "C022") is not None  # other systems unaffected
    assert a["packet"] is not None


def test_missing_data_is_pending():
    pp = passport()  # no P-03
    a = assess(pp, [scenario2_day(co2_1h=None, co2_7d=None)])
    assert hyp(a, "C098")["cf"] == pytest.approx(0.60, abs=CF_TOL)
    assert {"rule": "R-EYE-02", "missing": ["near_acuity_decline"]} in a["pending"]
    nm = a["next_measurement"]
    assert nm["fact"] == "near_acuity_decline"
    assert nm["label"] == "Near-vision test (each eye)"
    assert nm["reason"] == "VIIP / SANS"
    assert any(p["rule"] == "R-NEU-01" and p["missing"] == ["co2_1h"] for p in a["pending"])

    # Without the routine BP, the RED headache + BP-crisis rule is pending and asks for BP.
    no_bp = scenario2_day(co2_1h=None, co2_7d=None, bp_sys=None, bp_dia=None)
    b = assess(pp, [no_bp])
    assert any(p["rule"] == "R-NEU-13" and "bp_sys" in p["missing"] for p in b["pending"])


def test_packet_onboard_first_on_long_delay():
    long_ = assess(passport(delay=760), [scenario3_day()])["packet"]
    lines = long_.splitlines()
    assert "min" in lines[0]
    assert "ONBOARD FIRST:" in long_
    assert long_.index("ONBOARD FIRST:") < long_.index("REQUEST:")
    onboard = long_[long_.index("ONBOARD FIRST:"):long_.index("REQUEST:")]
    assert "A-RAD-04" in onboard and "A-GEN-03" not in onboard  # ground (🌍) action not onboard
    assert lines[1].startswith("STATUS: RED") and "94%" in lines[1]
    assert any(line.startswith("RULES:") and "R-RAD-05" in line and "R-RAD-06" in line for line in lines)
    assert any(line.startswith("VITALS") and "HR 96" in line for line in lines)

    short = assess(passport(delay=2), [scenario3_day()])["packet"]
    assert "ONBOARD FIRST:" not in short
    assert short.index("REQUEST:") < short.index("ONBOARD ACTIONS:")


def test_build_packet_direct_uses_day_delay():
    a = assess(passport(delay=2), [scenario3_day()])
    text = build_packet(a, passport(delay=2), dict(scenario3_day(), comm_delay_s=900))
    assert "ONBOARD FIRST:" in text and "15.0 min" in text.splitlines()[0]


def test_red_escalation_has_actions_in_assessment_and_packet():
    a = assess(passport(delay=760), [{"mission_day": 50, "spo2": 90}])
    res01 = next(e for e in a["escalations"] if e["rule"] == "R-RES-01")
    assert set(res01) == {"rule", "label", "level", "system", "actions"}
    assert res01["level"] == "RED"
    assert [x["id"] for x in res01["actions"]] == ["A-RESP-01", "A-RESP-02", "A-GEN-02"]
    assert set(res01["actions"][0]) == {"id", "text", "who"}
    onboard = a["packet"][a["packet"].index("ONBOARD FIRST:"):a["packet"].index("REQUEST:")]
    assert "A-RESP-01" in onboard and "A-RESP-02" in onboard
    assert onboard.count("A-GEN-02") == 1  # also listed by R-CV-01 (NEWS2 3): deduplicated
    assert "A-GEN-03" not in onboard  # ground action

    short = assess(passport(delay=2), [{"mission_day": 50, "spo2": 90}])["packet"]
    assert "A-RESP-01" in short[short.index("ONBOARD ACTIONS:"):]


def test_kidney_stone_history_raises_flank_pain_to_red():
    day = {"mission_day": 60, "sym_flank_pain": True}
    with_p02 = hyp(assess(passport(modifiers=["P-02"]), [day]), "C070")
    assert with_p02["level"] == "RED" and with_p02["cf"] == pytest.approx(0.70, abs=CF_TOL)
    assert [t["rule"] for t in with_p02["trace"]] == ["R-GU-04P"]
    assert "A-GEN-03" in {x["id"] for x in with_p02["actions"]}
    without = hyp(assess(passport(), [day]), "C070")
    assert without["level"] == "ORANGE" and without["cf"] == pytest.approx(0.70, abs=CF_TOL)
    assert [t["rule"] for t in without["trace"]] == ["R-GU-04"]


def test_sepsis_rule_pending_when_bp_not_measured():
    """qSOFA '2 of 3' must not treat an unmeasured BP as normal (review finding, R-IMM-04)."""
    day = {"mission_day": 60, "sym_cough": True, "temp": 38.6, "resp_rate": 24}
    a = assess(passport(), [day])
    assert hyp(a, "C077")["level"] == "RED"
    assert hyp(a, "C080") is None
    assert {"rule": "R-IMM-04", "missing": ["bp_sys"]} in a["pending"]
    # the fired RED finding's own confirmation (SpO2) outranks the pending qSOFA check, which stays listed
    assert a["next_measurement"]["fact"] == "spo2"

    b = assess(passport(), [dict(day, bp_sys=98)])
    c080 = hyp(b, "C080")
    assert c080["level"] == "RED" and c080["cf"] == pytest.approx(0.85, abs=CF_TOL)
    assert [t["rule"] for t in c080["trace"]] == ["R-IMM-04"]


def test_empty_history_is_green_without_crash():
    a = assess(passport(), [])
    assert a["overall_level"] == "GREEN" and a["hypotheses"] == [] and a["packet"] is None
    assert a["next_measurement"] is None


# --- Knowledge integrity ------------------------------------------------------------------

def _walk(cond):
    if "all" in cond or "any" in cond:
        children = cond.get("all", cond.get("any"))
        assert isinstance(children, list) and children
        for c in children:
            yield from _walk(c)
    elif "not" in cond:
        yield from _walk(cond["not"])
    else:
        yield cond


def test_rules_reference_integrity():
    kb = load_kb()
    ids = [r["id"] for r in kb.rules]
    assert len(ids) == len(set(ids)), "duplicate rule IDs"
    present = set(ids) | set(MODIFIER_RULES.values())
    assert not set(BRIEF_RULE_IDS) - present, sorted(set(BRIEF_RULE_IDS) - present)
    assert "R-GU-04P" in ids  # controller addition: P-02 kidney-stone personalisation
    for r in kb.rules:
        rid = r["id"]
        assert r["system"] in SYSTEMS, rid
        assert r.get("label"), rid
        then = r["then"]
        assert ("hypothesis" in then) != ("escalation" in then), rid
        if "hypothesis" in then:
            assert then["hypothesis"] in kb.conditions, rid
        assert then["level"] in LEVELS, rid
        assert 0 < then["cf"] <= 1, rid
        assert r["refs"] and all(k in kb.references for k in r["refs"]), rid
        assert all(a in kb.actions for a in r.get("actions", [])), rid
        for mod, bonus in (r.get("modifiers") or {}).items():
            assert mod.startswith("P-") and 0 < bonus < 0.5, rid
        if r.get("expected"):
            assert then["level"] == "GREEN", rid
        for leaf in _walk(r["when"]):
            assert leaf["op"] in OPS, (rid, leaf)
            assert isinstance(leaf["fact"], str), rid
            if leaf["op"] in ("between", "in"):
                assert isinstance(leaf["value"], list), (rid, leaf)
            if leaf["fact"].startswith("hyp_"):
                assert leaf["fact"][4:] in kb.conditions, (rid, leaf)


def test_packet_queued_on_los():
    from app.packet import build_packet
    a = {"overall_level": "RED", "hypotheses": [{"id": "C070", "name": "Renal colic", "level": "RED", "cf": 0.7,
         "trace": [{"rule": "R-GU-04P", "source": {"key": "TB030"}}], "actions": []}],
         "escalations": [], "news2": {"total": 0, "missing": []}}
    passport = {"astronaut": {"role": "Mission Specialist 2"}, "mission": {"comm_delay_s": 1.3}}
    p = build_packet(a, passport, {"mission_day": 6, "comm_los": True})
    assert "QUEUED - no link (far-side loss of signal); sends at acquisition of signal" in p.splitlines()[0]
    assert p.index("ONBOARD FIRST") < p.index("REQUEST")
    q = build_packet(a, passport, {"mission_day": 6})
    assert "QUEUED" not in q and q.index("REQUEST") < q.index("ONBOARD ACTIONS")


# --- C1: fever must never be silent or "expected" -------------------------------------------

def _esc(a, rule):
    return next((e for e in a["escalations"] if e["rule"] == rule), None)


def test_fever_alone_is_orange_escalation():
    a = assess(passport(), [{"mission_day": 30, "temp": 40.0}])
    assert a["overall_level"] in ("ORANGE", "RED")
    assert _esc(a, "R-IMM-06") and _esc(a, "R-IMM-07")
    assert a["systems"]["IMMUNE"] == "ORANGE"


def test_fever_chip_alone_is_orange():
    a = assess(passport(), [{"mission_day": 30, "sym_fever_chills": True}])
    assert _esc(a, "R-IMM-06") and a["overall_level"] == "ORANGE"


def test_day_two_headache_with_fever_is_not_expected_adaptation():
    for extra in ({"temp": 39.6}, {"sym_fever_chills": True}):
        a = assess(passport(), [{"mission_day": 2, "sym_headache": True, **extra}])
        assert hyp(a, "C053") is None
        assert a["overall_level"] == "ORANGE"


def test_back_pain_with_fever_early_is_red_escalation():
    a = assess(passport(), [{"mission_day": 5, "sym_back_pain": True, "temp": 38.5}])
    assert _esc(a, "R-MSK-02")["level"] == "RED"
    assert a["overall_level"] == "RED"
    assert hyp(a, "C022") is None


def test_normal_temp_stays_green():
    a = assess(passport(), [{"mission_day": 30, "temp": 36.8}])
    assert a["overall_level"] == "GREEN" and not a["escalations"]


def test_next_measurement_not_from_unrelated_system_under_red():
    from app.scenarios import get_scenario
    ms1 = get_scenario("hygieia-flyby")["crew"][2]  # day 5: possible radiation sickness after the flare
    a = assess(ms1["passport"], ms1["history"][:5])
    assert a["overall_level"] == "RED"
    nm = a["next_measurement"]
    assert nm is None or nm["fact"] != "cabin_temp"


def test_time_since_solar_event_is_never_a_measurement():
    """Nausea before any solar event leaves R-RAD-05 waiting, but 'hours since SPE' is context, not a test."""
    a = assess(passport(), [{"mission_day": 1, "sym_nausea": True}])
    assert any(p["rule"] == "R-RAD-05" for p in a["pending"])
    assert a["next_measurement"] is None or a["next_measurement"]["fact"] != "hours_since_spe"


def test_next_measurement_never_a_context_fact():
    a = assess(passport(), [{"mission_day": 5, "sym_back_pain": True}])
    nm = a["next_measurement"]
    assert nm and nm["fact"] == "temp"


def test_pending_excludes_green_rules():
    from app.kb import load_kb
    kb = load_kb()
    green = {r["id"] for r in kb.rules if r["then"]["level"] == "GREEN"}
    a = assess(passport(), [scenario4_day() | {"temp": None}])
    assert not green & {p["rule"] for p in a["pending"]}
