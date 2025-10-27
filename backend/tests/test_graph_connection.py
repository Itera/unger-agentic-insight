#!/usr/bin/env python3
"""
Test script for Neo4j graph service connection
Run this to verify Neo4j connectivity before starting the main application
"""

import sys
import os
from dotenv import load_dotenv

# Add the current directory to the Python path so we can import our services
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.graph_service import graph_service

def test_connection():
    """Test Neo4j connection and basic queries"""
    print("Testing Neo4j connection...")
    
    # Test connection
    connected = graph_service.connect()
    if not connected:
        print("❌ Failed to connect to Neo4j")
        print("Make sure Neo4j is running and check your credentials in .env")
        return False
    
    print("✅ Successfully connected to Neo4j")
    
    # Test basic query
    try:
        # Simple query to check if we can execute Cypher
        result = graph_service.execute_query("RETURN 1 as test")
        if result and result[0].get('test') == 1:
            print("✅ Basic query execution works")
        else:
            print("❌ Basic query failed")
            return False
    except Exception as e:
        print(f"❌ Query execution error: {e}")
        return False
    
    # Test node count query
    try:
        result = graph_service.execute_query("MATCH (n) RETURN count(n) as total_nodes")
        total_nodes = result[0].get('total_nodes', 0) if result else 0
        print(f"📊 Total nodes in graph: {total_nodes}")
        
        # Test label query
        result = graph_service.execute_query("CALL db.labels()")
        labels = [record.get('label') for record in result]
        print(f"🏷️  Node labels in graph: {labels}")
        
    except Exception as e:
        print(f"⚠️  Could not retrieve graph statistics: {e}")
    
    # Test our service methods
    try:
        plants = graph_service.get_all_plants()
        print(f"🏭 Found {len(plants)} plants")
        if plants:
            for plant in plants:
                print(f"   - {plant.get('name', 'Unknown')} (ID: {plant.get('id', 'N/A')})")
    except Exception as e:
        print(f"⚠️  Plant query error (this is expected if your graph has different schema): {e}")
    
    # Close connection
    graph_service.close()
    print("✅ Connection test completed successfully")
    return True

if __name__ == "__main__":
    load_dotenv()
    
    print("Neo4j Connection Test")
    print("=" * 30)
    
    # Check environment variables
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USERNAME", "neo4j")
    neo4j_pass = os.getenv("NEO4J_PASSWORD", "password")
    
    print(f"Neo4j URI: {neo4j_uri}")
    print(f"Username: {neo4j_user}")
    print(f"Password: {'*' * len(neo4j_pass)}")
    print()
    
    success = test_connection()
    
    if success:
        print("\n🎉 All tests passed! Neo4j integration is ready.")
        sys.exit(0)
    else:
        print("\n💥 Tests failed. Please check your Neo4j setup.")
        sys.exit(1)