# Multi-Agent Orchestration System

## Overview

The multi-agent orchestration system transforms natural language queries into actionable insights by coordinating multiple specialized AI agents. Each agent focuses on a specific data source or task, and their outputs are combined to provide comprehensive answers.

## Architecture

```
User Query
    ↓
WorkflowCoordinator (LangGraph)
    ├── Intent Analysis (LLM)
    ├── Graph Agent (Neo4j Cypher)
    ├── Maintenance Agent (MCP → Maintenance API)
    ├── ADX Agent (Azure Data Explorer - Mock)
    └── Synthesizer Agent (LLM)
        ↓
    Natural Language Response + Execution Trace
```

## Agents

### 1. WorkflowCoordinator
- **Purpose**: Orchestrates agent execution based on query intent
- **Technology**: LangGraph for workflow management
- **Features**:
  - Intent classification using GPT-4
  - Dynamic agent routing
  - Parallel and sequential execution
  - Error handling and recovery

### 2. GraphAgent
- **Purpose**: Queries Neo4j graph database for plant structure, equipment, and sensors
- **Technology**: Neo4j + OpenAI GPT-4 for Cypher generation
- **Capabilities**:
  - Natural language → Cypher query conversion
  - Hierarchical plant/area/equipment/sensor queries
  - Relationship traversal

### 3. MaintenanceAgent
- **Purpose**: Retrieves work orders and maintenance data
- **Technology**: MCP (Model Context Protocol) client → Maintenance API
- **Capabilities**:
  - Work order lookup by sensor
  - Sensor name transformation (e.g., `4010FI001.DACA.PV` → `40-10-FI-001`)
  - Batch sensor querying
  
### 4. ADXAgent
- **Purpose**: Queries time-series sensor data and detects anomalies
- **Technology**: Azure Data Explorer (currently mock implementation)
- **Capabilities**:
  - Real-time sensor measurements
  - Anomaly detection
  - Time-series analysis

### 5. SynthesizerAgent
- **Purpose**: Combines multi-agent outputs into coherent natural language responses
- **Technology**: OpenAI GPT-4
- **Capabilities**:
  - Context-aware synthesis
  - Data citation
  - Professional industrial language

## Query Flow

1. **User submits query** via `/query` API endpoint
2. **Intent Analysis**: LLM classifies which data sources are needed
3. **Agent Execution**: 
   - Graph Agent runs first (provides context for other agents)
   - Maintenance/ADX agents run conditionally based on intent
   - Agents execute in parallel when possible
4. **Synthesis**: Synthesizer combines all outputs
5. **Response returned** with execution trace

## Example Queries

| Query | Agents Invoked | Response Includes |
|-------|---------------|-------------------|
| "What sensors are in area 40-10?" | Graph, Synthesizer | List of sensors with tags |
| "Are there work orders in area 40-10?" | Graph, Maintenance, Synthesizer | Work order details with descriptions |
| "Show abnormal temperatures" | Graph, ADX, Synthesizer | Sensor readings + anomalies |
| "Equipment status with maintenance data" | Graph, Maintenance, ADX, Synthesizer | Complete operational picture |

## MCP Integration

The Maintenance Agent uses **Model Context Protocol (MCP)** for standardized tool access:

- **Protocol**: MCP Streamable HTTP with SSE (Server-Sent Events)
- **Transport**: HTTP POST with JSON-RPC 2.0
- **Session Management**: Automatic session initialization and renewal
- **Error Handling**: Graceful degradation if MCP server unavailable

### MCP Configuration

```python
# Environment variable
MAINTENANCE_MCP_URL=http://host.docker.internal:8080

# Client automatically:
# 1. Initializes session via POST /mcp with "initialize" method
# 2. Stores session ID from response headers
# 3. Uses session ID for all subsequent tool calls
# 4. Parses SSE responses
```

## Execution Trace

Every query returns an execution trace for transparency:

```json
{
  "execution_trace": {
    "total_duration_ms": 16537,
    "agents_invoked": [
      {
        "agent_name": "graph_agent",
        "status": "success",
        "duration_ms": 1760,
        "summary": "Found 9 results in graph database",
        "output": { /* agent-specific output */ },
        "error": null,
        "timestamp": "2025-10-28T10:08:14.040823"
      }
    ],
    "workflow_version": "1.0"
  }
}
```

## Testing

### Unit Tests
```bash
pytest backend/agents/tests/test_agents.py
```

### Integration Tests
```bash
pytest backend/agents/tests/test_integration.py
```

### Manual Testing
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Are there work orders in area 40-10?"}'
```

## Configuration

### Environment Variables
- `OPENAI_API_KEY`: OpenAI API key for LLM agents
- `NEO4J_URI`: Neo4j connection string
- `MAINTENANCE_MCP_URL`: Maintenance MCP server URL
- `ADX_MCP_URL`: ADX MCP server URL

### Agent Configuration
Agents are configured in `agents/workflow.py`. To add new agents:
1. Create agent class extending `BaseAgent`
2. Register in `WorkflowCoordinator.__init__()`
3. Add routing logic
4. Update intent analysis prompt

## Error Handling

- **Agent failures**: Captured in execution trace, workflow continues
- **MCP unavailable**: Synthesizer acknowledges missing data
- **LLM errors**: Fallback to raw data presentation
- **Neo4j errors**: Returned as error in graph agent output

## Performance

- **Average query time**: 10-18 seconds
  - Graph Agent: ~2s
  - Maintenance Agent: ~3-5s
  - Synthesizer: ~7-10s
- **Parallel execution**: Maintenance + ADX can run in parallel
- **Caching**: MCP sessions cached for performance

## Future Enhancements

- [ ] Real ADX integration (replace mock)
- [ ] Agent result caching
- [ ] Streaming responses
- [ ] Multi-turn conversations
- [ ] Scoped/contextual chat per asset
- [ ] Custom agent plugins

## Troubleshooting

### MCP Connection Issues
- Check `MAINTENANCE_MCP_URL` is reachable from backend container
- Verify MCP server is running: `docker ps | grep maintenance`
- Check backend logs: `docker logs unger-agentic-insight-backend-1`

### Graph Query Errors
- Verify Neo4j connection: Check Neo4j browser at http://localhost:7474
- Check Cypher query in execution trace
- Ensure graph data is loaded

### Missing Work Orders
- Verify sensor name transformation in maintenance MCP
- Check maintenance API connectivity
- Review execution trace for errors
