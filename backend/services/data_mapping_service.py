"""
Data Mapping Service

Maps Neo4j graph entities to sensor data from CSV files, creating connections
between graph nodes and actual sensor measurements/configurations.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
from services.graph_service import graph_service

logger = logging.getLogger(__name__)


class DataMappingService:
    """Service to map graph entities to sensor data"""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def extract_area_from_sensor_name(self, sensor_name: str, asset_path: str = None) -> Optional[str]:
        """
        Extract asset area identifier from sensor name or asset path
        
        Args:
            sensor_name: Sensor name (e.g., "7512TIC301_SP0.AUTOMANA.OP")
            asset_path: Asset path (e.g., "/Assets/T-plant/75-12/7512TIC301_SP0")
            
        Returns:
            Area identifier (e.g., "75-12") or None
        """
        # First try to extract from asset path if available
        if asset_path:
            path_match = re.search(r'/(\d{2}-\d{2})/', asset_path)
            if path_match:
                return path_match.group(1)
        
        # Fallback: extract from sensor name 
        # Pattern: first 4 digits, dash, next 2 digits (e.g., "7512" -> "75-12")
        name_match = re.match(r'(\d{2})(\d{2})', sensor_name)
        if name_match:
            return f"{name_match.group(1)}-{name_match.group(2)}"
            
        return None
    
    def get_sensor_configurations_by_area(self, area_id: str) -> List[Dict[str, Any]]:
        """
        Get all sensor configurations for a specific asset area
        
        Args:
            area_id: Asset area identifier (e.g., "75-12")
            
        Returns:
            List of sensor configuration dictionaries
        """
        with self.SessionLocal() as db:
            query = text("""
                SELECT record_id, name, description, tag_units, scan_frequency,
                       high_extreme, low_extreme, asset, item, function_name,
                       source_system, source_tag_type
                FROM tag_configuration 
                WHERE asset = :area_id OR item LIKE :item_pattern
                ORDER BY name
            """)
            
            results = db.execute(query, {
                "area_id": area_id,
                "item_pattern": f"%/{area_id}/%"
            }).fetchall()
            
            return [dict(row._mapping) for row in results]
    
    def get_sensor_data_by_name(self, sensor_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent sensor data for a specific sensor
        
        Args:
            sensor_name: Name of the sensor
            limit: Maximum number of records to return
            
        Returns:
            List of sensor data records
        """
        with self.SessionLocal() as db:
            query = text("""
                SELECT timestamp, name, value, unit, quality
                FROM hmi_sensor_data 
                WHERE name = :sensor_name
                ORDER BY timestamp DESC
                LIMIT :limit
            """)
            
            results = db.execute(query, {
                "sensor_name": sensor_name,
                "limit": limit
            }).fetchall()
            
            return [dict(row._mapping) for row in results]
    
    def map_graph_node_to_sensor_data(self, node_name: str, node_type: str) -> Dict[str, Any]:
        """
        Map a graph node to its associated sensor data
        
        Args:
            node_name: Name of the graph node
            node_type: Type of the graph node (AssetArea, Equipment, Sensor, etc.)
            
        Returns:
            Dictionary with mapped sensor configurations and recent data
        """
        mapped_data = {
            "node_name": node_name,
            "node_type": node_type,
            "sensor_configurations": [],
            "recent_sensor_data": [],
            "mapping_confidence": "unknown"
        }
        
        if node_type == "AssetArea":
            # Direct mapping for asset areas
            sensor_configs = self.get_sensor_configurations_by_area(node_name)
            mapped_data["sensor_configurations"] = sensor_configs
            mapped_data["mapping_confidence"] = "high" if sensor_configs else "low"
            
            # Get recent data for sensors in this area
            if sensor_configs:
                for config in sensor_configs[:5]:  # Limit to first 5 sensors
                    recent_data = self.get_sensor_data_by_name(config["name"], limit=10)
                    if recent_data:
                        mapped_data["recent_sensor_data"].extend(recent_data)
        
        elif node_type in ["Equipment", "Sensor"]:
            # Try to find sensors that match the equipment/sensor name
            area_id = self.extract_area_from_sensor_name(node_name)
            if area_id:
                with self.SessionLocal() as db:
                    query = text("""
                        SELECT record_id, name, description, tag_units, scan_frequency,
                               high_extreme, low_extreme, asset, item, function_name
                        FROM tag_configuration 
                        WHERE (name LIKE :node_pattern OR item LIKE :node_pattern)
                        AND (asset = :area_id OR item LIKE :area_pattern)
                        ORDER BY name
                    """)
                    
                    results = db.execute(query, {
                        "node_pattern": f"%{node_name}%",
                        "area_id": area_id,
                        "area_pattern": f"%/{area_id}/%"
                    }).fetchall()
                    
                    sensor_configs = [dict(row._mapping) for row in results]
                    mapped_data["sensor_configurations"] = sensor_configs
                    mapped_data["mapping_confidence"] = "high" if sensor_configs else "medium"
        
        return mapped_data
    
    def get_enriched_context_for_node(self, node_name: str, node_type: str) -> Dict[str, Any]:
        """
        Get enriched context combining graph relationships and sensor data
        
        Args:
            node_name: Name of the graph node
            node_type: Type of the graph node
            
        Returns:
            Combined context with graph and sensor data
        """
        # Get graph context
        graph_context = graph_service.get_contextual_subgraph(node_name, node_type, max_depth=1)
        
        # Get sensor data mapping
        sensor_mapping = self.map_graph_node_to_sensor_data(node_name, node_type)
        
        # Combine contexts
        enriched_context = {
            "node_info": {
                "name": node_name,
                "type": node_type,
                "graph_context": graph_context,
                "sensor_mapping": sensor_mapping
            },
            "connected_entities": [],
            "sensor_overview": {
                "total_sensors": len(sensor_mapping["sensor_configurations"]),
                "recent_data_points": len(sensor_mapping["recent_sensor_data"]),
                "mapping_confidence": sensor_mapping["mapping_confidence"]
            }
        }
        
        # Enrich connected entities with sensor data
        if graph_context and graph_context.get("connected_nodes"):
            for connected_node in graph_context["connected_nodes"]:
                node_sensor_data = self.map_graph_node_to_sensor_data(
                    connected_node["name"], 
                    connected_node["labels"][0] if connected_node.get("labels") else "Unknown"
                )
                
                enriched_entity = {
                    "graph_info": connected_node,
                    "sensor_data": node_sensor_data,
                    "has_sensor_data": len(node_sensor_data["sensor_configurations"]) > 0
                }
                
                enriched_context["connected_entities"].append(enriched_entity)
        
        return enriched_context
    
    def search_sensors_by_criteria(self, 
                                 area_id: Optional[str] = None, 
                                 sensor_type: Optional[str] = None,
                                 unit: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for sensors based on various criteria
        
        Args:
            area_id: Asset area to filter by
            sensor_type: Type of sensor (temperature, pressure, etc.)
            unit: Unit of measurement
            
        Returns:
            List of matching sensor configurations
        """
        conditions = []
        params = {}
        
        if area_id:
            conditions.append("(asset = :area_id OR item LIKE :area_pattern)")
            params["area_id"] = area_id
            params["area_pattern"] = f"%/{area_id}/%"
        
        if sensor_type:
            # Infer sensor type from name patterns
            type_patterns = {
                "temperature": ["TI", "TIC", "TC", "temp"],
                "pressure": ["PI", "PIC", "PC", "pressure", "trykk"],
                "level": ["LI", "LIC", "LC", "level", "nivå"],
                "flow": ["FI", "FIC", "FC", "flow", "mengde"],
                "current": ["EI", "current", "amper", "strøm"]
            }
            
            if sensor_type.lower() in type_patterns:
                patterns = type_patterns[sensor_type.lower()]
                pattern_conditions = []
                for i, pattern in enumerate(patterns):
                    pattern_key = f"pattern_{i}"
                    pattern_conditions.append(f"(name LIKE :{pattern_key} OR description LIKE :{pattern_key})")
                    params[pattern_key] = f"%{pattern}%"
                
                conditions.append(f"({' OR '.join(pattern_conditions)})")
        
        if unit:
            conditions.append("tag_units = :unit")
            params["unit"] = unit
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        with self.SessionLocal() as db:
            query = text(f"""
                SELECT record_id, name, description, tag_units, scan_frequency,
                       high_extreme, low_extreme, asset, item, function_name
                FROM tag_configuration 
                {where_clause}
                ORDER BY asset, name
            """)
            
            results = db.execute(query, params).fetchall()
            return [dict(row._mapping) for row in results]
    
    def get_data_quality_summary(self, area_id: str) -> Dict[str, Any]:
        """
        Get data quality summary for an asset area
        
        Args:
            area_id: Asset area identifier
            
        Returns:
            Data quality summary
        """
        sensor_configs = self.get_sensor_configurations_by_area(area_id)
        
        summary = {
            "area_id": area_id,
            "total_configured_sensors": len(sensor_configs),
            "sensors_with_data": 0,
            "data_quality_stats": {},
            "sensor_types": {}
        }
        
        with self.SessionLocal() as db:
            for config in sensor_configs:
                # Check if sensor has recent data
                data_query = text("""
                    SELECT COUNT(*) as count, 
                           AVG(CASE WHEN quality = 'Good' THEN 1 ELSE 0 END) * 100 as good_quality_pct
                    FROM hmi_sensor_data 
                    WHERE name = :sensor_name 
                    AND timestamp >= NOW() - INTERVAL '24 hours'
                """)
                
                result = db.execute(data_query, {"sensor_name": config["name"]}).fetchone()
                
                if result and result.count > 0:
                    summary["sensors_with_data"] += 1
                
                # Categorize sensor types
                sensor_name = config["name"]
                if any(x in sensor_name for x in ["TI", "TIC", "TC"]):
                    summary["sensor_types"]["Temperature"] = summary["sensor_types"].get("Temperature", 0) + 1
                elif any(x in sensor_name for x in ["PI", "PIC", "PC"]):
                    summary["sensor_types"]["Pressure"] = summary["sensor_types"].get("Pressure", 0) + 1
                elif any(x in sensor_name for x in ["LI", "LIC", "LC"]):
                    summary["sensor_types"]["Level"] = summary["sensor_types"].get("Level", 0) + 1
                elif any(x in sensor_name for x in ["FI", "FIC", "FC"]):
                    summary["sensor_types"]["Flow"] = summary["sensor_types"].get("Flow", 0) + 1
                elif any(x in sensor_name for x in ["EI", "EC"]):
                    summary["sensor_types"]["Electrical"] = summary["sensor_types"].get("Electrical", 0) + 1
                else:
                    summary["sensor_types"]["Other"] = summary["sensor_types"].get("Other", 0) + 1
        
        summary["data_coverage_pct"] = (summary["sensors_with_data"] / summary["total_configured_sensors"] * 100) if summary["total_configured_sensors"] > 0 else 0
        
        return summary


# Global instance
data_mapping_service = None

def initialize_data_mapping_service(database_url: str):
    """Initialize the global data mapping service instance"""
    global data_mapping_service
    data_mapping_service = DataMappingService(database_url)
    return data_mapping_service