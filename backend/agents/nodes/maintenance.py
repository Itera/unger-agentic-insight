"""
Maintenance Agent - Work Order Retrieval via MCP

Fetches work order information from the Maintenance API via MCP protocol.
Extracts sensor names from graph results and queries work orders for those assets.
"""

from typing import Dict, Any, List
from agents.nodes.base import BaseAgent
from agents.state import AgentState
from agents.tools.mcp_client import MCPClient, MCPService


class MaintenanceAgent(BaseAgent):
    """
    Agent that retrieves work order information via Maintenance MCP.
    
    Uses MCP protocol to query the Maintenance API for work orders
    related to sensors/equipment identified by other agents.
    """
    
    def __init__(self):
        super().__init__("maintenance_agent")
        self.mcp_client = None
    
    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Fetch work orders for sensors from graph results.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary with work orders and affected sensors
        """
        # Initialize MCP client
        self.mcp_client = MCPClient(MCPService.MAINTENANCE)
        
        try:
            # Check MCP health
            is_healthy = await self.mcp_client.health_check()
            if not is_healthy:
                return {
                    "work_orders": [],
                    "sensors_checked": [],
                    "error": "Maintenance MCP server unavailable"
                }
            
            # Extract sensor names from graph results
            sensor_names = self._extract_sensor_names(state)
            
            if not sensor_names:
                return {
                    "work_orders": [],
                    "sensors_checked": [],
                    "message": "No sensors found to check for work orders"
                }
            
            # Limit to 10 sensors to avoid overload
            sensor_names = sensor_names[:10]
            
            # Fetch work orders for each sensor
            work_orders = await self._fetch_work_orders(sensor_names)
            
            return {
                "work_orders": work_orders,
                "sensors_checked": sensor_names,
                "work_order_count": len(work_orders)
            }
            
        finally:
            # Clean up
            if self.mcp_client:
                await self.mcp_client.close()
    
    def _extract_sensor_names(self, state: AgentState) -> List[str]:
        """
        Extract sensor names/tags from graph agent results.
        
        Args:
            state: Current workflow state
            
        Returns:
            List of sensor names/tags
        """
        graph_result = state.get("graph_result")
        if not graph_result:
            return []
        
        results = graph_result.get("results", [])
        sensor_names = []
        
        for result in results:
            # Try different possible field names (Cypher results use aliases like "s.tag")
            if "s.tag" in result:
                sensor_names.append(result["s.tag"])
            elif "tag" in result:
                sensor_names.append(result["tag"])
            elif "s.name" in result:
                sensor_names.append(result["s.name"])
            elif "name" in result:
                name = result["name"]
                if any(char.isdigit() for char in name):
                    sensor_names.append(name)
            
            # Also check nested properties
            if "properties" in result and isinstance(result["properties"], dict):
                props = result["properties"]
                if "tag" in props:
                    sensor_names.append(props["tag"])
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(sensor_names))
    
    async def _fetch_work_orders(self, sensor_names: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch work orders for multiple sensors via MCP.
        
        Args:
            sensor_names: List of sensor identifiers
            
        Returns:
            List of work order dictionaries
        """
        all_work_orders = []
        
        for sensor_name in sensor_names:
            try:
                # Call MCP tool to get work orders for this sensor
                result = await self.mcp_client.call_tool(
                    "get_work_orders_by_sensor",
                    {"sensor_name": sensor_name}
                )
                
                # Extract work orders from result
                work_orders = result.get("work_orders", [])
                
                # Add sensor context to each work order
                for wo in work_orders:
                    wo["sensor_name"] = sensor_name
                
                all_work_orders.extend(work_orders)
                
            except Exception as e:
                # Log error but continue with other sensors
                print(f"Failed to fetch work orders for {sensor_name}: {e}")
                continue
        
        return all_work_orders
    
    def _generate_summary(self, output: Dict[str, Any]) -> str:
        """Generate summary of maintenance agent results."""
        if "error" in output:
            return f"Maintenance check failed: {output['error']}"
        
        if "message" in output:
            return output["message"]
        
        wo_count = output.get("work_order_count", 0)
        sensor_count = len(output.get("sensors_checked", []))
        
        if wo_count == 0:
            return f"No work orders found for {sensor_count} sensors"
        elif wo_count == 1:
            return f"Found 1 work order across {sensor_count} sensors"
        else:
            return f"Found {wo_count} work orders across {sensor_count} sensors"
    
    def _store_output(self, state: AgentState, output: Dict[str, Any]) -> None:
        """Store maintenance results in state."""
        state["maintenance_result"] = output
