# 07 — Action / countermeasure library

Text shown to the astronaut (English UI). **No drug names with doses**: medication always says "per onboard medical checklist / CMO".
`Who`: 🧑‍🚀 self · 👥 crewmate · 🩺 CMO · 🌍 flight surgeon / ground.

## General
| ID | Action (UI text) | Who | Ref |
|---|---|---|---|
| A-GEN-01 | Repeat this measurement now with the guided steps (or in the time shown). | 🧑‍🚀 | `[NEWS2]` |
| A-GEN-02 | Inform your Crew Medical Officer now. | 🩺 | `[STD3001-V1]` |
| A-GEN-03 | Send the flight-surgeon packet (summary, trend, rule trace). With a long comm delay, start the onboard steps first. | 🌍 | `[RISK-SYS]`, `[EXMC-CDS]` |
| A-GEN-04 | Follow the onboard medical checklist for this condition; medication only as the checklist / CMO directs. | 🩺 | `[CHECS]` |
| A-GEN-05 | Recheck in 24 h (scheduled reminder). | 🧑‍🚀 | `[T]` |
| A-GEN-06 | Added to today's medical downlink. | 🌍 | `[CHECS]` |
| A-GEN-07 | Stop the current activity and rest. | 🧑‍🚀 | `[T]` |
| A-GEN-08 | No EVA, piloting or safety-critical tasks until cleared by CMO. | 🩺 | `[RISK-SLEEP]`, `[RISK-SMV]` |
| A-GEN-09 | Take a photo for the medical log (same angle and light each time). | 🧑‍🚀 | `[T]` |
| A-GEN-10 | Emergency: alert the crew; CMO leads; get the emergency/trauma medical pack. | 👥 🩺 | `[AHA-ACLS]`, `[ATLS]`, `[CHECS]` |
| A-GEN-11 | Hygiene and isolation: wash/sanitise hands, mask, own utensils and towel, disinfect touched surfaces. | 🧑‍🚀 | `[RISK-HMI]` |
| A-GEN-12 | Ask crewmates whether anyone has the same symptoms (possible outbreak or environmental cause). | 👥 | `[RISK-HMI]` |
| A-GEN-13 | Start the guided symptom interview (tap the body region, answer onset / severity / red-flag questions). | 🧑‍🚀 | `[NRS-PAIN]` |

## Sleep and fatigue
| ID | Action | Who | Ref |
|---|---|---|---|
| A-SLP-01 | Keep a fixed sleep window tonight (same start time ±30 min). | 🧑‍🚀 | `[TB041]` |
| A-SLP-02 | Dim, blue-reduced light 1 h before sleep; bright light after waking (Earth-like light schedule). | 🧑‍🚀 | `[TB041]`, `[RISK-SLEEP]` |
| A-SLP-03 | Caffeine only in the first half of your work day. | 🧑‍🚀 | `[TB041]` |
| A-SLP-04 | Take a 20–40 min nap if the schedule allows (quiet, < 50 dB). | 🧑‍🚀 | `[RISK-SLEEP]` |
| A-SLP-05 | Eye mask, earplugs, secure sleeping bag; check sleep-station temperature and noise. | 🧑‍🚀 | `[TB041]`, `[STD3001-V2]` |
| A-SLP-06 | Ask for a rest block / move non-critical tasks (workload review). | 🩺 🌍 | `[RISK-SLEEP]` |
| A-SLP-07 | Review sleep-medication use with the CMO. | 🩺 | `[BARGER2014]` |

## Behavioral health
| ID | Action | Who | Ref |
|---|---|---|---|
| A-BEH-01 | Book a private psychological conference. | 🌍 | `[TB016]` |
| A-BEH-02 | Schedule a video call with family or friends. | 🧑‍🚀 | `[TB016]`, `[RISK-BMED]` |
| A-BEH-03 | Try one of *your* helpers from your passport (e.g. music, exercise, journaling). | 🧑‍🚀 | `[TB016]` |
| A-BEH-04 | Journal for 5 minutes (private). | 🧑‍🚀 | `[TB016]` |
| A-BEH-05 | Plan one task you choose yourself today (autonomy over schedule). | 🧑‍🚀 | `[TB016]`, `[RISK-TEAM]` |
| A-BEH-06 | Earth observation / photography session, or time with the plant garden. | 🧑‍🚀 | `[RISK-BMED]`, `[TB016]` |
| A-BEH-07 | Crew debrief or the conflict-resolution guide. | 👥 | `[RISK-TEAM]` |
| A-BEH-08 | Behavioral emergency: you are not alone — contact the CMO and the psychologist now (private channel). Crew stays with you. | 🩺 🌍 | `[TB016]` |
| A-BEH-09 | 3-minute guided breathing / relaxation (VR if available). | 🧑‍🚀 | `[RISK-IMMUNE]`, `[TB016]` |
| A-BEH-10 | Take the PHQ-9 / GAD-7 now (2 min). | 🧑‍🚀 | `[PHQ9]`, `[GAD7]` |

## Cardiovascular
| ID | Action | Who | Ref |
|---|---|---|---|
| A-CV-01 | Lie down (or restrain supine); legs elevated in gravity. | 🧑‍🚀 | `[CV-ER]` |
| A-CV-02 | Fluid and salt loading per protocol. | 🩺 | `[CV-ER]` |
| A-CV-03 | Put on the compression garment. | 🧑‍🚀 | `[CV-ER]` |
| A-CV-04 | Record an ECG strip and attach it to the report. | 🧑‍🚀 🩺 | `[TEMPUS]` |
| A-CV-05 | Rest 5 min, then repeat BP (same arm, seated/restrained). | 🧑‍🚀 | `[AHA-BP]` |
| A-CV-06 | Neck (jugular) ultrasound by CMO with ground guidance. | 🩺 🌍 | `[MARSHALL-GOEBEL2019]` |
| A-CV-07 | Cardiac arrest: start CPR, get the defibrillator, CMO leads. | 👥 🩺 | `[AHA-ACLS]` |

## Breathing / oxygen
| ID | Action | Who | Ref |
|---|---|---|---|
| A-RESP-01 | Supplemental oxygen per protocol. | 🩺 | `[NEWS2]`, `[CHECS]` |
| A-RESP-02 | Check cabin O₂ partial pressure / pressure altitude with life support. | 👥 | `[STD3001-V2]` |
| A-RESP-03 | Choking: abdominal thrusts (brace against a wall in 0 g) / back blows; call crew. | 👥 | `[AHA-ACLS]` |
| A-RESP-04 | Smoke: emergency mask, leave the module, oxygen per protocol. | 👥 | `[IMM-MYERS]` |

## Neuro
| ID | Action | Who | Ref |
|---|---|---|---|
| A-NEU-01 | BE-FAST check now; record the time symptoms started. | 👥 | `[BEFAST]` |
| A-NEU-02 | Neuro checks (GCS, pupils, limbs) every 15 min for 2 h, then hourly. | 👥 🩺 | `[GCS]` |
| A-NEU-03 | Seizure: protect from injury, restrain loosely, time it, nothing in the mouth, recovery position after. | 👥 | `[IMM-MYERS]` |
| A-NEU-04 | Answer the headache red-flag questions (SNNOOP10). | 🧑‍🚀 | `[SNNOOP10]` |

## Eyes
| ID | Action | Who | Ref |
|---|---|---|---|
| A-EYE-01 | Do the near-vision test in the app (each eye). | 🧑‍🚀 | `[RISK-SANS]` |
| A-EYE-02 | Schedule OCT / ocular ultrasound at the next CMO exam. | 🩺 | `[RISK-SANS]` |
| A-EYE-03 | Irrigate the eye with water/saline for at least 15 min. | 👥 | `[IMM-MYERS]` |
| A-EYE-04 | Cover with a rigid eye shield; no pressure on the eye. | 👥 | `[IMM-MYERS]` |
| A-EYE-05 | Remove contact lenses. | 🧑‍🚀 | `[T]` |
| A-EYE-06 | Wear goggles when working with particles or debris (they float in 0 g). | 🧑‍🚀 | `[T]` |

## Ear / nose / throat
| ID | Action | Who | Ref |
|---|---|---|---|
| A-ENT-01 | Decongestant per onboard checklist; head-up position if possible. | 🧑‍🚀 | `[IMM-INC]` |
| A-ENT-02 | Equalise pressure (gentle Valsalva); stop pressure changes if painful. | 🧑‍🚀 | `[IMM-MYERS]` |
| A-ENT-03 | Nosebleed: pinch the soft part of the nose 10–15 min, lean forward, absorbent pad (blood floats). | 🧑‍🚀 | `[T]` |
| A-ENT-04 | Hearing protection; review noise exposure. | 🧑‍🚀 | `[STD3001-V2]` |
| A-ENT-05 | Keep the ear canal dry; clean headset ear pieces. | 🧑‍🚀 | `[T]` |

## Dental
| ID | Action | Who | Ref |
|---|---|---|---|
| A-DENT-01 | Temporary filling / cement from the dental kit. | 🩺 | `[CHECS]` |
| A-DENT-02 | Knocked-out tooth: hold by the crown, rinse, re-implant now or keep in saline/milk; CMO. | 🩺 | `[IMM-MYERS]` |
| A-DENT-03 | Pain relief per onboard checklist. | 🧑‍🚀 | `[CHECS]` |
| A-DENT-04 | Brush, floss, rinse after meals. | 🧑‍🚀 | `[T]` |

## GI
| ID | Action | Who | Ref |
|---|---|---|---|
| A-GI-01 | Oral rehydration: small sips often; track fluids. | 🧑‍🚀 | `[NUTR-ER]` |
| A-GI-02 | Fibre and fluids; regular toilet time. | 🧑‍🚀 | `[T]` |
| A-GI-03 | Small frequent meals; limit head movements; medication per checklist. | 🧑‍🚀 | `[RISK-SMV]` |
| A-GI-04 | Guided abdominal check (where it hurts, rebound, guarding); repeat every 2 h. | 👥 🩺 | `[ALVARADO]` |
| A-GI-05 | Nothing by mouth until the CMO reviews. | 🩺 | `[ATLS]` |

## GU
| ID | Action | Who | Ref |
|---|---|---|---|
| A-GU-01 | Urine dipstick test (blood, nitrite, leukocytes). | 🧑‍🚀 | `[STONE]` |
| A-GU-02 | Drink to at least 2.5 L today (3.0 L if you have a kidney-stone history). | 🧑‍🚀 | `[STD3001-V2]`, `[TB030]` |
| A-GU-03 | Bladder catheter per onboard checklist (CMO). | 🩺 | `[IMM-INC]` |
| A-GU-04 | Timed voiding every 2–3 h. | 🧑‍🚀 | `[T]` |

## Musculoskeletal / trauma
| ID | Action | Who | Ref |
|---|---|---|---|
| A-MSK-01 | Rest the joint, cold pack, compression wrap; gentle movement as pain allows. | 🧑‍🚀 | `[T]` |
| A-MSK-02 | Splint / immobilise in the position found; CMO exam. | 👥 🩺 | `[ATLS]` |
| A-MSK-03 | Ottawa ankle/knee check (guided). | 👥 | `[OTTAWA-ANKLE]`, `[OTTAWA-KNEE]` |
| A-MSK-04 | Back pain (space adaptation): knees-to-chest position, gentle stretching, loading exercise. | 🧑‍🚀 | `[KERSTMAN2012]` |
| A-MSK-05 | Check circulation, sensation and movement beyond the injury every 30 min. | 👥 | `[ATLS]` |
| A-MSK-06 | Do today's resistance + aerobic session (goal ~1.5 h/day). | 🧑‍🚀 | `[RISK-FIT]`, `[TB030]` |
| A-MSK-07 | Adjust the exercise prescription with the ground team. | 🌍 | `[RISK-FIT]`, `[STD3001-V1]` |

## Skin
| ID | Action | Who | Ref |
|---|---|---|---|
| A-SKIN-01 | Clean and cover the wound; watch for redness or warmth. | 🧑‍🚀 | `[T]` |
| A-SKIN-02 | Firm pressure to stop bleeding; closure strips; CMO for deep wounds. | 👥 🩺 | `[ATLS]` |
| A-SKIN-03 | Mark the edge of the redness with a pen; recheck in 12 h. | 🧑‍🚀 | `[T]` |
| A-SKIN-04 | Cool the burn with running/clean water for 20 min; cover loosely; chemical burn → irrigate. | 👥 | `[WALLACE]` |
| A-SKIN-05 | Moisturise; avoid the irritant; check humidity. | 🧑‍🚀 | `[STD3001-V2]` |
| A-SKIN-06 | Glove fit check; protect nails (tape, trimmed) before the next EVA. | 🧑‍🚀 | `[RISK-EVA]` |

## Immune / allergy
| ID | Action | Who | Ref |
|---|---|---|---|
| A-IMM-01 | Antihistamine per onboard checklist; avoid the trigger. | 🧑‍🚀 | `[ANAPH]` |
| A-IMM-02 | Anaphylaxis protocol: emergency injector per checklist, oxygen, lie flat, crew alert. | 👥 🩺 | `[ANAPH]` |
| A-IMM-03 | Antiviral only if the CMO / flight surgeon decides. | 🩺 | `[RISK-IMMUNE]` |
| A-IMM-04 | Immune support: sleep window, stress reduction, diet and vitamin D plan. | 🧑‍🚀 | `[RISK-IMMUNE]` |

## Nutrition
| ID | Action | Who | Ref |
|---|---|---|---|
| A-NUT-01 | Low sugar: take 15–20 g fast carbohydrate now; recheck in 15 min. | 🧑‍🚀 | `[ADA-SOC]` |
| A-NUT-02 | Add your preferred foods and snacks today. | 🧑‍🚀 | `[NUTR-ER]` |
| A-NUT-03 | Dietitian review via downlink. | 🌍 | `[NUTR-ER]` |
| A-NUT-04 | Vitamin D plan per flight surgeon. | 🌍 | `[TB030]` |
| A-NUT-05 | Review meals, activity and timing of the glucose test; report. | 🧑‍🚀 🌍 | `[ADA-SOC]` |

## Radiation
| ID | Action | Who | Ref |
|---|---|---|---|
| A-RAD-01 | Go to the storm shelter (≥ 10 cm water equivalent) until the all-clear. | 👥 | `[TB020]` |
| A-RAD-02 | End the EVA and return inside within 2 h. | 👥 | `[TB020]` |
| A-RAD-03 | Review dose with the ground; plan shielding and EVA exposure. | 🌍 | `[STD3001-V1]` |
| A-RAD-04 | Blood count (lymphocytes) if an analyser is available; repeat at 24 h. | 🩺 | `[TB020]` |

## Environment
| ID | Action | Who | Ref |
|---|---|---|---|
| A-ENV-01 | Move to a better-ventilated module; report CO₂ to life support; recheck symptoms in 1 h. | 🧑‍🚀 👥 | `[TB004]` |
| A-ENV-02 | Ammonia: emergency mask, leave and isolate the module, irrigate eyes and skin. | 👥 | `[IMM-MYERS]` |
| A-ENV-03 | Adjust thermal control / airflow at the sleep station or work area. | 👥 | `[STD3001-V2]` |
| A-ENV-04 | Report for water / surface microbial sampling. | 👥 🌍 | `[RISK-HMI]` |

## EVA
| ID | Action | Who | Ref |
|---|---|---|---|
| A-EVA-01 | Breathe 100% oxygen and repressurise per the DCS protocol. | 👥 🩺 | `[RISK-DCS]` |
| A-EVA-02 | Post-EVA: rest, rehydrate, eat (+200 kcal per EVA hour). | 🧑‍🚀 | `[STD3001-V2]`, `[RISK-EVA]` |
| A-EVA-03 | Review suit and glove fit, padding at contact points. | 👥 🌍 | `[RISK-EVA]` |
