#!/usr/bin/env python3
"""
Test script for the data mapping service
Tests mapping between Neo4j graph entities and CSV sensor data
"""

import sys
import os
from dotenv import load_dotenv

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.data_mapping_service import initialize_data_mapping_service
from services.graph_service import graph_service

def test_data_mapping():
    """Test the data mapping service functionality"""
    print("Testing Data Mapping Service")
    print("=" * 40)
    
    # Initialize services
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/insight_db")
    data_mapping_service = initialize_data_mapping_service(DATABASE_URL)
    
    # Connect to graph
    if not graph_service.connect():
        print("❌ Failed to connect to graph service")
        return False
    
    print("✅ Connected to both services")
    print()
    
    # Test 1: Get sensor configurations for a known asset area
    print("1. Testing get_sensor_configurations_by_area('75-12')")
    try:
        sensor_configs = data_mapping_service.get_sensor_configurations_by_area("75-12")
        print(f"   Found {len(sensor_configs)} sensors in area 75-12:")
        for config in sensor_configs[:3]:  # Show first 3
            print(f"   - {config.get('name', 'Unknown')}: {config.get('description', 'No description')}")
        print()
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print()
    
    # Test 2: Map a graph node to sensor data
    print("2. Testing map_graph_node_to_sensor_data('75-12', 'AssetArea')")
    try:
        mapping = data_mapping_service.map_graph_node_to_sensor_data("75-12", "AssetArea")
        print(f"   Mapping confidence: {mapping.get('mapping_confidence')}")
        print(f"   Sensor configurations found: {len(mapping.get('sensor_configurations', []))}")
        print(f"   Recent data points: {len(mapping.get('recent_sensor_data', []))}")
        print()
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print()
    
    # Test 3: Get enriched context for an asset area
    print("3. Testing get_enriched_context_for_node('75-12', 'AssetArea')")
    try:
        enriched = data_mapping_service.get_enriched_context_for_node("75-12", "AssetArea")
        print(f"   Total sensors: {enriched['sensor_overview']['total_sensors']}")
        print(f"   Mapping confidence: {enriched['sensor_overview']['mapping_confidence']}")
        print(f"   Connected entities: {len(enriched['connected_entities'])}")
        
        # Show some connected entities with sensor data
        entities_with_sensors = [e for e in enriched['connected_entities'] if e['has_sensor_data']]
        print(f"   Connected entities with sensor data: {len(entities_with_sensors)}")
        print()
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print()
    
    # Test 4: Search sensors by type
    print("4. Testing search_sensors_by_criteria(sensor_type='temperature')")
    try:
        temp_sensors = data_mapping_service.search_sensors_by_criteria(sensor_type="temperature")
        print(f"   Found {len(temp_sensors)} temperature sensors")
        for sensor in temp_sensors[:3]:  # Show first 3
            print(f"   - {sensor.get('name', 'Unknown')} ({sensor.get('asset', 'No area')}) - {sensor.get('tag_units', 'No unit')}")
        print()
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print()
    
    # Test 5: Search sensors in specific area
    print("5. Testing search_sensors_by_criteria(area_id='75-18')")
    try:
        area_sensors = data_mapping_service.search_sensors_by_criteria(area_id="75-18")
        print(f"   Found {len(area_sensors)} sensors in area 75-18")
        for sensor in area_sensors[:3]:  # Show first 3
            print(f"   - {sensor.get('name', 'Unknown')}: {sensor.get('description', 'No description')[:50]}...")
        print()
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print()
    
    # Test 6: Get data quality summary
    print("6. Testing get_data_quality_summary('75-18')")
    try:
        quality = data_mapping_service.get_data_quality_summary("75-18")
        print(f"   Total configured sensors: {quality['total_configured_sensors']}")
        print(f"   Data coverage: {quality['data_coverage_pct']:.1f}%")
        print(f"   Sensor types: {quality['sensor_types']}")
        print()
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print()
    
    # Test 7: Test area extraction from sensor names
    print("7. Testing extract_area_from_sensor_name()")
    test_sensors = [
        "7512TIC301_SP0.AUTOMANA.OP",
        "7518EI050.DACA.PV",
        "7520LIC008.PIDA.OP"
    ]
    
    for sensor_name in test_sensors:
        area = data_mapping_service.extract_area_from_sensor_name(sensor_name)
        print(f"   {sensor_name} → {area}")
    print()
    
    # Close connections
    graph_service.close()
    print("✅ All tests completed!")
    return True

if __name__ == "__main__":
    load_dotenv()
    
    success = test_data_mapping()
    
    if success:
        print("\n🎉 Data mapping service is working!")
    else:
        print("\n💥 Some tests failed. Check your setup.")
    
    sys.exit(0 if success else 1)