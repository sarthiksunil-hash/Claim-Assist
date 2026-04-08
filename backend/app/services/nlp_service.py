"""
NLP Agent - Natural Language Processing & Entity Extraction
Performs regex-based entity extraction, sentiment analysis, and clause extraction
from REAL OCR text — no hardcoded mock data.
"""

import re
from typing import Dict, Any, List
from datetime import datetime


class NLPAgent:
    """Agent 2: NLP analysis of extracted document text."""

    AGENT_NAME = "NLP Text Analysis Agent"
    AGENT_ID = "nlp_agent"

    # ── Medical condition patterns ──
    CONDITION_PATTERNS = [
        (r"coronary\s*artery\s*disease|cad|triple\s*vessel", "Coronary Artery Disease", "I25.1"),
        (r"myocardial\s*infarction|heart\s*attack|mi\b", "Myocardial Infarction", "I21.9"),
        (r"hypertension|high\s*blood\s*pressure|htn\b", "Hypertension", "I10"),
        (r"diabetes\s*mellitus|type\s*[12]\s*diabetes|dm\b", "Diabetes Mellitus", "E11"),
        (r"chronic\s*kidney|ckd|renal\s*failure", "Chronic Kidney Disease", "N18.9"),
        (r"cancer|carcinoma|malignant|oncology", "Cancer / Malignancy", "C80.1"),
        (r"asthma|bronchial\s*asthma", "Bronchial Asthma", "J45.9"),
        (r"copd|chronic\s*obstructive", "COPD", "J44.9"),
        (r"stroke|cerebrovascular|cva\b", "Cerebrovascular Accident", "I63.9"),
        (r"thyroid|hypothyroid|hyperthyroid", "Thyroid Disorder", "E03.9"),
        (r"pneumonia", "Pneumonia", "J18.9"),
        (r"dengue", "Dengue Fever", "A90"),
        (r"fracture", "Fracture", "T14.8"),
        (r"appendicitis|appendectomy", "Appendicitis", "K35.9"),
        (r"hernia|hernioplasty", "Hernia", "K40.9"),
        (r"cataract", "Cataract", "H26.9"),
        (r"kidney\s*stone|renal\s*calcul|nephrolithiasis", "Kidney Stone", "N20.0"),
        (r"gall\s*stone|cholecystitis|cholecystectomy", "Gallstone Disease", "K80.2"),
    ]

    # ── Procedure patterns ──
    PROCEDURE_PATTERNS = [
        (r"cabg|coronary\s*artery\s*bypass|bypass\s*graft", "CABG Surgery"),
        (r"angioplasty|ptca|stent", "Coronary Angioplasty / Stenting"),
        (r"angiography|catheterization", "Coronary Angiography"),
        (r"echocardiography|echo\b", "Echocardiography"),
        (r"dialysis|hemodialysis", "Dialysis"),
        (r"chemotherapy|chemo\b", "Chemotherapy"),
        (r"radiotherapy|radiation\s*therapy", "Radiotherapy"),
        (r"mri\b|magnetic\s*resonance", "MRI"),
        (r"ct\s*scan|computed\s*tomography", "CT Scan"),
        (r"x[\s-]?ray|radiograph", "X-Ray"),
        (r"ultrasound|sonography|usg\b", "Ultrasound"),
        (r"surgery|surgical|operation", "Surgical Procedure"),
        (r"endoscopy|gastroscopy", "Endoscopy"),
        (r"biopsy", "Biopsy"),
        (r"transplant", "Organ Transplant"),
    ]

    # ── Medication patterns ──
    MEDICATION_PATTERNS = [
        (r"aspirin|ecosprin", "Aspirin", "antiplatelet"),
        (r"clopidogrel|plavix", "Clopidogrel", "antiplatelet"),
        (r"metoprolol|atenolol|beta.?blocker", "Beta-Blocker", "cardiac"),
        (r"atorvastatin|rosuvastatin|statin", "Statin", "lipid-lowering"),
        (r"metformin|glucophage", "Metformin", "antidiabetic"),
        (r"insulin", "Insulin", "antidiabetic"),
        (r"amlodipine|nifedipine", "Calcium Channel Blocker", "antihypertensive"),
        (r"losartan|telmisartan|olmesartan|arb\b", "ARB", "antihypertensive"),
        (r"enalapril|ramipril|ace\s*inhibitor", "ACE Inhibitor", "antihypertensive"),
        (r"paracetamol|acetaminophen", "Paracetamol", "analgesic"),
        (r"amoxicillin|azithromycin|antibiotic", "Antibiotic", "antimicrobial"),
        (r"omeprazole|pantoprazole|ppi\b", "PPI", "antacid"),
        (r"heparin|warfarin|anticoagulant", "Anticoagulant", "blood-thinner"),
    ]

    # ── Date patterns ──
    DATE_REGEX = re.compile(
        r"\b(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})\b"
    )

    # ── Amount patterns ──
    AMOUNT_REGEX = re.compile(
        r"(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d{2})?)|"
        r"([\d,]+(?:\.\d{2})?)\s*(?:Rs\.?|INR|rupees)",
        re.IGNORECASE,
    )

    # ── Person name patterns (Title. Name) ──
    PERSON_REGEX = re.compile(
        r"(?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?|Shri|Smt)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})"
    )

    # ── Policy section patterns ──
    CLAUSE_REGEX = re.compile(
        r"(?:section|clause|article|para|provision)\s*(\d+(?:\.\d+)?(?:\([a-z]\))?)",
        re.IGNORECASE,
    )

    async def process(
        self,
        ocr_output: Dict[str, Any],
        denial_reason: str = "",
    ) -> Dict[str, Any]:
        """
        Run NLP analysis on OCR-extracted text.
        Takes the OCR agent's output and performs entity/sentiment analysis.
        """
        start_time = datetime.utcnow()

        extracted_text = ocr_output.get("extracted_text", "")
        key_values = ocr_output.get("key_value_pairs", {})
        doc_type = ocr_output.get("document_type", "")

        # Run sub-tasks
        entities = await self._extract_entities(extracted_text, key_values)
        sentiment = await self._analyze_sentiment(extracted_text, denial_reason)
        clauses = await self._extract_clauses(extracted_text)
        denial_analysis = await self._classify_denial(denial_reason)

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        return {
            "agent_id": self.AGENT_ID,
            "agent_name": self.AGENT_NAME,
            "status": "completed",
            "timestamp": end_time.isoformat(),
            "processing_time": f"{max(duration, 1.0):.1f}s",
            "input": {
                "document_type": doc_type,
                "text_length": len(extracted_text),
                "denial_reason": denial_reason,
            },
            "output": {
                "entities": entities,
                "sentiment_analysis": sentiment,
                "clause_extraction": clauses,
                "denial_classification": denial_analysis,
                "full_text": extracted_text,
                "summary": {
                    "total_entities_found": sum(len(v) for v in entities.values() if isinstance(v, list)),
                    "denial_category": denial_analysis.get("category", "unknown"),
                    "denial_confidence": denial_analysis.get("confidence", 0),
                    "key_terms_count": len(entities.get("key_medical_terms", [])),
                },
            },
        }

    async def _extract_entities(
        self, text: str, key_values: Dict
    ) -> Dict[str, Any]:
        """Extract named entities from the actual document text using regex."""
        text_lower = text.lower()

        # Medical conditions
        conditions = []
        for pattern, name, icd in self.CONDITION_PATTERNS:
            if re.search(pattern, text_lower):
                conditions.append({"name": name, "icd_code": icd, "confidence": 0.90})

        # Procedures
        procedures = []
        for pattern, name in self.PROCEDURE_PATTERNS:
            if re.search(pattern, text_lower):
                procedures.append({"name": name, "confidence": 0.88})

        # Medications
        medications = []
        for pattern, name, med_type in self.MEDICATION_PATTERNS:
            if re.search(pattern, text_lower):
                medications.append({"name": name, "type": med_type})

        # Persons
        persons = []
        for match in self.PERSON_REGEX.finditer(text):
            name = match.group(1).strip()
            prefix = match.group(0).split()[0].lower().rstrip(".")
            role = "treating_doctor" if prefix == "dr" else "patient"
            if not any(p["name"] == name for p in persons):
                persons.append({"name": name, "role": role})

        # Also use key_values for patient/doctor names
        for key in ["Patient Name", "patient_name", "Name"]:
            if key in key_values and key_values[key]:
                name = str(key_values[key]).strip()
                if name and not any(p["name"] == name for p in persons):
                    persons.append({"name": name, "role": "patient"})

        # Organizations (insurers, hospitals)
        organizations = []
        insurer_patterns = [
            r"((?:star|hdfc|icici|bajaj|max|niva|care|aditya\s*birla|tata\s*aig|national|oriental|reliance|sbi|lic)\s*(?:health|general|insurance|ergo|lombard)[\w\s]*)",
        ]
        for pat in insurer_patterns:
            for m in re.finditer(pat, text, re.IGNORECASE):
                org_name = m.group(1).strip().title()
                if not any(o["name"] == org_name for o in organizations):
                    organizations.append({"name": org_name, "type": "insurer"})

        hospital_patterns = [
            r"((?:fortis|apollo|max|medanta|aiims|manipal|narayana|lilavati|kokilaben|hinduja|columbia|global|safdarjung)\s*(?:hospital|healthcare|medical)[\w\s]*)",
        ]
        for pat in hospital_patterns:
            for m in re.finditer(pat, text, re.IGNORECASE):
                org_name = m.group(1).strip().title()
                if not any(o["name"] == org_name for o in organizations):
                    organizations.append({"name": org_name, "type": "hospital"})

        # Also use key_values
        for key in ["Insurer", "Insurance Company", "insurer_name"]:
            if key in key_values and key_values[key]:
                name = str(key_values[key]).strip()
                if name and not any(o["name"] == name for o in organizations):
                    organizations.append({"name": name, "type": "insurer"})
        for key in ["Hospital", "Hospital Name"]:
            if key in key_values and key_values[key]:
                name = str(key_values[key]).strip()
                if name and not any(o["name"] == name for o in organizations):
                    organizations.append({"name": name, "type": "hospital"})

        # Dates
        dates = []
        for m in self.DATE_REGEX.finditer(text):
            date_str = m.group(1)
            # Try to infer context from surrounding text
            context_window = text[max(0, m.start() - 40):m.end() + 10].lower()
            if "admission" in context_window or "admitted" in context_window:
                ctx = "admission"
            elif "discharge" in context_window:
                ctx = "discharge"
            elif "denial" in context_window or "denied" in context_window:
                ctx = "denial_date"
            elif "policy" in context_window or "inception" in context_window:
                ctx = "policy_inception"
            elif "dob" in context_window or "birth" in context_window:
                ctx = "date_of_birth"
            else:
                ctx = "unknown"
            if not any(d["date"] == date_str for d in dates):
                dates.append({"date": date_str, "context": ctx})

        # Amounts
        amounts = []
        for m in self.AMOUNT_REGEX.finditer(text):
            amt = (m.group(1) or m.group(2)).strip()
            context_window = text[max(0, m.start() - 50):m.end() + 10].lower()
            if "claim" in context_window:
                ctx = "claim_amount"
            elif "sum" in context_window and "insured" in context_window:
                ctx = "sum_insured"
            elif "bill" in context_window or "total" in context_window:
                ctx = "bill_amount"
            elif "approved" in context_window or "sanctioned" in context_window:
                ctx = "approved_amount"
            elif "denied" in context_window or "rejected" in context_window:
                ctx = "denied_amount"
            else:
                ctx = "amount"
            amounts.append({"amount": f"Rs. {amt}", "context": ctx})

        # Key medical terms
        medical_terms = []
        term_patterns = [
            "pre-existing", "waiting period", "medical necessity", "cashless",
            "reimbursement", "exclusion", "co-pay", "deductible", "sub-limit",
            "room rent", "icu", "day care", "network hospital", "tpa",
            "policy period", "renewal", "portability", "grace period", "moratorium",
        ]
        for term in term_patterns:
            if term in text_lower:
                medical_terms.append(term)

        # Policy section references
        policy_refs = []
        for m in self.CLAUSE_REGEX.finditer(text):
            section_num = m.group(1)
            # Get surrounding text for title
            surrounding = text[max(0, m.start() - 5):min(len(text), m.end() + 60)].strip()
            policy_refs.append({"section": section_num, "title": surrounding[:80]})

        return {
            "medical_conditions": conditions,
            "procedures": procedures,
            "medications": medications,
            "persons": persons,
            "organizations": organizations,
            "dates": dates,
            "amounts": amounts,
            "key_medical_terms": medical_terms,
            "policy_references": policy_refs,
            "clinical_measurements": [],
        }

    async def _analyze_sentiment(self, text: str, denial_reason: str) -> Dict[str, Any]:
        """Analyze sentiment and tone of the denial letter from actual text."""
        text_lower = text.lower()
        deny_text = (text + " " + denial_reason).lower()

        # Negative phrases
        negative_phrases = []
        neg_patterns = [
            "claim is denied", "claim is rejected", "not eligible",
            "claim denied", "reject", "pre-existing condition",
            "grounds of denial", "not payable", "declined",
            "not covered under", "violation of policy terms",
        ]
        for phrase in neg_patterns:
            if phrase in deny_text:
                negative_phrases.append(phrase)

        # Positive/policyholder-friendly phrases
        friendly_phrases = []
        pos_patterns = [
            "you may appeal", "within 30 days", "grievance",
            "ombudsman", "review", "reconsider",
        ]
        for phrase in pos_patterns:
            if phrase in deny_text:
                friendly_phrases.append(phrase)

        # Determine sentiment
        neg_count = len(negative_phrases)
        pos_count = len(friendly_phrases)
        if neg_count > 2:
            sentiment = "negative"
            firmness = "strong"
        elif neg_count > 0:
            sentiment = "negative"
            firmness = "moderate"
        elif pos_count > neg_count:
            sentiment = "neutral"
            firmness = "mild"
        else:
            sentiment = "neutral"
            firmness = "unknown"

        # Check compliance gaps
        compliance_gaps = []
        if not re.search(r"section\s*\d|clause\s*\d|article\s*\d", deny_text):
            compliance_gaps.append("No specific policy section cited in denial")
        if not any(t in deny_text for t in ["calculation", "computed", "formula", "breakup"]):
            compliance_gaps.append("No calculation methodology explained")
        if "pre-existing" in deny_text and not re.search(r"\d+\s*month|\d+\s*year", deny_text):
            compliance_gaps.append("Vague reference to 'pre-existing condition' without specific duration details")

        specific_clause_cited = bool(re.search(r"section\s*\d|clause\s*\d", deny_text))
        appeal_mentioned = any(t in deny_text for t in ["appeal", "grievance", "ombudsman"])

        return {
            "overall_sentiment": sentiment,
            "confidence": min(0.7 + neg_count * 0.05 + pos_count * 0.03, 0.95),
            "tone": "formal_rejection" if neg_count > 0 else "informational",
            "denial_firmness": firmness,
            "key_negative_phrases": negative_phrases,
            "policyholder_friendly_phrases": friendly_phrases,
            "appeal_window_mentioned": appeal_mentioned,
            "specific_clause_cited": specific_clause_cited,
            "insurer_compliance_gaps": compliance_gaps,
        }

    async def _extract_clauses(self, text: str) -> List[Dict[str, Any]]:
        """Extract policy clauses from the actual text using regex."""
        clauses = []
        text_lower = text.lower()

        # Known clause patterns
        clause_patterns = [
            (r"(?:section|clause)\s*5\.1[^.]*(?:pre.?existing|ped)[^.]*\.", "5.1", "exclusion", "Pre-existing Disease Exclusion"),
            (r"(?:section|clause)\s*4\.1[^.]*(?:in.?patient|hospital)[^.]*\.", "4.1", "coverage", "In-Patient Hospitalization Coverage"),
            (r"(?:section|clause)\s*5\.2[^.]*(?:waiting|disease)[^.]*\.", "5.2", "waiting_period", "Specific Disease Waiting Period"),
            (r"(?:section|clause)\s*8\.1[^.]*(?:cashless|claim)[^.]*\.", "8.1", "process", "Cashless Claim Process"),
        ]

        for pattern, section, clause_type, title in clause_patterns:
            m = re.search(pattern, text_lower, re.DOTALL)
            if m:
                matched_text = text[m.start():m.end()].strip()
                clauses.append({
                    "section": section,
                    "type": clause_type,
                    "title": title,
                    "text": matched_text[:200],
                    "relevance": "high",
                })

        # Generic clause extraction for any section/clause mentions
        for m in self.CLAUSE_REGEX.finditer(text):
            section_num = m.group(1)
            if not any(c["section"] == section_num for c in clauses):
                surrounding = text[m.start():min(len(text), m.end() + 100)]
                period_idx = surrounding.find(".")
                if period_idx > 0:
                    surrounding = surrounding[:period_idx + 1]

                # Classify type
                surrounding_lower = surrounding.lower()
                if "exclusion" in surrounding_lower or "excluded" in surrounding_lower:
                    ctype = "exclusion"
                elif "coverage" in surrounding_lower or "covered" in surrounding_lower:
                    ctype = "coverage"
                elif "waiting" in surrounding_lower:
                    ctype = "waiting_period"
                else:
                    ctype = "general"

                clauses.append({
                    "section": section_num,
                    "type": ctype,
                    "title": f"Section {section_num}",
                    "text": surrounding.strip()[:200],
                    "relevance": "medium",
                })

        # If no clauses found in text, look for implicit clause references
        if not clauses:
            implicit_clauses = []
            if "pre-existing" in text_lower or "ped" in text_lower:
                implicit_clauses.append({
                    "section": "PED",
                    "type": "exclusion",
                    "title": "Pre-existing Disease Exclusion (inferred)",
                    "text": "Document references pre-existing disease exclusion.",
                    "relevance": "medium",
                })
            if "waiting period" in text_lower:
                implicit_clauses.append({
                    "section": "WP",
                    "type": "waiting_period",
                    "title": "Waiting Period (inferred)",
                    "text": "Document references a waiting period.",
                    "relevance": "medium",
                })
            if "not covered" in text_lower or "exclusion" in text_lower:
                implicit_clauses.append({
                    "section": "EXC",
                    "type": "exclusion",
                    "title": "Exclusion Clause (inferred)",
                    "text": "Document references an exclusion or non-coverage clause.",
                    "relevance": "medium",
                })
            clauses = implicit_clauses

        return clauses

    async def _classify_denial(self, denial_reason: str) -> Dict[str, Any]:
        """Classify the denial reason into a standard category."""
        denial_lower = denial_reason.lower()

        if any(term in denial_lower for term in ["pre-existing", "ped", "prior condition"]):
            category = "pre_existing_condition"
            confidence = 0.95
        elif any(term in denial_lower for term in ["medical necessity", "not necessary", "unnecessary"]):
            category = "medical_necessity"
            confidence = 0.92
        elif any(term in denial_lower for term in ["not covered", "excluded", "exclusion"]):
            category = "procedure_not_covered"
            confidence = 0.88
        elif any(term in denial_lower for term in ["document", "insufficient", "missing"]):
            category = "documentation_insufficient"
            confidence = 0.90
        elif any(term in denial_lower for term in ["waiting period", "cooling off"]):
            category = "waiting_period"
            confidence = 0.93
        else:
            category = "other"
            confidence = 0.60

        return {
            "category": category,
            "confidence": confidence,
            "original_reason": denial_reason,
            "standardized_label": category.replace("_", " ").title(),
        }


nlp_agent = NLPAgent()
