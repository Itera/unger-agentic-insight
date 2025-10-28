"""
Graph Agent - Neo4j Cypher Query Generation and Execution

Uses LLM to generate Cypher queries based on natural language and executes them
against the Neo4j graph database containing plant/area/equipment/sensor hierarchy.
"""

from typing import Dict, Any, List
from agents.nodes.base import BaseAgent
from agents.state import AgentState
from services.graph_service import graph_service
from core.dependencies import get_openai_client


GRAPH_SCHEMA_CONTEXT = """
You have access to a Neo4j graph database with the following schema:

NODES:
- Plant: S-Plant, T-Plant (properties: name)
- AssetArea: Areas within plants (properties: name, area_code - e.g., "40-10", "75-12")
- Equipment: Industrial equipment (properties: equipment_name, equipment_type, sensor_count, source_tags)
- Sensor: Measurement devices with properties:
  * tag: sensor tag identifier (e.g., "4010TI371.DACA.PV")
  * description: human-readable description
  * sensor_type_code: type code (e.g., "TI", "PI")
  * unit: measurement unit (e.g., "°C", "bar")
  * area_code: area identifier (e.g., "40-10")
  * classification: sensor classification (e.g., "PROCESS")
  * created_at: timestamp

RELATIONSHIPS:
- (Plant)-[:CONTAINS]->(AssetArea)
- (AssetArea)-[:CONTAINS]->(Equipment)
- (AssetArea)-[:HAS_SENSOR]->(Sensor)
- (Equipment)-[:HAS_SENSOR]->(Sensor)

IMPORTANT PROPERTY ACCESS RULES:
1. Sensor properties are DIRECT properties: use s.tag, s.description, s.unit (NOT s.properties.tag)
2. Equipment properties are NESTED: use e.properties.equipment_name
3. AssetArea and Plant use direct properties: a.name, p.name
4. Always use LIMIT 50 to prevent returning too many results
5. Use RETURN DISTINCT when appropriate to avoid duplicates
6. For counting, use COUNT(DISTINCT n)
"""


CYPHER_GENERATION_PROMPT = """You are an expert at generating Neo4j Cypher queries.

{schema_context}

User Query: {query}

Generate a single Cypher query that answers this question. Return ONLY the Cypher query, no explanation.
Do not include markdown code fences (```), just the raw Cypher.

IMPORTANT: For work order/maintenance queries about an area, return the SENSORS in that area.
The maintenance system will use those sensor tags to check for work orders.

Example queries:
- "What sensors are in area 40-10?" → MATCH (a:AssetArea {{name: "40-10"}})-[:HAS_SENSOR]->(s:Sensor) RETURN s.tag, s.description, s.unit LIMIT 50
- "Are there work orders in area 40-10?" → MATCH (a:AssetArea {{name: "40-10"}})-[:HAS_SENSOR]->(s:Sensor) RETURN s.tag, s.area_code LIMIT 50
- "Show maintenance for area 40-10" → MATCH (a:AssetArea {{name: "40-10"}})-[:HAS_SENSOR]->(s:Sensor) RETURN s.tag, s.description LIMIT 50
- "How many equipment items are there?" → MATCH (e:Equipment) RETURN COUNT(DISTINCT e) as equipment_count
- "Show me temperature sensors" → MATCH (s:Sensor) WHERE s.sensor_type_code = 'TI' RETURN s.tag, s.description, s.unit LIMIT 50
- "List equipment in area 40-10" → MATCH (a:AssetArea {{name: "40-10"}})-[:CONTAINS]->(e:Equipment) RETURN e.properties.equipment_name, e.properties.equipment_type LIMIT 50

Your query:"""


class GraphAgent(BaseAgent):
    """
    Agent that generates and executes Cypher queries on Neo4j graph.
    
    Uses OpenAI to convert natural language queries into Cypher,
    then executes them using the graph_service.
    """
    
    def __init__(self):
        super().__init__("graph_agent")
        self.openai_client = get_openai_client()
        
        if not graph_service.is_connected():
            raise RuntimeError("Graph service not connected. Cannot initialize GraphAgent.")
    
    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Generate Cypher query from user query and execute it.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary with query results
        """
        if not self.openai_client:
            raise RuntimeError("OpenAI client not available")
        
        query = state["query"]
        
        # Step 1: Generate Cypher query using LLM
        cypher_query = self._generate_cypher(query)
        
        # Step 2: Execute query on Neo4j
        results = self._execute_cypher(cypher_query)
        
        return {
            "cypher_query": cypher_query,
            "results": results,
            "result_count": len(results)
        }
    
    def _generate_cypher(self, query: str) -> str:
        """
        Use LLM to generate Cypher query from natural language.
        
        Args:
            query: Natural language query
            
        Returns:
            Generated Cypher query
        """
        prompt = CYPHER_GENERATION_PROMPT.format(
            schema_context=GRAPH_SCHEMA_CONTEXT,
            query=query
        )
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a Neo4j Cypher query expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        cypher = response.choices[0].message.content.strip()
        
        # Remove markdown code fences if LLM added them anyway
        cypher = cypher.replace("```cypher", "").replace("```", "").strip()
        
        return cypher
    
    def _execute_cypher(self, cypher_query: str) -> List[Dict[str, Any]]:
        """
        Execute Cypher query on Neo4j.
        
        Args:
            cypher_query: Valid Cypher query
            
        Returns:
            Query results
        """
        try:
            results = graph_service.execute_query(cypher_query)
            
            # Limit results to 50 to prevent overwhelming output
            if len(results) > 50:
                results = results[:50]
            
            return results
            
        except Exception as e:
            raise RuntimeError(f"Cypher execution failed: {e}")
    
    def _generate_summary(self, output: Dict[str, Any]) -> str:
        """Generate summary of graph agent results."""
        result_count = output.get("result_count", 0)
        
        if result_count == 0:
            return "No results found in graph database"
        elif result_count == 1:
            return f"Found 1 result in graph database"
        else:
            limited = " (limited to 50)" if result_count == 50 else ""
            return f"Found {result_count} results in graph database{limited}"
    
    def _store_output(self, state: AgentState, output: Dict[str, Any]) -> None:
        """Store graph results in state."""
        state["graph_result"] = output
