"""
Neo4j Graph Database Service

Provides connection management and basic graph operations for the factory asset graph.
Supports Plants -> Areas -> Equipment -> Sensors hierarchy with non-hierarchical relationships.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from neo4j import GraphDatabase, Driver, Session
from neo4j.exceptions import ServiceUnavailable, AuthError
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class GraphService:
    """Service class for Neo4j graph database operations"""
    
    def __init__(self):
        self.driver: Optional[Driver] = None
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.username = os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")
        self.database = os.getenv("NEO4J_DATABASE", "neo4j")
        
    def connect(self) -> bool:
        """
        Establish connection to Neo4j database
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.driver = GraphDatabase.driver(
                self.uri, 
                auth=(self.username, self.password)
            )
            
            # Test connection
            self.driver.verify_connectivity()
            logger.info(f"Successfully connected to Neo4j at {self.uri}")
            return True
            
        except ServiceUnavailable as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            return False
        except AuthError as e:
            logger.error(f"Authentication failed for Neo4j: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to Neo4j: {e}")
            return False
    
    def close(self):
        """Close the Neo4j driver connection"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    def is_connected(self) -> bool:
        """
        Check if connection to Neo4j is active
        
        Returns:
            bool: True if connected, False otherwise
        """
        try:
            if not self.driver:
                return False
            self.driver.verify_connectivity()
            return True
        except:
            return False
    
    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query and return results
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            
        Returns:
            List of result records as dictionaries
        """
        if not self.driver:
            raise RuntimeError("Neo4j driver not initialized. Call connect() first.")
        
        results = []
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(query, parameters or {})
                results = [record.data() for record in result]
                
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            logger.error(f"Query: {query}")
            raise
        
        return results
    
    def get_all_plants(self) -> List[Dict[str, Any]]:
        """
        Get all plant nodes (S-plant, T-plant)
        
        Returns:
            List of plant node dictionaries
        """
        query = """
        MATCH (p:Plant)
        RETURN p.id as id, p.name as name, p.type as type, 
               p.description as description, labels(p) as labels
        ORDER BY p.name
        """
        return self.execute_query(query)
    
    def get_asset_areas_by_plant(self, plant_name: str) -> List[Dict[str, Any]]:
        """
        Get all asset areas connected to a specific plant
        
        Args:
            plant_name: The plant name (e.g., 'S-Plant', 'T-Plant')
            
        Returns:
            List of AssetArea node dictionaries
        """
        query = """
        MATCH (p:Plant {name: $plant_name})-[r*1..2]->(a:AssetArea)
        RETURN a.id as id, a.name as name, a.description as description,
               labels(a) as labels, properties(a) as properties
        ORDER BY a.name
        """
        return self.execute_query(query, {"plant_name": plant_name})
    
    def get_equipment_by_asset_area(self, area_name: str) -> List[Dict[str, Any]]:
        """
        Get all equipment connected to a specific asset area
        
        Args:
            area_name: The asset area name
            
        Returns:
            List of equipment node dictionaries
        """
        query = """
        MATCH (a:AssetArea {name: $area_name})-[:CONTAINS]->(e:Equipment)
        RETURN e.id as id, e.name as name, e.description as description,
               labels(e) as labels, properties(e) as properties
        ORDER BY e.name
        """
        return self.execute_query(query, {"area_name": area_name})
    
    def get_sensors_by_asset_area(self, area_name: str) -> List[Dict[str, Any]]:
        """
        Get all sensors connected to a specific asset area
        This includes sensors directly connected to the area AND sensors connected via equipment
        
        Args:
            area_name: The asset area name
            
        Returns:
            List of sensor node dictionaries  
        """
        query = """
        MATCH (a:AssetArea {name: $area_name})-[:HAS_SENSOR]->(s:Sensor)
        RETURN s.id as id, s.name as name, s.description as description,
               labels(s) as labels, properties(s) as properties
        ORDER BY s.properties.tag, s.name
        """
        return self.execute_query(query, {"area_name": area_name})
    
    def get_sensors_by_equipment(self, equipment_name: str) -> List[Dict[str, Any]]:
        """
        Get all sensors connected to a specific equipment
        
        Args:
            equipment_name: The equipment name
            
        Returns:
            List of sensor node dictionaries
        """
        query = """
        MATCH path = (e:Equipment {name: $equipment_name})-[r*1..2]->(s:Sensor)
        RETURN s.id as id, s.name as name, s.description as description,
               labels(s) as labels, 
               [rel in relationships(path) | type(rel)] as relationship_types,
               length(path) as distance,
               properties(s) as properties
        ORDER BY distance, s.name
        """
        return self.execute_query(query, {"equipment_name": equipment_name})
    
    def get_categorized_sensors_by_area(self, area_name: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get sensors categorized by their connection type (equipment-connected vs area-only)
        
        Args:
            area_name: The asset area name
            
        Returns:
            Dictionary with 'equipment_connected' and 'area_only' sensor lists
        """
        # Get all area sensors
        area_sensors_query = """
        MATCH (a:AssetArea {name: $area_name})-[:HAS_SENSOR]->(s:Sensor)
        RETURN s.id as id, s.name as name, s.description as description,
               labels(s) as labels, properties(s) as properties
        ORDER BY s.properties.tag, s.name
        """
        area_sensors = self.execute_query(area_sensors_query, {"area_name": area_name})
        
        # Get equipment-connected sensors in this area
        equipment_sensors_query = """
        MATCH (a:AssetArea {name: $area_name})-[:CONTAINS]->(e:Equipment)
        MATCH (e)-[r*1..2]->(s:Sensor)
        WITH DISTINCT s, e
        RETURN s.id as id, s.name as name, s.description as description,
               labels(s) as labels, properties(s) as properties,
               e.properties.equipment_name as equipment_name
        ORDER BY s.properties.tag, s.name
        """
        equipment_sensors = self.execute_query(equipment_sensors_query, {"area_name": area_name})
        
        # Create a set of equipment-connected sensor tags for quick lookup
        equipment_sensor_tags = {sensor['properties'].get('tag') for sensor in equipment_sensors if sensor['properties']}
        
        # Categorize sensors
        area_only_sensors = []
        equipment_connected_sensors = []
        
        for sensor in area_sensors:
            sensor_tag = sensor['properties'].get('tag') if sensor['properties'] else None
            classification = sensor['properties'].get('classification') if sensor['properties'] else None
            
            # Check if sensor is equipment-connected via graph relationships OR classification
            if sensor_tag in equipment_sensor_tags or classification == 'EQUIPMENT':
                equipment_connected_sensors.append(sensor)
            else:
                area_only_sensors.append(sensor)
        
        return {
            'equipment_connected': equipment_connected_sensors,
            'area_only': area_only_sensors
        }
    
    def get_connected_nodes(self, node_id: str, max_depth: int = 1) -> List[Dict[str, Any]]:
        """
        Get nodes connected to a specific node up to max_depth
        
        Args:
            node_id: The source node identifier
            max_depth: Maximum relationship depth to traverse
            
        Returns:
            List of connected node dictionaries with relationship info
        """
        query = """
        MATCH path = (n {id: $node_id})-[r*1..""" + str(max_depth) + """]->(connected)
        RETURN connected.id as id, connected.name as name, connected.description as description,
               labels(connected) as labels, length(path) as depth,
               [rel in relationships(path) | type(rel)] as relationship_path
        ORDER BY depth, labels(connected), connected.name
        """
        return self.execute_query(query, {"node_id": node_id})
    
    def get_node_details(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific node
        
        Args:
            node_id: The node identifier
            
        Returns:
            Node details dictionary or None if not found
        """
        query = """
        MATCH (n {id: $node_id})
        RETURN n.id as id, n.name as name, n.description as description,
               labels(n) as labels, properties(n) as properties
        """
        results = self.execute_query(query, {"node_id": node_id})
        return results[0] if results else None
    
    def search_nodes(self, search_term: str, node_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Search for nodes by name or description
        
        Args:
            search_term: Text to search for
            node_types: Optional list of node labels to filter by
            
        Returns:
            List of matching node dictionaries
        """
        label_filter = ""
        if node_types:
            label_conditions = [f"n:{label}" for label in node_types]
            label_filter = f"WHERE ({' OR '.join(label_conditions)}) AND "
        else:
            label_filter = "WHERE "
        
        query = f"""
        MATCH (n)
        {label_filter}(
            toLower(n.name) CONTAINS toLower($search_term) OR 
            toLower(n.description) CONTAINS toLower($search_term)
        )
        RETURN n.id as id, n.name as name, n.description as description,
               labels(n) as labels
        ORDER BY labels(n), n.name
        LIMIT 50
        """
        return self.execute_query(query, {"search_term": search_term})
    
    def get_all_asset_areas(self) -> List[Dict[str, Any]]:
        """
        Get all asset areas in the graph
        
        Returns:
            List of all AssetArea nodes
        """
        query = """
        MATCH (a:AssetArea)
        RETURN a.id as id, a.name as name, a.description as description,
               labels(a) as labels, properties(a) as properties
        ORDER BY a.name
        """
        return self.execute_query(query)
    
    def get_all_equipment(self) -> List[Dict[str, Any]]:
        """
        Get all equipment in the graph
        
        Returns:
            List of all Equipment nodes
        """
        query = """
        MATCH (e:Equipment)
        RETURN e.id as id, e.name as name, e.description as description,
               labels(e) as labels, properties(e) as properties
        ORDER BY e.name
        """
        return self.execute_query(query)
    
    def get_all_sensors(self) -> List[Dict[str, Any]]:
        """
        Get all sensors in the graph
        
        Returns:
            List of all Sensor nodes
        """
        query = """
        MATCH (s:Sensor)
        RETURN s.id as id, s.name as name, s.description as description,
               labels(s) as labels, properties(s) as properties
        ORDER BY s.name
        """
        return self.execute_query(query)
    
    def get_node_relationships(self, node_name: str, node_type: str) -> List[Dict[str, Any]]:
        """
        Get all relationships for a specific node
        
        Args:
            node_name: The node name
            node_type: The node type/label (Plant, AssetArea, Equipment, Sensor)
            
        Returns:
            List of relationship dictionaries with connected nodes
        """
        query = f"""
        MATCH (n:{node_type} {{name: $node_name}})-[r]-(connected)
        RETURN type(r) as relationship_type,
               startNode(r).name as start_node_name,
               endNode(r).name as end_node_name,
               connected.name as connected_name,
               labels(connected) as connected_labels,
               properties(connected) as connected_properties
        ORDER BY relationship_type, connected_name
        """
        return self.execute_query(query, {"node_name": node_name})
    
    def get_contextual_subgraph(self, node_name: str, node_type: str, max_depth: int = 2) -> Dict[str, Any]:
        """
        Get a contextual subgraph around a specific node for AI chat context
        
        Args:
            node_name: The central node name
            node_type: The node type/label
            max_depth: Maximum relationship depth to include
            
        Returns:
            Dictionary with central node and connected nodes for context
        """
        # Get the central node details
        central_query = f"""
        MATCH (n:{node_type} {{name: $node_name}})
        RETURN n.name as name, labels(n) as labels, properties(n) as properties
        """
        central_node = self.execute_query(central_query, {"node_name": node_name})
        
        # Get connected nodes within max_depth
        connected_query = f"""
        MATCH path = (n:{node_type} {{name: $node_name}})-[r*1..{max_depth}]-(connected)
        RETURN connected.name as name, 
               labels(connected) as labels,
               properties(connected) as properties,
               length(path) as depth,
               [rel in relationships(path) | type(rel)] as relationship_path
        ORDER BY depth, labels(connected), connected.name
        """
        connected_nodes = self.execute_query(connected_query, {"node_name": node_name})
        
        return {
            "central_node": central_node[0] if central_node else None,
            "connected_nodes": connected_nodes,
            "context_scope": f"{node_type}: {node_name}",
            "total_nodes": 1 + len(connected_nodes)
        }


# Global instance
graph_service = GraphService()
