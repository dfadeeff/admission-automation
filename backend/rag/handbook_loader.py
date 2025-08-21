"""
PDF Handbook Loader and Chunker
Processes the 245-page IU admission handbook
"""
import logging
from typing import List, Dict, Any
from pathlib import Path
import pypdf
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

class HandbookLoader:
    """
    Loads and processes the IU admission handbook PDF
    """
    
    def __init__(self, pdf_path: str = None):
        self.pdf_path = Path(pdf_path or "../data/Leitfaden.pdf")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", " ", ""],
            length_function=len,
        )
        
    def load_pdf(self) -> List[Document]:
        """
        Load PDF and extract text with metadata
        """
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"Handbook not found at {self.pdf_path}")
            
        documents = []
        
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages, start=1):
                    text = page.extract_text()
                    
                    if text.strip():
                        # Create document with metadata
                        doc = Document(
                            page_content=text,
                            metadata={
                                "source": str(self.pdf_path),
                                "page": page_num,
                                "total_pages": len(pdf_reader.pages)
                            }
                        )
                        documents.append(doc)
                        
            logger.info(f"Loaded {len(documents)} pages from handbook")
            return documents
            
        except Exception as e:
            logger.error(f"Error loading PDF: {str(e)}")
            raise
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into smaller chunks for embedding
        """
        chunks = []
        
        for doc in documents:
            # Split the document text
            split_docs = self.text_splitter.split_text(doc.page_content)
            
            # Create new documents with preserved metadata
            for i, chunk_text in enumerate(split_docs):
                chunk_doc = Document(
                    page_content=chunk_text,
                    metadata={
                        **doc.metadata,
                        "chunk_index": i,
                        "chunk_total": len(split_docs)
                    }
                )
                chunks.append(chunk_doc)
        
        logger.info(f"Created {len(chunks)} chunks from {len(documents)} pages")
        return chunks
    
    def process_handbook(self) -> List[Document]:
        """
        Complete pipeline to load and chunk the handbook
        """
        documents = self.load_pdf()
        chunks = self.chunk_documents(documents)
        return chunks