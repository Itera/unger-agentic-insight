"""
Core configuration module

Centralizes all environment variable loading and configuration management.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment variables"""
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Azure Data Explorer (ADX) Configuration
    ADX_MCP_URL: str = os.getenv("ADX_MCP_URL", "http://localhost:8001")
    
    # Neo4j Configuration
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USERNAME: str = os.getenv("NEO4J_USERNAME", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")
    NEO4J_DATABASE: str = os.getenv("NEO4J_DATABASE", "neo4j")
    
    # CORS Origins
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",  # Vite default port
        "http://frontend:3000"
    ]


# Global settings instance
settings = Settings()
