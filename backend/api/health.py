"""
Health Check API Router

Basic health check endpoint.
"""

from fastapi import APIRouter

from services.graph_service import graph_service
from core.dependencies import get_openai_client
from core.config import settings


router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Returns:
        System health status including service availability
    """
    openai_client = get_openai_client()
    
    return {
        "status": "healthy",
        "openai_available": openai_client is not None,
        "graph_connected": graph_service.is_connected(),
        "adx_mcp_url": settings.ADX_MCP_URL,
        "neo4j_uri": settings.NEO4J_URI
    }
