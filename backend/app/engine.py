"""Forward-chaining rule engine: passport + history -> Assessment (contract in the MVP plan).

Conventions (knowledge-base/05-rules.md "Engine conventions"):
- tri-state evaluation: a missing fact is unknown (None), never "normal";
- MYCIN combination CF = a + b(1 - a); hypothesis level = highest level among its fired rules;
- red-flag guard: `expected: true` rules are dropped when a RED rule fired in the same system;
- a hypothesis that fires sets `hyp_<ID>` (+ `hyp_<ID>_cf`) so later rules can chain on it;
- pending rules + missing confirm-with facts rank the next best measurement.
"""
from functools import lru_cache

from .data import incidence
from .facts import build_facts
from .kb import KB, load_kb
from .news2 import news2
from .packet import build_packet

LEVELS = ("GREEN", "YELLOW", "ORANGE", "RED")
LEVEL_RANK = {lvl: i for i, lvl in enumerate(LEVELS)}
LEVEL_WEIGHT = {"GREEN": 0, "YELLOW": 1, "ORANGE": 2, "RED": 3}
MAX_PASSES = 10
CF_CAP = 0.99

# 05-rules "modifier rules", encoded as `modifiers:` on their base rule; named in the trace label.
MODIFIER_RULES = {"P-01": "R-VES-02", "P-03": "R-EYE-03", "P-17": "R-CV-14"}

# Closed-world facts: absent means "no" (symptom not reported, modifier not in passport, hypothesis not
# established, habitat alarm silent). Every other missing fact is unknown.
CLOSED_WORLD_PREFIXES = ("sym_", "mod_", "hyp_")
CLOSED_WORLD_FACTS = {"confusion", "spe_alert", "ammonia_alarm", "smoke_alarm", "depress_alarm", "microbial_alert"}

# Context facts the crew cannot "measure" (never offered as the next best measurement).
# Context, not something the crew can measure: never offered as "measure next".
NOT_MEASURABLE = {"phase", "mission_day", "hours_since_spe"}

FACT_LABELS = {
    "near_acuity_decline": "Near-vision test (each eye)",
    "bp_sys": "Blood pressure (cuff)",
    "bp_dia": "Blood pressure (cuff)",
    "hr_rest": "Resting heart rate",
    "spo2": "Pulse oximeter (SpO₂)",
    "temp": "Body temperature",
    "resp_rate": "Breathing rate (30-s count × 2)",
    "glucose": "Blood glucose (glucometer)",
    "pvt_rt": "Reaction-time test (3-min PVT)",
    "kss": "Sleepiness scale (KSS)",
    "sleep_hours": "Hours slept last night",
    "sleep_quality": "Sleep quality (1-5)",
    "mood_valence": "Evening mood check-in",
    "co2_1h": "Cabin CO₂, 1-h average",
    "co2_7d": "Cabin CO₂, 7-day average",
    "pio2": "Cabin oxygen pressure (pIO₂)",
    "cabin_temp": "Cabin temperature",
    "lymphocytes_abs": "Blood count (lymphocytes)",
    "hours_since_spe": "Hours since the solar particle event",
    "post_eva_hours": "Hours since the last EVA",
    "ecg_rhythm": "Single-lead ECG strip",
    "gcs": "Glasgow Coma Scale check by a crewmate",
    "befast_positive": "BE-FAST check by a crewmate",
    "body_mass": "Body mass measurement",
    "fluid_intake": "Fluid intake today (L)",
    "phq9": "PHQ-9 questionnaire",
    "gad7": "GAD-7 questionnaire",
    "awake_hours": "Hours awake since last sleep",
    "work_hours": "Work hours today",
    "work_days_in_row": "Work days in a row",
    "vomiting_hours": "How long the vomiting has lasted (h)",
    "abdominal_pain_location": "Where the abdominal pain is (guided check)",
    "urine_nitrite_le": "Urine dipstick (nitrite / leukocytes)",
    "urine_blood": "Urine dipstick (blood)",
    "nosebleed_minutes": "How long the nosebleed lasted (min)",
    "dose_cumulative": "Dosimeter readout",
    "hemoglobin": "Blood count (hemoglobin)",
    "sodium": "Blood chemistry (sodium)",
    "hrv_rmssd": "Morning heart-rate variability (wearable)",
    "urine_color": "Urine colour chart",
    "urine_osm": "Urine osmolality",
}


# ------------------------------------------------------------------------------ evaluation

def _leaf(cond: dict, facts: dict):
    value = facts.get(cond["fact"])
    if value is None:
        return None
    op, ref = cond["op"], cond.get("value")
    try:
        if op == "true":
            return bool(value)
        if op == "eq":
            return value == ref
        if op == "ne":
            return value != ref
        if op == "gt":
            return value > ref
        if op == "gte":
            return value >= ref
        if op == "lt":
            return value < ref
        if op == "lte":
            return value <= ref
        if op == "between":
            low, high = ref
            return low <= value <= high
        if op == "in":
            if isinstance(value, (list, tuple, set)):
                return bool(set(value) & set(ref))
            return value in ref
    except TypeError:
        return None
    raise ValueError(f"unknown op {op!r} in {cond}")


def evaluate(cond: dict, facts: dict):
    """Tri-state: True, False, or None when missing facts leave the outcome open."""
    if "all" in cond:
        results = [evaluate(c, facts) for c in cond["all"]]
        if any(r is False for r in results):
            return False
        return None if any(r is None for r in results) else True
    if "any" in cond:
        results = [evaluate(c, facts) for c in cond["any"]]
        if any(r is True for r in results):
            return True
        return None if any(r is None for r in results) else False
    if "not" in cond:
        result = evaluate(cond["not"], facts)
        return None if result is None else not result
    return _leaf(cond, facts)


def _leaves(cond: dict, positive: bool = True):
    """Yield (leaf, positive) pairs; `positive` is False under an odd number of `not`s."""
    if "all" in cond or "any" in cond:
        for child in cond.get("all", cond.get("any")):
            yield from _leaves(child, positive)
    elif "not" in cond:
        yield from _leaves(cond["not"], not positive)
    else:
        yield cond, positive


def _rule_facts(rule: dict) -> list[str]:
    return list(dict.fromkeys(leaf["fact"] for leaf, _ in _leaves(rule["when"])))


# ------------------------------------------------------------------------------ helpers

def _combine(a: float, b: float) -> float:
    return a + b * (1 - a)


def _effective_cf(rule: dict, facts: dict) -> tuple[float, list[str]]:
    base = rule["then"]["cf"]
    applied = [mod for mod in (rule.get("modifiers") or {}) if facts.get(f"mod_{mod}")]
    if not applied:
        return base, []
    bonus = sum(rule["modifiers"][mod] for mod in applied)
    return min(CF_CAP, base + bonus), applied


def _worst(levels) -> str:
    return max(levels, key=LEVEL_RANK.__getitem__, default="GREEN")


def _measurable(fact: str, facts: dict) -> str:
    """Map a derived fact to what the crew can actually measure."""
    if fact.startswith("delta_pct_"):
        raw = fact[len("delta_pct_"):]
        return raw if facts.get(raw) is None else f"baseline_{raw}"
    for prefix in ("lab_below_", "lab_above_"):
        if fact.startswith(prefix):
            return fact[len(prefix):]
    return fact


def _apply_closed_world(facts: dict, rules: list[dict]) -> None:
    for rule in rules:
        names = _rule_facts(rule) + [f"mod_{m}" for m in rule.get("modifiers") or {}]
        if "hypothesis" in rule["then"]:
            names.append(f"hyp_{rule['then']['hypothesis']}")
        for name in names:
            if name.startswith(CLOSED_WORLD_PREFIXES) or name in CLOSED_WORLD_FACTS:
                if facts.get(name) is None:
                    facts[name] = False


@lru_cache(maxsize=1)
def _default_kb() -> KB:
    return load_kb()


# ------------------------------------------------------------------------------ inference

def _forward_chain(rules: list[dict], facts: dict, blocked: set) -> list[dict]:
    """Fire rules until no new rule fires (max MAX_PASSES). Mutates `facts` with hyp_* chaining facts."""
    fired: list[dict] = []
    done: set = set()
    for _ in range(MAX_PASSES):
        new = False
        for rule in rules:
            if rule["id"] in done or rule["id"] in blocked:
                continue
            if evaluate(rule["when"], facts) is not True:
                continue
            cf, applied = _effective_cf(rule, facts)
            snapshot = {name: facts[name] for name in _rule_facts(rule) if facts.get(name) is not None}
            snapshot.update({f"mod_{m}": True for m in applied})
            fired.append({"rule": rule, "cf": cf, "modifiers": applied, "facts": snapshot})
            done.add(rule["id"])
            new = True
            hyp = rule["then"].get("hypothesis")
            if hyp:
                prev = facts.get(f"hyp_{hyp}_cf") or 0.0
                facts[f"hyp_{hyp}"] = True
                facts[f"hyp_{hyp}_cf"] = _combine(prev, cf)
        if not new:
            break
    return fired


def _run_with_guard(rules: list[dict], base_facts: dict) -> tuple[list[dict], dict, set]:
    blocked: set = set()
    while True:
        facts = dict(base_facts)
        fired = _forward_chain(rules, facts, blocked)
        red_systems = {f["rule"]["system"] for f in fired
                       if f["rule"]["then"]["level"] == "RED" and not f["rule"].get("expected")}
        newly = {f["rule"]["id"] for f in fired
                 if f["rule"].get("expected") and f["rule"]["system"] in red_systems} - blocked
        if not newly:
            return fired, facts, blocked
        blocked |= newly


# ------------------------------------------------------------------------------ output

def _label(fire: dict) -> str:
    label = fire["rule"]["label"]
    for mod in fire["modifiers"]:
        bonus = fire["rule"]["modifiers"][mod]
        via = f", {MODIFIER_RULES[mod]}" if mod in MODIFIER_RULES else ""
        label += f" (+{bonus:.2f} {mod} modifier{via})"
    return label


def _source(rule: dict, kb: KB) -> dict:
    key = rule["refs"][0]
    ref = kb.references.get(key) or {}
    return {"key": key, "title": ref.get("title", key), "url": ref.get("url")}


def _actions(rules: list[dict], kb: KB) -> list[dict]:
    ids = dict.fromkeys(a for rule in rules for a in rule.get("actions", []))
    return [dict(kb.actions[a]) for a in ids]


def _hypotheses(fired: list[dict], kb: KB) -> list[dict]:
    groups: dict[str, list[dict]] = {}
    for fire in fired:
        hyp = fire["rule"]["then"].get("hypothesis")
        if hyp:
            groups.setdefault(hyp, []).append(fire)
    out = []
    for hyp, fires in groups.items():
        cond = kb.conditions[hyp]
        cf = 0.0
        for fire in fires:
            cf = _combine(cf, fire["cf"])
        out.append({
            "id": hyp,
            "name": cond["name"],
            "system": cond["system"],
            "cf": round(cf, 2),
            "level": _worst(fire["rule"]["then"]["level"] for fire in fires),
            "expected": all(fire["rule"].get("expected", False) for fire in fires),
            "trace": [{
                "rule": fire["rule"]["id"],
                "label": _label(fire),
                "facts": fire["facts"],
                "cf": round(fire["cf"], 2),
                "source": _source(fire["rule"], kb),
            } for fire in fires],
            "actions": _actions([fire["rule"] for fire in fires], kb),
            "incidence": incidence().get(hyp),  # how common in flight (NASA IMM / ISS events), display only
        })
    out.sort(key=lambda h: (-LEVEL_RANK[h["level"]], -h["cf"], h["id"]))
    return out


def _pending(rules: list[dict], facts: dict, fired_ids: set, blocked: set) -> list[dict]:
    out = []
    for rule in rules:
        if rule["id"] in fired_ids or rule["id"] in blocked or rule["then"]["level"] == "GREEN":
            continue  # a GREEN rule waiting for data is not a pending check worth showing
        if evaluate(rule["when"], facts) is not None:
            continue
        leaves = list(_leaves(rule["when"]))
        support = any(positive and _leaf(leaf, facts) is True for leaf, positive in leaves)
        hyp = rule["then"].get("hypothesis")
        if not (support or (hyp and facts.get(f"hyp_{hyp}"))):
            continue
        missing = [_measurable(leaf["fact"], facts) for leaf, _ in leaves if facts.get(leaf["fact"]) is None]
        out.append({"rule": rule, "missing": list(dict.fromkeys(missing))})
    return out


def _reason(rule: dict, kb: KB) -> str:
    hyp = rule["then"].get("hypothesis")
    return kb.conditions[hyp]["name"] if hyp else rule["then"]["escalation"]


def _next_measurement(pending: list[dict], fired: list[dict], facts: dict, kb: KB):
    candidates: dict[str, dict] = {}

    def add(fact: str, rule: dict, weight: float, confirm: bool = False):
        entry = candidates.setdefault(fact, {"weight": 0.0, "best": 0.0, "rule": rule})
        if confirm and weight >= entry.get("cbest", 0.0):
            entry["confirm"], entry["cbest"], entry["crule"] = True, weight, rule
        entry["weight"] += weight
        if weight > entry["best"]:
            entry["best"], entry["rule"] = weight, rule

    alarming = {f["rule"]["system"] for f in fired if f["rule"]["then"]["level"] in ("ORANGE", "RED")}
    for item in pending:
        rule = item["rule"]
        if alarming and rule["system"] not in alarming:
            continue  # with an ORANGE/RED finding up, do not point at unrelated systems' checks
        weight = _effective_cf(rule, facts)[0] * LEVEL_WEIGHT[rule["then"]["level"]]
        for fact in item["missing"]:
            if fact not in NOT_MEASURABLE:
                add(fact, rule, weight)
    for fire in fired:
        rule = fire["rule"]
        if rule["then"]["level"] not in ("ORANGE", "RED"):
            continue
        weight = fire["cf"] * LEVEL_WEIGHT[rule["then"]["level"]]
        for fact in rule.get("confirm_with") or []:
            if facts.get(fact) is None and fact not in NOT_MEASURABLE:
                add(fact, rule, weight, True)

    # Facts that would confirm a fired ORANGE/RED finding come first; pending-rule candidates only fill in
    # when nothing alarming is waiting for confirmation.
    pool = {f: c for f, c in candidates.items() if c.get("confirm")}
    for c in pool.values():
        c["rule"] = c["crule"]
    pool = pool or candidates
    ranked = sorted((c for c in pool.items() if c[1]["weight"] > 0), key=lambda c: -c[1]["weight"])
    if not ranked:
        return None
    fact, entry = ranked[0]
    return {
        "fact": fact,
        "label": FACT_LABELS.get(fact, fact.replace("_", " ").capitalize()),
        "reason": _reason(entry["rule"], kb),
    }


def assess(passport: dict, history: list[dict], kb: KB | None = None) -> dict:
    kb = kb or _default_kb()
    rules = kb.rules
    base = build_facts(passport, history)
    _apply_closed_world(base, rules)
    fired, facts, blocked = _run_with_guard(rules, base)

    hypotheses = _hypotheses(fired, kb)
    escalations = [{
        "rule": f["rule"]["id"],
        "label": f["rule"]["then"]["escalation"],
        "level": f["rule"]["then"]["level"],
        "system": f["rule"]["system"],
        "actions": _actions([f["rule"]], kb),
    } for f in fired if "escalation" in f["rule"]["then"]]

    systems: dict[str, str] = {}
    for system, level in [(h["system"], h["level"]) for h in hypotheses] + \
                         [(e["system"], e["level"]) for e in escalations]:
        systems[system] = _worst([systems.get(system, "GREEN"), level])

    pending = _pending(rules, facts, {f["rule"]["id"] for f in fired}, blocked)
    day = history[-1] if history else {}
    assessment = {
        "overall_level": _worst(systems.values()),
        "systems": systems,
        "hypotheses": hypotheses,
        "escalations": escalations,
        "pending": [{"rule": p["rule"]["id"], "missing": p["missing"]} for p in pending],
        "next_measurement": _next_measurement(pending, fired, facts, kb),
        "news2": news2(day),
        "packet": None,
    }
    if assessment["overall_level"] == "RED":
        assessment["packet"] = build_packet(assessment, passport, day)
    return assessment
