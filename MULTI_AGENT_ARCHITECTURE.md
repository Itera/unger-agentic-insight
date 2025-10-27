# Multi-Agent Architecture Documentation

## Overview

The Agentic Insight system uses a **LangGraph-based multi-agent orchestration** to answer complex industrial queries. Instead of a single AI making all decisions, specialized agents collaborate to provide comprehensive analysis.

## Architecture Diagram

```
┌────────────────────────────────────────────────────────────┐
│                      User Query                             │
│              "What sensors need maintenance?"               │
└────────────────────────┬───────────────────────────────────┘
                         │
                         ▼
             ┌───────────────────────┐
             │  API Endpoint         │
             │  /query or            │
             │  /query/contextual    │
             └───────────┬───────────┘
                         │
                         ▼
        ┌────────────────────────────────┐
        │   Workflow Coordinator         │
        │   (LangGraph StateGraph)       │
        │   • Analyzes query intent      │
        │   • Selects agents to invoke   │
        │   • Orchestrates execution     │
        └────────────┬───────────────────┘
                     │
      ┌──────────────┼──────────────┬─────────────┐
      │              │              │             │
      ▼              ▼              ▼             ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│  Graph   │  │  Maint.  │  │   ADX    │  │  Synth.  │
│  Agent   │  │  Agent   │  │  Agent   │  │  Agent   │
├──────────┤  ├──────────┤  ├──────────┤  ├──────────┤
│ Neo4j    │  │ MCP →    │  │ Mock     │  │ Combines │
│ Cypher   │  │ Work     │  │ Sensor   │  │ All      │
│ Queries  │  │ Orders   │  │ Data     │  │ Results  │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
      │              │              │             │
      └──────────────┴──────────────┴─────────────┘
                     │
                     ▼
            ┌────────────────┐
            │ Final Response │
            │ + Exec. Trace  │
            └────────────────┘
```

## Components

### 1. Workflow Coordinator (`agents/workflow.py`)

**Responsibility:** Orchestrates the entire multi-agent workflow using LangGraph.

**Key Features:**
- **Intent Classification**: Uses LLM to determine which agents are needed
- **Conditional Routing**: Graph → Maintenance/ADX → Synthesizer (based on query)
- **State Management**: Maintains shared state across all agents
- **Execution Tracking**: Records timing, status, and output for each agent

**Example Flow:**
```python
Query: "Do we have work orders for sensors in area 40-10?"

1. analyze_intent → needs_graph=true, needs_maintenance=true, needs_adx=false
2. graph_agent → Find sensors in area 40-10 (returns 12 sensors)
3. maintenance_agent → Query work orders for those 12 sensors (returns 2 WOs)
4. synthesizer → Combine results into natural language response

Total: 2.3 seconds, 3 agents invoked
```

### 2. Graph Agent (`agents/nodes/graph.py`)

**Responsibility:** Query Neo4j graph database for plant/area/equipment/sensor topology.

**How It Works:**
1. Receives natural language query
2. Uses GPT-4 to generate Cypher query from schema context
3. Executes Cypher on Neo4j via `graph_service`
4. Returns results (limited to 50 items)

**Example:**
```
Input: "What sensors are in area 40-10?"
Cypher: MATCH (a:AssetArea {name: "40-10"})-[:HAS_SENSOR]->(s:Sensor) 
        RETURN s.name, s.properties.tag LIMIT 50
Output: 12 sensors with tags and properties
```

### 3. Maintenance Agent (`agents/nodes/maintenance.py`)

**Responsibility:** Retrieve work orders from Maintenance API via MCP protocol.

**How It Works:**
1. Extracts sensor names from Graph Agent results
2. Queries Maintenance MCP for work orders per sensor (max 10 sensors)
3. Returns work orders with sensor context
4. Handles MCP unavailability gracefully

**Example:**
```
Input: [sensor1, sensor2, sensor3] from graph results
MCP Call: get_work_orders_by_sensor(sensor_name="sensor1")
Output: [
  {nr: 12345, description: "Replace valve", sensor_name: "sensor1"},
  {nr: 12346, description: "Calibration", sensor_name: "sensor3"}
]
```

**Note:** Uses **MCP-only** (no direct API calls), cleaner architecture.

### 4. ADX Agent (`agents/nodes/adx.py`)

**Responsibility:** Retrieve sensor measurements and detect anomalies.

**Current State:** Stub with mock data (ready for MCP integration)

**How It Works:**
1. Extracts sensor names from Graph Agent results
2. Generates realistic mock measurements (5 per sensor)
3. Detects mock anomalies (20% probability)
4. Returns measurements with anomaly flags

**Example:**
```
Input: [4038LI579, 4038TI120] from graph results
Output: {
  measurements: [
    {sensor: "4038LI579", value: 45.2, unit: "%", timestamp: "..."},
    {sensor: "4038TI120", value: 72.5, unit: "°C", timestamp: "..."}
  ],
  anomalies: [
    {sensor: "4038LI579", type: "spike", severity: "high"}
  ],
  mock_data: true
}
```

**Future:** Switch `use_mcp = True` when ADX MCP is deployed.

### 5. Synthesizer Agent (`agents/nodes/synthesizer.py`)

**Responsibility:** Combine outputs from all agents into coherent natural language response.

**How It Works:**
1. Collects results from Graph, Maintenance, and ADX agents
2. Builds formatted context summary
3. Uses GPT-4 to synthesize professional response
4. Handles partial failures (missing agents)

**Example:**
```
Context:
  GRAPH DATA: Found 12 sensors in area 40-10
  MAINTENANCE DATA: 2 work orders found (WO#12345, WO#12346)
  SENSOR DATA [MOCK]: 60 measurements, 2 anomalies detected

Synthesized Response:
"Area 40-10 contains 12 sensors with 2 active work orders. Sensor 4038LI579 
shows a high-severity spike anomaly and has work order #12345 for valve 
replacement scheduled. Sensor 4038TI120 is operating normally with standard 
calibration work order #12346. Recommend prioritizing the valve replacement 
due to the detected anomaly."
```

## Execution Trace

Every query returns an `execution_trace` object showing exactly what happened:

```json
{
  "total_duration_ms": 2300,
  "workflow_version": "1.0",
  "agents_invoked": [
    {
      "agent_name": "graph_agent",
      "status": "success",
      "duration_ms": 800,
      "summary": "Found 12 sensors in area 40-10",
      "output": { /* full results */ }
    },
    {
      "agent_name": "maintenance_agent",
      "status": "success",
      "duration_ms": 1000,
      "summary": "Found 2 work orders across 10 sensors",
      "output": { /* work orders */ }
    },
    {
      "agent_name": "synthesizer",
      "status": "success",
      "duration_ms": 500,
      "summary": "Synthesized response from 2 agent(s)",
      "output": { /* synthesis metadata */ }
    }
  ]
}
```

## Workflow Routing Logic

The coordinator uses **conditional routing** based on query intent:

```
analyze_intent
  ↓
  Graph Agent (always runs first)
  ↓
  ┌─────────────────────────────────────┐
  │ Based on agents_to_invoke:          │
  ├─────────────────────────────────────┤
  │ - graph only     → Synthesizer      │
  │ - graph+maint    → Maintenance      │
  │ - graph+adx      → ADX              │
  │ - graph+both     → Maintenance→ADX  │
  └─────────────────────────────────────┘
  ↓
  Synthesizer (always runs last)
  ↓
  Final Response
```

## Benefits of Multi-Agent Design

1. **Modularity**: Each agent has single responsibility
2. **Scalability**: Easy to add new agents (e.g., Predictive Maintenance Agent)
3. **Transparency**: Execution trace shows which agents were consulted
4. **Efficiency**: Only invoke agents that are needed
5. **Resilience**: System works even if some agents fail
6. **Testability**: Each agent can be tested independently

## Adding a New Agent

To add a new agent (e.g., `AlertAgent`):

1. **Create agent class** in `agents/nodes/alert.py`:
```python
class AlertAgent(BaseAgent):
    def __init__(self):
        super().__init__("alert_agent")
    
    async def execute(self, state: AgentState) -> Dict[str, Any]:
        # Your logic here
        return {"alerts": [...]}
```

2. **Update workflow** in `agents/workflow.py`:
```python
# Add node
workflow.add_node("alert_agent", self._alert_agent_node)

# Add routing
workflow.add_conditional_edges("graph_agent", ..., {
    "alert": "alert_agent"
})
```

3. **Update intent classification** to detect when alert agent is needed

4. **Export from** `agents/nodes/__init__.py`

5. **Write tests** in `agents/tests/test_alert_agent.py`

## Configuration

### Environment Variables
```bash
# OpenAI (required for coordinator and synthesis)
OPENAI_API_KEY=your_key

# Neo4j (required for Graph Agent)
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password

# Maintenance MCP (optional, graceful degradation)
MAINTENANCE_MCP_URL=http://localhost:8001

# ADX MCP (optional, uses mock data if unavailable)
ADX_MCP_URL=http://localhost:8002
```

### Agent Behavior Flags

In `agents/nodes/adx.py`:
```python
self.use_mcp = False  # Set to True when ADX MCP is ready
```

## Testing

```bash
# Run all agent tests
cd backend
pytest agents/tests/ -v

# Test specific agent
pytest agents/tests/test_graph_agent.py -v

# Test workflow
pytest agents/tests/test_workflow.py -v
```

## Performance

Typical query performance:
- Graph Agent: 500-1000ms (Cypher generation + execution)
- Maintenance Agent: 800-1500ms (MCP calls per sensor)
- ADX Agent: 200-400ms (mock data) / TBD (real MCP)
- Synthesizer: 400-800ms (GPT-4 synthesis)

**Total:** 2-4 seconds for complex queries

## Error Handling

The system is designed for **graceful degradation**:

- If Maintenance MCP is unavailable → workflow continues without work orders
- If ADX returns no data → synthesizer acknowledges and focuses on available data
- If Graph Agent fails → workflow terminates (graph is foundational)
- If Synthesizer fails → fallback to concatenated context

## Future Enhancements (IDEA_BANK)

- Context-scoped queries (agents constrained to specific area/equipment)
- Parallel agent execution (Maintenance + ADX simultaneously)
- Agent result caching
- Streaming responses
- Agent performance dashboard
- User feedback loop for intent classification improvement
