# Knowledge Base — Astronaut Health Expert System

Version 0.2 · 2026-11-14 · Status: documentation (no code yet). Language: English (content goes straight into the app UI).

> RU: Это база знаний экспертной системы. Здесь описано всё, что система «знает»: какие данные собирает (паспорт, ежедневные опросы,
> показатели), какие состояния распознаёт (100 состояний NASA IMM + 15 дополнительных), по каким правилам (190+), что советует и на какие
> источники опирается каждое правило. Раздел «Methodology» ниже объясняет, как база собиралась и как её расширять.

---

## Files

| File | What it contains | Size |
|---|---|---|
| `01-physiological-passport.md` | Pre-flight onboarding quiz: 13 modules, ~120 fields, how each answer personalises the rules | 13 modules |
| `02-daily-checkins.md` | Morning / evening self-checks (Apple-Health-style state of mind + physical state), event-triggered and weekly checks, scoring, gamification | 4 check-in types |
| `03-indicators.md` | Every input the engine reads: vitals, self-report, tests, labs, environment, mission context — unit, how measured in space, frequency, thresholds | 60+ indicators |
| `04-conditions.md` | Diagnosis catalogue: all 100 NASA IMM conditions + 15 HRP-derived conditions, with features, max triage level, confirm-with | 115 conditions |
| `05-rules.md` | IF-THEN rules with certainty factors, triage level, actions, references; personal modifiers from the passport | 190+ rules |
| `06-scores-and-questionnaires.md` | Validated scores and questionnaires embedded in the system (NEWS2, qSOFA, GCS, BE-FAST, Ottawa, Centor, PHQ-9, GAD-7, KSS…) | 30+ instruments |
| `07-actions.md` | Countermeasure / action library referenced by rules | 80+ actions |
| `08-references.md` | Bibliography with keys used everywhere in the KB | 90+ references |
| `09-worked-examples.md` | Step-by-step traces: inputs → fired rules → certainty math → output | 4 scenarios |

---

## Core concepts

### Triage levels
| Level | Meaning | App behaviour |
|---|---|---|
| 🟢 `GREEN` | Nominal, or expected space adaptation | Info + tip, no alert |
| 🟡 `YELLOW` | Self-care countermeasure | Show actions; recheck in 24 h |
| 🟠 `ORANGE` | Attention: repeat measurement, inform Crew Medical Officer (CMO), add to daily downlink | "Confirm with…" prompt; report item |
| 🔴 `RED` | Possible serious condition | Immediate CMO alert + flight-surgeon packet; onboard protocol first when comm delay > 5 min [T] |

Overall status = worst active level. Levels never go down automatically within 24 h of a RED without a recheck [T].

### Evidence tags (on every threshold and rule)
| Tag | Meaning |
|---|---|
| **[N]** | Number/claim stated in a NASA source (standard, technical brief, evidence report, HRP page, IMM) |
| **[C]** | Validated clinical score or guideline (NEWS2, AHA, ADA, Sepsis-3, Ottawa rules…) |
| **[S]** | Peer-reviewed spaceflight study (Barger 2014, Crucian 2016, Norsk 2015…) |
| **[T]** | Team choice / heuristic — must be shown as such and tuned with a flight surgeon |

### Certainty factors (CF)
Each rule carries a CF in (0, 1]. Several rules supporting the same hypothesis combine MYCIN-style: `CF = a + b·(1 − a)`.
CF values are **team heuristics [T]** set with this scale:
| CF | When used |
|---|---|
| 0.9–1.0 | Validated score cut-off or unambiguous red flag (e.g. qSOFA ≥ 2, PHQ-9 item 9 > 0, glucose < 54 mg/dL) |
| 0.7–0.8 | Strong association documented in NASA evidence or a clinical decision rule |
| 0.5–0.6 | Suggestive pattern, needs confirmation |
| 0.3–0.4 | Weak or contextual support (raises a hypothesis for monitoring) |

### IDs
`C001–C100` NASA IMM conditions (in the order of Myers et al.) · `X01–X15` HRP-derived extra conditions ·
`R-<SYS>-nn` rules · `P-nn` passport modifiers · `A-<SYS>-nn` actions · `I-<group>-<name>` indicators · reference keys like `[TB004]`, `[NEWS2]`.

Systems: `CV` cardiovascular · `RESP` respiratory · `NEURO` neurology/head · `EYE` eyes/SANS · `ENT` ear-nose-throat · `DENT` dental ·
`GI` gastro-intestinal · `GU` genito-urinary · `MSK` musculoskeletal · `VEST` vestibular · `SKIN` skin · `IMMUNE` infection/allergy · `BEHAV` behavioral ·
`SLEEP` sleep/fatigue · `NUTR` nutrition/metabolic · `RAD` radiation · `ENV` environment/toxic · `EVA` spacewalk · `TRAUMA` injuries.

---

## Methodology — how this knowledge base was built (and how to extend it)

1. **Hazards → risks.** Start from NASA HRP's 5 hazards and 17 risks `[HRP-HAZ]`, `[HRP-RISKS]`. Every risk becomes a body-map system and a
   group of hypotheses, so every alert can say *which spaceflight hazard* is behind it.
2. **Diagnosis catalogue.** Use NASA's Integrated Medical Model list of 100 in-flight conditions `[IMM-MYERS]` as the master list, so the system
   never invents diagnoses NASA does not plan for. Add HRP-derived states that are not "conditions" but matter for performance (sleep deficit,
   cumulative radiation, deconditioning).
3. **Observable features.** For each condition list only what an astronaut can observe or measure onboard: symptoms, vitals, simple tests
   (near-vision chart, reaction test), devices NASA actually flies `[STDMEAS]`, `[TEMPUS]`, `[CHECS]`.
4. **Thresholds by source hierarchy.** NASA standard `[STD3001-V1/V2]` → NASA evidence `[HRR]`, technical briefs → peer-reviewed spaceflight
   studies → validated clinical scores → clinical guidelines → team choice. The highest available source wins; the tag records which one.
5. **One rule = one claim.** Each rule states one pattern → one hypothesis, with CF, level, actions and at least one reference.
6. **Space adjustment.** Where microgravity changes the "normal" (BP −8–10 mmHg `[NORSK2015]`, plasma volume, sleep ~6 h `[BARGER2014]`), rules
   use the astronaut's personal baseline from the passport and rolling 14-day medians instead of Earth population norms.
7. **Reassure, don't alarm.** The 9 IMM "space adaptation syndrome" conditions are expected early in flight; GREEN rules explain them, guarded by
   red-flag rules so a real emergency is never labelled "expected".
8. **Personalisation.** Passport answers act as modifiers (`P-nn`): they shift CFs, thresholds or check frequency for that astronaut only.
9. **Validation plan (future).** Each rule gets a reviewer column (flight surgeon sign-off), replay against synthetic scenarios
   (`09-worked-examples.md`), and a change log. Thresholds marked [T] are the first to review.
10. **Honesty.** NASA does not publish in-flight alarm thresholds for most vital signs; those come from clinical sources and are labelled [C].
    The system is decision support for crew self-assessment, not a diagnosis.

### Adding a new rule (checklist)
- [ ] Linked hypothesis exists in `04-conditions.md` (or add it)
- [ ] Every indicator used exists in `03-indicators.md`
- [ ] Threshold has an evidence tag and a reference key from `08-references.md`
- [ ] Level follows the triage table; RED only for time-critical risk
- [ ] Actions point to `07-actions.md`; no drug doses (use "per onboard medical checklist / CMO")
- [ ] A worked example or test scenario covers it
