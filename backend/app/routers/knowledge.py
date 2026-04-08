"""
Knowledge graph router
"""

from fastapi import APIRouter
from typing import Optional

router = APIRouter()


@router.get("/graph")
async def get_knowledge_graph():
    """Get the insurance knowledge graph data"""
    nodes = [
        # Policy Clauses
        {"id": "pc1", "label": "Pre-existing Disease Exclusion", "type": "policy_clause", "group": "policy",
         "description": "Section 5.1: PED excluded for first 48 months of continuous coverage"},
        {"id": "pc2", "label": "In-Patient Coverage", "type": "policy_clause", "group": "policy",
         "description": "Section 4.1: Covers hospitalization exceeding 24 hours"},
        {"id": "pc3", "label": "Waiting Period", "type": "policy_clause", "group": "policy",
         "description": "Section 5.2: Specific diseases have 2-4 year waiting periods"},
        {"id": "pc4", "label": "Cashless Claim Process", "type": "policy_clause", "group": "policy",
         "description": "Section 8.1: Cashless through network hospitals only"},
        {"id": "pc5", "label": "Sum Insured Limit", "type": "policy_clause", "group": "policy",
         "description": "Section 3.1: Maximum coverage amount per policy year"},

        # Medical Conditions
        {"id": "mc1", "label": "Coronary Artery Disease", "type": "medical_condition", "group": "medical",
         "description": "Triple vessel CAD requiring surgical intervention"},
        {"id": "mc2", "label": "Hypertension", "type": "medical_condition", "group": "medical",
         "description": "Pre-existing chronic condition, commonly cited in denials"},
        {"id": "mc3", "label": "Diabetes Mellitus", "type": "medical_condition", "group": "medical",
         "description": "Type 2 diabetes, common comorbidity"},
        {"id": "mc4", "label": "Chronic Kidney Disease", "type": "medical_condition", "group": "medical",
         "description": "Progressive kidney condition"},

        # Procedures
        {"id": "pr1", "label": "CABG Surgery", "type": "procedure", "group": "procedure",
         "description": "Coronary Artery Bypass Graft - standard treatment for multi-vessel CAD"},
        {"id": "pr2", "label": "Angioplasty", "type": "procedure", "group": "procedure",
         "description": "Percutaneous Coronary Intervention for single/dual vessel disease"},
        {"id": "pr3", "label": "Dialysis", "type": "procedure", "group": "procedure",
         "description": "Renal replacement therapy for CKD"},

        # Regulations
        {"id": "rg1", "label": "IRDAI PED Circular 2013", "type": "regulation", "group": "regulation",
         "description": "Pre-existing disease exclusion limits and guidelines"},
        {"id": "rg2", "label": "IRDAI Master Circular 2020", "type": "regulation", "group": "regulation",
         "description": "Comprehensive health insurance claim processing standards"},
        {"id": "rg3", "label": "Insurance Ombudsman Rules 2017", "type": "regulation", "group": "regulation",
         "description": "Policyholder grievance redressal mechanism"},
        {"id": "rg4", "label": "ABPMJAY Guidelines", "type": "regulation", "group": "regulation",
         "description": "Ayushman Bharat PM-JAY scheme treatment package rates"},
        {"id": "rg5", "label": "ABDM/ABHA Standards", "type": "regulation", "group": "regulation",
         "description": "National digital health ecosystem data standards"},

        # Exclusions
        {"id": "ex1", "label": "Cosmetic Treatment", "type": "exclusion", "group": "exclusion",
         "description": "Cosmetic/aesthetic procedures unless post-accident"},
        {"id": "ex2", "label": "Self-Inflicted Injury", "type": "exclusion", "group": "exclusion",
         "description": "Injuries resulting from self-harm"},
        {"id": "ex3", "label": "Hazardous Activities", "type": "exclusion", "group": "exclusion",
         "description": "Treatment from participation in adventure/extreme sports"},
    ]

    edges = [
        # Policy-Medical relationships
        {"source": "pc1", "target": "mc2", "label": "applies_to", "type": "restriction"},
        {"source": "pc1", "target": "mc3", "label": "applies_to", "type": "restriction"},
        {"source": "pc2", "target": "pr1", "label": "covers", "type": "coverage"},
        {"source": "pc2", "target": "pr2", "label": "covers", "type": "coverage"},
        {"source": "pc3", "target": "mc1", "label": "waiting_period_for", "type": "restriction"},

        # Medical condition-Procedure relationships
        {"source": "mc1", "target": "pr1", "label": "treated_by", "type": "treatment"},
        {"source": "mc1", "target": "pr2", "label": "treated_by", "type": "treatment"},
        {"source": "mc4", "target": "pr3", "label": "treated_by", "type": "treatment"},
        {"source": "mc2", "target": "mc1", "label": "risk_factor_for", "type": "medical"},

        # Regulation relationships
        {"source": "rg1", "target": "pc1", "label": "regulates", "type": "regulation"},
        {"source": "rg2", "target": "pc2", "label": "regulates", "type": "regulation"},
        {"source": "rg2", "target": "pc4", "label": "regulates", "type": "regulation"},
        {"source": "rg3", "target": "pc1", "label": "appeal_mechanism", "type": "regulation"},
        {"source": "rg4", "target": "pr1", "label": "package_rate", "type": "regulation"},
        {"source": "rg4", "target": "pr2", "label": "package_rate", "type": "regulation"},

        # Exclusion relationships
        {"source": "pc5", "target": "ex1", "label": "excludes", "type": "exclusion"},
        {"source": "pc5", "target": "ex2", "label": "excludes", "type": "exclusion"},
        {"source": "pc5", "target": "ex3", "label": "excludes", "type": "exclusion"},
    ]

    return {
        "nodes": nodes,
        "edges": edges,
        "total_nodes": len(nodes),
        "total_edges": len(edges),
    }


@router.get("/search")
async def search_knowledge(q: Optional[str] = ""):
    """Search the knowledge graph"""
    all_nodes = [
        {"id": "pc1", "label": "Pre-existing Disease Exclusion", "type": "policy_clause",
         "description": "PED excluded for first 48 months of continuous coverage"},
        {"id": "mc1", "label": "Coronary Artery Disease", "type": "medical_condition",
         "description": "Triple vessel CAD requiring surgical intervention"},
        {"id": "pr1", "label": "CABG Surgery", "type": "procedure",
         "description": "Coronary Artery Bypass Graft for multi-vessel CAD"},
        {"id": "rg1", "label": "IRDAI PED Circular 2013", "type": "regulation",
         "description": "Pre-existing disease exclusion limits"},
    ]

    if q:
        results = [n for n in all_nodes if q.lower() in n["label"].lower() or q.lower() in n["description"].lower()]
    else:
        results = all_nodes

    return {
        "query": q,
        "results": results,
        "total": len(results),
    }
