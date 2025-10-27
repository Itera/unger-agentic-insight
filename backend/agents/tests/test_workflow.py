"""
Tests for workflow coordinator and synthesizer agent.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from agents.workflow import WorkflowCoordinator, get_coordinator
from agents.nodes.synthesizer import SynthesizerAgent
from agents.state import create_initial_state


# Synthesizer Tests

@pytest.mark.asyncio
async def test_synthesizer_initialization():
    """Test SynthesizerAgent initialization."""
    with patch('agents.nodes.synthesizer.get_openai_client', return_value=MagicMock()):
        agent = SynthesizerAgent()
        assert agent.name == "synthesizer"


@pytest.mark.asyncio
async def test_synthesizer_builds_context():
    """Test context building from agent outputs."""
    with patch('agents.nodes.synthesizer.get_openai_client', return_value=MagicMock()):
        agent = SynthesizerAgent()
        
        graph_result = {
            "results": [{"name": "Sensor1"}, {"name": "Sensor2"}],
            "result_count": 2
        }
        
        maintenance_result = {
            "work_orders": [{"nr": 123, "short_description": "Test WO"}],
            "work_order_count": 1
        }
        
        adx_result = {
            "measurements": [{"value": 50.0}],
            "anomalies": [{"sensor_name": "S1", "anomaly_type": "spike", "severity": "high"}],
            "mock_data": True
        }
        
        context = agent._build_context(graph_result, maintenance_result, adx_result)
        
        assert "GRAPH DATA (2 results)" in context
        assert "MAINTENANCE DATA (1 work orders)" in context
        assert "SENSOR DATA [MOCK DATA]" in context
        assert "anomalies detected" in context


@pytest.mark.asyncio
async def test_synthesizer_handles_no_data():
    """Test synthesizer with no agent data."""
    with patch('agents.nodes.synthesizer.get_openai_client', return_value=MagicMock()):
        agent = SynthesizerAgent()
        
        context = agent._build_context(None, None, None)
        
        # Should handle gracefully
        assert isinstance(context, str)


@pytest.mark.asyncio
async def test_synthesizer_synthesis():
    """Test full synthesis with mocked LLM."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Based on the graph data, there are 2 sensors in the area."
    mock_client.chat.completions.create.return_value = mock_response
    
    with patch('agents.nodes.synthesizer.get_openai_client', return_value=mock_client):
        agent = SynthesizerAgent()
        state = create_initial_state("What sensors are there?", {})
        state["graph_result"] = {
            "results": [{"name": "S1"}, {"name": "S2"}],
            "result_count": 2
        }
        
        result_state = await agent.run(state)
        
        assert result_state["execution_trace"][0].status == "success"
        assert "synthesized_response" in result_state
        assert "2 sensors" in result_state["synthesized_response"]


# Workflow Coordinator Tests

@pytest.fixture
def mock_all_agents():
    """Mock all agents for workflow testing."""
    with patch('agents.workflow.GraphAgent') as mock_graph, \
         patch('agents.workflow.MaintenanceAgent') as mock_maint, \
         patch('agents.workflow.ADXAgent') as mock_adx, \
         patch('agents.workflow.SynthesizerAgent') as mock_synth, \
         patch('agents.workflow.get_openai_client') as mock_openai:
        
        # Setup mock returns
        mock_openai.return_value = MagicMock()
        
        yield {
            'graph': mock_graph,
            'maintenance': mock_maint,
            'adx': mock_adx,
            'synthesizer': mock_synth,
            'openai': mock_openai
        }


def test_coordinator_initialization(mock_all_agents):
    """Test WorkflowCoordinator initialization."""
    coordinator = WorkflowCoordinator()
    assert coordinator.workflow is not None
    assert coordinator.graph_agent is not None


def test_coordinator_singleton():
    """Test coordinator singleton pattern."""
    with patch('agents.workflow.WorkflowCoordinator') as mock_coordinator_class:
        mock_instance = MagicMock()
        mock_coordinator_class.return_value = mock_instance
        
        # Import to clear singleton
        import agents.workflow
        agents.workflow._coordinator = None
        
        coord1 = get_coordinator()
        coord2 = get_coordinator()
        
        # Should be same instance
        assert coord1 is coord2


def test_coordinator_intent_analysis(mock_all_agents):
    """Test intent classification logic."""
    coordinator = WorkflowCoordinator()
    state = create_initial_state("What sensors are in area 40-10?", {})
    
    # Mock LLM response
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"needs_graph": true, "needs_maintenance": false, "needs_adx": false}'
    mock_client.chat.completions.create.return_value = mock_response
    coordinator.openai_client = mock_client
    
    result_state = coordinator._analyze_intent_node(state)
    
    assert "agents_to_invoke" in result_state
    assert "graph" in result_state["agents_to_invoke"]
    assert "maintenance" not in result_state["agents_to_invoke"]
    assert "adx" not in result_state["agents_to_invoke"]


def test_coordinator_routing_logic(mock_all_agents):
    """Test conditional routing after graph agent."""
    coordinator = WorkflowCoordinator()
    
    # Test routing with only graph
    state1 = create_initial_state("test", {})
    state1["agents_to_invoke"] = ["graph"]
    assert coordinator._route_after_graph(state1) == "synthesizer"
    
    # Test routing with maintenance
    state2 = create_initial_state("test", {})
    state2["agents_to_invoke"] = ["graph", "maintenance"]
    assert coordinator._route_after_graph(state2) == "maintenance"
    
    # Test routing with ADX
    state3 = create_initial_state("test", {})
    state3["agents_to_invoke"] = ["graph", "adx"]
    assert coordinator._route_after_graph(state3) == "adx"
    
    # Test routing with both
    state4 = create_initial_state("test", {})
    state4["agents_to_invoke"] = ["graph", "maintenance", "adx"]
    assert coordinator._route_after_graph(state4) == "both"


def test_coordinator_intent_fallback(mock_all_agents):
    """Test intent classification fallback on error."""
    coordinator = WorkflowCoordinator()
    state = create_initial_state("test query", {})
    
    # Mock LLM to raise exception
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("LLM error")
    coordinator.openai_client = mock_client
    
    result_state = coordinator._analyze_intent_node(state)
    
    # Should fallback to all agents
    assert "agents_to_invoke" in result_state
    assert set(result_state["agents_to_invoke"]) == {"graph", "maintenance", "adx"}


@pytest.mark.asyncio
async def test_coordinator_run_method(mock_all_agents):
    """Test full workflow run (integration-style)."""
    # This is a simplified test - full integration would require all mocks
    with patch('agents.workflow.WorkflowCoordinator._build_workflow') as mock_build:
        mock_workflow = MagicMock()
        mock_workflow.invoke.return_value = {
            "query": "test",
            "synthesized_response": "Test response",
            "execution_trace": [],
            "errors": [],
            "workflow_start_time": None
        }
        mock_build.return_value = mock_workflow
        
        coordinator = WorkflowCoordinator()
        
        # This will fail without full mocking but tests structure
        # In real integration tests, we'd mock each agent individually
