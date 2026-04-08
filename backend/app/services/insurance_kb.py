"""
Insurance Knowledge Base - IRDAI Regulations, Policy Clauses & Appeal Strategies
This serves as the reference data for the Policy Agent to validate against.
"""

from typing import Dict, Any, List, Optional


# ═══════════════════════════════════════════════════════════════════
#  IRDAI REGULATIONS & CIRCULARS
# ═══════════════════════════════════════════════════════════════════

IRDAI_REGULATIONS = [
    {
        "id": "IRDAI-REG-001",
        "title": "IRDAI (Health Insurance) Regulations, 2016",
        "circular_no": "IRDA/HLT/REG/CIR/276/12/2016",
        "category": "health_insurance",
        "key_provisions": [
            "Pre-existing disease waiting period cannot exceed 48 months",
            "No claim can be denied solely on the basis of pre-existing disease after the waiting period",
            "Every denial must cite specific policy clause and provide clear rationale",
            "Insurers must settle or reject claims within 30 days of receipt of last necessary document",
            "Grace period of 30 days for premium payment in health insurance",
        ],
        "applicable_to": ["pre_existing_condition", "claim_denial", "waiting_period"],
    },
    {
        "id": "IRDAI-REG-002",
        "title": "IRDAI Master Circular on Health Insurance, 2020",
        "circular_no": "IRDAI/HLT/CIR/MISC/118/06/2020",
        "category": "health_insurance",
        "key_provisions": [
            "Medical necessity determination must be based on standard medical practice",
            "Cost considerations alone cannot be grounds for denial",
            "Treatment at non-network hospital must be reimbursed if treatment was emergency",
            "Standardized definitions for critical illness and specific diseases",
            "Portability of health insurance with credit for waiting periods served",
        ],
        "applicable_to": ["medical_necessity", "cost_dispute", "emergency_treatment", "portability"],
    },
    {
        "id": "IRDAI-REG-003",
        "title": "IRDAI Guidelines on TPA Regulations, 2016",
        "circular_no": "IRDAI/HLT/REG/CIR/180/07/2016",
        "category": "tpa_guidelines",
        "key_provisions": [
            "TPAs must process cashless requests within 2 hours for planned hospitalization",
            "Emergency cashless requests must be processed within 1 hour",
            "Every denial must be communicated in writing with specific reasons",
            "TPA cannot independently deny a claim without insurer's authorization",
            "Denial letter must specify the exact policy clause and exclusion relied upon",
        ],
        "applicable_to": ["cashless_claim", "denial_procedure", "tpa_compliance"],
    },
    {
        "id": "IRDAI-REG-004",
        "title": "Insurance Ombudsman Rules, 2017",
        "circular_no": "IRDAI/GA/GDL/OMBD/173/05/2017",
        "category": "grievance_redressal",
        "key_provisions": [
            "Complaints up to ₹30 lakhs can be filed with Insurance Ombudsman",
            "Complaint must be filed within 1 year of insurer's final response",
            "Ombudsman must pass award within 3 months of receipt of complaint",
            "Ombudsman award is binding on the insurer but not on the policyholder",
            "No legal representation required — policyholder can file directly",
        ],
        "applicable_to": ["claim_denial", "grievance", "appeal"],
    },
    {
        "id": "IRDAI-REG-005",
        "title": "IRDAI Regulation on Protection of Policyholders' Interests, 2017",
        "circular_no": "IRDAI/REG/8/147/2017",
        "category": "policyholder_protection",
        "key_provisions": [
            "Policyholder must be informed of claim status at every stage",
            "Insurer must provide free-look period of 15 days for new policies",
            "No arbitrary rejection of claims — must follow standardized processes",
            "Policy terms must be in simple, understandable language",
            "Insurer must maintain records of all claim communications",
        ],
        "applicable_to": ["claim_processing", "transparency", "communication"],
    },
    {
        "id": "IRDAI-REG-006",
        "title": "IRDAI Guidelines on Standardization of Health Insurance Exclusions, 2019",
        "circular_no": "IRDAI/HLT/CIR/MISC/067/04/2019",
        "category": "exclusions",
        "key_provisions": [
            "List of 17 permanent exclusions standardized across all health policies",
            "Pre-existing disease exclusion limited to 48 months maximum",
            "Specific disease waiting period limited to 24-48 months",
            "Maternity cover waiting period: 24-36 months depending on policy",
            "Exclusions must be explicitly listed in policy document",
        ],
        "applicable_to": ["exclusion", "waiting_period", "pre_existing_condition"],
    },
]


# ═══════════════════════════════════════════════════════════════════
#  STANDARD POLICY CLAUSE TEMPLATES
# ═══════════════════════════════════════════════════════════════════

STANDARD_POLICY_CLAUSES = {
    "pre_existing_disease": {
        "section": "5.1",
        "title": "Pre-existing Disease (PED) Exclusion",
        "standard_text": "Any condition, ailment, injury or disease that is diagnosed or for which medical advice or treatment was recommended by or received from a medical practitioner prior to the inception of the first policy, is excluded during the initial waiting period.",
        "irdai_max_waiting": 48,  # months
        "appeal_strategy": "If the policyholder has completed the waiting period, the PED exclusion no longer applies. Calculate months of continuous coverage from policy inception to claim date.",
    },
    "waiting_period": {
        "section": "5.2",
        "title": "Specific Disease Waiting Period",
        "standard_text": "Certain specified diseases/procedures have a waiting period of 24-48 months from the date of first policy inception.",
        "common_diseases": [
            "Cataract surgery (24 months)",
            "Joint replacement (24 months)",
            "Hernia surgery (24 months)",
            "Kidney/gallbladder stones (12 months)",
            "Benign prostatic hypertrophy (24 months)",
        ],
        "appeal_strategy": "Verify if the condition falls under the specified disease list and whether the waiting period has been served.",
    },
    "medical_necessity": {
        "section": "4.1",
        "title": "In-Patient Hospitalization Coverage",
        "standard_text": "The company shall cover reasonable and necessary medical expenses for treatment requiring hospitalization for a minimum period of 24 consecutive hours.",
        "appeal_strategy": "Demonstrate that the treatment was medically necessary as per standard medical guidelines (ACC/AHA, WHO, NHM). Provide clinical evidence including diagnosis, failed conservative treatments, and specialist recommendations.",
    },
    "cashless_claim": {
        "section": "8.1",
        "title": "Cashless Claim Process",
        "standard_text": "Cashless facility is available at network hospitals. Pre-authorization must be obtained before planned hospitalization. Emergency admissions must be notified within 24 hours.",
        "appeal_strategy": "If cashless was denied but the hospital is in-network and treatment was emergency, IRDAI mandates that the insurer cannot refuse cashless for emergencies.",
    },
    "sum_insured": {
        "section": "3.1",
        "title": "Sum Insured and Sub-limits",
        "standard_text": "The maximum liability of the company in respect of each and every claim shall not exceed the sum insured or any sub-limits specified in the policy schedule.",
        "appeal_strategy": "Check if the denial is due to sub-limits vs overall sum insured. Many sub-limits can be challenged if the policy wordings are ambiguous.",
    },
}


# ═══════════════════════════════════════════════════════════════════
#  COMMON DENIAL REASONS & COUNTER-ARGUMENTS
# ═══════════════════════════════════════════════════════════════════

DENIAL_CATEGORIES = {
    "pre_existing_condition": {
        "label": "Pre-existing Condition Exclusion",
        "description": "Claim denied because the insurer considers the condition to be pre-existing.",
        "counter_arguments": [
            "Verify if the 48-month PED waiting period (IRDAI maximum) has been completed",
            "Check if the condition was disclosed at policy inception — non-disclosure ≠ pre-existing",
            "Continuous renewal counts toward waiting period even if insurer was changed (portability)",
            "IRDAI mandates that PED exclusion cannot be applied indefinitely",
        ],
        "relevant_regulations": ["IRDAI-REG-001", "IRDAI-REG-006"],
    },
    "medical_necessity": {
        "label": "Medical Necessity Not Established",
        "description": "Insurer claims the procedure was not medically necessary.",
        "counter_arguments": [
            "Obtain treating doctor's certificate confirming medical necessity",
            "Reference standard medical guidelines (ACC/AHA, WHO, national protocols)",
            "Show that conservative/alternative treatments were tried and failed",
            "IRDAI Master Circular: necessity must be judged by medical standards, not cost",
        ],
        "relevant_regulations": ["IRDAI-REG-002"],
    },
    "procedure_not_covered": {
        "label": "Procedure Not Covered Under Plan",
        "description": "Insurer states the specific procedure is excluded from the plan.",
        "counter_arguments": [
            "Cross-reference the policy exclusion list — procedure may actually be covered",
            "Check if the procedure falls under a covered broader category",
            "IRDAI standardized exclusions: only 17 permanent exclusions are allowed",
            "If the policy wordings are ambiguous, interpretation favors the policyholder",
        ],
        "relevant_regulations": ["IRDAI-REG-006", "IRDAI-REG-005"],
    },
    "documentation_insufficient": {
        "label": "Insufficient Documentation",
        "description": "Insurer claims not enough documents were provided.",
        "counter_arguments": [
            "Insurer must specify EXACTLY which documents are missing",
            "Insurer must give reasonable time to submit additional documents",
            "IRDAI: Claims cannot be denied for trivial documentation gaps",
            "Insurer has duty to assist policyholder in documentation",
        ],
        "relevant_regulations": ["IRDAI-REG-003", "IRDAI-REG-005"],
    },
    "waiting_period": {
        "label": "Waiting Period Not Completed",
        "description": "Insurer claims the cooling-off or specific disease waiting period hasn't elapsed.",
        "counter_arguments": [
            "Calculate exact months from policy inception to admission date",
            "Credit must be given for previous insurer's waiting period (portability)",
            "Check if the condition actually falls under the specified disease list",
            "General waiting period is 30 days; specific diseases have separate periods",
        ],
        "relevant_regulations": ["IRDAI-REG-001", "IRDAI-REG-006"],
    },
}


# ═══════════════════════════════════════════════════════════════════
#  KNOWLEDGE BASE QUERY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

class InsuranceKnowledgeBase:
    """Queryable insurance knowledge base backed by IRDAI regulations."""

    def get_applicable_regulations(self, denial_category: str) -> List[Dict[str, Any]]:
        """Get IRDAI regulations applicable to a specific denial reason."""
        category_data = DENIAL_CATEGORIES.get(denial_category, {})
        reg_ids = category_data.get("relevant_regulations", [])
        return [r for r in IRDAI_REGULATIONS if r["id"] in reg_ids]

    def get_counter_arguments(self, denial_category: str) -> List[str]:
        """Get counter-arguments for a specific denial type."""
        category_data = DENIAL_CATEGORIES.get(denial_category, {})
        return category_data.get("counter_arguments", [])

    def get_policy_clause(self, clause_type: str) -> Optional[Dict[str, Any]]:
        """Get standard policy clause details by type."""
        return STANDARD_POLICY_CLAUSES.get(clause_type)

    def get_appeal_strategy(self, denial_category: str) -> Dict[str, Any]:
        """Get comprehensive appeal strategy for a denial category."""
        category_data = DENIAL_CATEGORIES.get(denial_category, {})
        regulations = self.get_applicable_regulations(denial_category)
        clause = self.get_policy_clause(denial_category)

        return {
            "denial_type": category_data.get("label", denial_category),
            "counter_arguments": category_data.get("counter_arguments", []),
            "applicable_regulations": [
                {"id": r["id"], "title": r["title"], "circular_no": r["circular_no"]}
                for r in regulations
            ],
            "policy_clause": clause.get("section", "") + " - " + clause.get("title", "") if clause else None,
            "appeal_strategy": clause.get("appeal_strategy", "") if clause else "",
            "irdai_confirmation": True,
        }

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search across all knowledge base entries."""
        query_lower = query.lower()
        results = []

        # Search regulations
        for reg in IRDAI_REGULATIONS:
            if (query_lower in reg["title"].lower()
                    or any(query_lower in p.lower() for p in reg["key_provisions"])):
                results.append({
                    "type": "regulation",
                    "id": reg["id"],
                    "title": reg["title"],
                    "circular_no": reg["circular_no"],
                    "match_source": "irdai_regulation",
                })

        # Search denial categories
        for key, cat in DENIAL_CATEGORIES.items():
            if query_lower in cat["label"].lower() or query_lower in cat["description"].lower():
                results.append({
                    "type": "denial_category",
                    "id": key,
                    "title": cat["label"],
                    "match_source": "denial_category",
                })

        # Search policy clauses
        for key, clause in STANDARD_POLICY_CLAUSES.items():
            if query_lower in clause["title"].lower() or query_lower in clause["standard_text"].lower():
                results.append({
                    "type": "policy_clause",
                    "id": clause["section"],
                    "title": clause["title"],
                    "match_source": "standard_clause",
                })

        return results

    def get_all_regulations(self) -> List[Dict[str, Any]]:
        """Return all IRDAI regulations."""
        return IRDAI_REGULATIONS

    def get_all_denial_categories(self) -> Dict[str, Any]:
        """Return all denial categories."""
        return DENIAL_CATEGORIES


insurance_kb = InsuranceKnowledgeBase()
