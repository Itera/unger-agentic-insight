"""
Query API Router

Handles AI-powered natural language queries with optional ADX integration.
"""

import json
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException

from models.requests import QueryRequest, ContextualQueryRequest
from models.responses import QueryResponse
from utils.serializers import serialize_neo4j_data
from services.graph_service import graph_service
from core.dependencies import get_openai_client
from core.config import settings
from core.prompt_templates import get_guidelines_template


router = APIRouter(prefix="", tags=["query"])


async def get_schema_info(use_adx: bool) -> Dict[str, Any]:
    """
    Get schema information from ADX MCP
    
    Args:
        use_adx: Whether to use Azure Data Explorer
        
    Returns:
        Schema information dictionary
    """
    if use_adx:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.ADX_MCP_URL}/mcp",
                    json={"method": "tools/call", "params": {"name": "get_schema", "arguments": {}}}
                )
                if response.status_code == 200:
                    return response.json().get("result", {})
        except Exception as e:
            print(f"Failed to get ADX schema: {e}")
    
    # Return empty schema if ADX not available
    return {"tables": [], "columns": {}}


def create_system_prompt(schema_info: Dict[str, Any], use_adx: bool) -> str:
    """
    Create system prompt for OpenAI agent
    
    Args:
        schema_info: Database schema information
        use_adx: Whether using ADX
        
    Returns:
        System prompt string
    """
    query_language = "KQL (Kusto Query Language)" if use_adx else "SQL"
    
    prompt = f"""You are an expert industrial data analyst with access to sensor and configuration data.

Available tables and columns:
{json.dumps(schema_info, indent=2)}

You can answer questions about:
- HMI sensor data (timestamps, values, units, quality)
- Tag configurations (descriptions, scan frequencies, limits)
- Itera measurements (various LI sensor readings)

When answering queries:
1. Provide clear, insightful analysis of the industrial data
2. If a {query_language} query would be helpful, include it in your response between ```{query_language.lower()} and ``` tags
3. Explain what the data shows in business/operational terms
4. Highlight any anomalies, trends, or important insights
5. Use appropriate industrial terminology

Focus on providing actionable insights for plant operations and maintenance."""
    
    return prompt


def create_contextual_system_prompt(schema_info: Dict[str, Any], context_data: Optional[Dict[str, Any]], use_adx: bool) -> str:
    """
    Create contextual system prompt for scoped OpenAI agent responses
    
    Args:
        schema_info: Database schema information
        context_data: Graph context data
        use_adx: Whether using ADX
        
    Returns:
        Contextual system prompt string
    """
    query_language = "KQL (Kusto Query Language)" if use_adx else "SQL"
    
    base_prompt = f"""You are an expert industrial data analyst with access to sensor and configuration data.

Available tables and columns:
{json.dumps(schema_info, indent=2)}
"""

    # Add contextual information if available
    if context_data:
        context_prompt = f"""
🔍 CURRENT NAVIGATION CONTEXT:
You are currently focused on: {context_data.get('context_scope', 'Unknown')}
Central Node: {context_data.get('central_node', {}).get('name', 'Unknown')} ({context_data.get('central_node', {}).get('labels', [])})
"""
        
        # Add connected nodes information with relationships
        if context_data.get('connected_nodes'):
            context_prompt += f"\nConnected Entities ({len(context_data['connected_nodes'])} found):\n"
            
            # Group by relationship types and entity types with rich properties
            entity_relationships = {}
            detailed_entities = []
            
            for node in context_data['connected_nodes'][:15]:  # Show more entities for better context
                # Safely handle labels
                labels = node.get('labels', [])
                if labels and all(label is not None for label in labels):
                    node_labels = ', '.join(str(label) for label in labels)
                else:
                    node_labels = 'Unknown'
                
                # Enhanced node identification with proper names
                node_name = str(node.get('name') or 
                               node.get('properties', {}).get('equipment_name') or 
                               node.get('properties', {}).get('tag') or 
                               'Unknown')
                
                relationship_path = node.get('relationship_path', [])
                depth = node.get('depth', 'unknown')
                properties = node.get('properties', {})
                
                # Determine relationship context safely
                if relationship_path and all(r is not None for r in relationship_path):
                    rel_context = f"via {' → '.join(str(r) for r in relationship_path)}"
                else:
                    rel_context = f"at depth {str(depth)}"
                
                # Enhanced entity description with rich properties
                entity_desc = f"- {node_name} ({node_labels})"
                
                # Add sensor-specific properties
                if 'Sensor' in node_labels:
                    sensor_details = []
                    if properties.get('unit'):
                        sensor_details.append(f"Unit: {properties['unit']}")
                    if properties.get('sensor_type_code'):
                        sensor_details.append(f"Type: {properties['sensor_type_code']}")
                    if properties.get('classification'):
                        sensor_details.append(f"Class: {properties['classification']}")
                    if sensor_details:
                        entity_desc += f" [{', '.join(sensor_details)}]"
                
                # Add equipment-specific properties
                elif 'Equipment' in node_labels:
                    equip_details = []
                    if properties.get('equipment_type'):
                        equip_details.append(f"Type: {properties['equipment_type']}")
                    if properties.get('sensor_count'):
                        equip_details.append(f"Sensors: {properties['sensor_count']}")
                    if equip_details:
                        entity_desc += f" [{', '.join(equip_details)}]"
                    
                    # Add source tags if available
                    if properties.get('source_tags'):
                        source_tags = properties['source_tags'].split(',')[:3]  # Show first 3 tags
                        entity_desc += f" [Tags: {', '.join([tag.strip() for tag in source_tags])}]"
                
                entity_desc += f" - {rel_context}"
                detailed_entities.append(entity_desc)
                
                # Track relationship patterns for summary
                primary_type = node_labels.split(',')[0].strip() if node_labels and node_labels != 'Unknown' else 'Unknown'
                if primary_type not in entity_relationships:
                    entity_relationships[primary_type] = []
                entity_relationships[primary_type].append({
                    'name': node_name,
                    'properties': properties,
                    'type': primary_type
                })
            
            # Display detailed entities
            for entity_desc in detailed_entities:
                context_prompt += entity_desc + "\n"
            
            if len(context_data['connected_nodes']) > 15:
                context_prompt += f"... and {len(context_data['connected_nodes']) - 15} more entities\n"
            
            # Add enhanced relationship summary with property insights
            context_prompt += "\n📊 RELATIONSHIP SUMMARY:\n"
            for entity_type, entities in entity_relationships.items():
                entity_names = [e['name'] for e in entities]
                context_prompt += f"- {len(entities)} {entity_type}(s): {', '.join(entity_names[:3])}"
                if len(entities) > 3:
                    context_prompt += f" and {len(entities) - 3} more"
                
                # Add property summary for each type
                if entity_type == 'Sensor':
                    units = [e['properties'].get('unit') for e in entities if e['properties'].get('unit')]
                    if units:
                        unique_units = list(set(units))
                        context_prompt += f" [Units: {', '.join(unique_units)}]"
                elif entity_type == 'Equipment':
                    types = [e['properties'].get('equipment_type') for e in entities if e['properties'].get('equipment_type')]
                    if types:
                        unique_types = list(set(types))
                        context_prompt += f" [Types: {', '.join(unique_types)}]"
                    
                    total_sensor_count = sum([int(e['properties'].get('sensor_count', 0)) for e in entities if e['properties'].get('sensor_count')])
                    if total_sensor_count > 0:
                        context_prompt += f" [Total Connected Sensors: {total_sensor_count}]"
                
                context_prompt += "\n"
        
        context_prompt += f"\nTotal entities in scope: {context_data.get('total_nodes', 0)}\n"
        context_prompt += "\n⚠️  IMPORTANT: Your responses should be FOCUSED on this specific context. When the user asks about 'sensors', 'equipment', or 'data', prioritize information related to the entities listed above.\n"
        
        base_prompt += context_prompt
    
    # Add guidelines template
    base_prompt += get_guidelines_template(query_language)
    
    return base_prompt


async def get_contextual_graph_data(context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Get contextual graph data for the current navigation scope
    
    Args:
        context: Navigation context dictionary
        
    Returns:
        Context data or None
    """
    if not graph_service.is_connected():
        return None
    
    try:
        node_type = context.get('nodeType')
        node_name = context.get('nodeName') 
        scope_depth = context.get('scopeDepth', 2)
        
        if not node_type or not node_name:
            return None
        
        # Get contextual subgraph using existing graph service method
        context_data = graph_service.get_contextual_subgraph(node_name, node_type, scope_depth)
        
        return context_data
        
    except Exception as e:
        print(f"Error getting contextual graph data: {e}")
        return None


async def execute_adx_query_from_response(response: str) -> Optional[List[Dict[str, Any]]]:
    """
    Extract and execute KQL query from agent response
    
    Args:
        response: OpenAI agent response text
        
    Returns:
        Query results or None
    """
    try:
        # Look for KQL query in response
        import re
        kql_match = re.search(r'```kql\n(.*?)\n```', response, re.DOTALL)
        if not kql_match:
            kql_match = re.search(r'```\n(.*?)\n```', response, re.DOTALL)
        
        if kql_match:
            query = kql_match.group(1).strip()
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.ADX_MCP_URL}/mcp",
                    json={
                        "method": "tools/call",
                        "params": {"name": "execute_kql", "arguments": {"query": query}}
                    }
                )
                
                if response.status_code == 200:
                    result = response.json().get("result", {})
                    return result.get("results", [])
    
    except Exception as e:
        print(f"Failed to execute ADX query: {e}")
    
    return None


@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process natural language queries using OpenAI agent and ADX MCP
    
    Args:
        request: Query request with query text and ADX flag
        
    Returns:
        Query response with AI analysis and optional data
    """
    openai_client = get_openai_client()
    if not openai_client:
        raise HTTPException(status_code=503, detail="OpenAI client not available")
    
    try:
        # Get schema information from ADX MCP
        schema_info = await get_schema_info(request.use_adx)
        
        # Create system prompt for the OpenAI agent
        system_prompt = create_system_prompt(schema_info, request.use_adx)
        
        # Query OpenAI agent
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.query}
            ],
            temperature=0.1
        )
        
        agent_response = response.choices[0].message.content
        
        # Try to extract and execute any KQL query from the response
        data = None
        if request.use_adx:
            data = await execute_adx_query_from_response(agent_response)
        
        return QueryResponse(
            query=request.query,
            response=agent_response,
            data=data,
            source="adx" if request.use_adx else "local",
            timestamp=datetime.now()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


@router.post("/query/contextual", response_model=QueryResponse)
async def process_contextual_query(request: ContextualQueryRequest):
    """
    Process contextual natural language queries with graph navigation scope
    
    Args:
        request: Contextual query request with context data
        
    Returns:
        Query response with scoped AI analysis
    """
    openai_client = get_openai_client()
    if not openai_client:
        raise HTTPException(status_code=503, detail="OpenAI client not available")
    
    try:
        # Get schema information from ADX MCP
        schema_info = await get_schema_info(request.use_adx)
        
        # Get contextual graph data if context is provided
        context_data = None
        if request.context and request.context.get('nodeType') and request.context.get('nodeName'):
            context_data = await get_contextual_graph_data(request.context)
        
        # Create contextual system prompt
        system_prompt = create_contextual_system_prompt(schema_info, context_data, request.use_adx)
        
        # Query OpenAI agent with context
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.query}
            ],
            temperature=0.1
        )
        
        agent_response = response.choices[0].message.content
        
        # Try to extract and execute any KQL query from the response
        data = None
        if request.use_adx:
            data = await execute_adx_query_from_response(agent_response)
        
        return QueryResponse(
            query=request.query,
            response=agent_response,
            data=data,
            source=f"{'adx' if request.use_adx else 'local'}-contextual",
            timestamp=datetime.now(),
            context_used=serialize_neo4j_data(context_data) if context_data else None  # Serialize context data
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Contextual query processing failed: {str(e)}")
