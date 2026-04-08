"""
Professional PDF generation service for appeal letters.
Uses reportlab to produce clean, legal-quality PDFs.
"""

import io
import re
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT


# ─── Brand Colors ──────────────────────────────────────────
BRAND_PRIMARY = HexColor("#5A67D8")
BRAND_DARK = HexColor("#1A1A2E")
GRAY_700 = HexColor("#374151")
GRAY_500 = HexColor("#6B7280")
GRAY_300 = HexColor("#D1D5DB")
WHITE = HexColor("#FFFFFF")
LIGHT_BG = HexColor("#F7F8FC")


def _build_styles():
    """Create professional paragraph styles."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        "AppealTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=22,
        textColor=BRAND_DARK,
        alignment=TA_CENTER,
        spaceAfter=4,
    ))

    styles.add(ParagraphStyle(
        "AppealSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=GRAY_500,
        alignment=TA_CENTER,
        spaceAfter=16,
    ))

    styles.add(ParagraphStyle(
        "SectionHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=16,
        textColor=BRAND_PRIMARY,
        spaceBefore=14,
        spaceAfter=6,
    ))

    styles.add(ParagraphStyle(
        "AppealBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=16,
        textColor=GRAY_700,
        alignment=TA_JUSTIFY,
        spaceAfter=4,
    ))

    styles.add(ParagraphStyle(
        "BodyBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=16,
        textColor=GRAY_700,
        alignment=TA_JUSTIFY,
        spaceAfter=4,
    ))

    styles.add(ParagraphStyle(
        "BulletItem",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=15,
        textColor=GRAY_700,
        leftIndent=20,
        spaceAfter=3,
        bulletIndent=8,
    ))

    styles.add(ParagraphStyle(
        "SmallGray",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=GRAY_500,
        alignment=TA_CENTER,
    ))

    styles.add(ParagraphStyle(
        "MetaLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=13,
        textColor=GRAY_500,
    ))

    styles.add(ParagraphStyle(
        "MetaValue",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=BRAND_DARK,
    ))

    styles.add(ParagraphStyle(
        "RegulationItem",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=13,
        textColor=GRAY_700,
        leftIndent=16,
        spaceAfter=3,
    ))

    return styles


def _escape_xml(text: str) -> str:
    """Escape XML special characters for reportlab Paragraph."""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text


def generate_appeal_pdf(
    appeal_text: str,
    patient_name: str = "",
    insurer_name: str = "",
    claim_amount: float = 0,
    denial_reason: str = "",
    appeal_strength: str = "moderate",
    confidence_score: float = 0,
    regulations_cited: list = None,
    word_count: int = 0,
) -> bytes:
    """
    Generate a professional PDF from an appeal letter.
    Returns raw PDF bytes.
    """
    buffer = io.BytesIO()
    styles = _build_styles()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=30 * mm,
        bottomMargin=25 * mm,
        leftMargin=25 * mm,
        rightMargin=25 * mm,
        title=f"Appeal Letter - {patient_name}",
        author="ClaimAssist AI",
    )

    elements = []

    # ═══════════════════════════════════════════════════════
    #  HEADER / LETTERHEAD
    # ═══════════════════════════════════════════════════════
    elements.append(Paragraph("ClaimAssist AI", styles["AppealTitle"]))
    elements.append(Paragraph(
        "AI-Powered Health Insurance Claim Appeal Platform",
        styles["AppealSubtitle"],
    ))

    # Divider
    elements.append(HRFlowable(
        width="100%", thickness=2, color=BRAND_PRIMARY,
        spaceAfter=12, spaceBefore=4,
    ))

    # ═══════════════════════════════════════════════════════
    #  CLAIM SUMMARY TABLE
    # ═══════════════════════════════════════════════════════
    date_str = datetime.now().strftime("%B %d, %Y")
    amount_str = f"₹{claim_amount:,.0f}" if claim_amount else "N/A"
    strength_display = (appeal_strength or "moderate").upper()

    meta_data = [
        [
            Paragraph("Patient Name", styles["MetaLabel"]),
            Paragraph(_escape_xml(patient_name or "N/A"), styles["MetaValue"]),
            Paragraph("Generated On", styles["MetaLabel"]),
            Paragraph(date_str, styles["MetaValue"]),
        ],
        [
            Paragraph("Insurer", styles["MetaLabel"]),
            Paragraph(_escape_xml(insurer_name or "N/A"), styles["MetaValue"]),
            Paragraph("Claim Amount", styles["MetaLabel"]),
            Paragraph(amount_str, styles["MetaValue"]),
        ],
        [
            Paragraph("Denial Reason", styles["MetaLabel"]),
            Paragraph(_escape_xml(denial_reason or "N/A"), styles["MetaValue"]),
            Paragraph("Appeal Strength", styles["MetaLabel"]),
            Paragraph(strength_display, styles["MetaValue"]),
        ],
    ]

    col_widths = [90, 155, 90, 155]
    meta_table = Table(meta_data, colWidths=col_widths)
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, GRAY_300),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, GRAY_300),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 16))

    # ═══════════════════════════════════════════════════════
    #  APPEAL LETTER BODY
    # ═══════════════════════════════════════════════════════
    elements.append(Paragraph("APPEAL LETTER", styles["SectionHeading"]))
    elements.append(HRFlowable(
        width="100%", thickness=0.5, color=GRAY_300,
        spaceAfter=8, spaceBefore=2,
    ))

    # Parse the appeal text into paragraphs and bullet points
    if appeal_text:
        lines = appeal_text.split("\n")
        for line in lines:
            stripped = line.strip()
            if not stripped:
                elements.append(Spacer(1, 6))
                continue

            # Section headings (numbered sections like "1. ANALYSIS" or ALL-CAPS lines)
            if re.match(r"^\d+\.\s+[A-Z]", stripped) or (
                stripped.isupper() and len(stripped) > 5 and len(stripped) < 80
            ):
                elements.append(Spacer(1, 8))
                elements.append(Paragraph(
                    _escape_xml(stripped),
                    styles["SectionHeading"],
                ))
                continue

            # Bullet points
            if stripped.startswith("•") or stripped.startswith("-"):
                bullet_text = stripped.lstrip("•- ").strip()
                elements.append(Paragraph(
                    f"&bull;  {_escape_xml(bullet_text)}",
                    styles["BulletItem"],
                ))
                continue

            # "To," or "From," or "Subject:" or "Date:" lines
            if any(stripped.startswith(prefix) for prefix in [
                "To,", "From,", "Subject:", "Date:", "Ref:", "Patient Name:",
                "Denial Reason:", "Respected", "Yours faithfully",
                "Enclosures:", "Policy Holder",
            ]):
                elements.append(Paragraph(
                    _escape_xml(stripped),
                    styles["BodyBold"],
                ))
                continue

            # Enclosure list items (numbered)
            if re.match(r"^\d+\.\s+", stripped) and len(stripped) < 120:
                elements.append(Paragraph(
                    f"&bull;  {_escape_xml(stripped.split('. ', 1)[-1])}",
                    styles["BulletItem"],
                ))
                continue

            # Regular paragraph text
            elements.append(Paragraph(
                _escape_xml(stripped),
                styles["AppealBody"],
            ))

    # ═══════════════════════════════════════════════════════
    #  REGULATIONS CITED
    # ═══════════════════════════════════════════════════════
    if regulations_cited:
        elements.append(Spacer(1, 16))
        elements.append(HRFlowable(
            width="100%", thickness=0.5, color=GRAY_300,
            spaceAfter=8, spaceBefore=4,
        ))
        elements.append(Paragraph(
            f"REGULATIONS &amp; GUIDELINES CITED ({len(regulations_cited)})",
            styles["SectionHeading"],
        ))
        for reg in regulations_cited:
            elements.append(Paragraph(
                f"&bull;  {_escape_xml(str(reg))}",
                styles["RegulationItem"],
            ))

    # ═══════════════════════════════════════════════════════
    #  FOOTER
    # ═══════════════════════════════════════════════════════
    elements.append(Spacer(1, 30))
    elements.append(HRFlowable(
        width="100%", thickness=1, color=BRAND_PRIMARY,
        spaceAfter=8, spaceBefore=4,
    ))
    elements.append(Paragraph(
        f"Generated by ClaimAssist AI &bull; {date_str} &bull; "
        f"Confidence: {confidence_score:.0f}% &bull; {word_count} words",
        styles["SmallGray"],
    ))
    elements.append(Paragraph(
        "This document was generated by AI. Please review for accuracy before submission.",
        styles["SmallGray"],
    ))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
