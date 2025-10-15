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
            with self.driver.session() as session:
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
    
    def get_areas_by_plant(self, plant_id: str) -> List[Dict[str, Any]]:
        """
        Get all areas connected to a specific plant
        
        Args:
            plant_id: The plant identifier
            
        Returns:
            List of area node dictionaries
        """
        query = """
        MATCH (p:Plant {id: $plant_id})-[:CONTAINS]->(a:Area)
        RETURN a.id as id, a.name as name, a.description as description,
               labels(a) as labels
        ORDER BY a.name
        """
        return self.execute_query(query, {"plant_id": plant_id})
    
    def get_nodes_by_area(self, area_id: str) -> List[Dict[str, Any]]:
        """
        Get all nodes (equipment, sensors) connected to a specific area
        
        Args:
            area_id: The area identifier
            
        Returns:
            List of node dictionaries
        """
        query = """
        MATCH (a:Area {id: $area_id})-[r]->(n)
        RETURN n.id as id, n.name as name, n.description as description,
               labels(n) as labels, type(r) as relationship_type
        ORDER BY labels(n), n.name
        """
        return self.execute_query(query, {"area_id": area_id})
    
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


# Global instance
graph_service = GraphService()