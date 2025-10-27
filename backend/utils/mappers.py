"""
Entity type mapping utilities

Helper functions for mapping between frontend entity types and Neo4j labels.
"""


def map_entity_type_to_neo4j_label(entity_type: str) -> str:
    """
    Map frontend entity types to actual Neo4j node labels
    
    Args:
        entity_type: Frontend entity type (e.g., "Area Sensors", "Equipment")
        
    Returns:
        Neo4j label string
    """
    type_mapping = {
        "Area Sensors": "Sensor",
        "Equipment Sensors": "Sensor", 
        "Equipment": "Equipment",
        "Sensor": "Sensor",
        "AssetArea": "AssetArea",
        "Tank": "Tank",
        "ProcessStep": "ProcessStep"
    }
    return type_mapping.get(entity_type, entity_type)
