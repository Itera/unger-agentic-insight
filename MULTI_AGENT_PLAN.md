# Multi-Agent Orchestration Plan

## Overview
Transform the Query Data page from a single-agent system to a multi-agent orchestration using LangGraph, where specialized agents collaborate to answer complex industrial queries.

## Current State
- Single OpenAI call generates SQL/KQL queries
- Simple context-aware responses
- Basic ADX integration via HTTP
- Maintenance service calls are direct

## Target Architecture

```
┌─────────────────────────────────────────────────────────┐
│  User Query in Query Data Page                          │
└──────────────────┬──────────────────────────────────────┘
                   │
         ┌─────────▼─────────┐
         │  Coordinator Agent │  (LangGraph State Machine)
         │  - Analyzes query  │
         │  - Plans workflow  │
         └─────────┬──────────┘
                   │
     ┌─────────────┼─────────────┬─────────────┐
     │             │             │             │
┌────▼────┐  ┌────▼────┐  ┌─────▼─────┐ ┌────▼────┐
│ Graph   │  │   ADX   │  │Maintenance│ │ Other   │
│ Agent   │  │  Agent  │  │  Agent    │ │ Agents  │
└────┬────┘  └────┬────┘  └─────┬─────┘ └────┬────┘
     │            │              │            │
     │       ┌────▼──────────────▼────────────▼────┐
     └──────►│      Synthesizer Agent              │
             │  - Combines all agent outputs       │
             │  - Generates coherent response      │
             └─────────────────────────────────────┘
```

## Example Workflows

### Example 1: "Do we have any active work orders?"
1. **Coordinator**: Determines this needs Graph + Maintenance agents
2. **Graph Agent**: Lists all sensors from Neo4j
3. **Maintenance Agent**: Takes sensor list, queries maintenance MCP for work orders
4. **Synthesizer**: Combines results into answer

### Example 2: "Do we have abnormalities in area 40-10?"
1. **Coordinator**: Needs all three agents
2. **Graph Agent**: Gets sensors and equipment in area 40-10 (runs first)
3. **ADX Agent**: Checks sensor values for abnormalities (parallel with maintenance)
4. **Maintenance Agent**: Checks work orders on those assets (parallel with ADX)
5. **Synthesizer**: Combines graph topology + sensor data + maintenance info

### Example 3: "Show me temperature sensors in S-Plant"
1. **Coordinator**: Only needs Graph agent
2. **Graph Agent**: Queries Neo4j for temperature sensors in S-Plant
3. **Synthesizer**: Formats results for user

## Branching Strategy

Each epic branches from `feature/multi-agent-orchestration` and merges back when complete:

```
main
└── feature/multi-agent-orchestration (integration branch)
    ├── epic/01-foundation → merge back
    ├── epic/02-individual-agents → merge back
    ├── epic/03-coordinator → merge back
    ├── epic/04-synthesizer → merge back
    ├── epic/05-integration → merge back
    └── epic/06-testing → merge back
```

**Workflow for Each Epic**:
1. Checkout `feature/multi-agent-orchestration` and pull latest
2. Create epic branch: `git checkout -b epic/XX-name`
3. Implement user stories
4. Commit regularly during development
5. Push epic branch when complete
6. Merge back to `feature/multi-agent-orchestration`
7. Repeat for next epic

**Testing Approach**:
- Each agent must have individual unit tests before integration
- Test agents in isolation first
- Then test orchestration end-to-end

## Implementation Epics

### Epic 1: Foundation Setup ✅ COMPLETED
**Branch**: `epic/01-foundation` (from `feature/multi-agent-orchestration`)
**Status**: Completed on 2025-10-27

**User Stories**:
- ✅ Install LangGraph, LangChain, and dependencies (updated to latest stable versions)
- ✅ Create `backend/agents/` directory structure
- ✅ Set up base agent classes and state management
- ✅ Create MCP client wrapper for Maintenance service (existing Docker MCP)
- ✅ Create stub for ADX agent (MCP client ready for when ADX MCP is finished)
- ✅ Add individual agent test files

**Files created**:
- ✅ `backend/agents/__init__.py`
- ✅ `backend/agents/base_agent.py` - Abstract base class with execution tracking
- ✅ `backend/agents/state.py` - AgentState and helper functions
- ✅ `backend/agents/mcp_client.py` - MCP client for both Maintenance and ADX
- ✅ `backend/agents/test_base_agent.py` - Unit tests for base agent
- ✅ `backend/agents/test_mcp_client.py` - Unit and integration tests for MCP client

**Testing**:
- ✅ Test base agent class with mock agent
- ✅ Test error handling and timing
- ✅ MCP client unit tests (creation, factory, URL normalization)
- ✅ MCP client integration tests (health checks, tool listing)

**Dependencies updated**:
- langgraph>=0.2.45
- langchain>=0.3.0
- langchain-openai>=0.2.0
- langchain-core>=0.3.0

### Epic 2: Individual Agents ✅ COMPLETED
**Branch**: `epic/02-individual-agents` (from `feature/multi-agent-orchestration`)
**Status**: Completed on 2025-10-27  
**Depends on**: Epic 1

**User Stories**:
- ✅ Implement Graph Agent using existing `graph_service.py` (LLM generates Cypher queries)
- ✅ Implement Maintenance Agent using MCP client wrapper
- ✅ Implement ADX Agent stub (returns mock data, ready for MCP when available)
- ✅ Each agent has clear input/output schema with execution trace
- ✅ Unit test each agent individually

**Files created**:
- ✅ `backend/agents/graph_agent.py` (180 lines) - LLM-powered Cypher generation and Neo4j execution
- ✅ `backend/agents/maintenance_agent.py` (160 lines) - MCP-based work order retrieval
- ✅ `backend/agents/adx_agent.py` (182 lines) - Stub with mock data, MCP-ready
- ✅ `backend/agents/test_graph_agent.py` (171 lines) - 9 unit tests
- ✅ `backend/agents/test_maintenance_agent.py` (157 lines) - 8 unit tests
- ✅ `backend/agents/test_adx_agent.py` (184 lines) - 10 unit tests

**Testing**:
- ✅ Graph Agent: Cypher generation, execution, error handling, markdown removal
- ✅ Maintenance Agent: Work order retrieval, sensor extraction, MCP error handling
- ✅ ADX Agent: Mock data generation, anomaly detection, sensor limits
- ✅ All 27 agent tests passing

**Agent Capabilities**:
- **Graph Agent**: Generates and executes Cypher queries via LLM, handles 50+ result limit
- **Maintenance Agent**: Retrieves work orders for sensors, limits to 10 sensors per query
- **ADX Agent**: Returns realistic mock sensor data, ready for MCP integration

### Epic 3: Coordinator Agent
**Depends on**: Epic 2

**User Stories**:
- Implement Coordinator using LangGraph
- Query analysis and intent classification
- Dynamic agent selection based on query
- Workflow orchestration with conditional routing

**Files to create**:
- `backend/agents/coordinator_agent.py`
- `backend/agents/workflows.py`

### Epic 4: Synthesizer Agent
**Depends on**: Epic 2, Epic 3

**User Stories**:
- Combine outputs from multiple agents
- Generate coherent, context-aware responses
- Handle partial failures gracefully
- Maintain conversational context

**Files to create**:
- `backend/agents/synthesizer_agent.py`

### Epic 5: Integration & API Updates
**Depends on**: Epic 4

**User Stories**:
- Update `/query/contextual` endpoint to use orchestration
- Add `/query/multi-agent` endpoint
- Implement proper error handling and logging
- Add agent execution metrics and tracing
- **Add execution trace to API response**
- **Create AgentTrace UI component for frontend**
- **Update QueryPage to display agent execution details**

**Files to modify**:
- `backend/main.py` (update endpoints, add execution_trace to response)
- `frontend/src/pages/QueryPage.js` (integrate agent trace display)

**Files to create**:
- `frontend/src/components/AgentTracePanel.jsx` (collapsible agent execution view)

### Epic 6: Testing & Documentation
**Depends on**: Epic 5

**User Stories**:
- Unit tests for each agent
- Integration tests for workflows
- End-to-end tests with example queries
- Update API documentation

**Files to create**:
- `backend/test_agents.py`
- `backend/test_orchestration.py`
- Updated README with architecture diagrams

## Technology Stack

- **LangGraph**: State machine for agent orchestration
- **LangChain**: Agent framework and LLM utilities
- **OpenAI**: LLM for coordinator and synthesizer
- **Neo4j**: Graph database (existing)
- **MCP Protocol**: For ADX and Maintenance service integration
- **FastAPI**: Backend API (existing)

## Dependencies to Add

```txt
langgraph==0.0.32
langchain==0.1.0
langchain-openai==0.0.5
langchain-core==0.1.10
```

## Key Design Decisions

1. **Graph Agent Always Runs First**: Provides context for other agents
2. **No MCP for Graph Agent**: Direct Python integration with existing `graph_service.py` - simpler and faster
3. **Parallel Execution**: ADX and Maintenance agents can run in parallel
4. **Graceful Degradation**: System works even if some agents fail
5. **State Management**: LangGraph state carries data between agents
6. **MCP Integration**: 
   - Maintenance: Uses existing MCP server (Docker → Azure)
   - ADX: Will use MCP server when available (stub implementation for now)
7. **Modular Agents**: Easy to add new agents (e.g., ADX MCP) without changing core orchestration

## Agent Execution Visibility (UI Feature)

Users will see:
1. **Primary Response**: The synthesized final answer (always visible)
2. **Agent Trace Panel** (collapsible/expandable):
   - Which agents were invoked
   - Execution order and timing
   - Individual agent outputs
   - Any errors or warnings from specific agents

### UI Mockup
```
┌─────────────────────────────────────────────────┐
│ AI Analysis Result                              │
│ ✓ Answer generated using 3 agents (2.3s)       │
├─────────────────────────────────────────────────┤
│                                                 │
│ [Final synthesized answer here...]             │
│                                                 │
│ ▼ View Agent Execution Details                 │
│   ┌───────────────────────────────────────┐   │
│   │ 1. Graph Agent (0.5s) ✓                │   │
│   │    Found 12 sensors in area 40-10     │   │
│   │    [View full output]                  │   │
│   │                                         │   │
│   │ 2. ADX Agent (1.2s) ✓                  │   │
│   │    Checked 12 sensors for anomalies   │   │
│   │    Found 2 abnormal readings          │   │
│   │    [View full output]                  │   │
│   │                                         │   │
│   │ 3. Maintenance Agent (0.6s) ✓          │   │
│   │    Found 1 active work order          │   │
│   │    [View full output]                  │   │
│   └───────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

### Backend Response Structure
```json
{
  "query": "Do we have abnormalities in area 40-10?",
  "response": "Final synthesized answer...",
  "timestamp": "2024-01-15T10:30:00Z",
  "execution_trace": {
    "total_duration_ms": 2300,
    "agents_invoked": [
      {
        "agent_name": "graph_agent",
        "duration_ms": 500,
        "status": "success",
        "summary": "Found 12 sensors in area 40-10",
        "output": {
          "sensors": [...],
          "equipment": [...]
        }
      },
      {
        "agent_name": "adx_agent",
        "duration_ms": 1200,
        "status": "success",
        "summary": "Checked 12 sensors, found 2 abnormalities",
        "output": {
          "abnormal_sensors": [...]
        }
      },
      {
        "agent_name": "maintenance_agent",
        "duration_ms": 600,
        "status": "success",
        "summary": "Found 1 active work order",
        "output": {
          "work_orders": [...]
        }
      }
    ]
  }
}
```

## Success Criteria

- [ ] User can ask complex queries spanning multiple data sources
- [ ] System intelligently routes queries to appropriate agents
- [ ] Responses combine information from multiple agents coherently
- [ ] **Users can view which agents were used and their individual outputs**
- [ ] **Agent execution trace is returned with timing and status**
- [ ] Performance is acceptable (< 5 seconds for most queries)
- [ ] System handles failures gracefully (partial results, clear errors)
- [ ] Code is well-tested and documented

## Future Enhancements

- Add more specialized agents (analytics, predictions, recommendations)
- Implement agent learning from user feedback
- Add streaming responses for real-time updates
- Create agent performance dashboard
- Multi-turn conversations with memory
