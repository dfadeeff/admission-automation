"""
Simplified settings for RAG-focused system
"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Anthropic Configuration (for LLM)
    ANTHROPIC_API_KEY: str = ""
    LLM_MODEL: str = "claude-3-5-sonnet-20241022"
    LLM_PROVIDER: str = "anthropic"  # Added this field
    
    # Free Local Embeddings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"  # Free sentence transformer model
    
    # RAG Configuration
    CHUNK_SIZE: int = 1500
    CHUNK_OVERLAP: int = 200
    RETRIEVAL_K: int = 5
    
    # Paths
    HANDBOOK_PATH: str = "data/Leitfaden.pdf"
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()