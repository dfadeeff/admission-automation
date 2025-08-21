"""
LangGraph workflow orchestrating the admission agents
"""
import logging
from typing import Dict, Any, TypedDict, List, Optional
from langgraph.graph import StateGraph, END
from .state import ApplicationState, DocumentFile, ClassifiedDocument, ExtractedData, AdmissionDecision
from .document_classifier import DocumentClassifierAgent
from .data_extractor import DataExtractionAgent
from .admission_agent import AdmissionDecisionAgent
from datetime import datetime

logger = logging.getLogger(__name__)

# TypedDict for LangGraph state
class WorkflowState(TypedDict):
    """State that flows through LangGraph"""
    application_id: str
    applicant_id: str
    target_program: str
    entity: str
    uploaded_files: List[DocumentFile]
    classified_documents: List[ClassifiedDocument]
    extracted_data: List[ExtractedData]
    admission_decision: Optional[AdmissionDecision]
    current_stage: str
    error_message: Optional[str]
    agent_logs: List[Dict[str, Any]]
    created_at: datetime

class AdmissionWorkflow:
    """
    LangGraph workflow that orchestrates the admission process
    """
    
    def __init__(self):
        self.document_classifier = DocumentClassifierAgent()
        self.data_extractor = DataExtractionAgent()
        self.admission_agent = AdmissionDecisionAgent()
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """
        Build the LangGraph workflow
        """
        workflow = StateGraph(WorkflowState)
        
        # Add nodes (agents)
        workflow.add_node("classify_documents", self._classify_documents_node)
        workflow.add_node("extract_data", self._extract_data_node)
        workflow.add_node("make_decision", self._make_decision_node)
        workflow.add_node("handle_error", self._handle_error_node)
        
        # Define the flow
        workflow.set_entry_point("classify_documents")
        
        # From classify_documents
        workflow.add_conditional_edges(
            "classify_documents",
            self._should_continue_after_classification,
            {
                "continue": "extract_data",
                "error": "handle_error"
            }
        )
        
        # From extract_data
        workflow.add_conditional_edges(
            "extract_data", 
            self._should_continue_after_extraction,
            {
                "continue": "make_decision",
                "error": "handle_error"
            }
        )
        
        # From make_decision
        workflow.add_edge("make_decision", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    def process_application(self, state: ApplicationState) -> ApplicationState:
        """
        Main entry point - process an application through the workflow
        """
        logger.info(f"Starting workflow for application {state.application_id}")
        
        try:
            # Convert ApplicationState to dict for LangGraph
            state_dict = {
                "application_id": state.application_id,
                "applicant_id": state.applicant_id,
                "target_program": state.target_program,
                "entity": state.entity,
                "uploaded_files": state.uploaded_files,
                "classified_documents": state.classified_documents,
                "extracted_data": state.extracted_data,
                "admission_decision": state.admission_decision,
                "current_stage": state.current_stage,
                "error_message": state.error_message,
                "agent_logs": state.agent_logs,
                "created_at": state.created_at
            }
            
            # Run the workflow
            result = self.workflow.invoke(state_dict)
            
            # Convert back to ApplicationState
            result_state = ApplicationState(
                application_id=result["application_id"],
                applicant_id=result["applicant_id"],
                target_program=result["target_program"],
                entity=result["entity"],
                uploaded_files=result["uploaded_files"],
                classified_documents=result.get("classified_documents", []),
                extracted_data=result.get("extracted_data", []),
                admission_decision=result.get("admission_decision"),
                current_stage=result.get("current_stage", "completed"),
                error_message=result.get("error_message"),
                agent_logs=result.get("agent_logs", []),
                created_at=result["created_at"]
            )
            
            logger.info(f"Workflow completed for application {state.application_id}")
            return result_state
            
        except Exception as e:
            logger.error(f"Workflow failed for application {state.application_id}: {e}")
            state.error_message = str(e)
            state.current_stage = "workflow_error"
            return state
    
    # Node implementations - now work with dicts
    def _classify_documents_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Node for document classification"""
        # Convert dict to ApplicationState
        app_state = ApplicationState(
            application_id=state["application_id"],
            applicant_id=state["applicant_id"],
            target_program=state["target_program"],
            entity=state["entity"],
            uploaded_files=state["uploaded_files"],
            classified_documents=state.get("classified_documents", []),
            extracted_data=state.get("extracted_data", []),
            admission_decision=state.get("admission_decision"),
            current_stage=state.get("current_stage", "classifying"),
            error_message=state.get("error_message"),
            agent_logs=state.get("agent_logs", []),
            created_at=state["created_at"]
        )
        
        # Process
        result = self.document_classifier.process(app_state)
        
        # Convert back to dict
        state["classified_documents"] = result.classified_documents
        state["current_stage"] = result.current_stage
        state["error_message"] = result.error_message
        state["agent_logs"] = result.agent_logs
        return state
    
    def _extract_data_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Node for data extraction"""
        # Convert dict to ApplicationState
        app_state = ApplicationState(
            application_id=state["application_id"],
            applicant_id=state["applicant_id"],
            target_program=state["target_program"],
            entity=state["entity"],
            uploaded_files=state["uploaded_files"],
            classified_documents=state.get("classified_documents", []),
            extracted_data=state.get("extracted_data", []),
            admission_decision=state.get("admission_decision"),
            current_stage=state.get("current_stage", "extracting"),
            error_message=state.get("error_message"),
            agent_logs=state.get("agent_logs", []),
            created_at=state["created_at"]
        )
        
        # Process
        result = self.data_extractor.process(app_state)
        
        # Convert back to dict
        state["extracted_data"] = result.extracted_data
        state["current_stage"] = result.current_stage
        state["error_message"] = result.error_message
        state["agent_logs"] = result.agent_logs
        return state
    
    def _make_decision_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Node for admission decision"""
        # Convert dict to ApplicationState
        app_state = ApplicationState(
            application_id=state["application_id"],
            applicant_id=state["applicant_id"],
            target_program=state["target_program"],
            entity=state["entity"],
            uploaded_files=state["uploaded_files"],
            classified_documents=state.get("classified_documents", []),
            extracted_data=state.get("extracted_data", []),
            admission_decision=state.get("admission_decision"),
            current_stage=state.get("current_stage", "deciding"),
            error_message=state.get("error_message"),
            agent_logs=state.get("agent_logs", []),
            created_at=state["created_at"]
        )
        
        # Process
        result = self.admission_agent.process(app_state)
        
        # Convert back to dict
        state["admission_decision"] = result.admission_decision
        state["current_stage"] = result.current_stage
        state["error_message"] = result.error_message
        state["agent_logs"] = result.agent_logs
        return state
    
    def _handle_error_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Node for error handling"""
        logger.error(f"Error in workflow: {state.get('error_message')}")
        state["current_stage"] = "error_handled"
        
        # Add error log
        if "agent_logs" not in state:
            state["agent_logs"] = []
        state["agent_logs"].append({
            "timestamp": datetime.now(),
            "agent": "Workflow",
            "action": "handle_error",
            "details": {"error": state.get("error_message")}
        })
        
        return state
    
    # Conditional edge functions - now work with dicts
    def _should_continue_after_classification(self, state: Dict[str, Any]) -> str:
        """Decide whether to continue after document classification"""
        if state.get("error_message"):
            return "error"
        
        if not state.get("classified_documents"):
            state["error_message"] = "No documents were successfully classified"
            return "error"
        
        # Check if we have at least some confidently classified documents
        confident_docs = [
            doc for doc in state.get("classified_documents", [])
            if doc.confidence > 0.5
        ]
        
        if not confident_docs:
            state["error_message"] = "No documents classified with sufficient confidence"
            return "error"
        
        return "continue"
    
    def _should_continue_after_extraction(self, state: Dict[str, Any]) -> str:
        """Decide whether to continue after data extraction"""
        if state.get("error_message"):
            return "error"
        
        if not state.get("extracted_data"):
            state["error_message"] = "No data was successfully extracted"
            return "error"
        
        # Check if we have at least some data with reasonable confidence
        # Lower threshold since we're extracting from real documents
        confident_extractions = [
            extraction for extraction in state.get("extracted_data", [])
            if extraction.confidence > 0.1  # Lowered from 0.3
        ]
        
        if not confident_extractions:
            state["error_message"] = "No data extracted with sufficient confidence"
            return "error"
        
        return "continue"

# Convenience function to create and run workflow
def process_admission_application(
    application_id: str,
    applicant_id: str, 
    target_program: str,
    entity: str,
    uploaded_files: list
) -> ApplicationState:
    """
    Convenience function to process an admission application
    """
    # Create initial state
    state = ApplicationState(
        application_id=application_id,
        applicant_id=applicant_id,
        target_program=target_program,
        entity=entity,
        uploaded_files=uploaded_files
    )
    
    # Create and run workflow
    workflow = AdmissionWorkflow()
    result = workflow.process_application(state)
    
    return result