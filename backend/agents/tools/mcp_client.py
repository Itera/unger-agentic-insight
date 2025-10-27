"""
Model Context Protocol (MCP) client for external service integration.

Provides a unified interface for agents to interact with MCP servers
(Maintenance API, ADX, and future services).
"""

import httpx
from typing import Dict, Any, List, Optional
from enum import Enum
import os


class MCPService(Enum):
    """Available MCP services."""
    MAINTENANCE = "maintenance"
    ADX = "adx"


class MCPClient:
    """
    Client for MCP protocol communication.
    
    Handles tool invocation, health checks, and error handling for MCP servers.
    """
    
    def __init__(self, service: MCPService, base_url: Optional[str] = None):
        """
        Initialize MCP client.
        
        Args:
            service: Which MCP service to connect to
            base_url: Override base URL (defaults to env var)
        """
        self.service = service
        self.base_url = base_url or self._get_default_url(service)
        self.client = httpx.AsyncClient(timeout=30.0)
    
    def _get_default_url(self, service: MCPService) -> str:
        """Get default URL from environment variables."""
        if service == MCPService.MAINTENANCE:
            return os.getenv("MAINTENANCE_MCP_URL", "http://localhost:8001")
        elif service == MCPService.ADX:
            return os.getenv("ADX_MCP_URL", "http://localhost:8002")
        else:
            raise ValueError(f"Unknown MCP service: {service}")
    
    async def health_check(self) -> bool:
        """
        Check if MCP server is healthy.
        
        Returns:
            True if server is responsive
        """
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception:
            return False
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available tools from MCP server.
        
        Returns:
            List of tool definitions
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/mcp",
                json={"method": "tools/list", "params": {}}
            )
            response.raise_for_status()
            result = response.json()
            return result.get("result", {}).get("tools", [])
        except Exception as e:
            raise RuntimeError(f"Failed to list tools from {self.service.value} MCP: {e}")
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call a specific tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to invoke
            arguments: Tool arguments
            
        Returns:
            Tool result dictionary
            
        Raises:
            RuntimeError: If tool invocation fails
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/mcp",
                json={
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments
                    }
                }
            )
            response.raise_for_status()
            result = response.json()
            
            # MCP protocol returns result in "result" field
            if "result" in result:
                return result["result"]
            elif "error" in result:
                raise RuntimeError(f"MCP tool error: {result['error']}")
            else:
                return result
                
        except httpx.HTTPError as e:
            raise RuntimeError(
                f"Failed to call {tool_name} on {self.service.value} MCP: {e}"
            )
        except Exception as e:
            raise RuntimeError(
                f"Unexpected error calling {tool_name} on {self.service.value} MCP: {e}"
            )
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Factory functions for convenience
def create_maintenance_client() -> MCPClient:
    """Create MCP client for Maintenance service."""
    return MCPClient(MCPService.MAINTENANCE)


def create_adx_client() -> MCPClient:
    """Create MCP client for ADX service."""
    return MCPClient(MCPService.ADX)
