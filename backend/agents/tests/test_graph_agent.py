"""
Unit tests for GraphAgent.
"""

import pytest
from unittest.mock import MagicMock, patch
from agents.nodes.graph import GraphAgent
from agents.state import create_initial_state


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "MATCH (s:Sensor) RETURN s.name LIMIT 10"
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_graph_service():
    """Mock graph service for testing."""
    with patch('agents.nodes.graph.graph_service') as mock:
        mock.is_connected.return_value = True
        mock.execute_query.return_value = [
            {"name": "Sensor1", "properties": {"tag": "4038LI579"}},
            {"name": "Sensor2", "properties": {"tag": "4038TI120"}}
        ]
        yield mock


@pytest.mark.asyncio
async def test_graph_agent_initialization(mock_graph_service):
    """Test GraphAgent initialization."""
    with patch('agents.nodes.graph.get_openai_client', return_value=MagicMock()):
        agent = GraphAgent()
        assert agent.name == "graph_agent"


@pytest.mark.asyncio
async def test_graph_agent_initialization_fails_without_graph(mock_openai_client):
    """Test GraphAgent fails if graph service not connected."""
    with patch('agents.nodes.graph.graph_service') as mock_service:
        mock_service.is_connected.return_value = False
        with patch('agents.nodes.graph.get_openai_client', return_value=mock_openai_client):
            with pytest.raises(RuntimeError, match="Graph service not connected"):
                GraphAgent()


@pytest.mark.asyncio
async def test_graph_agent_successful_execution(mock_openai_client, mock_graph_service):
    """Test successful query generation and execution."""
    with patch('agents.nodes.graph.get_openai_client', return_value=mock_openai_client):
        agent = GraphAgent()
        state = create_initial_state("What sensors are there?", {})
        
        result_state = await agent.run(state)
        
        # Check execution trace
        assert len(result_state["execution_trace"]) == 1
        trace = result_state["execution_trace"][0]
        assert trace.status == "success"
        assert "graph_agent" in trace.agent_name
        
        # Check results stored in state
        assert "graph_result" in result_state
        graph_result = result_state["graph_result"]
        assert "cypher_query" in graph_result
        assert "results" in graph_result
        assert "result_count" in graph_result
        assert graph_result["result_count"] == 2


@pytest.mark.asyncio
async def test_graph_agent_cypher_generation(mock_openai_client, mock_graph_service):
    """Test Cypher query generation from natural language."""
    with patch('agents.nodes.graph.get_openai_client', return_value=mock_openai_client):
        agent = GraphAgent()
        
        cypher = agent._generate_cypher("Show me all sensors")
        
        assert "MATCH" in cypher
        assert "LIMIT" in cypher
        # Should have removed markdown code fences
        assert "```" not in cypher


@pytest.mark.asyncio
async def test_graph_agent_removes_markdown_fences(mock_graph_service):
    """Test that markdown code fences are removed from Cypher."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    # LLM returns query with markdown fences
    mock_response.choices[0].message.content = "```cypher\nMATCH (s:Sensor) RETURN s\n```"
    mock_client.chat.completions.create.return_value = mock_response
    
    with patch('agents.nodes.graph.get_openai_client', return_value=mock_client):
        agent = GraphAgent()
        cypher = agent._generate_cypher("Show sensors")
        
        # Fences should be removed
        assert "```" not in cypher
        assert cypher == "MATCH (s:Sensor) RETURN s"


@pytest.mark.asyncio
async def test_graph_agent_limits_results(mock_openai_client, mock_graph_service):
    """Test that results are limited to 50 items."""
    # Mock 100 results
    large_results = [{"name": f"Sensor{i}"} for i in range(100)]
    mock_graph_service.execute_query.return_value = large_results
    
    with patch('agents.nodes.graph.get_openai_client', return_value=mock_openai_client):
        agent = GraphAgent()
        state = create_initial_state("Get all sensors", {})
        
        result_state = await agent.run(state)
        graph_result = result_state["graph_result"]
        
        # Should be limited to 50
        assert graph_result["result_count"] == 50
        assert len(graph_result["results"]) == 50


@pytest.mark.asyncio
async def test_graph_agent_handles_empty_results(mock_openai_client, mock_graph_service):
    """Test handling of queries that return no results."""
    mock_graph_service.execute_query.return_value = []
    
    with patch('agents.nodes.graph.get_openai_client', return_value=mock_openai_client):
        agent = GraphAgent()
        state = create_initial_state("Find nonexistent sensors", {})
        
        result_state = await agent.run(state)
        
        # Should succeed with empty results
        assert result_state["execution_trace"][0].status == "success"
        assert result_state["graph_result"]["result_count"] == 0
        assert "No results found" in result_state["execution_trace"][0].summary


@pytest.mark.asyncio
async def test_graph_agent_handles_cypher_error(mock_openai_client, mock_graph_service):
    """Test error handling for invalid Cypher queries."""
    mock_graph_service.execute_query.side_effect = Exception("Invalid Cypher syntax")
    
    with patch('agents.nodes.graph.get_openai_client', return_value=mock_openai_client):
        agent = GraphAgent()
        state = create_initial_state("Bad query", {})
        
        result_state = await agent.run(state)
        
        # Should record error
        assert result_state["execution_trace"][0].status == "error"
        assert len(result_state["errors"]) == 1
        assert "graph_agent" in result_state["errors"][0]
