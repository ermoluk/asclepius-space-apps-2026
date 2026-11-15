import pytest

from app.facts import build_facts
from app.news2 import news2

PASSPORT = {
    "astronaut": {"id": "A1"},
    "mission": {"profile": "Low Earth orbit", "comm_delay_s": 2},
    "baselines": {"hr_rest": 60, "pvt_rt": 262, "body_mass": 75, "sleep_hours": 7.5},
    "modifiers": ["P-01", "P-07"],
    "countermeasures": [],
}


def days(key, values, start=1):
    return [{"mission_day": start + i, key: v} for i, v in enumerate(values)]


def test_news2_bands():
    assert news2({"hr_rest": 135})["params"]["hr_rest"] == 3
    assert news2({"spo2": 92})["params"]["spo2"] == 2
    assert news2({"temp": 38.5})["params"]["temp"] == 1
    assert news2({"bp_sys": 95})["params"]["bp_sys"] == 2
    assert news2({"resp_rate": 22})["params"]["resp_rate"] == 2


def test_news2_total_max_missing_and_flags():
    r = news2({"hr_rest": 135, "on_oxygen": True, "confusion": True})
    assert r["params"]["on_oxygen"] == 2 and r["params"]["confusion"] == 3
    assert r["total"] == 8 and r["max"] == 3
    assert set(r["missing"]) == {"resp_rate", "spo2", "bp_sys", "temp"}
    assert news2({})["total"] == 0


def test_days_sleep_lt6():
    f = build_facts(PASSPORT, days("sleep_hours", [7, 5.5, 5.2, 5.8, 5.4]))
    assert f["days_sleep_lt6"] == 4


def test_days_sleep_le6_counts_exactly_six_hours():
    f = build_facts(PASSPORT, days("sleep_hours", [7, 6.0, 6.0, 6.0]))
    assert f["days_sleep_le6"] == 3 and f["days_sleep_lt6"] == 0


def test_streak_breaks_on_missing_value():
    h = days("sleep_hours", [5, 5, 5])
    h[1] = {"mission_day": 2}
    assert build_facts(PASSPORT, h)["days_sleep_lt6"] == 1


def test_pvt_delta():
    f = build_facts(PASSPORT, [{"mission_day": 1, "pvt_rt": 312}])
    assert f["delta_pct_pvt_rt"] == pytest.approx(0.19, abs=0.005)


def test_baseline_median_of_prior_days():
    h = days("hr_rest", [50, 52, 54, 56, 58, 60, 62, 100])
    f = build_facts(PASSPORT, h)
    assert f["baseline_hr_rest"] == 56  # median of 7 prior, current excluded
    assert f["baseline_pvt_rt"] == 262  # untouched passport value
    h2 = h[2:]  # only 5 prior values -> passport
    assert build_facts(PASSPORT, h2)["baseline_hr_rest"] == 60


def test_days_hr_gt15():
    f = build_facts(PASSPORT, days("hr_rest", [60, 70, 71, 72]))
    assert f["days_hr_gt15"] == 3


def test_other_streaks():
    h = [
        {"mission_day": i + 1, "glucose_fasting": 130, "fluid_intake": 2.0, "food_intake_pct": 70}
        for i in range(3)
    ]
    f = build_facts(PASSPORT, h)
    assert f["days_fasting_glu_ge126"] == 3
    assert f["days_fluid_lt25"] == 3
    assert f["days_intake_lt80"] == 3


def test_count7_and_labels():
    h = [
        {"mission_day": i, "mood_valence": 2, "sleep_quality": 3, "workload": 8,
         "exercise_min": 100, "team_cohesion": 2, "mood_labels": ["anxious"]}
        for i in range(1, 11)
    ]
    f = build_facts(PASSPORT, h)
    assert f["count7_mood_le2"] == 7
    assert f["count7_quality_le2"] == 0
    assert f["count7_workload_ge8"] == 7
    assert f["count7_exercise_lt90"] == 0
    assert f["count7_cohesion_le2"] == 7
    assert f["count7_label_anxious"] == 7


def test_facts_without_history_use_passport():
    f = build_facts(PASSPORT, [])
    assert f["baseline_hr_rest"] == 60
    assert f["mod_P-01"] is True and f["mod_P-07"] is True
    assert f["comm_delay_s"] == 2


def test_comm_delay_current_day_wins():
    f = build_facts(PASSPORT, [{"mission_day": 5, "comm_delay_s": 20}])
    assert f["comm_delay_s"] == 20


def test_qsofa():
    f = build_facts(PASSPORT, [{"mission_day": 5, "resp_rate": 23, "confusion": True, "bp_sys": 98}])
    assert f["qsofa"] == 3
    assert build_facts(PASSPORT, [{"mission_day": 5}])["qsofa"] == 0


def test_adaptation_window():
    assert build_facts(PASSPORT, [{"mission_day": 3}])["adaptation_window"] is True
    assert build_facts(PASSPORT, [{"mission_day": 50, "hours_since_transition": 48}])["adaptation_window"] is True
    assert build_facts(PASSPORT, [{"mission_day": 50}])["adaptation_window"] is False


def test_news2_in_facts_and_current_values_copied():
    f = build_facts(PASSPORT, [{"mission_day": 9, "hr_rest": 135, "sym_nausea": True}])
    assert f["news2_total"] == 3 and f["news2_max"] == 3
    assert f["sym_nausea"] is True and f["hr_rest"] == 135


def test_rule_support_streaks():
    h = [
        {"mission_day": 1, "bp_sys": 150, "bp_dia": 85, "fluid_intake": 2.8},
        {"mission_day": 2, "bp_sys": 132, "bp_dia": 92, "fluid_intake": 2.7},
    ]
    f = build_facts(PASSPORT, h)
    assert f["days_bp_ge140_90"] == 2
    assert f["days_fluid_lt30"] == 2 and f["days_fluid_lt25"] == 0
    h.append({"mission_day": 3})
    assert build_facts(PASSPORT, h)["days_bp_ge140_90"] == 0


def test_count14_poor_sleep():
    h = [{"mission_day": i, "sleep_hours": 5.5 if i % 2 else 7.5, "sleep_quality": 3} for i in range(1, 21)]
    h[-1]["sleep_quality"] = 1  # day 20: good hours but poor quality -> counts
    f = build_facts(PASSPORT, h)
    assert f["count14_poor_sleep"] == 8  # days 7..20: 7 odd days + day 20
