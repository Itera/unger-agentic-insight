"""
Model Context Protocol (MCP) client for external service integration.

Provides a unified interface for agents to interact with MCP servers
(Maintenance API, ADX, and future services) using the official MCP SDK.
"""

import os
from typing import Dict, Any, List, Optional
from enum import Enum

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client


class MCPService(Enum):
    """Available MCP services."""
    MAINTENANCE = "maintenance"
    ADX = "adx"


class MCPClient:
    """
    Client for MCP protocol communication using official SDK.
    
    Handles tool invocation, health checks, and error handling for MCP servers
    using the official MCP SDK with SSE transport.
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
        self.session: Optional[ClientSession] = None
        self._sse_context = None
        self._session_context = None
    
    def _get_default_url(self, service: MCPService) -> str:
        """Get default URL from environment variables."""
        if service == MCPService.MAINTENANCE:
            return os.getenv("MAINTENANCE_MCP_URL", "http://localhost:8001")
        elif service == MCPService.ADX:
            return os.getenv("ADX_MCP_URL", "http://localhost:8002")
        else:
            raise ValueError(f"Unknown MCP service: {service}")
    
    async def _ensure_connected(self) -> None:
        """Ensure MCP session is connected."""
        if self.session is not None:
            return
        
        try:
            # Use SSE client for HTTP transport
            self._sse_context = sse_client(url=f"{self.base_url}/mcp")
            self._session_context, session = await self._sse_context.__aenter__()
            
            # Initialize the session
            await session.initialize()
            self.session = session
            
        except Exception as e:
            raise RuntimeError(f"Failed to connect to {self.service.value} MCP: {e}")
    
    async def health_check(self) -> bool:
        """
        Check if MCP server is healthy.
        
        Returns:
            True if server is responsive
        """
        try:
            await self._ensure_connected()
            return self.session is not None
        except Exception:
            return False
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available tools from MCP server.
        
        Returns:
            List of tool definitions
        """
        try:
            await self._ensure_connected()
            tools_list = await self.session.list_tools()
            
            # Convert Tool objects to dicts
            return [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                }
                for tool in tools_list.tools
            ]
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
            await self._ensure_connected()
            
            # Call tool using MCP SDK
            result = await self.session.call_tool(tool_name, arguments)
            
            # Extract content from result
            if result.content:
                # MCP returns a list of content items
                if len(result.content) == 1:
                    content_item = result.content[0]
                    if hasattr(content_item, 'text'):
                        # Try to parse as JSON if it's a text response
                        import json
                        try:
                            return json.loads(content_item.text)
                        except:
                            return {"result": content_item.text}
                    return {"result": str(content_item)}
                else:
                    return {"content": [str(item) for item in result.content]}
            
            return {"success": True}
                
        except Exception as e:
            raise RuntimeError(
                f"Failed to call {tool_name} on {self.service.value} MCP: {e}"
            )
    
    async def close(self):
        """Close MCP session."""
        if self._session_context:
            try:
                await self._session_context.__aexit__(None, None, None)
            except:
                pass
        if self._sse_context:
            try:
                await self._sse_context.__aexit__(None, None, None)
            except:
                pass
        self.session = None
        self._session_context = None
        self._sse_context = None
    
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
