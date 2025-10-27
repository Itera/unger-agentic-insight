"""
Unit tests for BaseAgent class.
"""

import pytest
from datetime import datetime
from typing import Dict, Any

from agents.nodes.base import BaseAgent
from agents.state import AgentState, create_initial_state


class MockAgent(BaseAgent):
    """Mock agent for testing."""
    
    def __init__(self, name: str = "mock_agent", should_fail: bool = False):
        super().__init__(name)
        self.should_fail = should_fail
        self.execute_called = False
    
    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """Mock execute method."""
        self.execute_called = True
        
        if self.should_fail:
            raise RuntimeError("Mock agent failure")
        
        return {
            "result": "success",
            "data": {"test": "value"}
        }


@pytest.mark.asyncio
async def test_base_agent_successful_execution():
    """Test successful agent execution with timing and trace."""
    agent = MockAgent()
    state = create_initial_state("test query", {})
    
    result_state = await agent.run(state)
    
    # Verify execute was called
    assert agent.execute_called
    
    # Verify execution trace was updated
    assert len(result_state["execution_trace"]) == 1
    trace = result_state["execution_trace"][0]
    
    assert trace.agent_name == "mock_agent"
    assert trace.status == "success"
    assert trace.duration_ms > 0
    assert trace.error is None
    assert "mock_agent" in trace.summary


@pytest.mark.asyncio
async def test_base_agent_error_handling():
    """Test agent error handling and trace."""
    agent = MockAgent(should_fail=True)
    state = create_initial_state("test query", {})
    
    result_state = await agent.run(state)
    
    # Verify execution trace shows error
    assert len(result_state["execution_trace"]) == 1
    trace = result_state["execution_trace"][0]
    
    assert trace.status == "error"
    assert trace.error == "Mock agent failure"
    assert "Failed" in trace.summary
    
    # Verify error was added to state errors list
    assert len(result_state["errors"]) == 1
    assert "mock_agent" in result_state["errors"][0]


@pytest.mark.asyncio
async def test_base_agent_timing():
    """Test that agent execution timing is tracked."""
    agent = MockAgent()
    state = create_initial_state("test query", {})
    
    result_state = await agent.run(state)
    
    trace = result_state["execution_trace"][0]
    
    # Duration should be positive (execution takes some time)
    assert trace.duration_ms >= 0
    
    # Timestamp should be recent
    assert (datetime.now() - trace.timestamp).total_seconds() < 1


@pytest.mark.asyncio
async def test_multiple_agents_sequential():
    """Test multiple agents can run sequentially and update trace."""
    agent1 = MockAgent(name="agent_1")
    agent2 = MockAgent(name="agent_2")
    
    state = create_initial_state("test query", {})
    
    # Run agents sequentially
    state = await agent1.run(state)
    state = await agent2.run(state)
    
    # Verify both are in execution trace
    assert len(state["execution_trace"]) == 2
    assert state["execution_trace"][0].agent_name == "agent_1"
    assert state["execution_trace"][1].agent_name == "agent_2"
    
    # All successful
    assert all(t.status == "success" for t in state["execution_trace"])


@pytest.mark.asyncio
async def test_agent_continues_after_error():
    """Test that workflow can continue even if one agent fails."""
    failing_agent = MockAgent(name="failing", should_fail=True)
    success_agent = MockAgent(name="success", should_fail=False)
    
    state = create_initial_state("test query", {})
    
    # Run failing agent then successful one
    state = await failing_agent.run(state)
    state = await success_agent.run(state)
    
    # Both should be in trace
    assert len(state["execution_trace"]) == 2
    
    # First failed, second succeeded
    assert state["execution_trace"][0].status == "error"
    assert state["execution_trace"][1].status == "success"
    
    # Error recorded
    assert len(state["errors"]) == 1
