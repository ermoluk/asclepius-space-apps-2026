# 02 — Daily self-checks (morning / evening), event-triggered and periodic checks

> RU: Рекомендация — **2 обязательные самооценки в день: утром (после сна) и вечером (перед сном)**, плюс необязательная «эмоция прямо
> сейчас» в любой момент, плюс внеплановые проверки по событиям (выход в открытый космос, солнечная вспышка, новый симптом, посадка).
> Утро — тело и сон, вечер — настроение и день. Так устроены опросы NASA (после сна и перед сном) и Apple Health (эмоция сейчас / настроение за день).

## Why twice a day
| Evidence | What it says | Design consequence |
|---|---|---|
| NASA Standard Measures `[STDMEAS]` | Daily **post-sleep** survey (sleep) and **pre-sleep** survey (mood, team cohesion, performance, living conditions) | Morning = body + sleep; evening = mind + day |
| ISS Reaction Self Test `[PVT-BASNER]`, `[RST-ISS]` | Morning and evening sessions: sleep log, ratings of stress / workload / fatigue / sleepiness, 3-min PVT | Optional PVT in both sessions |
| Apple Health State of Mind `[APPLE-SOM]` | Separates **momentary emotion** ("how you feel right now") from **daily mood** ("how you've felt overall today"); 7-point slider Very Unpleasant → Very Pleasant; feeling words + "what's affecting you"; default reminders mid-day and end of day | Evening = daily mood; any time = momentary emotion; same slider + labels + context |
| Circumplex model of affect `[CIRCUMPLEX]` | Emotions vary on valence (pleasant–unpleasant) and arousal | Slider = valence; labels cover high/low arousal |
| Single-item self-rated health `[SRH]` | One "how is your health" item predicts outcomes | One-tap "How does your body feel?" item |
| Burden | Crew time is scarce; Tempus Pro testing found complex interfaces were a problem `[TEMPUS]` | ≤ 2 min each; adaptive shortening |

Three or more scheduled check-ins add burden with little gain [T]; one per day misses the morning/evening split (sleep vs mood). Hence 2 + optional.

---

## 1. Morning check-in — "Body & Sleep" (≈ 90–120 s, within 60 min after wake)

| # | Item | Input | Indicator | Feeds rules |
|---|---|---|---|---|
| M1 | Sleep — auto from wearable, confirm or edit | hours (pre-filled) | `I-SLEEP-sleep_hours` | R-SLP-* |
| M2 | "How well did you sleep?" | 1–5 stars (NASA post-sleep style) | `I-SLEEP-sleep_quality` | R-SLP-03 |
| M3 | "How rested do you feel?" | KSS 1–9 `[KSS]` | `I-SLEEP-kss` | R-SLP-04 |
| M4 | **"How does your body feel?"** | 7-point slider Very bad → Very good (same widget as mood) | `I-SELF-physical_state` | R-SELF-01/02 |
| M5 | "Anything bothering you?" — tap body regions on the figure (head, eyes, ears/nose, mouth/teeth, chest, stomach, back, joints, skin, urination) → short symptom list per region | body map + chips | `I-SYM-*` | symptom rules |
| M6 | Morning vitals (scheduled days or when prompted): resting HR, BP, temp, SpO₂; fasting glucose on scheduled days | numbers, guided with "how to measure" | `I-VIT-*` | R-CV-*, R-NUTR-* |
| M7 | Optional 3-min reaction test (PVT) | game | `I-TEST-pvt_rt`, `I-TEST-pvt_lapses` | R-SLP-05 |
| M8 | Today's "focus" suggestion | output | — | from active hypotheses |

## 2. Evening check-in — "Mind & Day" (≈ 90–120 s, within 60 min before sleep)

| # | Item | Input | Indicator | Feeds rules |
|---|---|---|---|---|
| E1 | **"How have you felt overall today?"** (daily mood) | 7-point valence slider Very unpleasant → Very pleasant `[APPLE-SOM]` | `I-SELF-mood_valence` (1–7) | R-BEH-* |
| E2 | Feeling words (multi-select, max 5): calm, content, focused, motivated, grateful, tired, stressed, anxious, irritated, sad, lonely, bored, overwhelmed, homesick | chips | `I-SELF-mood_labels` | R-BEH-04/05 |
| E3 | "What's affecting you?": work, crewmates, family, health, sleep, food, exercise, environment (noise/CO₂/temp), news from Earth | chips | `I-SELF-mood_context` | explanations, countermeasure choice |
| E4 | Team cohesion: "How well did the crew work together today?" | 1–5 (Standard Measures item `[STDMEAS]`) | `I-BEH-team_cohesion` | R-BEH-06 |
| E5 | Workload: "How demanding was today?" | Bedford-style 1–10 `[BEDFORD]`, `[TB-COGWL]` | `I-BEH-workload` | R-SLP-07 |
| E6 | Fatigue now | Samn-Perelli 1–7 `[SAMN-PERELLI]` | `I-SLEEP-fatigue` | R-SLP-05 |
| E7 | Day log (pre-filled from devices, confirm): exercise minutes, fluids (L), food eaten (% of plan), caffeine after 14:00 | numbers | `I-NUTR-*`, `I-MSK-exercise_min` | R-NUTR-*, R-MSK-* |
| E8 | New or changed symptoms since morning | body map | `I-SYM-*` | symptom rules |
| E9 | Environment check (auto from habitat): CO₂, cabin temp, noise, dose today | auto | `I-ENV-*` | R-ENV-*, R-RAD-* |

## 3. Momentary emotion (any time, ≈ 10 s, optional)
Same valence slider + feeling words, labelled "right now" (`I-SELF-emotion_now`). Used for trends and to catch acute distress; never required.
A very unpleasant entry (1/7) prompts one supportive follow-up ("Would one of your helpers help now?" from passport J4) [T].

## 4. Event-triggered checks
| Trigger | Check | Timing | Feeds |
|---|---|---|---|
| After EVA (`I-CTX-post_eva_hours ≤ 24`) | DCS checklist (joint pain, tingling/numbness, skin mottling, vision, breathing, confusion), hand/fingernail and shoulder pain, fatigue, hydration `[RISK-DCS]`, `[RISK-EVA]` | 0 h, 6 h, 24 h | R-EVA-* |
| Solar particle event alert (`I-ENV-spe_alert`) | Shelter confirmation; then symptom check (nausea, vomiting, fatigue, skin redness) `[TB020]` | 0 h, 6 h, 24 h, 48 h | R-RAD-* |
| New symptom reported any time | Guided symptom interview for that region (onset, severity NRS 0–10 `[NRS-PAIN]`, red flags) | immediate | region rules |
| Gravity transition (landing, docking with lunar lander, return) | Orthostatic symptoms, dizziness, nausea, gait, BP lying/standing `[RISK-SMV]`, `[CV-ER]` | 0 h, 24 h, 72 h | R-CV-orthostatic, R-SMV-* |
| Cabin event (CO₂ spike, ammonia alarm, smoke, depressurization) | Symptom check per event `[TB004]`, `[IMM-MYERS]` | immediate, +1 h | R-ENV-* |
| Medication taken | Effect check after 1–2 h (helped? side effects?) | +1–2 h | follow-up rules |
| Injury | Mechanism, location, pain NRS, function tests (Ottawa-style where applicable) `[OTTAWA-ANKLE]` | immediate | R-TRA-* |

## 5. Periodic checks
| Period | Check | Source |
|---|---|---|
| Weekly | PHQ-9 `[PHQ9]`, GAD-7 `[GAD7]` (Apple Health offers the same two `[APPLE-MHA]`); body mass; near-vision self-test; exercise and sleep summary | `[RISK-BMED]`, `[RISK-SANS]` |
| Every 30 days | Fitness self-check (submax cycle HR), cognition tests, periodic health exam with CMO (BP, ECG, ultrasound when available) | `[RISK-FIT]`, `[STDMEAS]`, `[CHECS]` |
| Every 30 days (from day 30; weekly if `P-03`) | Neuro-ocular: near/far acuity each eye; OCT/ultrasound at CMO exam | `[RISK-SANS]` |
| Monthly | UCLA-3 loneliness `[UCLA3]`, PSS `[PSS]`, WHO-5 well-being `[WHO5]` (optional, rotate) | `[TB016]` |

---

## Scoring and display

### Daily Wellbeing Index (DWI) — display only, never used for triage
`DWI = 100 × mean(physical_state/7, mood_valence/7, min(sleep_hours/target,1), sleep_quality/5, 1 − symptom_burden)` [T]
- `symptom_burden` = min(1, Σ NRS of active symptoms / 20) [T]
- Shown as a ring with 7-day sparkline; compared with personal 14-day median.
- Triage always comes from rules (`05-rules.md`), never from DWI.

### Personal baselines
Rolling 14-day median for each self-report and vital, seeded with passport values (`01-physiological-passport.md`). First 3 days of flight are
flagged "adaptation window" (SAS conditions expected `[IMM-INC]`).

### Adaptive behaviour
| Situation | Behaviour [T] |
|---|---|
| All GREEN for 7 days | Shorter forms (skip M6/E7 confirmations, keep sliders) |
| Any ORANGE/RED active | Add targeted questions for that hypothesis ("Confirm with…") |
| Check-in missed | One reminder at +30 min; after 2 missed in a row → CMO sees "no data" (not "fine") |
| Very unpleasant mood 3 evenings in a row | Offer private conference booking; PHQ-9 early |
| Sleep < 6 h reported | Evening check-in includes light/caffeine plan for tonight `[TB041]` |

### Gamification (opt-in, M4)
- Streaks for completed check-ins, exercise minutes (1.5 h/day `[RISK-FIT]`), hydration ≥ 2.5 L `[STD3001-V2]`, sleep window kept.
- Crew-level goals (crew hydration %, crew exercise minutes) instead of individual leaderboards — avoids competition on health data [T].
- Badges tied to countermeasures ("7 nights in sleep window", "first Earth photo session"). No points for symptoms reporting being "low"
  (never reward hiding symptoms) [T].

### Privacy
Mood and behavioral answers: visible to the astronaut; shared per passport M3. CMO sees only the triage level for behavioral items unless the
astronaut shares details. RED behavioral (R-BEH-09) always reaches the psychologist/flight surgeon `[TB016]`.
