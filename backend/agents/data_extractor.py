"""
Data Extraction Agent
Extracts structured data from classified documents
"""
import logging
import os
from typing import List, Dict, Any
import anthropic
from .state import ApplicationState, ExtractedData, ClassifiedDocument
from config.settings import settings
import json

logger = logging.getLogger(__name__)

class DataExtractionAgent:
    """
    Agent that extracts structured data from classified documents
    """
    
    def __init__(self):
        # Get API key from environment
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
            
        self.client = anthropic.Anthropic(api_key=anthropic_key)
        self.model = "claude-3-5-sonnet-20241022"
        
        # Extraction templates for different document types
        self.extraction_prompts = {
            "transcript": """
            Extract structured data from this academic transcript:
            - institution_name: string
            - degree_type: string (Bachelor, Master, etc.)
            - field_of_study: string
            - graduation_date: string (YYYY-MM-DD)
            - final_grade: string
            - gpa: float (if available)
            - grading_system: string
            - subjects: list of {subject_name, grade, credits}
            - country: string
            - language_of_instruction: string
            """,
            
            "a_levels": """
            Extract A-Level examination data:
            - exam_board: string (AQA, Edexcel, OCR, etc.)
            - examination_session: string (e.g., "June 2023")
            - subjects: list of {subject_name, grade, unit_codes}
            - overall_grade: string
            - centre_number: string
            - candidate_number: string
            - country: string (usually UK)
            """,
            
            "abitur": """
            Extract German Abitur data:
            - school_name: string
            - state: string (Bayern, NRW, etc.)
            - graduation_year: int
            - overall_grade: float (1.0-4.0 scale)
            - subjects: list of {subject_name, grade, level}
            - advanced_courses: list of subject names
            - basic_courses: list of subject names
            """,
            
            "ib": """
            Extract International Baccalaureate data:
            - school_name: string
            - country: string
            - graduation_year: int
            - total_points: int (out of 45)
            - subjects: list of {subject_name, level, grade}
            - extended_essay_grade: string
            - tok_grade: string (Theory of Knowledge)
            - cas_completed: boolean (Creativity, Activity, Service)
            """,
            
            "work_certificate": """
            Extract work experience data:
            - company_name: string
            - position_title: string
            - start_date: string (YYYY-MM-DD)
            - end_date: string (YYYY-MM-DD)
            - employment_type: string (full-time, part-time, internship)
            - responsibilities: list of strings
            - industry: string
            - supervisor_name: string
            - supervisor_contact: string
            """,
            
            "cv": """
            Extract CV/Resume data:
            - personal_info: {name, email, phone, address}
            - education: list of education entries
            - work_experience: list of work entries
            - skills: list of strings
            - languages: list of {language, proficiency_level}
            - certifications: list of strings
            """,
            
            "other": """
            Extract any relevant admission-related information:
            - document_type: string (best guess)
            - key_information: list of important facts
            - dates: list of relevant dates
            - institutions: list of mentioned institutions
            """
        }
    
    def process(self, state: ApplicationState) -> ApplicationState:
        """
        Extract data from all classified documents
        """
        logger.info(f"Extracting data from {len(state.classified_documents)} documents")
        
        state.current_stage = "extracting_data"
        extracted_data = []
        
        for classified_doc in state.classified_documents:
            try:
                extraction = self._extract_from_document(classified_doc)
                extracted_data.append(extraction)
                
                state.add_log(
                    agent="DataExtractor",
                    action="extract_data",
                    details={
                        "document": classified_doc.file.filename,
                        "type": classified_doc.document_type,
                        "fields_extracted": len(extraction.data),
                        "confidence": extraction.confidence
                    }
                )
                
            except Exception as e:
                logger.error(f"Data extraction failed for {classified_doc.file.filename}: {e}")
                state.add_log(
                    agent="DataExtractor",
                    action="extraction_error",
                    details={
                        "document": classified_doc.file.filename,
                        "error": str(e)
                    }
                )
        
        state.extracted_data = extracted_data
        state.current_stage = "data_extracted"
        
        logger.info(f"Extracted data from {len(extracted_data)} documents")
        return state
    
    def _extract_from_document(self, classified_doc: ClassifiedDocument) -> ExtractedData:
        """
        Extract structured data from a single classified document
        """
        # Get document text
        text_content = self._get_document_text(classified_doc.file.file_path)
        
        # Get extraction prompt for this document type
        extraction_template = self.extraction_prompts.get(
            classified_doc.document_type, 
            self.extraction_prompts["other"]
        )
        
        prompt = f"""
        You are an expert data extraction system for university admissions.
        
        Document Type: {classified_doc.document_type}
        Document Content:
        {text_content}
        
        {extraction_template}
        
        Extract the requested information and return as valid JSON.
        If information is not available, use null.
        Be precise with grades, dates, and institutional names.
        
        Return only the JSON object, no additional text.
        """
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            # Parse the JSON response
            extracted_json = json.loads(response.content[0].text)
            confidence = self._calculate_extraction_confidence(extracted_json, classified_doc.document_type)
            
            return ExtractedData(
                document_type=classified_doc.document_type,
                data=extracted_json,
                confidence=confidence,
                source_file=classified_doc.file.filename
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse extraction JSON: {e}")
            return ExtractedData(
                document_type=classified_doc.document_type,
                data={"error": "Failed to parse extracted data"},
                confidence=0.0,
                source_file=classified_doc.file.filename
            )
    
    def _get_document_text(self, file_path: str) -> str:
        """
        Get text content from document file
        """
        try:
            if file_path.lower().endswith('.pdf'):
                import pypdf
                with open(file_path, 'rb') as file:
                    pdf_reader = pypdf.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                    return text
            else:
                # For demo - in production would use OCR for images
                return f"[Image file: {file_path}]"
                
        except Exception as e:
            logger.error(f"Failed to read document {file_path}: {e}")
            return ""
    
    def _calculate_extraction_confidence(self, extracted_data: Dict[str, Any], doc_type: str) -> float:
        """
        Calculate confidence score based on how much data was extracted
        """
        if not extracted_data or "error" in extracted_data:
            return 0.0
        
        # Count non-null fields
        non_null_fields = sum(1 for v in extracted_data.values() if v is not None)
        total_fields = len(extracted_data)
        
        if total_fields == 0:
            return 0.0
        
        base_confidence = non_null_fields / total_fields
        
        # Boost confidence for critical fields based on document type
        critical_fields = {
            "transcript": ["institution_name", "graduation_date", "final_grade"],
            "a_levels": ["exam_board", "subjects"],
            "abitur": ["school_name", "overall_grade", "graduation_year"],
            "ib": ["total_points", "subjects", "graduation_year"]
        }
        
        if doc_type in critical_fields:
            critical_present = sum(
                1 for field in critical_fields[doc_type] 
                if field in extracted_data and extracted_data[field] is not None
            )
            critical_ratio = critical_present / len(critical_fields[doc_type])
            return min(1.0, base_confidence * 0.5 + critical_ratio * 0.5)
        
        return base_confidence