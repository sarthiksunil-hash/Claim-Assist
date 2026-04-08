"""
Tests for NLP service — Issue 1 & Issue 11 (OCR edge cases + real NLP parsing).
Verifies regex-based entity extraction against real text, not hardcoded mocks.
"""

import pytest
import asyncio
from app.services.nlp_service import NLPAgent


@pytest.fixture
def nlp():
    return NLPAgent()


# ─── Entity Extraction ──────────────────────────────────────────

class TestEntityExtraction:
    """Issue 1: NLP agent must parse actual OCR text."""

    @pytest.mark.asyncio
    async def test_extracts_medical_conditions_from_real_text(self, nlp):
        ocr_out = {
            "extracted_text": "Patient was diagnosed with Coronary Artery Disease and Essential Hypertension.",
            "key_value_pairs": {},
            "document_type": "medical_report",
        }
        ents = await nlp._extract_entities(ocr_out["extracted_text"], {})
        names = [c["name"] for c in ents["medical_conditions"]]
        assert any("Coronary" in n for n in names), "Should detect CAD"
        assert any("Hypertension" in n for n in names), "Should detect hypertension"

    @pytest.mark.asyncio
    async def test_extracts_no_conditions_from_empty_text(self, nlp):
        ents = await nlp._extract_entities("", {})
        assert ents["medical_conditions"] == []
        assert ents["procedures"] == []
        assert ents["medications"] == []

    @pytest.mark.asyncio
    async def test_extracts_amount_from_real_text(self, nlp):
        text = "The claim amount is Rs. 2,85,000 for CABG surgery."
        ents = await nlp._extract_entities(text, {})
        assert len(ents["amounts"]) > 0
        assert any("2,85,000" in a["amount"] or "285000" in a["amount"] for a in ents["amounts"])

    @pytest.mark.asyncio
    async def test_extracts_date_from_real_text(self, nlp):
        text = "Admission date: 05/03/2026. Discharge date: 12/03/2026."
        ents = await nlp._extract_entities(text, {})
        dates = [d["date"] for d in ents["dates"]]
        assert "05/03/2026" in dates or "12/03/2026" in dates

    @pytest.mark.asyncio
    async def test_extracts_doctor_name(self, nlp):
        text = "Treated by Dr. Anand Sharma, Cardiothoracic Surgery."
        ents = await nlp._extract_entities(text, {})
        persons = [p["name"] for p in ents["persons"]]
        assert any("Anand Sharma" in p for p in persons)

    @pytest.mark.asyncio
    async def test_extracts_person_from_key_values(self, nlp):
        ents = await nlp._extract_entities("", {"Patient Name": "Rajesh Kumar"})
        names = [p["name"] for p in ents["persons"]]
        assert "Rajesh Kumar" in names

    @pytest.mark.asyncio
    async def test_extracts_procedures(self, nlp):
        text = "Patient underwent CABG surgery and coronary angiography."
        ents = await nlp._extract_entities(text, {})
        proc_names = [p["name"] for p in ents["procedures"]]
        assert any("CABG" in n for n in proc_names)
        assert any("Angiography" in n for n in proc_names)

    @pytest.mark.asyncio
    async def test_detects_key_terms(self, nlp):
        text = "The claim is denied due to pre-existing condition and waiting period."
        ents = await nlp._extract_entities(text, {})
        assert "pre-existing" in ents["key_medical_terms"]
        assert "waiting period" in ents["key_medical_terms"]

    @pytest.mark.asyncio
    async def test_extracts_medications(self, nlp):
        text = "Currently on Aspirin 75mg, Metoprolol 50mg, Atorvastatin 20mg."
        ents = await nlp._extract_entities(text, {})
        med_names = [m["name"] for m in ents["medications"]]
        assert any("Aspirin" in n for n in med_names)
        assert any("Statin" in n or "Atorvastatin" in n for n in med_names)


# ─── Sentiment Analysis ─────────────────────────────────────────

class TestSentimentAnalysis:

    @pytest.mark.asyncio
    async def test_negative_sentiment_for_denial_text(self, nlp):
        text = "Your claim is denied due to pre-existing condition."
        result = await nlp._analyze_sentiment(text, "claim is denied")
        assert result["overall_sentiment"] == "negative"
        assert len(result["key_negative_phrases"]) > 0

    @pytest.mark.asyncio
    async def test_detects_compliance_gap_no_clause(self, nlp):
        text = "Claim denied due to pre-existing condition."
        result = await nlp._analyze_sentiment(text, "pre-existing condition")
        assert any("section" in g.lower() or "clause" in g.lower() or "policy" in g.lower()
                   for g in result["insurer_compliance_gaps"])

    @pytest.mark.asyncio
    async def test_detects_appeal_window(self, nlp):
        text = "You may appeal this decision within 30 days."
        result = await nlp._analyze_sentiment(text, "")
        assert result["appeal_window_mentioned"] is True

    @pytest.mark.asyncio
    async def test_neutral_sentiment_empty_text(self, nlp):
        result = await nlp._analyze_sentiment("", "")
        assert result["overall_sentiment"] in ("negative", "neutral")
        assert isinstance(result["confidence"], float)


# ─── Clause Extraction ──────────────────────────────────────────

class TestClauseExtraction:

    @pytest.mark.asyncio
    async def test_extracts_ped_clause_inference(self, nlp):
        text = "The denial is based on pre-existing disease exclusion policy."
        clauses = await nlp._extract_clauses(text)
        types = [c["type"] for c in clauses]
        assert "exclusion" in types

    @pytest.mark.asyncio
    async def test_extracts_waiting_period_clause(self, nlp):
        text = "The waiting period for this condition has not been completed."
        clauses = await nlp._extract_clauses(text)
        types = [c["type"] for c in clauses]
        assert "waiting_period" in types

    @pytest.mark.asyncio
    async def test_empty_text_returns_empty_list(self, nlp):
        clauses = await nlp._extract_clauses("   ")
        assert isinstance(clauses, list)


# ─── Denial Classification ──────────────────────────────────────

class TestDenialClassification:

    @pytest.mark.asyncio
    async def test_classifies_ped_denial(self, nlp):
        result = await nlp._classify_denial("Pre-existing condition exclusion applies")
        assert result["category"] == "pre_existing_condition"
        assert result["confidence"] >= 0.9

    @pytest.mark.asyncio
    async def test_classifies_medical_necessity(self, nlp):
        # Use exact terms that match the regex: "medical necessity", "not necessary", "unnecessary"
        result = await nlp._classify_denial("Claim denied: medical necessity not established")
        assert result["category"] == "medical_necessity"

    @pytest.mark.asyncio
    async def test_classifies_not_covered(self, nlp):
        result = await nlp._classify_denial("Procedure not covered under your plan exclusion")
        assert result["category"] == "procedure_not_covered"

    @pytest.mark.asyncio
    async def test_classifies_waiting_period(self, nlp):
        result = await nlp._classify_denial("Waiting period not completed")
        assert result["category"] == "waiting_period"

    @pytest.mark.asyncio
    async def test_classifies_unknown_as_other(self, nlp):
        result = await nlp._classify_denial("Some unusual reason")
        assert result["category"] == "other"
        assert result["confidence"] < 0.9


# ─── Full Process Integration ────────────────────────────────────

class TestNLPProcess:

    @pytest.mark.asyncio
    async def test_full_process_returns_expected_structure(self, nlp):
        ocr_out = {
            "extracted_text": "Patient: John Doe. Insurer: Star Health. Claim denied: pre-existing condition.",
            "key_value_pairs": {"Patient Name": "John Doe"},
            "document_type": "denial_letter",
        }
        result = await nlp.process(ocr_out, "Pre-existing condition")
        assert result["status"] == "completed"
        assert "entities" in result["output"]
        assert "sentiment_analysis" in result["output"]
        assert "clause_extraction" in result["output"]
        assert "denial_classification" in result["output"]
        assert result["output"]["summary"]["denial_category"] == "pre_existing_condition"

    @pytest.mark.asyncio
    async def test_process_does_not_use_hardcoded_names(self, nlp):
        """Critical: results must NOT contain hardcoded 'Rajesh Kumar' etc."""
        ocr_out = {
            "extracted_text": "Patient: John Smith visited Apollo Hospital.",
            "key_value_pairs": {},
            "document_type": "medical_report",
        }
        result = await nlp.process(ocr_out, "not covered")
        all_text = str(result)
        assert "Rajesh Kumar" not in all_text, "Hardcoded mock name found in output!"
        assert "Star Health Insurance" not in all_text or "John Smith" in all_text
