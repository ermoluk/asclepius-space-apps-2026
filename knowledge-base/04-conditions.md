# 04 — Conditions (diagnosis catalogue)

Master list: the **100 conditions of NASA's Integrated Medical Model** `[IMM-MYERS]` (C001–C100, numbered alphabetically as listed there) plus
**15 HRP-derived conditions** (X01–X15) that matter for performance but are not in the IMM list.
Type: **SAS** = space adaptation syndrome condition (counted per person, expected early in flight, does not recur `[IMM-INC]`) ·
**IMM** = other IMM condition (counted per person-year, can recur) · **X** = HRP-derived.
"Max" = highest triage level the condition can reach. "Confirm with" = next best measurement the engine asks for.

## Known in-flight frequencies (used as priors)
| Condition | Frequency | Refs |
|---|---|---|
| Headache (any) | 91.7% of ISS astronauts (prospective), mostly tension-type | `[HEADACHE2024]` |
| Space motion sickness | 67% on a first Shuttle flight (57 of 85); lower on a repeat flight, not significant | `[SMS-SHUTTLE]` |
| Back pain (SAS) | 52% (86% mild) | `[KERSTMAN2012]` |
| Nasal congestion (SAS) | 0.61 events per person | `[IMM-INC]` |
| Headache reports, CO₂ association study | 39% (19/49 astronauts); association, not proven cause; a later prospective study found no link with CO₂ | `[TB004]`, `[HEADACHE2024]` |
| Skin rash / hypersensitivity | 1.12 per flight-year (23 / 20.57); earlier cohort 1.25 (21 / 16.75) | `[CRUCIAN2016]`, `[ISS-EVENTS]` |
| Upper respiratory symptoms (congestion, rhinitis, sneezing; not confirmed infections) | 0.97 per flight-year (20 / 20.57); earlier cohort 0.66 (11 / 16.75) | `[CRUCIAN2016]`, `[ISS-EVENTS]` |
| Cold sores (HSV); skin infection | 0.3 per flight-year each (6 / 20.57); herpes zoster: 0 events in ISS Exp. 1–28/29 | `[CRUCIAN2016]`, `[ISS-EVENTS]` |
| All clinical events, ISS Exp. 1–28/29 | 3.3 per flight-year | `[ISS-EVENTS]` |
| Short sleep / hypnotic use | ~6 h average; hypnotics on 52% of nights | `[BARGER2014]` |
| Early SANS findings (optic disc edema on OCT) | ~70% of crew on 4–6-month missions; not severe disease, not an individual probability | `[RISK-SANS]` |
| Evacuation drivers in IMM | kidney stone, exposed dental pulp, skin infection, UTI, sepsis, AFib, chest injury, wrist fracture, toxic exposure, smoke inhalation | `[IMM-INC]` |

---

## A. NASA IMM conditions (C001–C100)

| ID | Condition | Sys | Type | What the app looks for | Max | Confirm with | Refs |
|---|---|---|---|---|---|---|---|
| C001 | Abdominal injury | TRAUMA | IMM | Blunt impact to abdomen + pain, guarding, falling BP / rising HR | RED | vitals q15 min; ultrasound (FAST) by CMO | `[IMM-MYERS]`, `[ATLS]` |
| C002 | Abdominal wall hernia | GI | IMM | New bulge in abdominal wall/groin, worse on straining; painful, irreducible → urgent | RED | guided palpation; pain NRS | `[IMM-MYERS]` |
| C003 | Abnormal uterine bleeding | GU | IMM | Bleeding outside expected pattern (passport C13), heavy flow, dizziness | ORANGE | Hb if available; HR/BP | `[IMM-MYERS]` |
| C004 | Acute arthritis | MSK | IMM | Hot, red, swollen joint ± fever | ORANGE | temperature; joint exam | `[IMM-MYERS]` |
| C005 | Acute cholecystitis / biliary colic | GI | IMM | RUQ pain after meals, nausea, ± fever | RED | temperature; ultrasound | `[IMM-MYERS]` |
| C006 | Acute compartment syndrome | TRAUMA | IMM | Limb injury + pain out of proportion, tense compartment, pain on passive stretch, numbness | RED | serial neuro-vascular checks | `[IMM-MYERS]`, `[ATLS]` |
| C007 | Acute diverticulitis | GI | IMM | LLQ pain, fever, change in bowel habit | ORANGE | temperature; WBC | `[IMM-MYERS]` |
| C008 | Acute glaucoma | EYE | IMM | Sudden painful red eye, halos around lights, blurred vision, headache, nausea | RED | IOP (tonometer) | `[IMM-MYERS]` |
| C009 | Acute pancreatitis | GI | IMM | Severe epigastric pain radiating to back, vomiting | RED | vitals; lipase if available | `[IMM-MYERS]` |
| C010 | Acute prostatitis | GU | IMM | Perineal pain, dysuria, fever | ORANGE | temperature; urine dipstick | `[IMM-MYERS]` |
| C011 | Acute radiation syndrome | RAD | IMM | Nausea / vomiting / fatigue / skin redness within 48 h of an SPE or high dose | RED | dose record; lymphocyte count trend | `[IMM-MYERS]`, `[TB020]` |
| C012 | Acute sinusitis | ENT | IMM | Facial pain/pressure + congestion > 10 days or worsening, ± fever | YELLOW | temperature | `[IMM-MYERS]` |
| C013 | Allergic reaction | IMMUNE | IMM | Hives, itching, mild swelling, no airway or circulation signs | YELLOW | recheck in 30 min for anaphylaxis signs | `[IMM-MYERS]`, `[ANAPH]` |
| C014 | Altitude sickness (hypobaric hypoxia) | RESP | IMM | Headache, confusion, insomnia, nausea at reduced cabin pressure / low pIO₂; SpO₂ low | RED | SpO₂; cabin pIO₂ | `[IMM-MYERS]`, `[RISK-HYPOX]` |
| C015 | Angina / myocardial infarction | CV | IMM | Pressure-like chest pain, esp. exertional, ± sweating, dyspnea, nausea | RED | ECG; HEART-score elements | `[IMM-MYERS]`, `[HEART]` |
| C016 | Anaphylaxis | IMMUNE | IMM | Skin/mucosal signs + breathing difficulty or low BP, minutes–hours after exposure | RED | BP, SpO₂, airway | `[IMM-MYERS]`, `[ANAPH]` |
| C017 | Ankle sprain / strain | MSK | IMM | Ankle injury, pain, swelling; Ottawa criteria negative | YELLOW | Ottawa ankle check | `[IMM-MYERS]`, `[OTTAWA-ANKLE]` |
| C018 | Anxiety | BEHAV | IMM | GAD-7 ≥ 10, "anxious/overwhelmed" labels, sleep loss | ORANGE | GAD-7 | `[IMM-MYERS]`, `[GAD7]`, `[TB016]` |
| C019 | Appendicitis | GI | IMM | Periumbilical → RLQ pain, anorexia, nausea, fever; Alvarado ≥ 7 | RED | Alvarado elements; WBC; ultrasound | `[IMM-MYERS]`, `[ALVARADO]` |
| C020 | Atrial fibrillation / flutter | CV | IMM | Palpitations, irregular pulse, dyspnea, dizziness | RED | ECG strip | `[IMM-MYERS]`, `[CV-ER]` |
| C021 | Back injury | MSK | IMM | Back pain after load/impact; neurological signs → RED | ORANGE | neuro check (strength, sensation, bladder) | `[IMM-MYERS]`, `[NICE-NG59]` |
| C022 | Back pain (SAS) | MSK | SAS | Low back ache in first ~2 weeks, no trauma, no red flags | GREEN | — | `[KERSTMAN2012]`, `[IMM-INC]` |
| C023 | Barotrauma (ear/sinus block) | ENT | IMM | Ear/sinus pain or fullness after pressure change (EVA, repress, depress) | YELLOW | hearing check | `[IMM-MYERS]` |
| C024 | Behavioral emergency | BEHAV | IMM | Self-harm thoughts (PHQ-9 item 9), hallucinations, danger to self/others | RED | private contact with psychologist | `[IMM-MYERS]`, `[TB016]`, `[PHQ9]` |
| C025 | Burns | SKIN | IMM | Thermal/electrical/chemical burn; size by rule of nines; face/hands/airway → RED | RED | % body area | `[IMM-MYERS]`, `[WALLACE]` |
| C026 | Cardiogenic shock | CV | IMM | Low BP, cold clammy skin, confusion, chest pain/arrhythmia | RED | BP, ECG, SpO₂ | `[IMM-MYERS]`, `[AHA-ACLS]` |
| C027 | Chest injury | TRAUMA | IMM | Chest impact + pain on breathing, dyspnea, low SpO₂ | RED | SpO₂, RR; ultrasound | `[IMM-MYERS]`, `[ATLS]` |
| C028 | Choking / obstructed airway | RESP | IMM | Cannot speak/cough/breathe after eating | RED | — (act immediately) | `[IMM-MYERS]`, `[AHA-ACLS]` |
| C029 | Constipation (SAS) | GI | SAS | No stool ≥ 3 days early in flight, no red flags | GREEN | — | `[IMM-INC]` |
| C030 | Decompression sickness (EVA) | EVA | IMM | Joint pain, tingling, skin mottling, dyspnea, confusion ≤ 24 h after EVA/depress | RED | neuro check; symptom recheck after repress | `[IMM-MYERS]`, `[RISK-DCS]` |
| C031 | Dental: exposed pulp | DENT | IMM | Broken tooth with exposed pink/bleeding centre, severe pain | ORANGE | photo; pain NRS | `[IMM-MYERS]`, `[IMM-INC]` |
| C032 | Dental caries | DENT | IMM | Sensitivity to sweet/cold, visible cavity | YELLOW | photo | `[IMM-MYERS]` |
| C033 | Dental abscess | DENT | IMM | Throbbing tooth pain, gum swelling, fever | ORANGE | temperature | `[IMM-MYERS]` |
| C034 | Dental avulsion | DENT | IMM | Tooth knocked out after impact | ORANGE | — (time-critical re-implant) | `[IMM-MYERS]` |
| C035 | Dental crown loss | DENT | IMM | Crown came off | YELLOW | — | `[IMM-MYERS]` |
| C036 | Dental filling loss | DENT | IMM | Filling lost, sensitivity | YELLOW | — | `[IMM-MYERS]` |
| C037 | Toothache | DENT | IMM | Tooth pain without visible cause | YELLOW | pain NRS, temperature | `[IMM-MYERS]` |
| C038 | Depression | BEHAV | IMM | PHQ-9 ≥ 10, low mood ≥ 5/7 days, withdrawal, sleep change | ORANGE | PHQ-9 | `[IMM-MYERS]`, `[PHQ9]`, `[RISK-BMED]` |
| C039 | Diarrhea | GI | IMM | ≥ 3 loose stools/day; dehydration signs | ORANGE | fluids, HR, temperature | `[IMM-MYERS]` |
| C040 | Elbow dislocation | TRAUMA | IMM | Elbow deformity after fall/load, cannot move | RED | neuro-vascular check of hand | `[IMM-MYERS]` |
| C041 | Elbow sprain / strain | MSK | IMM | Elbow pain after load, full range kept | YELLOW | function check | `[IMM-MYERS]` |
| C042 | Eye abrasion | EYE | IMM | Foreign-body sensation, tearing, pain after debris contact (debris floats in 0 g) | ORANGE | fluorescein exam by CMO | `[IMM-MYERS]` |
| C043 | Eye chemical burn | EYE | IMM | Chemical splash to eye | RED | — (irrigate immediately) | `[IMM-MYERS]` |
| C044 | Eye corneal ulcer | EYE | IMM | Painful red eye, discharge, contact-lens wearer | RED | CMO exam | `[IMM-MYERS]` |
| C045 | Eye infection (conjunctivitis) | EYE | IMM | Red eye, discharge, itch, vision normal | YELLOW | vision check | `[IMM-MYERS]` |
| C046 | Eye penetration | EYE | IMM | Penetrating eye injury | RED | — (shield, no pressure) | `[IMM-MYERS]` |
| C047 | Finger dislocation | TRAUMA | IMM | Finger deformity after impact | ORANGE | circulation/sensation of finger | `[IMM-MYERS]` |
| C048 | Fingernail delamination (EVA) | EVA | IMM | Fingernail lifting, pain after EVA glove use | YELLOW | photo | `[IMM-MYERS]`, `[RISK-EVA]` |
| C049 | Gastroenteritis | GI | IMM | Vomiting + diarrhea ± fever; crewmates with same symptoms | ORANGE | temperature; fluids; crew cluster | `[IMM-MYERS]`, `[RISK-HMI]` |
| C050 | Head injury | TRAUMA | IMM | Head impact; LOC, amnesia, vomiting ≥ 2, GCS < 15 → RED | RED | GCS; Canadian CT head rule elements | `[IMM-MYERS]`, `[GCS]`, `[CCHR]` |
| C051 | Headache (CO₂-associated) | ENV | IMM | Headache with CO₂ 1-h > 3.0 or 7-day > 2.5 mmHg | YELLOW | cabin CO₂; recheck after 1 h in fresh-air module | `[IMM-MYERS]`, `[TB004]` |
| C052 | Headache (late) | NEURO | IMM | Headache after the adaptation window, no CO₂ cause | YELLOW | red-flag screen (SNNOOP10); BP | `[IMM-MYERS]`, `[SNNOOP10]` |
| C053 | Headache (SAS) | NEURO | SAS | Headache in first 3 days, no red flags | GREEN | — | `[HEADACHE2024]`, `[IMM-INC]` |
| C054 | Hearing loss | ENT | IMM | Hearing change, tinnitus; noise dose > 100% | ORANGE | hearing self-test vs passport | `[IMM-MYERS]`, `[STD3001-V2]` |
| C055 | Hemorrhoids | GI | IMM | Rectal pain/bleeding with straining, constipation | YELLOW | — | `[IMM-MYERS]` |
| C056 | Herpes zoster reactivation | SKIN | IMM | Painful band-shaped rash on one side (VZV seropositive → P-04) | ORANGE | photo; temperature | `[IMM-MYERS]`, `[RISK-IMMUNE]` |
| C057 | Hip sprain / strain | MSK | IMM | Hip pain after load, can move | YELLOW | function check | `[IMM-MYERS]` |
| C058 | Hip / proximal femur fracture | TRAUMA | IMM | Fall/impact, severe hip pain, cannot move leg, shortened/rotated leg (risk ↑ with bone loss) | RED | ultrasound/CMO exam | `[IMM-MYERS]`, `[TB030]` |
| C059 | Hypertension | CV | IMM | BP ≥ 140/90 repeated; ≥ 180/120 crisis | RED | repeat BP after 5 min rest | `[IMM-MYERS]`, `[AHA-BP]` |
| C060 | Indigestion | GI | IMM | Heartburn, epigastric discomfort after meals | YELLOW | — | `[IMM-MYERS]` |
| C061 | Influenza | IMMUNE | IMM | Sudden fever, myalgia, cough, fatigue; crew cluster | ORANGE | temperature, SpO₂, NEWS2 | `[IMM-MYERS]`, `[RISK-HMI]` |
| C062 | Insomnia (SAS) | SLEEP | SAS | Difficulty sleeping in first days of flight | GREEN | sleep log 3 nights | `[IMM-INC]`, `[BARGER2014]` |
| C063 | Knee sprain / strain | MSK | IMM | Knee injury, pain; Ottawa knee negative | YELLOW | Ottawa knee check | `[IMM-MYERS]`, `[OTTAWA-KNEE]` |
| C064 | Late insomnia | SLEEP | IMM | Sleep < 6 h or poor quality beyond adaptation window | YELLOW | actigraphy; ISI | `[IMM-MYERS]`, `[RISK-SLEEP]`, `[ISI]` |
| C065 | Lower-extremity stress fracture | MSK | IMM | Localised bone pain with loading (partial-gravity surface ops, treadmill) | ORANGE | point tenderness; ultrasound | `[IMM-MYERS]`, `[TB030]` |
| C066 | Lumbar spine fracture | TRAUMA | IMM | High load (landing) + severe back pain, neuro signs | RED | neuro check | `[IMM-MYERS]`, `[RISK-DYN]` |
| C067 | Medication overdose / adverse reaction | ENV | IMM | New symptom 0–24 h after a medication; rash, drowsiness, confusion | ORANGE | medication log; vitals | `[IMM-MYERS]` |
| C068 | Mouth ulcer | DENT | IMM | Painful mouth sore | GREEN | — (escalate if > 2 weeks) | `[IMM-MYERS]` |
| C069 | Nasal congestion (SAS) | ENT | SAS | Stuffy nose / facial fullness from fluid shift, no fever | GREEN | — | `[IMM-INC]` |
| C070 | Nephrolithiasis (kidney stone) | GU | IMM | Colicky flank pain → groin, blood in urine, nausea (urine Ca +50% in flight) | RED | urine dipstick; STONE elements; ultrasound | `[IMM-MYERS]`, `[TB030]`, `[STONE]` |
| C071 | Neurogenic shock | TRAUMA | IMM | Spinal injury + low BP with slow HR, warm skin | RED | BP, HR, neuro check | `[IMM-MYERS]`, `[ATLS]` |
| C072 | Nosebleed (SAS) | ENT | SAS | Nosebleed early in flight, stops with pressure < 20 min | GREEN | — (ORANGE if > 20 min) | `[IMM-INC]` |
| C073 | Otitis externa | ENT | IMM | Ear canal pain, worse when pulling ear, itch, discharge (headsets, humidity) | YELLOW | — | `[IMM-MYERS]` |
| C074 | Otitis media | ENT | IMM | Ear pain, fullness, reduced hearing ± fever | YELLOW | temperature | `[IMM-MYERS]` |
| C075 | Paresthesias | NEURO | IMM | Tingling/numbness (EVA suit pressure points, or neuro cause) | ORANGE | distribution; post-EVA? | `[IMM-MYERS]` |
| C076 | Pharyngitis | ENT | IMM | Sore throat; Centor ≥ 3 suggests bacterial | YELLOW | Centor elements; temperature | `[IMM-MYERS]`, `[CENTOR]` |
| C077 | Respiratory infection | RESP | IMM | Cough, congestion, fever; low SpO₂ → ORANGE/RED | ORANGE | temperature, SpO₂, RR | `[IMM-MYERS]`, `[NEWS2]` |
| C078 | Retinal detachment | EYE | IMM | Flashes, new floaters, curtain over vision | RED | visual field check | `[IMM-MYERS]` |
| C079 | Seizures | NEURO | IMM | Witnessed convulsion / loss of awareness | RED | — (protect, time it) | `[IMM-MYERS]` |
| C080 | Sepsis | IMMUNE | IMM | Infection + qSOFA ≥ 2 or NEWS2 ≥ 7 | RED | vitals; qSOFA | `[IMM-MYERS]`, `[SEPSIS3]`, `[NEWS2]` |
| C081 | Shoulder dislocation | TRAUMA | IMM | Shoulder deformity after load (EVA, translation), cannot move | ORANGE | neuro-vascular check of arm | `[IMM-MYERS]` |
| C082 | Shoulder sprain / strain | MSK | IMM | Shoulder pain after EVA/exercise, movement kept | YELLOW | function check | `[IMM-MYERS]`, `[RISK-EVA]` |
| C083 | Skin abrasion | SKIN | IMM | Superficial scrape | GREEN | — (watch for infection) | `[IMM-MYERS]` |
| C084 | Skin infection | SKIN | IMM | Red, warm, spreading, painful skin ± fever (an IMM evacuation driver) | ORANGE | mark border; temperature | `[IMM-MYERS]`, `[IMM-INC]` |
| C085 | Skin laceration | SKIN | IMM | Cut; deep / gaping / bleeding > 10 min → ORANGE | ORANGE | photo; bleeding control | `[IMM-MYERS]` |
| C086 | Skin rash | SKIN | IMM | Rash / hypersensitivity without systemic signs (most common ISS event) | YELLOW | photo; temperature | `[IMM-MYERS]`, `[CRUCIAN2016]` |
| C087 | Small bowel obstruction | GI | IMM | Colicky abdominal pain, vomiting, distension, no stool/flatus | RED | — | `[IMM-MYERS]` |
| C088 | Smoke inhalation | ENV | IMM | Fire/smoke event + cough, dyspnea, low SpO₂ | RED | SpO₂ | `[IMM-MYERS]` |
| C089 | Space motion sickness (SAS) | VEST | SAS | Nausea/vomiting, malaise in first 72 h or after gravity transition | YELLOW | — | `[SMS-SHUTTLE]`, `[RISK-SMV]`, `[PENSACOLA]` |
| C090 | Stroke | NEURO | IMM | Sudden one-sided weakness, facial droop, speech trouble, vision loss, imbalance (BE-FAST) | RED | BE-FAST; time of onset | `[IMM-MYERS]`, `[BEFAST]` |
| C091 | Sudden cardiac arrest | CV | IMM | Unresponsive, not breathing normally | RED | — (CPR/defibrillation) | `[IMM-MYERS]`, `[AHA-ACLS]` |
| C092 | Toxic exposure (ammonia) | ENV | IMM | Ammonia alarm + eye/throat burning, cough | RED | SpO₂; eye irrigation | `[IMM-MYERS]` |
| C093 | Traumatic hypovolemic shock | TRAUMA | IMM | Bleeding/injury + HR > 100, falling BP, confusion | RED | vitals q5 min | `[IMM-MYERS]`, `[ATLS]` |
| C094 | Urinary incontinence (SAS) | GU | SAS | Leakage early in flight (altered bladder sensation) | GREEN | — | `[IMM-INC]` |
| C095 | Urinary retention (SAS) | GU | SAS | Cannot empty bladder early in flight (0 g, medications) | ORANGE | time since last void; bladder ultrasound | `[IMM-INC]` |
| C096 | Urinary tract infection | GU | IMM | Dysuria, frequency ± fever (an IMM evacuation driver; urosepsis caused a real evacuation) | ORANGE | urine dipstick; temperature | `[IMM-MYERS]`, `[IMM-INC]` |
| C097 | Vaginal yeast infection | GU | IMM | Itch, discharge | YELLOW | — | `[IMM-MYERS]` |
| C098 | VIIP / SANS | EYE | IMM | Near-vision blur, acuity decline (one eye), headache, after day 30 | ORANGE | near acuity; OCT/ultrasound | `[IMM-MYERS]`, `[RISK-SANS]`, `[LEE2020]` |
| C099 | Wrist fracture | TRAUMA | IMM | Fall/impact on hand, deformity, bony tenderness (an IMM evacuation driver) | ORANGE | splint; CMO exam | `[IMM-MYERS]`, `[IMM-INC]` |
| C100 | Wrist sprain / strain | MSK | IMM | Wrist pain, no deformity, no bony tenderness | YELLOW | function check | `[IMM-MYERS]` |

## B. HRP-derived conditions (X01–X15)

| ID | Condition | Sys | What the app looks for | Max | Confirm with | Refs |
|---|---|---|---|---|---|---|
| X01 | Sleep deficit | SLEEP | Sleep ≤ 6 h × 3 days (< 6 h × 2 if P-10) | YELLOW | actigraphy | `[RISK-SLEEP]`, `[TB041]` |
| X02 | Fatigue impairing performance | SLEEP | Sleep deficit + PVT slower / KSS ≥ 7 / Samn-Perelli ≥ 5 | ORANGE | PVT now | `[RISK-SLEEP]`, `[PVT-BASNER]`, `[SAMN-PERELLI]` |
| X03 | Orthostatic intolerance | CV | Dizziness/fainting at gravity transition, orthostatic BP drop | ORANGE | lying/standing BP | `[CV-ER]`, `[ORTHO2011]`, `[MECK2001]` |
| X04 | Jugular venous thrombosis | CV | One-sided neck/face swelling or pain, new headache, after day 30 | RED | neck ultrasound | `[CV-ER]`, `[MARSHALL-GOEBEL2019]` |
| X05 | Hypoglycemia | NUTR | Glucose < 70 (level 1) or < 54 (level 2) ± shakiness, sweating, confusion | RED | glucose recheck in 15 min | `[ADA-SOC]` |
| X06 | Hyperglycemia | NUTR | Fasting ≥ 126 on 2 days or random ≥ 200 + symptoms | ORANGE | fasting glucose; HbA1c at exam | `[ADA-SOC]` |
| X07 | Inadequate nutrition / weight loss | NUTR | Mass −5% / −7.7%, intake < 80% × 3 days | RED | weekly mass; food log | `[NUTR-ER]`, `[RISK-NUTR]` |
| X08 | Dehydration | NUTR | Fluids < 2.5 L, dark urine, Na > 145, vomiting/diarrhea | ORANGE | fluid log; urine color | `[NUTR-ER]`, `[STD3001-V2]` |
| X09 | Cumulative radiation exposure | RAD | Cumulative dose ≥ 80% of 600 mSv; BFO 30-day near 250 mGy-Eq | ORANGE | dosimeter readout | `[STD3001-V1]`, `[TB020]` |
| X10 | Deconditioning (aerobic, strength, bone) | MSK | Exercise < 90 min/day; aerobic or strength < 80% of pre-flight | ORANGE | submax cycle test | `[RISK-FIT]`, `[STD3001-V1]`, `[TB030]` |
| X11 | Heat stress / hyperthermia | ENV | Cabin/suit temp high + temp ≥ 38.1 + HR ↑, during EVA or exercise | ORANGE | temperature; HR | `[RISK-EVA]`, `[STD3001-V2]` |
| X12 | Team conflict / low cohesion | BEHAV | Cohesion ≤ 2 on ≥ 3/7 days; "crewmates" as negative context | YELLOW | crew debrief | `[RISK-TEAM]`, `[STDMEAS]` |
| X13 | Loneliness / isolation stress | BEHAV | "Lonely/homesick" labels, UCLA-3 ≥ 6, no family contact > 14 days | YELLOW | UCLA-3 | `[RISK-BMED]`, `[UCLA3]`, `[TB016]` |
| X14 | Cognitive decline vs baseline | BEHAV | Cognition z ≤ −1.5 or PVT lapses ×2 without sleep cause; CO₂/hypoxia check | ORANGE | repeat test; check CO₂, SpO₂ | `[COGNITION]`, `[TB016]`, `[TB004]` |
| X15 | Space anemia | CV | Hb below range, fatigue, reduced exercise tolerance (hemolysis ↑ in flight) | ORANGE | Hb at exam | `[TRUDEL2022]` |
