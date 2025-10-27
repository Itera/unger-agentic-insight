"""
Request models for API endpoints

Pydantic models for validating incoming request data.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel


class QueryRequest(BaseModel):
    """Request model for basic AI queries"""
    query: str
    use_adx: bool = True


class ContextualQueryRequest(BaseModel):
    """Request model for contextual AI queries with navigation scope"""
    query: str
    use_adx: bool = True
    context: Optional[Dict[str, Any]] = None  # Navigation context for scoped queries
