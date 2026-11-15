# 05 — Rules

Format: **IF** pattern → **THEN** hypothesis (CF) · level · actions (`07-actions.md`) · references (`08-references.md`).
Levels: 🟢 GREEN · 🟡 YELLOW · 🟠 ORANGE · 🔴 RED. "esc" = escalation rule (sets level without a single hypothesis).
Indicator names drop the `I-…-` prefix for readability (`sleep_hours` = `I-SLEEP-sleep_hours`). `baseline`, `days()`, `count_7d()`,
`news2_total`, `qsofa`, `adaptation_window`, `red_flag_any()` are derived facts (`03-indicators.md` §12).
**All CF values are team heuristics [T]** following the scale in `00-README.md`; thresholds carry their own evidence tags in `03-indicators.md`.

## Engine conventions
1. Forward chaining until no new facts (rules may use hypotheses as inputs, e.g. R-SLP-05 uses X01).
2. Same hypothesis from several rules → `CF = a + b(1 − a)`; level = highest level among fired rules.
3. **Red-flag guard:** GREEN "expected adaptation" rules (marked †) do not fire if `red_flag_any(system)` is true.
4. Passport modifiers `P-nn` (`01-physiological-passport.md`) adjust CF / thresholds before evaluation.
5. Every RED creates a flight-surgeon packet; with `comm_delay_s > 300` the packet follows onboard first-response actions [T].
6. A missing indicator never counts as normal: the rule is "pending" and the engine asks for it (next best measurement).

---

## SLEEP — sleep and fatigue (HRP: Risk of Inadequate Sleep and Irregular Schedules)
| ID | IF | THEN (CF) | Lvl | Actions | Refs |
|---|---|---|---|---|---|
| R-SLP-01 | `sleep_hours ≤ 6` for `days ≥ 3` | X01 Sleep deficit (0.8) | 🟡 | A-SLP-01, A-SLP-02, A-SLP-03, A-SLP-05 | `[RISK-SLEEP]`, `[TB041]`, `[BARGER2014]`, `[JONES2022]` |
| R-SLP-02 | P-10 AND `sleep_hours < 6` for `days ≥ 2` | X01 (0.7) | 🟡 | A-SLP-01, A-SLP-02 | `[PSQI]`, `[ISI]` |
| R-SLP-03 | `sleep_quality ≤ 2` on `count_7d ≥ 3` | X01 (0.5) | 🟡 | A-SLP-05, A-SLP-02 | `[STDMEAS]` |
| R-SLP-04 | `kss ≥ 7` | X02 Fatigue impairing performance (0.6) | 🟠 | A-GEN-08, A-SLP-04 | `[KSS]` |
| R-SLP-05 | X01 AND (`pvt_rt > baseline × 1.15` OR `pvt_lapses ≥ 2 × baseline`) | X02 (0.75) | 🟠 | A-GEN-08, A-SLP-04, A-GEN-02 | `[PVT-BASNER]`, `[RST-ISS]` |
| R-SLP-06 | `fatigue (Samn-Perelli) ≥ 5` before a safety-critical task | X02 (0.7) | 🟠 | A-GEN-08 | `[SAMN-PERELLI]` |
| R-SLP-07 | `awake_hours ≥ 16` OR `work_hours > 16` OR > 6 work days in a row | X02 (0.5) | 🟡 | A-SLP-06 | `[RISK-SLEEP]` |
| R-SLP-08 | `workload ≥ 8` on `count_7d ≥ 3` AND `sleep_hours < 6` | X02 (0.5) | 🟡 | A-SLP-06, A-BEH-05 | `[TB-COGWL]`, `[BEDFORD]` |
| R-SLP-09 † | `adaptation_window` AND difficulty sleeping | C062 Insomnia (SAS) (0.7) | 🟢 | A-SLP-05, A-SLP-02 | `[IMM-INC]`, `[BARGER2014]` |
| R-SLP-10 | NOT `adaptation_window` AND (`sleep_hours < 6` OR `sleep_quality ≤ 2`) on ≥ 7 of 14 days | C064 Late insomnia (0.7) | 🟡 | A-SLP-01, A-SLP-02, A-SLP-03, A-SLP-05, A-SLP-07 | `[RISK-SLEEP]`, `[ISI]` |
| R-SLP-11 | `hypnotic_use ≥ 4` of 7 nights | C064 (0.5) | 🟡 | A-SLP-07 | `[BARGER2014]` |
| R-SLP-12 | `caffeine_late` AND `sleep_hours < 6` | X01 (0.3) | 🟡 | A-SLP-03 | `[TB041]` |
| R-SLP-13 | `sleep_hours < 6` AND (`noise_dose > 100` OR `cabin_temp` outside 18–27 °C) | X01 (0.4) | 🟡 | A-ENV-03, A-SLP-05 | `[STD3001-V2]`, `[TB041]` |

## BEHAV — behavioral health (HRP: Behavioral Conditions; Inadequate Teamwork)
| ID | IF | THEN (CF) | Lvl | Actions | Refs |
|---|---|---|---|---|---|
| R-BEH-01 | `mood_valence ≤ 2` on `count_7d ≥ 5` | C038 Depression (0.6) | 🟠 | A-BEH-01, A-BEH-03, A-BEH-10 | `[RISK-BMED]`, `[APPLE-SOM]` |
| R-BEH-02 | `phq9 ≥ 10` | C038 (0.75) | 🟠 | A-BEH-01, A-BEH-03 | `[PHQ9]`, `[TB016]` |
| R-BEH-03 | `phq9 ≥ 20` | C038 (0.9) | 🟠 | A-BEH-01 (within 24 h), A-GEN-02 | `[PHQ9]` |
| R-BEH-04 | `gad7 ≥ 10` | C018 Anxiety (0.75) | 🟠 | A-BEH-01, A-BEH-09 | `[GAD7]`, `[TB016]` |
| R-BEH-05 | "anxious" or "overwhelmed" label on `count_7d ≥ 3` | C018 (0.4) | 🟡 | A-BEH-09, A-BEH-10 | `[APPLE-SOM]`, `[GAD7]` |
| R-BEH-06 | `team_cohesion ≤ 2` on `count_7d ≥ 3` | X12 Team conflict (0.6) | 🟡 | A-BEH-07 | `[RISK-TEAM]`, `[STDMEAS]` |
| R-BEH-07 | "lonely"/"homesick" on `count_7d ≥ 3` OR `ucla3 ≥ 6` | X13 Loneliness (0.6) | 🟡 | A-BEH-02, A-BEH-06 | `[UCLA3]`, `[TB016]` |
| R-BEH-08 | `family_contact_days > 14` | X13 (0.3) | 🟡 | A-BEH-02 | `[TB016]` |
| R-BEH-09 | `phq9_item9 > 0` OR `self_harm_thoughts` OR `hallucinations` OR `feeling_unsafe_or_unable_to_cope` | C024 Behavioral emergency (1.0) | 🔴 | A-BEH-08 | `[PHQ9]`, `[TB016]`, `[IMM-MYERS]` |
| R-BEH-10 | X01 AND `mood_valence ≤ 2` | C038 (0.3) — "fix sleep first" | 🟡 | A-SLP-01, A-BEH-03 | `[TB016]` |
| R-BEH-11 | `emotion_now = 1` on 3 days in a row | C038 (0.4) | 🟡 | A-BEH-03, A-BEH-01 | `[APPLE-SOM]` |
| R-BEH-12 | `who5 ≤ 28` | C038 (0.6) | 🟠 | A-BEH-10 | `[WHO5]` |
| R-BEH-13 | `pss` rise ≥ 5 vs passport AND `sleep_hours < 6` | C018 (0.3) | 🟡 | A-BEH-09, A-SLP-01 | `[PSS]` |
| R-BEH-14 | P-18 personal early-warning sign present on 2 days | C038 / C018 (0.4) | 🟡 | A-BEH-03 | `[TB016]` |
| R-BEH-15 | `workload ≥ 8` on `count_7d ≥ 3` AND `mood_valence ≤ 3` | C018 (0.4) | 🟡 | A-BEH-05, A-SLP-06 | `[TB-COGWL]` |
| R-BEH-16 | `cognition z ≤ −1.5` AND NOT X01 | X14 Cognitive decline (0.6) | 🟠 | A-GEN-01, A-ENV-01, A-GEN-06 | `[COGNITION]`, `[TB016]` |
| R-BEH-17 | X14 AND `co2_1h > 3.0` | X14 environmental cause (0.5) | 🟡 | A-ENV-01 | `[TB004]` |
| R-BEH-18 | `anxiety_or_panic` reported now | C018 (0.6) | 🟡 | A-BEH-09, A-BEH-03 | `[TB016]` |

## SELF — self-assessment prompts
| ID | IF | THEN | Lvl | Actions | Refs |
|---|---|---|---|---|---|
| R-SELF-01 | `physical_state ≤ 2` on 2 consecutive days | esc: guided symptom interview | 🟡 | A-GEN-13 | `[SRH]` |
| R-SELF-02 | `physical_state` drop ≥ 2 vs baseline AND no symptom reported | esc: ask HR + temperature + body-map check | 🟡 | A-GEN-13, A-GEN-01 | `[SRH]` |

## NEURO — head and nervous system
| ID | IF | THEN (CF) | Lvl | Actions | Refs |
|---|---|---|---|---|---|
| R-NEU-01 | `headache` AND `co2_1h > 3.0` | C051 Headache (CO₂) (0.75) | 🟡 | A-ENV-01, A-GEN-05 | `[TB004]`, `[STD3001-V2]` |
| R-NEU-02 | `headache` AND `co2_7d > 2.5` | C051 (0.5) | 🟡 | A-ENV-01 | `[TB004]` |
| R-NEU-03 † | `headache` AND `adaptation_window` | C053 Headache (SAS) (0.7) | 🟢 | A-GEN-04 | `[HEADACHE2024]`, `[IMM-INC]` |
| R-NEU-04 | `headache` AND NOT `adaptation_window` AND NOT (`co2_1h > 3.0` OR `co2_7d > 2.5`) | C052 Headache (late) (0.5) | 🟡 | A-NEU-04, A-CV-05 | `[SNNOOP10]`, `[IMM-MYERS]` |
| R-NEU-05 | `headache` with any red flag: sudden "worst ever", fever + neck stiffness, neuro deficit, after head injury, new pattern after day 30 | esc: secondary headache | 🔴 | A-NEU-04, A-NEU-01, A-GEN-03 | `[SNNOOP10]` |
| R-NEU-06 | `headache` AND P-05 AND matches personal migraine pattern AND no red flag | C052 (0.6) — own plan | 🟡 | A-GEN-04, A-BEH-03 | `[SNNOOP10]` |
| R-NEU-07 | any BE-FAST item positive OR `weakness_one_side` OR `facial_droop` OR `speech_difficulty` | C090 Stroke (0.85) | 🔴 | A-NEU-01, A-GEN-10, A-GEN-03 | `[BEFAST]` |
| R-NEU-08 | `seizure_witnessed` | C079 Seizures (0.95) | 🔴 | A-NEU-03, A-GEN-10 | `[IMM-MYERS]` |
| R-NEU-09 | `fainting` AND `phase` = gravity transition | X03 Orthostatic intolerance (0.7) | 🟠 | A-CV-01, A-CV-02 | `[CV-ER]`, `[MECK2001]` |
| R-NEU-10 | `fainting` NOT at gravity transition | C020 AFib (0.4) + esc | 🟠 | A-CV-04, A-GEN-02 | `[CV-ER]` |
| R-NEU-11 | `tingling_numbness` localised to a suit-contact area, NOT `post_eva_hours ≤ 24` with DCS features | C075 Paresthesias (0.5) | 🟡 | A-EVA-03, A-GEN-05 | `[IMM-MYERS]`, `[RISK-EVA]` |
| R-NEU-12 | new `confusion` | esc (NEWS2 +3) + ask glucose and SpO₂ | 🔴 | A-GEN-01, A-NEU-02, A-GEN-02 | `[NEWS2]` |
| R-NEU-13 | `headache` AND `bp_sys ≥ 180` OR `bp_dia ≥ 120` | C059 Hypertension (0.8) | 🔴 | A-CV-05, A-GEN-03 | `[AHA-BP]` |
| R-NEU-14 | `headache` AND `pio2 < 127` | C014 Altitude sickness (0.6) | 🟠 | A-RESP-02, A-GEN-01 | `[RISK-HYPOX]`, `[STD3001-V2]` |
| R-NEU-15 | `dizziness` OR `vertigo` AND (`adaptation_window` OR gravity transition) | C089 Space motion sickness (0.5) | 🟡 | A-GEN-08, A-GI-03 | `[RISK-SMV]` |

## EYE — eyes and SANS
| ID | IF | THEN (CF) | Lvl | Actions | Refs |
|---|---|---|---|---|---|
| R-EYE-01 | `headache` AND `blurred_near_vision` AND `mission_day > 30` | C098 VIIP/SANS (0.6) | 🟠 | A-EYE-01, A-EYE-02, A-GEN-06 | `[RISK-SANS]`, `[LEE2020]` |
| R-EYE-02 | `near_acuity` decline ≥ 1 line OR change in one eye only | C098 (0.5) | 🟠 | A-EYE-01, A-EYE-02 | `[RISK-SANS]` |
| R-EYE-03 | P-03 AND any near-vision complaint | C098 (+0.1 modifier) | 🟠 | A-EYE-01 | `[ZWART2016]` |
| R-EYE-04 | `eye_foreign_body_sensation` (tearing, pain after debris/particles) | C042 Eye abrasion (0.7) | 🟠 | A-EYE-05, A-EYE-06, A-GEN-02 | `[IMM-MYERS]` |
| R-EYE-05 | `eye_chemical_exposure` | C043 Eye chemical burn (0.95) | 🔴 | A-EYE-03, A-GEN-02 | `[IMM-MYERS]` |
| R-EYE-06 | `red_eye` AND `eye_pain` AND `eye_discharge` AND contact-lens wearer (P-13) | C044 Corneal ulcer (0.6) | 🔴 | A-EYE-05, A-GEN-02 | `[IMM-MYERS]` |
| R-EYE-07 | `red_eye` AND (`eye_discharge` OR itch) AND normal vision AND no pain | C045 Eye infection (0.6) | 🟡 | A-GEN-11, A-GEN-05 | `[IMM-MYERS]` |
| R-EYE-08 | `eye_penetrating_injury` | C046 Eye penetration (1.0) | 🔴 | A-EYE-04, A-GEN-10 | `[IMM-MYERS]` |
| R-EYE-09 | `flashes_floaters_curtain` | C078 Retinal detachment (0.7) | 🔴 | A-GEN-03 | `[IMM-MYERS]` |
| R-EYE-10 | `eye_pain` AND `halos_around_lights` AND blurred vision (± headache, nausea) | C008 Acute glaucoma (0.7) | 🔴 | A-GEN-03 | `[IMM-MYERS]` |
| R-EYE-11 | `vision_loss_sudden` | esc (C078 / C090 / C008) | 🔴 | A-NEU-01, A-GEN-03 | `[IMM-MYERS]`, `[BEFAST]` |
| R-EYE-12 † | `light_flashes_closed_eyes` only, no other eye symptom | info: radiation light flashes, harmless | 🟢 | — | `[HAZ-RAD]` |

## ENT — ear, nose, throat
| ID | IF | THEN (CF) | Lvl | Actions | Refs |
|---|---|---|---|---|---|
| R-ENT-01 † | `nasal_congestion` AND no fever | C069 Nasal congestion (SAS) (0.7) | 🟢 | A-ENT-01 | `[IMM-INC]` |
| R-ENT-02 | congestion > 10 days or worsening AND `facial_pain_sinus` (± fever) | C012 Acute sinusitis (0.6) | 🟡 | A-ENT-01, A-GEN-02 | `[IMM-MYERS]` |
| R-ENT-03 † | `nosebleed` AND `mission_day ≤ 14` AND stopped < 20 min | C072 Nosebleed (SAS) (0.7) | 🟢 | A-ENT-03 | `[IMM-INC]` |
| R-ENT-04 | `nosebleed` > 20 min OR with `bp_sys ≥ 180` | C072 (0.6) + esc | 🟠 | A-ENT-03, A-CV-05, A-GEN-02 | `[IMM-MYERS]`, `[AHA-BP]` |
| R-ENT-05 | `ear_pain` OR `ear_fullness_after_pressure_change` after a pressure change | C023 Barotrauma (0.7) | 🟡 | A-ENT-02 | `[IMM-MYERS]` |
| R-ENT-06 | ear-canal pain + itch/discharge | C073 Otitis externa (0.6) | 🟡 | A-ENT-05 | `[IMM-MYERS]` |
| R-ENT-07 | `ear_pain` + fullness + `hearing_change` (± fever) | C074 Otitis media (0.6) | 🟡 | A-GEN-04, A-GEN-05 | `[IMM-MYERS]` |
| R-ENT-08 | (`hearing_change` OR `tinnitus`) AND `noise_dose > 100` | C054 Hearing loss (0.6) | 🟠 | A-ENT-04, A-GEN-06 | `[STD3001-V2]` |
| R-ENT-09 | `sore_throat` AND Centor ≥ 3 | C076 Pharyngitis (bacterial possible) (0.6) | 🟡 | A-GEN-04, A-GEN-11 | `[CENTOR]` |
| R-ENT-10 | `sore_throat` AND Centor ≤ 2 | C076 (likely viral) (0.4) | 🟡 | A-GEN-11, A-GEN-05 | `[CENTOR]` |

## DENT — dental (7 dental conditions in IMM; exposed pulp is an evacuation driver)
| ID | IF | THEN (CF) | Lvl | Actions | Refs |
|---|---|---|---|---|---|
| R-DEN-01 | `toothache` without visible cause | C037 Toothache (0.6) | 🟡 | A-DENT-03, A-DENT-04 | `[IMM-MYERS]` |
| R-DEN-02 | `tooth_sensitivity` + visible cavity | C032 Dental caries (0.6) | 🟡 | A-DENT-01 | `[IMM-MYERS]` |
| R-DEN-03 | throbbing pain + `gum_swelling` (± fever) | C033 Dental abscess (0.7) | 🟠 | A-GEN-02, A-GEN-04 | `[IMM-MYERS]` |
| R-DEN-04 | `tooth_broken_or_knocked_out` (broken) with pink/bleeding centre | C031 Exposed pulp (0.8) | 🟠 | A-DENT-01, A-GEN-03 | `[IMM-MYERS]`, `[IMM-INC]` |
| R-DEN-05 | tooth knocked out | C034 Dental avulsion (0.9) | 🟠 | A-DENT-02 | `[IMM-MYERS]` |
| R-DEN-06 | `lost_filling_or_crown` (crown) | C035 Crown loss (0.8) | 🟡 | A-DENT-01 | `[IMM-MYERS]` |
| R-DEN-07 | `lost_filling_or_crown` (filling) | C036 Filling loss (0.8) | 🟡 | A-DENT-01 | `[IMM-MYERS]` |
| R-DEN-08 | `mouth_ulcer` ≤ 14 days | C068 Mouth ulcer (0.6) (🟠 if > 14 days) | 🟢 | A-DENT-04 | `[IMM-MYERS]` |

## CV — cardiovascular (HRP: Cardiovascular Adaptations)
| ID | IF | THEN (CF) | Lvl | Actions | Refs |
|---|---|---|---|---|---|
| R-CV-01 | `news2_total ≥ 7` OR any NEWS2 parameter = 3 | esc | 🔴 | A-GEN-01, A-GEN-02, A-GEN-03 | `[NEWS2]` |
| R-CV-02 | `news2_total` 5–6 | esc | 🟠 | A-GEN-01 (in 1 h), A-GEN-02 | `[NEWS2]` |
| R-CV-03 | `bp_sys ≥ 180` OR `bp_dia ≥ 120`, confirmed on repeat | C059 Hypertension (0.8) | 🔴 | A-CV-05, A-GEN-03 | `[AHA-BP]` |
| R-CV-04 | `bp ≥ 140/90` on 2 days | C059 (0.6) | 🟠 | A-CV-05, A-GEN-06 | `[AHA-BP]` |
| R-CV-05 | P-06 AND `bp ≥ 130/80` | C059 (0.4) | 🟡 | A-CV-05, A-GEN-05 | `[AHA-BP]` |
| R-CV-06 | `bp_sys ≤ 90` AND (`dizziness` OR `phase` = landing/post-landing) | X03 Orthostatic intolerance (0.7) | 🟠 | A-CV-01, A-CV-02, A-CV-03 | `[CV-ER]`, `[MECK2001]` |
| R-CV-07 | `bp_orthostatic` meets criteria | X03 (0.8) | 🟠 | A-CV-01, A-CV-02, A-CV-03 | `[ORTHO2011]` |
| R-CV-08 | `palpitations` OR irregular pulse on cuff | C020 AFib/flutter (0.5) | 🟠 | A-CV-04 | `[CV-ER]` |
| R-CV-09 | `ecg_rhythm = irregular` | C020 (0.85) | 🔴 | A-GEN-02, A-GEN-03 | `[CV-ER]`, `[IMM-INC]` |
| R-CV-10 | `chest_pain` (pressure-like or exertional) | C015 Angina/MI (0.7) | 🔴 | A-GEN-07, A-CV-04, A-GEN-10 | `[HEART]`, `[IMM-MYERS]` |
| R-CV-11 | `chest_pain` AND (`bp_sys < 90` OR `confusion` OR cold clammy skin) | C026 Cardiogenic shock (0.7) | 🔴 | A-GEN-10, A-CV-04 | `[AHA-ACLS]` |
| R-CV-12 | unresponsive AND not breathing normally | C091 Sudden cardiac arrest (1.0) | 🔴 | A-CV-07 | `[AHA-ACLS]` |
| R-CV-13 | (`neck_pain_or_swelling_one_side` OR (`headache` AND `facial_swelling_one_side`)) AND `mission_day > 30` | X04 Jugular venous thrombosis (0.6) | 🔴 | A-CV-06, A-GEN-03 | `[MARSHALL-GOEBEL2019]`, `[CV-ER]` |
| R-CV-14 | P-17 | X04 (+0.1 modifier); weekly neck-symptom question from day 30 | — | — | `[MARSHALL-GOEBEL2019]` |
| R-CV-15 | `hr_rest > baseline × 1.15` for `days ≥ 3` AND no fever | X02 (0.3) — recovery flag | 🟡 | A-SLP-06, A-GEN-05 | `[T]` |
| R-CV-16 | `hemoglobin` below range AND (`fatigue` OR exercise tolerance ↓) | X15 Space anemia (0.6) | 🟠 | A-GEN-02, A-GEN-06 | `[TRUDEL2022]` |
| R-CV-17 | `hrv_rmssd < baseline × 0.7` for `days ≥ 3` (baseline = six-month passport median) | X02 (0.3) — recovery flag | 🟡 | A-SLP-06, A-GEN-05 | `[T]` |
| R-CV-17 | `hrv_rmssd < baseline × 0.7` for `days ≥ 3` | X02 (0.3) | 🟡 | A-SLP-06 | `[T]` |

## RESP — breathing and oxygen (HRP: Hypoxia)
| ID | IF | THEN (CF) | Lvl | Actions | Refs |
|---|---|---|---|---|---|
| R-RES-01 | `spo2 ≤ 91` | esc (hypoxemia) | 🔴 | A-RESP-01, A-RESP-02, A-GEN-02 | `[NEWS2]` |
| R-RES-02 | `spo2` 92–93 | esc | 🟠 | A-GEN-01, A-RESP-02 | `[NEWS2]` |
| R-RES-03 | `pio2 < 127` OR `cabin_alt > 8,300 ft` | C014 Altitude sickness (0.6) | 🟠 | A-RESP-02 | `[STD3001-V2]`, `[RISK-HYPOX]` |
| R-RES-04 | C014 AND (`headache` OR `confusion` OR insomnia) | C014 (0.75); 🔴 if `spo2 ≤ 91` | 🟠 | A-RESP-01, A-RESP-02 | `[RISK-HYPOX]` |
| R-RES-05 | (`cough` OR congestion) AND `temp ≥ 38.1` | C077 Respiratory infection (0.6) | 🟠 | A-GEN-11, A-GEN-12 | `[NEWS2]`, `[RISK-HMI]` |
| R-RES-06 | `cough` AND (`spo2 ≤ 93` OR `resp_rate ≥ 21`) | C077 (0.7) | 🔴 | A-RESP-01, A-GEN-03 | `[NEWS2]` |
| R-RES-07 | sudden `fever_chills` + `muscle_pain` + `cough` (± crew cluster) | C061 Influenza (0.7) | 🟠 | A-GEN-11, A-GEN-12 | `[RISK-HMI]` |
| R-RES-08 | `choking` | C028 Choking (1.0) | 🔴 | A-RESP-03 | `[AHA-ACLS]` |
| R-RES-09 | (`smoke_alarm` OR `smoke_exposure`) AND (`cough` OR `shortness_of_breath`) | C088 Smoke inhalation (0.85) | 🔴 | A-RESP-04, A-GEN-10 | `[IMM-MYERS]` |
| R-RES-10 | `wheeze` AND P-16 | C077 (0.4) — airway flare | 🟠 | A-GEN-04, A-GEN-02 | `[T]` |
| R-RES-11 | `resp_rate ≥ 25` OR ≤ 8 | esc | 🔴 | A-GEN-02, A-GEN-03 | `[NEWS2]` |

## VEST — vestibular (HRP: Altered Sensorimotor / Vestibular Function)
| ID | IF | THEN (CF) | Lvl | Actions | Refs |
|---|---|---|---|---|---|
| R-VES-01 | `nausea` AND (`mission_day ≤ 3` OR ≤ 72 h after gravity transition) | C089 Space motion sickness (0.8) | 🟡 | A-GI-03, A-GEN-04 | `[SMS-SHUTTLE]`, `[RISK-SMV]` |
| R-VES-02 | P-01 | C089 (+0.15 modifier; +0.05 if MSSQ only) | — | pre-flight tips | `[RISK-SMV]`, `[MSSQ]` |
| R-VES-03 | (`vertigo` OR `dizziness`) at gravity transition AND gait unsteady | C089 (0.6) | 🟡 | A-GEN-08 (no piloting/rover driving) | `[RISK-SMV]` |
| R-VES-04 | C089 symptoms persist after day 4 with no transition | esc: reconsider C049 / C011 / C050 | 🟠 | A-GEN-02, A-GEN-13 | `[RISK-SMV]` |

## GI — gastro-intestinal
| ID | IF | THEN (CF) | Lvl | Actions | Refs |
|---|---|---|---|---|---|
| R-GI-01 | `vomiting` > 24 h | X08 Dehydration (0.6) | 🟠 | A-GI-01, A-GEN-02 | `[RISK-SMV]`, `[NUTR-ER]` |
| R-GI-02 | `vomiting` AND `diarrhea` (± fever) | C049 Gastroenteritis (0.7) | 🟠 | A-GI-01, A-GEN-11, A-GEN-12 | `[RISK-HMI]` |
| R-GI-03 | `crew_symptom_cluster ≥ 2` with GI symptoms | C049 (+0.2) | 🟠 | A-ENV-04, A-GEN-12 | `[RISK-HMI]` |
| R-GI-04 | `diarrhea ≥ 3`/day | C039 Diarrhea (0.6); 🟠 with fever or blood | 🟡 | A-GI-01 | `[IMM-MYERS]` |
| R-GI-05 † | `constipation_days ≥ 3` AND `mission_day ≤ 14` AND no pain/vomiting | C029 Constipation (SAS) (0.7) | 🟢 | A-GI-02 | `[IMM-INC]` |
| R-GI-06 | abdominal distension AND `vomiting` AND no stool/flatus | C087 Small bowel obstruction (0.7) | 🔴 | A-GI-05, A-GEN-03 | `[IMM-MYERS]` |
| R-GI-07 | `abdominal_pain` RLQ or migrating to RLQ + `loss_of_appetite`/nausea (± fever); Alvarado ≥ 7 → CF 0.8 | C019 Appendicitis (0.6) | 🔴 | A-GI-05, A-GI-04, A-GEN-03 | `[ALVARADO]` |
| R-GI-08 | `abdominal_pain` RUQ after meals (± fever) | C005 Cholecystitis/biliary colic (0.6) | 🔴 | A-GI-05, A-GEN-02 | `[IMM-MYERS]` |
| R-GI-09 | severe epigastric pain radiating to back + `vomiting` | C009 Pancreatitis (0.6) | 🔴 | A-GI-05, A-GEN-03 | `[IMM-MYERS]` |
| R-GI-10 | `abdominal_pain` LLQ + `temp ≥ 38.1` | C007 Diverticulitis (0.6) | 🟠 | A-GI-05, A-GEN-02 | `[IMM-MYERS]` |
| R-GI-11 | `heartburn` / epigastric discomfort after meals, no red flags | C060 Indigestion (0.6) | 🟡 | A-GI-03 | `[IMM-MYERS]` |
| R-GI-12 | `rectal_pain_or_bleeding` with straining | C055 Hemorrhoids (0.6) | 🟡 | A-GI-02 | `[IMM-MYERS]` |
| R-GI-13 | `blood_in_stool` large OR with `dizziness` / HR > 100 | esc | 🔴 | A-GEN-02, A-GEN-03 | `[ATLS]` |
| R-GI-14 | `bulge_abdominal_wall` reducible, mild pain | C002 Abdominal wall hernia (0.6); 🔴 if painful, irreducible or with vomiting | 🟡 | A-GEN-02 | `[IMM-MYERS]` |
| R-GI-15 | abdominal impact AND (`abdominal_pain` with guarding OR `hr_rest > 100`) | C001 Abdominal injury (0.7) | 🔴 | A-GI-04, A-GEN-10 | `[ATLS]` |
| R-GI-16 | `abdominal_pain` with rebound or guarding (any location) | esc (surgical abdomen) | 🔴 | A-GI-05, A-GEN-03 | `[ATLS]` |
| R-GI-17 | `nausea` after day 4, no transition, no other cause | esc: reconsider C049 / C067 / C011 | 🟡 | A-GEN-13 | `[IMM-MYERS]` |

## GU — urinary and genital
| ID | IF | THEN (CF) | Lvl | Actions | Refs |
|---|---|---|---|---|---|
| R-GU-01 | `dysuria` AND `urinary_frequency` | C096 UTI (0.7) | 🟠 | A-GU-01, A-GU-02, A-GEN-02 | `[IMM-INC]` |
| R-GU-02 | `urine_nitrite_le` positive AND `dysuria` | C096 (0.85) | 🟠 | A-GEN-04, A-GEN-02 | `[IMM-INC]` |
| R-GU-03 | C096 AND (`temp ≥ 38.1` OR `flank_pain`) | C080 Sepsis risk (0.4) + esc | 🔴 | A-GEN-03 | `[SEPSIS3]`, `[IMM-INC]` |
| R-GU-04 | colicky `flank_pain` (± `blood_in_urine`, nausea) | C070 Kidney stone (0.7); 🔴 with P-02 | 🟠 | A-GU-01, A-GU-02, A-GEN-02 | `[TB030]`, `[STONE]` |
| R-GU-05 | STONE score elements high (sudden pain, nausea/vomiting, hematuria) | C070 (0.8) | 🟠 | A-GEN-03 | `[STONE]` |
| R-GU-06 | cannot void > 6 h with bladder fullness | C095 Urinary retention (SAS) (0.7) | 🟠 | A-GU-04, A-GU-03 | `[IMM-INC]` |
| R-GU-07 † | `urinary_incontinence` AND `mission_day ≤ 14` | C094 Urinary incontinence (SAS) (0.6) | 🟢 | A-GU-04 | `[IMM-INC]` |
| R-GU-08 | `perineal_pain` + `dysuria` + `temp ≥ 38.1` | C010 Acute prostatitis (0.6) | 🟠 | A-GEN-02 | `[IMM-MYERS]` |
| R-GU-09 | `vaginal_itch_discharge` | C097 Vaginal yeast infection (0.6) | 🟡 | A-GEN-04 | `[IMM-MYERS]` |
| R-GU-10 | `abnormal_uterine_bleeding` | C003 (0.6); 🔴 with `dizziness` or HR > 100 | 🟠 | A-GEN-02 | `[IMM-MYERS]` |
| R-GU-11 | `fluid_intake < 2.5 L` on 2 days (3.0 if P-02) | X08 Dehydration (0.5) | 🟡 | A-GU-02 | `[STD3001-V2]` |
| R-GU-12 | `urine_color ≥ 6` OR `sodium > 145` OR `urine_osm > 700` | X08 (0.6); `sodium > 145` → CF 0.8, 🟠 | 🟡 | A-GU-02 | `[NUTR-ER]` |

## MSK / TRAUMA — bones, muscles, injuries (HRP: Bone Changes, Fitness, Dynamic Loads)
| ID | IF | THEN (CF) | Lvl | Actions | Refs |
|---|---|---|---|---|---|
| R-MSK-01 † | `back_pain` AND `mission_day ≤ 14` AND no trauma AND no red flags | C022 Back pain (SAS) (0.7) | 🟢 | A-MSK-04 | `[KERSTMAN2012]`, `[IMM-INC]` |
| R-MSK-02 | `back_pain` + red flag (neuro deficit, bladder/bowel change, fever, after high load) | esc (C021 / C066) | 🔴 | A-MSK-05, A-GEN-03 | `[NICE-NG59]` |
| R-MSK-03 | `back_pain` after load/impact, no neuro signs | C021 Back injury (0.6) | 🟠 | A-MSK-01, A-GEN-02 | `[NICE-NG59]` |
| R-MSK-04 | high load (landing, `phase` = landing) + severe back pain | C066 Lumbar fracture (0.6) | 🔴 | A-MSK-02, A-MSK-05, A-GEN-03 | `[RISK-DYN]` |
| R-MSK-05 | ankle injury AND (`ottawa_ankle` positive where gravity > 0, OR malleolar bony tenderness in 0 g) | C017 (0.6) + esc "fracture not excluded" | 🟠 | A-MSK-02, A-GEN-02 | `[OTTAWA-ANKLE]` |
| R-MSK-06 | ankle injury AND `ottawa_ankle` negative | C017 Ankle sprain (0.7) | 🟡 | A-MSK-01 | `[OTTAWA-ANKLE]` |
| R-MSK-07 | knee injury AND `ottawa_knee` positive | C063 (0.6) + esc "fracture not excluded" | 🟠 | A-MSK-02, A-GEN-02 | `[OTTAWA-KNEE]` |
| R-MSK-08 | knee injury AND `ottawa_knee` negative | C063 Knee sprain (0.7) | 🟡 | A-MSK-01 | `[OTTAWA-KNEE]` |
| R-MSK-09 | fall/impact on hand + deformity or bony tenderness | C099 Wrist fracture (0.7) | 🟠 | A-MSK-02, A-MSK-05, A-GEN-02 | `[IMM-INC]` |
| R-MSK-10 | wrist pain, no deformity, no bony tenderness | C100 Wrist sprain (0.6) | 🟡 | A-MSK-01 | `[IMM-MYERS]` |
| R-MSK-11 | hip impact + `inability_to_move_limb` or shortened/rotated leg | C058 Hip fracture (0.8; +0.1 with P-12) | 🔴 | A-MSK-02, A-GEN-10 | `[TB030]` |
| R-MSK-12 | hip pain after load, movement kept | C057 Hip sprain (0.6) | 🟡 | A-MSK-01 | `[IMM-MYERS]` |
| R-MSK-13 | shoulder `limb_deformity` or cannot move after load | C081 Shoulder dislocation (0.7) | 🟠 | A-MSK-02, A-MSK-05, A-GEN-02 | `[IMM-MYERS]` |
| R-MSK-14 | shoulder pain, movement kept (often after EVA) | C082 Shoulder sprain (0.6) | 🟡 | A-MSK-01, A-EVA-03 | `[RISK-EVA]` |
| R-MSK-15 | elbow `limb_deformity` | C040 Elbow dislocation (0.8) | 🔴 | A-MSK-02, A-MSK-05, A-GEN-10 | `[IMM-MYERS]` |
| R-MSK-16 | elbow pain, movement kept | C041 Elbow sprain (0.6) | 🟡 | A-MSK-01 | `[IMM-MYERS]` |
| R-MSK-17 | finger `limb_deformity` | C047 Finger dislocation (0.8) | 🟠 | A-MSK-02, A-MSK-05 | `[IMM-MYERS]` |
| R-MSK-18 | localised bone pain with loading in partial gravity or on treadmill | C065 Stress fracture (0.6) | 🟠 | A-MSK-02, A-MSK-07 | `[TB030]` |
| R-MSK-19 | limb injury + `severe_pain_out_of_proportion_tight_compartment` (± numbness) | C006 Compartment syndrome (0.7) | 🔴 | A-MSK-05, A-GEN-10 | `[ATLS]` |
| R-MSK-20 | `joint_swelling_red_hot` (± fever) | C004 Acute arthritis (0.6) | 🟠 | A-GEN-02 | `[IMM-MYERS]` |
| R-MSK-21 | chest impact + pain on breathing or `shortness_of_breath` | C027 Chest injury (0.7) | 🔴 | A-GEN-10, A-RESP-01 | `[ATLS]` |
| R-MSK-22 | head impact + (GCS < 15 OR loss of consciousness OR vomiting ≥ 2 OR amnesia > 30 min OR dangerous mechanism) | C050 Head injury (0.8) | 🔴 | A-NEU-02, A-GEN-10 | `[CCHR]`, `[GCS]` |
| R-MSK-23 | head impact, GCS 15, none of the above | C050 (0.5) | 🟡 | A-NEU-02 (q1h × 4) | `[CCHR]` |
| R-MSK-24 | injury/bleeding AND `hr_rest > 100` AND falling `bp_sys` | C093 Hypovolemic shock (0.8) | 🔴 | A-SKIN-02, A-GEN-10 | `[ATLS]` |
| R-MSK-25 | spinal injury AND low BP with HR < 60 | C071 Neurogenic shock (0.7) | 🔴 | A-GEN-10 | `[ATLS]` |
| R-MSK-26 | `exercise_min < 90` on `count_7d ≥ 3` AND `mission_day > 14` (long flights only) | X10 Deconditioning (0.5) | 🟡 | A-MSK-06 | `[RISK-FIT]` |
| R-MSK-27 | `aerobic_pct < 80` OR `strength_pct < 80` | X10 (0.8) | 🟠 | A-MSK-07, A-GEN-06 | `[STD3001-V1]` |
| R-MSK-28 | P-12 AND any fall/impact | fracture rules CF +0.1 | — | — | `[TB030]` |

## SKIN
| ID | IF | THEN (CF) | Lvl | Actions | Refs |
|---|---|---|---|---|---|
| R-SKN-01 | `rash` without fever or systemic signs | C086 Skin rash (0.6) | 🟡 | A-GEN-09, A-SKIN-05, A-IMM-01 | `[CRUCIAN2016]`, `[ISS-EVENTS]` |
| R-SKN-02 | `painful_band_rash_one_side` OR (`rash` AND `temp ≥ 38.1`) | C056 Herpes zoster (0.75; +0.1 with P-04) | 🟠 | A-IMM-03, A-GEN-02, A-GEN-09 | `[RISK-IMMUNE]` |
| R-SKN-03 | `cold_sore` | C086 (0.4) — HSV reactivation, counted as ISS clinical event | 🟡 | A-IMM-03, A-IMM-04 | `[ISS-EVENTS]`, `[RISK-IMMUNE]` |
| R-SKN-04 | `skin_redness_warm_spreading` (± fever) | C084 Skin infection (0.7) | 🟠 | A-SKIN-03, A-GEN-02 | `[IMM-INC]` |
| R-SKN-05 | `skin_wound` superficial scrape | C083 Skin abrasion (0.7) | 🟢 | A-SKIN-01 | `[IMM-MYERS]` |
| R-SKN-06 | `skin_wound` deep/gaping OR bleeding > 10 min | C085 Skin laceration (0.7) | 🟠 | A-SKIN-02, A-GEN-02 | `[IMM-MYERS]` |
| R-SKN-07 | `skin_wound` minor cut | C085 (0.5) | 🟡 | A-SKIN-01 | `[IMM-MYERS]` |
| R-SKN-08 | `burn` small, superficial (< 1% body area), not face/hands | C025 Burns (0.6) | 🟡 | A-SKIN-04, A-SKIN-01 | `[WALLACE]` |
| R-SKN-09 | `burn` ≥ 10% body area OR face/hands/genitals/airway OR electrical/chemical | C025 (0.9) | 🔴 | A-SKIN-04, A-GEN-10 | `[WALLACE]`, `[ATLS]` |
| R-SKN-10 | `fingernail_damage` after EVA | C048 Fingernail delamination (0.8) | 🟡 | A-SKIN-06, A-EVA-03 | `[RISK-EVA]` |

## IMMUNE — allergy and infection (HRP: Immune; Host-Microorganism)
| ID | IF | THEN (CF) | Lvl | Actions | Refs |
|---|---|---|---|---|---|
| R-IMM-01 | `hives` OR itching OR mild swelling, no airway/breathing/BP signs | C013 Allergic reaction (0.7) | 🟡 | A-IMM-01, A-GEN-05 | `[ANAPH]` |
| R-IMM-02 | skin/mucosal signs AND (`throat_tightness` OR `shortness_of_breath` OR `bp_sys < 90`) | C016 Anaphylaxis (0.9; +0.05 with P-08) | 🔴 | A-IMM-02, A-GEN-10 | `[ANAPH]` |
| R-IMM-03 | `lip_tongue_swelling` alone | C016 (0.5) — watch 30 min | 🟠 | A-IMM-01, A-GEN-01 | `[ANAPH]` |
| R-IMM-04 | suspected infection AND `qsofa ≥ 2` | C080 Sepsis (0.85) | 🔴 | A-GEN-10, A-GEN-03 | `[SEPSIS3]` |
| R-IMM-05 | suspected infection AND `news2_total ≥ 5` | C080 (0.5) | 🟠 | A-GEN-01, A-GEN-02 | `[NEWS2]` |
| R-IMM-06 | `temp ≥ 38.1` with no localising symptom | C061 (0.3) + esc: febrile illness | 🟠 | A-GEN-13, A-GEN-11 | `[NEWS2]` |
| R-IMM-07 | `temp ≥ 39.1` | esc | 🟠 | A-GEN-02, A-GEN-04 | `[NEWS2]` |
| R-IMM-08 | `crew_symptom_cluster ≥ 2` febrile within 72 h | C061 (+0.2) + environment check | 🟠 | A-GEN-12, A-ENV-04 | `[RISK-HMI]` |
| R-IMM-09 | `microbial_alert` AND (GI or skin symptoms) | C049 / C084 (+0.2) | 🟠 | A-ENV-04, A-GEN-11 | `[RISK-HMI]` |

## NUTR — nutrition and metabolism (HRP: Inadequate Food and Nutrition)
| ID | IF | THEN (CF) | Lvl | Actions | Refs |
|---|---|---|---|---|---|
| R-NUT-01 | `glucose < 54` | X05 Hypoglycemia (0.9) | 🔴 | A-NUT-01, A-GEN-02 | `[ADA-SOC]` |
| R-NUT-02 | `glucose` 54–69 | X05 (0.7) | 🟡 | A-NUT-01 | `[ADA-SOC]` |
| R-NUT-03 | `glucose` 54–69 AND `confusion` | X05 (0.9) | 🔴 | A-NUT-01, A-GEN-02 | `[ADA-SOC]` |
| R-NUT-04 | fasting `glucose ≥ 126` on 2 days | X06 Hyperglycemia (0.6) | 🟠 | A-NUT-05, A-GEN-06 | `[ADA-SOC]` |
| R-NUT-05 | random `glucose ≥ 200` AND (`thirst` OR frequent urination) | X06 (0.7) | 🟠 | A-NUT-05, A-GEN-02 | `[ADA-SOC]` |
| R-NUT-06 | `body_mass ≤ pre-flight × 0.95` OR `food_intake_pct < 80` for `days ≥ 3` | X07 Inadequate nutrition (0.6) | 🟠 | A-NUT-02, A-NUT-03 | `[NUTR-ER]` |
| R-NUT-07 | `body_mass ≤ pre-flight × 0.923` (−7.7%) | X07 (0.9) | 🔴 | A-NUT-03, A-GEN-03 | `[NUTR-ER]` |
| R-NUT-08 | `loss_of_appetite` for `days ≥ 3` | X07 (0.4) | 🟡 | A-NUT-02 | `[NUTR-ER]` |
| R-NUT-09 | `vitd < 20` | X10 bone risk (0.5) | 🟠 | A-NUT-04 | `[TB030]` |
| R-NUT-10 | `vitd` 20–34 | X10 bone risk (0.3) | 🟡 | A-NUT-04 | `[TB030]` |

## RAD — radiation (HRP: Space Radiation)
| ID | IF | THEN (CF) | Lvl | Actions | Refs |
|---|---|---|---|---|---|
| R-RAD-01 | `spe_alert` | esc: shelter | 🟠 | A-RAD-01, A-RAD-02 | `[TB020]` |
| R-RAD-02 | `dose_cumulative ≥ 480 mSv` (team early warning `[T]` at 80% of the NASA career limit of < 600 mSv, incl. P-11) | X09 Cumulative exposure (0.9) | 🟠 | A-RAD-03, A-GEN-06 | `[STD3001-V1]` |
| R-RAD-03 | `dose_cumulative ≥ 600 mSv` | X09 (1.0) — limit reached | 🔴 | A-RAD-03, A-GEN-03 | `[STD3001-V1]` |
| R-RAD-04 | `bfo_30d ≥ 200 mGy-Eq` (80% of 250) | X09 (0.7) | 🟠 | A-RAD-03 | `[STD3001-V1]` |
| R-RAD-05 | (`nausea` OR `vomiting` OR `fatigue`) AND `hours_since_spe ≤ 48` | C011 Acute radiation syndrome (0.6) | 🔴 | A-RAD-04, A-GEN-03 | `[TB020]` |
| R-RAD-06 | C011 AND `lymphocytes_abs` drop > 50% vs baseline | C011 (0.85) | 🔴 | A-GEN-03 | `[TB020]`, `[OSD569]` |
| R-RAD-07 | `skin_redness_after_spe` AND GI symptoms | C011 (+0.2) | 🔴 | A-GEN-03 | `[TB020]` |
| R-RAD-08 | `dose_today > 2 ×` mission daily average | X09 (0.4) — check dosimeter/shielding | 🟡 | A-RAD-03 | `[TB020]` |
| R-RAD-09 † | `light_flashes_closed_eyes` only | info (see R-EYE-12) | 🟢 | — | `[HAZ-RAD]` |

## ENV — environment and toxic (HRP: Hostile/Closed Environments)
| ID | IF | THEN (CF) | Lvl | Actions | Refs |
|---|---|---|---|---|---|
| R-ENV-01 | `co2_1h > 3.0` (no symptoms yet) | C051 (0.2) — advisory | 🟡 | A-ENV-01 | `[STD3001-V2]` |
| R-ENV-02 | `ammonia_alarm` | C092 Toxic exposure (0.9) | 🔴 | A-ENV-02 | `[IMM-MYERS]` |
| R-ENV-03 | `ammonia_alarm` AND (eye or throat burning OR `cough`) | C092 (1.0) | 🔴 | A-ENV-02, A-EYE-03, A-GEN-10 | `[IMM-MYERS]` |
| R-ENV-04 | `smoke_alarm` (no symptoms) | C088 (0.5) — watch | 🟠 | A-RESP-04 | `[IMM-MYERS]` |
| R-ENV-05 | `cabin_temp` outside 18–27 °C AND (`temp ≥ 38.1` OR `hr_rest > baseline × 1.15`) | X11 Heat stress (0.5) | 🟠 | A-ENV-03, A-GI-01 | `[STD3001-V2]` |
| R-ENV-06 | `humidity` outside 25–75% AND dry eyes/skin | info | 🟡 | A-SKIN-05, A-ENV-03 | `[STD3001-V2]` |
| R-ENV-07 | `depress_alarm` AND (`ear_pain` OR sinus pain) | C023 Barotrauma (0.7); DCS / hypoxia rules activated | 🟠 | A-ENT-02, A-RESP-02 | `[RISK-DCS]` |
| R-ENV-08 | medication taken ≤ 24 h AND new `rash` / drowsiness / `confusion` | C067 Medication adverse reaction (0.6) | 🟠 | A-GEN-02 | `[IMM-MYERS]` |

## EVA — spacewalks (HRP: EVA; Decompression Sickness)
| ID | IF | THEN (CF) | Lvl | Actions | Refs |
|---|---|---|---|---|---|
| R-EVA-01 | `post_eva_hours ≤ 24` AND (`joint_pain` OR `tingling_numbness` OR skin mottling OR `confusion` OR `shortness_of_breath`) | C030 Decompression sickness (0.8) | 🔴 | A-EVA-01, A-GEN-03 | `[RISK-DCS]` |
| R-EVA-02 | `post_eva_hours ≤ 24` AND `fingernail_damage` | C048 (0.8) | 🟡 | A-SKIN-06 | `[RISK-EVA]` |
| R-EVA-03 | `post_eva_hours ≤ 24` AND `hand_or_shoulder_pain_after_eva` | C082 (0.6) | 🟡 | A-EVA-03, A-MSK-01 | `[RISK-EVA]` |
| R-EVA-04 | during EVA: `temp ≥ 38.1` OR sustained HR > 85% of max | X11 Heat stress (0.6) | 🟠 | A-EVA-02, A-GEN-02 | `[RISK-EVA]` |
| R-EVA-05 | `post_eva_hours ≤ 24` AND `fatigue` AND low intake/fluids | X08 / X07 (0.4) | 🟡 | A-EVA-02 | `[RISK-EVA]`, `[STD3001-V2]` |
| R-EVA-06 | `spe_alert` during EVA | esc | 🔴 | A-RAD-02 | `[TB020]` |
| R-EVA-07 | paresthesia at suit-contact points after EVA, no DCS features | C075 (0.5) | 🟡 | A-EVA-03 | `[RISK-EVA]` |

---

## Coverage check
Every condition C001–C100 and X01–X15 is the THEN of at least one rule above. Rule count: SLEEP 13 · BEHAV 18 · SELF 2 · NEURO 15 · EYE 12 ·
ENT 10 · DENT 8 · CV 17 · RESP 11 · VEST 4 · GI 17 · GU 12 · MSK 28 · SKIN 10 · IMMUNE 9 · NUTR 10 · RAD 9 · ENV 8 · EVA 7 = **220 rules**,
plus 19 passport modifiers (P-01…P-19).
