"""
ADX Agent - Azure Data Explorer Sensor Data Retrieval

Stub implementation that returns mock sensor data.
Ready for MCP integration when ADX MCP server is available.
"""

from typing import Dict, Any, List
import random
from datetime import datetime, timedelta
from agents.nodes.base import BaseAgent
from agents.state import AgentState
from agents.tools.mcp_client import MCPClient, MCPService


class ADXAgent(BaseAgent):
    """
    Agent that retrieves sensor data from Azure Data Explorer.
    
    Currently returns mock data. Will use MCP protocol when ADX MCP server
    is deployed and available.
    """
    
    def __init__(self):
        super().__init__("adx_agent")
        self.use_mcp = False  # Set to True when ADX MCP is ready
        self.mcp_client = None
    
    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Fetch sensor data for sensors from graph results.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary with sensor measurements and anomalies
        """
        if self.use_mcp:
            return await self._execute_via_mcp(state)
        else:
            return self._execute_with_mock_data(state)
    
    async def _execute_via_mcp(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute via MCP protocol (when available).
        
        Args:
            state: Current workflow state
            
        Returns:
            Sensor data from ADX
        """
        self.mcp_client = MCPClient(MCPService.ADX)
        
        try:
            # Check MCP health
            is_healthy = await self.mcp_client.health_check()
            if not is_healthy:
                return {
                    "measurements": [],
                    "anomalies": [],
                    "error": "ADX MCP server unavailable"
                }
            
            # Extract sensor names from graph results
            sensor_names = self._extract_sensor_names(state)
            
            if not sensor_names:
                return {
                    "measurements": [],
                    "anomalies": [],
                    "message": "No sensors found to query"
                }
            
            # Limit to 10 sensors
            sensor_names = sensor_names[:10]
            
            # Call MCP tool to get sensor data
            result = await self.mcp_client.call_tool(
                "get_sensor_data",
                {
                    "sensor_names": sensor_names,
                    "time_range": "24h"
                }
            )
            
            return {
                "measurements": result.get("measurements", []),
                "anomalies": result.get("anomalies", []),
                "sensors_queried": sensor_names
            }
            
        finally:
            if self.mcp_client:
                await self.mcp_client.close()
    
    def _execute_with_mock_data(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute with mock data (current implementation).
        
        Args:
            state: Current workflow state
            
        Returns:
            Mock sensor data
        """
        # Extract sensor names from graph results
        sensor_names = self._extract_sensor_names(state)
        
        if not sensor_names:
            return {
                "measurements": [],
                "anomalies": [],
                "message": "No sensors found to query",
                "mock_data": True
            }
        
        # Limit to 10 sensors
        sensor_names = sensor_names[:10]
        
        # Generate mock measurements
        measurements = self._generate_mock_measurements(sensor_names)
        
        # Detect mock anomalies (randomly flag 20% as anomalous)
        anomalies = self._generate_mock_anomalies(measurements)
        
        return {
            "measurements": measurements,
            "anomalies": anomalies,
            "sensors_queried": sensor_names,
            "mock_data": True
        }
    
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
            # Try different possible field names for sensors
            if "tag" in result:
                sensor_names.append(result["tag"])
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
    
    def _generate_mock_measurements(self, sensor_names: List[str]) -> List[Dict[str, Any]]:
        """
        Generate realistic mock sensor measurements.
        
        Args:
            sensor_names: List of sensor identifiers
            
        Returns:
            List of measurement dictionaries
        """
        measurements = []
        now = datetime.now()
        
        for sensor_name in sensor_names:
            # Generate 5 recent measurements per sensor
            for i in range(5):
                timestamp = now - timedelta(hours=i)
                
                # Generate value based on sensor type hint in name
                if any(temp in sensor_name.upper() for temp in ['T', 'TEMP', 'TI', 'TT']):
                    value = round(random.uniform(20.0, 80.0), 2)
                    unit = "°C"
                elif any(press in sensor_name.upper() for press in ['P', 'PRESS', 'PI', 'PT']):
                    value = round(random.uniform(1.0, 10.0), 2)
                    unit = "bar"
                elif any(level in sensor_name.upper() for level in ['L', 'LEVEL', 'LI', 'LT']):
                    value = round(random.uniform(0.0, 100.0), 2)
                    unit = "%"
                else:
                    value = round(random.uniform(0.0, 100.0), 2)
                    unit = "units"
                
                measurements.append({
                    "sensor_name": sensor_name,
                    "timestamp": timestamp.isoformat(),
                    "value": value,
                    "unit": unit,
                    "quality": "Good" if random.random() > 0.1 else "Uncertain"
                })
        
        return measurements
    
    def _generate_mock_anomalies(self, measurements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate mock anomalies from measurements.
        
        Args:
            measurements: List of measurements
            
        Returns:
            List of anomaly dictionaries
        """
        anomalies = []
        
        # Group measurements by sensor
        sensors = {}
        for m in measurements:
            sensor_name = m["sensor_name"]
            if sensor_name not in sensors:
                sensors[sensor_name] = []
            sensors[sensor_name].append(m)
        
        # Check each sensor for anomalies (20% chance)
        for sensor_name, sensor_measurements in sensors.items():
            if random.random() < 0.2:  # 20% chance of anomaly
                latest = sensor_measurements[0]
                anomalies.append({
                    "sensor_name": sensor_name,
                    "timestamp": latest["timestamp"],
                    "value": latest["value"],
                    "anomaly_type": random.choice(["spike", "drop", "out_of_range"]),
                    "severity": random.choice(["low", "medium", "high"])
                })
        
        return anomalies
    
    def _generate_summary(self, output: Dict[str, Any]) -> str:
        """Generate summary of ADX agent results."""
        if "error" in output:
            return f"ADX query failed: {output['error']}"
        
        if "message" in output:
            return output["message"]
        
        measurement_count = len(output.get("measurements", []))
        anomaly_count = len(output.get("anomalies", []))
        mock_note = " (mock data)" if output.get("mock_data") else ""
        
        if anomaly_count > 0:
            return f"Retrieved {measurement_count} measurements, found {anomaly_count} anomalies{mock_note}"
        else:
            return f"Retrieved {measurement_count} measurements, no anomalies detected{mock_note}"
    
    def _store_output(self, state: AgentState, output: Dict[str, Any]) -> None:
        """Store ADX results in state."""
        state["adx_result"] = output
