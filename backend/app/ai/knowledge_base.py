"""knowledge_base.py
====================
Clinical reference knowledge base for the MediSys disease-prediction system.

This module provides a structured, human-readable knowledge dictionary that
enriches AI predictions with actionable clinical context — severity levels,
recommended specialists, diagnostic tests, and self-care guidance.

Architecture role
-----------------
This module sits between the AI inference engine and the API response layer::

    predictor.py  ──►  diagnosis_service.py  ──►  knowledge_base.py
                                                        │
                                                        ▼
                                               DiagnosisResponse
                                         (enriched with clinical context)

The service layer calls :func:`get_disease_info` with the predicted disease
name and merges the result into the diagnosis response before returning it
to the client.

Design principles
-----------------
* **Keys match ML output exactly** — every key in :data:`DISEASE_KNOWLEDGE`
  is spelled identically to its corresponding label in ``disease_dataset.csv``
  and the ``LabelEncoder`` fitted during training.  A mismatch silently
  returns ``None`` from :func:`get_disease_info`, so key accuracy is critical.

* **Informational only** — medication entries describe drug *classes* and
  common examples as clinical reference information.  They are **not**
  prescriptions, dosage recommendations, or medical advice.  The disclaimer
  is embedded in every medication entry and in the module docstring.

* **Extensible to 254+ diseases** — the ``DiseaseInfo`` TypedDict defines the
  contract every entry must satisfy.  Adding a new disease requires only a
  new dictionary entry that conforms to this schema.

* **No external dependencies** — pure Python standard library.  Safe to import
  in any context without triggering database or network I/O.

⚠️  MEDICAL DISCLAIMER
    All information in this module is provided for **informational and
    educational purposes only**.  It does not constitute medical advice,
    diagnosis, or treatment.  Medication names listed here are examples of
    drug classes commonly associated with each condition and must **never**
    be interpreted as prescriptions.  Always consult a qualified healthcare
    professional for diagnosis and treatment decisions.

Usage
-----
::

    from app.ai.knowledge_base import get_disease_info, DISEASE_KNOWLEDGE

    info = get_disease_info("Diabetes")
    if info:
        print(info["specialist"])   # "Endocrinologist"
        print(info["emergency"])    # False
"""

from typing import TypedDict

# ---------------------------------------------------------------------------
# Type contract
# ---------------------------------------------------------------------------


class DiseaseInfo(TypedDict):
    """Schema that every entry in :data:`DISEASE_KNOWLEDGE` must conform to.

    Attributes:
        severity: Clinical urgency level.  One of:
            ``"low"``, ``"moderate"``, ``"high"``, or ``"critical"``.
        specialist: Primary medical specialist to consult for this condition.
        tests: Ordered list of recommended diagnostic investigations.
            Listed from first-line to confirmatory tests.
        medications: List of drug classes / common agents associated with
            treatment.  **Informational only — not prescriptions.**
        home_care: Practical self-care measures the patient can take at home
            while awaiting or alongside formal medical treatment.
        emergency: ``True`` if this condition may require emergency care or
            immediate hospital attendance.  ``False`` otherwise.
    """

    severity: str
    specialist: str
    tests: list[str]
    medications: list[str]
    home_care: list[str]
    emergency: bool


# ---------------------------------------------------------------------------
# Severity level reference
# ---------------------------------------------------------------------------
# low      — Self-limiting; resolves with rest and basic self-care.
# moderate — Requires medical evaluation; may need prescription treatment.
# high     — Significant morbidity risk; prompt specialist consultation needed.
# critical — Life-threatening; immediate emergency care required.

# ---------------------------------------------------------------------------
# Main knowledge dictionary
# ---------------------------------------------------------------------------
# Keys must match disease labels in disease_dataset.csv and LabelEncoder EXACTLY.
# Diseases are grouped by clinical category for readability.
# Each group is separated by a blank comment line.
# To add a new disease: add a new key that matches the ML label, following
# the DiseaseInfo schema.  Run the training pipeline to register the new label.

DISEASE_KNOWLEDGE: dict[str, DiseaseInfo] = {

    # =========================================================================
    # RESPIRATORY DISEASES
    # =========================================================================

    "Common Cold": {
        "severity": "low",
        "specialist": "General Practitioner",
        "tests": [
            "Clinical examination (diagnosis is usually clinical)",
            "Throat swab — if bacterial infection suspected",
            "Complete Blood Count (CBC) — if symptoms persist beyond 10 days",
        ],
        "medications": [
            # Informational only — not a prescription.
            "Decongestants (e.g. pseudoephedrine, oxymetazoline nasal spray) — for congestion relief",
            "Antihistamines (e.g. loratadine, cetirizine) — for runny nose and sneezing",
            "Analgesics / antipyretics (e.g. paracetamol, ibuprofen) — for fever and sore throat",
            "Cough suppressants (e.g. dextromethorphan) — for dry cough",
            "NOTE: Antibiotics are NOT effective against viral common colds",
        ],
        "home_care": [
            "Rest and increase fluid intake (water, warm broths, herbal teas)",
            "Inhale steam or use a humidifier to ease congestion",
            "Gargle warm salt water for sore throat relief",
            "Honey and lemon in warm water for cough and throat comfort",
            "Avoid smoking and secondhand smoke during recovery",
            "Wash hands frequently to prevent spreading to others",
        ],
        "emergency": False,
    },

    "Influenza": {
        "severity": "moderate",
        "specialist": "General Practitioner / Infectious Disease Specialist",
        "tests": [
            "Rapid Influenza Diagnostic Test (RIDT) — nasal or throat swab",
            "PCR (RT-PCR) — gold standard for influenza type and subtype",
            "Complete Blood Count (CBC) — to assess severity and rule out bacterial co-infection",
            "Chest X-ray — if pneumonia is suspected",
        ],
        "medications": [
            # Informational only — not a prescription.
            "Antivirals (e.g. oseltamivir / Tamiflu, zanamivir) — most effective if started within 48 h of symptom onset",
            "Analgesics / antipyretics (e.g. paracetamol, ibuprofen) — for fever and body aches",
            "NOTE: Aspirin should be avoided in children due to Reye syndrome risk",
        ],
        "home_care": [
            "Strict bed rest — the body needs energy to fight the virus",
            "Stay well hydrated; fever dramatically increases fluid loss",
            "Isolate from others for at least 24 hours after fever resolves",
            "Use cool compresses and light clothing to manage high fever",
            "Annual influenza vaccination for prevention",
        ],
        "emergency": False,
    },

    "Pneumonia": {
        "severity": "high",
        "specialist": "Pulmonologist / Infectious Disease Specialist",
        "tests": [
            "Chest X-ray — primary diagnostic tool; shows pulmonary infiltrates",
            "CT scan of chest — for complex or non-resolving cases",
            "Complete Blood Count (CBC) with differential",
            "Sputum culture and sensitivity — to identify causative organism",
            "Blood cultures — if bacteraemia is suspected",
            "Pulse oximetry / Arterial Blood Gas (ABG) — to assess oxygenation",
            "Urine antigen tests — for Legionella and Streptococcus pneumoniae",
        ],
        "medications": [
            # Informational only — not a prescription.
            "Antibiotics (e.g. amoxicillin, azithromycin, doxycycline) — for bacterial pneumonia; choice depends on organism and severity",
            "Antivirals (e.g. oseltamivir) — if viral (influenza-associated) pneumonia",
            "Antipyretics (e.g. paracetamol) — for fever management",
            "Bronchodilators — if bronchospasm is present",
            "Oxygen therapy — for hypoxaemia (SpO₂ < 94 %)",
        ],
        "home_care": [
            "Complete the full prescribed antibiotic course without skipping doses",
            "Rest completely — avoid physical exertion during recovery",
            "Drink at least 8 glasses of water daily to loosen secretions",
            "Sleep on your side or sit upright to ease breathing",
            "Avoid cold air, smoke, and dust",
            "Seek emergency care immediately if breathlessness worsens",
        ],
        "emergency": True,
    },

    "Asthma": {
        "severity": "moderate",
        "specialist": "Pulmonologist / Allergist",
        "tests": [
            "Spirometry — measures FEV1/FVC ratio (key diagnostic test)",
            "Peak Expiratory Flow (PEF) monitoring — for ongoing control assessment",
            "Bronchodilator reversibility test — confirms airway reversibility",
            "Allergy skin-prick testing or specific IgE (RAST) — to identify triggers",
            "Chest X-ray — to exclude other causes of breathlessness",
            "Exhaled Nitric Oxide (FeNO) — marker of eosinophilic airway inflammation",
        ],
        "medications": [
            # Informational only — not a prescription.
            "Short-acting beta-2 agonists / SABA (e.g. salbutamol / albuterol inhaler) — rapid relief of acute symptoms",
            "Inhaled corticosteroids / ICS (e.g. beclomethasone, fluticasone) — first-line preventive therapy",
            "Long-acting beta-2 agonists / LABA (e.g. salmeterol, formoterol) — combined with ICS for moderate-severe asthma",
            "Leukotriene receptor antagonists (e.g. montelukast) — add-on therapy",
            "Biological agents (e.g. omalizumab, mepolizumab) — for severe refractory asthma",
        ],
        "home_care": [
            "Identify and avoid personal triggers (dust mites, pollen, pets, cold air, smoke)",
            "Keep a symptom and peak flow diary to track control",
            "Always carry a reliever inhaler (SABA)",
            "Use correct inhaler technique — ask a nurse or pharmacist to verify",
            "Maintain a clean, dust-free home environment; use allergen-proof bedding covers",
            "Get annual influenza vaccination",
        ],
        "emergency": True,
    },

    "Tuberculosis": {
        "severity": "high",
        "specialist": "Pulmonologist / Infectious Disease Specialist",
        "tests": [
            "Sputum smear microscopy (AFB stain) — initial screening test",
            "Sputum culture (Lowenstein-Jensen or MGIT liquid culture) — gold standard",
            "GeneXpert MTB/RIF PCR — rapid diagnosis and rifampicin resistance detection",
            "Chest X-ray — classically shows upper-lobe infiltrates and cavitation",
            "Tuberculin Skin Test (TST / Mantoux) — for latent TB screening",
            "Interferon-Gamma Release Assay (IGRA / QuantiFERON-TB Gold) — latent TB",
            "HIV test — TB and HIV co-infection is common",
        ],
        "medications": [
            # Informational only — not a prescription.
            "Standard first-line HRZE regimen: Isoniazid (H) + Rifampicin (R) + Pyrazinamide (Z) + Ethambutol (E) for 2 months, then HR for 4 months",
            "Pyridoxine (Vitamin B6) — co-prescribed with isoniazid to prevent peripheral neuropathy",
            "Drug-resistant TB requires second-line agents (e.g. bedaquiline, linezolid) — specialist management only",
            "NOTE: Full treatment adherence is critical; incomplete courses cause drug resistance",
        ],
        "home_care": [
            "Adhere strictly to the full treatment course (typically 6 months) — NEVER stop early",
            "Cover mouth and nose when coughing or sneezing; dispose of tissues safely",
            "Ensure good ventilation in living spaces — open windows when possible",
            "Eat a nutritious, high-calorie diet to support recovery from weight loss",
            "Report all household contacts to the public health authority for screening",
            "Avoid alcohol — it increases the risk of isoniazid-induced liver toxicity",
        ],
        "emergency": False,
    },

    # =========================================================================
    # CARDIOVASCULAR & CEREBROVASCULAR DISEASES
    # =========================================================================

    "Heart Disease": {
        "severity": "critical",
        "specialist": "Cardiologist",
        "tests": [
            "12-lead Electrocardiogram (ECG / EKG) — first-line; identifies arrhythmias and ischaemia",
            "Cardiac biomarkers: Troponin I / T (high-sensitivity) — rules in/out myocardial infarction",
            "Echocardiogram — assesses cardiac structure and function",
            "Coronary Angiography (Cardiac Catheterisation) — gold standard for CAD",
            "Stress Test (Exercise Tolerance Test or Nuclear Stress Test)",
            "CT Coronary Angiography (CTCA) — non-invasive assessment of coronary arteries",
            "Lipid Panel, Blood Glucose, HbA1c — cardiovascular risk factor assessment",
        ],
        "medications": [
            # Informational only — not a prescription.
            "Antiplatelets (e.g. aspirin, clopidogrel) — reduce thrombotic events",
            "Statins (e.g. atorvastatin, rosuvastatin) — lower LDL cholesterol",
            "Beta-blockers (e.g. metoprolol, carvedilol) — reduce heart rate and myocardial oxygen demand",
            "ACE inhibitors / ARBs (e.g. ramipril, losartan) — improve cardiac remodelling post-MI",
            "Nitrates (e.g. glyceryl trinitrate / GTN) — relieve anginal chest pain",
            "Anticoagulants (e.g. heparin, warfarin, apixaban) — for atrial fibrillation or thrombus",
        ],
        "home_care": [
            "Call emergency services (ambulance) immediately for sudden severe chest pain",
            "Chew a 300 mg aspirin tablet immediately if a heart attack is suspected (unless allergic)",
            "Adopt a heart-healthy diet: low saturated fat, low sodium, high fibre",
            "Engage in regular moderate aerobic exercise as advised by the cardiologist",
            "Stop smoking — smoking doubles the risk of heart attack",
            "Control blood pressure, cholesterol, and blood sugar diligently",
            "Attend all cardiac rehabilitation sessions after a cardiac event",
        ],
        "emergency": True,
    },

    "Hypertension": {
        "severity": "moderate",
        "specialist": "Cardiologist / General Practitioner",
        "tests": [
            "Blood pressure measurement (both arms, multiple readings on separate days)",
            "Ambulatory Blood Pressure Monitoring (ABPM) — 24-hour profile",
            "Urine dipstick and albumin-to-creatinine ratio — renal damage assessment",
            "Blood tests: Renal function (eGFR, creatinine), electrolytes, fasting glucose, lipid panel",
            "ECG — left ventricular hypertrophy screening",
            "Echocardiogram — if cardiac involvement is suspected",
            "Fundoscopy — hypertensive retinopathy grading",
        ],
        "medications": [
            # Informational only — not a prescription.
            "ACE inhibitors (e.g. ramipril, lisinopril) — first-line, especially with diabetes or CKD",
            "ARBs (e.g. losartan, valsartan) — alternative if ACE inhibitor not tolerated",
            "Calcium channel blockers (e.g. amlodipine) — effective across all ethnic groups",
            "Thiazide-like diuretics (e.g. indapamide, chlorthalidone) — often used in combination",
            "Beta-blockers (e.g. bisoprolol, atenolol) — preferred if heart failure or angina co-exists",
        ],
        "home_care": [
            "Monitor blood pressure at home twice daily and keep a log",
            "Reduce dietary sodium to less than 2 g per day (avoid processed foods)",
            "Follow the DASH diet — rich in fruits, vegetables, and low-fat dairy",
            "Maintain a healthy BMI through regular physical activity (30 min/day, 5 days/week)",
            "Limit alcohol to no more than 1–2 units per day",
            "Manage stress through relaxation techniques, mindfulness, or yoga",
            "Never stop antihypertensive medication without medical advice",
        ],
        "emergency": False,
    },

    "Stroke": {
        "severity": "critical",
        "specialist": "Neurologist / Stroke Specialist",
        "tests": [
            "Non-contrast CT scan of brain — immediate; distinguishes haemorrhagic from ischaemic stroke",
            "MRI brain with DWI (Diffusion-Weighted Imaging) — most sensitive for acute ischaemic stroke",
            "CT Angiography (CTA) or MR Angiography (MRA) — assess cerebral vasculature",
            "12-lead ECG — detect atrial fibrillation as a cardioembolic source",
            "Carotid Doppler Ultrasound — assess carotid stenosis",
            "Echocardiogram — detect cardiac thrombus or structural abnormality",
            "Blood tests: FBC, coagulation screen, glucose, lipids, ESR/CRP",
        ],
        "medications": [
            # Informational only — not a prescription.
            "IV Alteplase (tPA) thrombolysis — for ischaemic stroke within 4.5 hours of onset (contraindicated in haemorrhagic stroke)",
            "Mechanical thrombectomy — endovascular treatment for large vessel occlusion",
            "Antiplatelets (e.g. aspirin + clopidogrel dual therapy) — secondary prevention of ischaemic stroke",
            "Anticoagulants (e.g. apixaban, warfarin) — for AF-related cardioembolic stroke",
            "Statins (e.g. atorvastatin) — secondary prevention",
            "Antihypertensives — blood pressure control is critical post-stroke",
        ],
        "home_care": [
            "CALL EMERGENCY SERVICES IMMEDIATELY — stroke is a time-critical emergency",
            "Use the FAST acronym: Face drooping, Arm weakness, Speech difficulty, Time to call 999/911",
            "Do NOT give food or water — aspiration risk is high",
            "During recovery: attend all physiotherapy, speech therapy, and occupational therapy sessions",
            "Modify the home to prevent falls (grab rails, non-slip mats)",
            "Adhere strictly to all secondary prevention medications",
            "Address all modifiable risk factors: hypertension, AF, smoking, diabetes",
        ],
        "emergency": True,
    },

    # =========================================================================
    # INFECTIOUS DISEASES
    # =========================================================================

    "Malaria": {
        "severity": "high",
        "specialist": "Infectious Disease Specialist / Tropical Medicine",
        "tests": [
            "Thick and thin blood film microscopy — gold standard; identifies species and parasite density",
            "Rapid Diagnostic Test (RDT) — HRP2/pLDH antigen detection; point-of-care",
            "PCR — most sensitive; used for species confirmation and resistance screening",
            "Complete Blood Count (CBC) — anaemia, thrombocytopenia, leukopenia",
            "Blood glucose — hypoglycaemia is common, especially in severe malaria",
            "Renal and liver function tests — assess end-organ involvement",
        ],
        "medications": [
            # Informational only — not a prescription.
            "Artemisinin-based Combination Therapies (ACTs) — e.g. artemether-lumefantrine (Coartem) for uncomplicated P. falciparum",
            "IV Artesunate — first-line for severe / complicated malaria (preferred over quinine)",
            "Chloroquine — for chloroquine-sensitive P. vivax and P. malariae",
            "Primaquine — for radical cure of P. vivax and P. ovale hypnozoites (check G6PD status first)",
            "Chemoprophylaxis (e.g. atovaquone-proguanil, doxycycline, mefloquine) — for travellers to endemic areas",
        ],
        "home_care": [
            "Use insecticide-treated bed nets (ITNs) every night",
            "Apply DEET-based insect repellent on exposed skin at dusk and dawn",
            "Wear long-sleeved clothing and long trousers in the evenings",
            "Eliminate stagnant water around the home (mosquito breeding sites)",
            "Complete the full antimalarial treatment course even if symptoms resolve early",
            "Seek immediate medical care if high fever develops within 3 months of travel to endemic area",
        ],
        "emergency": True,
    },

    "Typhoid Fever": {
        "severity": "high",
        "specialist": "Infectious Disease Specialist / General Physician",
        "tests": [
            "Blood culture — gold standard, especially in the first 2 weeks",
            "Bone marrow culture — highest sensitivity (80–95 %) throughout illness",
            "Widal test — agglutination test; limited specificity, widely used in endemic settings",
            "Typhidot / Tubex TF — rapid serological tests",
            "Stool and urine culture — useful after the first week",
            "Complete Blood Count — relative leucopenia is characteristic",
            "Liver function tests — hepatomegaly and mild transaminitis are common",
        ],
        "medications": [
            # Informational only — not a prescription.
            "Fluoroquinolones (e.g. ciprofloxacin, ofloxacin) — first-line in fluoroquinolone-sensitive strains",
            "Third-generation cephalosporins (e.g. ceftriaxone, cefixime) — for multidrug-resistant strains",
            "Azithromycin — effective oral alternative, especially for uncomplicated typhoid",
            "Antipyretics (e.g. paracetamol) — fever management; avoid NSAIDs due to GI bleeding risk",
            "NOTE: Resistance to ampicillin, chloramphenicol, and co-trimoxazole is now common",
        ],
        "home_care": [
            "Drink only boiled or bottled water; avoid ice from unknown sources",
            "Eat only thoroughly cooked, freshly prepared food",
            "Maintain strict hand hygiene — wash with soap after using the toilet and before eating",
            "Rest and maintain adequate nutrition; eat small, frequent, easily digestible meals",
            "Typhoid vaccination (Vi polysaccharide or Ty21a oral) before travel to endemic areas",
            "Monitor for serious complications: intestinal perforation (sudden severe abdominal pain), haemorrhage",
        ],
        "emergency": False,
    },

    "Meningitis": {
        "severity": "critical",
        "specialist": "Neurologist / Infectious Disease Specialist / Emergency Medicine",
        "tests": [
            "Lumbar puncture (CSF analysis) — definitive; sent for cell count, protein, glucose, Gram stain, culture",
            "Blood cultures — taken BEFORE antibiotics if feasible",
            "CT head — before LP if focal neurology, papilloedema, or altered consciousness",
            "Complete Blood Count (CBC), CRP, procalcitonin — systemic inflammation markers",
            "PCR on CSF and blood — for meningococcal, pneumococcal, viral, and TB meningitis",
            "Serum glucose — compare with CSF glucose (normal CSF:serum ratio > 0.6)",
        ],
        "medications": [
            # Informational only — not a prescription.
            "IV Ceftriaxone (or Cefotaxime) — empirical first-line for bacterial meningitis",
            "IV Dexamethasone — given before or with first antibiotic dose; reduces inflammation and hearing loss risk",
            "IV Aciclovir — if viral (HSV) encephalitis / meningitis is suspected",
            "IV Vancomycin — added if penicillin-resistant pneumococcus is suspected",
            "Anti-TB regimen — for tuberculous meningitis (prolonged 9–12 month course)",
        ],
        "home_care": [
            "CALL EMERGENCY SERVICES IMMEDIATELY — bacterial meningitis is life-threatening",
            "Do NOT wait for a rash to appear; meningitis can kill without a rash",
            "Vaccination: MenACWY and MenB vaccines are highly preventive",
            "Post-recovery: attend follow-up for hearing assessment and cognitive evaluation",
            "Notify close contacts — chemoprophylaxis (rifampicin or ciprofloxacin) may be required",
        ],
        "emergency": True,
    },

    "Hepatitis": {
        "severity": "high",
        "specialist": "Hepatologist / Gastroenterologist",
        "tests": [
            "Liver function tests (LFTs): ALT, AST, ALP, bilirubin, albumin, PT",
            "Hepatitis serology panel: HBsAg, Anti-HBc, Anti-HBs, Anti-HCV, Anti-HAV IgM",
            "HCV RNA PCR and HBV DNA PCR — quantify viral load",
            "Ultrasound abdomen — assess liver size, echogenicity, and portal hypertension",
            "Liver biopsy or FibroScan (transient elastography) — assess fibrosis grade",
            "Alpha-fetoprotein (AFP) — screen for hepatocellular carcinoma in chronic hepatitis",
        ],
        "medications": [
            # Informational only — not a prescription.
            "Hepatitis B: Tenofovir disoproxil fumarate (TDF) or Entecavir — long-term suppression of HBV replication",
            "Hepatitis C: Direct-acting antivirals (DAAs) e.g. sofosbuvir/velpatasvir — 8–12 week cure rates > 95 %",
            "Hepatitis A: Supportive care only; no specific antiviral available",
            "Corticosteroids (e.g. prednisolone) — for autoimmune hepatitis",
            "Ursodeoxycholic acid — for primary biliary cholangitis",
        ],
        "home_care": [
            "Avoid all alcohol — it accelerates liver damage significantly",
            "Do not take over-the-counter paracetamol / acetaminophen without medical advice",
            "Eat a balanced diet; avoid raw shellfish (HAV/HEV risk)",
            "Practice strict hand hygiene; use barrier contraception",
            "Vaccination for Hepatitis A and B is available — highly effective prevention",
            "Attend regular follow-up for viral load monitoring and cancer surveillance",
        ],
        "emergency": False,
    },

    "Chickenpox": {
        "severity": "low",
        "specialist": "General Practitioner / Paediatrician",
        "tests": [
            "Clinical diagnosis (characteristic vesicular rash in crops — diagnosis is usually clinical)",
            "Varicella-zoster virus (VZV) PCR from vesicle swab — for atypical presentations",
            "VZV IgM serology — for primary infection confirmation",
            "Full Blood Count — if severe or immunocompromised patient",
        ],
        "medications": [
            # Informational only — not a prescription.
            "Oral Aciclovir (acyclovir) — antiviral treatment for immunocompromised patients or adults with severe disease; most effective if started within 24 h of rash",
            "Calamine lotion — topically for itch relief",
            "Oral antihistamines (e.g. chlorphenamine) — reduce itch",
            "Paracetamol — for fever; AVOID aspirin in children (Reye syndrome risk)",
            "Varicella-zoster immunoglobulin (VZIG) — post-exposure prophylaxis for high-risk contacts",
        ],
        "home_care": [
            "Keep nails short and clean to prevent skin infection from scratching",
            "Apply cool wet compresses to the rash for relief",
            "Wear loose, soft cotton clothing",
            "Isolate from school / work until all blisters have crusted (typically day 5–6)",
            "Avoid contact with pregnant women, newborns, and immunocompromised individuals",
            "Varicella vaccine provides > 90 % protection — recommended for non-immune adults",
        ],
        "emergency": False,
    },

    "Shingles": {
        "severity": "moderate",
        "specialist": "General Practitioner / Dermatologist / Neurologist",
        "tests": [
            "Clinical diagnosis — dermatomal distribution of painful vesicular rash is characteristic",
            "VZV PCR from vesicle swab — confirms diagnosis in atypical cases",
            "Tzanck smear — bedside test showing multinucleated giant cells",
            "Ophthalmology referral — if ophthalmic zoster (V1 dermatome) is suspected",
        ],
        "medications": [
            # Informational only — not a prescription.
            "Oral Aciclovir, Valaciclovir, or Famciclovir — antivirals; start within 72 h of rash onset to reduce severity and duration",
            "Analgesics: paracetamol, NSAIDs, or opioids for moderate-severe pain",
            "Tricyclic antidepressants (e.g. amitriptyline) or gabapentinoids (e.g. pregabalin) — for post-herpetic neuralgia (PHN)",
            "Topical lidocaine patches or capsaicin cream — for PHN",
            "Corticosteroids — sometimes added in severe cases (controversial)",
        ],
        "home_care": [
            "Keep the rash clean and dry; use cool, damp cloths for relief",
            "Do not burst the blisters — increases infection risk",
            "Cover the rash to prevent spreading VZV to susceptible individuals",
            "Rest and manage stress — immune suppression reactivates the virus",
            "Recombinant zoster vaccine (Shingrix) — 2-dose course is > 90 % effective in prevention",
        ],
        "emergency": False,
    },

    "Strep Throat": {
        "severity": "low",
        "specialist": "General Practitioner / Ear, Nose & Throat (ENT) Surgeon",
        "tests": [
            "Rapid Strep Antigen Test (RSAT) — point-of-care throat swab; result in 5–10 minutes",
            "Throat culture — gold standard; takes 24–48 hours",
            "Centor Score / McIsaac Score — clinical decision tool to estimate strep probability",
            "ASO titre (Antistreptolysin O) — if rheumatic fever is suspected",
            "Full Blood Count — moderate leucocytosis with neutrophilia in bacterial infection",
        ],
        "medications": [
            # Informational only — not a prescription.
            "Phenoxymethylpenicillin (Penicillin V) oral — first-line treatment for 10 days",
            "Amoxicillin — common alternative; avoid if EBV infection suspected (causes rash)",
            "Erythromycin or Azithromycin — for penicillin-allergic patients",
            "Paracetamol or Ibuprofen — for pain and fever relief",
            "NOTE: Complete the full antibiotic course to prevent rheumatic fever and glomerulonephritis",
        ],
        "home_care": [
            "Gargle warm salt water several times daily",
            "Stay well hydrated; cold fluids and ice chips can soothe the throat",
            "Rest voice and avoid irritants (smoke, dry air)",
            "Use throat lozenges or sprays for temporary pain relief",
            "Remain off school / work for 24 hours after starting antibiotics",
        ],
        "emergency": False,
    },

    "Tonsillitis": {
        "severity": "low",
        "specialist": "General Practitioner / Ear, Nose & Throat (ENT) Surgeon",
        "tests": [
            "Clinical examination — enlarged, inflamed tonsils with or without exudate",
            "Throat swab for culture and sensitivity",
            "Monospot test (Paul-Bunnell) — exclude infectious mononucleosis (EBV)",
            "FBC — leucocytosis in bacterial; atypical lymphocytes in EBV",
        ],
        "medications": [
            # Informational only — not a prescription.
            "Penicillin V or Amoxicillin — for Group A Streptococcal (GAS) tonsillitis",
            "Analgesics (paracetamol, ibuprofen) — pain and fever",
            "Corticosteroids (e.g. single dose dexamethasone) — to reduce tonsillar swelling and pain rapidly",
            "IV antibiotics — for peritonsillar abscess (quinsy) requiring hospitalisation",
            "Tonsillectomy — considered for recurrent episodes (typically ≥ 7 per year or ≥ 5/year for 2 years)",
        ],
        "home_care": [
            "Drink cold fluids and eat soft foods — ice cream and yoghurt are soothing",
            "Rest the voice; avoid shouting or excessive talking",
            "Use a humidifier to keep the throat moist",
            "Seek urgent care if drooling, stridor, or difficulty swallowing develops (quinsy)",
        ],
        "emergency": False,
    },

    "Ear Infection": {
        "severity": "low",
        "specialist": "General Practitioner / Ear, Nose & Throat (ENT) Surgeon",
        "tests": [
            "Otoscopy — visualise the eardrum (tympanic membrane); key diagnostic step",
            "Tympanometry — assess middle ear pressure and eardrum mobility",
            "Ear swab culture — for chronic or recurrent otitis media with discharge",
            "Audiogram — if hearing loss is suspected",
            "CT scan of temporal bones — for complicated otitis media (mastoiditis, cholesteatoma)",
        ],
        "medications": [
            # Informational only — not a prescription.
            "Amoxicillin — first-line antibiotic for acute otitis media (AOM) in children",
            "Amoxicillin-clavulanate — for treatment failures or high-risk patients",
            "Topical antibiotic drops (e.g. ciprofloxacin + dexamethasone) — for otitis externa",
            "Analgesics (paracetamol, ibuprofen) — pain management",
            "Decongestants — may help eustachian tube dysfunction but evidence is limited",
            "Tympanostomy (grommet) insertion — for recurrent or persistent glue ear",
        ],
        "home_care": [
            "Apply warm (not hot) compress against the ear for comfort",
            "Elevate the head during sleep to encourage fluid drainage",
            "Keep the ear canal dry — avoid swimming until fully recovered",
            "Do not insert cotton buds or fingers into the ear",
            "Breastfeeding infants and avoiding passive smoke exposure reduces risk in children",
        ],
        "emergency": False,
    },

    "Allergic Reaction": {
        "severity": "high",
        "specialist": "Allergist / Immunologist / Emergency Medicine",
        "tests": [
            "Skin prick testing (SPT) — identifies specific allergens",
            "Specific IgE blood tests (RAST / ImmunoCAP) — quantify allergen sensitisation",
            "Serum tryptase — elevated after anaphylaxis; confirms mast cell activation",
            "Oral food challenge — gold standard for food allergy diagnosis",
            "Patch testing — for contact (delayed-type) allergic reactions",
        ],
        "medications": [
            # Informational only — not a prescription.
            "IM Adrenaline / Epinephrine (e.g. EpiPen) — FIRST-LINE treatment for anaphylaxis; administer immediately",
            "IV / oral antihistamines (e.g. chlorphenamine, cetirizine) — for mild to moderate reactions",
            "Corticosteroids (e.g. hydrocortisone IV, prednisolone oral) — reduce biphasic reaction risk",
            "Inhaled bronchodilators (e.g. salbutamol) — for bronchospasm associated with anaphylaxis",
            "Allergen immunotherapy (desensitisation) — for insect venom and inhalant allergies",
        ],
        "home_care": [
            "Always carry two adrenaline auto-injectors (EpiPen) if prescribed",
            "Wear a medical alert bracelet identifying the allergy",
            "Read food labels meticulously; inform restaurant staff of severe food allergies",
            "Avoid known triggers — maintain an allergy action plan in writing",
            "Seek emergency care immediately for throat swelling, difficulty breathing, or collapse",
        ],
        "emergency": True,
    },

    # =========================================================================
    # ENDOCRINE & METABOLIC DISEASES
    # =========================================================================

    "Diabetes": {
        "severity": "moderate",
        "specialist": "Endocrinologist / Diabetologist",
        "tests": [
            "Fasting Plasma Glucose (FPG) — ≥ 7.0 mmol/L (126 mg/dL) is diagnostic",
            "HbA1c (Glycated Haemoglobin) — ≥ 48 mmol/mol (≥ 6.5 %) is diagnostic; reflects 3-month average",
            "Oral Glucose Tolerance Test (OGTT) — 2-hour plasma glucose ≥ 11.1 mmol/L",
            "Random Plasma Glucose ≥ 11.1 mmol/L with symptoms — diagnostic",
            "Urine Albumin:Creatinine Ratio (ACR) — annual diabetic nephropathy screening",
            "Lipid panel, renal and liver function — cardiovascular risk and complication screening",
            "Annual dilated fundus examination — diabetic retinopathy screening",
            "Peripheral neuropathy assessment (10 g monofilament, vibration sense)",
        ],
        "medications": [
            # Informational only — not a prescription.
            "Type 1 DM: Insulin (basal-bolus regimen with long-acting e.g. insulin glargine + rapid-acting e.g. insulin aspart)",
            "Type 2 DM first-line: Metformin (biguanide) — reduces hepatic glucose production",
            "SGLT2 inhibitors (e.g. empagliflozin, dapagliflozin) — cardiovascular and renal protective benefits",
            "GLP-1 receptor agonists (e.g. semaglutide, liraglutide) — weight loss and glucose lowering",
            "DPP-4 inhibitors (e.g. sitagliptin, saxagliptin) — safe add-on with low hypoglycaemia risk",
            "Sulfonylureas (e.g. gliclazide, glibenclamide) — older but effective; hypoglycaemia risk",
        ],
        "home_care": [
            "Monitor blood glucose daily as directed (fasting and 2-hour post-meal)",
            "Follow a low-glycaemic-index, low-refined-sugar diet",
            "Exercise regularly — aerobic and resistance training both improve insulin sensitivity",
            "Inspect feet daily for cuts, blisters, or ulcers that may go unnoticed due to neuropathy",
            "Maintain HbA1c within the personalised target set by the clinician",
            "Do not skip medications or insulin doses",
            "Attend annual eye, kidney, foot, and cardiovascular risk reviews",
        ],
        "emergency": False,
    },

    "Hypothyroidism": {
        "severity": "moderate",
        "specialist": "Endocrinologist",
        "tests": [
            "Thyroid Stimulating Hormone (TSH) — elevated in primary hypothyroidism; most sensitive screening test",
            "Free T4 (FT4) — low in overt hypothyroidism",
            "Anti-TPO antibodies (Anti-Thyroid Peroxidase) — confirms Hashimoto's thyroiditis",
            "Anti-Thyroglobulin antibodies — additional autoimmune marker",
            "Complete Blood Count — normocytic or macrocytic anaemia may be present",
            "Lipid panel — hypothyroidism raises LDL cholesterol",
            "Thyroid ultrasound — if goitre or nodule is palpated",
        ],
        "medications": [
            # Informational only — not a prescription.
            "Levothyroxine (synthetic T4) — first-line, lifelong replacement therapy",
            "Liothyronine (T3) — occasionally added to levothyroxine in T4-to-T3 conversion issues",
            "NOTE: Take levothyroxine on an empty stomach 30–60 minutes before food or other medications",
            "NOTE: Calcium, iron, and antacids impair levothyroxine absorption",
        ],
        "home_care": [
            "Take levothyroxine at the same time every day — consistency is essential",
            "Attend TSH monitoring 6–8 weeks after any dose change, then annually when stable",
            "Eat a balanced diet; iodine-rich foods (fish, dairy) support thyroid health",
            "Avoid excessive soy or cruciferous vegetables as they may interfere with thyroxine absorption",
            "Regular gentle exercise helps combat fatigue and weight gain",
        ],
        "emergency": False,
    },

    "Hyperthyroidism": {
        "severity": "moderate",
        "specialist": "Endocrinologist",
        "tests": [
            "TSH — suppressed (very low or undetectable) in hyperthyroidism",
            "Free T3 (FT3) and Free T4 (FT4) — elevated",
            "TSH receptor antibodies (TRAb / TSHR-Ab) — positive in Graves' disease",
            "Anti-TPO antibodies — elevated in Graves' and Hashimoto's thyrotoxicosis",
            "Thyroid uptake scan (radioiodine uptake) — differentiates Graves' from toxic nodule / thyroiditis",
            "Thyroid ultrasound with Doppler — vascularity pattern aids diagnosis",
            "ECG — atrial fibrillation is a common complication",
        ],
        "medications": [
            # Informational only — not a prescription.
            "Thionamides (e.g. carbimazole, propylthiouracil) — block thyroid hormone synthesis; first-line medical treatment",
            "Beta-blockers (e.g. propranolol, atenolol) — rapid symptomatic control (palpitations, tremor, anxiety)",
            "Radioiodine (I-131) — definitive treatment for Graves' disease; induces hypothyroidism (then replaced with levothyroxine)",
            "Thyroidectomy — surgical option for large goitre, compressive symptoms, or failed medical therapy",
        ],
        "home_care": [
            "Avoid iodine-rich foods (seaweed, kelp supplements, iodinated contrast) and iodine-containing medications",
            "Protect eyes from sunlight (UV sunglasses) if Graves' ophthalmopathy is present",
            "Rest adequately — metabolism is running at abnormally high rate",
            "Attend regular blood tests as thyroid function can change rapidly",
            "Use eye drops and eye protection for Graves' eye disease",
        ],
        "emergency": False,
    },

    "Adrenal Insufficiency": {
        "severity": "high",
        "specialist": "Endocrinologist",
        "tests": [
            "Short Synacthen Test (SST) / ACTH stimulation test — gold standard for primary and secondary insufficiency",
            "Morning serum cortisol (08:00–09:00 h) — < 100 nmol/L is strongly suggestive",
            "Plasma ACTH — elevated in primary (Addison's), low/normal in secondary",
            "Electrolytes: hyponatraemia, hyperkalaemia in Addison's disease",
            "Glucose — hypoglycaemia in adrenal crisis",
            "Anti-adrenal antibodies (21-hydroxylase Ab) — autoimmune Addison's confirmation",
            "Adrenal CT / MRI — assess adrenal size and morphology",
        ],
        "medications": [
            # Informational only — not a prescription.
            "Hydrocortisone (glucocorticoid replacement) — three-times-daily dosing to mimic cortisol diurnal rhythm",
            "Fludrocortisone (mineralocorticoid replacement) — for primary adrenal insufficiency",
            "DHEA — considered in women with secondary adrenal insufficiency and reduced wellbeing",
            "Emergency hydrocortisone injection kit — all patients should carry; administer during sick days or vomiting",
        ],
        "home_care": [
            "Wear a medical alert bracelet or carry a steroid emergency card at all times",
            "Never stop steroid medication abruptly — life-threatening adrenal crisis can result",
            "Double or triple steroid dose during illness, fever, surgery, or significant physical stress (sick-day rules)",
            "Administer emergency hydrocortisone injection if unable to take oral medication",
            "Increase sodium intake in hot weather or with vigorous exercise",
            "Attend regular endocrine follow-up for dose optimisation",
        ],
        "emergency": True,
    },

    # =========================================================================
    # GASTROINTESTINAL DISEASES
    # =========================================================================

    "Gastroenteritis": {
        "severity": "low",
        "specialist": "General Practitioner / Gastroenterologist",
        "tests": [
            "Clinical diagnosis in most cases — history and examination are usually sufficient",
            "Stool microscopy, culture, and sensitivity — if symptoms persist > 3 days or blood in stool",
            "Stool PCR panel (GI pathogen panel) — rapid multiplex detection of bacterial, viral, and parasitic causes",
            "Electrolytes and renal function — assess dehydration severity",
            "Full Blood Count — leucocytosis suggests bacterial aetiology",
        ],
        "medications": [
            # Informational only — not a prescription.
            "Oral Rehydration Solution (ORS) — cornerstone of treatment; replaces fluid and electrolytes",
            "Antiemetics (e.g. ondansetron, metoclopramide) — for persistent vomiting",
            "Antibiotics (e.g. ciprofloxacin, azithromycin) — ONLY if bacterial cause confirmed (Campylobacter, Shigella, Salmonella non-typhi) or travellers' diarrhoea",
            "Antidiarrhoeals (e.g. loperamide) — symptomatic relief in adults; AVOID in children or bloody diarrhoea",
            "Zinc supplements — recommended for children in low-income settings",
        ],
        "home_care": [
            "Drink ORS or diluted clear fluids frequently in small sips to prevent dehydration",
            "Resume eating as soon as tolerated — avoid the 'nothing by mouth' approach",
            "Eat bland, easily digestible foods (banana, rice, apple sauce, toast — BRAT diet)",
            "Strict hand hygiene especially after using the toilet and before food preparation",
            "Seek medical care if unable to keep fluids down, blood in stool, signs of severe dehydration, or symptoms lasting > 7 days",
        ],
        "emergency": False,
    },

    "Acid Reflux": {
        "severity": "low",
        "specialist": "Gastroenterologist",
        "tests": [
            "Clinical diagnosis for typical symptoms (heartburn, regurgitation)",
            "Upper GI Endoscopy (OGD) — if alarm symptoms (dysphagia, weight loss, bleeding, anaemia) or failure to respond to PPIs",
            "24-hour ambulatory pH monitoring / pH-impedance study — gold standard for GORD diagnosis and quantification",
            "Oesophageal manometry — assesses lower oesophageal sphincter pressure",
            "H. pylori testing (breath test or stool antigen) — treat if positive",
        ],
        "medications": [
            # Informational only — not a prescription.
            "Proton Pump Inhibitors / PPIs (e.g. omeprazole, lansoprazole, esomeprazole) — most effective acid suppressants; taken 30–60 min before meals",
            "H2 receptor antagonists (e.g. famotidine, ranitidine) — less potent than PPIs; useful for night-time symptoms",
            "Antacids (e.g. Gaviscon, Rennies) — rapid but short-lived symptomatic relief",
            "Prokinetics (e.g. domperidone) — if gastroparesis or delayed gastric emptying is a contributing factor",
        ],
        "home_care": [
            "Elevate the head of the bed by 15–20 cm (use bed blocks or a wedge pillow)",
            "Eat smaller, more frequent meals; avoid eating within 3 hours of bedtime",
            "Identify and avoid trigger foods: fatty foods, chocolate, caffeine, alcohol, tomatoes, citrus, spicy food",
            "Maintain a healthy weight — excess abdominal fat increases intra-abdominal pressure",
            "Stop smoking — nicotine relaxes the lower oesophageal sphincter",
            "Wear loose-fitting clothing around the waist",
        ],
        "emergency": False,
    },

    "Peptic Ulcer": {
        "severity": "moderate",
        "specialist": "Gastroenterologist",
        "tests": [
            "Upper GI Endoscopy (OGD) — diagnostic gold standard; allows biopsy and H. pylori testing",
            "H. pylori testing: urea breath test (UBT), stool antigen test, or CLO test at endoscopy",
            "Barium meal / upper GI series — less common; used if endoscopy unavailable",
            "Full Blood Count — anaemia suggests chronic blood loss",
            "Stool occult blood (FOB) — screens for GI bleeding",
            "Fasting gastrin level — if Zollinger-Ellison syndrome (gastrinoma) is suspected",
        ],
        "medications": [
            # Informational only — not a prescription.
            "H. pylori eradication (triple therapy): PPI + Clarithromycin + Amoxicillin for 7–14 days",
            "Proton Pump Inhibitors (PPIs) — continue for 4–8 weeks after eradication to allow ulcer healing",
            "H2 blockers (e.g. famotidine) — alternative if PPI intolerant",
            "Bismuth subsalicylate — mucosal protectant; used in quadruple therapy for antibiotic-resistant strains",
            "NSAIDs should be stopped or replaced with paracetamol — NSAIDs cause and worsen peptic ulcers",
        ],
        "home_care": [
            "Stop NSAIDs and aspirin — discuss alternatives with the doctor",
            "Avoid smoking and alcohol — both impair ulcer healing significantly",
            "Eat regular meals; an empty stomach worsens symptoms",
            "Avoid foods that increase acid: caffeine, spicy food, carbonated drinks",
            "Seek emergency care for black tarry stools, vomiting blood, or sudden severe abdominal pain (perforation)",
        ],
        "emergency": False,
    },

    "Appendicitis": {
        "severity": "critical",
        "specialist": "General Surgeon / Emergency Medicine",
        "tests": [
            "Clinical examination — Rovsing's sign, McBurney's point tenderness, rebound tenderness",
            "Alvarado Score / MANTRELS score — clinical decision scoring tool",
            "Ultrasound abdomen — first-line imaging, especially in children and pregnant women",
            "CT abdomen and pelvis with contrast — highest sensitivity (95–98 %) for appendicitis",
            "MRI abdomen — preferred in pregnant patients to avoid radiation",
            "Full Blood Count — neutrophilic leucocytosis; CRP elevated",
        ],
        "medications": [
            # Informational only — not a prescription.
            "IV antibiotics (e.g. co-amoxiclav, metronidazole + cefuroxime) — given pre-operatively and post-operatively",
            "IV analgesics (e.g. morphine, paracetamol) — pain relief does NOT mask signs; give early",
            "IV fluids — resuscitation and nil-by-mouth preparation for surgery",
            "Non-operative antibiotics-only management — considered in uncomplicated cases (evidence supports but risk of recurrence)",
        ],
        "home_care": [
            "SEEK EMERGENCY CARE IMMEDIATELY — appendicitis is a surgical emergency",
            "Do NOT take laxatives or apply heat to the abdomen",
            "Do NOT eat or drink anything if appendicitis is suspected (nil by mouth for surgery)",
            "Post-operatively: follow wound care instructions; report fever, wound redness, or severe pain",
            "Return to normal activity gradually over 4–6 weeks after open appendicectomy",
        ],
        "emergency": True,
    },

    "Irritable Bowel Syndrome": {
        "severity": "low",
        "specialist": "Gastroenterologist",
        "tests": [
            "Rome IV diagnostic criteria — IBS is a clinical diagnosis based on symptom pattern",
            "FBC, CRP, ESR, coeliac serology — to exclude organic disease",
            "Stool calprotectin — distinguishes IBS (low) from IBD (high)",
            "Colonoscopy — if alarm features or onset > 50 years",
            "Hydrogen breath tests — for small intestinal bacterial overgrowth (SIBO) and lactose intolerance",
            "Thyroid function tests — hypothyroidism can mimic IBS-C symptoms",
        ],
        "medications": [
            # Informational only — not a prescription.
            "Antispasmodics (e.g. mebeverine, hyoscine butylbromide) — for abdominal cramping",
            "Loperamide — for IBS-D (diarrhoea-predominant) subtype",
            "Laxatives (e.g. macrogol) — for IBS-C (constipation-predominant) subtype",
            "Low-dose tricyclic antidepressants (e.g. amitriptyline) — for pain modulation in IBS-D",
            "SSRIs (e.g. fluoxetine) — may help IBS-C with comorbid anxiety or depression",
            "Linaclotide — licensed for moderate-severe IBS-C",
        ],
        "home_care": [
            "Follow the Low-FODMAP diet (under dietitian guidance) — highly evidence-based for IBS",
            "Eat regular meals at consistent times; avoid skipping meals",
            "Increase soluble fibre (oats, psyllium); reduce insoluble fibre initially",
            "Stay well hydrated — especially important for IBS-C",
            "Identify and manage psychological triggers — CBT and gut-directed hypnotherapy are effective",
            "Probiotics (e.g. Lactobacillus, Bifidobacterium) — may help; trial for 4 weeks",
        ],
        "emergency": False,
    },

    "Crohn Disease": {
        "severity": "high",
        "specialist": "Gastroenterologist",
        "tests": [
            "Colonoscopy with ileoscopy and biopsies — gold standard; shows skip lesions, cobblestone mucosa",
            "MRI enterography (MRE) — assesses small bowel extent and perianal disease; no radiation",
            "CT abdomen and pelvis — for complications (stricture, abscess, fistula)",
            "Faecal calprotectin — non-invasive marker of intestinal inflammation",
            "FBC, CRP, ESR, albumin, B12, folate, iron studies — disease activity and nutritional status",
            "Stool culture and C. difficile — exclude infection before commencing immunosuppression",
        ],
        "medications": [
            # Informational only — not a prescription.
            "5-aminosalicylates (e.g. mesalazine) — limited role in Crohn's; more effective in ulcerative colitis",
            "Corticosteroids (e.g. prednisolone, budesonide) — for induction of remission",
            "Immunomodulators (e.g. azathioprine, mercaptopurine, methotrexate) — maintenance of remission",
            "Biologics — anti-TNF (e.g. infliximab, adalimumab), anti-integrins (vedolizumab), anti-IL-12/23 (ustekinumab)",
            "Antibiotics (e.g. metronidazole, ciprofloxacin) — for perianal disease and bacterial overgrowth",
        ],
        "home_care": [
            "Follow dietary advice from a specialist dietitian — nutritional deficiencies are common",
            "Keep a food and symptom diary to identify personal dietary triggers",
            "Stop smoking — smoking significantly worsens Crohn's disease course and response to treatment",
            "Attend regular endoscopic surveillance and blood monitoring as directed",
            "Get vaccinations — biological therapy increases infection risk; ensure vaccines are up to date",
            "Join patient support groups (e.g. Crohn's & Colitis charity) for peer support",
        ],
        "emergency": False,
    },

    # =========================================================================
    # MUSCULOSKELETAL DISEASES
    # =========================================================================

    "Rheumatoid Arthritis": {
        "severity": "moderate",
        "specialist": "Rheumatologist",
        "tests": [
            "Rheumatoid Factor (RF) — positive in 70–80 % of cases",
            "Anti-CCP antibodies (ACPA) — highly specific (> 95 %) for RA; positive years before symptoms",
            "FBC, ESR, CRP — inflammation markers; FBC shows normocytic anaemia",
            "X-rays of hands and feet — erosive changes in established disease",
            "MRI / Ultrasound joints — detects early synovitis and erosions before X-ray changes",
            "Renal and liver function — baseline before starting disease-modifying therapy",
            "Hepatitis B/C serology — before biological therapy",
        ],
        "medications": [
            # Informational only — not a prescription.
            "DMARDs (Disease-Modifying Anti-Rheumatic Drugs): Methotrexate — anchor drug; slows radiological progression",
            "Hydroxychloroquine and Sulfasalazine — often combined with methotrexate (triple therapy)",
            "Biologic DMARDs: anti-TNF (e.g. etanercept, adalimumab), anti-IL-6 (tocilizumab), anti-CD20 (rituximab)",
            "JAK inhibitors (e.g. baricitinib, tofacitinib) — oral targeted synthetic DMARDs",
            "NSAIDs (e.g. naproxen, diclofenac) — symptomatic relief; not disease-modifying",
            "Corticosteroids (e.g. prednisolone) — short-term bridge therapy during flares",
        ],
        "home_care": [
            "Balance rest (during flares) and gentle exercise (during remission) — hydrotherapy is particularly beneficial",
            "Apply heat for stiffness; cold packs for swollen, inflamed joints",
            "Use assistive devices (jar openers, raised toilet seats) to protect joints",
            "Attend occupational therapy for adaptive strategies and splinting",
            "Maintain a healthy weight — reduces mechanical stress on weight-bearing joints",
            "Quit smoking — smoking is an independent risk factor for RA and worsens severity",
        ],
        "emergency": False,
    },

    "Sciatica": {
        "severity": "moderate",
        "specialist": "Orthopaedic Surgeon / Neurosurgeon / Pain Medicine Specialist",
        "tests": [
            "Clinical examination — Straight Leg Raise (SLR / Lasègue) test, dermatomal sensory mapping",
            "MRI lumbar spine — gold standard for visualising disc herniation, nerve root compression, and spinal stenosis",
            "CT myelography — if MRI is contraindicated",
            "X-ray lumbar spine — limited; shows bony alignment and degenerative changes but not disc/nerve",
            "Nerve Conduction Studies (NCS) and Electromyography (EMG) — differentiate radiculopathy from peripheral neuropathy",
        ],
        "medications": [
            # Informational only — not a prescription.
            "NSAIDs (e.g. naproxen, diclofenac, ibuprofen) — first-line; reduce inflammation around nerve root",
            "Analgesics (paracetamol) — adjunctive pain relief",
            "Muscle relaxants (e.g. diazepam, cyclobenzaprine) — for associated muscle spasm",
            "Neuropathic agents (e.g. pregabalin, gabapentin, amitriptyline) — for burning, shooting, or electric shock pain",
            "Epidural corticosteroid injection — for severe or persistent radiculopathy; provides medium-term relief",
            "Surgical decompression (microdiscectomy) — if conservative treatment fails or neurological deficit progresses",
        ],
        "home_care": [
            "Remain active — bed rest for more than 48 hours worsens outcomes",
            "Apply ice (first 48–72 h) then heat alternately for pain relief",
            "Sleep on a firm mattress with a pillow between knees (side-lying) to reduce lumbar pressure",
            "Attend physiotherapy — core strengthening, stretching, and postural correction are evidence-based",
            "Avoid prolonged sitting — stand and walk for 5 minutes every 30 minutes",
            "Maintain a healthy weight to reduce mechanical load on the lumbar spine",
        ],
        "emergency": False,
    },

    # =========================================================================
    # NEUROLOGICAL & MENTAL HEALTH DISEASES
    # =========================================================================

    "Migraine": {
        "severity": "moderate",
        "specialist": "Neurologist",
        "tests": [
            "Clinical diagnosis based on ICHD-3 criteria — no specific diagnostic test exists",
            "MRI brain with contrast — if atypical features, neurological signs, or change in headache pattern",
            "CT brain — if sudden-onset thunderclap headache (exclude subarachnoid haemorrhage first)",
            "Headache diary — essential for diagnosis, trigger identification, and treatment monitoring",
        ],
        "medications": [
            # Informational only — not a prescription.
            "Acute / abortive: Triptans (e.g. sumatriptan, rizatriptan) — 5-HT1B/D agonists; most effective migraine-specific treatment",
            "Acute: NSAIDs (e.g. ibuprofen, naproxen) and paracetamol — for mild-moderate attacks",
            "Acute: Antiemetics (e.g. metoclopramide, prochlorperazine) — treat nausea and potentiate analgesics",
            "Acute: CGRP antagonists (gepants e.g. rimegepant, ubrogepant) — newer class; no vasoconstriction",
            "Prophylaxis (if ≥ 4 attacks/month): Propranolol, amitriptyline, topiramate, valproate, candesartan",
            "Prophylaxis: Anti-CGRP monoclonal antibodies (e.g. erenumab, fremanezumab) — monthly injections for refractory migraine",
        ],
        "home_care": [
            "Keep a detailed headache diary — identify and avoid personal triggers (stress, sleep disruption, dehydration, hormonal changes)",
            "Maintain regular sleep, meal, and exercise schedules — irregular patterns are major triggers",
            "Rest in a dark, quiet room at the onset of an attack",
            "Apply cold packs to the forehead or back of the neck",
            "Stay well hydrated — dehydration is a common trigger",
            "Practice relaxation techniques and stress management (mindfulness, biofeedback)",
        ],
        "emergency": False,
    },

    "Depression": {
        "severity": "moderate",
        "specialist": "Psychiatrist / Psychologist / General Practitioner",
        "tests": [
            "PHQ-9 (Patient Health Questionnaire-9) — validated screening and severity tool",
            "Thyroid function tests (TSH, FT4) — exclude hypothyroidism",
            "Full Blood Count — exclude anaemia",
            "Vitamin B12 and folate — deficiencies can cause depressive symptoms",
            "Vitamin D level — low levels associated with depression",
            "Liver and renal function — baseline before antidepressants",
            "Urine drug screen — exclude substance-induced mood disorder",
        ],
        "medications": [
            # Informational only — not a prescription.
            "SSRIs (e.g. fluoxetine, sertraline, escitalopram) — first-line antidepressants; generally well tolerated",
            "SNRIs (e.g. venlafaxine, duloxetine) — particularly useful when pain or anxiety co-exists",
            "Tricyclic antidepressants (e.g. amitriptyline) — effective but more side effects; used in refractory cases",
            "Mirtazapine — useful when poor appetite or insomnia is prominent",
            "Lithium or antipsychotics (augmentation) — for treatment-resistant depression",
            "NOTE: Antidepressants typically take 2–4 weeks to show effect; do not discontinue abruptly",
        ],
        "home_care": [
            "Engage in regular aerobic exercise — as effective as medication for mild-moderate depression",
            "Maintain social connections — isolation worsens depression; reach out to trusted friends or family",
            "Establish a consistent daily routine including regular sleep and meal times",
            "Access talking therapies — CBT and interpersonal therapy (IPT) are highly evidence-based",
            "Limit alcohol — it is a central nervous system depressant",
            "Contact a mental health crisis line if suicidal thoughts occur",
        ],
        "emergency": False,
    },

    "Anxiety Disorder": {
        "severity": "moderate",
        "specialist": "Psychiatrist / Psychologist / General Practitioner",
        "tests": [
            "GAD-7 (Generalised Anxiety Disorder 7-item scale) — validated severity screening tool",
            "Thyroid function tests — hyperthyroidism causes anxiety symptoms",
            "Cardiac assessment (ECG, 24-hour Holter) — if palpitations are prominent",
            "Phaeochromocytoma screen (24-hour urinary catecholamines) — if episodic hypertension, sweating, and headache",
            "Urine drug screen and alcohol history — exclude substance-related anxiety",
            "Blood glucose — hypoglycaemia mimics panic attacks",
        ],
        "medications": [
            # Informational only — not a prescription.
            "SSRIs (e.g. sertraline, escitalopram) — first-line for GAD, panic disorder, and social anxiety",
            "SNRIs (e.g. venlafaxine, duloxetine) — effective alternative; venlafaxine licensed for GAD",
            "Buspirone — non-sedating anxiolytic; takes 2–4 weeks to work; no dependence risk",
            "Benzodiazepines (e.g. diazepam, lorazepam) — SHORT-TERM only for severe acute anxiety; significant dependence risk",
            "Beta-blockers (e.g. propranolol) — for situational (performance) anxiety and physical symptoms",
            "Pregabalin — licensed for GAD; also addresses neuropathic pain",
        ],
        "home_care": [
            "Learn and practice diaphragmatic breathing and progressive muscle relaxation daily",
            "Engage in regular aerobic exercise (30 min, 5 times weekly) — proven to reduce anxiety",
            "Limit caffeine, alcohol, and recreational drugs — all worsen anxiety",
            "Practice mindfulness meditation — 10 minutes daily reduces ruminative thinking",
            "CBT (Cognitive Behavioural Therapy) — gold standard psychological treatment",
            "Gradually face feared situations (exposure) rather than avoidance — avoidance maintains anxiety",
        ],
        "emergency": False,
    },

    "Parkinson Disease": {
        "severity": "high",
        "specialist": "Neurologist (Movement Disorder Specialist)",
        "tests": [
            "Clinical diagnosis by a movement disorder specialist — based on UK Parkinson's Disease Society Brain Bank criteria",
            "DaTSCAN (dopamine transporter SPECT imaging) — differentiates PD from essential tremor",
            "MRI brain — to exclude structural causes (normal in PD)",
            "Response to levodopa trial — diagnostic and prognostic",
            "Neuropsychological assessment — baseline cognitive evaluation",
        ],
        "medications": [
            # Informational only — not a prescription.
            "Levodopa + Carbidopa (e.g. Sinemet, Madopar) — most effective symptomatic treatment; gold standard",
            "Dopamine agonists (e.g. pramipexole, ropinirole, rotigotine patch) — used early to delay levodopa initiation",
            "MAO-B inhibitors (e.g. selegiline, rasagiline) — mild symptomatic benefit; possible neuroprotective effect",
            "COMT inhibitors (e.g. entacapone) — extend levodopa effect; reduce 'wearing off'",
            "Amantadine — for dyskinesia management in advanced PD",
            "Deep Brain Stimulation (DBS) — surgical option for motor complications in suitable candidates",
        ],
        "home_care": [
            "Engage in regular physiotherapy — improves gait, balance, and reduces fall risk",
            "Speech and language therapy — for dysarthria and dysphagia",
            "Occupational therapy — adaptive tools for daily tasks and home safety assessment",
            "Tai Chi, dance, and cycling are particularly beneficial for motor symptoms",
            "Maintain a high-fibre diet and adequate hydration to manage constipation",
            "Take medication at precise times — even small delays can cause significant motor deterioration",
        ],
        "emergency": False,
    },

    "Alzheimer Disease": {
        "severity": "high",
        "specialist": "Neurologist / Geriatrician / Psychiatrist (Old Age)",
        "tests": [
            "Cognitive assessment: MMSE, MoCA (Montreal Cognitive Assessment) — screening tools",
            "MRI brain — hippocampal atrophy is characteristic; exclude other causes",
            "CT brain — exclude structural causes (subdural haematoma, NPH, tumour)",
            "PET amyloid scan — detects amyloid plaques; confirms diagnosis",
            "CSF biomarkers (amyloid-β 42, total tau, phospho-tau) — via lumbar puncture",
            "Blood tests: TFTs, B12, folate, calcium, glucose, HIV, syphilis — exclude reversible causes",
            "Neuropsychological testing — detailed cognitive profile",
        ],
        "medications": [
            # Informational only — not a prescription.
            "Cholinesterase inhibitors (e.g. donepezil, rivastigmine, galantamine) — mild to moderate AD; modest cognitive benefit",
            "Memantine (NMDA receptor antagonist) — moderate to severe AD; may be combined with cholinesterase inhibitors",
            "Anti-amyloid monoclonal antibodies (e.g. lecanemab, donanemab) — emerging therapies for early AD; specialist-only",
            "Antipsychotics (e.g. quetiapine) — used cautiously for severe behavioural symptoms; increased mortality risk",
            "Antidepressants (e.g. sertraline) — for co-morbid depression in AD",
        ],
        "home_care": [
            "Maintain a structured, predictable daily routine to reduce confusion",
            "Label rooms, drawers, and objects clearly; use clocks, calendars, and reminder apps",
            "Ensure home safety: stove safety devices, door alarms, remove fall hazards",
            "Keep the patient physically and mentally active — walking, puzzles, music, social interaction",
            "Carer education and support is essential — consider carer respite services",
            "Register with the local dementia support services and obtain a lasting power of attorney early",
        ],
        "emergency": False,
    },

    # =========================================================================
    # SKIN DISEASES
    # =========================================================================

    "Eczema": {
        "severity": "low",
        "specialist": "Dermatologist / Allergist",
        "tests": [
            "Clinical diagnosis based on morphology and distribution of rash",
            "Skin-prick testing or specific IgE — if food allergy or aeroallergen is suspected trigger",
            "Patch testing — for contact (Type IV) allergic dermatitis",
            "Skin swab culture — if secondary bacterial infection (Staphylococcus aureus) is suspected",
            "IgE serum level — often markedly elevated in atopic eczema",
        ],
        "medications": [
            # Informational only — not a prescription.
            "Emollients (moisturisers) — CORNERSTONE of treatment; apply immediately after bathing and at least twice daily",
            "Topical corticosteroids (e.g. hydrocortisone 1 % for face, betamethasone for body) — anti-inflammatory; use appropriate potency for site",
            "Topical calcineurin inhibitors (e.g. tacrolimus, pimecrolimus) — steroid-sparing; safe for face and flexures",
            "Dupilumab (biologic, anti-IL-4/13) — for moderate-severe atopic eczema not controlled with topicals",
            "Oral antihistamines (e.g. chlorphenamine, hydroxyzine) — for sleep disturbance due to itch",
            "Oral antibiotics (e.g. flucloxacillin) — for secondary bacterial infection",
        ],
        "home_care": [
            "Apply emollient generously and frequently — this is the single most important self-care measure",
            "Bath or shower in lukewarm water for no more than 10–15 minutes; apply emollient within 3 minutes of drying",
            "Avoid soap — use soap-free emollient wash or aqueous cream as a substitute",
            "Wear loose, soft cotton clothing; avoid wool and synthetic fibres",
            "Identify and avoid environmental triggers: dust mites, pet dander, fragranced products, smoke",
            "Keep nails short and smooth to minimise skin damage from scratching",
        ],
        "emergency": False,
    },

    "Psoriasis": {
        "severity": "moderate",
        "specialist": "Dermatologist / Rheumatologist (if psoriatic arthritis present)",
        "tests": [
            "Clinical diagnosis — characteristic silvery-scaled erythematous plaques",
            "Skin biopsy — for atypical presentations; shows parakeratosis and Munro's microabscesses",
            "PASI score (Psoriasis Area and Severity Index) — assesses severity for treatment decisions",
            "Joint X-rays / MRI — if psoriatic arthritis is suspected",
            "Liver function tests, FBC, renal function — baseline before systemic therapy",
            "Hepatitis B/C serology — before biological therapy",
        ],
        "medications": [
            # Informational only — not a prescription.
            "Topical: Vitamin D analogues (e.g. calcipotriol) and topical corticosteroids — first-line for mild-moderate plaque psoriasis",
            "Topical: Coal tar preparations — anti-inflammatory and antiproliferative",
            "Phototherapy: Narrowband UVB (NB-UVB) or PUVA — for widespread disease",
            "Systemic: Methotrexate — weekly oral dosing; monitor LFTs and FBC",
            "Systemic: Ciclosporin — rapid onset; for severe flares; monitor renal function and BP",
            "Biological: Anti-TNF (e.g. adalimumab, etanercept), Anti-IL-17 (e.g. secukinumab, ixekizumab), Anti-IL-23 (e.g. guselkumab) — for moderate-severe psoriasis",
        ],
        "home_care": [
            "Moisturise daily with thick emollients to reduce scaling and itch",
            "Avoid triggers: stress, infections (streptococcal throat), alcohol, smoking, skin trauma (Koebner phenomenon)",
            "Sunlight exposure (in moderation) can improve psoriasis — apply SPF 30+ to uninvolved skin",
            "Limit alcohol — alcohol worsens psoriasis and reduces treatment response",
            "Join Psoriasis Association for support, education, and peer community",
        ],
        "emergency": False,
    },

    # =========================================================================
    # UROLOGICAL DISEASES
    # =========================================================================

    "Urinary Tract Infection": {
        "severity": "low",
        "specialist": "General Practitioner / Urologist / Nephrologist (if recurrent)",
        "tests": [
            "Urine dipstick — screens for nitrites and leucocyte esterase; rapid and cheap",
            "Midstream Urine (MSU) culture and sensitivity — gold standard; identifies organism and antibiotic sensitivities",
            "FBC and CRP — if upper UTI (pyelonephritis) or systemic illness is suspected",
            "Renal ultrasound — for recurrent UTIs to exclude structural abnormalities",
            "CT urogram — if urinary tract stones or obstructive uropathy is suspected",
            "Cystoscopy — for haematuria, recurrent infections, or suspected interstitial cystitis",
        ],
        "medications": [
            # Informational only — not a prescription.
            "Trimethoprim or Nitrofurantoin — first-line for uncomplicated lower UTI (3–7 day course)",
            "Pivmecillinam — alternative first-line option in many guidelines",
            "Co-amoxiclav or Cefalexin — second-line or in pregnancy",
            "IV Ceftriaxone or Gentamicin — for severe pyelonephritis or sepsis requiring hospitalisation",
            "Phenazopyridine — urinary analgesic for symptom relief; NOT an antibiotic",
            "Vaginal oestrogen cream — reduces recurrent UTIs in post-menopausal women",
        ],
        "home_care": [
            "Drink at least 2–3 litres of fluid daily to flush bacteria from the urinary tract",
            "Urinate promptly when the urge arises — do not delay",
            "Wipe front to back after using the toilet",
            "Urinate after sexual intercourse",
            "Avoid using perfumed soaps, bubble baths, or talcum powder around the genital area",
            "Cranberry products — modest evidence for prevention; generally safe to use",
        ],
        "emergency": False,
    },

    "Enlarged Prostate": {
        "severity": "moderate",
        "specialist": "Urologist",
        "tests": [
            "International Prostate Symptom Score (IPSS) questionnaire — standardises symptom severity",
            "Digital Rectal Examination (DRE) — assesses prostate size and consistency",
            "Prostate-Specific Antigen (PSA) blood test — elevated in BPH and prostate cancer",
            "Urine dipstick and MSU culture — exclude UTI",
            "Urinary flow rate (uroflowmetry) and post-void residual ultrasound",
            "Renal function tests — assess upper tract complications",
            "Flexible cystoscopy — if haematuria or bladder outflow obstruction requires direct visualisation",
        ],
        "medications": [
            # Informational only — not a prescription.
            "Alpha-blockers (e.g. tamsulosin, alfuzosin) — relax prostatic smooth muscle; rapid onset of action",
            "5-alpha reductase inhibitors (e.g. finasteride, dutasteride) — reduce prostate size over 3–6 months; best for large prostates",
            "Combination: alpha-blocker + 5-ARI — for moderate-severe symptoms with large prostate",
            "PDE5 inhibitors (e.g. tadalafil 5 mg daily) — licensed for BPH; particularly if erectile dysfunction co-exists",
            "Anticholinergics / beta-3 agonists (mirabegron) — if overactive bladder symptoms predominate",
        ],
        "home_care": [
            "Reduce fluid intake in the evenings to minimise nocturia",
            "Avoid alcohol and caffeine — both worsen BPH symptoms",
            "Double voiding — after urinating, wait a few minutes and try again",
            "Avoid decongestants and antihistamines — they worsen bladder outflow obstruction",
            "Maintain a healthy weight and exercise regularly",
            "Seek emergency care for acute urinary retention (inability to pass urine and bladder pain)",
        ],
        "emergency": False,
    },

    "Vaginal Infection": {
        "severity": "low",
        "specialist": "Gynaecologist / General Practitioner",
        "tests": [
            "Vaginal pH measurement — bacterial vaginosis (pH > 4.5); candidiasis (pH < 4.5)",
            "High Vaginal Swab (HVS) — microscopy (clue cells, hyphae), culture and sensitivity",
            "Whiff test — positive (fishy odour with 10 % KOH) suggests bacterial vaginosis",
            "STI screen (NAAT): Chlamydia trachomatis, Neisseria gonorrhoeae, Trichomonas vaginalis, HSV",
            "Vulvovaginal examination",
        ],
        "medications": [
            # Informational only — not a prescription.
            "Bacterial vaginosis: Metronidazole (oral or vaginal gel) or Clindamycin vaginal cream",
            "Vulvovaginal candidiasis: Topical azoles (e.g. clotrimazole pessary) or single-dose oral fluconazole",
            "Trichomonas vaginalis: Metronidazole or Tinidazole — treat both partners simultaneously",
            "Gonorrhoea: IM Ceftriaxone — antibiotic resistance requires culture-guided treatment",
            "Chlamydia: Azithromycin (single dose) or Doxycycline (7 days)",
        ],
        "home_care": [
            "Wear loose, breathable cotton underwear",
            "Avoid feminine hygiene sprays, scented soaps, and vaginal douching — they disrupt the natural flora",
            "Wipe front to back after using the toilet",
            "Shower (not bath) and change out of wet swimwear or exercise clothing promptly",
            "Complete the full treatment course even if symptoms improve",
            "Inform sexual partners and practice safe sex with condoms",
        ],
        "emergency": False,
    },

    # =========================================================================
    # ONCOLOGY
    # =========================================================================

    "Breast Cancer": {
        "severity": "high",
        "specialist": "Oncologist / Breast Surgeon",
        "tests": [
            "Mammography — first-line breast imaging; screening and diagnostic",
            "Breast Ultrasound — adjunct to mammography; preferred in younger women and dense breasts",
            "MRI breast — for high-risk screening, extent of disease, and implant assessment",
            "Core needle biopsy — tissue diagnosis; histology, grade, ER/PR/HER2 receptor status",
            "Sentinel lymph node biopsy — axillary staging",
            "CT chest/abdomen/pelvis, bone scan, or PET-CT — for staging in confirmed cancer",
            "BRCA1/BRCA2 genetic testing — for hereditary breast cancer risk",
        ],
        "medications": [
            # Informational only — not a prescription.
            "Hormone therapy (e.g. tamoxifen for pre-menopausal; aromatase inhibitors e.g. anastrozole for post-menopausal) — for ER+ tumours",
            "HER2-targeted therapy (e.g. trastuzumab / Herceptin, pertuzumab) — for HER2+ tumours",
            "Chemotherapy (e.g. anthracyclines e.g. doxorubicin, taxanes e.g. paclitaxel) — neoadjuvant or adjuvant",
            "CDK4/6 inhibitors (e.g. palbociclib, ribociclib) — for ER+/HER2- metastatic breast cancer",
            "PARP inhibitors (e.g. olaparib) — for BRCA-mutated HER2-negative breast cancer",
        ],
        "home_care": [
            "Attend all scheduled chemotherapy, radiotherapy, and hormone therapy appointments",
            "Report new symptoms promptly — bone pain, breathlessness, headaches — to the oncology team",
            "Maintain a balanced diet rich in fruits, vegetables, and lean protein",
            "Regular gentle exercise (walking, yoga) during and after treatment improves outcomes",
            "Engage with breast cancer support groups — peer support significantly improves psychological wellbeing",
            "Monthly self-breast examination after treatment — report any new lumps or changes immediately",
        ],
        "emergency": False,
    },

    "Colorectal Cancer": {
        "severity": "high",
        "specialist": "Colorectal Surgeon / Oncologist / Gastroenterologist",
        "tests": [
            "Colonoscopy — gold standard; direct visualisation and biopsy",
            "CT Colonography (virtual colonoscopy) — for patients unfit for colonoscopy",
            "Faecal Immunochemical Test (FIT) — population-based screening test",
            "CT chest/abdomen/pelvis — TNM staging for confirmed cancer",
            "MRI pelvis — essential for rectal cancer staging and surgical planning",
            "Carcinoembryonic Antigen (CEA) — tumour marker for monitoring and prognosis",
            "Microsatellite Instability (MSI) / MMR testing and KRAS/NRAS/BRAF mutation testing — guides systemic therapy",
        ],
        "medications": [
            # Informational only — not a prescription.
            "Adjuvant chemotherapy (e.g. FOLFOX — oxaliplatin + leucovorin + 5-FU) — for stage III colon cancer",
            "Targeted therapy: anti-VEGF (bevacizumab) and anti-EGFR (cetuximab, panitumumab) for RAS wild-type metastatic CRC",
            "Immunotherapy (e.g. pembrolizumab) — for MSI-High / dMMR colorectal cancer",
            "Neoadjuvant chemoradiotherapy — for locally advanced rectal cancer before surgery",
        ],
        "home_care": [
            "Attend all post-operative surveillance colonoscopies and CT scans",
            "Eat a high-fibre diet rich in fruits, vegetables, and wholegrains; limit red and processed meat",
            "Maintain a healthy BMI — obesity is a risk factor for CRC recurrence",
            "Stoma care education — if a stoma was formed; specialist stoma nurses are invaluable",
            "Physical activity reduces CRC recurrence risk — aim for 150 min/week of moderate exercise",
        ],
        "emergency": False,
    },

    "Cervical Cancer": {
        "severity": "high",
        "specialist": "Gynaecological Oncologist / Radiation Oncologist",
        "tests": [
            "Colposcopy with biopsy — after abnormal cervical smear or HPV positive screening",
            "Cervical smear (Pap test) / HPV primary screening — national cervical screening programme",
            "MRI pelvis — tumour extent, parametrial invasion, and nodal involvement",
            "CT chest/abdomen/pelvis and PET-CT — lymph node and distant metastasis staging",
            "Examination Under Anaesthesia (EUA) — surgical staging of locally advanced disease",
            "Cystoscopy / sigmoidoscopy — bladder or rectal invasion assessment in advanced cases",
        ],
        "medications": [
            # Informational only — not a prescription.
            "Concurrent chemoradiotherapy: cisplatin-based chemotherapy with external beam radiotherapy (EBRT) and brachytherapy — for locally advanced cervical cancer",
            "Cisplatin, carboplatin, paclitaxel — for metastatic disease",
            "Bevacizumab (anti-VEGF) — added to chemotherapy for metastatic cervical cancer",
            "Pembrolizumab (anti-PD1) — for PD-L1 positive recurrent/metastatic disease",
        ],
        "home_care": [
            "Attend all cervical smear appointments — early detection saves lives",
            "HPV vaccination (Gardasil 9) prevents the high-risk HPV strains responsible for most cervical cancers",
            "Practice safe sex — use condoms; HPV is sexually transmitted",
            "Stop smoking — smoking significantly increases cervical cancer risk in HPV-positive women",
            "Attend all follow-up imaging and clinical appointments post-treatment",
        ],
        "emergency": False,
    },

    "Thyroid Cancer": {
        "severity": "moderate",
        "specialist": "Endocrinologist / Thyroid Surgeon / Nuclear Medicine",
        "tests": [
            "Thyroid Ultrasound — first-line; assesses nodule characteristics (TIRADS classification)",
            "Fine Needle Aspiration Cytology (FNAC) — definitive for tissue diagnosis (Bethesda classification)",
            "TSH, Free T4, calcitonin (if MTC suspected), thyroglobulin",
            "CT neck/chest — for pre-operative lymph node staging",
            "Radioiodine (I-131) whole-body scan — post-thyroidectomy for differentiated thyroid cancer",
            "BRAF, RET mutation testing — for targeted therapy decisions in papillary and MTC",
        ],
        "medications": [
            # Informational only — not a prescription.
            "Levothyroxine (TSH suppression therapy) — after total thyroidectomy for differentiated thyroid cancer",
            "Radioiodine (I-131) ablation — for remnant ablation and metastatic differentiated thyroid cancer",
            "Tyrosine kinase inhibitors (e.g. sorafenib, lenvatinib) — for radioiodine-refractory differentiated thyroid cancer",
            "Vandetanib or Cabozantinib — for medullary thyroid cancer (MTC)",
            "Selpercatinib — for RET-mutant thyroid cancer",
        ],
        "home_care": [
            "Take levothyroxine at the correct suppressive dose as prescribed — do not self-adjust",
            "Attend regular thyroglobulin monitoring and radioiodine scans",
            "Low-iodine diet for 2–3 weeks before radioiodine treatment — avoid seafood and dairy",
            "Radiation safety precautions for family members for 1–2 weeks after radioiodine treatment",
            "Report new neck lumps, hoarseness, or difficulty swallowing promptly",
        ],
        "emergency": False,
    },

    # =========================================================================
    # EYE DISEASES
    # =========================================================================

    "Glaucoma": {
        "severity": "high",
        "specialist": "Ophthalmologist",
        "tests": [
            "Tonometry (Goldman applanation tonometry) — measures intraocular pressure (IOP)",
            "Visual Field Test (Humphrey perimetry) — detects peripheral vision loss",
            "Optical Coherence Tomography (OCT) — assesses retinal nerve fibre layer thinning",
            "Fundoscopy (dilated fundus examination) — optic disc cup-to-disc ratio assessment",
            "Gonioscopy — classifies angle (open vs closed) and grading",
            "Corneal Pachymetry — central corneal thickness affects IOP measurement accuracy",
        ],
        "medications": [
            # Informational only — not a prescription.
            "Prostaglandin analogues (e.g. latanoprost, bimatoprost) — first-line; once-daily eye drops; most effective IOP lowering",
            "Beta-blocker eye drops (e.g. timolol) — reduce aqueous humour production; avoid in asthma and bradycardia",
            "Carbonic anhydrase inhibitors (e.g. dorzolamide, brinzolamide drops; acetazolamide oral) — reduce aqueous production",
            "Alpha-2 agonists (e.g. brimonidine) — reduce production and increase outflow",
            "Surgical / laser: Selective Laser Trabeculoplasty (SLT), trabeculectomy, or drainage implants — for inadequate IOP control",
        ],
        "home_care": [
            "Use eye drops exactly as prescribed — missing doses allows IOP to rise and damage the optic nerve",
            "Apply nasolacrimal occlusion (finger pressure on inner corner of eye) for 1–2 min after drops to reduce systemic absorption",
            "Attend regular ophthalmology appointments — glaucoma is a silent disease with no pain until vision loss is advanced",
            "Avoid activities that significantly raise IOP: heavy lifting and head-down yoga positions",
            "Protective eyewear if at risk of eye injury",
            "Inform first-degree relatives — glaucoma has a strong genetic component",
        ],
        "emergency": False,
    },

}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_disease_info(disease_name: str) -> DiseaseInfo | None:
    """Retrieve clinical information for a named disease.

    Performs a case-sensitive lookup against :data:`DISEASE_KNOWLEDGE` using
    the exact disease name string produced by the ML label encoder.

    Args:
        disease_name: The predicted disease label as returned by
            ``LabelEncoder.classes_[predicted_index]``.  Must match a key in
            :data:`DISEASE_KNOWLEDGE` exactly.

    Returns:
        A :class:`DiseaseInfo` dictionary containing severity, specialist,
        tests, medications, home care advice, and emergency flag.
        Returns ``None`` if the disease name is not found in the knowledge
        base — the service layer should handle this gracefully.

    Example:
        >>> info = get_disease_info("Diabetes")
        >>> info["severity"]
        'moderate'
        >>> info["emergency"]
        False
        >>> info["specialist"]
        'Endocrinologist / Diabetologist'
    """
    return DISEASE_KNOWLEDGE.get(disease_name)


def list_diseases() -> list[str]:
    """Return an alphabetically sorted list of all disease names in the knowledge base.

    Useful for administrative interfaces, validation, and API documentation.

    Returns:
        Sorted list of disease name strings.

    Example:
        >>> diseases = list_diseases()
        >>> "Diabetes" in diseases
        True
        >>> len(diseases) >= 25
        True
    """
    return sorted(DISEASE_KNOWLEDGE.keys())


def get_emergency_diseases() -> list[str]:
    """Return the names of all diseases flagged as potential emergencies.

    Intended for use in the diagnosis service to add an urgent care warning
    to API responses when the predicted disease is a known emergency.

    Returns:
        Sorted list of disease names where ``emergency`` is ``True``.

    Example:
        >>> emergencies = get_emergency_diseases()
        >>> "Heart Disease" in emergencies
        True
        >>> "Common Cold" in emergencies
        False
    """
    return sorted(
        disease for disease, info in DISEASE_KNOWLEDGE.items() if info["emergency"]
    )


def get_diseases_by_severity(severity: str) -> list[str]:
    """Return disease names filtered by severity level.

    Args:
        severity: One of ``"low"``, ``"moderate"``, ``"high"``, or ``"critical"``.

    Returns:
        Sorted list of disease names matching the requested severity level.
        Returns an empty list if no diseases match or the severity string is invalid.

    Example:
        >>> critical = get_diseases_by_severity("critical")
        >>> "Stroke" in critical
        True
        >>> "Eczema" in critical
        False
    """
    return sorted(
        disease
        for disease, info in DISEASE_KNOWLEDGE.items()
        if info["severity"] == severity
    )