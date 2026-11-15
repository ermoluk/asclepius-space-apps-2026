# 03 — Indicators (every input the engine reads)

Columns: **ID** · **Unit / scale** · **How measured in space** · **Frequency** · **Thresholds** (tagged) · **Space note** · **Refs**.
`baseline` = passport value or rolling 14-day median. Derived facts (trends, durations) are listed at the end.

## 1. Vital signs (`I-VIT-*`)
| ID | Unit | How measured in space | Freq. | Thresholds | Space note | Refs |
|---|---|---|---|---|---|---|
| `I-VIT-hr_rest` | bpm | Wrist wearable; BP cuff; ECG (Tempus Pro) | AM daily | NEWS2 ≤40→3 · 41–50→1 · 51–90→0 · 91–110→1 · 111–130→2 · ≥131→3 [C]; > baseline +15% × 3 days [T] | Fit crew often 50s | `[NEWS2]`, `[TEMPUS]` |
| `I-VIT-bp_sys` / `I-VIT-bp_dia` | mmHg | Automatic cuff | AM scheduled | NEWS2 sys ≤90→3 · 91–100→2 · 101–110→1 · 111–219→0 · ≥220→3 [C]; AHA ≥130/80 stage 1, ≥140/90 stage 2, >180/120 crisis [C] | 24-h BP −8–10 mmHg in flight [S] | `[NEWS2]`, `[AHA-BP]`, `[NORSK2015]` |
| `I-VIT-bp_orthostatic` | Δ mmHg / Δ bpm | Lying 5 min → standing/seated upright 3 min (or LBNP on ISS) | gravity transition | SBP drop ≥ 20 or DBP ≥ 10 within 3 min = orthostatic hypotension; HR rise ≥ 30 without hypotension = orthostatic tachycardia [C] | 66% of ISS crew failed 10-min tilt on landing day [N] | `[ORTHO2011]`, `[CV-ER]`, `[MECK2001]` |
| `I-VIT-spo2` | % | Finger pulse oximeter | AM scheduled / symptoms | NEWS2 ≤91→3 · 92–93→2 · 94–95→1 · ≥96→0 [C] | ISS cabin at sea-level pressure → Earth norms | `[NEWS2]`, `[STD3001-V2]` |
| `I-VIT-temp` | °C | Oral/ear thermometer; T-Mini headband | AM daily / symptoms | NEWS2 ≤35.0→3 · 35.1–36.0→1 · 36.1–38.0→0 · 38.1–39.0→1 · ≥39.1→2 [C] | Core temp (forehead heat-flux sensor, not an oral thermometer) +1.0 °C at rest, +1.4 °C peak in exercise on long missions [S] | `[NEWS2]`, `[STAHN2017]` |
| `I-VIT-resp_rate` | /min | Guided 30-s count × 2 | symptoms | NEWS2 ≤8→3 · 9–11→1 · 12–20→0 · 21–24→2 · ≥25→3 [C]; qSOFA ≥22 [C] | — | `[NEWS2]`, `[SEPSIS3]` |
| `I-VIT-hrv_rmssd` | ms | Wearable, morning | AM daily | < baseline −30% × 3 days → recovery flag [T] | Personal only | `[T]` |
| `I-VIT-glucose` | mg/dL | Glucometer / CGM (Polaris Dawn used CGM) | scheduled fasting / symptoms | <54 level-2 hypo · 54–69 level-1 · 70–99 normal fasting · 100–125 elevated · ≥126 fasting ×2 high · ≥200 random + symptoms [C] | Inspiration4 pre/post values in `data/` | `[ADA-SOC]`, `[OSD575]` |
| `I-VIT-ecg_rhythm` | regular / irregular / not done | Single-lead ECG (wearable or Tempus) | on palpitations | irregular → arrhythmia rule [C] | — | `[CV-ER]`, `[TEMPUS]` |
| `I-VIT-consciousness` | ACVPU / GCS | Crewmate assessment | emergencies | new confusion → NEWS2 +3 [C]; GCS ≤ 13 after head injury → RED [C] | — | `[NEWS2]`, `[GCS]` |

## 2. Self-assessment (`I-SELF-*`) — see `02-daily-checkins.md`
| ID | Scale | When | Thresholds | Refs |
|---|---|---|---|---|
| `I-SELF-physical_state` | 1–7 (Very bad → Very good) | AM | ≤ 2 on 2 consecutive days → prompt symptom interview [T]; drop ≥ 2 points vs baseline [T] | `[SRH]` |
| `I-SELF-mood_valence` | 1–7 (Very unpleasant → Very pleasant) | PM | ≤ 2 on ≥ 5 of 7 days → ORANGE [T]; 1 on 3 days in a row → offer conference [T] | `[APPLE-SOM]`, `[CIRCUMPLEX]` |
| `I-SELF-mood_labels` | multi-select | PM | ≥ 3 days with "anxious"/"overwhelmed" → GAD-7 early [T] | `[APPLE-SOM]` |
| `I-SELF-mood_context` | multi-select | PM | used for explanations and countermeasure choice | `[APPLE-SOM]` |
| `I-SELF-emotion_now` | 1–7 + labels | any | 1/7 → supportive follow-up [T] | `[APPLE-SOM]` |

## 3. Sleep and fatigue (`I-SLEEP-*`)
| ID | Unit | How | Freq. | Thresholds | Refs |
|---|---|---|---|---|---|
| `I-SLEEP-sleep_hours` | h / 24 h | Actigraphy (Actiwatch on ISS) + confirm | AM | ≤ 6 h = restricted [N]; need 7–9 h [N]; ISS mean ≈ 6 h [S] | `[RISK-SLEEP]`, `[TB041]`, `[BARGER2014]`, `[JONES2022]` |
| `I-SLEEP-sleep_quality` | 1–5 | Post-sleep survey | AM | ≤ 2 on 3 of 7 days [T] | `[STDMEAS]` |
| `I-SLEEP-kss` | 1–9 | Karolinska Sleepiness Scale | AM / pre-task | ≥ 7 = sleepy [C] | `[KSS]` |
| `I-SLEEP-fatigue` | 1–7 | Samn-Perelli | PM / pre-task | ≥ 5 = fatigued, not fit for critical tasks [C] | `[SAMN-PERELLI]` |
| `I-SLEEP-awake_hours` | h | Schedule / actigraphy | continuous | ≥ 16 h awake [N] | `[RISK-SLEEP]` |
| `I-SLEEP-work_hours` | h / day; consecutive days | Schedule | daily | > 16 h/day; > 6 work days in a row [N] | `[RISK-SLEEP]` |
| `I-SLEEP-hypnotic_use` | nights / 7 | Self-report | PM | ≥ 4 of 7 nights → review with CMO [T] (hypnotics used on 52% of ISS nights [S]) | `[BARGER2014]` |
| `I-SLEEP-caffeine_late` | yes/no after 14:00 | Self-report | PM | yes + sleep < 6 h → tip [T] | `[TB041]` |

## 4. Tests (`I-TEST-*`)
| ID | Unit | How | Freq. | Thresholds | Refs |
|---|---|---|---|---|---|
| `I-TEST-pvt_rt` | ms (mean) | 3-min PVT (ISS Reaction Self Test) | optional AM/PM | > baseline × 1.15 [T] | `[PVT-BASNER]`, `[RST-ISS]` |
| `I-TEST-pvt_lapses` | count (RT > 500 ms) | same | same | ≥ 2× baseline [T] | `[PVT-BASNER]` |
| `I-TEST-near_acuity` | logMAR or lines vs baseline, each eye | Tablet near-vision chart at fixed distance | weekly from day 30 (day 14 if P-03) | any decline ≥ 1 line or one-eye-only change → SANS rule [T] | `[RISK-SANS]`, `[LEE2020]` |
| `I-TEST-cognition` | composite z vs baseline | Cognition-style battery | monthly | z ≤ −1.5 [T] | `[COGNITION]`, `[TB016]` |
| `I-TEST-aerobic_pct` | % of pre-flight | Submax cycle test HR | every 30 days | < 80% [N] | `[STD3001-V1]`, `[RISK-FIT]` |
| `I-TEST-strength_pct` | % of pre-flight | Exercise device load logs | every 30 days | < 80% [N] | `[STD3001-V1]` |
| `I-TEST-befast` | each item +/– | Guided crewmate check (Balance, Eyes, Face, Arm, Speech, Time) | on neuro symptoms | any positive → RED [C] | `[BEFAST]` |
| `I-TEST-ottawa_ankle` / `_knee` | criteria met yes/no | Guided exam | on injury | criteria met → possible fracture [C] (weight-bearing items only valid in partial/full gravity) | `[OTTAWA-ANKLE]`, `[OTTAWA-KNEE]` |

## 5. Symptoms (`I-SYM-*`) — from body-map taps; yes/no plus severity NRS 0–10 `[NRS-PAIN]`
| Region | Indicators |
|---|---|
| Head / neuro | `headache` (+ onset sudden "worst ever", with fever/neck stiffness, after head injury, positional), `dizziness`, `vertigo`, `confusion`, `fainting`, `seizure_witnessed`, `weakness_one_side`, `facial_droop`, `speech_difficulty`, `tingling_numbness` |
| Eyes | `blurred_near_vision`, `vision_loss_sudden`, `flashes_floaters_curtain`, `eye_pain`, `red_eye`, `eye_foreign_body_sensation`, `eye_discharge`, `halos_around_lights`, `eye_chemical_exposure`, `eye_penetrating_injury`, `light_flashes_closed_eyes` (radiation phosphenes — expected, harmless) |
| Ear / nose / throat | `nasal_congestion`, `nosebleed`, `sore_throat`, `ear_pain`, `ear_fullness_after_pressure_change`, `hearing_change`, `tinnitus`, `facial_pain_sinus` |
| Mouth / teeth | `toothache`, `tooth_sensitivity`, `tooth_broken_or_knocked_out`, `lost_filling_or_crown`, `gum_swelling`, `mouth_ulcer` |
| Chest / breathing | `chest_pain` (+ exertional, pressure-like), `palpitations`, `shortness_of_breath`, `cough`, `wheeze`, `choking`, `smoke_exposure` |
| Abdomen / GI | `nausea`, `vomiting` (hours), `diarrhea` (episodes/day), `constipation_days`, `abdominal_pain` (+ location: RLQ, RUQ, LLQ, epigastric, diffuse; rebound/guarding on guided check), `heartburn`, `blood_in_stool`, `rectal_pain_or_bleeding`, `bulge_abdominal_wall` |
| Urinary / genital | `dysuria`, `urinary_frequency`, `urinary_retention`, `urinary_incontinence`, `flank_pain`, `blood_in_urine`, `perineal_pain`, `vaginal_itch_discharge`, `abnormal_uterine_bleeding` |
| Back / neck / limbs | `back_pain`, `neck_pain_or_swelling_one_side`, `facial_swelling_one_side`, `joint_pain` (+ location), `joint_swelling_red_hot`, `leg_swelling_pain_one_side`, `muscle_pain`, `limb_deformity`, `inability_to_move_limb`, `severe_pain_out_of_proportion_tight_compartment`, `fingernail_damage`, `hand_or_shoulder_pain_after_eva` |
| Skin | `rash`, `itching`, `hives`, `cold_sore`, `painful_band_rash_one_side`, `skin_wound` (+ depth, bleeding), `skin_redness_warm_spreading`, `burn` (+ % body area), `skin_redness_after_spe` |
| Allergy | `lip_tongue_swelling`, `throat_tightness`, `hives` + `shortness_of_breath` |
| General | `fever_chills`, `fatigue`, `loss_of_appetite`, `thirst`, `weight_loss_noticed` |
| Mind | `anxiety_or_panic`, `hallucinations`, `self_harm_thoughts`, `feeling_unsafe_or_unable_to_cope` |

## 6. Nutrition, hydration, activity (`I-NUTR-*`, `I-MSK-*`)
| ID | Unit | How | Freq. | Thresholds | Refs |
|---|---|---|---|---|---|
| `I-NUTR-body_mass` | kg (vs pre-flight) | Mass measurement device (scales do not work in 0 g) | weekly | ≤ −5% → ORANGE [T]; ≤ −7.7% → RED (performance decline) [N] | `[NUTR-ER]`, `[RISK-NUTR]` |
| `I-NUTR-food_intake_pct` | % of planned kcal | Food log (tablet) | PM | < 80% × 3 days [T]; ISS mean ≈ 80% [N] | `[NUTR-ER]` |
| `I-NUTR-energy_target` | kcal/day | NASA EER from passport; 3,035 kcal default; +200 kcal/EVA hour | computed | — | `[STD3001-V2]` |
| `I-NUTR-fluid_intake` | L/day | Drink log | PM | < 2.5 L [N]; < 3.0 L if P-02 [T] | `[STD3001-V2]` |
| `I-NUTR-urine_color` | 1–8 chart | Self-check | AM | ≥ 6 = likely dehydrated [T] | `[T]` |
| `I-MSK-exercise_min` | min/day | Exercise device logs | PM | < 90 min on ≥ 3 of 7 days [T] (HRR: 1.5 h/day, 6–7 days/week [N]) | `[RISK-FIT]` |
| `I-MSK-height_change` | cm | Tape measure | weekly | +3% expected (spine) [N] | `[RISK-BONE]` |

## 7. Behavioral (`I-BEH-*`)
| ID | Scale | Freq. | Thresholds | Refs |
|---|---|---|---|---|
| `I-BEH-team_cohesion` | 1–5 | PM | ≤ 2 on ≥ 3 of 7 days [T] | `[STDMEAS]`, `[RISK-TEAM]` |
| `I-BEH-workload` | 1–10 (Bedford-style) | PM | ≥ 8 on ≥ 3 days [T] | `[BEDFORD]`, `[TB-COGWL]` |
| `I-BEH-phq9` | 0–27 | weekly | 5 mild · 10 moderate · 15 mod-severe · 20 severe [C]; item 9 > 0 → RED [C] | `[PHQ9]` |
| `I-BEH-gad7` | 0–21 | weekly | 5 mild · 10 moderate · 15 severe [C] | `[GAD7]` |
| `I-BEH-pss` | 0–40 | monthly | ≥ 27 "high" (commonly used band, not a validated cut-off) [T]; rise ≥ 5 vs passport [T] | `[PSS]` |
| `I-BEH-who5` | 0–100 | monthly | ≤ 50 poor well-being; ≤ 28 likely depression → PHQ-9 [C] | `[WHO5]` |
| `I-BEH-ucla3` | 3–9 | monthly | ≥ 6 lonely [C] | `[UCLA3]` |
| `I-BEH-family_contact_days` | days since last | auto | > 14 days → reminder [T] | `[TB016]` |

## 8. Labs (`I-LAB-*`) — at periodic exams if onboard analyser exists; passport baselines otherwise
| ID | Unit | Thresholds | Refs |
|---|---|---|---|
| `I-LAB-wbc` | ×10³/µL | lab range from passport (Inspiration4 format) | `[OSD569]` |
| `I-LAB-lymphocytes_abs` | cells/µL | drop > 50% vs baseline within 48 h of SPE → ARS concern [T] | `[TB020]`, `[OSD569]` |
| `I-LAB-hemoglobin` | g/dL | below lab range → anemia flag [C] | `[OSD569]` |
| `I-LAB-sodium` | mmol/L | > 145 → dehydration [N] | `[NUTR-ER]` |
| `I-LAB-creatinine` | mg/dL | > 1.5 × baseline [C] | `[OSD575]` |
| `I-LAB-urine_osm` | mOsm/kg | > 700 → under-hydrated [N] | `[NUTR-ER]` |
| `I-LAB-vitd` | ng/mL | < 35 supplement · < 20 treat [N] | `[TB030]` |
| `I-LAB-urine_blood` | dipstick | positive + flank pain → stone [C] | `[STONE]` |
| `I-LAB-urine_nitrite_le` | dipstick | positive + dysuria → UTI [C] | `[T]` |

## 9. Environment (`I-ENV-*`) — from habitat sensors
| ID | Unit | Thresholds | Refs |
|---|---|---|---|
| `I-ENV-co2_1h` | mmHg | > 3.0 (1-h average) [N] | `[STD3001-V2]`, `[TB004]` |
| `I-ENV-co2_7d` | mmHg | > 2.5 → headache risk > 1% [N] | `[TB004]` |
| `I-ENV-pio2` | mmHg | normoxia 145–155; < 127 mild-hypoxia limit [N] | `[STD3001-V2]` |
| `I-ENV-cabin_alt` | ft equivalent | > 8,300 ft equivalent → hypoxia watch [N] | `[RISK-HYPOX]` |
| `I-ENV-cabin_temp` | °C | outside 18–27 [N] | `[STD3001-V2]` |
| `I-ENV-humidity` | % RH | outside 25–75 [N] | `[STD3001-V2]` |
| `I-ENV-noise_dose` | % of 24-h dose | > 100 [N]; sleep quarters > NC-40 [N] | `[STD3001-V2]` |
| `I-ENV-ammonia_alarm` | bool | true → toxic exposure protocol [N] | `[IMM-MYERS]` |
| `I-ENV-smoke_alarm` | bool | true → smoke inhalation protocol [N] | `[IMM-MYERS]` |
| `I-ENV-depress_alarm` | bool | true → barotrauma / hypoxia / DCS watch [N] | `[RISK-DCS]` |
| `I-ENV-microbial_alert` | bool | water/surface contamination → infection watch [N] | `[RISK-HMI]` |

## 10. Radiation (`I-RAD-*`)
| ID | Unit | Thresholds | Refs |
|---|---|---|---|
| `I-RAD-dose_today` | mSv | context: transit ≈ 1.5 mSv/day, surface ≈ 0.5 mSv/day [N]; > 2× mission average → check [T] | `[TB020]` |
| `I-RAD-dose_cumulative` | mSv (incl. P-11 prior dose) | career limit < 600 [N]; ≥ 480 (80%) → ORANGE [T] | `[STD3001-V1]` |
| `I-RAD-bfo_30d` | mGy-Eq | blood-forming organs 30-day limit 250 [N] | `[STD3001-V1]` |
| `I-RAD-spe_alert` | bool | true → shelter (≥ 10 cm water eq.), end EVA within 2 h [N] | `[TB020]` |
| `I-RAD-neutron_fraction` | % | context: ≈ 30% of ISS dose [N] | `[CSA-RAD]` |

## 11. Mission context (`I-CTX-*`)
| ID | Unit | Use |
|---|---|---|
| `I-CTX-mission_day` | day | ≤ 3 adaptation window [T]; ≤ 14 back-pain window [T]; > 30 SANS window [T] |
| `I-CTX-gravity` | 0 / 0.16 / 0.38 / 1 g | Ottawa weight-bearing items only when > 0 g; orthostatic rules at transitions |
| `I-CTX-phase` | cruise / EVA day / landing / post-landing | phase-specific rules |
| `I-CTX-post_eva_hours` | h | ≤ 24 → DCS and EVA-injury rules active |
| `I-CTX-comm_delay_s` | s one-way | ISS ≈ 0 · Moon ≈ 1.3 · Mars up to ~1,200 (≈ 20 min) [N] → escalation mode |
| `I-CTX-hours_since_spe` | h | ARS symptom window ≤ 48 h [T] |
| `I-CTX-crew_symptom_cluster` | n crew with same symptom in 72 h | ≥ 2 → outbreak / environmental cause [T] `[RISK-HMI]` |

## 12. Derived facts (computed by the engine)
| Fact | Definition |
|---|---|
| `baseline(x)` | Passport value, replaced by rolling 14-day median after day 14 |
| `delta_pct(x)` | (x − baseline) / baseline |
| `days(cond)` | Consecutive days a condition held |
| `count_7d(cond)` | Days in the last 7 on which a condition held |
| `news2_total` | Sum of NEWS2 parameter scores (+3 new confusion, +2 supplemental O₂) `[NEWS2]` |
| `qsofa` | RR ≥ 22 + altered mentation + SBP ≤ 100 (0–3) `[SEPSIS3]` |
| `adaptation_window` | `mission_day ≤ 3` or ≤ 72 h after a gravity transition |
| `red_flag_any(system)` | Any RED rule fired in that system — blocks GREEN "expected adaptation" rules |
