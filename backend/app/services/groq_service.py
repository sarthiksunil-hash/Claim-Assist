"""
Groq Service — Vision OCR + Text Chat via Groq API.

Two main functions:
1. groq_vision_ocr(file_path) — extract text from document images using Groq vision models
2. groq_chat(messages) — generate RAG-augmented responses using Groq text models

Falls back gracefully if Groq API is unavailable.
"""

import os
import base64
import json
from typing import Optional, List, Dict

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Model preferences (try in order)
VISION_MODELS = [
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
    "llama-3.2-90b-vision-preview",
    "llama-3.2-11b-vision-preview",
]
TEXT_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "llama3-8b-8192",
    "mixtral-8x7b-32768",
]

_client = None
_vision_model = None
_text_model = None


def _get_client():
    """Lazy-init Groq client."""
    global _client
    if _client is not None:
        return _client
    key = os.getenv("GROQ_API_KEY", GROQ_API_KEY)
    if not key or key.startswith("your-"):
        print("[Groq] No API key set")
        return None
    try:
        from groq import Groq
        _client = Groq(api_key=key)
        print("[Groq] Client initialized")
        return _client
    except Exception as e:
        print(f"[Groq] Init error: {e}")
        return None


def _pick_model(candidates: List[str], available: List[str]) -> Optional[str]:
    """Pick the first available model from a preference list."""
    for m in candidates:
        if m in available:
            return m
    return None


def _get_models():
    """Discover and cache available vision + text models."""
    global _vision_model, _text_model
    if _vision_model and _text_model:
        return _vision_model, _text_model

    client = _get_client()
    if client is None:
        return None, None

    try:
        models = client.models.list()
        available = [m.id for m in models.data]
        _vision_model = _pick_model(VISION_MODELS, available)
        _text_model = _pick_model(TEXT_MODELS, available)
        print(f"[Groq] Vision model: {_vision_model}")
        print(f"[Groq] Text model:   {_text_model}")
        return _vision_model, _text_model
    except Exception as e:
        print(f"[Groq] Model discovery error: {e}")
        return None, None


def _file_to_base64(file_path: str) -> Optional[str]:
    """Read a file and return its base64 encoding."""
    try:
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        print(f"[Groq] File read error: {e}")
        return None


def _get_mime_type(file_path: str) -> str:
    """Determine MIME type from file extension."""
    ext = os.path.splitext(file_path)[1].lower()
    mime_map = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".tiff": "image/tiff",
        ".tif": "image/tiff",
        ".bmp": "image/bmp",
    }
    return mime_map.get(ext, "application/octet-stream")


# ══════════════════════════════════════════════════════════════
#  VISION OCR
# ══════════════════════════════════════════════════════════════

OCR_SYSTEM_PROMPT = """You are an expert OCR and document analysis assistant for Indian health insurance claims.

Extract ALL text from this document image. Then provide structured analysis.

CRITICAL EXTRACTION RULES:
- Only extract a field if you are CONFIDENT about its value.
- For names: Extract the FULL name (first + last name minimum). Never return just a title like "Mr" or "Mrs" alone.
- For insurance company: Extract the FULL company name (e.g., "Star Health and Allied Insurance Co. Ltd"). Never return sentence fragments.
- For amounts: Extract only numeric values (e.g., "500000" or "2,85,000"). Remove currency symbols.
- For denial reasons: Extract the complete reason text, not just a few words.
- If you cannot confidently determine a field, set its value to null — do NOT guess or use sentence fragments.

Required output structure:
1. **Full Text**: Transcribe every word you can read from the document.
2. **Key-Value Pairs**: Extract ONLY fields you are confident about as JSON:
   - "Patient Name": Full name (e.g., "Rajesh Kumar Sharma"), null if unclear
   - "Policy Number": Policy/Certificate number, null if not found
   - "Insurer Name": Full insurance company name, null if not found
   - "Hospital": Hospital name, null if not found
   - "Admission Date": In DD/MM/YYYY format if found, null otherwise
   - "Discharge Date": In DD/MM/YYYY format if found, null otherwise
   - "Diagnosis": Primary diagnosis, null if not found
   - "Claim Amount": Numeric amount only, null if not found
   - "Denial Reason": Full denial reason text, null if not found
   - "Policy Period": Policy validity period if found, null otherwise
   - "Sum Insured": Numeric amount only, null if not found

3. **Document Type**: Classify as: policy_document, claim_form, denial_letter, medical_report, hospital_bill, discharge_summary, prescription, other

4. **Summary**: 2-3 sentence summary of what this document says.

Return as valid JSON with keys: full_text, key_value_pairs, document_type, summary, confidence (0-100).
"""


def _pdf_to_images(file_path: str) -> List[str]:
    """
    Convert a PDF to a list of base64-encoded PNG images (one per page).
    Tries pdf2image (poppler) first, then PyMuPDF (fitz), then returns empty.
    """
    images_b64 = []

    # Approach 1: pdf2image (requires Poppler)
    try:
        from pdf2image import convert_from_path
        pages = convert_from_path(file_path, dpi=200, first_page=1, last_page=5)
        import io
        for page_img in pages:
            buf = io.BytesIO()
            page_img.save(buf, format="PNG")
            images_b64.append(base64.b64encode(buf.getvalue()).decode("utf-8"))
        if images_b64:
            print(f"[Groq] pdf2image converted {len(images_b64)} page(s)")
            return images_b64
    except Exception as e:
        print(f"[Groq] pdf2image not available: {e}")

    # Approach 2: PyMuPDF (fitz)
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        for page_num in range(min(5, len(doc))):
            page = doc[page_num]
            pix = page.get_pixmap(dpi=200)
            images_b64.append(base64.b64encode(pix.tobytes("png")).decode("utf-8"))
        doc.close()
        if images_b64:
            print(f"[Groq] PyMuPDF converted {len(images_b64)} page(s)")
            return images_b64
    except Exception as e:
        print(f"[Groq] PyMuPDF not available: {e}")

    return images_b64


def _extract_text_from_pdf(file_path: str) -> str:
    """Try to extract raw text from a text-based PDF (no vision needed)."""
    # Try pdfplumber
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages[:10]:
                t = page.extract_text()
                if t:
                    text_parts.append(t)
        if text_parts:
            return "\n\n".join(text_parts)
    except Exception:
        pass

    # Try PyPDF2
    try:
        import PyPDF2
        text_parts = []
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages[:10]:
                t = page.extract_text()
                if t and t.strip():
                    text_parts.append(t)
        if text_parts:
            return "\n\n".join(text_parts)
    except Exception:
        pass

    return ""


def _groq_vision_single_image(client, vision_model: str, b64_data: str,
                               file_type: str, page_label: str = "") -> Optional[str]:
    """Send a single base64 PNG image to Groq Vision and return raw response text."""
    data_url = f"data:image/png;base64,{b64_data}"
    page_hint = f" (page {page_label})" if page_label else ""
    user_prompt = f"Extract all text and structured data from this {file_type.replace('_', ' ')} document{page_hint}."

    try:
        response = client.chat.completions.create(
            model=vision_model,
            messages=[
                {"role": "system", "content": OCR_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": data_url}},
                        {"type": "text", "text": user_prompt},
                    ],
                },
            ],
            max_tokens=4096,
            temperature=0.1,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[Groq] Vision API error{page_hint}: {e}")
        return None


def groq_vision_ocr(file_path: str, file_type: str = "") -> Optional[Dict]:
    """
    Extract text and structured data from a document using Groq vision models.

    For PDFs: converts to images first (Groq Vision only accepts images).
    For images: sends directly.

    Returns:
        Dict with: full_text, key_value_pairs, document_type, summary, confidence
        Or None if Groq is unavailable
    """
    client = _get_client()
    if client is None:
        return None

    vision_model, text_model = _get_models()
    if vision_model is None:
        print("[Groq] No vision model available")
        return None

    ext = os.path.splitext(file_path)[1].lower()
    is_pdf = ext == ".pdf"

    # ── Handle PDFs ──
    if is_pdf:
        # First try: extract text directly from text-based PDFs (fast, no vision needed)
        direct_text = _extract_text_from_pdf(file_path)
        if direct_text and len(direct_text.strip()) > 200:
            print(f"[Groq] Text PDF detected ({len(direct_text)} chars), using LLM for structuring")
            # Use text model to structure the extracted text
            if text_model:
                try:
                    response = client.chat.completions.create(
                        model=text_model,
                        messages=[
                            {"role": "system", "content": OCR_SYSTEM_PROMPT},
                            {"role": "user", "content": f"Here is the text extracted from a {file_type.replace('_', ' ')} document. Analyze and structure it:\n\n{direct_text[:8000]}"},
                        ],
                        max_tokens=4096,
                        temperature=0.1,
                    )
                    content = response.choices[0].message.content
                    result = _parse_ocr_response(content)
                    # Ensure the full raw text is preserved
                    if len(result.get("full_text", "")) < len(direct_text):
                        result["full_text"] = direct_text
                    result["model"] = text_model
                    result["source"] = "groq_text_pdf"
                    print(f"[Groq] Text PDF structured successfully")
                    return result
                except Exception as e:
                    print(f"[Groq] Text PDF structuring failed: {e}")

            # If no text model, still return the raw text
            return {
                "full_text": direct_text,
                "key_value_pairs": {},
                "document_type": file_type or "unknown",
                "summary": "",
                "confidence": 60,
                "model": "pdfplumber",
                "source": "direct_text_extraction",
            }

        # Second try: convert PDF pages to images for vision OCR
        page_images = _pdf_to_images(file_path)
        if page_images:
            all_texts = []
            merged_kvp = {}
            for i, img_b64 in enumerate(page_images):
                content = _groq_vision_single_image(client, vision_model, img_b64, file_type, str(i + 1))
                if content:
                    page_result = _parse_ocr_response(content)
                    all_texts.append(page_result.get("full_text", ""))
                    # Merge key-value pairs (first-found wins)
                    for k, v in page_result.get("key_value_pairs", {}).items():
                        if k not in merged_kvp:
                            merged_kvp[k] = v

            if all_texts:
                combined_text = "\n\n--- Page Break ---\n\n".join(all_texts)
                return {
                    "full_text": combined_text,
                    "key_value_pairs": merged_kvp,
                    "document_type": file_type or "unknown",
                    "summary": f"Extracted from {len(page_images)} page(s)",
                    "confidence": 85,
                    "model": vision_model,
                    "source": "groq_vision_pdf",
                }

        print("[Groq] PDF conversion failed — no images generated")
        # Return the direct text if we got any earlier
        if direct_text:
            return {
                "full_text": direct_text,
                "key_value_pairs": {},
                "document_type": file_type or "unknown",
                "summary": "",
                "confidence": 50,
                "model": "fallback",
                "source": "direct_text_only",
            }
        return None

    # ── Handle images (PNG, JPG, etc.) — send directly ──
    b64_data = _file_to_base64(file_path)
    if b64_data is None:
        return None

    mime_type = _get_mime_type(file_path)
    data_url = f"data:{mime_type};base64,{b64_data}"
    user_prompt = f"Extract all text and structured data from this {file_type.replace('_', ' ')} document."

    try:
        response = client.chat.completions.create(
            model=vision_model,
            messages=[
                {"role": "system", "content": OCR_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": data_url}},
                        {"type": "text", "text": user_prompt},
                    ],
                },
            ],
            max_tokens=4096,
            temperature=0.1,
        )

        content = response.choices[0].message.content
        print(f"[Groq] Vision OCR completed ({vision_model}, {len(content)} chars)")

        result = _parse_ocr_response(content)
        result["model"] = vision_model
        result["source"] = "groq_vision"
        return result

    except Exception as e:
        print(f"[Groq] Vision OCR error: {e}")
        return None


def _parse_ocr_response(content: str) -> Dict:
    """Parse the vision model's response into structured data."""
    # Try JSON parse first
    try:
        # Strip markdown code block if present
        text = content.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        data = json.loads(text)
        raw_kvp = data.get("key_value_pairs", {})

        # Filter out null/None/empty values from key_value_pairs
        kvp = {}
        if isinstance(raw_kvp, dict):
            for k, v in raw_kvp.items():
                if v is not None and str(v).strip() and str(v).strip().lower() != "null":
                    kvp[k] = str(v).strip()

        # Map standardized key names for compatibility
        key_aliases = {
            "Insurer Name": "Insurer",
            "Hospital Name": "Hospital",
            "Patient Name": "Patient Name",
            "Policyholder Name": "Patient Name",
        }
        for alias, standard in key_aliases.items():
            if alias in kvp and standard not in kvp:
                kvp[standard] = kvp[alias]

        return {
            "full_text": data.get("full_text", content),
            "key_value_pairs": kvp,
            "document_type": data.get("document_type", "unknown"),
            "summary": data.get("summary", ""),
            "confidence": data.get("confidence", 85),
        }
    except (json.JSONDecodeError, KeyError):
        pass

    # Fallback: treat entire response as extracted text
    return {
        "full_text": content,
        "key_value_pairs": {},
        "document_type": "unknown",
        "summary": content[:200],
        "confidence": 70,
    }


# ══════════════════════════════════════════════════════════════
#  TEXT CHAT (for RAG generation)
# ══════════════════════════════════════════════════════════════

async def groq_chat(
    messages: List[Dict],
    max_tokens: int = 1024,
    temperature: float = 0.7,
) -> Optional[str]:
    """
    Generate a chat response using Groq text models.

    Args:
        messages: List of {"role": ..., "content": ...} dicts
        max_tokens: Max response tokens
        temperature: Creativity control

    Returns:
        Generated text, or None if Groq unavailable
    """
    client = _get_client()
    if client is None:
        return None

    _, text_model = _get_models()
    if text_model is None:
        print("[Groq] No text model available")
        return None

    try:
        response = client.chat.completions.create(
            model=text_model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        content = response.choices[0].message.content
        print(f"[Groq] Chat response ({text_model}, {len(content)} chars)")
        return content
    except Exception as e:
        print(f"[Groq] Chat error: {e}")
        return None
