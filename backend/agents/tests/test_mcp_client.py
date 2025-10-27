"""
Unit tests for MCP client.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from agents.tools.mcp_client import MCPClient, MCPService, create_maintenance_client, create_adx_client


@pytest.mark.asyncio
async def test_mcp_client_initialization():
    """Test MCP client initialization with default URLs."""
    client = MCPClient(MCPService.MAINTENANCE)
    
    assert client.service == MCPService.MAINTENANCE
    assert "localhost" in client.base_url or "MAINTENANCE_MCP_URL" in str(client.base_url)
    assert client.client is not None
    
    await client.close()


@pytest.mark.asyncio
async def test_mcp_client_custom_url():
    """Test MCP client with custom base URL."""
    custom_url = "http://custom-mcp-server:9000"
    client = MCPClient(MCPService.ADX, base_url=custom_url)
    
    assert client.base_url == custom_url
    
    await client.close()


@pytest.mark.asyncio
async def test_health_check_success():
    """Test successful health check."""
    client = MCPClient(MCPService.MAINTENANCE)
    
    # Mock successful health check
    with patch.object(client.client, 'get', new_callable=AsyncMock) as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        is_healthy = await client.health_check()
        
        assert is_healthy is True
        mock_get.assert_called_once()
    
    await client.close()


@pytest.mark.asyncio
async def test_health_check_failure():
    """Test failed health check."""
    client = MCPClient(MCPService.ADX)
    
    # Mock failed health check
    with patch.object(client.client, 'get', new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.ConnectError("Connection refused")
        
        is_healthy = await client.health_check()
        
        assert is_healthy is False
    
    await client.close()


@pytest.mark.asyncio
async def test_list_tools():
    """Test listing available tools from MCP server."""
    client = MCPClient(MCPService.MAINTENANCE)
    
    mock_tools = [
        {"name": "get_work_orders", "description": "Get work orders"},
        {"name": "get_asset_details", "description": "Get asset info"}
    ]
    
    with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": {"tools": mock_tools}}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        tools = await client.list_tools()
        
        assert len(tools) == 2
        assert tools[0]["name"] == "get_work_orders"
        mock_post.assert_called_once()
    
    await client.close()


@pytest.mark.asyncio
async def test_call_tool_success():
    """Test successful tool invocation."""
    client = MCPClient(MCPService.MAINTENANCE)
    
    mock_result = {
        "work_orders": [
            {"id": 1, "description": "Test WO"}
        ]
    }
    
    with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": mock_result}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        result = await client.call_tool("get_work_orders", {"status": 2})
        
        assert "work_orders" in result
        assert len(result["work_orders"]) == 1
        
        # Verify request format
        call_args = mock_post.call_args
        request_json = call_args[1]["json"]
        assert request_json["method"] == "tools/call"
        assert request_json["params"]["name"] == "get_work_orders"
        assert request_json["params"]["arguments"]["status"] == 2
    
    await client.close()


@pytest.mark.asyncio
async def test_call_tool_error():
    """Test tool invocation with error response."""
    client = MCPClient(MCPService.ADX)
    
    with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": "Tool not found"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        with pytest.raises(RuntimeError, match="MCP tool error"):
            await client.call_tool("invalid_tool", {})
    
    await client.close()


@pytest.mark.asyncio
async def test_call_tool_http_error():
    """Test tool invocation with HTTP error."""
    client = MCPClient(MCPService.MAINTENANCE)
    
    with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.HTTPError("Server error")
        
        with pytest.raises(RuntimeError, match="Failed to call"):
            await client.call_tool("get_work_orders", {})
    
    await client.close()


@pytest.mark.asyncio
async def test_context_manager():
    """Test MCP client as async context manager."""
    async with MCPClient(MCPService.MAINTENANCE) as client:
        assert client.client is not None
    
    # Client should be closed after context exit
    # (We can't easily verify this without accessing internals)


def test_factory_functions():
    """Test convenience factory functions."""
    maintenance_client = create_maintenance_client()
    assert maintenance_client.service == MCPService.MAINTENANCE
    
    adx_client = create_adx_client()
    assert adx_client.service == MCPService.ADX
