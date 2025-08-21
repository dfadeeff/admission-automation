"""
IU Admissions RAG System
Query system for the 245-page admission handbook
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import uuid
from datetime import datetime
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="../.env")

# Import RAG system and agents
from rag.retriever import AdmissionRulesRetriever
from agents.workflow import process_admission_application
from agents.state import ApplicationState, DocumentFile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="IU Admissions RAG System",
    version="1.0.0",
    description="RAG system for querying 245-page admission handbook"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

# Initialize RAG system
rag_system = AdmissionRulesRetriever()

# In-memory storage for demo (use database in production)
APPLICATIONS: Dict[str, ApplicationState] = {}

# Request/Response models
class RuleQueryRequest(BaseModel):
    question: str

class InitializeRequest(BaseModel):
    force_reload: bool = False

class ApplicationResponse(BaseModel):
    application_id: str
    status: str
    message: str

class ApplicationStatusResponse(BaseModel):
    application_id: str
    current_stage: str
    decision: Optional[Dict[str, Any]] = None
    logs: List[Dict[str, Any]] = []

# Core endpoints
@app.get("/")
def root():
    return {
        "service": "IU Admissions RAG System",
        "status": "ready",
        "handbook": "data/Leitfaden.pdf (245 pages)",
        "features": [
            "RAG handbook queries",
            "Free local embeddings (Sentence Transformers)",
            "Anthropic Claude for intelligent responses",
            "Vector search with ChromaDB"
        ]
    }

@app.post("/initialize-rag")
async def initialize_rag(request: InitializeRequest):
    """Initialize the RAG system with the 245-page handbook"""
    try:
        logger.info("Initializing RAG system...")
        rag_system.initialize(force_reload=request.force_reload)
        return {
            "status": "success",
            "message": "RAG system initialized with 245-page handbook",
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Failed to initialize RAG: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query-handbook")
async def query_handbook(request: RuleQueryRequest):
    """Query the admission handbook directly"""
    try:
        logger.info(f"Processing query: {request.question[:100]}...")
        result = rag_system.query_admission_rules(request.question)
        return result
    except Exception as e:
        logger.error(f"Handbook query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/handbook-status")
async def handbook_status():
    """Get status of the handbook processing"""
    handbook_path = "../data/Leitfaden.pdf"
    
    if not os.path.exists(handbook_path):
        return {
            "status": "error",
            "message": f"Handbook not found at {handbook_path}"
        }
    
    try:
        if rag_system.vector_store.vector_store is None:
            return {
                "status": "not_initialized",
                "message": "RAG system not initialized. Call /initialize-rag first"
            }
        
        return {
            "status": "ready",
            "handbook_path": handbook_path,
            "message": "RAG system ready for queries"
        }
    except:
        return {
            "status": "not_initialized",
            "message": "RAG system not initialized. Call /initialize-rag first"
        }

@app.post("/submit-application", response_model=ApplicationResponse)
async def submit_application(
    applicant_id: str = Form(...),
    target_program: str = Form(...),
    entity: str = Form("DE"),
    files: List[UploadFile] = File(...)
):
    """
    Submit a complete application with documents for agent processing
    This will use the full agent workflow: classify docs -> extract data -> check rules -> make decision
    """
    application_id = f"APP-{uuid.uuid4().hex[:8].upper()}"
    
    try:
        # Save uploaded files
        uploaded_files = []
        upload_dir = f"./uploads/{application_id}"
        os.makedirs(upload_dir, exist_ok=True)
        
        for file in files:
            file_path = os.path.join(upload_dir, file.filename)
            
            # Save file
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            # Create DocumentFile object
            doc_file = DocumentFile(
                file_id=f"DOC-{uuid.uuid4().hex[:6]}",
                filename=file.filename,
                file_type=file.content_type,
                file_path=file_path,
                size_bytes=len(content)
            )
            uploaded_files.append(doc_file)
        
        logger.info(f"Processing application {application_id} with {len(uploaded_files)} files")
        
        # Process through agent workflow (connected to your RAG system!)
        result_state = process_admission_application(
            application_id=application_id,
            applicant_id=applicant_id,
            target_program=target_program,
            entity=entity,
            uploaded_files=uploaded_files
        )
        
        # Store result
        APPLICATIONS[application_id] = result_state
        
        logger.info(f"Application {application_id} processed: {result_state.current_stage}")
        
        return ApplicationResponse(
            application_id=application_id,
            status=result_state.current_stage,
            message=f"Application processed through agent workflow. Decision: {result_state.admission_decision.status if result_state.admission_decision else 'Pending'}"
        )
        
    except Exception as e:
        logger.error(f"Application submission failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/application/{application_id}", response_model=ApplicationStatusResponse)
async def get_application_status(application_id: str):
    """Get detailed application status and agent decision"""
    
    if application_id not in APPLICATIONS:
        raise HTTPException(status_code=404, detail="Application not found")
    
    state = APPLICATIONS[application_id]
    
    # Prepare decision data
    decision_data = None
    if state.admission_decision:
        decision_data = {
            "status": state.admission_decision.status,
            "confidence": state.admission_decision.confidence,
            "reasoning": state.admission_decision.reasoning,
            "applied_rules": state.admission_decision.applied_rules,
            "missing_documents": state.admission_decision.missing_documents,
            "handbook_citations": state.admission_decision.handbook_citations
        }
    
    return ApplicationStatusResponse(
        application_id=application_id,
        current_stage=state.current_stage,
        decision=decision_data,
        logs=state.agent_logs
    )

@app.get("/applications")
async def list_applications():
    """List all processed applications"""
    summaries = []
    for app_id, state in APPLICATIONS.items():
        summary = {
            "application_id": app_id,
            "applicant_id": state.applicant_id,
            "target_program": state.target_program,
            "entity": state.entity,
            "current_stage": state.current_stage,
            "created_at": state.created_at,
            "num_documents": len(state.uploaded_files),
            "decision_status": state.admission_decision.status if state.admission_decision else None
        }
        summaries.append(summary)
    
    return {"applications": summaries, "total": len(summaries)}

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.now()}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting IU Admissions RAG System")
    print("📚 This will process your 245-page handbook with FREE embeddings")
    print("🤖 Uses Anthropic Claude for intelligent rule interpretation")
    print()
    print("Next steps after server starts:")
    print("1. POST /initialize-rag  (processes 245 pages - takes 3-4 min)")
    print("2. POST /query-handbook  (ask questions about admission rules)")
    print()
    uvicorn.run(app, host="0.0.0.0", port=8000)