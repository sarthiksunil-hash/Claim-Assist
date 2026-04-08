"""
Claim analysis router — delegates to the pipeline for real analysis.
"""

from fastapi import APIRouter, Header
from typing import Optional
from app.models.schemas import ClaimAnalysisRequest
from app.routers.pipeline import run_pipeline, user_pipeline_results, PipelineRequest
from datetime import datetime
import uuid

router = APIRouter()


@router.post("/analyze")
async def analyze_claim(
    request: ClaimAnalysisRequest,
    x_user_email: Optional[str] = Header(None),
):
    """Run full claim analysis — delegates to the multi-agent pipeline."""
    user_email = x_user_email or "default"

    # Build a PipelineRequest from the ClaimAnalysisRequest
    pipeline_req = PipelineRequest(
        patient_name=request.patient_name,
        insurer_name=request.insurer_name,
        claim_amount=request.claim_amount,
        denial_reason=request.denial_reason,
        document_types=getattr(request, "document_types", ["policy", "medical_report", "denial_letter"]),
    )

    # Run the actual pipeline
    result = await run_pipeline(pipeline_req, x_user_email=user_email)

    return result


@router.get("/")
async def list_claims(x_user_email: Optional[str] = Header(None)):
    """List all claim analyses for this user — reads from pipeline results store."""
    user_email = x_user_email or "default"

    # user_pipeline_results stores the LATEST result per user as a single dict
    user_result = user_pipeline_results.get(user_email)

    claims = []
    if user_result and isinstance(user_result, dict):
        assessment = user_result.get("overall_assessment", {})
        if isinstance(assessment, str):
            assessment = {}
        appeal = assessment.get("appeal_strength", "unknown")

        claims.append({
            "id": 1,
            "claim_id": user_result.get("claim_id", "CLM-001"),
            "patient_name": user_result.get("claim_summary", {}).get("patient_name", "Unknown")
                if isinstance(user_result.get("claim_summary"), dict) else "Unknown",
            "insurer_name": user_result.get("claim_summary", {}).get("insurer_name", "Unknown")
                if isinstance(user_result.get("claim_summary"), dict) else "Unknown",
            "claim_amount": user_result.get("claim_summary", {}).get("claim_amount", 0)
                if isinstance(user_result.get("claim_summary"), dict) else 0,
            "status": user_result.get("status", "unknown"),
            "appeal_strength": appeal.get("label", "unknown") if isinstance(appeal, dict) else str(appeal),
            "analysis_date": user_result.get("timestamp", ""),
        })

    return {
        "claims": claims,
        "total": len(claims),
    }


@router.get("/{claim_id}")
async def get_claim(
    claim_id: str,
    x_user_email: Optional[str] = Header(None),
):
    """Get specific claim analysis by claim_id — reads from pipeline results."""
    user_email = x_user_email or "default"
    user_result = user_pipeline_results.get(user_email)

    if user_result and isinstance(user_result, dict):
        if user_result.get("claim_id") == claim_id:
            return user_result

    # Not found — return a summary
    return {
        "claim_id": claim_id,
        "status": "not_found",
        "message": f"No analysis found for claim {claim_id}. Run the pipeline first.",
    }
