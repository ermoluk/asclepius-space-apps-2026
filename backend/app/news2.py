"""NEWS2 aggregate early-warning score (bands from knowledge-base/03-indicators.md section 1)."""

# (upper bound inclusive, score) evaluated in order; the last entry is the fallback score.
_BANDS = {
    "resp_rate": ([(8, 3), (11, 1), (20, 0), (24, 2)], 3),
    "spo2": ([(91, 3), (93, 2), (95, 1)], 0),
    "bp_sys": ([(90, 3), (100, 2), (110, 1), (219, 0)], 3),
    "hr_rest": ([(40, 3), (50, 1), (90, 0), (110, 1), (130, 2)], 3),
    "temp": ([(35.0, 3), (36.0, 1), (38.0, 0), (39.0, 1)], 2),
}


def _band(name: str, value: float) -> int:
    bands, fallback = _BANDS[name]
    for upper, score in bands:
        if value <= upper:
            return score
    return fallback


def news2(day: dict) -> dict:
    params: dict[str, int] = {}
    missing: list[str] = []
    for name in _BANDS:
        value = day.get(name)
        if value is None:
            params[name] = 0
            missing.append(name)
        else:
            params[name] = _band(name, value)
    params["on_oxygen"] = 2 if day.get("on_oxygen") else 0
    params["confusion"] = 3 if day.get("confusion") else 0
    return {
        "total": sum(params.values()),
        "params": params,
        "max": max(params.values()),
        "missing": missing,
    }
