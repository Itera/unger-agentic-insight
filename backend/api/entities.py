"""
Entities API Router

Handles entity detail and relationship endpoints.
"""

from fastapi import APIRouter, HTTPException

from utils.serializers import serialize_neo4j_data
from utils.mappers import map_entity_type_to_neo4j_label
from services.graph_service import graph_service


router = APIRouter(prefix="/api/entities", tags=["entities"])


@router.get("/{entity_type}/{entity_id}")
async def get_entity_details(entity_type: str, entity_id: str):
    """
    Get detailed information about a specific entity
    
    Args:
        entity_type: Type of entity (e.g., Equipment, Sensor, AssetArea)
        entity_id: ID or name of the entity
        
    Returns:
        Entity details including properties and labels
    """
    if not graph_service.is_connected():
        raise HTTPException(status_code=503, detail="Graph service not available")
    
    try:
        # Map UI entity types to Neo4j labels
        neo4j_label = map_entity_type_to_neo4j_label(entity_type)
        
        # Try to get real entity data from Neo4j
        # First try by ID, then by name if ID doesn't work
        query = f"""
        MATCH (e:{neo4j_label})
        WHERE e.id = $entity_id OR e.name = $entity_id OR e.equipment_id = $entity_id OR e.tag = $entity_id
        RETURN e.id as id, e.name as name, e.description as description,
               labels(e) as labels, properties(e) as properties
        LIMIT 1
        """
        results = graph_service.execute_query(query, {"entity_id": entity_id})
        
        if not results:
            raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")
        
        entity_data = results[0]
        return serialize_neo4j_data({
            "id": entity_data.get("id"),
            "name": entity_data.get("name"),
            "description": entity_data.get("description"),
            "type": entity_type,
            "labels": entity_data.get("labels", []),
            "properties": entity_data.get("properties", {})
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get entity details: {str(e)}")


@router.get("/{entity_type}/{entity_id}/connected")
async def get_entity_connected_entities(entity_type: str, entity_id: str):
    """
    Get all entities connected to a specific entity
    
    Args:
        entity_type: Type of entity
        entity_id: ID or name of the entity
        
    Returns:
        Dictionary of connected entities grouped by type
    """
    if not graph_service.is_connected():
        raise HTTPException(status_code=503, detail="Graph service not available")
    
    try:
        # Map UI entity types to Neo4j labels
        neo4j_label = map_entity_type_to_neo4j_label(entity_type)
        
        # Get connected entities from Neo4j
        query = f"""
        MATCH (e:{neo4j_label})-[r]-(connected)
        WHERE e.id = $entity_id OR e.name = $entity_id OR e.equipment_id = $entity_id OR e.tag = $entity_id
        WITH connected, type(r) as rel_type, labels(connected) as connected_labels
        RETURN connected.id as id, connected.name as name, connected.description as description,
               connected_labels as labels, properties(connected) as properties,
               rel_type
        ORDER BY connected_labels, connected.name
        """
        results = graph_service.execute_query(query, {"entity_id": entity_id})
        
        # Group entities by their labels
        entity_groups = {}
        for result in results:
            # Get primary label (skip generic ones)
            primary_label = None
            for label in result.get('labels', []):
                if label not in ['Node']:  # Skip generic labels
                    primary_label = label
                    break
            
            if primary_label:
                if primary_label not in entity_groups:
                    entity_groups[primary_label] = []
                
                entity_groups[primary_label].append({
                    "id": result.get("id"),
                    "name": result.get("name"),
                    "description": result.get("description"),
                    "labels": result.get("labels", []),
                    "properties": result.get("properties", {}),
                    "relationship_type": result.get("rel_type")
                })
        
        return serialize_neo4j_data(entity_groups)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get connected entities: {str(e)}")
