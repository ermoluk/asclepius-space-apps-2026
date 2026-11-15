"""Import of a crew member's own data ("My crew"): CSV tables and six-month passport JSON."""
import json
import random
import statistics
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app import data, importer
from app.main import app

client = TestClient(app)


def _wide(days=range(-180, 0), seed=7, extra_flight=()):
    rnd = random.Random(seed)
    rows = ["day,hr_rest,hrv_rmssd,sleep_hours,spo2"]
    hr = []
    for t in days:
        h = 58 + rnd.randint(-5, 5)
        hr.append(h)
        rows.append(f"{t},{h},{55 + rnd.randint(-10, 10)},{6.5 + rnd.random():.2f},{97 + rnd.random():.1f}")
    rows += list(extra_flight)
    return "\n".join(rows), hr


def _pct(vals, p):
    s = sorted(vals)
    k = (len(s) - 1) * p
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def test_wide_csv_builds_passport_and_engine_inputs():
    text, hr = _wide()
    r = importer.parse("me.csv", text)
    assert r["kind"] == "table" and r["report"]["layout"] == "wide"
    doc = r["passport_doc"]
    assert doc["window"] == {"start": -180, "end": -1}
    assert len(doc["series"]["hr_rest"]) == 180
    assert all(p[2] == "IM" for p in doc["series"]["hr_rest"])
    f = next(f for f in doc["fields"] if f["metric"] == "hr_rest")
    assert f["readiness"] == "ready" and f["provenance"] == "imported" and f["field_id"] == "B3"
    pr = r["engine"]["personal_ranges"]["hr_rest"]
    assert pr["lo"] == pytest.approx(round(_pct(hr, 0.1), 2))
    assert pr["hi"] == pytest.approx(round(_pct(hr, 0.9), 2))
    assert pr["ready"] is True and pr["n"] == 180
    assert r["engine"]["baselines"]["hr_rest"] == pytest.approx(statistics.median(hr))
    assert r["engine"]["baselines_source"].startswith("Imported file me.csv")
    assert r["history"] == []


def test_short_series_is_partial_not_ready():
    text, _ = _wide(days=range(-10, 0))
    r = importer.parse("short.csv", text)
    f = next(f for f in r["passport_doc"]["fields"] if f["metric"] == "hr_rest")
    assert f["readiness"] == "partial"
    assert r["engine"]["personal_ranges"]["hr_rest"]["ready"] is False


def test_positive_days_go_to_history_and_day_zero_is_skipped():
    text, _ = _wide(days=range(-30, 0), extra_flight=["1,62,50,6.0,96", "2,66,45,5.5,95", "0,60,50,7,97"])
    r = importer.parse("me.csv", text)
    assert [d["mission_day"] for d in r["history"]] == [1, 2]
    assert r["history"][1]["hr_rest"] == 66
    assert any("day 0" in s["reason"] for s in r["report"]["skipped"])
    targets = {m["target"] for m in r["report"]["metrics"]}
    assert targets == {"passport", "check-ins"}


def test_dates_split_at_launch_date():
    rows = ["date,hr_rest,sleep_hours"]
    for i in range(40):
        d = date(2026, 1, 1).toordinal() + i
        rows.append(f"{date.fromordinal(d).isoformat()},60,7")
    r = importer.parse("dates.csv", "\n".join(rows), launch_date=date(2026, 2, 1))
    # 2026-01-01..2026-01-31 -> L-31..L-1; 2026-02-01..2026-02-09 -> mission days 1..9
    assert r["passport_doc"]["series"]["hr_rest"][0][0] == -31
    assert r["passport_doc"]["series"]["hr_rest"][-1][0] == -1
    assert [d["mission_day"] for d in r["history"]] == list(range(1, 10))


def test_dates_without_launch_date_are_all_preflight():
    rows = ["Date;HR rest;Sleep hours"] + [f"{d:02d}.03.2026;6{d % 10};7,{d % 10}" for d in range(1, 21)]
    r = importer.parse("ru.csv", "\n".join(rows))
    s = r["passport_doc"]["series"]
    assert s["hr_rest"][-1][0] == -1 and len(s["hr_rest"]) == 20
    assert s["sleep_hours"][0][1] == pytest.approx(7.1)  # decimal comma with ';' separator
    assert r["history"] == []


def test_long_csv_labs_with_reference_ranges_and_fallback():
    text = "\n".join([
        "day,metric,value,unit,ref_lo,ref_hi",
        "-92,hemoglobin,14.6,g/dL,13.2,17.1",
        "-44,hemoglobin,148,g/L,13.2,17.1",
        "-92,lymphocytes_abs,2.1,10^3/uL,,",
        "-92,glucose,5.0,mmol/L,,",
        "-92,unobtainium,1,,,",
    ])
    r = importer.parse("labs.csv", text)
    assert r["report"]["layout"] == "long"
    labs = r["engine"]["lab_ranges"]
    assert labs["hemoglobin"] == {"lo": 13.2, "hi": 17.1}
    hb = next(f for f in r["passport_doc"]["fields"] if f["metric"] == "hemoglobin")
    assert hb["value"] == pytest.approx(14.7)  # mean of 14.6 and 148 g/L -> 14.8 g/dL
    assert r["passport_doc"]["series"]["lymphocytes_abs"][0][1] == pytest.approx(2100)
    assert r["passport_doc"]["series"]["glucose"][0][1] == pytest.approx(90.08)
    # lymphocytes had no range in the file: standard Inspiration4 lab range, said so in the source line
    assert labs["lymphocytes_abs"] == data.passport_baselines("CM-2")["lab_ranges"]["lymphocytes_abs"]
    assert "Inspiration4 lab report" in r["engine"]["baselines_source"]
    assert any("unobtainium" in s["reason"] for s in r["report"]["skipped"])
    assert "glucose: mmol/L -> mg/dL" in r["report"]["converted"]


def test_units_and_out_of_range_values_are_reported_not_clipped():
    text = "day,weight (lb),temp (F),hr_rest,spo2,mystery\n-3,160,98.6,300,97,1\n-2,161,98.4,59,abc,2\n-1,150,98.5,58,96,3"
    r = importer.parse("u.csv", text)
    s = r["passport_doc"]["series"]
    assert s["body_mass"][0][1] == pytest.approx(72.575, abs=0.01)
    temp = next(x for x in r["passport_doc"]["sessions"] if x["t"] == -3)["values"]["temp_oral"]
    assert temp == pytest.approx(37.0, abs=0.01)
    assert [p[1] for p in s["hr_rest"]] == [59, 58]  # 300 bpm rejected, not clipped to 120
    reasons = " ".join(x["reason"] for x in r["report"]["skipped"])
    assert "outside the plausible range" in reasons and "not a number" in reasons
    assert r["report"]["unknown"] == ["mystery"]


def test_unsupported_unit_is_skipped():
    r = importer.parse("x.csv", "day,metric,value,unit\n-1,hr_rest,60,furlongs\n-2,hr_rest,61,bpm")
    assert len(r["passport_doc"]["series"]["hr_rest"]) == 1
    assert "not supported" in r["report"]["skipped"][0]["reason"]


def test_history_values_checked_against_check_in_bounds():
    r = importer.parse("h.csv", "day,sleep_quality,kss,sym_headache,phase\n1,3,7,yes,transit\n2,9,4,no,transit")
    d1, d2 = r["history"]
    assert d1["sleep_quality"] == 3 and d1["sym_headache"] is True and d1["phase"] == "transit"
    assert "sleep_quality" not in d2 and d2["kss"] == 4  # 9 is outside 1..5
    assert any("sleep_quality" in s["reason"] for s in r["report"]["skipped"])
    assert r["passport_doc"] is None and r["engine"] is None


def test_old_rows_outside_window_are_counted():
    text, _ = _wide(days=range(-200, 0))
    r = importer.parse("old.csv", text)
    assert r["report"]["outside_window"] == 20 * 4
    assert r["passport_doc"]["series"]["hr_rest"][0][0] == -180


def test_engine_inputs_refactor_matches_pipeline_passports():
    for cid in data.crew_ids():
        assert data.engine_inputs(data.crew_passport(cid)) == data.passport_baselines(cid)


def test_passport_json_import_keeps_provenance():
    doc = data.crew_passport("HY-CDR")
    r = importer.parse("HY-CDR.json", json.dumps(doc))
    assert r["kind"] == "passport" and r["name"] == doc["name"]
    assert r["engine"] == data.passport_baselines("HY-CDR")
    codes = {p[2] for pts in r["passport_doc"]["series"].values() for p in pts}
    assert codes <= {"RA", "RG", "RP", "SC", "AU"} and "RA" in codes


@pytest.mark.parametrize("filename,content,msg", [
    ("x.csv", "hr_rest,spo2\n60,97", "No time column"),
    ("x.csv", "day,hr_rest", "no data rows"),
    ("x.csv", "day,foo,bar\n-1,1,2", "No usable values"),
    ("x.json", "{\"hello\": 1}", "Not a passport file"),
    ("x.json", "{\"format\": \"asclepius-crew\", \"members\": []}", "crew backup"),
    ("x.json", "{oops", "cannot be read"),
])
def test_unusable_files_raise(filename, content, msg):
    with pytest.raises(importer.ImportProblem, match=msg):
        importer.parse(filename, content)


def test_api_parse_and_assess_with_imported_passport():
    text, _ = _wide(days=range(-60, 0), extra_flight=["1,61,50,6.5,97", "2,63,48,6.0,96"])
    r = client.post("/api/import/parse", json={"filename": "me.csv", "content": text, "name": "Ira"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["name"] == "Ira" and body["report"]["history_days"] == 2
    base = client.post("/api/passport/derive", json={"answers": {"name": "Ira", "new_member": True,
                                                                 "baselines": body["engine"]["baselines"]}}).json()
    passport = {**base, "personal_ranges": body["engine"]["personal_ranges"], "lab_ranges": body["engine"]["lab_ranges"],
                "baselines_source": body["engine"]["baselines_source"], "passport_ref": "local:MY-1@abc"}
    a = client.post("/api/assess", json={"passport": passport, "history": body["history"]})
    assert a.status_code == 200, a.text
    assert a.json()["overall_level"] in ("GREEN", "YELLOW", "ORANGE", "RED")


@pytest.mark.parametrize("payload", [
    {"filename": "x.csv", "content": ""},
    {"filename": "x.csv", "content": "day,foo\n-1,2"},
    {"filename": "x.csv", "content": "x" * 3_000_001},
    {"filename": "x.csv", "content": "day,hr_rest\n-1,60", "launch_date": "not-a-date"},
    {"filename": "x.csv", "content": "day,hr_rest\n-1,60", "unexpected": 1},
])
def test_api_rejects_bad_imports(payload):
    r = client.post("/api/import/parse", json=payload)
    assert r.status_code == 422
    assert "x" * 100 not in r.text  # input is not echoed back
