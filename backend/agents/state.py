"""
State management for multi-agent orchestration.

Defines the shared state structure that flows through the LangGraph workflow.
"""

from typing import TypedDict, List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class AgentResult(BaseModel):
    """Result from a single agent execution."""
    
    agent_name: str
    status: str  # "success" | "error" | "skipped"
    duration_ms: int
    summary: str
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime


class ExecutionTrace(BaseModel):
    """Complete execution trace for all agents in workflow."""
    
    total_duration_ms: int
    agents_invoked: List[AgentResult]
    workflow_version: str = "1.0"


class AgentState(TypedDict):
    """
    Shared state that flows through the LangGraph workflow.
    
    This is the single source of truth for all agents in the orchestration.
    """
    
    # Input
    query: str
    user_request: Dict[str, Any]  # Original request metadata
    
    # Agent outputs
    graph_result: Optional[Dict[str, Any]]
    maintenance_result: Optional[Dict[str, Any]]
    adx_result: Optional[Dict[str, Any]]
    
    # Final output
    synthesized_response: Optional[str]
    
    # Execution tracking
    execution_trace: List[AgentResult]
    workflow_start_time: datetime
    
    # Control flow
    agents_to_invoke: List[str]  # Determined by coordinator
    current_agent: Optional[str]
    errors: List[str]


def create_initial_state(query: str, user_request: Dict[str, Any]) -> AgentState:
    """
    Create initial state for workflow execution.
    
    Args:
        query: User's natural language query
        user_request: Additional request metadata
        
    Returns:
        Initial AgentState
    """
    return AgentState(
        query=query,
        user_request=user_request,
        graph_result=None,
        maintenance_result=None,
        adx_result=None,
        synthesized_response=None,
        execution_trace=[],
        workflow_start_time=datetime.now(),
        agents_to_invoke=[],
        current_agent=None,
        errors=[]
    )


def build_execution_trace(state: AgentState) -> ExecutionTrace:
    """
    Build final execution trace from state.
    
    Args:
        state: Final workflow state
        
    Returns:
        ExecutionTrace for API response
    """
    total_duration = int((datetime.now() - state["workflow_start_time"]).total_seconds() * 1000)
    
    return ExecutionTrace(
        total_duration_ms=total_duration,
        agents_invoked=state["execution_trace"]
    )
