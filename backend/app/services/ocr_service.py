"""
OCR Agent - Document Text Extraction using Tesseract OCR
Extracts text from uploaded PDFs and images using pytesseract.
Falls back to basic text extraction if Tesseract binary is not installed.
"""

from typing import Dict, Any
from datetime import datetime
import os
import re

# Try importing OCR dependencies
try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

try:
    import pytesseract
    # Common Tesseract install paths on Windows
    common_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Users\sunil\AppData\Local\Tesseract-OCR\tesseract.exe",
    ]
    for p in common_paths:
        if os.path.exists(p):
            pytesseract.pytesseract.tesseract_cmd = p
            break
    # Quick test
    pytesseract.get_tesseract_version()
    HAS_TESSERACT = True
except Exception:
    HAS_TESSERACT = False

try:
    from pdf2image import convert_from_path
    HAS_PDF2IMAGE = True
except ImportError:
    HAS_PDF2IMAGE = False

# Try PyPDF2 as fallback for text PDFs
try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

# Try pdfplumber as another fallback
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False


class OCRAgent:
    """Agent 1: Handles optical character recognition for uploaded documents."""

    AGENT_NAME = "OCR Text Extraction Agent"
    AGENT_ID = "ocr_agent"

    def __init__(self):
        self.tesseract_available = HAS_TESSERACT and HAS_PILLOW
        print(f"[OCR Agent] Tesseract available: {HAS_TESSERACT}")
        print(f"[OCR Agent] Pillow available: {HAS_PILLOW}")
        print(f"[OCR Agent] pdf2image available: {HAS_PDF2IMAGE}")
        print(f"[OCR Agent] PyPDF2 available: {HAS_PYPDF2}")
        print(f"[OCR Agent] pdfplumber available: {HAS_PDFPLUMBER}")

    async def process(self, file_path: str, file_type: str = "unknown") -> Dict[str, Any]:
        """
        Run OCR extraction on a document.
        Returns structured output with agent metadata.
        """
        start_time = datetime.utcnow()

        # Check if file exists
        real_path = self._resolve_path(file_path)

        if real_path and os.path.exists(real_path):
            extraction = await self._extract_real(real_path, file_type)
        else:
            # No real file — return notice
            extraction = {
                "document_type": file_type.replace("_", " ").title(),
                "pages": 0,
                "confidence": 0,
                "extracted_text": f"[No file found at: {file_path}. Upload a real document to extract text.]",
                "key_value_pairs": {},
                "notice": "No document file available for OCR processing.",
            }

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        return {
            "agent_id": self.AGENT_ID,
            "agent_name": self.AGENT_NAME,
            "status": "completed",
            "timestamp": end_time.isoformat(),
            "processing_time": f"{max(duration, 0.1):.1f}s",
            "input": {
                "file_path": os.path.basename(file_path) if file_path else "N/A",
                "file_type": file_type,
            },
            "output": extraction,
        }

    def _resolve_path(self, file_path: str) -> str | None:
        """Try to find the actual file on disk."""
        # Directly given path
        if os.path.exists(file_path):
            return file_path

        # Try relative to backend uploads folder
        uploads_dir = os.path.join(os.getcwd(), "uploads")
        if os.path.isdir(uploads_dir):
            # Check for exact filename
            basename = os.path.basename(file_path)
            full = os.path.join(uploads_dir, basename)
            if os.path.exists(full):
                return full

            # Search for files matching the file_type in the uploads directory
            for f in os.listdir(uploads_dir):
                fpath = os.path.join(uploads_dir, f)
                if os.path.isfile(fpath):
                    # Match by partial name (e.g., "policy" in filename)
                    file_type_part = basename.replace(".pdf", "").replace(".jpg", "").replace(".png", "")
                    if file_type_part.lower() in f.lower():
                        return fpath

        return None

    async def _extract_real(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """Extract text from a real file using available tools."""
        ext = os.path.splitext(file_path)[1].lower()
        extracted_text = ""
        pages = 0
        confidence = 0.0

        if ext in (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"):
            # Image file — use Tesseract directly
            extracted_text, confidence = self._ocr_image(file_path)
            pages = 1

        elif ext == ".pdf":
            # PDF — try multiple methods
            extracted_text, pages, confidence = self._extract_pdf(file_path)

        elif ext in (".doc", ".docx"):
            extracted_text = f"[.doc/.docx extraction not yet supported. File: {os.path.basename(file_path)}]"
            confidence = 0.0

        else:
            # Try reading as plain text
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    extracted_text = f.read()
                confidence = 0.7
                pages = 1
            except Exception:
                extracted_text = f"[Unsupported file type: {ext}]"

        # Extract key-value pairs from text
        kvp = self._extract_key_value_pairs(extracted_text)

        return {
            "document_type": file_type.replace("_", " ").title(),
            "pages": pages,
            "confidence": round(confidence, 2),
            "extracted_text": extracted_text[:10000] if extracted_text else "[No text extracted]",
            "key_value_pairs": kvp,
            "ocr_engine": "tesseract" if self.tesseract_available else "text-based",
        }

    def _ocr_image(self, image_path: str) -> tuple[str, float]:
        """Extract text from an image file."""
        if not self.tesseract_available:
            return "[Tesseract OCR is not installed. Install it to extract text from images.]", 0.0

        try:
            img = Image.open(image_path)
            # Get detailed OCR data for confidence
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            text = pytesseract.image_to_string(img)

            # Calculate average confidence
            confidences = [int(c) for c in data["conf"] if int(c) > 0]
            avg_conf = sum(confidences) / len(confidences) / 100.0 if confidences else 0.5

            return text.strip(), avg_conf
        except Exception as e:
            return f"[OCR Error: {str(e)}]", 0.0

    def _extract_pdf(self, pdf_path: str) -> tuple[str, int, float]:
        """Extract text from PDF using best available method."""
        # Method 1: pdfplumber (best for text-based PDFs)
        if HAS_PDFPLUMBER:
            try:
                text_parts = []
                with pdfplumber.open(pdf_path) as pdf:
                    pages = len(pdf.pages)
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)

                if text_parts:
                    full_text = "\n\n".join(text_parts)
                    if len(full_text.strip()) > 50:
                        return full_text, pages, 0.95
            except Exception as e:
                print(f"[OCR] pdfplumber failed: {e}")

        # Method 2: PyPDF2
        if HAS_PYPDF2:
            try:
                text_parts = []
                with open(pdf_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    pages = len(reader.pages)
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)

                if text_parts:
                    full_text = "\n\n".join(text_parts)
                    if len(full_text.strip()) > 50:
                        return full_text, pages, 0.90
            except Exception as e:
                print(f"[OCR] PyPDF2 failed: {e}")

        # Method 3: Tesseract OCR on PDF pages (scanned PDFs)
        if self.tesseract_available and HAS_PDF2IMAGE:
            try:
                images = convert_from_path(pdf_path)
                text_parts = []
                total_conf = 0.0
                for img in images:
                    text = pytesseract.image_to_string(img)
                    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                    confidences = [int(c) for c in data["conf"] if int(c) > 0]
                    avg = sum(confidences) / len(confidences) / 100.0 if confidences else 0.5
                    total_conf += avg
                    text_parts.append(text)

                full_text = "\n\n".join(text_parts)
                avg_conf = total_conf / len(images) if images else 0.0
                return full_text, len(images), avg_conf
            except Exception as e:
                print(f"[OCR] Tesseract PDF failed: {e}")

        return "[Could not extract text from this PDF. Try installing pdfplumber: pip install pdfplumber]", 0, 0.0

    def _is_valid_name(self, value: str) -> bool:
        """Check if a value looks like a real person name (not a sentence fragment)."""
        if not value or len(value) < 3:
            return False
        # Reject if contains common verbs/articles that indicate sentence fragments
        noise_words = [
            "must", "shall", "should", "will", "would", "could", "may", "might",
            "the ", "this ", "that ", "with ", "from ", "have ", "been ", "being",
            "not ", "also", "such", "which", "where", "when", "your", "their",
            "filed", "claim", "denied", "rejected", "approved", "submitted",
            "insurance", "policy", "hospital", "medical", "treatment",
            "amount", "date", "period", "coverage", "under", "above",
        ]
        lower = value.lower()
        for word in noise_words:
            if word in lower:
                return False
        # Must contain at least 2 word-like tokens (first + last name)
        parts = [p for p in value.split() if len(p) >= 2 and p[0].isupper()]
        if len(parts) < 2:
            return False
        # Must be mostly alphabetic
        alpha_ratio = sum(1 for c in value if c.isalpha() or c.isspace()) / max(len(value), 1)
        if alpha_ratio < 0.8:
            return False
        return True

    def _is_valid_insurer(self, value: str) -> bool:
        """Check if a value looks like a real insurance company name."""
        if not value or len(value) < 5:
            return False
        # Reject common sentence fragments
        noise = [
            "must be", "shall be", "should be", "will be", "would be",
            "the policyholder", "the insured", "the patient", "as per",
            "in accordance", "with respect", "subject to", "provided that",
        ]
        lower = value.lower()
        for n in noise:
            if n in lower:
                return False
        # Should contain at least one proper noun or company indicator
        company_indicators = ["insurance", "assurance", "health", "ltd", "limited", "co.", "inc", "pvt", "tpa"]
        has_indicator = any(ind in lower for ind in company_indicators)
        # If no company indicator, at least check it starts with a capital letter
        if not has_indicator and not value[0].isupper():
            return False
        return True

    def _extract_key_value_pairs(self, text: str) -> Dict[str, str]:
        """Try to extract key-value pairs from extracted text with validation."""
        kvp = {}
        if not text or len(text) < 10:
            return kvp

        # Common patterns in insurance/medical documents
        patterns = [
            (r"Policy\s*(?:No|Number|#)\s*[:\-]?\s*([A-Z0-9/\-]+(?:\s*[A-Z0-9/\-]+)*)", "Policy Number"),
            (r"Claim\s*(?:No|Number|#|Ref)\s*[:\-]?\s*([A-Z0-9/\-]+(?:\s*[A-Z0-9/\-]+)*)", "Claim Number"),
            (r"Sum\s*(?:Insured|Assured)\s*[:\-]?\s*(?:Rs\.?\s*|₹\s*)?([\d,]+(?:\.\d+)?)", "Sum Insured"),
            (r"Hospital\s*(?:Name)?\s*[:\-]\s*([^\n]{3,80})", "Hospital"),
            (r"(?:Admission|Admitted)\s*(?:Date)?\s*[:\-]?\s*([\d]{1,2}[\-/][\d]{1,2}[\-/][\d]{2,4})", "Admission Date"),
            (r"(?:Discharge|Discharged)\s*(?:Date)?\s*[:\-]?\s*([\d]{1,2}[\-/][\d]{1,2}[\-/][\d]{2,4})", "Discharge Date"),
            (r"Diagnosis\s*[:\-]?\s*([^\n]{3,120})", "Diagnosis"),
            # Claim/Bill Amount — require numeric value
            (r"(?:Total\s*)?(?:Claim|Bill|Invoice)\s*(?:Amount)?\s*[:\-]?\s*(?:Rs\.?|INR|₹)?\s*([\d,]+(?:\.\d+)?)", "Bill Amount"),
            (r"(?:Amount\s*(?:Claimed|Payable|Submitted))\s*[:\-]?\s*(?:Rs\.?|INR|₹)?\s*([\d,]+(?:\.\d+)?)", "Bill Amount"),
            (r"(?:Claimed\s*Amount)\s*[:\-]?\s*(?:Rs\.?|INR|₹)?\s*([\d,]+(?:\.\d+)?)", "Bill Amount"),
            # Denial reason — look for explicit label
            (r"(?:Denial|Rejection)\s*(?:Reason|Ground)\s*[:\-]\s*([^\n]{10,200})", "Denial Reason"),
            (r"(?:Reason\s*(?:for|of)\s*(?:denial|rejection|decline))\s*[:\-]?\s*([^\n]{10,200})", "Denial Reason"),
            # Insurer: must have explicit label OR contain 'Insurance' as company name
            (r"(?:Insurer|Insurance\s*Company|TPA)\s*[:\-]\s*([^\n]{5,60})", "Insurer"),
            (r"([A-Z][A-Za-z\s]+(?:Insurance|Assurance)\s*(?:Co\.?|Company|Ltd\.?|Limited|Pvt\.?)?)", "Insurer"),
            # Policy Period
            (r"Policy\s*Period\s*[:\-]?\s*([^\n]{5,60})", "Policy Period"),
        ]

        # Case-sensitive patterns (need proper capitalization for name detection)
        case_sensitive_patterns = [
            (r"(?:Patient|Policyholder|Insured)\s*Name\s*[:\-]\s*(?:(?:Mr|Mrs|Ms|Dr|Shri|Smt)\.?[^\S\n]+)?([A-Z][a-z]+(?:[^\S\n]+[A-Z][a-z]+)+)", "Patient Name"),
            (r"(?:Name\s*of\s*(?:the\s*)?(?:Patient|Policyholder|Insured))\s*[:\-]\s*(?:(?:Mr|Mrs|Ms|Dr|Shri|Smt)\.?[^\S\n]+)?([A-Z][a-z]+(?:[^\S\n]+[A-Z][a-z]+)+)", "Patient Name"),
            (r"(?:Mr|Mrs|Ms|Dr|Shri|Smt)\.?[^\S\n]+([A-Z][a-z]+(?:[^\S\n]+[A-Z][a-z]+)+)", "Patient Name"),
        ]

        for pattern, key in case_sensitive_patterns:
            if key in kvp:
                continue
            match = re.search(pattern, text)  # NO IGNORECASE — need proper caps
            if match:
                value = match.group(1).strip()
                if value and 2 <= len(value) <= 200 and self._is_valid_name(value):
                    kvp[key] = value

        for pattern, key in patterns:
            # Don't override already found values
            if key in kvp:
                continue
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if not value or len(value) < 2 or len(value) > 200:
                    continue

                # Apply field-specific validation
                if key == "Patient Name" and not self._is_valid_name(value):
                    continue
                if key == "Insurer" and not self._is_valid_insurer(value):
                    continue
                if key in ("Bill Amount", "Sum Insured"):
                    # Must be a valid number
                    cleaned = re.sub(r"[,\s]", "", value)
                    try:
                        float(cleaned)
                    except ValueError:
                        continue

                kvp[key] = value

        return kvp


ocr_agent = OCRAgent()
