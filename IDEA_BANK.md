# Idea Bank

Future features and enhancements to consider after multi-agent implementation.

## Contextual Chat Integration

**Status:** Future Enhancement  
**Priority:** Medium  
**Dependencies:** Multi-agent orchestration (Epic 1-6)

### Overview
Extend the multi-agent chat system to support contextual, scoped conversations embedded directly in navigation pages (Areas, Equipment, Sensors).

### Current State
- Query Page provides global chat with all data
- Agents automatically narrow scope based on queries
- No contextual chat UI in navigation pages

### Proposed Enhancement

#### Option 1: Contextual Chat Panels
Embed collapsible chat panels on Area/Equipment/Sensor pages:
```
┌─────────────────────────────────────────────────┐
│ Equipment: Pump P-101                  [💬 Ask] │
├─────────────────────────────────────────────────┤
│ Status: Active    |  Sensors: 12               │
│                                                  │
│ ┌─ Chat about Pump P-101 ──────────────────┐   │
│ │ 🤖 I can answer about this equipment...   │   │
│ │ [What's the vibration trend?_______] ➤    │   │
│ └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

#### Option 2: Quick Context Toggle
Add "Focus on [X]" button on Query Page when navigating from specific pages:
```
Query Page Header:
┌────────────────────────────────────────┐
│ 🎯 Focused on: Area 40-10    [✕ Clear] │
│ [Ask about this area...]               │
└────────────────────────────────────────┘
```

### Technical Implementation

**Backend Changes:**
- Modify `api/query.py` to accept optional `context` parameter again
- Update coordinator to constrain Graph Agent when context exists
- Add context serialization to response

**Frontend Changes:**
- Create `ContextChatPanel.jsx` component
- Update Area/Equipment/Sensor pages with chat integration
- Sync context with NavigationContext provider

**Agent Behavior:**
```python
# In coordinator workflow
if state.context:
    # Scoped mode - Graph Agent constrained to context
    graph_result = await graph_agent.execute(
        query=query,
        constraint=f"LIMIT TO {state.context['nodeType']}: {state.context['nodeName']}"
    )
else:
    # Global mode - Graph Agent explores freely
    graph_result = await graph_agent.execute(query=query)
```

### Benefits
- **Natural workflow**: Ask questions while viewing specific equipment
- **Reduced cognitive load**: Users don't need to specify context in query
- **Faster responses**: Pre-scoped queries are more efficient
- **Progressive disclosure**: Advanced users still have Query Page

### Open Questions
1. Should context be automatic or user-toggled?
2. Where should agent trace be displayed in contextual chat?
3. Should contextual chat support multi-turn conversations?
4. How to handle "exit context" gracefully?

---

## Other Future Ideas

### 1. Agent Performance Dashboard
Monitor agent execution metrics, success rates, and performance over time.

### 2. Multi-turn Conversations with Memory
Add conversation history and context memory for follow-up questions.

### 3. Streaming Responses
Real-time agent execution updates instead of waiting for full completion.

### 4. Agent Learning from Feedback
User ratings on responses to improve agent selection logic.

### 5. Predictive Maintenance Agent
New agent that analyzes trends to predict equipment failures.

### 6. Custom Agent Builder
Allow users to create specialized agents for specific workflows.

---

**Note:** Review and prioritize these ideas after completing multi-agent orchestration core functionality.
