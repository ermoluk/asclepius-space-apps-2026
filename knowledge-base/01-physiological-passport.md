# 01 — Physiological Passport (pre-flight onboarding quiz)

> RU: «Физиологический паспорт» заполняется до полёта (примерно за 6–1 месяц). Часть отвечает сам космонавт в формате квиза, часть
> вносит лётный врач (анализы, денситометрия, ОКТ). Паспорт даёт системе (1) личные базовые значения вместо «земных норм»,
> (2) модификаторы правил (P-xx) и (3) личные контрмеры — что помогает именно этому человеку.

## Why it exists
- Space "normal" differs from Earth normal (BP −8–10 mmHg `[NORSK2015]`, plasma volume −10–17% `[CV-ER]`, mass −1–5% `[NUTR-ER]`), so the engine
  compares each astronaut with **their own pre-flight baseline** — the same approach NASA uses with pre-flight baselines in Standard Measures
  and WinSCAT `[STDMEAS]`, `[TB016]`.
- Some risks are personal: motion-sickness history, kidney-stone history, SANS-risk gene variants `[ZWART2016]`, latent herpes viruses
  (reactivation in flight `[RISK-IMMUNE]`), low bone density `[TB030]`.
- Behavioral countermeasures work best when personal (what helps *this* person relax) `[TB016]`.

## Format and timing
| Item | Design |
|---|---|
| When | First pass L-180 to L-90 days; update L-30; re-baseline vitals in the last 14 days before launch [T] |
| Length | 13 modules, each 2–5 min; progress bar; can pause; ~25 min self-report + clinician-entered modules |
| Who fills | 🧑‍🚀 astronaut (quiz) · 🩺 flight surgeon / lab · ⌚ device (7-day wearable baseline) |
| Output | `profile.baselines`, `profile.modifiers` (P-nn), `profile.countermeasures`, `profile.preferences` |
| Privacy | Behavioral and genetic modules visible only to astronaut, flight surgeon, psychologist (NASA keeps psychological conferences private `[TB016]`) |
| Re-test | Baselines refresh after each mission; post-flight comparison uses the same fields |

---

## Pre-flight data collection (L-21 months → launch)

> Timings are NASA **reference schedules** (ISS Standard Measures design, OCHMO surveillance brief, HRP data-share poster, Artemis II quarantine blog); real schedules vary by mission. L-XX = days before launch. Programme order: crew selection standards → Health Stabilization Program → in-mission care → post-landing care → lifetime surveillance (TREAT Astronauts Act) `[LHS-TB]`. The same list ships in the app as `PREFLIGHT_TIMELINE` (`preflight` in the passport).

| When | Session | What is collected | How | Who | Feeds | Source |
|---|---|---|---|---|---|---|
| L-21/18 mo and/or L-9/6 mo | Comprehensive eye exam | acuity, refraction, fields, contrast, retina, IOP, OCT, biometry, MRI; lighter exam at L-90/30 | clinic exam, MRI, OCT, 2-D ultrasound | 🩺 | G1, G2, G4; `P-03`, `P-13` | `LHS-TB` |
| < L-365 d | Ultrasound | abdominal and retroperitoneal (all), pelvic (females) | ultrasound | 🩺 | C18 | `LHS-TB` |
| Pre-mission (per mission) | Core medical exam | physical exam, ECG, neuro exam, hearing, nutrition, dental + orthopantomogram, H. pylori/TB, MRSA screen | clinic exam, audiogram, X-ray, labs, nasal swab | 🩺 | B11, C14, C16–C20; `P-24`, `P-26` | `LHS-TB` |
| Any time | Personality | IPIP-NEO | paper questionnaire | 🧑‍🚀 | J1 (tone only) | `STDMEAS` |
| L-270 and L-180 | Actigraphy + sleep logs | activity, light, sleep timing (2 × 2 weeks) | wrist actigraph, daily post-sleep survey | ⌚ + 🧑‍🚀 | H7, `sleep_hours`, chronotype; `P-09`, `P-10` | `STDMEAS` |
| L-270 and L-90 | Cellular profile | stress hormones, viral shedding, proteins, counts, cell types | blood 10 mL + saliva, same morning | lab | D1, D7; `P-04`, `P-23` | `STDMEAS` |
| L-270/180 and L-90/30 | Strength and fitness | isokinetic strength, functional fitness | dynamometry, tests | 🩺 | F6; `P-12` | `SPACEPHYS-2024` |
| L-225 | Sensorimotor familiarisation | practice run | same battery as L-90 | 🧑‍🚀 | (learning effect only) | `STDMEAS` |
| L-180 | Biochemical markers | CBC, CMP, chemistry, 24-h urine, exercise log | early-morning blood 15.7 mL, urine | lab | D8, D9; `lymphocytes_abs`, `hemoglobin`, `glucose` | `STDMEAS` |
| L-180 | Carotid IMT | carotid wall thickness | ultrasound + survey | 🩺 | B12 | `STDMEAS` |
| L-180 and L-60 | VO₂peak | aerobic capacity | graded exercise test | 🩺 | F5 | `SPACEPHYS-2024` |
| L-180/30 | DXA | BMD, body composition | DXA scan | 🩺 | F7; `body_mass`; `P-12` | `SPACEPHYS-2024` |
| L-180 and L-60 | Muscle quality | muscle imaging | imaging | 🩺 | F8 | `SPACEPHYS-2024` |
| L-120 and L-90 | Cognition battery | 10 tests (memory … vigilant attention) | computerised battery | 🧑‍🚀 | K3, `pvt_rt` | `STDMEAS` |
| L-90 | Sensorimotor baseline | sit-to-stand, tandem walk, recovery from prone, motion-sickness questionnaire | tests + questionnaire | 🩺 | I3; `P-01`, `P-25` | `STDMEAS` |
| L-90/30 | Dynamic posturography | balance on platform | neurovestibular platform | 🩺 | C15; `P-25` | `LHS-TB` |
| L-90 | Microbiome | skin, nose, saliva, stool | swabs, saliva ×4, stool kit | lab | D10; `P-24` | `STDMEAS` |
| L-90/30 | Medical labs and strength/diet | lab panel, lighter eye exam, IMTP, diet and supplement intake | blood, clinic tests, log | lab + 🩺 | D8, G4, F6, L5 | `LHS-TB`, `SPACEPHYS-2024` |
| ~L-14 d | Health Stabilization Program quarantine | mission simulations, medical checkouts, infection control | quarantine in Houston; can exit and re-enter 14 d before a new launch date | 🩺 + crew | last-14-day vitals re-baseline | `HSP-A2` |
| ~L-6 d | Move to KSC | checkouts continue | flight to Kennedy Space Center | crew | last-14-day vitals re-baseline | `HSP-A2` |

**Artemis II specifics:** ARCHeR actigraphy before, during and after flight (`[ARCHER]`); Standard Measures blood, saliva and urine before and after (blood not in flight), MRI eye/brain, balance, motion-sickness, vestibular and muscle tests (`[A2-STDMEAS]`); Immune Biomarkers — blood before/after, liquid saliva on Earth, dry-saliva booklets in flight (`[IMMUNE-BIOM]`); quarantine began 23 Jan 2026 (`[HSP-A2]`).

### Baseline derivation
- `sleep_hours` and chronotype ← median of the 2 × 14 actigraphy nights (L-270, L-180).
- `pvt_rt` / cognition ← L-90 run, **not** the L-120 familiarisation run.
- Lab baselines (CBC, CMP) ← L-180 biochemical markers plus L-90/30 medical labs; viral shedding ← L-270/L-90 cellular profile.
- Body mass and composition, BMD ← DXA L-180/30; aerobic baseline ← VO₂peak L-180/L-60; strength ← isokinetic and IMTP.
- Near/far acuity, OCT, IOP ← eye exams (L-9/6 mo and L-90/30); balance ← posturography L-90/30 plus sensorimotor L-90; hearing ← audiogram.
- Personality ← IPIP-NEO (NASA's instrument); BFI-2 may stay as an alternative.
- Each field names: source session (when), how it is measured, who enters it (🧑‍🚀/🩺/⌚/lab) and which baseline or modifier it feeds.

---

## Module A — Identity and mission profile (🧑‍🚀)
| Field | Question / input | Type | Used for |
|---|---|---|---|
| A1 | Crew role (Commander, Pilot, Mission Specialist, Crew Medical Officer) | choice | CMO gets crew view; escalation routing |
| A2 | Mission profile (ISS/LEO, lunar transit, lunar surface, Mars transit, Mars surface) | choice | comm-delay preset, dose-rate context, gravity rules |
| A3 | Planned mission length (days) | number | SANS / bone / nutrition time windows |
| A4 | Prior spaceflights: count, total days | number | `P-01`, experience flag |
| A5 | Problems on previous flights (motion sickness, back pain, headache, vision change, insomnia, orthostatic intolerance on landing, other) | multi | `P-01`, `P-02`, `P-14`, `P-19` |
| A6 | Prior occupational / spaceflight radiation dose (mSv), from dosimetry records 🩺 | number | `P-11` cumulative-dose rules `[STD3001-V1]` |
| A7 | Pre-flight session calendar (which sessions of the timeline below are done) 🩺 | checklist | progress of baseline collection `[LHS-TB]` |

## Module B — Anthropometrics and baseline vitals (🩺 + ⌚)
| Field | Input | Type | Used for |
|---|---|---|---|
| B1 | Height (cm) | number | BMI, EER energy need `[STD3001-V2]` |
| B2 | Pre-flight body mass (kg) — mean of last 3 measurements | number | `I-NUTR-body_mass` −5% / −7.7% rules `[NUTR-ER]` |
| B3 | Resting HR (bpm), 7-day wearable mean | number | personal HR baseline |
| B4 | Seated BP (mmHg), mean of 3 | number | personal BP baseline; `P-06` |
| B5 | Orthostatic test: BP/HR lying → standing 3 min | numbers | orthostatic baseline for landing `[MECK2001]` |
| B6 | SpO₂ (%) at rest | number | personal baseline (normal ≥96% `[NEWS2]`) |
| B7 | Oral temperature (°C), morning | number | fever relative to baseline |
| B8 | Respiratory rate (/min) | number | NEWS2 input |
| B9 | HRV (RMSSD, ms), 7-day morning mean ⌚ | number | stress/recovery trend (personal only) |
| B10 | Fasting glucose (mg/dL); HbA1c (%) 🩺 | number | glucose rules `[ADA-SOC]` |
| B11 | 12-lead resting ECG 🩺 | tracing + intervals | rhythm/conduction baseline `[LHS-TB]` |
| B12 | Carotid intima-media thickness (ultrasound, L-180) 🩺 | mm | CV baseline, `P-17` `[STDMEAS]` |

## Module C — Medical history (🧑‍🚀 + 🩺)
| Field | Question | Type | Used for |
|---|---|---|---|
| C1 | Chronic conditions (hypertension, asthma, migraine, GERD, allergic rhinitis, other) | multi | `P-05`, `P-06`, `P-16` |
| C2 | Previous kidney stone? | yes/no | `P-02` — kidney stones drive evacuations `[IMM-INC]`, urine Ca +50% in flight `[TB030]` |
| C3 | Migraine or recurrent headache — type, triggers, what helps | text+multi | `P-05` headache rules |
| C4 | Allergies: drugs, foods, environment; ever anaphylaxis? | multi + yes/no | `P-08` medication cross-check; anaphylaxis rule sensitivity `[ANAPH]` |
| C5 | Current medications and supplements | list | interaction notes, `P-08` |
| C6 | Surgeries / injuries (back, knee, shoulder, ankle) | list | `P-12` MSK rules |
| C7 | Dental status: last exam, fillings, crowns, root canals 🩺 | multi | dental rules (IMM has 7 dental conditions `[IMM-MYERS]`) |
| C8 | Vision: refraction (D), contact lenses, previous eye disease 🩺 | numbers | SANS baseline (hyperopic shift `[RISK-SANS]`) |
| C9 | Hearing baseline (audiogram) 🩺 | numbers | noise-induced hearing loss rule `[STD3001-V2]` |
| C10 | Blood type 🩺 | choice | emergency record |
| C11 | Vaccinations (influenza, VZV/shingles…) 🩺 | list | infection rules |
| C12 | Family history: early heart disease, clots (DVT/PE), glaucoma | multi | `P-17` jugular-clot and CV rules `[MARSHALL-GOEBEL2019]` |
| C13 | Menstrual cycle / contraception (if applicable) | choice | `C003` abnormal uterine bleeding, cycle-aware symptom notes |
| C14 | Neurological exam: gaze/ocular movements, finger-to-nose, drift, gait and station (Romberg, hop, tandem walk) 🩺 | findings | neuro baseline; `P-25` `[LHS-TB]` |
| C15 | Dynamic posturography (platform test, L-90/30) and sensorimotor battery (L-90) 🩺 | scores | balance baseline; `P-25` `[LHS-TB]`, `[STDMEAS]` |
| C16 | Audiogram 🩺 (detail of C9) | dB thresholds | `P-26` `[LHS-TB]` |
| C17 | Dental exam with orthopantomogram 🩺 (detail of C7) | findings + image | dental rules `[LHS-TB]` |
| C18 | Ultrasound imaging: abdominal and retroperitoneal (all), pelvic (females), before L-365 d 🩺 | findings | medical history baseline `[LHS-TB]` |
| C19 | H. pylori and tuberculosis testing 🩺 | result | infection history `[LHS-TB]` |
| C20 | MRSA nasal screen (and suppression if positive) 🩺 | result | `P-24` `[LHS-TB]` |

## Module D — Laboratory baseline (🩺, Inspiration4-compatible format `[OSD569]`, `[OSD575]`)
| Field | Analytes | Used for |
|---|---|---|
| D1 | CBC: WBC, neutrophils, lymphocytes, Hb, Hct, platelets | infection / anemia / radiation (lymphocytes) rules |
| D2 | CMP: glucose, Na, K, Cl, CO₂, Ca, BUN, creatinine, eGFR, albumin, ALT, AST, ALP, bilirubin | dehydration (Na > 145 `[NUTR-ER]`), kidney, liver baselines |
| D3 | 25-OH vitamin D (ng/mL) | `P-15`; target 35–90 ng/mL, < 20 = treat `[TB030]` |
| D4 | Lipids, hs-CRP | CV risk context |
| D5 | Urine: calcium, osmolality, volume | `P-02`; urine osmolality > 700 mOsm/kg flag `[NUTR-ER]` |
| D6 | Latent virus serostatus: EBV, VZV, HSV-1/2, CMV | `P-04` reactivation rules `[RISK-IMMUNE]`, `[CRUCIAN2016]` |
| D7 | Cellular profile: blood counts, cell types, stress hormones, **viral shedding** (blood + saliva, L-270 and L-90) lab | values | `P-04`, `P-23` `[STDMEAS]` |
| D8 | Biochemical markers L-180 (early-morning CBC, CMP, chemistry) and medical labs L-90/30 lab | values | main source of the CBC/CMP baselines `[STDMEAS]`, `[LHS-TB]` |
| D9 | 24-hour urine (shared with the medical team, L-180) lab | values | `P-02` `[STDMEAS]` |
| D10 | Microbiome baseline: body swabs, saliva ×4 over 7 days, stool (L-90) lab | profile | host-microbe baseline, `P-24` `[STDMEAS]` |

## Module E — Genetics (optional, explicit consent 🩺)
| Field | Variant | Used for |
|---|---|---|
| E1 | MTRR A66G (G allele), SHMT1 C1420T (C allele) | `P-03` — linked to higher SANS risk `[ZWART2016]`, `[RISK-SANS]` |
| E2 | Consent flags (store / do not store; share with whom) | privacy |

## Module F — Fitness and bone (🩺)
| Field | Input | Used for |
|---|---|---|
| F1 | VO₂max (ml/kg/min) | ≥ 32.9 for EVA `[STD3001-V1]`; in-flight ≥ 80% of this `[STD3001-V1]` |
| F2 | Strength tests (squat, bench, grip) | ≥ 80% of baseline in flight `[STD3001-V1]` |
| F3 | DXA hip/spine BMD and T-score | `P-12`; T ≥ −1.0 to fly `[TB030]` |
| F4 | Usual weekly exercise (type, minutes) — IPAQ-style `[IPAQ]` | countermeasure plan |
| F5 | VO₂peak at L-180 and L-60 🩺 | ml/kg/min | aerobic baseline `[SPACEPHYS-2024]` |
| F6 | Isokinetic strength (L-270/180, L-90/30) and isometric mid-thigh pull IMTP (L-90/30) 🩺 | N·m, N | strength baseline `[SPACEPHYS-2024]` |
| F7 | DXA bone mineral density and body composition (L-180/30) 🩺 | g/cm², % | `P-12` `[SPACEPHYS-2024]` |
| F8 | Muscle quality imaging (L-180 and L-60); dietary and supplement intake (L-90/30) 🩺 | imaging, log | `[SPACEPHYS-2024]` |

## Module G — Neuro-ocular baseline (🩺)
| Field | Input | Used for |
|---|---|---|
| G1 | Near and far visual acuity (each eye), on the same tablet chart used in flight | `R-EYE` rules (change vs baseline) |
| G2 | OCT total retinal thickness, IOP, fundus photo | SANS comparison at in-flight exams `[RISK-SANS]`, `[LEE2020]` |
| G3 | Headache-free baseline? Typical headache frequency per month | `P-05` |
| G4 | Comprehensive eye exam at L-21/18 months and/or L-9/6 months (MRI, refraction, fields, OCT, biometry, 2-D ultrasound); lighter exam at L-90/30 🩺 | exam set | SANS comparison `[LHS-TB]` |

## Module H — Sleep and chronotype (🧑‍🚀 + ⌚)
| Field | Question / instrument | Used for |
|---|---|---|
| H1 | Usual sleep duration and timing (work days / free days) — MCTQ-style `[MCTQ]` | personal sleep target; check-in windows `P-09` |
| H2 | Chronotype — morningness–eveningness `[MEQ]` | schedule advice `P-09` |
| H3 | Sleep quality last month — PSQI global score `[PSQI]` | `P-10` (PSQI > 5 = poor sleeper) |
| H4 | Insomnia symptoms — ISI `[ISI]` | `P-10` |
| H5 | Hypnotic use history; napping habit; caffeine (cups/day, latest time) | sleep countermeasures `[TB041]` |
| H6 | 7-day actigraphy baseline ⌚ | personal baseline sleep hours |
| H7 | Actigraphy 2 × 2 weeks (L-270 and L-180) with daily post-sleep survey ⌚ | median of the 28 nights | personal sleep hours, chronotype `[STDMEAS]` |

## Module I — Motion sickness susceptibility (🧑‍🚀)
| Field | Instrument | Used for |
|---|---|---|
| I1 | Motion Sickness Susceptibility Questionnaire, short form `[MSSQ]` | `P-01` (note: Earth susceptibility does not reliably predict space motion sickness `[RISK-SMV]` — so modifier is small) |
| I2 | Previous space motion sickness (from A5) | `P-01` (stronger modifier) |
| I3 | Sensorimotor battery at L-90 (sit-to-stand, tandem walk, recovery from prone; familiarisation at L-225) 🩺 | scores | baseline for landing and gravity transitions `[STDMEAS]` |

## Module J — Psychological profile (🧑‍🚀, private)
| Field | Instrument | Used for |
|---|---|---|
| J1 | IPIP-NEO (NASA Standard Measures `[STDMEAS]`); BFI-2 as an alternative `[BFI2]` — NASA collects personality once pre-flight | personalised tone of messages and countermeasures **only — never triage** [T] |
| J2 | Baseline PHQ-9 `[PHQ9]`, GAD-7 `[GAD7]` | personal baseline for weekly scores |
| J3 | Perceived Stress Scale `[PSS]` | baseline stress |
| J4 | "What helps you when you feel low / stressed / lonely?" (music, call family, exercise, journaling, gardening, Earth photos, being alone, talking to a crewmate) | `profile.countermeasures` — HRP lists journaling, plants, Earth photography, family contact `[TB016]`, `[RISK-BMED]` |
| J5 | Support contacts and preferred contact cadence | family-conference reminders |
| J6 | Early warning signs the astronaut knows in themselves ("when I'm overloaded I stop eating / sleep badly / get irritable") | `P-18` personal red flags |

## Module K — Cognitive baseline (🧑‍🚀 + test)
| Field | Test | Used for |
|---|---|---|
| K1 | 3-min PVT × 3 sessions (morning/evening) — like ISS Reaction Self Test `[PVT-BASNER]` | baseline mean RT and lapses |
| K2 | Optional Cognition-battery-style tests (memory, digit-symbol, 2-back) `[COGNITION]` | monthly comparison |
| K3 | Cognition battery (10 tests): familiarisation L-120, baseline L-90 🧑‍🚀 | scores | `pvt_rt` and cognition baseline `[STDMEAS]` |

## Module L — Nutrition and hydration (🧑‍🚀)
| Field | Question | Used for |
|---|---|---|
| L1 | Diet type, intolerances, foods disliked | menu preferences — letting crew pick foods improves intake `[NUTR-ER]` |
| L2 | Comfort foods / favourites | morale countermeasure |
| L3 | Usual fluid intake (L/day) | `P-02`; target ≥ 2.5 L `[STD3001-V2]` |
| L4 | Energy need (computed from age, mass, height, activity) | NASA EER equations `[STD3001-V2]` |
| L5 | Nutritional assessment 🩺 and dietary/supplement intake log (L-90/30) | log | `[LHS-TB]`, `[SPACEPHYS-2024]` |

## Module M — Preferences (🧑‍🚀)
| Field | Setting | Used for |
|---|---|---|
| M1 | Check-in times (aligned with sleep window) | scheduler |
| M2 | Notification style (quiet / standard); language | UX |
| M3 | Data sharing: who sees mood data (me / + CMO / + flight surgeon / + psychologist) | privacy |
| M4 | Gamification on/off; crew-level (not individual) leaderboard | engagement |
| M5 | Pre-flight sessions: reminders and consent per session (quarantine period included) | toggle | timeline scheduler |

---

## Passport modifiers (how answers change the rules)

| ID | Trigger in passport | Effect on the engine | Source |
|---|---|---|---|
| P-01 | Prior space motion sickness (A5) / high MSSQ (I1) | CF +0.15 for space-motion-sickness rules; pre-launch tip set; MSSQ alone: CF +0.05 | `[RISK-SMV]`, `[MSSQ]` [T] |
| P-02 | Kidney-stone history (C2) or high urine Ca (D5) | Fluid target 3.0 L/day [T]; flank pain → RED instead of ORANGE; weekly hydration review | `[TB030]`, `[IMM-INC]` |
| P-03 | SANS-risk alleles (E1) or previous vision change (A5) | Near-vision self-test weekly from day 14 (instead of day 30); SANS rules CF +0.1 | `[ZWART2016]`, `[RISK-SANS]` |
| P-04 | VZV/HSV/EBV seropositive (D6) | Rash / cold-sore rules CF +0.1; stress + poor sleep → prevention tip | `[RISK-IMMUNE]`, `[CRUCIAN2016]` |
| P-05 | Migraine history (C1/C3) | Headache matching personal pattern → YELLOW with own plan; new pattern or red flags keep full rules | `[SNNOOP10]` |
| P-06 | Hypertension history or baseline ≥ 130/80 (B4) | BP stage-1 values trigger YELLOW recheck | `[AHA-BP]` |
| P-07 | Athletic resting HR < 55 (B3) | Personal layer explains low HR; NEWS2 tile shown unchanged | `[NEWS2]` [T] |
| P-08 | Allergies / medications (C4, C5) | Medication suggestions show allergy warning; anaphylaxis history → allergic-reaction rule level +1 | `[ANAPH]` |
| P-09 | Chronotype & sleep timing (H1, H2) | Check-in windows and light-schedule advice aligned to the astronaut | `[MEQ]`, `[TB041]` |
| P-10 | Poor sleeper (PSQI > 5 or ISI ≥ 15) | Sleep-deficit rule fires after 2 nights instead of 3 | `[PSQI]`, `[ISI]` [T] |
| P-11 | Prior radiation dose (A6) | Added to cumulative dose for career-limit rules | `[STD3001-V1]` |
| P-12 | Low BMD (T < −1.0 at any site) or prior fracture/injury (F3, C6) | MSK trauma rules: lower threshold for "possible fracture"; extra resistance-exercise emphasis | `[TB030]` |
| P-13 | Refraction / contact lenses (C8) | Near-vision change interpreted vs corrected baseline; contact-lens eye-infection tips | `[RISK-SANS]` |
| P-14 | Back pain on previous flight (A5) or back injury (C6) | Early back-pain countermeasure plan from day 1 | `[KERSTMAN2012]` |
| P-15 | Vitamin D < 35 ng/mL (D3) | Supplement reminder per flight surgeon; bone-risk tile | `[TB030]` |
| P-16 | Asthma / allergic rhinitis (C1) | Respiratory rules: wheeze → ORANGE; congestion beyond adaptation window → own plan | [T] |
| P-17 | Family history of clots (C12) | Jugular-clot rule CF +0.1; neck-symptom question added weekly from day 30 | `[MARSHALL-GOEBEL2019]` [T] |
| P-18 | Personal early-warning signs (J6) | Added as custom behavioral indicators (e.g. "skipped meals 2 days" → check-in prompt) | `[TB016]` [T] |
| P-19 | Orthostatic intolerance on previous landing (A5) or abnormal B5 | Landing-phase countermeasures (fluid loading, compression garment) emphasised; orthostatic rules CF +0.1 | `[CV-ER]`, `[MECK2001]` |
| P-23 | Viral shedding detected at baseline (D7, L-270/L-90) | Immune-rash / zoster rules more sensitive: CF +0.1 [T] | `[STDMEAS]`, `[RISK-IMMUNE]` [T] |
| P-24 | MRSA carrier on nasal screen (C20) | Skin-infection rules more sensitive: CF +0.1; hygiene tip set [T] | `[LHS-TB]` [T] |
| P-25 | Abnormal baseline posturography / sensorimotor (C15, I3) | Vestibular rules more sensitive at gravity transitions: CF +0.1 [T] | `[LHS-TB]`, `[STDMEAS]`, `[RISK-SMV]` [T] |
| P-26 | Baseline hearing loss on audiogram (C16) | Hearing rule judged relative to the audiogram, not a population norm [T] | `[LHS-TB]`, `[STD3001-V2]` [T] |

> P-20…P-22 are reserved for the reproductive-health follow-up. P-23…P-26 are **documentation only** — no engine rule changes yet.
