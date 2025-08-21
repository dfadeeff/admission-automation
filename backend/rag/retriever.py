"""
RAG Retriever for Admission Rules
Queries the handbook for relevant admission criteria
"""
import logging
import os
from typing import List, Dict, Any, Optional
import anthropic
from langchain_core.documents import Document
from .vector_store import HandbookVectorStore
from .handbook_loader import HandbookLoader

logger = logging.getLogger(__name__)

class AdmissionRulesRetriever:
    """
    RAG system for retrieving and interpreting admission rules
    """
    
    def __init__(self):
        self.vector_store = HandbookVectorStore()
        
        # Get API key from environment
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
            
        self.client = anthropic.Anthropic(api_key=anthropic_key)
        self.model = "claude-3-5-sonnet-20241022"
        
    def initialize(self, force_reload: bool = False):
        """
        Initialize the RAG system
        """
        if force_reload:
            # Reload and reindex the handbook
            loader = HandbookLoader()
            chunks = loader.process_handbook()
            self.vector_store.create_or_load_index(documents=chunks)
        else:
            # Load existing index
            self.vector_store.create_or_load_index()
        
    
    def query_admission_rules(self, question: str) -> Dict[str, Any]:
        """
        Query the handbook for specific admission rules
        """
        if not hasattr(self.vector_store, 'vector_store') or not self.vector_store.vector_store:
            raise ValueError("RAG system not initialized. Call initialize() first.")
        
        logger.info(f"Querying admission rules: {question[:100]}...")
        
        # Get relevant documents
        docs = self.vector_store.search(question, k=5)
        
        # Build context from documents
        context = "\n\n".join([
            f"Page {doc.metadata.get('page', '?')}: {doc.page_content}"
            for doc in docs
        ])
        
        # Create prompt
        prompt = f"""You are an expert on IU admission rules and regulations. 
        Use the following context from the IU admission handbook to answer the question.
        Always cite the specific page numbers and sections when providing information.
        If the information is not in the context, say so clearly.
        
        Context from handbook:
        {context}
        
        Question: {question}
        
        Answer (include page references):"""
        
        # Query Anthropic
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )
            
            answer = response.content[0].text
            
            # Extract source information
            sources = []
            for doc in docs:
                sources.append({
                    "page": doc.metadata.get("page"),
                    "excerpt": doc.page_content[:200] + "...",
                    "chunk_index": doc.metadata.get("chunk_index")
                })
            
            return {
                "answer": answer,
                "sources": sources,
                "question": question
            }
            
        except Exception as e:
            logger.error(f"Query failed: {str(e)}")
            raise
    
    def check_admission_criteria(self, applicant_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if an applicant meets admission criteria based on handbook rules
        """
        # Build a comprehensive query based on applicant data
        query_parts = []
        
        if applicant_data.get("target_program"):
            query_parts.append(f"admission requirements for {applicant_data['target_program']}")
        
        if applicant_data.get("previous_qualification"):
            query_parts.append(f"recognition of {applicant_data['previous_qualification']}")
        
        if applicant_data.get("has_exmatrikulation"):
            query_parts.append("rules about Zwangsexmatrikulation and forced deregistration")
        
        if applicant_data.get("work_experience_years"):
            query_parts.append(f"work experience requirements ({applicant_data['work_experience_years']} years)")
        
        query = "What are the " + " and ".join(query_parts) + "?"
        
        return self.query_admission_rules(query)
    
    def find_relevant_sections(self, topics: List[str], k: int = 3) -> Dict[str, List[Document]]:
        """
        Find relevant handbook sections for multiple topics
        """
        results = {}
        
        for topic in topics:
            docs = self.vector_store.search(topic, k=k)
            results[topic] = docs
            
        return results