"""
Model Context Protocol (MCP) client for external service integration.

Provides a unified interface for agents to interact with MCP servers
(Maintenance API, ADX, and future services) using the official MCP SDK.
"""

import os
from typing import Dict, Any, List, Optional
from enum import Enum

import httpx
import json


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
        self.session_id: Optional[str] = None
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self._message_id = 0
    
    def _get_default_url(self, service: MCPService) -> str:
        """Get default URL from environment variables."""
        if service == MCPService.MAINTENANCE:
            return os.getenv("MAINTENANCE_MCP_URL", "http://localhost:8001")
        elif service == MCPService.ADX:
            return os.getenv("ADX_MCP_URL", "http://localhost:8002")
        else:
            raise ValueError(f"Unknown MCP service: {service}")
    
    def _get_next_id(self) -> int:
        """Get next message ID."""
        self._message_id += 1
        return self._message_id
    
    async def _ensure_connected(self) -> None:
        """Ensure MCP session is initialized using Streamable HTTP protocol."""
        if self.session_id is not None:
            return
        
        try:
            print(f"[MCP] Initializing session with {self.base_url}/mcp")
            
            # Initialize MCP session via POST
            response = await self.http_client.post(
                f"{self.base_url}/mcp",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                },
                json={
                    "jsonrpc": "2.0",
                    "id": self._get_next_id(),
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {
                            "name": "unger-agentic-insight",
                            "version": "1.0.0"
                        }
                    }
                }
            )
            response.raise_for_status()
            
            # Extract session ID from response headers
            self.session_id = response.headers.get("mcp-session-id")
            if not self.session_id:
                raise RuntimeError("No session ID in response headers")
            
            print(f"[MCP] Session initialized: {self.session_id}")
            
        except Exception as e:
            print(f"[MCP] Failed to initialize: {e}")
            raise RuntimeError(f"Failed to connect to {self.service.value} MCP: {e}")
    
    async def health_check(self) -> bool:
        """
        Check if MCP server is healthy.
        
        Returns:
            True if server is responsive
        """
        try:
            print(f"[MCP] Starting health check for {self.service.value}...")
            await self._ensure_connected()
            result = self.session_id is not None
            print(f"[MCP] Health check result: {result}, session_id: {self.session_id}")
            return result
        except Exception as e:
            print(f"[MCP] Health check exception: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available tools from MCP server.
        
        Returns:
            List of tool definitions
        """
        try:
            await self._ensure_connected()
            
            response = await self.http_client.post(
                f"{self.base_url}/mcp",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                    "mcp-session-id": self.session_id
                },
                json={
                    "jsonrpc": "2.0",
                    "id": self._get_next_id(),
                    "method": "tools/list",
                    "params": {}
                }
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
            await self._ensure_connected()
            
            print(f"[MCP] Calling tool: {tool_name}")
            
            # Call tool via POST with session ID
            response = await self.http_client.post(
                f"{self.base_url}/mcp",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                    "mcp-session-id": self.session_id
                },
                json={
                    "jsonrpc": "2.0",
                    "id": self._get_next_id(),
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments
                    }
                }
            )
            response.raise_for_status()
            result = response.json()
            
            # Extract result from JSON-RPC response
            if "result" in result:
                tool_result = result["result"]
                # MCP tools return {"content": [{"type": "text", "text": "..."}]}
                if isinstance(tool_result, dict) and "content" in tool_result:
                    content_items = tool_result["content"]
                    if content_items and len(content_items) > 0:
                        first_item = content_items[0]
                        if isinstance(first_item, dict) and "text" in first_item:
                            text = first_item["text"]
                            # Try to parse as JSON
                            try:
                                return json.loads(text)
                            except:
                                return {"result": text}
                return tool_result
            elif "error" in result:
                raise RuntimeError(f"MCP tool error: {result['error']}")
            
            return {}
                
        except Exception as e:
            print(f"[MCP] Tool call failed: {e}")
            raise RuntimeError(
                f"Failed to call {tool_name} on {self.service.value} MCP: {e}"
            )
    
    async def close(self):
        """Close MCP session and HTTP client."""
        if self.http_client:
            try:
                await self.http_client.aclose()
            except:
                pass
        self.session_id = None
    
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
