# Frontend Integration Notes for Multi-Agent System

## API Response Changes

The `/query` and `/query/contextual` endpoints now return additional fields:

```typescript
interface QueryResponse {
  query: string;
  response: string;
  data: any[] | null;  // Now null, data is in execution_trace
  source: string;      // Now "multi-agent"
  timestamp: string;
  context_used: any | null;
  execution_trace: ExecutionTrace | null;  // NEW
  errors: string[] | null;                  // NEW
}

interface ExecutionTrace {
  total_duration_ms: number;
  workflow_version: string;
  agents_invoked: AgentResult[];
}

interface AgentResult {
  agent_name: string;         // "graph_agent", "maintenance_agent", "adx_agent", "synthesizer"
  status: string;              // "success" | "error" | "skipped"
  duration_ms: number;
  summary: string;             // Human-readable summary
  output: any | null;          // Agent-specific output
  error: string | null;
  timestamp: string;
}
```

## UI Changes Needed

### 1. Remove ADX Checkbox (COMPLETED in requirements)
- ~~Remove `useAdx` state and checkbox from `QueryPage.js`~~
- ~~ADX agent is now automatically invoked by coordinator~~

### 2. Add AgentTracePanel Component (Optional Enhancement)

**Location:** `frontend/src/components/AgentTracePanel.jsx`

```jsx
import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Clock, CheckCircle, XCircle } from 'lucide-react';

const AgentTracePanel = ({ executionTrace }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  if (!executionTrace || !executionTrace.agents_invoked) {
    return null;
  }
  
  const { total_duration_ms, agents_invoked } = executionTrace;
  const successCount = agents_invoked.filter(a => a.status === 'success').length;
  
  return (
    <div className="mt-4 border border-stone-200 rounded-lg overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-4 bg-stone-50 hover:bg-stone-100 transition-colors"
      >
        <div className="flex items-center gap-2">
          {isExpanded ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
          <span className="font-semibold">Agent Execution Details</span>
          <span className="text-sm text-stone-600">
            ({successCount}/{agents_invoked.length} agents, {(total_duration_ms / 1000).toFixed(2)}s)
          </span>
        </div>
      </button>
      
      {isExpanded && (
        <div className="p-4 space-y-3 bg-white">
          {agents_invoked.map((agent, index) => (
            <div key={index} className="border-l-4 border-stone-300 pl-4">
              <div className="flex items-center gap-2 mb-1">
                {agent.status === 'success' ? (
                  <CheckCircle size={16} className="text-green-600" />
                ) : (
                  <XCircle size={16} className="text-red-600" />
                )}
                <span className="font-medium">{agent.agent_name}</span>
                <span className="text-sm text-stone-500">
                  ({agent.duration_ms}ms)
                </span>
              </div>
              <p className="text-sm text-stone-700">{agent.summary}</p>
              {agent.error && (
                <p className="text-sm text-red-600 mt-1">Error: {agent.error}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AgentTracePanel;
```

### 3. Update QueryPage.js

```jsx
import AgentTracePanel from '../components/AgentTracePanel';

// In your response rendering:
{response && (
  <div className="mt-6">
    <div className="prose max-w-none">
      {response.response}
    </div>
    
    {/* NEW: Add agent trace panel */}
    <AgentTracePanel executionTrace={response.execution_trace} />
    
    {/* Show errors if any */}
    {response.errors && response.errors.length > 0 && (
      <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
        <h4 className="font-semibold text-red-800 mb-2">Errors:</h4>
        <ul className="list-disc pl-5 text-sm text-red-700">
          {response.errors.map((error, i) => (
            <li key={i}>{error}</li>
          ))}
        </ul>
      </div>
    )}
  </div>
)}
```

## Testing the Integration

1. **Start backend:** `cd backend && uvicorn main:app --reload --port 8000`
2. **Start frontend:** `cd frontend && npm run dev`
3. **Test queries:**
   - "What sensors are in the plant?" → Should invoke graph_agent only
   - "Show me work orders" → Should invoke graph_agent + maintenance_agent
   - "Are there any sensor anomalies?" → Should invoke all three agents
4. **Check execution trace** in browser DevTools Network tab

## Benefits

- **Transparency:** Users see which agents were consulted
- **Performance Insights:** Duration per agent visible
- **Error Visibility:** Clear indication if any agent failed
- **Educational:** Helps users understand the multi-agent system

## Future Enhancements (IDEA_BANK)

- Collapsible agent output details (show actual Cypher queries, work orders, etc.)
- Visual workflow diagram
- Agent invocation history/analytics
- Real-time streaming updates as agents execute
