"""
Synthesizer Agent - Multi-Agent Output Combination

Combines outputs from Graph, Maintenance, and ADX agents into a coherent,
natural language response using LLM.
"""

from typing import Dict, Any
from agents.nodes.base import BaseAgent
from agents.state import AgentState
from core.dependencies import get_openai_client


class SynthesizerAgent(BaseAgent):
    """
    Agent that synthesizes outputs from multiple agents into final response.
    
    Uses LLM to combine structured data from specialized agents into
    a coherent, context-aware natural language answer.
    """
    
    def __init__(self):
        super().__init__("synthesizer")
        self.openai_client = get_openai_client()
    
    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Synthesize final response from agent outputs.
        
        Args:
            state: Current workflow state with agent results
            
        Returns:
            Dictionary with synthesized response
        """
        if not self.openai_client:
            raise RuntimeError("OpenAI client not available")
        
        query = state["query"]
        
        # Collect agent outputs
        graph_result = state.get("graph_result")
        maintenance_result = state.get("maintenance_result")
        adx_result = state.get("adx_result")
        
        # Build context from agent outputs
        context = self._build_context(graph_result, maintenance_result, adx_result)
        
        # Generate synthesized response
        response = self._synthesize_response(query, context, state)
        
        # Store in state
        state["synthesized_response"] = response
        
        return {
            "response": response,
            "agents_used": self._get_agents_used(state)
        }
    
    def _build_context(
        self,
        graph_result: Dict[str, Any],
        maintenance_result: Dict[str, Any],
        adx_result: Dict[str, Any]
    ) -> str:
        """
        Build context string from agent outputs.
        
        Args:
            graph_result: Graph agent output
            maintenance_result: Maintenance agent output
            adx_result: ADX agent output
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        # Graph context
        if graph_result:
            result_count = graph_result.get("result_count", 0)
            if result_count > 0:
                context_parts.append(f"GRAPH DATA ({result_count} results):")
                # Include sample of results (first 5)
                results = graph_result.get("results", [])[:5]
                for i, result in enumerate(results, 1):
                    context_parts.append(f"  {i}. {result}")
                if result_count > 5:
                    context_parts.append(f"  ... and {result_count - 5} more results")
            else:
                context_parts.append("GRAPH DATA: No results found")
        
        # Maintenance context
        if maintenance_result and not maintenance_result.get("error"):
            wo_count = maintenance_result.get("work_order_count", 0)
            if wo_count > 0:
                context_parts.append(f"\nMAINTENANCE DATA ({wo_count} work orders):")
                work_orders = maintenance_result.get("work_orders", [])[:3]
                for i, wo in enumerate(work_orders, 1):
                    context_parts.append(f"  {i}. WO#{wo.get('nr', 'N/A')}: {wo.get('short_description', 'No description')}")
                if wo_count > 3:
                    context_parts.append(f"  ... and {wo_count - 3} more work orders")
            else:
                context_parts.append("\nMAINTENANCE DATA: No work orders found")
        elif maintenance_result and maintenance_result.get("error"):
            context_parts.append(f"\nMAINTENANCE DATA: Unavailable ({maintenance_result['error']})")
        
        # ADX context
        if adx_result and not adx_result.get("error"):
            measurement_count = len(adx_result.get("measurements", []))
            anomaly_count = len(adx_result.get("anomalies", []))
            
            if measurement_count > 0:
                mock_note = " [MOCK DATA]" if adx_result.get("mock_data") else ""
                context_parts.append(f"\nSENSOR DATA{mock_note} ({measurement_count} measurements):")
                
                if anomaly_count > 0:
                    context_parts.append(f"  ⚠️  {anomaly_count} anomalies detected:")
                    for anomaly in adx_result.get("anomalies", [])[:3]:
                        context_parts.append(
                            f"    - {anomaly['sensor_name']}: {anomaly['anomaly_type']} "
                            f"(severity: {anomaly['severity']})"
                        )
                else:
                    context_parts.append("  ✓ All sensors operating normally")
            else:
                context_parts.append("\nSENSOR DATA: No measurements available")
        elif adx_result and adx_result.get("error"):
            context_parts.append(f"\nSENSOR DATA: Unavailable ({adx_result['error']})")
        
        return "\n".join(context_parts)
    
    def _synthesize_response(
        self,
        query: str,
        context: str,
        state: AgentState
    ) -> str:
        """
        Use LLM to synthesize final response.
        
        Args:
            query: Original user query
            context: Formatted context from agents
            state: Current workflow state
            
        Returns:
            Natural language response
        """
        # Check for errors
        errors = state.get("errors", [])
        error_note = ""
        if errors:
            error_note = f"\n\nNote: Some agents encountered errors:\n" + "\n".join(f"- {e}" for e in errors)
        
        synthesis_prompt = f"""You are an industrial data analyst. Synthesize a clear, actionable response to the user's query based on the data provided by our specialized systems.

User Query: "{query}"

Available Data:
{context}{error_note}

Instructions:
1. Provide a direct answer to the user's question
2. Cite specific data points from the context
3. Highlight any important findings (anomalies, work orders, patterns)
4. If data is incomplete, acknowledge it briefly but focus on what IS available
5. Use clear, professional language suitable for plant operations
6. Keep the response concise (2-4 paragraphs max)

Your response:"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert industrial data analyst providing insights for plant operations."},
                    {"role": "user", "content": synthesis_prompt}
                ],
                temperature=0.3,
                max_tokens=600
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            # Fallback to basic concatenation if synthesis fails
            return f"Query: {query}\n\n{context}\n\n(Note: Response synthesis failed: {e})"
    
    def _get_agents_used(self, state: AgentState) -> list:
        """Get list of agents that were successfully executed."""
        agents_used = []
        for trace in state.get("execution_trace", []):
            if trace.status == "success" and trace.agent_name != "synthesizer":
                agents_used.append(trace.agent_name)
        return agents_used
    
    def _generate_summary(self, output: Dict[str, Any]) -> str:
        """Generate summary of synthesis."""
        agents_used = output.get("agents_used", [])
        return f"Synthesized response from {len(agents_used)} agent(s)"
    
    def _store_output(self, state: AgentState, output: Dict[str, Any]) -> None:
        """Synthesizer already stores in synthesized_response field."""
        pass  # Response already stored in execute()
