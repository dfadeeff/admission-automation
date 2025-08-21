"""
Vector Store for RAG System
Handles embedding and retrieval of handbook chunks using FREE embeddings
"""
import logging
from typing import List, Dict, Any, Optional
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from .free_embeddings import get_free_embeddings

logger = logging.getLogger(__name__)

class HandbookVectorStore:
    """
    Vector store for handbook chunks using ChromaDB
    """
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.embeddings = get_free_embeddings()  # FREE local embeddings!
        self.vector_store = None
        
    def create_or_load_index(self, documents: Optional[List[Document]] = None) -> Chroma:
        """
        Create a new index or load existing one
        """
        import os
        
        if documents:
            # Create new index
            logger.info("Creating new vector store index...")
            self.vector_store = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=self.persist_directory
            )
            self.vector_store.persist()
            logger.info(f"Index created with {len(documents)} documents")
        else:
            # Check if existing index exists and has data
            if os.path.exists(self.persist_directory):
                logger.info("Loading existing vector store...")
                try:
                    self.vector_store = Chroma(
                        persist_directory=self.persist_directory,
                        embedding_function=self.embeddings
                    )
                    # Test if it has any data
                    test_result = self.vector_store.similarity_search("test", k=1)
                    logger.info(f"Loaded existing vector store with data")
                except Exception as e:
                    logger.warning(f"Failed to load existing vector store: {e}")
                    logger.info("Creating new vector store from handbook...")
                    # Load and process handbook
                    from .handbook_loader import HandbookLoader
                    loader = HandbookLoader()
                    chunks = loader.process_handbook()
                    self.vector_store = Chroma.from_documents(
                        documents=chunks,
                        embedding=self.embeddings,
                        persist_directory=self.persist_directory
                    )
                    self.vector_store.persist()
                    logger.info(f"New index created with {len(chunks)} documents")
            else:
                logger.info("No existing vector store found. Creating new one from handbook...")
                # Load and process handbook
                from .handbook_loader import HandbookLoader
                loader = HandbookLoader()
                chunks = loader.process_handbook()
                self.vector_store = Chroma.from_documents(
                    documents=chunks,
                    embedding=self.embeddings,
                    persist_directory=self.persist_directory
                )
                self.vector_store.persist()
                logger.info(f"New index created with {len(chunks)} documents")
            
        return self.vector_store
    
    def search(self, query: str, k: int = 5, filter_dict: Optional[Dict] = None) -> List[Document]:
        """
        Search for relevant chunks
        """
        if not self.vector_store:
            raise ValueError("Vector store not initialized. Call create_or_load_index first.")
        
        if filter_dict:
            results = self.vector_store.similarity_search(
                query=query,
                k=k,
                filter=filter_dict
            )
        else:
            results = self.vector_store.similarity_search(
                query=query,
                k=k
            )
        
        logger.debug(f"Found {len(results)} relevant chunks for query: {query[:100]}...")
        return results
    
    def search_with_scores(self, query: str, k: int = 5) -> List[tuple]:
        """
        Search with relevance scores
        """
        if not self.vector_store:
            raise ValueError("Vector store not initialized. Call create_or_load_index first.")
        
        results = self.vector_store.similarity_search_with_score(
            query=query,
            k=k
        )
        
        return results