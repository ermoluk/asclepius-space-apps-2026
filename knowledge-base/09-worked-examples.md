# 09 — Worked examples (how the engine reasons)

CF combination: `CF = a + b(1 − a)`. Passport modifiers add to a rule's CF (capped at 0.99). Level = highest level among fired rules.

---

## Scenario 1 — Sleep debt → fatigue (Mars transit, day 47, comm delay 12 min 40 s)

**Inputs**
| Indicator | Values |
|---|---|
| `sleep_hours` (last 4 nights) | 5.5 · 5.2 · 5.8 · 5.4 |
| `pvt_rt` | 312 ms (passport baseline 262 ms → +19%) |
| `kss` (morning) | 7 |
| `workload` (last 3 evenings) | 8 · 9 · 8 |
| `mood_valence` | 3 |

**Rules fired**
| Rule | Pattern matched | Hypothesis | CF |
|---|---|---|---|
| R-SLP-01 | sleep ≤ 6 h for 4 days | X01 Sleep deficit | 0.80 |
| R-SLP-05 | X01 + PVT +19% (> 15%) | X02 Fatigue impairing performance | 0.75 |
| R-SLP-04 | KSS 7 | X02 | 0.60 |
| R-SLP-08 | workload ≥ 8 on 3 days + sleep < 6 | X02 | 0.50 |
| R-BEH-10 | not fired (mood 3 > 2) | — | — |

**Certainty for X02**: 0.75 → 0.75 + 0.60 × 0.25 = **0.90** → 0.90 + 0.50 × 0.10 = **0.95**

**Output**
| Hypothesis | Confidence | Level | Why (shown in UI) | What to do |
|---|---|---|---|---|
| Fatigue impairing performance | 95% | 🟠 | 4 nights < 6 h (need 7–9 h `[TB041]`); reaction time 19% slower than your baseline `[RST-ISS]`; KSS 7 `[KSS]`; heavy workload 3 days | A-GEN-08 no EVA/critical tasks today · A-SLP-04 nap · A-GEN-02 tell CMO |
| Sleep deficit | 80% | 🟡 | Sleep ≤ 6 h for 4 days `[RISK-SLEEP]` | A-SLP-01, A-SLP-02, A-SLP-03, A-SLP-05 |
Overall status: 🟠. Next best measurement: repeat PVT after the nap.

---

## Scenario 2 — CO₂ headache or SANS? (day 47)

**Inputs (evening)**: `headache` = yes (NRS 4) · `co2_1h` = 3.4 mmHg · `co2_7d` = 2.7 mmHg · `blurred_near_vision` = yes ·
`mission_day` = 47 · `near_acuity` = not measured yet · passport: SANS-risk allele (P-03).

**Step 1 — rules fired**
| Rule | Hypothesis | CF |
|---|---|---|
| R-NEU-01 (headache + CO₂ 1 h > 3.0) | C051 Headache (CO₂) | 0.75 |
| R-NEU-02 (headache + CO₂ 7 d > 2.5) | C051 | 0.50 |
| R-ENV-01 (CO₂ 1 h > 3.0) | C051 | 0.20 |
| R-EYE-01 (headache + near blur + day > 30) | C098 SANS | 0.60 |
| R-EYE-03 (P-03 modifier) | C098 | +0.10 → 0.70 |
| R-EYE-02 (acuity decline) | pending — `near_acuity` missing | — |

C051: 0.75 → 0.875 → 0.875 + 0.2 × 0.125 = **0.90** (🟡). C098: **0.70** (🟠).

**Step 2 — next best measurement.** Active ORANGE hypothesis C098 lists `near_acuity`; it is missing → the app asks:
"Do the 1-minute near-vision test (each eye)."

**Step 3 — after the test**: right eye 1 line worse than baseline, left unchanged → R-EYE-02 fires (CF 0.5).
C098: 0.70 + 0.5 × 0.30 = **0.85** (🟠).

**Output**
| Hypothesis | Confidence | Level | What to do |
|---|---|---|---|
| SANS suspected | 85% | 🟠 | A-EYE-02 OCT/ultrasound at next exam · A-GEN-06 downlink · inform flight surgeon |
| Headache from CO₂ | 90% | 🟡 | A-ENV-01 move to better-ventilated module; report CO₂; recheck in 1 h |
Both can be true: the explanation panel shows that CO₂ explains the headache, but not the one-eye acuity change `[TB004]`, `[RISK-SANS]`.

---

## Scenario 3 — Solar particle event (Mars transit, comm delay 12 min 40 s)

| Time | Event / input | Rules fired | Result |
|---|---|---|---|
| T0 | `spe_alert` = true | R-RAD-01 | 🟠 "Go to storm shelter; end EVA within 2 h" (A-RAD-01, A-RAD-02) `[TB020]` |
| T0 + 6 h | event check: no symptoms | — | stays 🟠 until all-clear |
| T0 + 20 h | `nausea` = yes, `fatigue` = yes | R-RAD-05 (≤ 48 h after SPE) → C011 0.60; R-GI-17 (nausea after day 4) → reconsider | 🔴 Acute radiation syndrome suspected (60%) |
| T0 + 24 h | `lymphocytes_abs` −55% vs baseline | R-RAD-06 → C011 0.85 | C011 = 0.60 + 0.85 × 0.40 = **0.94** 🔴 |

Because `comm_delay_s` = 760 > 300, the RED screen shows **onboard first** (A-GEN-02 CMO now, A-RAD-04 repeat blood count, hydration),
then the packet:

```
FLIGHT-SURGEON PACKET  ·  Crew: CM-2  ·  Mission day 112  ·  Sent 14:05 MET (arrives ~14:18)
STATUS: RED — Acute radiation syndrome suspected (94%)
TIMELINE: SPE alert T0 · shelter 0:20 · nausea + fatigue T0+20 h · lymphocytes −55% at T0+24 h
DOSE: event 38 mSv (dosimeter) · cumulative 109 / 600 mSv
VITALS (T0+24 h): HR 96 · BP 118/76 · SpO2 98 · T 37.4 · NEWS2 1
RULES: R-RAD-05, R-RAD-06 (TB020) · R-GI-17
ONBOARD ACTIONS DONE: CMO informed 14:01 · fluids started · blood count repeat scheduled 24 h
REQUEST: guidance on antiemetic / further management
```

---

## Scenario 4 — Day 2: reassure, but never hide a red flag

**Variant A — inputs**: `mission_day` = 2 · `headache` (NRS 3) · `nasal_congestion` · `nausea` · `back_pain` (NRS 3) · no fever ·
passport: motion sickness on previous flight (P-01).

| Rule | Hypothesis | CF | Level |
|---|---|---|---|
| R-NEU-03 † | C053 Headache (SAS) | 0.70 | 🟢 |
| R-ENT-01 † | C069 Nasal congestion (SAS) | 0.70 | 🟢 |
| R-VES-01 + P-01 | C089 Space motion sickness | 0.80 + 0.15 = 0.95 | 🟡 |
| R-MSK-01 † | C022 Back pain (SAS) | 0.70 | 🟢 |

Overall 🟡. UI message: "These are common in the first days of flight (headache in 92% of ISS astronauts `[HEADACHE2024]`, back pain
in 52% `[KERSTMAN2012]`). Here is what helps…" — reassurance plus countermeasures.

**Variant B** — same day, but the headache is sudden, "worst ever", with vomiting twice.
R-NEU-05 fires (red flag, SNNOOP10) → `red_flag_any(NEURO)` = true → **R-NEU-03 † is blocked**, so the headache is *not* labelled
"expected". Output 🔴 "Possible secondary headache — CMO now", BE-FAST check (A-NEU-01) and flight-surgeon packet `[SNNOOP10]`.

---

## What these examples demonstrate
1. **Combining factors** (sleep + PVT + KSS + workload) gives higher confidence than any single number.
2. **Environment as an input** separates a CO₂ headache from a possible SANS case.
3. **Next best measurement** turns a vague suspicion into a specific, quick test.
4. **Comm-delay awareness** changes the order of actions on Mars.
5. **Personalisation** (P-01, P-03) changes confidence for the same symptoms.
6. **Safety guard**: "expected adaptation" never hides a red flag.
