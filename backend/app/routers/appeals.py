"""
Appeal letter generation router — generates dynamic appeal letters
based on actual pipeline analysis results.
"""

from fastapi import APIRouter, Header
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter()

# In-memory store (fallback when Supabase is unavailable)
user_appeals_store: dict[str, list] = {}

def _get_user_appeals(user_email: str) -> list:
    from app.database.supabase_repo import get_user_appeals as sb_get
    sb_appeals = sb_get(user_email)
    if sb_appeals:
        user_appeals_store[user_email] = sb_appeals
        return sb_appeals
    # Fallback to memory
    if user_email not in user_appeals_store:
        user_appeals_store[user_email] = []
    return user_appeals_store[user_email]


class AppealGenerateRequest(BaseModel):
    claim_id: Optional[str] = ""
    patient_name: str = ""
    insurer_name: str = ""
    claim_amount: float = 0
    denial_reason: str = ""
    appeal_strength: str = "moderate"
    policy_violations: Optional[list] = []
    medical_findings: Optional[str] = ""
    tone: Optional[str] = "formal"
    include_regulations: Optional[bool] = True
    include_medical_evidence: Optional[bool] = True


def _generate_appeal_letter(data: AppealGenerateRequest) -> str:
    """Generate a dynamic appeal letter based on actual claim data."""
    date_str = datetime.now().strftime("%B %d, %Y")
    patient = data.patient_name or "Policyholder"
    insurer = data.insurer_name or "Insurance Company"
    amount = data.claim_amount
    denial = data.denial_reason or "claim denial"

    # Format amount with commas
    amount_str = f"₹{amount:,.0f}" if amount else "the claimed amount"
    amount_words = _amount_to_words(amount)

    # Build violation sections dynamically
    violation_sections = ""
    if data.policy_violations:
        for i, violation in enumerate(data.policy_violations, 1):
            if isinstance(violation, dict):
                violation_sections += f"\n• {violation.get('description', violation.get('violation', str(violation)))}"
            else:
                violation_sections += f"\n• {violation}"

    letter = f"""APPEAL LETTER FOR CLAIM DENIAL REVERSAL

Date: {date_str}

To,
The Grievance Redressal Officer,
{insurer},

Subject: Appeal Against Claim Denial
Patient Name: {patient}
Denial Reason: {denial}

Respected Sir/Madam,

I am writing to formally appeal the denial of my health insurance claim. After careful analysis of the denial grounds against the policy terms, medical evidence, and applicable IRDAI regulations, I respectfully submit that the denial is not justified on the following grounds:

1. ANALYSIS OF DENIAL REASON

The denial cites "{denial}" as the basis for rejection. However, upon thorough review:
"""

    # Add denial-specific arguments
    denial_lower = denial.lower()
    if "pre-existing" in denial_lower or "ped" in denial_lower:
        letter += f"""
• Under IRDAI Health Insurance Regulations, 2016, pre-existing disease exclusions cannot exceed 48 months of continuous coverage
• If the policy has been active for more than 48 months, this exclusion clause can no longer be invoked
• IRDAI Circular No. IRDA/HLT/REG/2013 explicitly mandates that PED exclusions must adhere to the specified waiting period
• The insurer is obligated to verify the exact period of continuous coverage before applying this exclusion
"""
    elif "not covered" in denial_lower or "exclusion" in denial_lower:
        letter += f"""
• The policy terms must be read in conjunction with IRDAI's standardized health insurance product guidelines
• Any exclusion not explicitly and clearly stated in the policy schedule cannot be applied retroactively
• IRDAI Master Circular on Health Insurance (2020) requires that exclusions be clearly communicated at the time of policy issuance
"""
    elif "medical necessity" in denial_lower or "not medically necessary" in denial_lower:
        letter += f"""
• Medical necessity is determined by the treating physician, not the insurer
• The treating doctor's recommendation in the discharge summary constitutes sufficient evidence of medical necessity
• IRDAI guidelines prohibit insurers from overruling qualified medical opinions without independent medical board review
"""
    elif "waiting period" in denial_lower:
        letter += f"""
• The applicable waiting period must be calculated from the policy inception date
• Under IRDAI regulations, waiting period credits from previous insurers must be honored upon policy portability
• Any ambiguity in waiting period computation must be resolved in favor of the policyholder
"""
    else:
        letter += f"""
• The denial reason "{denial}" must be supported by specific policy clause references
• IRDAI mandates that insurers provide clear, documented reasons with policy clause citations for any denial
• Generic or vague denial reasons violate IRDAI claim settlement guidelines
"""

    if data.include_regulations:
        letter += f"""
2. REGULATORY NON-COMPLIANCE IN DENIAL

The denial letter fails to meet mandatory IRDAI regulatory requirements:

• Insurers must cite specific policy clause numbers when denying claims (IRDAI Guidelines on TPA Regulations, 2016)
• Clear, patient-understandable rationale must be provided (IRDAI Master Circular on Health Insurance, 2020)
• Claims must be settled or rejected within 30 days of receiving all documents (IRDAI TAT Guidelines)
• The Insurance Ombudsman Rules, 2017 (Rule 17) require detailed written reasons for any denial
"""

    if violation_sections:
        letter += f"""
3. IDENTIFIED POLICY VIOLATIONS

The following violations have been identified in the insurer's handling of this claim:{violation_sections}
"""

    if data.include_medical_evidence:
        letter += f"""
{"4" if violation_sections else "3"}. MEDICAL EVIDENCE

{data.medical_findings if data.medical_findings else "The medical records, discharge summary, and treating doctor's certification all support the medical necessity of the treatment provided. The diagnosis and treatment protocol follow established clinical guidelines."}
"""

    letter += f"""
RELIEF SOUGHT

Based on the above analysis, I respectfully request:
(a) Immediate reversal of the claim denial
(b) Settlement of the full claimed amount of {amount_str}{f' ({amount_words})' if amount_words else ''}
(c) Written confirmation of claim approval within 15 business days as per IRDAI TAT guidelines

I reserve my right to escalate this matter to the Insurance Ombudsman under Rule 14 of the Insurance Ombudsman Rules, 2017, and to IRDAI's Integrated Grievance Management System (IGMS) should this appeal not receive due consideration.

All supporting documents including the policy document, discharge summary, diagnostic reports, and the original denial letter are enclosed herewith.

Yours faithfully,
{patient}
Policy Holder

Enclosures:
1. Insurance Policy Document
2. Hospital Discharge Summary
3. Diagnostic Reports
4. Original Denial Letter
5. Hospital Bills and Payment Receipts
6. Treating Doctor's Medical Necessity Certificate"""

    return letter.strip()


def _amount_to_words(amount: float) -> str:
    """Convert amount to Indian number words (simplified)."""
    if not amount or amount <= 0:
        return ""
    amt = int(amount)
    if amt >= 10000000:
        return f"Rupees {amt // 10000000} Crore {_amount_to_words(amt % 10000000)}"
    elif amt >= 100000:
        return f"Rupees {amt // 100000} Lakh {(amt % 100000) // 1000} Thousand" if amt % 100000 else f"Rupees {amt // 100000} Lakhs"
    elif amt >= 1000:
        return f"Rupees {amt // 1000} Thousand {amt % 1000}" if amt % 1000 else f"Rupees {amt // 1000} Thousand"
    else:
        return f"Rupees {amt}"


@router.post("/generate")
async def generate_appeal(request: AppealGenerateRequest, x_user_email: Optional[str] = Header(None)):
    """Generate a dynamic appeal letter based on claim analysis data."""
    user_email = x_user_email or "default"
    appeal_text = _generate_appeal_letter(request)

    # Determine regulations based on denial reason
    regulations = [
        "IRDAI Master Circular on Health Insurance (2020) - Claim Processing Standards",
        "IRDAI Guidelines on TPA Regulations (2016) - Denial Requirements",
        "Insurance Ombudsman Rules, 2017 - Rule 14, Rule 17",
        "IRDAI TAT Guidelines - Claim Settlement Timelines",
    ]

    denial_lower = request.denial_reason.lower()
    if "pre-existing" in denial_lower or "ped" in denial_lower:
        regulations.insert(0, "IRDAI Circular No. IRDA/HLT/REG/2013 - Pre-existing Disease Exclusion Limits")
        regulations.append("IRDAI Health Insurance Regulations, 2016 - Section on Waiting Periods")
    if "waiting period" in denial_lower:
        regulations.append("IRDAI Portability Guidelines - Waiting Period Credits")

    appeal = {
        "claim_id":      request.claim_id or f"CLM-NONE",
        "patient_name":  request.patient_name,
        "insurer_name":  request.insurer_name,
        "appeal_text":   appeal_text,
        "regulations_cited": regulations,
        "citations":     [],
        "generated_at":  datetime.utcnow().isoformat(),
        "status":        "generated",
        "confidence_score": 85.0 if request.appeal_strength == "strong" else 70.0 if request.appeal_strength == "moderate" else 55.0,
        "appeal_strength": request.appeal_strength,
        "word_count":    len(appeal_text.split()),
        "denial_reason": request.denial_reason,
        "claim_amount":  request.claim_amount,
        "user_email":    user_email,
        "tone":          request.tone or "formal",
    }

    # Persist to Supabase
    try:
        from app.database.supabase_repo import save_appeal
        save_appeal(appeal)
    except Exception as e:
        print(f"[Appeals] Supabase save error (non-fatal): {e}")
        # Fallback: keep in memory
        if user_email not in user_appeals_store:
            user_appeals_store[user_email] = []
        user_appeals_store[user_email].append(appeal)

    return appeal


@router.get("/")
async def list_appeals(x_user_email: Optional[str] = Header(None)):
    """List appeal letters for the current user"""
    user_email = x_user_email or "default"
    user_appeals = _get_user_appeals(user_email)
    return {"appeals": user_appeals, "total": len(user_appeals)}


@router.get("/{appeal_id}")
async def get_appeal(appeal_id: int, x_user_email: Optional[str] = Header(None)):
    """Get a specific appeal letter"""
    user_email = x_user_email or "default"
    user_appeals = _get_user_appeals(user_email)
    for appeal in user_appeals:
        if appeal["id"] == appeal_id:
            return appeal
    return {
        "id": appeal_id,
        "status": "not_found",
        "message": "Appeal not found. Generate one first.",
    }


class PDFDownloadRequest(BaseModel):
    appeal_text: str = ""
    patient_name: str = ""
    insurer_name: str = ""
    claim_amount: float = 0
    denial_reason: str = ""
    appeal_strength: str = "moderate"
    confidence_score: float = 0
    regulations_cited: List[str] = []
    word_count: int = 0


@router.post("/download-pdf")
async def download_appeal_pdf(req: PDFDownloadRequest):
    """Generate a professional PDF of the appeal letter and return it for download."""
    from app.services.pdf_service import generate_appeal_pdf

    pdf_bytes = generate_appeal_pdf(
        appeal_text=req.appeal_text,
        patient_name=req.patient_name,
        insurer_name=req.insurer_name,
        claim_amount=req.claim_amount,
        denial_reason=req.denial_reason,
        appeal_strength=req.appeal_strength,
        confidence_score=req.confidence_score,
        regulations_cited=req.regulations_cited,
        word_count=req.word_count,
    )

    safe_name = (req.patient_name or "appeal").replace(" ", "_")
    filename = f"Appeal_Letter_{safe_name}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
