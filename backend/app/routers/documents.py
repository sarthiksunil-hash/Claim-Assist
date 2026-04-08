"""
Document upload and processing router
Each user's documents are isolated using user_email from request headers.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Header
from typing import List, Optional
import os
import re
import uuid


def _clean_extracted_value(value: str) -> str:
    """Clean an extracted value: strip newlines, take first meaningful line."""
    if not value:
        return ""
    # Replace newlines with spaces, collapse whitespace
    cleaned = re.sub(r'[\n\r]+', ' ', value).strip()
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned


def _clean_person_name(value: str) -> str:
    """Clean a person name: strip titles, trailing noise words."""
    if not value:
        return ""
    # Strip leading title
    cleaned = re.sub(r'^(?:Mr|Mrs|Ms|Dr|Shri|Smt)\.?\s*', '', value, flags=re.IGNORECASE).strip()
    # Strip newlines first
    cleaned = _clean_extracted_value(cleaned)
    # Remove trailing noise words (Date, Age, Birth, Gender, DOB, etc.)
    noise_suffixes = [
        r'\s+(?:Date|Age|Gender|DOB|D\.O\.B|Birth|Sex|Address|Phone|Mobile|Email|Contact|Occupation)\b.*$',
        r'\s+(?:of|Of|OF)\s+(?:Birth|birth|BIRTH).*$',
    ]
    for pattern in noise_suffixes:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE).strip()
    return cleaned


def _is_valid_person_name(value: str) -> bool:
    """Validate that a value looks like a real person name."""
    if not value or len(value.strip()) < 3:
        return False
    value = value.strip()
    # Reject sentence fragments and noise
    noise = [
        "must", "shall", "should", "will", "would", "could", "may", "might",
        "the ", "this ", "that ", "with ", "from ", "have ", "been ",
        "not ", "also", "such", "which", "your", "their", "under",
        "claim", "denied", "rejected", "approved", "insurance", "policy",
        "hospital", "medical", "treatment", "amount", "coverage",
        "period", "filed", "submitted", "mr ", "mrs ", "ms ", "dr ",
        "age", "gender", "dob", "birth", "address", "phone", "email",
        "ization", "subject", "covered",
    ]
    lower = value.lower()
    # If the entire value is just a title
    if lower in ("mr", "mrs", "ms", "dr", "name", "name mr", "name mrs", "name ms"):
        return False
    for n in noise:
        if lower.startswith(n) or lower == n.strip():
            return False
    # Must have at least 2 word-like parts
    parts = value.split()
    valid_parts = [p for p in parts if len(p) >= 2 and p[0].isupper()]
    if len(valid_parts) < 2:
        return False
    # Must not be too long (names rarely exceed 5 words)
    if len(parts) > 6:
        return False
    # Must be mostly alphabetic
    alpha_count = sum(1 for c in value if c.isalpha() or c.isspace() or c == '.')
    if alpha_count / max(len(value), 1) < 0.75:
        return False
    return True


def _is_valid_company_name(value: str) -> bool:
    """Validate that a value looks like a real company name."""
    if not value or len(value.strip()) < 5:
        return False
    value = value.strip()
    lower = value.lower()
    # Reject obvious sentence fragments
    bad_starts = [
        "must", "shall", "should", "will", "would", "could", "the ",
        "this ", "that ", "with ", "from ", "have ", "been ", "not ",
        "also", "such", "which", "your", "their", "under", "above",
        "as per", "in case", "in the", "for the", "by the", "to the",
        ", the", "ization", "subject", "covered",
    ]
    for bs in bad_starts:
        if lower.startswith(bs):
            return False
    # Reject if it's clearly a sentence fragment
    sentence_noise = [
        "must be", "shall be", "should be", "will be", "provided that",
        "subject to", "in accordance", "the policyholder", "the insured",
        "the patient", "as per", "with respect", "are covered",
    ]
    for sn in sentence_noise:
        if sn in lower:
            return False
    return True


def _clean_policy_number(value: str) -> str:
    """Extract just the policy number from a string that may have trailing text."""
    if not value:
        return ""
    cleaned = _clean_extracted_value(value)
    # If it contains 'Policy Period', truncate before it
    for sep in ['Policy Period', 'policy period', 'Period', 'Valid', 'Effective']:
        idx = cleaned.find(sep)
        if idx > 0:
            cleaned = cleaned[:idx].strip()
    return cleaned


def _clean_denial_reason(value: str) -> str:
    """Clean a denial reason: strip leading punctuation, ensure it's substantive."""
    if not value:
        return ""
    cleaned = _clean_extracted_value(value)
    # Strip leading commas, semicolons, periods
    cleaned = re.sub(r'^[,;.\s]+', '', cleaned).strip()
    return cleaned


def _is_valid_denial_reason(value: str) -> bool:
    """Validate that extracted denial reason is substantive."""
    if not value or len(value.strip()) < 15:
        return False
    # Should not start with punctuation
    if value[0] in ',;.':
        return False
    return True
from datetime import datetime

from app.services.ocr_service import ocr_agent
from app.database.supabase_repo import (
    get_user_documents,
    save_document,
    update_document,
    delete_document_record,
)

router = APIRouter()

# Thin in-memory cache for pipeline compatibility (refreshed on every request)
_mem_cache: dict[str, list] = {}


def _get_user_docs(user_email: str) -> list:
    """Get docs from Supabase (with in-memory cache for pipeline access)."""
    docs = get_user_documents(user_email)
    _mem_cache[user_email] = docs
    return docs


def get_all_user_stores():
    """Return the full per-user store dict (for pipeline compatibility)."""
    return _mem_cache


def _extract_metadata_from_text(text: str, file_type: str = "") -> dict:
    """Extract key-value metadata from raw OCR text using regex patterns."""
    meta = {}

    # Patient / Policyholder Name
    for pattern in [
        # With colon: "Patient Name: Mr. Ravi Kumar"
        r"(?:Patient|Policyholder|Insured|Policy\s*Holder)\s*(?:Name)?\s*[:\-]\s*(?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?)?\s*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,3})",
        # Without colon: "Patient Name Mr. Ravi Kumar"  (most common in Indian docs)
        r"(?:Patient|Policyholder|Insured|Policy\s*Holder)\s+Name\s+(?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?)?\s*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,3})",
        # "Name of Insured: Mr. Ravi Kumar"
        r"Name\s+of\s+(?:the\s+)?(?:Patient|Insured|Policyholder|Life\s+Assured)\s*[:\-]?\s*(?:Mr\.?|Mrs\.?|Ms\.?)?\s*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,3})",
        # "Mr. Ravi Kumar" after any name-related keyword
        r"(?:Name|Patient|Policyholder|Insured)[^\n]{0,20}(?:Mr\.?|Mrs\.?|Ms\.?|Dr\.)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,3})",
    ]:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            name = m.group(1).strip()
            if len(name) >= 4 and not any(w in name.lower() for w in ["health", "insurance", "hospital", "limited", "care"]):
                meta["Patient Name"] = name
                break

    # Insurance Company
    for pattern in [
        r"(?:Insurance\s*Company|Insurer|TPA)\s*[:\-]\s*([^\n]{5,60})",
        r"([A-Z][A-Za-z\s]+(?:Insurance|Assurance|Health)\s*(?:Co\.?|Company|Ltd\.?|Limited|Pvt\.?)?[A-Za-z.\s]*)",
    ]:
        m = re.search(pattern, text, re.IGNORECASE)
        if m and "Patient" not in m.group(1):
            val = m.group(1).strip().rstrip(".,;")
            if 5 < len(val) < 80 and any(w in val.lower() for w in ["insurance", "health", "assurance"]):
                meta["Insurer"] = val
                break

    # Claim / Bill Amount  
    for pattern in [
        r"(?:Claim|Bill|Total)\s*(?:Amount)?\s*[:\-]?\s*(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d{2})?)",
        r"(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d{2})?)\s*(?:/\-)?",
        r"(?:Sum\s*Insured|Coverage)\s*[:\-]?\s*(?:Rs\.?|INR|₹)?\s*([\d,]+)",
    ]:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            amount = re.sub(r"[,\s]", "", m.group(1))
            try:
                if float(amount) > 100:
                    meta["Bill Amount"] = amount
                    break
            except ValueError:
                pass

    # Denial Reason
    for pattern in [
        r"(?:Reason\s*(?:for|of)\s*(?:Denial|Rejection|Repudiation))\s*[:\-]\s*([^\n]{10,200})",
        r"(?:claim\s*(?:has been|is)\s*(?:denied|rejected|repudiated))\s*(?:due to|because|as|for)\s*([^\n]{10,200})",
        r"(?:Denial|Rejection)\s*(?:Reason)?\s*[:\-]\s*([^\n]{10,200})",
    ]:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            meta["Denial Reason"] = m.group(1).strip().rstrip(".")
            break

    # Policy Number
    m = re.search(r"(?:Policy\s*(?:No\.?|Number))\s*[:\-]\s*([A-Za-z0-9/\-]{5,30})", text, re.IGNORECASE)
    if m:
        meta["Policy Number"] = m.group(1).strip()

    # Hospital
    m = re.search(r"(?:Hospital|Medical\s*Centre|Nursing\s*Home)\s*(?:Name)?\s*[:\-]\s*([^\n]{5,80})", text, re.IGNORECASE)
    if m:
        val = m.group(1).strip().rstrip(".,;")
        if len(val) >= 5:
            meta["Hospital"] = val

    # Diagnosis
    for pattern in [
        r"(?:Diagnosis|Diagnosed\s*with)\s*[:\-]\s*([^\n]{5,100})",
        r"(?:Primary\s*Diagnosis)\s*[:\-]\s*([^\n]{5,100})",
    ]:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            meta["Diagnosis"] = m.group(1).strip().rstrip(".")
            break

    # Sum Insured
    m = re.search(r"(?:Sum\s*Insured)\s*[:\-]?\s*(?:Rs\.?|INR|₹)?\s*([\d,]+)", text, re.IGNORECASE)
    if m:
        meta["Sum Insured"] = re.sub(r"[,\s]", "", m.group(1))

    return meta


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    file_type: str = Form(..., description="Type: policy, medical_report, denial_letter, medical_bill"),
    x_user_email: Optional[str] = Header(None),
):
    """Upload a document for processing"""
    user_email = x_user_email or "default"

    allowed_types = ["policy", "medical_report", "denial_letter", "medical_bill"]
    if file_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"file_type must be one of: {allowed_types}")

    allowed_extensions = [".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"]
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"File extension {ext} not allowed. Allowed: {allowed_extensions}")

    # Save file in user-specific directory
    user_dir = f"uploads/{user_email.replace('@', '_at_').replace('.', '_')}"
    os.makedirs(user_dir, exist_ok=True)

    file_id = str(uuid.uuid4())[:8]
    save_path = f"{user_dir}/{file_id}_{file.filename}"

    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    # ── OCR: Fast local extraction first, Groq as fallback ──
    extracted_text = ""
    metadata = {}
    ocr_status = "uploaded"
    ocr_source = "none"
    is_pdf = ext == ".pdf"

    # ─── Approach 1: Fast local text extraction for PDFs ───
    if is_pdf:
        try:
            import pdfplumber
            text_parts = []
            with pdfplumber.open(save_path) as pdf:
                for page in pdf.pages[:10]:
                    t = page.extract_text()
                    if t:
                        text_parts.append(t)
            if text_parts:
                extracted_text = "\n\n".join(text_parts)
                ocr_source = "pdfplumber"
                print(f"[Documents] pdfplumber: {len(extracted_text)} chars extracted")
        except Exception as e:
            print(f"[Documents] pdfplumber failed: {e}")

        if not extracted_text:
            try:
                import PyPDF2
                text_parts = []
                with open(save_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages[:10]:
                        t = page.extract_text()
                        if t and t.strip():
                            text_parts.append(t)
                if text_parts:
                    extracted_text = "\n\n".join(text_parts)
                    ocr_source = "pypdf2"
                    print(f"[Documents] PyPDF2: {len(extracted_text)} chars extracted")
            except Exception as e:
                print(f"[Documents] PyPDF2 failed: {e}")

    # ─── Approach 2: Groq Vision for images or scanned PDFs ───
    if not extracted_text or (is_pdf and len(extracted_text.strip()) < 50):
        try:
            from app.services.groq_service import groq_vision_ocr
            groq_result = groq_vision_ocr(save_path, file_type)
            if groq_result and groq_result.get("full_text", "").strip():
                extracted_text = groq_result["full_text"]
                metadata = groq_result.get("key_value_pairs", {})
                ocr_source = groq_result.get("source", "groq_vision")
                print(f"[Documents] Groq OCR: {len(extracted_text)} chars extracted")
        except Exception as e:
            print(f"[Documents] Groq Vision OCR failed: {e}")

    # ─── Approach 3: Local OCR agent fallback ───
    if not extracted_text:
        try:
            ocr_result = await ocr_agent.process(save_path, file_type)
            extracted_text = ocr_result.get("output", {}).get("extracted_text", "")
            metadata = ocr_result.get("output", {}).get("key_value_pairs", {})
            ocr_source = "local_ocr"
        except Exception as e:
            print(f"[Documents] Local OCR also failed: {e}")

    # ─── Extract metadata from text using regex (if metadata is empty) ───
    if extracted_text and (not metadata or len(metadata) == 0):
        metadata = _extract_metadata_from_text(extracted_text, file_type)
        print(f"[Documents] Regex metadata: {list(metadata.keys())}")

    if extracted_text:
        ocr_status = "processed"

    # ── Build document record ──
    doc = {
        "file_id":        file_id,
        "filename":       file.filename,
        "file_type":      file_type,
        "file_path":      save_path,
        "file_size":      len(content),
        "upload_date":    datetime.utcnow().isoformat(),
        "status":         ocr_status,
        "ocr_source":     ocr_source,
        "extracted_text": extracted_text,
        "metadata":       metadata if isinstance(metadata, dict) else {},
        "user_email":     user_email,
        "rag_indexed":    False,
        "rag_chunks":     0,
    }

    # ── RAG: Chunk and index into FAISS ──
    if extracted_text and len(extracted_text.strip()) > 50:
        try:
            from app.services.semantic_chunker import semantic_chunk
            from app.services.vector_store import index_document as vs_index

            chunks = semantic_chunk(extracted_text)
            if chunks:
                vs_index(
                    doc_id=file_id,
                    chunks=chunks,
                    metadata={"file_type": file_type, "filename": file.filename},
                    user_email=user_email,
                )
                doc["rag_indexed"] = True
                doc["rag_chunks"] = len(chunks)
                print(f"[Documents] RAG indexed {len(chunks)} chunks for {file.filename}")
        except Exception as e:
            print(f"[Documents] RAG indexing skipped: {e}")

    # ── Persist to Supabase (or in-memory fallback) ──
    saved_doc = save_document(doc)

    # Update in-memory cache so pipeline can see the doc immediately
    _mem_cache.setdefault(user_email, [])
    # Avoid duplicates: replace by file_type (each user has one doc per type)
    _mem_cache[user_email] = [
        d for d in _mem_cache[user_email] if d.get("file_type") != file_type
    ]
    _mem_cache[user_email].append(saved_doc)

    return {"message": "Document uploaded successfully", "document": saved_doc}


@router.get("/")
async def list_documents(x_user_email: Optional[str] = Header(None)):
    """List documents for the current user"""
    user_email = x_user_email or "default"
    user_docs = _get_user_docs(user_email)
    return {"documents": user_docs, "total": len(user_docs)}


@router.get("/extracted-details")
async def get_extracted_details(x_user_email: Optional[str] = Header(None)):
    """Get OCR-extracted details for the current user's documents."""
    user_email = x_user_email or "default"
    user_docs = _get_user_docs(user_email)

    details = {
        "patient_name": "",
        "insurer_name": "",
        "claim_amount": "",
        "denial_reason": "",
        "policy_number": "",
        "hospital": "",
        "diagnosis": "",
        "documents_count": len(user_docs),
        "extraction_sources": {},
    }

    for doc in user_docs:
        meta = doc.get("metadata", {})
        if not isinstance(meta, dict):
            continue
        text = doc.get("extracted_text", "")
        doc_type = doc.get("file_type", "")

        # ── Patient / Policyholder Name ──
        if not details["patient_name"]:
            for key in ["Patient Name", "Policyholder", "Policyholder Name",
                        "Insured Name", "patient_name"]:
                if key in meta and meta[key]:
                    candidate = _clean_person_name(str(meta[key]))
                    if _is_valid_person_name(candidate):
                        details["patient_name"] = candidate
                        details["extraction_sources"]["patient_name"] = doc_type
                        break

        # ── Insurance Company ──
        if not details["insurer_name"]:
            for key in ["Insurer", "Insurer Name", "Insurance Company",
                        "TPA Name", "insurer_name"]:
                if key in meta and meta[key]:
                    candidate = _clean_extracted_value(str(meta[key]))
                    if _is_valid_company_name(candidate):
                        details["insurer_name"] = candidate
                        details["extraction_sources"]["insurer_name"] = doc_type
                        break
            # Fallback: search in full text for a company name with "Insurance"
            if not details["insurer_name"] and text:
                insurer_patterns = [
                    r"(?:Insurer|Insurance\s*Company|TPA)\s*[:\-]\s*([^\n]{5,60})",
                    r"([A-Z][A-Za-z\s]+(?:Insurance|Assurance)\s*(?:Co\.?|Company|Ltd\.?|Limited|Pvt\.?)?)",
                ]
                for pattern in insurer_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        val = match.group(1).strip()
                        if _is_valid_company_name(val) and 5 < len(val) < 80:
                            details["insurer_name"] = val
                            details["extraction_sources"]["insurer_name"] = doc_type
                            break

        # ── Claim Amount ──
        if not details["claim_amount"]:
            for key in ["Claim Amount", "Total Bill", "Bill Amount",
                        "Amount", "Sum Insured", "Total", "claim_amount"]:
                if key in meta and meta[key]:
                    val = str(meta[key]).strip()
                    amount = re.sub(r"[₹,\s]", "", val)
                    try:
                        parsed = float(amount)
                        if parsed > 0:
                            details["claim_amount"] = amount
                            details["extraction_sources"]["claim_amount"] = doc_type
                    except ValueError:
                        pass
                    break

        # ── Denial Reason ──
        if not details["denial_reason"]:
            for key in ["Denial Reason", "Rejection Reason", "Denial Reason Extracted",
                        "denial_reason_extracted", "denial_reason"]:
                if key in meta and meta[key]:
                    candidate = _clean_denial_reason(str(meta[key]))
                    if _is_valid_denial_reason(candidate):
                        details["denial_reason"] = candidate
                        details["extraction_sources"]["denial_reason"] = doc_type
                        break

        # ── Policy Number ──
        if not details["policy_number"]:
            for key in ["Policy Number", "Policy No", "policy_number"]:
                if key in meta and meta[key]:
                    val = _clean_policy_number(str(meta[key]))
                    if len(val) >= 3:
                        details["policy_number"] = val
                        break

        # ── Hospital ──
        if not details["hospital"]:
            for key in ["Hospital", "Hospital Name", "hospital"]:
                if key in meta and meta[key]:
                    val = _clean_extracted_value(str(meta[key]))
                    # Reject partial/garbage values
                    if len(val) >= 5 and not val.lower().startswith("ization"):
                        details["hospital"] = val
                        break

        # ── Diagnosis ──
        if not details["diagnosis"]:
            for key in ["Diagnosis", "Primary Diagnosis", "diagnosis"]:
                if key in meta and meta[key]:
                    val = _clean_extracted_value(str(meta[key]))
                    # Strip "Primary Diagnosis:" prefix if present
                    val = re.sub(r'^(?:Primary\s+)?Diagnosis\s*[:\-]\s*', '', val, flags=re.IGNORECASE).strip()
                    if len(val) >= 5:
                        details["diagnosis"] = val
                        break

        # ── Policy Period ──
        if "policy_period" not in details:
            for key in ["Policy Period", "policy_period"]:
                if key in meta and meta[key]:
                    details["policy_period"] = str(meta[key]).strip()
                    break

    # ══════════════════════════════════════════════════════════════
    #  FALLBACK: Extract from raw text when metadata is empty
    #  (common when Groq Vision returns text but no key_value_pairs)
    # ══════════════════════════════════════════════════════════════
    for doc in user_docs:
        text = doc.get("extracted_text", "") or ""
        if not text or len(text) < 100:
            continue
        doc_type = doc.get("file_type", "")

        # Patient Name from text
        if not details["patient_name"]:
            for pattern in [
                # With colon: "Patient Name: Mr. Ravi Kumar"
                r"(?:Patient|Policyholder|Insured|Policy\s*Holder)\s*(?:Name)?\s*[:\-]\s*(?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?)?\s*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,3})",
                # Without colon: "Patient Name Mr. Ravi Kumar"
                r"(?:Patient|Policyholder|Insured|Policy\s*Holder)\s+Name\s+(?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?)?\s*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,3})",
                # "Name of Insured: Mr. Ravi Kumar"
                r"Name\s+of\s+(?:the\s+)?(?:Patient|Insured|Policyholder|Life\s+Assured)\s*[:\-]?\s*(?:Mr\.?|Mrs\.?|Ms\.?)?\s*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,3})",
                # "Mr. Ravi Kumar" near a name keyword
                r"(?:Name|Patient|Policyholder|Insured)[^\n]{0,20}(?:Mr\.?|Mrs\.?|Ms\.?|Dr\.)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,3})",
            ]:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    name = match.group(1).strip()
                    if _is_valid_person_name(name):
                        details["patient_name"] = name
                        details["extraction_sources"]["patient_name"] = doc_type
                        break

        # Insurer from text
        if not details["insurer_name"]:
            for pattern in [
                r"(?:Insurer|Insurance\s*Company|TPA)\s*[:\-]\s*([^\n]{5,60})",
                r"([A-Z][A-Za-z\s]+(?:Insurance|Assurance|Health)\s*(?:Co\.?|Company|Ltd\.?|Limited|Pvt\.?)?)",
            ]:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    val = match.group(1).strip().rstrip(".")
                    if _is_valid_company_name(val) and 5 < len(val) < 80:
                        details["insurer_name"] = val
                        details["extraction_sources"]["insurer_name"] = doc_type
                        break

        # Claim Amount from text
        if not details["claim_amount"]:
            for pattern in [
                r"(?:Claim|Bill|Total)\s*(?:Amount)?\s*[:\-]?\s*(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d{2})?)",
                r"(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d{2})?)\s*(?:/\-)?",
                r"(?:Sum\s*Insured|Coverage)\s*[:\-]?\s*(?:Rs\.?|INR|₹)?\s*([\d,]+)",
            ]:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    amount = re.sub(r"[,\s]", "", match.group(1))
                    try:
                        if float(amount) > 0:
                            details["claim_amount"] = amount
                            details["extraction_sources"]["claim_amount"] = doc_type
                            break
                    except ValueError:
                        pass

        # Denial Reason from text
        if not details["denial_reason"]:
            for pattern in [
                r"(?:Reason\s*(?:for|of)\s*(?:Denial|Rejection|Repudiation))\s*[:\-]\s*([^\n]{10,200})",
                r"(?:claim\s*(?:has been|is)\s*(?:denied|rejected|repudiated))\s*(?:due to|because|as|for)\s*([^\n]{10,200})",
                r"(?:Denial|Rejection)\s*(?:Reason)?\s*[:\-]\s*([^\n]{10,200})",
            ]:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    reason = match.group(1).strip().rstrip(".")
                    if len(reason) >= 10:
                        details["denial_reason"] = reason
                        details["extraction_sources"]["denial_reason"] = doc_type
                        break

        # Diagnosis from text
        if not details["diagnosis"]:
            for pattern in [
                r"(?:Diagnosis|Diagnosed\s*with)\s*[:\-]\s*([^\n]{5,100})",
                r"(?:Primary\s*Diagnosis)\s*[:\-]\s*([^\n]{5,100})",
            ]:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    val = match.group(1).strip().rstrip(".")
                    if len(val) >= 5:
                        details["diagnosis"] = val
                        break

        # Hospital from text
        if not details["hospital"]:
            for pattern in [
                r"(?:Hospital|Medical\s*Centre|Nursing\s*Home)\s*(?:Name)?\s*[:\-]\s*([^\n]{5,80})",
            ]:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    val = match.group(1).strip().rstrip(".")
                    if len(val) >= 5:
                        details["hospital"] = val
                        break

        # Policy Number from text
        if not details["policy_number"]:
            match = re.search(r"(?:Policy\s*(?:No\.?|Number))\s*[:\-]\s*([A-Za-z0-9/\-]{5,30})", text, re.IGNORECASE)
            if match:
                details["policy_number"] = match.group(1).strip()

    return details


@router.get("/{doc_id}")
async def get_document(doc_id: int, x_user_email: Optional[str] = Header(None)):
    """Get document details"""
    user_email = x_user_email or "default"
    user_docs = _get_user_docs(user_email)
    for doc in user_docs:
        if doc["id"] == doc_id:
            return doc
    raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")


@router.post("/{doc_id}/process")
async def process_document(doc_id: int, x_user_email: Optional[str] = Header(None)):
    """Trigger OCR processing for a document"""
    user_email = x_user_email or "default"
    user_docs = _get_user_docs(user_email)
    for doc in user_docs:
        if doc["id"] == doc_id:
            try:
                ocr_result = await ocr_agent.process(doc["file_path"], doc["file_type"])
                doc["extracted_text"] = ocr_result.get("output", {}).get("extracted_text", "")
                doc["metadata"] = ocr_result.get("output", {}).get("key_value_pairs", {})
                doc["status"] = "processed"
                return {
                    "message": f"Processing complete for document {doc_id}",
                    "status": "processed",
                    "ocr_result": ocr_result,
                }
            except Exception as e:
                return {
                    "message": f"Processing failed: {str(e)}",
                    "status": "error",
                }
    raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")


@router.delete("/{doc_id}")
async def delete_document(doc_id: int, x_user_email: Optional[str] = Header(None)):
    """Delete a document — removes from store, disk, and FAISS index."""
    user_email = x_user_email or "default"
    user_docs = _get_user_docs(user_email)

    for i, doc in enumerate(user_docs):
        if doc["id"] == doc_id:
            # Remove file from disk
            file_path = doc.get("file_path", "")
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"[Documents] File delete error: {e}")

            # Remove from FAISS vector store
            file_id = doc.get("file_id", "")
            if file_id:
                try:
                    from app.services.vector_store import delete_document as vs_delete
                    vs_delete(file_id, user_email=user_email)
                except Exception as e:
                    print(f"[Documents] FAISS delete error: {e}")

            # Remove from in-memory store
            user_docs.pop(i)
            return {"message": f"Document {doc_id} deleted successfully"}

    raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
