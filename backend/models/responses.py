"""
Response models for API endpoints

Pydantic models for structuring API responses.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class QueryResponse(BaseModel):
    """Response model for AI query results"""
    query: str
    response: str
    data: Optional[List[Dict[str, Any]]] = None
    source: str
    timestamp: datetime
    context_used: Optional[Dict[str, Any]] = None  # Context data that was actually used
