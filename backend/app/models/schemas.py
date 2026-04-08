"""
Pydantic schemas for request/response models
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# Document schemas
class DocumentUploadResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size: int
    upload_date: datetime
    status: str

    class Config:
        from_attributes = True


class DocumentDetail(DocumentUploadResponse):
    extracted_text: str = ""
    metadata_json: dict = {}


# Claim Analysis schemas
class ClaimAnalysisRequest(BaseModel):
    patient_name: str = Field(..., description="Patient's full name")
    insurer_name: str = Field(..., description="Insurance company name")
    claim_amount: float = Field(..., description="Claim amount in INR")
    denial_reason: str = Field(..., description="Reason for claim denial")
    policy_document_id: Optional[int] = Field(None, description="ID of uploaded policy document")
    medical_report_id: Optional[int] = Field(None, description="ID of uploaded medical report")
    denial_letter_id: Optional[int] = Field(None, description="ID of uploaded denial letter")


class Discrepancy(BaseModel):
    type: str  # policy_violation, medical_necessity, documentation_gap, regulation_breach
    severity: str  # low, medium, high, critical
    description: str
    policy_clause: Optional[str] = None
    supporting_evidence: Optional[str] = None
    regulation_reference: Optional[str] = None


class ClaimAnalysisResponse(BaseModel):
    id: int
    claim_id: str
    patient_name: str
    insurer_name: str
    claim_amount: float
    denial_reason: str
    analysis_date: datetime
    status: str
    discrepancies: List[Discrepancy] = []
    policy_alignment_score: float = 0.0
    medical_necessity_score: float = 0.0
    appeal_strength: str = "unknown"
    pipeline_results: dict = {}

    class Config:
        from_attributes = True


# Appeal Letter schemas
class AppealGenerateRequest(BaseModel):
    claim_id: str = Field(..., description="Claim analysis ID")
    tone: str = Field(default="formal", description="Letter tone: formal, assertive, empathetic")
    include_regulations: bool = Field(default=True, description="Include regulatory references")
    include_medical_evidence: bool = Field(default=True, description="Include medical evidence citations")


class Citation(BaseModel):
    source: str
    text: str
    page: Optional[int] = None
    relevance_score: float = 0.0


class AppealLetterResponse(BaseModel):
    id: int
    claim_id: str
    appeal_text: str
    citations: List[Citation] = []
    regulations_cited: List[str] = []
    generated_date: datetime
    status: str
    confidence_score: float = 0.0

    class Config:
        from_attributes = True


# Knowledge Graph schemas
class KnowledgeNode(BaseModel):
    id: str
    label: str
    type: str  # policy_clause, medical_condition, procedure, regulation, exclusion
    description: str
    connections: List[str] = []


class KnowledgeGraphResponse(BaseModel):
    nodes: List[KnowledgeNode]
    edges: List[dict]
    total_nodes: int
    total_edges: int


class KnowledgeSearchResult(BaseModel):
    query: str
    results: List[KnowledgeNode]
    total: int


# Chat schemas
class ChatMessage(BaseModel):
    message: str
    sender: str = "user"  # user, ai


class ChatResponse(BaseModel):
    response: str
    type: str = "info"  # greeting, info, action, regulation, error


# Dashboard schemas
class DashboardStats(BaseModel):
    claims_analyzed: int
    appeals_generated: int
    success_rate: float
    active_cases: int
    total_documents: int
    avg_processing_time: str
