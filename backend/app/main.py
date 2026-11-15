"""FastAPI app: knowledge, demo scenarios, passport derivation and assessment."""
import math
from datetime import date
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

from . import data as warehouse
from . import importer
from .engine import _default_kb, assess
from .passport import derive_passport
from .scenarios import get_scenario, list_scenarios

app = FastAPI(title="Asclepius - Astronaut Health Expert System")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"],
                   allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(RequestValidationError)
def _validation_error(_request, exc: RequestValidationError):
    # Drop echoed input/ctx: NaN/inf inputs would make the default 422 body un-serialisable (500).
    detail = [{"loc": list(e.get("loc", ())), "msg": str(e.get("msg", "")), "type": str(e.get("type", ""))}
              for e in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": detail})


def _f(lo=None, hi=None):
    return Field(default=None, ge=lo, le=hi)


class DayRecord(BaseModel):
    model_config = ConfigDict(extra="allow", allow_inf_nan=False)

    mission_day: int | None = _f(0)
    # vitals
    hr_rest: float | None = _f(20, 250)
    bp_sys: float | None = _f(40, 300)
    bp_dia: float | None = _f(40, 300)
    spo2: float | None = _f(50, 100)
    temp: float | None = _f(30, 43)
    resp_rate: float | None = _f(4, 80)
    glucose: float | None = _f(20, 600)
    glucose_fasting: bool | float | None = None
    on_oxygen: bool | None = None
    confusion: bool | None = None
    # self-report
    sleep_hours: float | None = _f(0, 24)
    sleep_quality: float | None = _f(1, 5)
    kss: float | None = _f(1, 9)
    physical_state: float | None = _f(1, 7)
    mood_valence: float | None = _f(1, 7)
    mood_labels: list[str] | None = None
    team_cohesion: float | None = _f(1, 7)
    workload: float | None = _f(0, 10)
    fatigue: float | None = _f(0, 10)
    fluid_intake: float | None = _f(0, 10)
    food_intake_pct: float | None = _f(0, 200)
    exercise_min: float | None = _f(0, 600)
    body_mass: float | None = _f(20, 250)
    lymphocytes_abs: float | None = _f(0, 20000)
    hemoglobin: float | None = _f(0, 30)
    wbc: float | None = _f(0, 100)
    sodium: float | None = _f(100, 180)
    potassium: float | None = _f(1, 10)
    creatinine: float | None = _f(0, 20)
    crp: float | None = _f(0, 500)
    urine_osm: float | None = _f(0, 2000)
    urine_color: float | None = _f(1, 8)
    hrv_rmssd: float | None = _f(1, 300)
    spe_event_id: str | None = Field(default=None, max_length=64)
    # tests
    pvt_rt: float | None = _f(100, 2000)
    near_acuity_decline: float | None = _f(0, 20)
    # environment
    co2_1h: float | None = _f(0, 20)
    co2_7d: float | None = _f(0, 20)
    pio2: float | None = _f(0, 500)
    cabin_temp: float | None = _f(0, 60)
    spe_alert: bool | None = None
    hours_since_spe: float | None = _f(0, 10000)
    dose_cumulative: float | None = _f(0, 100000)
    dose_today: float | None = _f(0, 100000)
    # context
    phase: str | None = None
    post_eva_hours: float | None = _f(0, 10000)
    hours_since_transition: float | None = _f(0, 10000)
    comm_delay_s: float | None = _f(0, 5000)
    comm_los: StrictBool | None = None
    # raw keys used by rules
    awake_hours: float | None = _f(0, 200)
    work_hours: float | None = _f(0, 24)
    phq9: float | None = _f(0, 27)
    phq9_item9: float | None = _f(0, 3)
    gad7: float | None = _f(0, 21)
    who5: float | None = _f(0, 100)
    ucla3: float | None = _f(3, 9)
    centor: float | None = _f(0, 5)
    ecg_rhythm: str | None = None
    cabin_alt: float | None = _f(0, 20000)
    constipation_days: float | None = _f(0, 365)
    gcs: float | None = _f(3, 15)
    urine_nitrite_le: bool | None = None
    urine_blood: bool | None = None
    depress_alarm: bool | None = None
    ammonia_alarm: bool | None = None
    work_days_in_row: float | None = _f(0, 365)
    befast_positive: bool | None = None
    nosebleed_minutes: float | None = _f(0, 1000)
    pulse_irregular: bool | None = None
    vomiting_hours: float | None = _f(0, 1000)
    vomiting_episodes: float | None = _f(0, 1000)
    abdominal_pain_location: str | None = None
    amnesia_minutes: float | None = _f(0, 100000)
    dangerous_mechanism: bool | None = None

    @model_validator(mode="after")
    def _sym_bool(self):
        for k, v in (self.model_extra or {}).items():
            if k.startswith("sym_") and v is not None and not isinstance(v, bool):
                raise ValueError(f"{k} must be a boolean")
            if isinstance(v, float) and not math.isfinite(v):
                raise ValueError(f"{k} must be finite")
        return self


class Astronaut(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str = "CM-1"
    name: str = ""
    role: str = ""


class Mission(BaseModel):
    model_config = ConfigDict(extra="allow", allow_inf_nan=False)
    profile: str = ""
    vehicle: str = ""
    comm_delay_s: float = Field(default=0, ge=0, le=5000)


class PreflightSession(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    when: str
    what: str
    how: str
    feeds: list[str]
    source: str


class Range(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    lo: float | None = None
    hi: float | None = None
    n: int | None = Field(default=None, ge=0)
    ready: bool | None = None
    rebase14: float | None = None


class Passport(BaseModel):
    model_config = ConfigDict(extra="allow", allow_inf_nan=False)
    astronaut: Astronaut = Astronaut()
    mission: Mission = Mission()
    baselines: dict[str, float] = {}
    personal_ranges: dict[str, Range] = {}  # p10..p90 of the six-month pre-flight passport
    lab_ranges: dict[str, Range] = {}       # lab reference ranges (Inspiration4 format)
    passport_ref: str | None = Field(default=None, max_length=50)
    modifiers: list[str] = []
    countermeasures: list[str] = []
    preflight: list[PreflightSession] | None = None


class AssessRequest(BaseModel):
    passport: Passport
    history: list[DayRecord] = Field(min_length=1, max_length=60)


class DeriveAnswers(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    id: str | None = Field(default=None, max_length=50)
    name: str | None = Field(default=None, max_length=100)
    role: str | None = Field(default=None, max_length=100)
    mission_profile: Literal["leo", "lunar", "mars"] | None = None
    prior_motion_sickness: StrictBool | None = None
    kidney_stone: StrictBool | None = None
    sans_risk_or_vision_change: StrictBool | None = None
    migraine: StrictBool | None = None
    poor_sleeper: StrictBool | None = None
    helpers: list[str] | None = None
    baselines: dict[str, float] | None = None
    # new_member: registered in the "My crew" mode, no six-month passport (population baselines).
    new_member: StrictBool | None = None
    # passport_ref: keep this crew member's six-month passport when the quiz edits an existing member.
    passport_ref: str | None = Field(default=None, max_length=50)


class DeriveRequest(BaseModel):
    answers: DeriveAnswers = DeriveAnswers()


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/knowledge")
def knowledge():
    kb = _default_kb()
    return {
        "counts": {"conditions": len(kb.conditions), "actions": len(kb.actions),
                   "references": len(kb.references), "rules": len(kb.rules)},
        "conditions": kb.conditions, "actions": kb.actions, "references": kb.references,
    }


@app.get("/api/scenarios")
def scenarios():
    return list_scenarios()


@app.get("/api/scenarios/{scenario_id}")
def scenario(scenario_id: str):
    try:
        return get_scenario(scenario_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"unknown scenario: {scenario_id}")


@app.post("/api/assess")
def post_assess(req: AssessRequest):
    history = [d.model_dump(exclude_none=True) for d in req.history]
    return assess(req.passport.model_dump(), history)


@app.get("/api/datasets")
def datasets():
    """Every data source (catalog) with how many warehouse rows it contributes, by provenance."""
    return warehouse.datasets_summary()


@app.get("/api/crew")
def crew_list():
    out = []
    for cid in warehouse.crew_ids():
        doc = warehouse.crew_passport(cid)
        out.append({k: doc[k] for k in ("crew_id", "name", "role", "sex", "age", "modifiers")})
    return out


@app.get("/api/crew/{crew_id}/passport")
def crew_passport(crew_id: str):
    """Six-month pre-flight passport: fields (with provenance), sessions, donors and daily series."""
    doc = warehouse.crew_passport(crew_id) if crew_id in warehouse.crew_ids() else None
    if doc is None:
        raise HTTPException(status_code=404, detail=f"no passport for crew member: {crew_id}")
    return doc


@app.get("/api/space-weather/sep")
def space_weather_sep():
    """Snapshot of real solar energetic particle events (NASA DONKI)."""
    return {"source": "NASA DONKI", "events": list(warehouse.sep_events())}


class BiodoseRequest(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    fold_changes: dict[str, float] = Field(min_length=1, max_length=50)


@app.get("/api/biodosimetry")
def biodosimetry_model():
    """Lab-on-chip gene panel (NASA OSDR OSD-410): model summary and held-out real samples for the demo."""
    bio = warehouse.biodosimetry_model()
    if bio is None:
        raise HTTPException(status_code=404, detail="biodosimetry model not built (run the data pipeline)")
    return bio


@app.post("/api/biodosimetry/classify")
def biodosimetry_classify(req: BiodoseRequest):
    out = warehouse.biodose_classify(req.fold_changes)
    if out is None:
        raise HTTPException(status_code=404, detail="biodosimetry model not built (run the data pipeline)")
    if "error" in out:
        raise HTTPException(status_code=422, detail=out["error"])
    return out


@app.post("/api/passport/derive")
def post_derive(req: DeriveRequest):
    return derive_passport(req.answers.model_dump(exclude_none=True))


class ImportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    filename: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=3_000_000)
    launch_date: date | None = None
    name: str | None = Field(default=None, max_length=100)


@app.post("/api/import/parse")
def post_import(req: ImportRequest):
    """A crew member's own file (CSV table or six-month passport JSON) -> passport document, engine inputs,
    check-in days and a report. Nothing is stored: the browser keeps the result (the "My crew" mode)."""
    try:
        return importer.parse(req.filename, req.content, req.launch_date, (req.name or "").strip() or None)
    except importer.ImportProblem as e:
        raise HTTPException(status_code=422, detail=str(e))
