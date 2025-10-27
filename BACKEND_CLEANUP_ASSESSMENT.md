# Backend Cleanup Assessment

## 🎯 Current State Analysis

### Active Endpoints (Used by Frontend)

#### ✅ **Graph Navigation Endpoints** (ACTIVE - PRIMARY USE)
- `GET /api/graph/plants` - List all plants
- `GET /api/graph/plants/{plant_name}/areas` - Get areas for a plant
- `GET /api/graph/areas/{area_name}/equipment` - Get equipment in an area
- `GET /api/graph/areas/{area_name}/sensors/categorized` - Get categorized sensors
- `GET /api/graph/context/{node_type}/{node_name}` - Get contextual subgraph for AI

#### ✅ **Entity Detail Endpoints** (ACTIVE)
- `GET /api/entities/{entity_type}/{entity_id}` - Get entity details
- `GET /api/entities/{entity_type}/{entity_id}/connected` - Get connected entities

#### ✅ **Query/AI Endpoints** (ACTIVE)
- `POST /query` - Global AI queries
- `POST /query/contextual` - Scoped AI queries with context

#### ✅ **Work Orders Endpoints** (ACTIVE)
- `GET /api/sensors/{sensor_name}/work-orders` - Get work orders for sensor
- `GET /api/equipment/{equipment_name}/work-orders` - Get work orders for equipment
- `GET /api/areas/{area_name}/work-orders` - Get work orders for area

#### ✅ **Health Check** (ACTIVE)
- `GET /health` - System health status

---

### ❌ **Unused/Legacy Code to Remove**

#### 1. **PostgreSQL Database Code** (Lines 39-51, 464-472, etc.)
```python
DATABASE_URL = os.getenv("DATABASE_URL", ...)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(...)
```
**Reason**: Not using PostgreSQL - Neo4j is the primary data store

#### 2. **CSV Import Endpoints & Functions** (Lines 164-353)
- `POST /import-csv` - CSV upload endpoint
- `determine_table_name()` - CSV format detection
- `import_hmi_data()` - HMI data import
- `import_tag_config()` - Tag config import
- `import_itera_data()` - Itera measurements import
**Reason**: User confirmed CSV import is not in use

#### 3. **Import Status Endpoints** (Lines 770-783)
- `GET /tables` - List database tables
- `GET /import-status` - CSV import tracking
**Reason**: Related to CSV import, no longer needed

#### 4. **Mock/Fallback Data Functions** (Lines 799-856, 1080-1194)
- Mock plants data
- Mock areas data
- Mock entities data
**Reason**: Neo4j should always be available; no need for mock fallbacks

#### 5. **Unused Area Detail Endpoint** (Lines 1051-1092)
- `GET /api/areas/{area_name}` - Get area details
**Reason**: Frontend uses graph endpoints, not this one

#### 6. **Unused Area Entities Endpoint** (Lines 1095-1194)
- `GET /api/areas/{area_name}/entities` - Get all area entities
**Reason**: Frontend uses more specific graph endpoints

#### 7. **ADX (Azure Data Explorer) Functions** (Lines 449-472, 714-742)
- `get_schema_info()` with ADX support
- `execute_adx_query_from_response()`
**Reason**: User has `use_adx` toggle but likely not configured; could be removed or kept as future feature

#### 8. **SQL Query Execution** (Lines 745-767)
- `execute_sql_query_from_response()`
**Reason**: No PostgreSQL database

#### 9. **Data Mapping Endpoints** (Lines 986-1048)
- `GET /api/mapping/area/{area_id}/sensors`
- `GET /api/mapping/node/{node_type}/{node_name}`
- `GET /api/mapping/enriched/{node_type}/{node_name}`
- `GET /api/mapping/search/sensors`
- `GET /api/mapping/area/{area_id}/quality`
**Reason**: Not used by frontend; data mapping service may be unused

#### 10. **Empty `agents/` Folder**
**Reason**: Only contains `__pycache__`, no actual code

#### 11. **Other Unused Graph Endpoints**
- `GET /api/graph/areas/{area_name}/sensors` - Non-categorized version (superseded)
- `GET /api/graph/equipment/{equipment_name}/sensors` - Not used by frontend
- `GET /api/graph/nodes/{node_type}/{node_name}` - Similar to entities endpoint
- `GET /api/suggestions/{node_type}/{node_name}` - Not visible in frontend code
- `GET /api/graph/search` - Search functionality not implemented in frontend
- `GET /api/work-orders/test-transform/{sensor_name}` - Test endpoint

---

## 📁 Proposed New Structure

```
backend/
├── main.py                      # FastAPI app + startup only
├── core/
│   ├── __init__.py
│   ├── config.py               # Environment variables & settings
│   └── dependencies.py         # Service initialization (Neo4j, OpenAI, etc.)
├── api/
│   ├── __init__.py
│   ├── graph.py                # Graph navigation endpoints
│   ├── entities.py             # Entity detail endpoints
│   ├── query.py                # AI query endpoints
│   └── maintenance.py          # Work order endpoints
├── models/
│   ├── __init__.py
│   ├── requests.py             # Pydantic request models
│   └── responses.py            # Pydantic response models
├── utils/
│   ├── __init__.py
│   ├── serializers.py          # Neo4j data serialization
│   └── mappers.py              # Entity type mapping
├── services/
│   ├── __init__.py
│   ├── graph_service.py        # (existing - keep)
│   ├── maintenance_service.py  # (existing - keep)
│   └── sensor_utils.py         # (existing - keep)
├── tests/
│   ├── __init__.py
│   ├── test_graph_service.py
│   ├── test_maintenance_service.py
│   └── test_sensor_utils.py
├── requirements.txt
└── Dockerfile
```

---

## 🔧 Cleanup Steps (Priority Order)

### Phase 1: Assess Dependencies (DO FIRST)
1. ✅ Check if `data_mapping_service` is actually used
2. ✅ Confirm ADX is configured and needed
3. ✅ Verify which imports are actually required

### Phase 2: Remove Dead Code
1. Remove PostgreSQL database setup
2. Remove CSV import endpoints and functions
3. Remove import status endpoints
4. Remove mock/fallback data functions
5. Remove unused endpoints (see list above)
6. Remove `agents/` folder if confirmed empty
7. Remove SQL query execution
8. Remove ADX code if not configured

### Phase 3: Reorganize Structure
1. Create new directory structure
2. Extract config to `core/config.py`
3. Extract service initialization to `core/dependencies.py`
4. Split endpoints into routers (`api/`)
5. Extract Pydantic models to `models/`
6. Extract helper functions to `utils/`
7. Move tests to `tests/` directory

### Phase 4: Update Imports
1. Update all import statements
2. Update main.py to register routers
3. Verify all endpoints still work

### Phase 5: Documentation & Standards
1. Add docstrings to all functions
2. Ensure single-responsibility principle
3. Update README.md with new structure
4. Add comments where needed

---

## 📊 Estimated Line Reductions

| Category | Lines to Remove |
|----------|----------------|
| PostgreSQL code | ~100 |
| CSV Import | ~250 |
| Mock data | ~150 |
| Unused endpoints | ~300 |
| ADX (if removed) | ~100 |
| Duplicate/unused | ~50 |
| **Total Reduction** | **~950 lines** |
| **New main.py** | **~50-100 lines** |
| **Final Total (split)** | **~600 lines** across multiple files |

---

## ⚠️ Questions to Confirm

1. **Data Mapping Service**: Is `data_mapping_service` used anywhere? The endpoints aren't called by frontend.
2. **ADX Configuration**: Is Azure Data Explorer actually configured and used?
3. **Search Functionality**: Should we keep the `/api/graph/search` endpoint for future use?
4. **Suggestions Endpoint**: Is `/api/suggestions/` used or planned?

---

## ✨ Benefits of Cleanup

1. **Maintainability**: Smaller, focused files following single-responsibility
2. **Testability**: Easier to test individual routers and utilities
3. **Clarity**: Clear separation of concerns (config, routes, models, utils)
4. **Performance**: Less code loaded, faster startup
5. **Best Practices**: Follows FastAPI recommended structure
6. **Documentation**: Self-documenting file structure
