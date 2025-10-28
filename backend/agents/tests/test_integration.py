"""
Integration tests for multi-agent workflow orchestration.

Tests the complete workflow from query to response with real agent collaboration.
"""

import pytest
from agents.workflow import WorkflowCoordinator
from agents.state import create_initial_state


@pytest.fixture
def coordinator():
    """Create workflow coordinator instance."""
    return WorkflowCoordinator()


@pytest.mark.asyncio
async def test_graph_only_query(coordinator):
    """Test query that only requires graph data."""
    query = "What sensors are in area 40-10?"
    
    result = await coordinator.run(query)
    
    assert "query" in result
    assert result["query"] == query
    assert "response" in result
    assert "execution_trace" in result
    
    # Should invoke graph_agent and synthesizer
    trace = result["execution_trace"]
    agents_invoked = {agent["agent_name"] for agent in trace["agents_invoked"]}
    assert "graph_agent" in agents_invoked
    assert "synthesizer" in agents_invoked


@pytest.mark.asyncio
async def test_maintenance_query(coordinator):
    """Test query that requires graph + maintenance data."""
    query = "Are there work orders in area 40-10?"
    
    result = await coordinator.run(query)
    
    assert "response" in result
    assert len(result["response"]) > 0
    
    # Should invoke graph, maintenance, and synthesizer
    trace = result["execution_trace"]
    agents_invoked = {agent["agent_name"] for agent in trace["agents_invoked"]}
    assert "graph_agent" in agents_invoked
    assert "maintenance_agent" in agents_invoked
    assert "synthesizer" in agents_invoked


@pytest.mark.asyncio
async def test_sensor_data_query(coordinator):
    """Test query that requires graph + sensor data."""
    query = "Show me abnormal temperature readings"
    
    result = await coordinator.run(query)
    
    assert "response" in result
    
    # Should invoke graph, ADX, and synthesizer
    trace = result["execution_trace"]
    agents_invoked = {agent["agent_name"] for agent in trace["agents_invoked"]}
    assert "graph_agent" in agents_invoked
    assert "adx_agent" in agents_invoked
    assert "synthesizer" in agents_invoked


@pytest.mark.asyncio
async def test_combined_query(coordinator):
    """Test query that requires all data sources."""
    query = "Show equipment status with maintenance and sensor data for area 40-10"
    
    result = await coordinator.run(query)
    
    assert "response" in result
    assert "execution_trace" in result
    
    # Should invoke all agents
    trace = result["execution_trace"]
    agents_invoked = {agent["agent_name"] for agent in trace["agents_invoked"]}
    assert "graph_agent" in agents_invoked
    # May include maintenance_agent and adx_agent depending on intent classification


@pytest.mark.asyncio
async def test_execution_trace_structure(coordinator):
    """Test that execution trace has correct structure."""
    query = "What sensors are in area 40-10?"
    
    result = await coordinator.run(query)
    
    trace = result["execution_trace"]
    assert "total_duration_ms" in trace
    assert "agents_invoked" in trace
    assert "workflow_version" in trace
    
    # Check agent trace structure
    for agent_trace in trace["agents_invoked"]:
        assert "agent_name" in agent_trace
        assert "status" in agent_trace
        assert "duration_ms" in agent_trace
        assert "summary" in agent_trace
        assert "timestamp" in agent_trace


@pytest.mark.asyncio
async def test_error_handling(coordinator):
    """Test workflow handles errors gracefully."""
    # Empty query should still complete
    query = ""
    
    result = await coordinator.run(query)
    
    assert "response" in result
    # Should not crash, may have error in trace


@pytest.mark.asyncio
async def test_agent_output_preservation(coordinator):
    """Test that agent outputs are preserved in state."""
    query = "What sensors are in area 40-10?"
    
    result = await coordinator.run(query)
    
    # Check that outputs are in trace
    trace = result["execution_trace"]
    graph_trace = next((a for a in trace["agents_invoked"] if a["agent_name"] == "graph_agent"), None)
    
    assert graph_trace is not None
    assert "output" in graph_trace
    assert graph_trace["output"] is not None
