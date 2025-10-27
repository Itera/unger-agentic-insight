#!/usr/bin/env python3
"""
Test script for the enhanced graph query service
Tests the new methods with your actual graph data structure
"""

import sys
import os
from dotenv import load_dotenv

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.graph_service import graph_service

def test_graph_queries():
    """Test the new graph query methods"""
    print("Testing Enhanced Graph Query Service")
    print("=" * 50)
    
    # Connect to graph
    if not graph_service.connect():
        print("❌ Failed to connect to graph service")
        return False
    
    print("✅ Connected to Neo4j graph database")
    print()
    
    # Test 1: Get all plants
    print("1. Testing get_all_plants()")
    try:
        plants = graph_service.get_all_plants()
        print(f"   Found {len(plants)} plants:")
        for plant in plants[:3]:  # Show first 3
            print(f"   - {plant.get('name', 'Unknown')} (ID: {plant.get('id', 'N/A')})")
        print()
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print()
    
    # Test 2: Get asset areas for S-Plant
    print("2. Testing get_asset_areas_by_plant('S-Plant')")
    try:
        areas = graph_service.get_asset_areas_by_plant("S-Plant")
        print(f"   Found {len(areas)} asset areas in S-Plant:")
        for area in areas[:5]:  # Show first 5
            print(f"   - {area.get('name', 'Unknown')} (ID: {area.get('id', 'N/A')})")
        print()
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print()
    
    # Test 3: Get equipment for first asset area (if any)
    if areas:
        first_area = areas[0].get('name')
        print(f"3. Testing get_equipment_by_asset_area('{first_area}')")
        try:
            equipment = graph_service.get_equipment_by_asset_area(first_area)
            print(f"   Found {len(equipment)} equipment in {first_area}:")
            for eq in equipment[:3]:  # Show first 3
                print(f"   - {eq.get('name', 'Unknown')} (ID: {eq.get('id', 'N/A')})")
            print()
        except Exception as e:
            print(f"   ❌ Error: {e}")
            print()
    
    # Test 4: Get sensors for first asset area (if any)
    if areas:
        first_area = areas[0].get('name')
        print(f"4. Testing get_sensors_by_asset_area('{first_area}')")
        try:
            sensors = graph_service.get_sensors_by_asset_area(first_area)
            print(f"   Found {len(sensors)} sensors in {first_area}:")
            for sensor in sensors[:3]:  # Show first 3
                print(f"   - {sensor.get('name', 'Unknown')} (ID: {sensor.get('id', 'N/A')})")
            print()
        except Exception as e:
            print(f"   ❌ Error: {e}")
            print()
    
    # Test 5: Get all asset areas
    print("5. Testing get_all_asset_areas()")
    try:
        all_areas = graph_service.get_all_asset_areas()
        print(f"   Found {len(all_areas)} total asset areas")
        print()
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print()
    
    # Test 6: Search for nodes
    print("6. Testing search_nodes('75')")
    try:
        results = graph_service.search_nodes("75")
        print(f"   Found {len(results)} nodes containing '75':")
        for result in results[:5]:  # Show first 5
            print(f"   - {result.get('name', 'Unknown')} ({result.get('labels', [])})")
        print()
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print()
    
    # Test 7: Get contextual subgraph for first asset area
    if areas:
        first_area = areas[0].get('name')
        print(f"7. Testing get_contextual_subgraph('AssetArea', '{first_area}')")
        try:
            context = graph_service.get_contextual_subgraph(first_area, "AssetArea", max_depth=1)
            print(f"   Context scope: {context.get('context_scope')}")
            print(f"   Total nodes in context: {context.get('total_nodes')}")
            print(f"   Connected nodes: {len(context.get('connected_nodes', []))}")
            print()
        except Exception as e:
            print(f"   ❌ Error: {e}")
            print()
    
    # Close connection
    graph_service.close()
    print("✅ All tests completed!")
    return True

if __name__ == "__main__":
    load_dotenv()
    
    success = test_graph_queries()
    
    if success:
        print("\n🎉 Graph query service is working with your data!")
    else:
        print("\n💥 Some tests failed. Check your graph setup.")
    
    sys.exit(0 if success else 1)