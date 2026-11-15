"""Flight-surgeon packet text for RED assessments (format: 09-worked-examples, Scenario 3)."""

LONG_DELAY_S = 300  # one-way delay above which onboard steps come first (05-rules convention 5)
ONBOARD_WHO = ("🧑‍🚀", "👥", "🩺")
CAREER_LIMIT_MSV = 600
LOS_NOTE = "QUEUED - no link (far-side loss of signal); sends at acquisition of signal"

_VITALS = (("hr_rest", "HR"), ("bp", "BP"), ("spo2", "SpO2"), ("temp", "T"), ("resp_rate", "RR"),
           ("glucose", "Glucose"))


def _num(value) -> str:
    return f"{value:g}" if isinstance(value, (int, float)) else str(value)


def _comm_delay(passport: dict, day: dict):
    if day.get("comm_delay_s") is not None:
        return day["comm_delay_s"]
    return (passport.get("mission") or {}).get("comm_delay_s")


def _timeline(passport: dict, day: dict) -> list[str]:
    items = []
    if day.get("hours_since_spe") is not None:
        items.append(f"SPE alert T0 · now T0+{_num(day['hours_since_spe'])} h")
    if day.get("post_eva_hours") is not None:
        items.append(f"EVA ended {_num(day['post_eva_hours'])} h ago")
    if day.get("hours_since_transition") is not None:
        items.append(f"gravity transition {_num(day['hours_since_transition'])} h ago")
    symptoms = [k[4:].replace("_", " ") for k, v in day.items() if k.startswith("sym_") and v is True]
    if symptoms:
        items.append("symptoms: " + ", ".join(symptoms))
    base = (passport.get("baselines") or {}).get("lymphocytes_abs")
    if base and day.get("lymphocytes_abs") is not None:
        pct = (day["lymphocytes_abs"] - base) / base * 100
        items.append(f"lymphocytes {pct:+.0f}% vs baseline")
    return items


def _vitals(day: dict, news2: dict) -> str:
    values = dict(day)
    if day.get("bp_sys") is not None:
        values["bp"] = f"{_num(day['bp_sys'])}/{_num(day.get('bp_dia') or '?')}"
    parts = [f"{label} {_num(values[key])}" for key, label in _VITALS if values.get(key) is not None]
    score = f"NEWS2 {news2['total']}"
    if news2.get("missing"):
        score += f" (not measured: {', '.join(news2['missing'])})"
    return " · ".join(parts + [score])


def _action_lines(actions: list[dict]) -> list[str]:
    return [f"  - {a['id']} {a['text']} [{a['who']}]" for a in actions]


def build_packet(assessment: dict, passport: dict, day: dict) -> str:
    day = day or {}
    astronaut = passport.get("astronaut") or {}
    crew = astronaut.get("role") or astronaut.get("id") or "-"
    delay = _comm_delay(passport, day)
    los = day.get("comm_los") is True
    long_delay = los or (delay is not None and delay > LONG_DELAY_S)

    mission_day = _num(day["mission_day"]) if day.get("mission_day") is not None else "-"
    header = f"FLIGHT-SURGEON PACKET  ·  Crew: {crew}  ·  Mission day {mission_day}"
    if los:
        header += f"  ·  {LOS_NOTE}"
    elif long_delay:
        header += f"  ·  One-way comm delay {delay / 60:.1f} min - onboard steps first"
    elif delay is not None:
        header += f"  ·  Comm delay {_num(delay)} s"

    red_hyps = [h for h in assessment["hypotheses"] if h["level"] == "RED"]
    red_escs = [e for e in assessment["escalations"] if e["level"] == "RED"]
    status = [f"{h['name']} suspected ({round(h['cf'] * 100)}%)" for h in red_hyps]
    status += [e["label"] for e in red_escs]

    lines = [header, f"STATUS: {assessment['overall_level']} - " + "; ".join(status)]
    lines.append("TIMELINE: " + (" · ".join(_timeline(passport, day)) or "-"))
    if day.get("dose_cumulative") is not None:
        lines.append(f"DOSE: cumulative {_num(day['dose_cumulative'])} / {CAREER_LIMIT_MSV} mSv")
    lines.append("VITALS: " + _vitals(day, assessment["news2"]))

    rules = [f"{t['rule']} ({t['source']['key']})" for h in red_hyps for t in h["trace"]]
    rules += [e["rule"] for e in red_escs]
    lines.append("RULES: " + " · ".join(dict.fromkeys(rules)))

    others = [f"{h['name']} {round(h['cf'] * 100)}% {h['level']}" for h in assessment["hypotheses"]
              if h["level"] != "RED"]
    if others:
        lines.append("ALSO: " + " · ".join(others))

    red_items = red_hyps + red_escs
    actions = list({a["id"]: a for item in red_items for a in item.get("actions", [])}.values())
    onboard = [a for a in actions if any(w in a["who"] for w in ONBOARD_WHO)]
    names = [h["name"] for h in red_hyps] + [e["label"].split(" - ")[0] for e in red_escs]
    request = "REQUEST: guidance on further management - " + "; ".join(names)

    if long_delay:
        lines.append("ONBOARD FIRST:")
        lines += _action_lines(onboard) or ["  - Follow the onboard medical checklist with the CMO."]
        lines.append(request)
    else:
        lines.append(request)
        lines.append("ONBOARD ACTIONS:")
        lines += _action_lines(actions) or ["  - Follow the onboard medical checklist with the CMO."]
    return "\n".join(lines)
