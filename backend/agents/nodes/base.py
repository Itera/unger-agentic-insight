"""
Base agent class for all agents in the multi-agent system.

Provides common functionality for execution tracking, error handling, and timing.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import time

from agents.state import AgentState, AgentResult


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    
    Agents must implement the execute() method which contains their core logic.
    This class handles timing, error tracking, and result formatting automatically.
    """
    
    def __init__(self, name: str):
        """
        Initialize agent.
        
        Args:
            name: Agent identifier (e.g., "graph_agent", "maintenance_agent")
        """
        self.name = name
    
    @abstractmethod
    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute agent logic.
        
        Args:
            state: Current workflow state
            
        Returns:
            Agent-specific output dictionary
            
        Raises:
            Exception: If agent execution fails
        """
        pass
    
    async def run(self, state: AgentState) -> AgentState:
        """
        Run agent with automatic timing and error handling.
        
        This method wraps execute() to track performance and handle errors.
        Updates the state with agent results and execution trace.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with agent results
        """
        start_time = time.time()
        status = "success"
        output = None
        error_msg = None
        summary = ""
        
        try:
            # Execute agent logic
            output = await self.execute(state)
            summary = self._generate_summary(output)
            
        except Exception as e:
            status = "error"
            error_msg = str(e)
            summary = f"Failed: {error_msg}"
            state["errors"].append(f"{self.name}: {error_msg}")
        
        finally:
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Create agent result
            agent_result = AgentResult(
                agent_name=self.name,
                status=status,
                duration_ms=duration_ms,
                summary=summary,
                output=output,
                error=error_msg,
                timestamp=datetime.now()
            )
            
            # Add to execution trace
            state["execution_trace"].append(agent_result)
            
            # Store output in state (agent-specific key)
            if status == "success" and output:
                self._store_output(state, output)
        
        return state
    
    def _generate_summary(self, output: Dict[str, Any]) -> str:
        """
        Generate human-readable summary of agent output.
        
        Can be overridden by subclasses for custom summaries.
        
        Args:
            output: Agent output dictionary
            
        Returns:
            Summary string
        """
        return f"{self.name} completed successfully"
    
    def _store_output(self, state: AgentState, output: Dict[str, Any]) -> None:
        """
        Store agent output in state.
        
        Can be overridden by subclasses to customize storage location.
        
        Args:
            state: Current workflow state
            output: Agent output to store
        """
        # Default: store in agent-specific key
        state_key = f"{self.name}_result"
        if state_key in state:
            state[state_key] = output
