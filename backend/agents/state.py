"""
State management for the admissions agent workflow
"""
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel
from datetime import datetime

class DocumentFile(BaseModel):
    file_id: str
    filename: str
    file_type: str  # pdf, jpg, png
    file_path: str
    size_bytes: int

class ClassifiedDocument(BaseModel):
    file: DocumentFile
    document_type: str  # transcript, a_levels, abitur, ib, passport, cv, work_certificate
    confidence: float
    
class ExtractedData(BaseModel):
    document_type: str
    data: Dict[str, Any]
    confidence: float
    source_file: str

class AdmissionDecision(BaseModel):
    status: Literal["APPROVED", "REJECTED", "REVIEW_REQUIRED", "MISSING_DOCS"]
    confidence: float
    reasoning: str
    applied_rules: List[Dict[str, Any]]
    missing_documents: List[str] = []
    handbook_citations: List[str] = []
    
class ApplicationState(BaseModel):
    """
    State object that flows through the agent pipeline
    """
    # Input
    application_id: str
    applicant_id: str
    target_program: str
    entity: str = "DE"
    uploaded_files: List[DocumentFile] = []
    
    # Processing stages
    classified_documents: List[ClassifiedDocument] = []
    extracted_data: List[ExtractedData] = []
    admission_decision: Optional[AdmissionDecision] = None
    
    # Metadata
    created_at: datetime = datetime.now()
    current_stage: str = "created"
    error_message: Optional[str] = None
    
    # Agent outputs
    agent_logs: List[Dict[str, Any]] = []
    
    def add_log(self, agent: str, action: str, details: Dict[str, Any]):
        """Add log entry for agent action"""
        self.agent_logs.append({
            "timestamp": datetime.now(),
            "agent": agent,
            "action": action,
            "details": details
        })