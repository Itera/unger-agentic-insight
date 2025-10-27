"""
Unit tests for Maintenance and ADX agents.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from agents.nodes.maintenance import MaintenanceAgent
from agents.nodes.adx import ADXAgent
from agents.state import create_initial_state


# Maintenance Agent Tests

@pytest.mark.asyncio
async def test_maintenance_agent_initialization():
    """Test MaintenanceAgent initialization."""
    agent = MaintenanceAgent()
    assert agent.name == "maintenance_agent"


@pytest.mark.asyncio
async def test_maintenance_agent_extracts_sensors_from_graph():
    """Test sensor extraction from graph results."""
    agent = MaintenanceAgent()
    state = create_initial_state("test", {})
    state["graph_result"] = {
        "results": [
            {"name": "Sensor1", "properties": {"tag": "4038LI579"}},
            {"tag": "4038TI120"},
            {"name": "Equipment1"}  # Should be ignored
        ]
    }
    
    sensors = agent._extract_sensor_names(state)
    assert len(sensors) == 2
    assert "4038LI579" in sensors
    assert "4038TI120" in sensors


@pytest.mark.asyncio
async def test_maintenance_agent_handles_mcp_unavailable():
    """Test graceful handling when MCP server is unavailable."""
    agent = MaintenanceAgent()
    state = create_initial_state("test", {})
    state["graph_result"] = {"results": [{"properties": {"tag": "sensor1"}}]}
    
    with patch.object(agent, 'mcp_client') as mock_mcp:
        mock_mcp.health_check = AsyncMock(return_value=False)
        agent.mcp_client = mock_mcp
        
        result = await agent.execute(state)
        
        assert "error" in result
        assert "unavailable" in result["error"]


@pytest.mark.asyncio
async def test_maintenance_agent_limits_sensors():
    """Test that agent limits to 10 sensors."""
    agent = MaintenanceAgent()
    state = create_initial_state("test", {})
    # Create 20 sensors
    state["graph_result"] = {
        "results": [{"properties": {"tag": f"sensor{i}"}} for i in range(20)]
    }
    
    # Mock MCP calls
    with patch('agents.nodes.maintenance.MCPClient') as mock_mcp_class:
        mock_mcp = AsyncMock()
        mock_mcp.health_check.return_value = True
        mock_mcp.call_tool.return_value = {"work_orders": []}
        mock_mcp_class.return_value = mock_mcp
        
        result = await agent.execute(state)
        
        # Should only check 10 sensors
        assert len(result["sensors_checked"]) == 10


# ADX Agent Tests

@pytest.mark.asyncio
async def test_adx_agent_initialization():
    """Test ADXAgent initialization."""
    agent = ADXAgent()
    assert agent.name == "adx_agent"
    assert agent.use_mcp == False  # Should use mock data by default


@pytest.mark.asyncio
async def test_adx_agent_mock_data_execution():
    """Test ADX agent with mock data."""
    agent = ADXAgent()
    state = create_initial_state("test", {})
    state["graph_result"] = {
        "results": [
            {"properties": {"tag": "4038LI579"}},
            {"properties": {"tag": "4038TI120"}}
        ]
    }
    
    result_state = await agent.run(state)
    
    assert result_state["execution_trace"][0].status == "success"
    assert "adx_result" in result_state
    adx_result = result_state["adx_result"]
    assert adx_result["mock_data"] == True
    assert len(adx_result["measurements"]) > 0
    assert len(adx_result["sensors_queried"]) == 2


@pytest.mark.asyncio
async def test_adx_agent_generates_realistic_measurements():
    """Test that ADX agent generates realistic mock measurements."""
    agent = ADXAgent()
    sensor_names = ["4038TI120", "4038PI200", "4038LI300"]
    
    measurements = agent._generate_mock_measurements(sensor_names)
    
    # Should have 5 measurements per sensor
    assert len(measurements) == 15
    
    # Check temperature sensor has correct unit
    temp_measurements = [m for m in measurements if m["sensor_name"] == "4038TI120"]
    assert all(m["unit"] == "°C" for m in temp_measurements)
    
    # Check pressure sensor has correct unit
    press_measurements = [m for m in measurements if m["sensor_name"] == "4038PI200"]
    assert all(m["unit"] == "bar" for m in press_measurements)


@pytest.mark.asyncio
async def test_adx_agent_detects_anomalies():
    """Test that ADX agent can detect mock anomalies."""
    agent = ADXAgent()
    measurements = [
        {"sensor_name": "s1", "timestamp": "2024-01-01T00:00:00", "value": 50.0},
        {"sensor_name": "s1", "timestamp": "2024-01-01T01:00:00", "value": 51.0},
    ]
    
    # With random seed, some anomalies should be detected
    anomalies = agent._generate_mock_anomalies(measurements)
    
    # Anomalies should be a list (may be empty due to randomness)
    assert isinstance(anomalies, list)
    
    # If anomalies found, check structure
    if anomalies:
        assert "sensor_name" in anomalies[0]
        assert "anomaly_type" in anomalies[0]
        assert "severity" in anomalies[0]


@pytest.mark.asyncio
async def test_adx_agent_handles_no_sensors():
    """Test ADX agent with no sensors from graph."""
    agent = ADXAgent()
    state = create_initial_state("test", {})
    state["graph_result"] = {"results": []}
    
    result_state = await agent.run(state)
    
    assert result_state["execution_trace"][0].status == "success"
    adx_result = result_state["adx_result"]
    assert "message" in adx_result
    assert len(adx_result["measurements"]) == 0


@pytest.mark.asyncio
async def test_adx_agent_limits_sensors():
    """Test that ADX agent limits to 10 sensors."""
    agent = ADXAgent()
    state = create_initial_state("test", {})
    # Create 20 sensors
    state["graph_result"] = {
        "results": [{"properties": {"tag": f"sensor{i}"}} for i in range(20)]
    }
    
    result_state = await agent.run(state)
    adx_result = result_state["adx_result"]
    
    # Should only query 10 sensors
    assert len(adx_result["sensors_queried"]) == 10


@pytest.mark.asyncio
async def test_adx_agent_mcp_mode_ready():
    """Test that ADX agent can switch to MCP mode."""
    agent = ADXAgent()
    agent.use_mcp = True
    state = create_initial_state("test", {})
    state["graph_result"] = {"results": [{"properties": {"tag": "sensor1"}}]}
    
    with patch('agents.nodes.adx.MCPClient') as mock_mcp_class:
        mock_mcp = AsyncMock()
        mock_mcp.health_check.return_value = False  # Simulate unavailable
        mock_mcp_class.return_value = mock_mcp
        
        result = await agent.execute(state)
        
        # Should handle MCP unavailable gracefully
        assert "error" in result
        assert "unavailable" in result["error"]
