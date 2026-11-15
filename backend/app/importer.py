"""Import a crew member's own data for the "My crew" mode: a CSV table or a six-month passport JSON.

Stateless, like the rest of the server: the file comes in as text, the answer is a six-month passport document
(same shape as data/passports/<crew>.json), the rule-engine inputs computed from it, check-in days for the history,
and a report of what was used and what was skipped. The browser keeps the result.

CSV layouts
  wide  day|date, <metric>, <metric>, ...          one row per day, one column per metric
  long  day|date, metric, value[, unit, ref_lo, ref_hi]   one row per value (labs with their reference range)
Time: `day` is an L-day (-180..-1, before launch) or a mission day (1, 2, ...); `date` needs the launch date
(without it the day after the last date is taken, so the whole file is pre-flight).
Every imported value gets the provenance "imported" (code IM).
"""
import csv
import io
import json
import math
import re
import statistics
from datetime import date, datetime, timedelta
from functools import lru_cache

import yaml
from pydantic import ValidationError

from .data import DATA, LAB_RANGE_METRICS, engine_inputs, passport_baselines

WINDOW = 180                     # passport window L-180 .. L-1
MAX_HISTORY_DAYS = 400
MAX_SKIPPED_SHOWN = 50
IMPORTED, CODE = "imported", "IM"
KNOWN_CODES = {"RA", "RG", "RP", "SC", "AU", CODE}
LAB_METRICS = set(LAB_RANGE_METRICS) | {"crp"}
KB_PASSPORT = DATA.parent / "knowledge-base" / "01-physiological-passport.md"
FIELD_ORDER = "ABCDEFGHIJKLM"


class ImportProblem(ValueError):
    """The file cannot be imported at all (the API answers 422 with this message)."""


@lru_cache(maxsize=1)
def metrics() -> dict:
    return yaml.safe_load((DATA / "metrics.yaml").read_text(encoding="utf-8"))["metrics"]


def _day_model():
    from .main import DayRecord  # late import: main imports this module
    return DayRecord


# ---- names and units -----------------------------------------------------------------------------------------
ALIASES = {
    "rhr": "hr_rest", "resting_hr": "hr_rest", "resting_heart_rate": "hr_rest", "heart_rate_resting": "hr_rest",
    "hrv": "hrv_rmssd", "rmssd": "hrv_rmssd",
    "sleep": "sleep_hours", "sleep_duration": "sleep_hours", "sleep_time": "sleep_hours", "total_sleep": "sleep_hours",
    "weight": "body_mass", "body_weight": "body_mass", "mass": "body_mass",
    "systolic": "bp_sys", "sbp": "bp_sys", "diastolic": "bp_dia", "dbp": "bp_dia",
    "hgb": "hemoglobin", "hb": "hemoglobin", "lymphocytes": "lymphocytes_abs", "lymph": "lymphocytes_abs",
    "neutrophils": "neutrophils_abs", "plt": "platelets",
    "oxygen_saturation": "spo2", "sp_o2": "spo2", "o2_saturation": "spo2",
    "temp": "temp_oral", "temperature": "temp_oral", "body_temperature": "temp_oral",
    "reaction_time": "pvt_rt", "pvt": "pvt_rt", "mood": "mood_valence",
}
# passport metric -> check-in (DayRecord) key, where they differ
HISTORY_KEY = {"temp_oral": "temp"}
TIME_DAY = ("day", "l_day", "t", "mission_day")
TIME_DATE = ("date", "datetime", "timestamp", "time")
LONG_COLS = {"metric": ("metric", "parameter", "name", "test"), "value": ("value", "result"),
             "unit": ("unit", "units"), "ref_lo": ("ref_lo", "ref_low", "reference_low", "range_min", "lo", "low"),
             "ref_hi": ("ref_hi", "ref_high", "reference_high", "range_max", "hi", "high")}
EMPTY = {"", "na", "n/a", "nan", "-", "—", "null", "none"}
TRUE, FALSE = {"true", "yes", "y", "1"}, {"false", "no", "n", "0"}

_UNIT_SAME = {"c": "degc", "°c": "degc", "degc": "degc", "f": "degf", "°f": "degf", "degf": "degf",
              "lbs": "lb", "pound": "lb", "pounds": "lb", "kgs": "kg", "hours": "h", "hour": "h", "hr": "h", "hrs": "h",
              "minutes": "min", "mins": "min", "minute": "min", "beats/min": "bpm", "msec": "ms",
              "k/ul": "10^3/ul", "x10^3/ul": "10^3/ul", "10^9/l": "10^3/ul", "x10^9/l": "10^3/ul",
              "cells/µl": "cells/ul", "/ul": "cells/ul", "mmhg": "mmhg"}
# (from, to, metrics it applies to or None for any, conversion)
_CONVERT = [
    ("degf", "degc", None, lambda v: (v - 32) * 5 / 9),
    ("lb", "kg", None, lambda v: v * 0.45359237),
    ("min", "h", None, lambda v: v / 60),
    ("mmol/l", "mg/dl", {"glucose"}, lambda v: v * 18.016),
    ("g/l", "g/dl", None, lambda v: v / 10),
    ("10^3/ul", "cells/ul", None, lambda v: v * 1000),
]


def _unit_key(u: str) -> str:
    k = re.sub(r"\s+", "", u.lower()).replace("µ", "u").replace("μ", "u").replace("°", "deg")
    k = k.replace("degdeg", "deg")
    return _UNIT_SAME.get(k, _UNIT_SAME.get(u.strip().lower(), k))


def _convert(metric: str, value: float, unit: str | None) -> tuple[float, str | None]:
    """(value in the dictionary unit, note) - raises ValueError for a unit we cannot convert."""
    expected = (metrics().get(metric) or {}).get("unit")
    if not unit or not expected or _unit_key(unit) == _unit_key(expected):
        return value, None
    src, dst = _unit_key(unit), _unit_key(expected)
    for a, b, only, fn in _CONVERT:
        if a == src and b == dst and (only is None or metric in only):
            return fn(value), f"{metric}: {unit} -> {expected}"
    raise ValueError(f"unit '{unit}' is not supported for {metric} (expected {expected})")


def _header(h: str) -> tuple[str, str | None]:
    """'Weight (lb)' -> ('weight', 'lb')."""
    h = h.strip().lstrip("﻿")
    unit = None
    m = re.match(r"^(.*?)\s*[\(\[]\s*([^)\]]+?)\s*[\)\]]\s*$", h)
    if m:
        h, unit = m.group(1), m.group(2)
    return re.sub(r"[^a-z0-9]+", "_", h.lower()).strip("_"), unit


def _resolve(key: str) -> str | None:
    """Column/metric name -> passport metric id (metrics.yaml), a check-in key, or None."""
    if key in metrics():
        return key
    if key in ALIASES:
        return ALIASES[key]
    if key.startswith("sym_") or key in _day_model().model_fields:
        return key
    return None


def _number(s: str, decimal_comma: bool) -> float | None:
    s = s.strip()
    if s.lower() in EMPTY:
        return None
    if decimal_comma:
        s = s.replace(" ", "").replace(",", ".")
    v = float(s)
    if not math.isfinite(v):
        raise ValueError("not a finite number")
    return v


# ---- time ----------------------------------------------------------------------------------------------------
def _parse_day(s: str) -> int:
    s = s.strip().upper().replace(" ", "")
    m = re.fullmatch(r"L([-+])(\d+)", s)
    if m:
        return int(m.group(2)) * (-1 if m.group(1) == "-" else 1)
    return int(float(s)) if re.fullmatch(r"[-+]?\d+(\.0+)?", s) else int("x")


def _parse_date(s: str) -> date:
    s = re.split(r"[T ]", s.strip())[0]
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"unrecognised date '{s}' (use YYYY-MM-DD or DD.MM.YYYY)")


# ---- CSV -> entries ------------------------------------------------------------------------------------------
def _rows(text: str) -> tuple[list[list[str]], bool]:
    text = text.lstrip("﻿")
    first = next((ln for ln in text.splitlines() if ln.strip()), "")
    delim = max(",;\t", key=first.count)
    rows = [r for r in csv.reader(io.StringIO(text), delimiter=delim) if any(c.strip() for c in r)]
    return rows, delim != ","


def _entries(text: str, launch_date: date | None, rep: dict) -> tuple[list[dict], date | None]:
    """Flat list of {line, kind ('L'|'M'), t, key, value, unit, ref_lo, ref_hi}."""
    rows, comma = _rows(text)
    if len(rows) < 2:
        raise ImportProblem("The file has no data rows (expected a header row and at least one row of values).")
    heads = [_header(h) for h in rows[0]]
    keys = [k for k, _ in heads]
    tcol = next((i for i, k in enumerate(keys) if k in TIME_DAY), None)
    dcol = next((i for i, k in enumerate(keys) if k in TIME_DATE), None) if tcol is None else None
    if tcol is None and dcol is None:
        raise ImportProblem("No time column: add a 'day' column (L-day like -92, or mission day 1, 2, ...) "
                            "or a 'date' column (YYYY-MM-DD).")
    col = {name: next((i for i, k in enumerate(keys) if k in alts), None) for name, alts in LONG_COLS.items()}
    long = col["metric"] is not None and col["value"] is not None
    rep["layout"] = "long" if long else "wide"

    # time of every row
    times: list[tuple[int, list[str], object]] = []
    for n, r in enumerate(rows[1:], start=2):
        raw = r[tcol if tcol is not None else dcol] if len(r) > (tcol if tcol is not None else dcol) else ""
        try:
            times.append((n, r, _parse_day(raw) if tcol is not None else _parse_date(raw)))
        except ValueError as e:
            _skip(rep, n, str(e) if dcol is not None else f"unrecognised day '{raw}' (use -92, L-92 or 3)")
    if dcol is not None:
        dates = [t for _, _, t in times]
        if not dates:
            raise ImportProblem("No row has a readable date.")
        launch = launch_date or (max(dates) + timedelta(days=1))
    else:
        launch = launch_date

    def place(t) -> tuple[str, int] | None:
        if dcol is not None:
            d = (t - launch).days
            return ("L", d) if d < 0 else ("M", d + 1)
        if t == 0:
            return None
        return ("L", t) if t < 0 else ("M", t)

    out: list[dict] = []
    unknown: dict[str, None] = {}
    for n, r, t in times:
        where = place(t)
        if where is None:
            _skip(rep, n, "day 0 is ambiguous: use -1 for the day before launch or 1 for the first mission day")
            continue
        cells: list[tuple[str, str, str | None, str, str]] = []  # (key, value, unit, ref_lo, ref_hi)
        if long:
            cell = lambda name: r[col[name]].strip() if col[name] is not None and col[name] < len(r) else ""  # noqa: E731
            name = cell("metric")
            if not name:
                continue
            k, u = _header(name)
            cells.append((k, cell("value"), cell("unit") or u, cell("ref_lo"), cell("ref_hi")))
        else:
            for i, (k, u) in enumerate(heads):
                if i in (tcol, dcol) or i >= len(r) or not k:
                    continue
                cells.append((k, r[i], u, "", ""))
        for k, raw, unit, lo, hi in cells:
            metric = _resolve(k)
            if metric is None:
                unknown[k] = None
                if long:
                    _skip(rep, n, f"unknown metric '{k}'")
                continue
            try:
                v = _value(metric, raw, comma)
                if v is None:
                    continue
                ref = (_number(lo, comma) if lo else None, _number(hi, comma) if hi else None)
            except ValueError:
                _skip(rep, n, f"{k}: '{raw.strip()}' is not a number")
                continue
            out.append({"line": n, "kind": where[0], "t": where[1], "key": metric, "value": v, "unit": unit,
                        "ref_lo": ref[0], "ref_hi": ref[1]})
    rep["unknown"] = list(unknown)
    rep["dates"] = dcol is not None
    rep["launch_date"] = launch.isoformat() if launch else None
    return out, launch


def _value(metric: str, raw: str, comma: bool):
    """Number for dictionary metrics; check-in items may also be yes/no or a short text (e.g. phase)."""
    if metric.startswith("sym_"):
        return _bool(raw)
    try:
        return _number(raw, comma)
    except ValueError:
        if metric in metrics():
            raise
    try:
        return _bool(raw)
    except ValueError:
        return raw.strip()[:64]


def _bool(s: str) -> bool | None:
    s = s.strip().lower()
    if s in EMPTY:
        return None
    if s in TRUE:
        return True
    if s in FALSE:
        return False
    raise ValueError("not a boolean")


def _skip(rep: dict, line: int, reason: str):
    rep["skipped_count"] += 1
    if len(rep["skipped"]) < MAX_SKIPPED_SHOWN:
        rep["skipped"].append({"line": line, "reason": reason})


# ---- passport fields (port of pipeline/passport.py fields()) -----------------------------------------------
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


def _rebase(obs):
    last = [o["value"] for o in obs if -14 <= o["t"] <= -1]
    return round(statistics.median(last), 2) if len(last) >= 5 else None


@lru_cache(maxsize=1)
def _field_labels() -> dict:
    """Passport field names (A1..M5) from the knowledge base tables."""
    out = {}
    if KB_PASSPORT.exists():
        for line in KB_PASSPORT.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^\|\s*([A-M]\d{1,2})\s*\|\s*([^|]+?)\s*\|", line)
            if m and m.group(1) not in out:
                label = re.sub(r"[`*]|\s+[—–-]\s+.*$", "", m.group(2)).strip()
                label = re.sub("[\U0001F9D1\U0001FA7A⌚‍\U0001F680️]", "", label).strip()
                out[m.group(1)] = label[:90]
    out["CHECKIN"] = "Daily check-in (practised pre-flight)"
    return out


def _fields(by_metric: dict[str, list[dict]], lab_fallback: dict) -> tuple[list[dict], list[str]]:
    out, fallback_used = [], []
    labels = _field_labels()

    def row(metric, value, method, obs, lo=None, hi=None, rebase=None, trend=None):
        meta = metrics().get(metric, {})
        n = len(obs)
        expected = {"daily": WINDOW, "weekly": WINDOW // 7, "monthly": WINDOW // 30}.get(meta.get("freq"), 1)
        need = {"daily": 28, "weekly": 4, "monthly": 2}.get(meta.get("freq"), 1)
        fid = meta.get("field") or "CHECKIN"
        out.append({"crew_id": "IMPORT", "field_id": fid, "metric": metric, "value": value, "lo": lo, "hi": hi,
                    "n": n, "completeness": round(min(1.0, n / expected), 3) if expected else None,
                    "readiness": "ready" if n >= need else ("partial" if n else "missing"),
                    "rebase14": rebase, "trend_per_30d": trend, "method": method, "unit": meta.get("unit", ""),
                    "provenance": IMPORTED, "source_ids": "IMPORT",
                    "label": meta.get("label") or labels.get(fid, fid), "field_label": labels.get(fid, fid)})

    for m, obs in sorted(by_metric.items()):
        obs = sorted(obs, key=lambda o: o["t"])
        freq = metrics().get(m, {}).get("freq")
        vals = sorted(o["value"] for o in obs)
        pts = [(o["t"], o["value"]) for o in obs]
        if m in LAB_METRICS:
            with_ref = [o for o in obs if o["ref_lo"] is not None or o["ref_hi"] is not None]
            if with_ref:
                lo, hi, how = with_ref[-1]["ref_lo"], with_ref[-1]["ref_hi"], "reference range from your file"
            elif m in lab_fallback:
                lo, hi = lab_fallback[m].get("lo"), lab_fallback[m].get("hi")
                how = "standard lab reference range (Inspiration4 lab report)"
                fallback_used.append(m)
            else:
                lo, hi, how = None, None, "no reference range"
            row(m, round(statistics.fmean(vals), 3), f"mean of imported draws; {how}", obs, lo, hi)
        elif m == "body_mass":
            row(m, round(statistics.fmean(v for _, v in pts[-3:]), 1), "mean of the last 3 measurements (KB B2)", obs,
                round(vals[0], 1), round(vals[-1], 1), trend=_trend(pts))
        elif m in ("bp_sys", "bp_dia"):
            row(m, round(statistics.fmean(vals), 1), "mean of imported measurements", obs,
                round(vals[0], 1), round(vals[-1], 1))
        elif freq == "daily":
            row(m, round(statistics.median(vals), 2), f"median of {len(vals)} imported days; personal range = p10..p90",
                obs, round(_pct(vals, 0.1), 2), round(_pct(vals, 0.9), 2), rebase=_rebase(obs), trend=_trend(pts))
        elif freq in ("weekly", "monthly"):
            row(m, round(statistics.median(vals), 2), f"median of {freq} measurements", obs,
                round(_pct(vals, 0.1), 2), round(_pct(vals, 0.9), 2), trend=_trend(pts))
        else:
            row(m, obs[-1]["value"] if len(obs) == 1 else round(statistics.fmean(vals), 3),
                "single measurement" if len(obs) == 1 else "mean of imported measurements", obs)

    def order(r):
        fid = r["field_id"]
        num = int(fid[1:]) if fid[1:].isdigit() else 0
        return (FIELD_ORDER.find(fid[0]) if fid[0] in FIELD_ORDER and fid[1:].isdigit() else 99, num, r["metric"])

    out.sort(key=order)
    return out, fallback_used


# ---- table import --------------------------------------------------------------------------------------------
def _new_report() -> dict:
    return {"rows": 0, "used": 0, "skipped": [], "skipped_count": 0, "metrics": [], "unknown": [], "converted": [],
            "outside_window": 0, "duplicates": 0, "history_days": 0, "layout": "", "dates": False,
            "launch_date": None}


def _table(filename: str, content: str, launch_date: date | None, name: str | None) -> dict:
    rep = _new_report()
    entries, launch = _entries(content, launch_date, rep)
    rep["rows"] = max(0, len(_rows(content)[0]) - 1)
    converted: dict[str, None] = {}
    passport: dict[tuple[int, str], list[dict]] = {}
    history: dict[int, dict] = {}
    hist_lines: dict[int, int] = {}
    for e in entries:
        m, v = e["key"], e["value"]
        if isinstance(v, float):
            if m in metrics():
                try:
                    v, note = _convert(m, v, e["unit"])
                except ValueError as err:
                    _skip(rep, e["line"], str(err))
                    continue
                if note:
                    converted[note] = None
                v = round(v, 3)
        if e["kind"] == "L":
            if e["t"] < -WINDOW:
                rep["outside_window"] += 1
                continue
            meta = metrics().get(m)
            if meta is None:
                _skip(rep, e["line"], f"{m} is a check-in item, not a passport metric (use a mission day 1, 2, ...)")
                continue
            rng = meta.get("range")
            if rng and not (rng[0] <= v <= rng[1]):
                _skip(rep, e["line"], f"{m} = {v:g} is outside the plausible range {rng[0]}..{rng[1]} {meta.get('unit', '')}".rstrip())
                continue
            if v < 0 and m in LAB_METRICS:
                _skip(rep, e["line"], f"{m} = {v:g} cannot be negative")
                continue
            passport.setdefault((e["t"], m), []).append({**e, "value": v})
        else:
            key = HISTORY_KEY.get(m, m)
            day = history.setdefault(e["t"], {"mission_day": e["t"]})
            if key in day:
                rep["duplicates"] += 1
            day[key] = v
            hist_lines.setdefault(e["t"], e["line"])
    rep["converted"] = list(converted)

    # passport observations: duplicates of the same day and metric are averaged
    obs_by_metric: dict[str, list[dict]] = {}
    for (t, m), group in passport.items():
        rep["duplicates"] += len(group) - 1
        lo = next((g["ref_lo"] for g in reversed(group) if g["ref_lo"] is not None), None)
        hi = next((g["ref_hi"] for g in reversed(group) if g["ref_hi"] is not None), None)
        val = round(statistics.fmean(g["value"] for g in group), 3)
        obs_by_metric.setdefault(m, []).append({"t": t, "value": val, "ref_lo": lo, "ref_hi": hi})

    days = _validate_days(history, hist_lines, rep)
    if not obs_by_metric and not days:
        reasons = "; ".join(s["reason"] for s in rep["skipped"][:3])
        raise ImportProblem("No usable values in the file." + (f" First problems: {reasons}" if reasons else
                            f" Known metrics include: {', '.join(list(metrics())[:12])}, ..."))

    doc = engine = None
    if obs_by_metric:
        lab_fallback = passport_baselines("CM-2").get("lab_ranges", {})
        fields, fallback_used = _fields(obs_by_metric, lab_fallback)
        series = {m: [[o["t"], o["value"], CODE] for o in sorted(obs, key=lambda o: o["t"])]
                  for m, obs in obs_by_metric.items()
                  if metrics()[m].get("freq") in ("daily", "weekly", "monthly") or m in LAB_METRICS}
        sessions: dict[int, dict] = {}
        for m, obs in obs_by_metric.items():
            if metrics()[m].get("freq") in ("daily", "weekly", "monthly"):
                continue
            for o in obs:
                s = sessions.setdefault(o["t"], {"session_id": f"import-L{-o['t']}", "t": o["t"],
                                                 "title": f"Imported measurements (L{o['t']})", "status": "done",
                                                 "provenance": IMPORTED, "source_ids": "IMPORT", "values": {}})
                s["values"][m] = o["value"]
        ts = [o["t"] for obs in obs_by_metric.values() for o in obs]
        used = sum(len(obs) for obs in obs_by_metric.values())
        doc = {"crew_id": "IMPORT", "name": name or _stem(filename), "role": "", "sex": "", "age": None,
               "modifiers": [], "window": {"start": -WINDOW, "end": -1}, "provenance_codes": {CODE: IMPORTED},
               "donors": [], "fields": fields, "sessions": [sessions[t] for t in sorted(sessions)], "series": series,
               "import": {"filename": filename, "used": used, "first": min(ts), "last": max(ts),
                          "launch_date": launch.isoformat() if launch else None, "lab_ref_fallback": fallback_used}}
        engine = engine_inputs(doc)
        rep["used"] += used
        for m, obs in sorted(obs_by_metric.items()):
            t = [o["t"] for o in obs]
            rep["metrics"].append({"metric": m, "label": metrics()[m].get("label", m), "unit": metrics()[m].get("unit", ""),
                                   "n": len(obs), "first": min(t), "last": max(t), "target": "passport"})
    if days:
        counts: dict[str, list[int]] = {}
        for d in days:
            for k in d:
                if k != "mission_day":
                    counts.setdefault(k, []).append(d["mission_day"])
        for k, ds in sorted(counts.items()):
            meta = metrics().get(k) or metrics().get({v: k2 for k2, v in HISTORY_KEY.items()}.get(k, ""), {})
            rep["metrics"].append({"metric": k, "label": meta.get("label", k.replace("_", " ").capitalize()), "unit": meta.get("unit", ""),
                                   "n": len(ds), "first": min(ds), "last": max(ds), "target": "check-ins"})
            rep["used"] += len(ds)
    rep["history_days"] = len(days)
    return {"kind": "table", "name": name or _stem(filename), "role": "", "sex": "", "age": None, "modifiers": [],
            "passport_doc": doc, "engine": engine, "history": days, "report": rep}


def _validate_days(history: dict[int, dict], lines: dict[int, int], rep: dict) -> list[dict]:
    model = _day_model()
    out = []
    for md in sorted(history):
        rec = dict(history[md])
        for _ in range(len(rec)):
            try:
                out.append(model(**rec).model_dump(exclude_none=True))
                break
            except ValidationError as err:
                bad = {e["loc"][0] for e in err.errors() if e.get("loc")}
                bad.discard("mission_day")
                if not bad:
                    _skip(rep, lines.get(md, 0), f"mission day {md}: {err.errors()[0].get('msg', 'invalid')}")
                    break
                for e in err.errors():
                    if e.get("loc") and e["loc"][0] in bad:
                        _skip(rep, lines.get(md, 0), f"mission day {md}: {e['loc'][0]}: {e.get('msg', 'invalid')}")
                for k in bad:
                    rec.pop(k, None)
        if out and out[-1]["mission_day"] == md and len(out[-1]) == 1:
            out.pop()  # nothing left but the day number
    if len(out) > MAX_HISTORY_DAYS:
        rep["history_truncated"] = len(out) - MAX_HISTORY_DAYS
        out = out[-MAX_HISTORY_DAYS:]
    return out


def _stem(filename: str) -> str:
    base = re.split(r"[\\/]", filename)[-1]
    return re.sub(r"\.[A-Za-z0-9]+$", "", base)[:100] or "Imported crew member"


# ---- passport JSON import ------------------------------------------------------------------------------------
def _passport_json(filename: str, doc: dict, name: str | None) -> dict:
    if doc.get("format") == "asclepius-crew":
        raise ImportProblem("This is a crew backup file: it is restored in the browser, not parsed here.")
    if not (isinstance(doc.get("fields"), list) and isinstance(doc.get("series"), dict)
            and isinstance(doc.get("window"), dict)):
        raise ImportProblem("Not a passport file: expected the six-month passport format "
                            "(keys 'window', 'fields', 'series', as in data/passports/*.json) or a crew backup.")
    series: dict[str, list] = {}
    for m, pts in doc["series"].items():
        if not isinstance(pts, list):
            continue
        clean = []
        for p in pts:
            if isinstance(p, list) and len(p) >= 2 and isinstance(p[0], (int, float)) and isinstance(p[1], (int, float)) \
                    and math.isfinite(p[1]) and -WINDOW <= p[0] <= -1:
                code = p[2] if len(p) > 2 and p[2] in KNOWN_CODES else CODE
                clean.append([int(p[0]), p[1], code])
        if clean:
            series[str(m)] = clean
    fields = [f for f in doc["fields"] if isinstance(f, dict) and isinstance(f.get("field_id"), str)
              and isinstance(f.get("metric"), str)]
    for f in fields:
        for k in ("lo", "hi", "rebase14"):
            if not isinstance(f.get(k), (int, float, type(None))) or (isinstance(f.get(k), float) and not math.isfinite(f[k])):
                f[k] = None
        f.setdefault("readiness", "partial")
        f.setdefault("n", 0)
    sessions = [s for s in doc.get("sessions") or [] if isinstance(s, dict) and isinstance(s.get("values"), dict)]
    clean_doc = {**doc, "series": series, "fields": fields, "sessions": sessions,
                 "donors": [d for d in doc.get("donors") or [] if isinstance(d, dict)],
                 "window": {"start": -WINDOW, "end": -1}}
    try:
        engine = engine_inputs(clean_doc)
    except (KeyError, TypeError, ValueError) as e:
        raise ImportProblem(f"The passport file is incomplete: {e}") from None
    rep = _new_report()
    rep["layout"] = "passport"
    labels = {f["metric"]: f.get("label") for f in fields}
    for m, pts in sorted(series.items()):
        ts = [p[0] for p in pts]
        meta = metrics().get(m, {})
        rep["metrics"].append({"metric": m, "label": labels.get(m) or meta.get("label", m), "unit": meta.get("unit", ""),
                               "n": len(pts), "first": min(ts), "last": max(ts), "target": "passport"})
        rep["used"] += len(pts)
    rep["rows"] = rep["used"]
    who = name or (doc.get("name") if isinstance(doc.get("name"), str) else None) or _stem(filename)
    mods = [m for m in doc.get("modifiers") or [] if isinstance(m, str)]
    age = doc.get("age") if isinstance(doc.get("age"), (int, float)) else None
    return {"kind": "passport", "name": who[:100], "role": str(doc.get("role") or "")[:100],
            "sex": str(doc.get("sex") or "")[:1], "age": age, "modifiers": mods,
            "passport_doc": clean_doc, "engine": engine, "history": [], "report": rep}


def parse(filename: str, content: str, launch_date: date | None = None, name: str | None = None) -> dict:
    text = content.lstrip("﻿")
    if filename.lower().endswith(".json") or text.lstrip().startswith(("{", "[")):
        try:
            doc = json.loads(text)
        except json.JSONDecodeError as e:
            raise ImportProblem(f"The JSON file cannot be read: {e.msg} (line {e.lineno}).") from None
        if not isinstance(doc, dict):
            raise ImportProblem("Not a passport file: expected a JSON object.")
        return _passport_json(filename, doc, name)
    return _table(filename, text, launch_date, name)
