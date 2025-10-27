"""
Graph API Router

Handles graph navigation endpoints for plants, areas, equipment, and sensors.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException

from utils.serializers import serialize_neo4j_data
from services.graph_service import graph_service


router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("/plants")
async def get_plants():
    """
    Get all plants in the graph
    
    Returns:
        Dictionary with list of plants
    """
    if not graph_service.is_connected():
        raise HTTPException(status_code=503, detail="Graph service not available")
    
    try:
        plants = graph_service.get_all_plants()
        return {"plants": serialize_neo4j_data(plants)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get plants: {str(e)}")


@router.get("/plants/{plant_name}/areas")
async def get_asset_areas_by_plant(plant_name: str):
    """
    Get all asset areas for a specific plant
    
    Args:
        plant_name: Name of the plant
        
    Returns:
        Dictionary with plant name and list of asset areas
    """
    if not graph_service.is_connected():
        raise HTTPException(status_code=503, detail="Graph service not available")
    
    try:
        areas = graph_service.get_asset_areas_by_plant(plant_name)
        return {"plant": plant_name, "asset_areas": serialize_neo4j_data(areas)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get areas: {str(e)}")


@router.get("/areas/{area_name}/equipment")
async def get_equipment_by_area(area_name: str):
    """
    Get all equipment for a specific asset area
    
    Args:
        area_name: Name of the asset area
        
    Returns:
        Dictionary with area name and list of equipment
    """
    if not graph_service.is_connected():
        raise HTTPException(status_code=503, detail="Graph service not available")
    
    try:
        equipment = graph_service.get_equipment_by_asset_area(area_name)
        return {"area": area_name, "equipment": equipment}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get equipment: {str(e)}")


@router.get("/areas/{area_name}/sensors/categorized")
async def get_categorized_sensors_by_area(area_name: str):
    """
    Get sensors categorized by connection type (equipment-connected vs area-only)
    
    Args:
        area_name: Name of the asset area
        
    Returns:
        Dictionary with area name and categorized sensors
    """
    if not graph_service.is_connected():
        raise HTTPException(status_code=503, detail="Graph service not available")
    
    try:
        categorized_sensors = graph_service.get_categorized_sensors_by_area(area_name)
        return {"area": area_name, "categorized_sensors": categorized_sensors}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get categorized sensors: {str(e)}")


@router.get("/context/{node_type}/{node_name}")
async def get_contextual_subgraph(node_type: str, node_name: str, max_depth: int = 2):
    """
    Get contextual subgraph for AI chat scoping
    
    Args:
        node_type: Type of the node (e.g., AssetArea, Equipment, Sensor)
        node_name: Name of the node
        max_depth: Maximum depth for graph traversal (default: 2)
        
    Returns:
        Contextual subgraph with central node and connected entities
    """
    if not graph_service.is_connected():
        raise HTTPException(status_code=503, detail="Graph service not available")
    
    try:
        context = graph_service.get_contextual_subgraph(node_name, node_type, max_depth)
        if not context.get("central_node"):
            raise HTTPException(status_code=404, detail=f"Node {node_name} not found")
        
        return serialize_neo4j_data(context)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get contextual subgraph: {str(e)}")


@router.get("/suggestions/{node_type}/{node_name}")
async def get_suggestions(node_type: str, node_name: str, max_suggestions: int = 6):
    """
    Get smart suggestions for related entities based on graph connections (US-018)
    
    Args:
        node_type: Type of the node
        node_name: Name of the node
        max_suggestions: Maximum number of suggestions to return (default: 6)
        
    Returns:
        Dictionary with suggestions for related entities
    """
    if not graph_service.is_connected():
        raise HTTPException(status_code=503, detail="Graph service not available")
    
    try:
        suggestions = graph_service.get_smart_suggestions(node_name, node_type, max_suggestions)
        return {
            "node_name": node_name,
            "node_type": node_type,
            "suggestions": serialize_neo4j_data(suggestions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")


@router.get("/search")
async def search_nodes(q: str, node_types: Optional[str] = None):
    """
    Search nodes by name or description
    
    Args:
        q: Search query string
        node_types: Optional comma-separated list of node types to filter by
        
    Returns:
        Dictionary with search results
    """
    if not graph_service.is_connected():
        raise HTTPException(status_code=503, detail="Graph service not available")
    
    try:
        types_list = node_types.split(',') if node_types else None
        results = graph_service.search_nodes(q, types_list)
        return {"query": q, "results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
