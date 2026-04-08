"""
Medical Knowledge Base - ICD-10 Codes, Treatment Protocols & Clinical Guidelines
This serves as the reference data for the Medical Agent to validate against.
"""

from typing import Dict, Any, List, Optional


# ═══════════════════════════════════════════════════════════════════
#  ICD-10 CODE DATABASE
# ═══════════════════════════════════════════════════════════════════

ICD10_CODES = {
    "I25.1": {
        "code": "I25.1",
        "description": "Atherosclerotic heart disease of native coronary artery",
        "category": "Cardiovascular",
        "common_name": "Coronary Artery Disease (CAD)",
        "related_codes": ["I25.0", "I25.2", "I25.5", "I21.0"],
        "standard_treatments": ["CABG", "PCI/Angioplasty", "Medical Management"],
        "severity": "high",
    },
    "I10": {
        "code": "I10",
        "description": "Essential (primary) hypertension",
        "category": "Cardiovascular",
        "common_name": "Hypertension",
        "related_codes": ["I11.0", "I12.0", "I13.0"],
        "standard_treatments": ["Antihypertensive medications", "Lifestyle modification"],
        "severity": "moderate",
    },
    "E11": {
        "code": "E11",
        "description": "Type 2 diabetes mellitus",
        "category": "Endocrine",
        "common_name": "Diabetes Mellitus Type 2",
        "related_codes": ["E11.0", "E11.2", "E11.5", "E11.9"],
        "standard_treatments": ["Oral hypoglycemics", "Insulin therapy", "Lifestyle modification"],
        "severity": "moderate",
    },
    "N18": {
        "code": "N18",
        "description": "Chronic kidney disease",
        "category": "Genitourinary",
        "common_name": "Chronic Kidney Disease (CKD)",
        "related_codes": ["N18.1", "N18.2", "N18.3", "N18.4", "N18.5"],
        "standard_treatments": ["Dialysis", "Kidney transplant", "Medication management"],
        "severity": "high",
    },
    "I21": {
        "code": "I21",
        "description": "Acute myocardial infarction",
        "category": "Cardiovascular",
        "common_name": "Heart Attack",
        "related_codes": ["I21.0", "I21.1", "I21.2", "I21.3"],
        "standard_treatments": ["Primary PCI", "Thrombolysis", "CABG", "ICU care"],
        "severity": "critical",
    },
    "C50": {
        "code": "C50",
        "description": "Malignant neoplasm of breast",
        "category": "Oncology",
        "common_name": "Breast Cancer",
        "related_codes": ["C50.1", "C50.2", "C50.4", "C50.9"],
        "standard_treatments": ["Surgery", "Chemotherapy", "Radiation therapy", "Hormone therapy"],
        "severity": "critical",
    },
    "K80": {
        "code": "K80",
        "description": "Cholelithiasis",
        "category": "Digestive",
        "common_name": "Gallbladder Stones",
        "related_codes": ["K80.0", "K80.1", "K80.2"],
        "standard_treatments": ["Cholecystectomy", "ERCP", "Medical dissolution"],
        "severity": "moderate",
    },
    "M17": {
        "code": "M17",
        "description": "Osteoarthritis of knee",
        "category": "Musculoskeletal",
        "common_name": "Knee Osteoarthritis",
        "related_codes": ["M17.0", "M17.1", "M17.9"],
        "standard_treatments": ["Total knee replacement", "Arthroscopy", "Physiotherapy"],
        "severity": "moderate",
    },
}


# ═══════════════════════════════════════════════════════════════════
#  TREATMENT PROTOCOLS & CLINICAL GUIDELINES
# ═══════════════════════════════════════════════════════════════════

TREATMENT_PROTOCOLS = {
    "CABG": {
        "procedure_name": "Coronary Artery Bypass Graft Surgery",
        "procedure_code": "33533-33536",
        "indications": [
            "Triple vessel coronary artery disease",
            "Left main coronary artery disease (>50% stenosis)",
            "Two-vessel disease with proximal LAD involvement",
            "Failed PCI or recurrent restenosis",
            "Reduced ejection fraction (<40%) with significant CAD",
        ],
        "guidelines": [
            {"source": "ACC/AHA", "year": 2021, "recommendation": "Class I indication for left main disease and triple vessel disease"},
            {"source": "ESC/EACTS", "year": 2018, "recommendation": "Recommended for complex multivessel CAD with SYNTAX score >32"},
            {"source": "NHM India", "year": 2020, "recommendation": "Standard surgical treatment for multi-vessel CAD in Indian healthcare setting"},
        ],
        "medical_necessity_criteria": [
            "Documented significant coronary artery stenosis (>70%)",
            "Failed or unsuitable for medical management",
            "Not a candidate for less invasive procedures (PCI)",
            "Cardiac catheterization/angiography confirming disease",
        ],
        "average_cost_inr": {"range_min": 200000, "range_max": 500000},
        "recovery_days": "7-10 hospital days, 6-8 weeks full recovery",
    },
    "PCI": {
        "procedure_name": "Percutaneous Coronary Intervention (Angioplasty)",
        "procedure_code": "92920-92944",
        "indications": [
            "Single or dual vessel coronary artery disease",
            "Acute myocardial infarction (primary PCI)",
            "Unstable angina not responding to medications",
            "Restenosis after previous intervention",
        ],
        "guidelines": [
            {"source": "ACC/AHA", "year": 2021, "recommendation": "Class I for acute STEMI within 12 hours of symptom onset"},
            {"source": "ESC", "year": 2019, "recommendation": "Primary PCI is the preferred reperfusion strategy for STEMI"},
        ],
        "medical_necessity_criteria": [
            "Significant coronary stenosis (>70%) causing ischemia",
            "Symptoms not controlled by optimal medical therapy",
            "Favorable anatomy for percutaneous approach",
        ],
        "average_cost_inr": {"range_min": 100000, "range_max": 350000},
        "recovery_days": "1-2 hospital days, 1-2 weeks full recovery",
    },
    "Dialysis": {
        "procedure_name": "Hemodialysis / Peritoneal Dialysis",
        "procedure_code": "90935-90999",
        "indications": [
            "End-stage renal disease (CKD Stage 5, GFR <15)",
            "Acute kidney injury not responding to treatment",
            "Severe electrolyte/acid-base imbalance",
            "Uremic symptoms (encephalopathy, pericarditis)",
        ],
        "guidelines": [
            {"source": "KDIGO", "year": 2012, "recommendation": "Initiate dialysis when GFR < 10-15 ml/min with uremic symptoms"},
            {"source": "NKF-KDOQI", "year": 2015, "recommendation": "Patient education on dialysis modalities should begin at CKD Stage 4"},
        ],
        "medical_necessity_criteria": [
            "Documented CKD Stage 5 or acute kidney failure",
            "Laboratory evidence (eGFR, creatinine, BUN)",
            "Failed conservative management",
        ],
        "average_cost_inr": {"range_min": 2000, "range_max": 5000},  # per session
        "recovery_days": "Ongoing treatment, 3 sessions per week",
    },
    "Cholecystectomy": {
        "procedure_name": "Cholecystectomy (Gallbladder Removal)",
        "procedure_code": "47562-47564",
        "indications": [
            "Symptomatic gallstones (biliary colic)",
            "Acute cholecystitis",
            "Gallstone pancreatitis",
            "Gallbladder polyps > 10mm",
        ],
        "guidelines": [
            {"source": "SAGES", "year": 2020, "recommendation": "Laparoscopic cholecystectomy is gold standard for symptomatic gallstones"},
            {"source": "NICE", "year": 2014, "recommendation": "Offer laparoscopic cholecystectomy within 1 week of diagnosis of acute cholecystitis"},
        ],
        "medical_necessity_criteria": [
            "Documented gallstones on imaging (ultrasound/CT)",
            "Symptomatic presentation (pain, nausea, fever)",
            "No contraindication to surgery",
        ],
        "average_cost_inr": {"range_min": 50000, "range_max": 150000},
        "recovery_days": "1-2 hospital days, 1-2 weeks full recovery",
    },
    "Total_Knee_Replacement": {
        "procedure_name": "Total Knee Arthroplasty (TKR)",
        "procedure_code": "27447",
        "indications": [
            "Severe osteoarthritis of the knee (Kellgren-Lawrence Grade III/IV)",
            "Failed conservative treatment for >6 months",
            "Significant pain affecting daily activities",
            "Radiographic evidence of joint space narrowing",
        ],
        "guidelines": [
            {"source": "AAOS", "year": 2021, "recommendation": "TKR recommended for patients with radiographic evidence and failed non-operative management"},
        ],
        "medical_necessity_criteria": [
            "Radiographic evidence of severe joint degeneration",
            "Failed conservative treatments (physiotherapy, medications, injections)",
            "Significant functional impairment documented",
        ],
        "average_cost_inr": {"range_min": 150000, "range_max": 400000},
        "recovery_days": "5-7 hospital days, 6-12 weeks full recovery",
    },
}


# ═══════════════════════════════════════════════════════════════════
#  MEDICAL KNOWLEDGE BASE CLASS
# ═══════════════════════════════════════════════════════════════════

class MedicalKnowledgeBase:
    """Queryable medical knowledge base with ICD codes & treatment protocols."""

    def lookup_icd_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Look up a specific ICD-10 code."""
        return ICD10_CODES.get(code)

    def find_icd_by_condition(self, condition: str) -> List[Dict[str, Any]]:
        """Find ICD-10 codes matching a medical condition."""
        condition_lower = condition.lower()
        results = []
        for code_data in ICD10_CODES.values():
            if (condition_lower in code_data["common_name"].lower()
                    or condition_lower in code_data["description"].lower()):
                results.append(code_data)
        return results

    def get_treatment_protocol(self, procedure: str) -> Optional[Dict[str, Any]]:
        """Get the standard treatment protocol for a procedure."""
        procedure_upper = procedure.upper().replace(" ", "_")
        # Try exact match first
        if procedure_upper in TREATMENT_PROTOCOLS:
            return TREATMENT_PROTOCOLS[procedure_upper]
        # Fuzzy match
        procedure_lower = procedure.lower()
        for key, protocol in TREATMENT_PROTOCOLS.items():
            if (procedure_lower in protocol["procedure_name"].lower()
                    or procedure_lower in key.lower()):
                return protocol
        return None

    def validate_medical_necessity(
        self, condition: str, procedure: str
    ) -> Dict[str, Any]:
        """Validate whether a procedure is medically necessary for a condition."""
        icd_matches = self.find_icd_by_condition(condition)
        protocol = self.get_treatment_protocol(procedure)

        is_standard = False
        guidelines_cited = []
        necessity_criteria = []

        if protocol:
            guidelines_cited = [
                f"{g['source']} ({g['year']}): {g['recommendation']}"
                for g in protocol.get("guidelines", [])
            ]
            necessity_criteria = protocol.get("medical_necessity_criteria", [])
            # Check if the condition maps to this procedure
            for icd in icd_matches:
                if procedure.upper() in [t.upper() for t in icd.get("standard_treatments", [])]:
                    is_standard = True
                    break
                # Partial match
                for treatment in icd.get("standard_treatments", []):
                    if procedure.lower() in treatment.lower():
                        is_standard = True
                        break

        return {
            "medical_necessity_confirmed": is_standard or bool(protocol),
            "is_standard_treatment": is_standard,
            "icd_codes_matched": [
                {"code": i["code"], "description": i["common_name"]} for i in icd_matches
            ],
            "clinical_guidelines": guidelines_cited,
            "necessity_criteria": necessity_criteria,
            "procedure_details": {
                "name": protocol["procedure_name"] if protocol else procedure,
                "average_cost": protocol.get("average_cost_inr") if protocol else None,
                "recovery": protocol.get("recovery_days") if protocol else None,
            },
            "kb_confirmation": True,
        }

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search across all medical knowledge base entries."""
        query_lower = query.lower()
        results = []

        for code_data in ICD10_CODES.values():
            if (query_lower in code_data["common_name"].lower()
                    or query_lower in code_data["description"].lower()
                    or query_lower in code_data["code"].lower()):
                results.append({
                    "type": "icd_code",
                    "code": code_data["code"],
                    "title": code_data["common_name"],
                    "category": code_data["category"],
                })

        for key, protocol in TREATMENT_PROTOCOLS.items():
            if query_lower in protocol["procedure_name"].lower():
                results.append({
                    "type": "procedure",
                    "code": protocol["procedure_code"],
                    "title": protocol["procedure_name"],
                    "category": "Treatment Protocol",
                })

        return results

    def get_all_icd_codes(self) -> Dict[str, Any]:
        """Return all ICD-10 codes."""
        return ICD10_CODES

    def get_all_protocols(self) -> Dict[str, Any]:
        """Return all treatment protocols."""
        return TREATMENT_PROTOCOLS


medical_kb = MedicalKnowledgeBase()
