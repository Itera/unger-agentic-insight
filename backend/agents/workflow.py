"""
Multi-Agent Workflow Coordinator using LangGraph

Orchestrates the execution of specialized agents based on query intent.
Uses LangGraph StateGraph for workflow management with conditional routing.
"""

from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from agents.state import AgentState, create_initial_state, build_execution_trace
from agents.nodes import GraphAgent, MaintenanceAgent, ADXAgent
from agents.nodes.synthesizer import SynthesizerAgent
from core.dependencies import get_openai_client


class WorkflowCoordinator:
    """
    Coordinates multi-agent workflow execution using LangGraph.
    
    Analyzes queries, determines which agents to invoke, and orchestrates
    their execution through a LangGraph StateGraph.
    """
    
    def __init__(self):
        """Initialize coordinator and build workflow graph."""
        self.openai_client = get_openai_client()
        
        # Initialize agents
        self.graph_agent = GraphAgent()
        self.maintenance_agent = MaintenanceAgent()
        self.adx_agent = ADXAgent()
        self.synthesizer_agent = SynthesizerAgent()
        
        # Build workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """
        Build LangGraph StateGraph for workflow execution.
        
        Returns:
            Compiled StateGraph
        """
        # Create state graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("analyze_intent", self._analyze_intent_node)
        workflow.add_node("graph_agent", self._graph_agent_node)
        workflow.add_node("maintenance_agent", self._maintenance_agent_node)
        workflow.add_node("adx_agent", self._adx_agent_node)
        workflow.add_node("synthesizer", self._synthesizer_node)
        
        # Define edges with conditional routing
        workflow.set_entry_point("analyze_intent")
        
        # After intent analysis, always run graph agent first
        workflow.add_edge("analyze_intent", "graph_agent")
        
        # After graph agent, conditionally route to maintenance/ADX or directly to synthesizer
        workflow.add_conditional_edges(
            "graph_agent",
            self._route_after_graph,
            {
                "maintenance": "maintenance_agent",
                "adx": "adx_agent",
                "both": "maintenance_agent",  # Will route to ADX after
                "synthesizer": "synthesizer"
            }
        )
        
        # After maintenance, check if ADX is also needed
        workflow.add_conditional_edges(
            "maintenance_agent",
            self._route_after_maintenance,
            {
                "adx": "adx_agent",
                "synthesizer": "synthesizer"
            }
        )
        
        # After ADX, always go to synthesizer
        workflow.add_edge("adx_agent", "synthesizer")
        
        # Synthesizer is the final node
        workflow.add_edge("synthesizer", END)
        
        return workflow.compile()
    
    def _analyze_intent_node(self, state: AgentState) -> AgentState:
        """
        Analyze query intent and determine which agents to invoke.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with agents_to_invoke list
        """
        query = state["query"]
        
        # Use LLM to classify intent
        intent_prompt = f"""Analyze this industrial data query and determine which data sources are needed.

Query: "{query}"

Available data sources:
- GRAPH: Neo4j graph database with plants, areas, equipment, and sensors
- MAINTENANCE: Work orders, maintenance schedules, and asset status
- ADX: Real-time sensor measurements, time-series data, and anomalies

Respond with a JSON object containing:
{{
  "needs_graph": true/false,
  "needs_maintenance": true/false,
  "needs_adx": true/false,
  "reasoning": "brief explanation"
}}

Examples:
- "What sensors are in area 40-10?" → {{"needs_graph": true, "needs_maintenance": false, "needs_adx": false}}
- "Do we have work orders for pump P-101?" → {{"needs_graph": true, "needs_maintenance": true, "needs_adx": false}}
- "Show me abnormal temperature readings" → {{"needs_graph": true, "needs_maintenance": false, "needs_adx": true}}
- "Equipment status with maintenance and sensor data" → {{"needs_graph": true, "needs_maintenance": true, "needs_adx": true}}

Your analysis (JSON only):"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an intent classification expert. Respond only with valid JSON."},
                    {"role": "user", "content": intent_prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            import json
            intent = json.loads(response.choices[0].message.content.strip())
            
            # Build agents list (Graph always runs first)
            agents = ["graph"]
            if intent.get("needs_maintenance"):
                agents.append("maintenance")
            if intent.get("needs_adx"):
                agents.append("adx")
            
            state["agents_to_invoke"] = agents
            
        except Exception as e:
            # Fallback: invoke all agents if classification fails
            print(f"Intent classification failed: {e}")
            state["agents_to_invoke"] = ["graph", "maintenance", "adx"]
        
        return state
    
    def _graph_agent_node(self, state: AgentState) -> AgentState:
        """Execute Graph Agent node."""
        import asyncio
        return asyncio.run(self.graph_agent.run(state))
    
    def _maintenance_agent_node(self, state: AgentState) -> AgentState:
        """Execute Maintenance Agent node."""
        import asyncio
        return asyncio.run(self.maintenance_agent.run(state))
    
    def _adx_agent_node(self, state: AgentState) -> AgentState:
        """Execute ADX Agent node."""
        import asyncio
        return asyncio.run(self.adx_agent.run(state))
    
    def _synthesizer_node(self, state: AgentState) -> AgentState:
        """Execute Synthesizer Agent node."""
        import asyncio
        return asyncio.run(self.synthesizer_agent.run(state))
    
    def _route_after_graph(self, state: AgentState) -> str:
        """
        Determine routing after graph agent completes.
        
        Args:
            state: Current workflow state
            
        Returns:
            Next node name
        """
        agents_to_invoke = state.get("agents_to_invoke", ["graph"])
        
        needs_maintenance = "maintenance" in agents_to_invoke
        needs_adx = "adx" in agents_to_invoke
        
        if needs_maintenance and needs_adx:
            return "both"
        elif needs_maintenance:
            return "maintenance"
        elif needs_adx:
            return "adx"
        else:
            return "synthesizer"
    
    def _route_after_maintenance(self, state: AgentState) -> str:
        """
        Determine routing after maintenance agent completes.
        
        Args:
            state: Current workflow state
            
        Returns:
            Next node name
        """
        agents_to_invoke = state.get("agents_to_invoke", [])
        
        if "adx" in agents_to_invoke:
            return "adx"
        else:
            return "synthesizer"
    
    async def run(self, query: str, user_request: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute workflow for a given query.
        
        Args:
            query: Natural language query
            user_request: Additional request metadata
            
        Returns:
            Dictionary with response and execution trace
        """
        # Create initial state
        initial_state = create_initial_state(query, user_request or {})
        
        # Execute workflow
        final_state = self.workflow.invoke(initial_state)
        
        # Build execution trace
        execution_trace = build_execution_trace(final_state)
        
        return {
            "query": query,
            "response": final_state.get("synthesized_response", "No response generated"),
            "execution_trace": execution_trace.dict(),
            "errors": final_state.get("errors", [])
        }


# Singleton instance
_coordinator = None


def get_coordinator() -> WorkflowCoordinator:
    """
    Get or create workflow coordinator singleton.
    
    Returns:
        WorkflowCoordinator instance
    """
    global _coordinator
    if _coordinator is None:
        _coordinator = WorkflowCoordinator()
    return _coordinator
