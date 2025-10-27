"""
Maintenance API Router

Handles work order endpoints for sensors, equipment, and areas.
"""

from fastapi import APIRouter, HTTPException

from services.graph_service import graph_service
from utils.mappers import map_entity_type_to_neo4j_label
from core.dependencies import get_maintenance_service


router = APIRouter(prefix="/api", tags=["maintenance"])


@router.get("/sensors/{sensor_name}/work-orders")
async def get_sensor_work_orders(sensor_name: str):
    """
    Get work orders for a specific sensor
    
    Args:
        sensor_name: Name/tag of the sensor
        
    Returns:
        Dictionary with sensor name and list of work orders
    """
    maintenance_service = get_maintenance_service()
    if not maintenance_service:
        raise HTTPException(status_code=503, detail="Maintenance API service not available")
    
    try:
        work_orders = maintenance_service.get_work_orders_by_sensor(sensor_name)
        return {
            "sensor": sensor_name,
            "work_orders": [{
                "id": wo.id,
                "nr": wo.nr,
                "asset_id": wo.asset_id,
                "short_description": wo.short_description,
                "description": wo.description,
                "comment": wo.comment,
                "status": wo.status,
                "from_date": wo.from_date,
                "to_date": wo.to_date,
                "created_at": wo.created_at,
                "finished_date": wo.finished_date,
                "priority": wo.priority,
                "url": wo.url,
                "is_reactive_maintenance": wo.is_reactive_maintenance
            } for wo in work_orders],
            "count": len(work_orders)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get work orders: {str(e)}")


@router.get("/areas/{area_name}/work-orders")
async def get_area_work_orders(area_name: str):
    """
    Get all work orders for sensors within a specific area
    
    Args:
        area_name: Name of the asset area
        
    Returns:
        Dictionary with area name, sensors checked, and deduplicated work orders
    """
    maintenance_service = get_maintenance_service()
    if not maintenance_service:
        raise HTTPException(status_code=503, detail="Maintenance API service not available")
    
    if not graph_service.is_connected():
        raise HTTPException(status_code=503, detail="Graph service not available")
    
    try:
        # Get all sensors in the area
        sensors = graph_service.get_sensors_by_asset_area(area_name)
        if not sensors:
            return {
                "area": area_name,
                "work_orders": [],
                "count": 0,
                "message": "No sensors found in area"
            }
        
        # Get sensor names from the graph results
        sensor_names = []
        for sensor in sensors:
            # Try different possible fields for sensor name/tag
            sensor_name = (sensor.get('name') or 
                          sensor.get('tag') or 
                          sensor.get('properties', {}).get('tag') or
                          sensor.get('properties', {}).get('name'))
            if sensor_name:
                sensor_names.append(sensor_name)
        
        if not sensor_names:
            return {
                "area": area_name,
                "work_orders": [],
                "count": 0,
                "message": "No valid sensor names found in area"
            }
        
        # Get work orders for all sensors in the area
        all_work_orders_by_sensor = maintenance_service.get_work_orders_for_sensors(sensor_names)
        
        # Flatten all work orders with sensor information, deduplicating by work order ID
        work_orders_dict = {}  # Use dict to deduplicate by work order ID
        sensor_mapping = {}  # Track which sensors are associated with each work order
        
        for sensor_name, work_orders in all_work_orders_by_sensor.items():
            for wo in work_orders:
                wo_id = wo.id
                if wo_id not in work_orders_dict:
                    work_orders_dict[wo_id] = {
                        "sensor_name": sensor_name,  # Use first sensor found
                        "id": wo.id,
                        "nr": wo.nr,
                        "asset_id": wo.asset_id,
                        "short_description": wo.short_description,
                        "description": wo.description,
                        "comment": wo.comment,
                        "status": wo.status,
                        "from_date": wo.from_date,
                        "to_date": wo.to_date,
                        "created_at": wo.created_at,
                        "finished_date": wo.finished_date,
                        "priority": wo.priority,
                        "url": wo.url,
                        "is_reactive_maintenance": wo.is_reactive_maintenance
                    }
                    sensor_mapping[wo_id] = [sensor_name]
                else:
                    # Add additional sensors to the mapping for this work order
                    if sensor_name not in sensor_mapping[wo_id]:
                        sensor_mapping[wo_id].append(sensor_name)
        
        # Convert dict back to list and add related sensors
        all_work_orders = list(work_orders_dict.values())
        for wo in all_work_orders:
            wo["related_sensors"] = sensor_mapping[wo["id"]]
        
        # Sort by created_at date, handling empty dates
        all_work_orders.sort(key=lambda x: x['created_at'] if x['created_at'] else '', reverse=True)
        
        return {
            "area": area_name,
            "sensors_checked": sensor_names,
            "work_orders": all_work_orders,
            "count": len(all_work_orders)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get area work orders: {str(e)}")


@router.get("/equipment/{equipment_name}/work-orders")
async def get_equipment_work_orders(equipment_name: str):
    """
    Get all work orders for sensors connected to a specific equipment
    
    Args:
        equipment_name: Name of the equipment
        
    Returns:
        Dictionary with equipment name, sensors checked, and work orders
    """
    maintenance_service = get_maintenance_service()
    if not maintenance_service:
        raise HTTPException(status_code=503, detail="Maintenance API service not available")
    
    if not graph_service.is_connected():
        raise HTTPException(status_code=503, detail="Graph service not available")
    
    try:
        # Get all sensors connected to this equipment using the same logic as connected entities
        neo4j_label = map_entity_type_to_neo4j_label('Equipment')
        
        # Get connected entities from Neo4j (same query as in get_entity_connected_entities)
        query = f"""
        MATCH (e:{neo4j_label})-[r]-(connected)
        WHERE e.id = $entity_id OR e.name = $entity_id OR e.equipment_id = $entity_id OR e.tag = $entity_id
        AND 'Sensor' IN labels(connected)
        WITH connected, type(r) as rel_type, labels(connected) as connected_labels
        RETURN connected.id as id, connected.name as name, connected.description as description,
               connected_labels as labels, properties(connected) as properties,
               rel_type
        ORDER BY connected_labels, connected.name
        """
        results = graph_service.execute_query(query, {"entity_id": equipment_name})
        
        sensors = []
        for result in results:
            sensors.append({
                "id": result.get("id"),
                "name": result.get("name"),
                "description": result.get("description"),
                "labels": result.get("labels", []),
                "properties": result.get("properties", {}),
                "relationship_type": result.get("rel_type")
            })
        
        if not sensors:
            return {
                "equipment": equipment_name,
                "work_orders": [],
                "count": 0,
                "message": "No sensors found connected to equipment"
            }
        
        # Get sensor names from the graph results
        sensor_names = []
        for sensor in sensors:
            # Try different possible fields for sensor name/tag
            sensor_name = (sensor.get('name') or 
                          sensor.get('tag') or 
                          sensor.get('properties', {}).get('tag') or
                          sensor.get('properties', {}).get('name'))
            if sensor_name:
                sensor_names.append(sensor_name)
        
        if not sensor_names:
            return {
                "equipment": equipment_name,
                "work_orders": [],
                "count": 0,
                "message": "No valid sensor names found connected to equipment"
            }
        
        # Get work orders for all sensors connected to the equipment
        all_work_orders_by_sensor = maintenance_service.get_work_orders_for_sensors(sensor_names)
        
        # Flatten all work orders with sensor information
        all_work_orders = []
        for sensor_name, work_orders in all_work_orders_by_sensor.items():
            for wo in work_orders:
                all_work_orders.append({
                    "sensor_name": sensor_name,
                    "id": wo.id,
                    "nr": wo.nr,
                    "asset_id": wo.asset_id,
                    "short_description": wo.short_description,
                    "description": wo.description,
                    "comment": wo.comment,
                    "status": wo.status,
                    "from_date": wo.from_date,
                    "to_date": wo.to_date,
                    "created_at": wo.created_at,
                    "finished_date": wo.finished_date,
                    "priority": wo.priority,
                    "url": wo.url,
                    "is_reactive_maintenance": wo.is_reactive_maintenance
                })
        
        # Sort by date (most recent first)
        all_work_orders.sort(key=lambda x: x['created_at'], reverse=True)
        
        return {
            "equipment": equipment_name,
            "sensors_checked": sensor_names,
            "work_orders": all_work_orders,
            "count": len(all_work_orders)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get equipment work orders: {str(e)}")
