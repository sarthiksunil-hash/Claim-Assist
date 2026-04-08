"""
Agent Pipeline Router - Orchestrates all 4 agents and returns individual outputs.
Pipeline: OCR → NLP → Policy Agent (IRDAI) → Medical Agent (Medical KB)
Per-user data isolation using X-User-Email header.
"""

from fastapi import APIRouter, Header
from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime

from app.services.ocr_service import ocr_agent
from app.services.nlp_service import nlp_agent
from app.services.policy_agent import policy_agent
from app.services.medical_agent import medical_agent
from app.services.insurance_kb import insurance_kb
from app.services.medical_kb import medical_kb
from app.routers.documents import _get_user_docs as docs_get_user_docs
from app.database.supabase_repo import save_claim, get_user_claims, get_claim_by_id

router = APIRouter()


class PipelineRequest(BaseModel):
    patient_name: str
    insurer_name: str
    claim_amount: float
    denial_reason: str
    policy_inception_date: Optional[str] = ""
    claim_date: Optional[str] = ""
    document_types: Optional[list] = ["policy", "medical_report", "denial_letter"]
    user_email: Optional[str] = ""


# Per-user pipeline results: { user_email: result_dict }
user_pipeline_results: dict[str, dict] = {}


def _get_user_docs(user_email: str) -> list:
    """Get documents for a specific user from Supabase/memory."""
    return docs_get_user_docs(user_email)


@router.post("/run")
async def run_pipeline(request: PipelineRequest, x_user_email: Optional[str] = Header(None)):
    """
    Run the full multi-agent pipeline.
    Uses actual uploaded files from the user's documents store.
    """
    user_email = request.user_email or x_user_email or "default"
    pipeline_start = datetime.utcnow()

    # Get THIS user's documents
    user_docs = _get_user_docs(user_email)

    # ══════════════════════════════════════════════════════════
    #  AGENT 1: OCR Text Extraction — USE CACHED results from upload
    # ══════════════════════════════════════════════════════════
    ocr_results = {}

    # Build a map of uploaded docs by file_type, using CACHED OCR results
    uploaded_docs = {}
    for doc in user_docs:
        ftype = doc.get("file_type", "")
        if ftype:
            uploaded_docs[ftype] = doc

    for doc_type in request.document_types:
        if doc_type in uploaded_docs:
            cached_doc = uploaded_docs[doc_type]
            cached_text = cached_doc.get("extracted_text", "")
            cached_kvp = cached_doc.get("metadata", {})

            if cached_text and cached_text.strip():
                # Use cached OCR results — no reprocessing needed
                result = {
                    "agent_id": "ocr_agent",
                    "agent_name": "OCR Text Extraction Agent",
                    "status": "completed",
                    "timestamp": datetime.utcnow().isoformat(),
                    "processing_time": "0.0s (cached)",
                    "input": {"file_path": cached_doc.get("file_path", ""), "file_type": doc_type},
                    "output": {
                        "document_type": doc_type.replace("_", " ").title(),
                        "pages": 1,
                        "confidence": 95 if cached_doc.get("ocr_source") == "groq_vision" else 85,
                        "extracted_text": cached_text,
                        "key_value_pairs": cached_kvp if isinstance(cached_kvp, dict) else {},
                        "ocr_source": cached_doc.get("ocr_source", "cached"),
                    },
                }
            else:
                # No cached text — run OCR now
                result = await ocr_agent.process(
                    file_path=cached_doc.get("file_path", ""),
                    file_type=doc_type,
                )
        else:
            result = {
                "agent_id": "ocr_agent",
                "agent_name": "OCR Text Extraction Agent",
                "status": "skipped",
                "timestamp": datetime.utcnow().isoformat(),
                "processing_time": "0.0s",
                "input": {"file_path": "N/A", "file_type": doc_type},
                "output": {
                    "document_type": doc_type.replace("_", " ").title(),
                    "pages": 0,
                    "confidence": 0,
                    "extracted_text": f"[No {doc_type.replace('_', ' ')} was uploaded. Upload this document for analysis.]",
                    "key_value_pairs": {},
                    "notice": f"No {doc_type.replace('_', ' ')} file was uploaded.",
                },
            }
        ocr_results[doc_type] = result

    # Merge all OCR outputs for NLP
    merged_text = "\n\n".join(
        r.get("output", {}).get("extracted_text", "")
        for r in ocr_results.values()
        if r.get("status") != "skipped"
    )
    merged_kvp = {}
    for r in ocr_results.values():
        merged_kvp.update(r.get("output", {}).get("key_value_pairs", {}))

    merged_ocr = {
        "extracted_text": merged_text if merged_text.strip() else f"Patient: {request.patient_name}. Insurer: {request.insurer_name}. Claim Amount: {request.claim_amount}. Denial Reason: {request.denial_reason}.",
        "key_value_pairs": merged_kvp if merged_kvp else {
            "Patient Name": request.patient_name,
            "Insurer": request.insurer_name,
            "Claim Amount": str(request.claim_amount),
            "Denial Reason": request.denial_reason,
        },
        "document_type": "merged_documents",
    }

    # ══════════════════════════════════════════════════════════
    #  AGENT 2: NLP Text Analysis
    # ══════════════════════════════════════════════════════════
    nlp_result = await nlp_agent.process(
        ocr_output=merged_ocr,
        denial_reason=request.denial_reason,
    )

    # ══════════════════════════════════════════════════════════
    #  AGENT 3: Policy Interpretation (IRDAI-Verified)
    # ══════════════════════════════════════════════════════════
    policy_result = await policy_agent.process(
        nlp_output=nlp_result,
        denial_reason=request.denial_reason,
        policy_inception_date=request.policy_inception_date,
        claim_date=request.claim_date,
    )

    # ══════════════════════════════════════════════════════════
    #  AGENT 4: Medical Validation (KB-Verified)
    # ══════════════════════════════════════════════════════════
    medical_result = await medical_agent.process(
        nlp_output=nlp_result,
        denial_reason=request.denial_reason,
    )

    pipeline_end = datetime.utcnow()
    total_duration = (pipeline_end - pipeline_start).total_seconds()

    # ══════════════════════════════════════════════════════════
    #  Compile Final Response
    # ══════════════════════════════════════════════════════════
    result = {
        "pipeline_id": f"PL-{pipeline_start.strftime('%Y%m%d%H%M%S')}",
        "status": "completed",
        "total_processing_time": f"{max(total_duration, 0.5):.1f}s",
        "timestamp": pipeline_end.isoformat(),
        "user_email": user_email,
        "claim_summary": {
            "patient_name": request.patient_name,
            "insurer_name": request.insurer_name,
            "claim_amount": request.claim_amount,
            "denial_reason": request.denial_reason,
        },
        "agents": {
            "ocr_agent": ocr_results,
            "nlp_agent": nlp_result,
            "policy_agent": policy_result,
            "medical_agent": medical_result,
        },
        "overall_assessment": {
            "appeal_strength": _calculate_appeal_strength(policy_result, medical_result),
            "policy_alignment_score": policy_result.get("output", {}).get("policy_alignment_score", 0),
            "medical_necessity_score": medical_result.get("output", {}).get("medical_necessity_score", 0),
            "irdai_violations_count": len(policy_result.get("output", {}).get("insurer_violations", [])),
            "irdai_verified": policy_result.get("irdai_verified", False),
            "medical_kb_verified": medical_result.get("kb_verified", False),
        },
    }

    # Store in memory for fast access + persist to Supabase
    user_pipeline_results[user_email] = result
    try:
        claim_to_save = {
            "claim_id":               result.get("claim_id", ""),
            "user_email":             user_email,
            "patient_name":           request.patient_name,
            "insurer_name":           request.insurer_name,
            "claim_amount":           request.claim_amount,
            "denial_reason":          request.denial_reason,
            "status":                 "completed",
            "policy_alignment_score": result.get("overall_assessment", {}).get("policy_alignment_score", 0),
            "medical_necessity_score": result.get("overall_assessment", {}).get("medical_necessity_score", 0),
            "appeal_strength":        result.get("overall_assessment", {}),
            "discrepancies":          result.get("discrepancies", []),
            "pipeline_results":       result.get("agents", {}),
            "recommendation":         result.get("recommendation", ""),
        }
        save_claim(claim_to_save)
    except Exception as e:
        print(f"[Pipeline] Supabase save error (non-fatal): {e}")

    return result


@router.get("/latest-result")
async def get_latest_pipeline_result(x_user_email: Optional[str] = Header(None)):
    """Get the latest pipeline result for the current user."""
    user_email = x_user_email or "default"

    # Check in-memory cache first
    result = user_pipeline_results.get(user_email)
    if result:
        return result

    # Fallback: rebuild from latest Supabase claim_analyses
    try:
        claims = get_user_claims(user_email)
        if claims:
            latest = claims[0]  # already ordered desc by analyzed_at
            # Reconstruct the pipeline result shape the frontend expects
            pipeline_results = latest.get("pipeline_results", {})
            appeal_strength = latest.get("appeal_strength", {})
            appeal_label = appeal_strength.get("appeal_strength", "moderate") if isinstance(appeal_strength, dict) else "moderate"
            result = {
                "status": "completed",
                "claim_id": latest.get("claim_id", ""),
                "user_email": user_email,
                "claim_summary": {
                    "patient_name": latest.get("patient_name", ""),
                    "insurer_name": latest.get("insurer_name", ""),
                    "claim_amount": float(latest.get("claim_amount", 0)),
                    "denial_reason": latest.get("denial_reason", ""),
                },
                "agents": pipeline_results if isinstance(pipeline_results, dict) else {},
                "overall_assessment": {
                    "appeal_strength": appeal_label,
                    "policy_alignment_score": float(latest.get("policy_alignment_score", 0)),
                    "medical_necessity_score": float(latest.get("medical_necessity_score", 0)),
                    "irdai_violations_count": appeal_strength.get("irdai_violations_count", 0) if isinstance(appeal_strength, dict) else 0,
                },
            }
            user_pipeline_results[user_email] = result
            return result
    except Exception as e:
        print(f"[Pipeline] Supabase latest-result fallback error: {e}")

    return {"status": "no_result", "message": "No pipeline has been run yet."}


@router.get("/agent/{agent_id}")
async def get_agent_output(agent_id: str, x_user_email: Optional[str] = Header(None)):
    """Get a single agent's output individually."""
    user_email = x_user_email or "default"
    user_docs = _get_user_docs(user_email)

    uploaded_files = {}
    for doc in user_docs:
        ftype = doc.get("file_type", "")
        fpath = doc.get("file_path", "")
        if ftype and fpath:
            uploaded_files[ftype] = fpath

    if agent_id == "ocr_agent":
        path = uploaded_files.get("policy", "")
        result = await ocr_agent.process(path, "policy")
        return result

    elif agent_id == "nlp_agent":
        path = uploaded_files.get("medical_report", "")
        ocr_out = await ocr_agent.process(path, "medical_report")
        result = await nlp_agent.process(ocr_out.get("output", {}), "Pre-existing condition")
        return result

    elif agent_id == "policy_agent":
        path = uploaded_files.get("policy", "")
        ocr_out = await ocr_agent.process(path, "policy")
        nlp_out = await nlp_agent.process(ocr_out.get("output", {}), "Pre-existing condition")
        result = await policy_agent.process(nlp_out, "Pre-existing condition exclusion")
        return result

    elif agent_id == "medical_agent":
        path = uploaded_files.get("medical_report", "")
        ocr_out = await ocr_agent.process(path, "medical_report")
        nlp_out = await nlp_agent.process(ocr_out.get("output", {}), "Pre-existing condition")
        result = await medical_agent.process(nlp_out, "Pre-existing condition")
        return result

    else:
        return {"error": f"Unknown agent: {agent_id}", "available_agents": [
            "ocr_agent", "nlp_agent", "policy_agent", "medical_agent"
        ]}


@router.get("/agents")
async def list_agents():
    """List all available agents with their status."""
    return {
        "agents": [
            {
                "id": "ocr_agent",
                "name": "OCR Text Extraction Agent",
                "description": "Extracts text from uploaded documents (policy, medical reports, denial letters)",
                "status": "active",
                "input": "Uploaded document file",
                "output": "Structured text, key-value pairs, sections",
            },
            {
                "id": "nlp_agent",
                "name": "NLP Text Analysis Agent",
                "description": "Performs entity extraction, sentiment analysis, and denial classification",
                "status": "active",
                "input": "OCR extracted text",
                "output": "Entities, sentiment, clauses, denial category",
            },
            {
                "id": "policy_agent",
                "name": "Policy Interpretation Agent (IRDAI-Verified)",
                "description": "Analyzes policy clauses and validates against IRDAI regulations",
                "status": "active",
                "input": "NLP output + denial reason",
                "output": "IRDAI-confirmed clause analysis, violations, appeal strategy",
                "knowledge_base": "Insurance Knowledge Base (IRDAI Regulations)",
                "irdai_verified": True,
            },
            {
                "id": "medical_agent",
                "name": "Medical Validation Agent (KB-Verified)",
                "description": "Validates medical necessity against ICD-10 codes and clinical guidelines",
                "status": "active",
                "input": "NLP output + denial reason",
                "output": "ICD-10 validation, procedure verification, necessity score",
                "knowledge_base": "Medical Knowledge Base (ICD-10, Treatment Protocols)",
                "kb_verified": True,
            },
        ],
        "knowledge_bases": [
            {
                "id": "insurance_kb",
                "name": "Insurance Knowledge Base",
                "description": "IRDAI regulations, circulars, policy clauses, denial categories",
                "entries": {
                    "regulations": len(insurance_kb.get_all_regulations()),
                    "denial_categories": len(insurance_kb.get_all_denial_categories()),
                },
            },
            {
                "id": "medical_kb",
                "name": "Medical Knowledge Base",
                "description": "ICD-10 codes, treatment protocols, clinical guidelines",
                "entries": {
                    "icd_codes": len(medical_kb.get_all_icd_codes()),
                    "treatment_protocols": len(medical_kb.get_all_protocols()),
                },
            },
        ],
    }


@router.get("/knowledge/insurance")
async def get_insurance_kb():
    """View the full Insurance Knowledge Base."""
    return {
        "knowledge_base": "Insurance Knowledge Base (IRDAI)",
        "regulations": insurance_kb.get_all_regulations(),
        "denial_categories": insurance_kb.get_all_denial_categories(),
    }


@router.get("/knowledge/medical")
async def get_medical_kb():
    """View the full Medical Knowledge Base."""
    return {
        "knowledge_base": "Medical Knowledge Base",
        "icd_codes": medical_kb.get_all_icd_codes(),
        "treatment_protocols": medical_kb.get_all_protocols(),
    }


@router.get("/knowledge/search")
async def search_knowledge_bases(q: str = ""):
    """Search across both knowledge bases."""
    insurance_results = insurance_kb.search(q) if q else []
    medical_results = medical_kb.search(q) if q else []

    return {
        "query": q,
        "insurance_kb_results": insurance_results,
        "medical_kb_results": medical_results,
        "total_results": len(insurance_results) + len(medical_results),
    }


def _calculate_appeal_strength(
    policy_result: Dict, medical_result: Dict
) -> str:
    """Calculate overall appeal strength from agent outputs."""
    violations = len(policy_result.get("output", {}).get("insurer_violations", []))
    med_score = medical_result.get("output", {}).get("medical_necessity_score", 0)
    med_confirmed = medical_result.get("output", {}).get("medical_necessity_confirmed", False)
    irdai_verified = policy_result.get("irdai_verified", False)

    if violations >= 2 and med_confirmed and irdai_verified:
        return "strong"
    elif violations >= 1 or med_score >= 70:
        return "moderate"
    else:
        return "weak"
