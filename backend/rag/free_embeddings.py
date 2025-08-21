"""
Free Local Embeddings using Sentence Transformers
No API keys required - completely free!
"""
import logging
from typing import List
from sentence_transformers import SentenceTransformer
from langchain.embeddings.base import Embeddings

logger = logging.getLogger(__name__)

class FreeSentenceTransformerEmbeddings(Embeddings):
    """
    Free local embeddings using Sentence Transformers
    """
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or "all-MiniLM-L6-v2"
        logger.info(f"Loading free embedding model: {self.model_name}")
        
        # Load the model locally (downloads once, then cached)
        self.model = SentenceTransformer(self.model_name)
        logger.info("Free embedding model loaded successfully!")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of documents
        """
        logger.debug(f"Embedding {len(texts)} documents")
        embeddings = self.model.encode(texts, convert_to_tensor=False)
        return embeddings.tolist()
    
    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query
        """
        logger.debug("Embedding query")
        embedding = self.model.encode([text], convert_to_tensor=False)
        return embedding[0].tolist()

def get_free_embeddings() -> FreeSentenceTransformerEmbeddings:
    """
    Factory function to get free embeddings
    """
    return FreeSentenceTransformerEmbeddings()