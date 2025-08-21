"""
Admission Decision Agent
Makes admission decisions based on extracted data and handbook rules
"""
import logging
import os
from typing import List, Dict, Any, Optional
import anthropic
from .state import ApplicationState, AdmissionDecision, ExtractedData
from rag.retriever import AdmissionRulesRetriever
import json

logger = logging.getLogger(__name__)

class AdmissionDecisionAgent:
    """
    Agent that makes admission decisions using RAG + business rules
    """
    
    def __init__(self):
        # Get API key from environment
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
            
        self.client = anthropic.Anthropic(api_key=anthropic_key)
        self.model = "claude-3-5-sonnet-20241022"
        
        # Initialize RAG system for handbook queries
        self.rag_retriever = AdmissionRulesRetriever()
        
        # Required documents by entity
        self.required_docs = {
            "DE": ["transcript", "abitur"],  # German entity
            "UK": ["transcript", "a_levels"],  # UK entity  
            "CA": ["transcript"]  # Canadian entity
        }
    
    def process(self, state: ApplicationState) -> ApplicationState:
        """
        Make admission decision based on extracted data
        """
        logger.info(f"Making admission decision for application {state.application_id}")
        
        state.current_stage = "making_decision"
        
        try:
            # Check document completeness first
            missing_docs = self._check_document_completeness(state)
            
            if missing_docs:
                decision = AdmissionDecision(
                    status="MISSING_DOCS",
                    confidence=1.0,
                    reasoning=f"Missing required documents: {', '.join(missing_docs)}",
                    applied_rules=[],
                    missing_documents=missing_docs
                )
            else:
                # Make admission decision using RAG + rules
                decision = self._evaluate_admission(state)
            
            state.admission_decision = decision
            state.current_stage = "decision_made"
            
            state.add_log(
                agent="AdmissionDecision",
                action="make_decision",
                details={
                    "status": decision.status,
                    "confidence": decision.confidence,
                    "rules_applied": len(decision.applied_rules)
                }
            )
            
            logger.info(f"Decision made: {decision.status} (confidence: {decision.confidence})")
            
        except Exception as e:
            logger.error(f"Decision making failed: {e}")
            state.error_message = str(e)
            state.current_stage = "error"
            
            state.add_log(
                agent="AdmissionDecision",
                action="decision_error",
                details={"error": str(e)}
            )
        
        return state
    
    def _check_document_completeness(self, state: ApplicationState) -> List[str]:
        """
        Check if all required documents are present and classified
        """
        required = self.required_docs.get(state.entity, [])
        provided_types = [doc.document_type for doc in state.classified_documents]
        
        missing = []
        for doc_type in required:
            if doc_type not in provided_types:
                missing.append(doc_type)
        
        return missing
    
    def _evaluate_admission(self, state: ApplicationState) -> AdmissionDecision:
        """
        Evaluate admission using RAG system and business rules
        """
        # Build applicant profile from extracted data
        applicant_profile = self._build_applicant_profile(state)
        
        # Query handbook for relevant admission rules
        handbook_rules = self._query_admission_rules(state.target_program, applicant_profile)
        
        # Apply decision logic
        decision = self._apply_decision_logic(applicant_profile, handbook_rules, state)
        
        return decision
    
    def _build_applicant_profile(self, state: ApplicationState) -> Dict[str, Any]:
        """
        Build comprehensive applicant profile from extracted data
        """
        profile = {
            "target_program": state.target_program,
            "entity": state.entity,
            "qualifications": [],
            "work_experience": [],
            "personal_info": {}
        }
        
        for extraction in state.extracted_data:
            if extraction.document_type == "transcript":
                profile["qualifications"].append({
                    "type": "university_degree",
                    "data": extraction.data,
                    "confidence": extraction.confidence
                })
            
            elif extraction.document_type in ["a_levels", "abitur", "ib"]:
                profile["qualifications"].append({
                    "type": "secondary_education",
                    "subtype": extraction.document_type,
                    "data": extraction.data,
                    "confidence": extraction.confidence
                })
            
            elif extraction.document_type == "work_certificate":
                profile["work_experience"].append(extraction.data)
            
            elif extraction.document_type == "cv":
                profile["personal_info"] = extraction.data
        
        return profile
    
    def _query_admission_rules(self, target_program: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query the handbook for relevant admission rules
        """
        # Build specific queries based on applicant profile
        queries = []
        
        # Base program requirements
        queries.append(f"What are the admission requirements for {target_program}?")
        
        # Qualification-specific queries
        for qual in profile.get("qualifications", []):
            if qual["type"] == "secondary_education":
                subtype = qual["subtype"]
                queries.append(f"How is {subtype} recognized for admission to {target_program}?")
                
                # Specific grade requirements
                if "overall_grade" in qual["data"]:
                    grade = qual["data"]["overall_grade"]
                    queries.append(f"What is the minimum grade requirement for {target_program} with {subtype}?")
        
        # Work experience queries
        if profile.get("work_experience"):
            queries.append(f"Can work experience substitute for academic qualifications in {target_program}?")
        
        # Execute queries and aggregate results
        all_rules = []
        for query in queries:
            try:
                result = self.rag_retriever.query_admission_rules(query)
                all_rules.append(result)
            except Exception as e:
                logger.warning(f"RAG query failed: {query} - {e}")
        
        return {"queries": queries, "results": all_rules}
    
    def _apply_decision_logic(self, profile: Dict[str, Any], handbook_rules: Dict[str, Any], state: ApplicationState) -> AdmissionDecision:
        """
        Apply comprehensive decision logic combining RAG results with business rules
        """
        # Prepare decision context
        decision_context = {
            "applicant_profile": profile,
            "handbook_rules": handbook_rules,
            "target_program": state.target_program,
            "entity": state.entity
        }
        
        prompt = f"""
        You are an expert admission officer for IU University making an admission decision.
        
        APPLICANT PROFILE:
        {json.dumps(profile, indent=2)}
        
        RELEVANT HANDBOOK RULES:
        {json.dumps(handbook_rules, indent=2)}
        
        TARGET PROGRAM: {state.target_program}
        ENTITY: {state.entity}
        
        Based on the handbook rules and applicant qualifications, make an admission decision.
        
        Consider:
        1. Does the applicant meet minimum qualification requirements?
        2. Are grades/scores sufficient for the program?
        3. Are there any regulatory compliance issues?
        4. Is there sufficient evidence to make a confident decision?
        
        Respond with JSON format:
        {{
            "status": "APPROVED|REJECTED|REVIEW_REQUIRED",
            "confidence": 0.95,
            "reasoning": "detailed explanation with specific rule references",
            "applied_rules": [
                {{"rule_id": "R1", "rule_text": "...", "outcome": "satisfied|not_satisfied"}},
                {{"rule_id": "R2", "rule_text": "...", "outcome": "satisfied|not_satisfied"}}
            ],
            "handbook_citations": ["page 42", "section 3.2"],
            "missing_documents": [],
            "concerns": ["any concerns or risk factors"]
        }}
        
        If confidence is below 0.8, use REVIEW_REQUIRED status.
        """
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            decision_data = json.loads(response.content[0].text)
            
            return AdmissionDecision(
                status=decision_data["status"],
                confidence=decision_data["confidence"],
                reasoning=decision_data["reasoning"],
                applied_rules=decision_data.get("applied_rules", []),
                missing_documents=decision_data.get("missing_documents", []),
                handbook_citations=decision_data.get("handbook_citations", [])
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse decision JSON: {e}")
            
            # Fallback decision
            return AdmissionDecision(
                status="REVIEW_REQUIRED",
                confidence=0.0,
                reasoning="Decision parsing failed - requires manual review",
                applied_rules=[],
                handbook_citations=[]
            )