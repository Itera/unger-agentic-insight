# Hierarchical Data Navigation - Feature Plan

## Development Workflow Rules

1. **Branch Structure**: Each Epic gets its own branch from `feature/hierarchical-data-navigation`
   - Epic 1: `epic/graph-database-integration`
   - Epic 2: `epic/graph-based-navigation-ui` 
   - Epic 3: `epic/contextual-ai-chat`
   - Epic 4: `epic/graph-visualization`
   - Epic 5: `epic/data-integration-foundation`

2. **Commit Strategy**: Commit after completing each User Story
   - Clear commit messages referencing US number: "feat: US-001 - Set up Neo4j connection"
   - Each US should be a logical, working increment

3. **Integration**: Merge epic branches back to `feature/hierarchical-data-navigation` when complete

4. **Initial Commit**: Commit this plan document before starting implementation

## Vision
Create a contextual, hierarchical exploration interface that allows users to navigate from factory-wide view down to individual sensors, with AI chat scoped to their current context and relevant data sources.

## Core Concept
Users navigate through a graph-based exploration interface:
**Plants (S-plant/T-plant)** → **Areas** → **Equipment/Sensors** → **Connected Entities**

Key principles:
- **All graph nodes** are explorable (not just predefined entity types)
- **Non-hierarchical relationships** - graph serves as ontology showing connections
- **Contextual scope** - AI chat limited to current selection + connected nodes
- **Visual + textual** context indicators
- **Graph visualization** within scope to show relationships
- **Expandable detail views** rather than separate navigation pages

## User Stories

### Epic 1: Graph Database Integration
- [ ] **US-001**: As a developer, I need to connect to the existing Neo4j graph database so that I can query asset relationships
- [ ] **US-002**: As a developer, I need to create graph query functions so that I can retrieve hierarchical asset data
- [ ] **US-003**: As a developer, I need to map graph entities to the existing sensor data so that I can provide enriched context

### Epic 2: Graph-Based Navigation UI
- [x] **US-004**: As a user, I want to see a plant overview with area cards so that I can choose which part of the facility to explore
- [x] **US-005**: As a user, I want to click on any graph node and see its connected entities so that I can understand relationships
- [x] **US-006**: As a user, I want expandable detail views for nodes so that I can explore deeper without losing context
- [x] **US-007**: As a user, I want to see my current path/context so that I understand what scope I'm exploring
- [x] **US-008**: As a user, I want to see orphaned sensors (area-connected but not equipment-specific) so that I can still access all available data

### Epic 3: Contextual AI Chat
- [x] **US-009**: As a user, I want the AI chat to be scoped to my current selection + connected nodes so that queries are more relevant and precise
- [x] **US-010**: As a user, I want to see what context the AI is using (both visually and textually) so that I understand the scope of responses
- [x] **US-011**: As a user, I want to toggle between scoped and global chat modes so that I can choose my query scope
- [x] **US-012**: As a user, I want the AI to understand graph relationships so that it can provide insights about connected entities
- [x] **US-013**: As a user, I want the AI to clearly indicate when it doesn't have data rather than making up answers

### Epic 4: Graph Visualization - ❌ REMOVED
- [x] ~~**US-014**: Visual representation of current scope~~ - Removed due to poor UX
- [x] ~~**US-015**: Discover related equipment through visualization~~ - Removed due to poor UX  
- [x] ~~**US-016**: Clear indication of orphaned sensors~~ - Removed due to poor UX
- ✅ **Enhanced Neo4j Properties**: Added UI support for new sensor units, equipment types, and source tags

### Epic 5: Data Integration (Foundation)
- [ ] **US-017**: As a user, I want the AI to use graph node properties and relationships so that I get contextual responses based on available data
- [ ] **US-018**: As a user, I want the system to suggest related sensors/assets based on graph connections so that I can discover relevant information
- [ ] **US-019**: As a user, I want clear indication when asking about live/maintenance data that isn't available yet so that I have realistic expectations

## Technical Tasks

### Phase 1: Foundation (Graph Integration)
- [x] **T-001**: Set up Neo4j connection in backend
- [x] **T-002**: Create graph query service with basic CRUD operations
- [x] **T-003**: Create API endpoints for hierarchical data retrieval
- [ ] **T-004**: Map existing sensor data to graph entities
- [ ] **T-005**: Create graph data models (Area, Asset, Sensor, Equipment)

### Phase 2: Navigation Interface
- [x] **T-006**: Create hierarchical navigation component structure
- [x] **T-007**: Build area overview page with clickable cards
- [x] **T-008**: Build asset detail page with sensor listings
- [x] **T-009**: Implement breadcrumb navigation component
- [ ] **T-010**: Add routing for hierarchical paths (/area/75-12/asset/7512TIC301)

### Phase 3: Contextual Chat Integration
- [ ] **T-011**: Modify chat service to accept context parameters
- [ ] **T-012**: Create context management system (scope tracking)
- [ ] **T-013**: Update AI prompts to use hierarchical context
- [ ] **T-014**: Add context indicator in chat UI
- [ ] **T-015**: Implement context toggle (scoped vs global)

### Phase 4: Advanced Features
- [ ] **T-016**: Add related entity suggestions based on graph relationships
- [ ] **T-017**: Implement query expansion using graph data
- [ ] **T-018**: Add maintenance data integration hooks (for future MCP)
- [ ] **T-019**: Performance optimization for large hierarchies
- [ ] **T-020**: Add caching layer for graph queries

## Data Flow

```
Graph DB (Neo4j)     →    Backend Service    →    Frontend UI
     ↓                          ↓                     ↓
Asset Relationships   →   Context Management  →   Navigation Cards
     ↓                          ↓                     ↓  
Sensor Mappings      →   Scoped AI Queries   →   Contextual Chat
```

## API Design (Draft)

```
GET /api/hierarchy/areas                    # Get all areas
GET /api/hierarchy/areas/{area_id}/assets   # Get assets in area  
GET /api/hierarchy/assets/{asset_id}        # Get asset details + sensors
GET /api/context/{path}                     # Get AI context for path
POST /api/query/scoped                      # Scoped AI query
```

## UI Components (Draft)

```
- HierarchyBreadcrumb: Shows current path
- EntityCard: Reusable card for areas/assets/sensors  
- NavigationGrid: Grid layout for cards
- ContextualChat: Chat with scope indicator
- ScopeToggle: Switch between global/scoped mode
```

## Remaining Questions for Discussion

1. **Graph Visualization Library**: What would you prefer for the graph visualization? (D3.js, vis.js, react-force-graph, or something else?)
2. **Detail View Layout**: For expandable details, should we use:
   - Side panel that slides out?
   - Modal/overlay?
   - In-place expansion with accordion-style?
3. **Context Scope Definition**: When scoped to a node, should context include:
   - Only the selected node + directly connected nodes?
   - Selected node + connected nodes + their immediate connections?
   - Configurable depth (1-2 hops from selection)?
4. **Orphaned Sensor Handling**: How should we display sensors connected to areas but not equipment?
   - Separate "Unclassified Sensors" card in each area?
   - Mixed in with equipment but clearly labeled?
   - Special category/filter?
5. **Performance Expectations**: Rough scale of your graph?
   - How many nodes total?
   - Max connections per node?
   - Any performance concerns?

## Success Criteria

- [ ] Users can navigate from factory overview to individual sensors
- [ ] AI chat provides contextually relevant responses based on current location
- [ ] Graph relationships enhance query understanding and responses  
- [ ] Navigation is intuitive with clear breadcrumbs and context indicators
- [ ] System performs well with expected data volume
- [ ] Foundation is ready for future maintenance API integration

## Out of Scope (Future Phases)

- Maintenance API MCP integration (separate feature)
- ADX MCP expansion (separate feature)  
- Real-time data visualization in cards
- Advanced graph visualization components
- User preferences/saved contexts
- Advanced analytics/ML integration