"""
Document Classification Agent
Classifies uploaded documents into categories
"""
import logging
import os
from typing import List, Dict, Any
import anthropic
from .state import ApplicationState, ClassifiedDocument, DocumentFile
from config.settings import settings
import pypdf
import base64
import json

logger = logging.getLogger(__name__)

class DocumentClassifierAgent:
    """
    Agent that classifies documents into admission document types
    """
    
    def __init__(self):
        # Get API key from environment
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
            
        self.client = anthropic.Anthropic(api_key=anthropic_key)
        self.model = "claude-3-5-sonnet-20241022"
        
        self.document_types = [
            "transcript",      # University/school transcripts
            "a_levels",       # A-Level certificates
            "abitur",         # German Abitur certificates
            "ib",             # International Baccalaureate
            "passport",       # Identity documents
            "cv",             # Curriculum Vitae
            "work_certificate", # Work experience certificates
            "apprenticeship", # Apprenticeship certificates
            "other"           # Unclassified documents
        ]
    
    def process(self, state: ApplicationState) -> ApplicationState:
        """
        Main processing function - classifies all uploaded documents
        """
        logger.info(f"Classifying {len(state.uploaded_files)} documents for application {state.application_id}")
        
        state.current_stage = "classifying_documents"
        classified_docs = []
        
        for file in state.uploaded_files:
            try:
                classification = self._classify_single_document(file)
                classified_docs.append(classification)
                
                state.add_log(
                    agent="DocumentClassifier",
                    action="classify_document", 
                    details={
                        "file": file.filename,
                        "classified_as": classification.document_type,
                        "confidence": classification.confidence
                    }
                )
                
            except Exception as e:
                logger.error(f"Failed to classify {file.filename}: {str(e)}")
                state.add_log(
                    agent="DocumentClassifier",
                    action="classification_error",
                    details={"file": file.filename, "error": str(e)}
                )
        
        state.classified_documents = classified_docs
        state.current_stage = "documents_classified"
        
        logger.info(f"Classified {len(classified_docs)} documents")
        return state
    
    def _classify_single_document(self, file: DocumentFile) -> ClassifiedDocument:
        """
        Classify a single document using Claude
        """
        # Extract text from document
        text_content = self._extract_text(file)
        
        # Prepare classification prompt
        prompt = f"""
        You are a document classifier for university admissions. 
        Classify this document into one of these categories: {', '.join(self.document_types)}
        
        Document filename: {file.filename}
        Document content (first 1000 characters):
        {text_content[:1000]}
        
        Consider:
        - File name patterns (transcript, cv, abitur, etc.)
        - Content keywords and structure
        - Academic terminology
        - Official document formats
        
        Respond with JSON format:
        {{
            "document_type": "category",
            "confidence": 0.95,
            "reasoning": "brief explanation"
        }}
        """
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse response
        try:
            result = json.loads(response.content[0].text)
            
            return ClassifiedDocument(
                file=file,
                document_type=result["document_type"],
                confidence=result["confidence"]
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse classification response for {file.filename}: {e}")
            # Fallback classification
            return ClassifiedDocument(
                file=file,
                document_type="other",
                confidence=0.1
            )
    
    def _extract_text(self, file: DocumentFile) -> str:
        """
        Extract text from PDF or image files
        """
        try:
            if file.file_type.lower() == "pdf":
                return self._extract_pdf_text(file.file_path)
            else:
                # For images, we'd use OCR here
                return f"Image file: {file.filename} (OCR not implemented in demo)"
                
        except Exception as e:
            logger.error(f"Text extraction failed for {file.filename}: {e}")
            return f"Text extraction failed: {str(e)}"
    
    def _extract_pdf_text(self, file_path: str) -> str:
        """
        Extract text from PDF file
        """
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                text = ""
                
                # Extract text from first few pages
                for page_num in range(min(3, len(pdf_reader.pages))):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
                
                return text
                
        except Exception as e:
            logger.error(f"PDF text extraction failed: {e}")
            return ""