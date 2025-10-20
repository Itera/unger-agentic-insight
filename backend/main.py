"""
Backend API for Agentic Insight Application
Integrates OpenAI agents with Azure ADX MCP for industrial data insights
"""

import os
import json
import pandas as pd
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import httpx
from openai import OpenAI
from dotenv import load_dotenv
import io
from datetime import datetime
from services.graph_service import graph_service
from services.data_mapping_service import initialize_data_mapping_service
from services.maintenance_service import MaintenanceAPIService
from datetime import datetime
import json

load_dotenv()

app = FastAPI(title="Agentic Insight API", version="1.0.0")

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/insight_db")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADX_MCP_URL = os.getenv("ADX_MCP_URL", "http://localhost:8001")

# Neo4j Configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# Initialize database
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Initialize OpenAI client
openai_client = None
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    print("OpenAI client initialized successfully")
else:
    print("OpenAI API key not provided")

# Initialize Graph service
graph_connected = graph_service.connect()
if graph_connected:
    print("Neo4j graph service initialized successfully")
else:
    print("Neo4j graph service connection failed - continuing without graph features")

# Initialize Data Mapping service
data_mapping_service = initialize_data_mapping_service(DATABASE_URL)
print("Data mapping service initialized successfully")

# Initialize Maintenance service
try:
    maintenance_service = MaintenanceAPIService()
    print("Maintenance API service initialized successfully")
except ValueError as e:
    maintenance_service = None
    print(f"Maintenance API service not initialized: {e}")


# Helper function to map UI entity types to Neo4j labels
def map_entity_type_to_neo4j_label(entity_type: str) -> str:
    """Map frontend entity types to actual Neo4j node labels"""
    type_mapping = {
        "Area Sensors": "Sensor",
        "Equipment Sensors": "Sensor", 
        "Equipment": "Equipment",
        "Sensor": "Sensor",
        "AssetArea": "AssetArea",
        "Tank": "Tank",
        "ProcessStep": "ProcessStep"
    }
    return type_mapping.get(entity_type, entity_type)


# Helper function to serialize Neo4j data
def serialize_neo4j_data(data):
    """Convert Neo4j data types to JSON-serializable formats"""
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            result[key] = serialize_neo4j_data(value)
        return result
    elif isinstance(data, list):
        return [serialize_neo4j_data(item) for item in data]
    elif hasattr(data, '_DateTime__date') and hasattr(data, '_DateTime__time'):
        # Handle Neo4j DateTime objects
        try:
            # Convert to ISO format string
            date_part = data._DateTime__date
            time_part = data._DateTime__time
            # Create a simple datetime string
            return f"{date_part._Date__year:04d}-{date_part._Date__month:02d}-{date_part._Date__day:02d}T{time_part._Time__hour:02d}:{time_part._Time__minute:02d}:{time_part._Time__second:02d}Z"
        except:
            return str(data)
    elif hasattr(data, '__dict__'):
        # Handle other Neo4j objects
        return str(data)
    else:
        return data


# Pydantic models
class QueryRequest(BaseModel):
    query: str
    use_adx: bool = True


class ContextualQueryRequest(BaseModel):
    query: str
    use_adx: bool = True
    context: Optional[Dict[str, Any]] = None  # Navigation context for scoped queries


class QueryResponse(BaseModel):
    query: str
    response: str
    data: Optional[List[Dict[str, Any]]] = None
    source: str
    timestamp: datetime
    context_used: Optional[Dict[str, Any]] = None  # Context data that was actually used


class CSVImportResponse(BaseModel):
    filename: str
    rows_imported: int
    table: str
    status: str


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "openai_available": openai_client is not None,
        "database_connected": True,
        "graph_connected": graph_service.is_connected(),
        "adx_mcp_url": ADX_MCP_URL,
        "neo4j_uri": NEO4J_URI
    }


@app.post("/import-csv", response_model=CSVImportResponse)
async def import_csv(file: UploadFile = File(...)):
    """Import CSV data into the database"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    try:
        # Read CSV content
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        # Determine table based on filename or content structure
        table_name = determine_table_name(file.filename, df.columns.tolist())
        
        # Import data based on table type
        if table_name == "hmi_sensor_data":
            rows_imported = import_hmi_data(df)
        elif table_name == "tag_configuration":
            rows_imported = import_tag_config(df)
        elif table_name == "itera_measurements":
            rows_imported = import_itera_data(df)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown data format in file: {file.filename}")
        
        # Update import tracking
        with SessionLocal() as db:
            db.execute(
                text("UPDATE csv_imports SET rows_imported = :rows WHERE filename = :filename"),
                {"rows": rows_imported, "filename": file.filename}
            )
            db.commit()
        
        return CSVImportResponse(
            filename=file.filename,
            rows_imported=rows_imported,
            table=table_name,
            status="success"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


def determine_table_name(filename: str, columns: List[str]) -> str:
    """Determine which table to import data into based on filename and columns"""
    if "sample_data" in filename.lower():
        return "hmi_sensor_data"
    elif "tagconfig" in filename.lower() or "itera" in filename.lower() and "RecordId" in columns:
        return "tag_configuration"
    elif "itera" in filename.lower() and "Time" in columns:
        return "itera_measurements"
    elif set(["Time", "Name", "Value"]).issubset(set(columns)):
        return "hmi_sensor_data"
    elif "RecordId" in columns and "Name" in columns:
        return "tag_configuration"
    else:
        return "itera_measurements"


def import_hmi_data(df: pd.DataFrame) -> int:
    """Import HMI sensor data"""
    with SessionLocal() as db:
        rows_imported = 0
        for _, row in df.iterrows():
            try:
                # Parse timestamp - handle different formats
                timestamp_str = str(row.get('Time', ''))
                if timestamp_str and timestamp_str != 'nan':
                    # Handle the specific format in sample_data.csv
                    timestamp = pd.to_datetime(timestamp_str.replace(',', '.'), format='%d.%m.%Y %H.%M.%S.%f')
                    
                    db.execute(
                        text("""
                            INSERT INTO hmi_sensor_data (timestamp, name, value, unit, quality)
                            VALUES (:timestamp, :name, :value, :unit, :quality)
                        """),
                        {
                            "timestamp": timestamp,
                            "name": str(row.get('Name', '')),
                            "value": float(str(row.get('Value', '0')).replace(',', '.')) if row.get('Value') else None,
                            "unit": str(row.get('Unit', '')) if pd.notna(row.get('Unit')) else None,
                            "quality": str(row.get('Quality', ''))
                        }
                    )
                    rows_imported += 1
            except Exception as e:
                print(f"Error importing row: {e}")
                continue
        
        db.commit()
        return rows_imported


def import_tag_config(df: pd.DataFrame) -> int:
    """Import tag configuration data"""
    with SessionLocal() as db:
        rows_imported = 0
        for _, row in df.iterrows():
            try:
                db.execute(
                    text("""
                        INSERT INTO tag_configuration 
                        (record_id, name, phd_entity_type, tag_no, active, description, 
                         parent_tag, class_tag, tag_units, tolerance, tolerance_type, 
                         collection, scan_frequency, high_extreme, low_extreme, asset, 
                         item, function_name, source_system, source_tag_type, source_name)
                        VALUES (:record_id, :name, :phd_entity_type, :tag_no, :active, :description,
                                :parent_tag, :class_tag, :tag_units, :tolerance, :tolerance_type,
                                :collection, :scan_frequency, :high_extreme, :low_extreme, :asset,
                                :item, :function_name, :source_system, :source_tag_type, :source_name)
                    """),
                    {
                        "record_id": int(row.get('RecordId', 0)) if pd.notna(row.get('RecordId')) else None,
                        "name": str(row.get('Name', '')),
                        "phd_entity_type": str(row.get('PhdEntityType', '')) if pd.notna(row.get('PhdEntityType')) else None,
                        "tag_no": int(row.get('TagNo', 0)) if pd.notna(row.get('TagNo')) else None,
                        "active": str(row.get('Active', '')).upper() == 'TRUE',
                        "description": str(row.get('Description', '')) if pd.notna(row.get('Description')) else None,
                        "parent_tag": str(row.get('ParentTag', '')) if pd.notna(row.get('ParentTag')) else None,
                        "class_tag": str(row.get('ClassTag', '')).upper() == 'TRUE',
                        "tag_units": str(row.get('TagUnits', '')) if pd.notna(row.get('TagUnits')) else None,
                        "tolerance": float(row.get('Tolerance', 0)) if pd.notna(row.get('Tolerance')) else None,
                        "tolerance_type": str(row.get('ToleranceType', '')) if pd.notna(row.get('ToleranceType')) else None,
                        "collection": str(row.get('Collection', '')).upper() == 'TRUE',
                        "scan_frequency": int(row.get('ScanFrequency', 0)) if pd.notna(row.get('ScanFrequency')) else None,
                        "high_extreme": float(row.get('HighExtreme', 0)) if pd.notna(row.get('HighExtreme')) else None,
                        "low_extreme": float(row.get('LowExtreme', 0)) if pd.notna(row.get('LowExtreme')) else None,
                        "asset": str(row.get('Asset', '')) if pd.notna(row.get('Asset')) else None,
                        "item": str(row.get('Item', '')) if pd.notna(row.get('Item')) else None,
                        "function_name": str(row.get('Function', '')) if pd.notna(row.get('Function')) else None,
                        "source_system": str(row.get('SourceSystem', '')) if pd.notna(row.get('SourceSystem')) else None,
                        "source_tag_type": str(row.get('SourceTagType', '')) if pd.notna(row.get('SourceTagType')) else None,
                        "source_name": str(row.get('SourceName', '')) if pd.notna(row.get('SourceName')) else None,
                    }
                )
                rows_imported += 1
            except Exception as e:
                print(f"Error importing tag config row: {e}")
                continue
        
        db.commit()
        return rows_imported


def import_itera_data(df: pd.DataFrame) -> int:
    """Import Itera measurement data"""
    with SessionLocal() as db:
        rows_imported = 0
        for _, row in df.iterrows():
            try:
                # Parse timestamp
                timestamp_str = str(row.get('Time String', ''))
                if timestamp_str and timestamp_str != 'nan':
                    timestamp = pd.to_datetime(timestamp_str.strip().replace('\t', ''), format='%d.%m.%Y %H:%M:%S')
                    
                    db.execute(
                        text("""
                            INSERT INTO itera_measurements 
                            (timestamp, time_string, li_329_value, li_331_value, li_440_value, 
                             li_038_value, li_001_value, li_002_value, li_003_value, li_327_value,
                             li_329_daca_value, li_331_daca_value, li_351_value, li_353_value)
                            VALUES (:timestamp, :time_string, :li_329, :li_331, :li_440,
                                    :li_038, :li_001, :li_002, :li_003, :li_327,
                                    :li_329_daca, :li_331_daca, :li_351, :li_353)
                        """),
                        {
                            "timestamp": timestamp,
                            "time_string": timestamp_str,
                            "li_329": float(row.get('740-38-LI-329.DACA.PV', 0)) if pd.notna(row.get('740-38-LI-329.DACA.PV')) else None,
                            "li_331": float(row.get('740-38-LI-331.DACA.PV', 0)) if pd.notna(row.get('740-38-LI-331.DACA.PV')) else None,
                            "li_440": float(row.get('740-40-LI-440.DACA.PV', 0)) if pd.notna(row.get('740-40-LI-440.DACA.PV')) else None,
                            "li_038": float(row.get('792-37-LI-038.DACA.PV', 0)) if pd.notna(row.get('792-37-LI-038.DACA.PV')) else None,
                            "li_001": float(row.get('740-38-LI-001.DACA.PV', 0)) if pd.notna(row.get('740-38-LI-001.DACA.PV')) else None,
                            "li_002": float(row.get('740-38-LI-002.DACA.PV', 0)) if pd.notna(row.get('740-38-LI-002.DACA.PV')) else None,
                            "li_003": float(row.get('740-38-LI-003.DACA.PV', 0)) if pd.notna(row.get('740-38-LI-003.DACA.PV')) else None,
                            "li_327": float(row.get('740-38-LI-327.DACA.PV', 0)) if pd.notna(row.get('740-38-LI-327.DACA.PV')) else None,
                            "li_329_daca": float(row.get('740-38-LI-329.DACA.PV', 0)) if pd.notna(row.get('740-38-LI-329.DACA.PV')) else None,
                            "li_331_daca": float(row.get('740-38-LI-331.DACA.PV', 0)) if pd.notna(row.get('740-38-LI-331.DACA.PV')) else None,
                            "li_351": float(row.get('740-38-LI-351.DACA.PV', 0)) if pd.notna(row.get('740-38-LI-351.DACA.PV')) else None,
                            "li_353": float(row.get('740-38-LI-353.DACA.PV', 0)) if pd.notna(row.get('740-38-LI-353.DACA.PV')) else None,
                        }
                    )
                    rows_imported += 1
            except Exception as e:
                print(f"Error importing itera row: {e}")
                continue
        
        db.commit()
        return rows_imported


@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process natural language queries using OpenAI agent and ADX MCP"""
    if not openai_client:
        raise HTTPException(status_code=503, detail="OpenAI client not available")
    
    try:
        # Get schema information from ADX MCP or local database
        schema_info = await get_schema_info(request.use_adx)
        
        # Create system prompt for the OpenAI agent
        system_prompt = create_system_prompt(schema_info, request.use_adx)
        
        # Query OpenAI agent
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.query}
            ],
            temperature=0.1
        )
        
        agent_response = response.choices[0].message.content
        
        # Try to extract and execute any SQL/KQL query from the response
        data = None
        if request.use_adx:
            data = await execute_adx_query_from_response(agent_response)
        else:
            data = await execute_sql_query_from_response(agent_response)
        
        return QueryResponse(
            query=request.query,
            response=agent_response,
            data=data,
            source="adx" if request.use_adx else "local",
            timestamp=datetime.now()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


@app.post("/query/contextual", response_model=QueryResponse)
async def process_contextual_query(request: ContextualQueryRequest):
    """Process contextual natural language queries with graph navigation scope"""
    if not openai_client:
        raise HTTPException(status_code=503, detail="OpenAI client not available")
    
    try:
        # Get schema information from ADX MCP or local database
        schema_info = await get_schema_info(request.use_adx)
        
        # Get contextual graph data if context is provided
        context_data = None
        if request.context and request.context.get('nodeType') and request.context.get('nodeName'):
            context_data = await get_contextual_graph_data(request.context)
        
        # Create contextual system prompt
        system_prompt = create_contextual_system_prompt(schema_info, context_data, request.use_adx)
        
        # Query OpenAI agent with context
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.query}
            ],
            temperature=0.1
        )
        
        agent_response = response.choices[0].message.content
        
        # Try to extract and execute any SQL/KQL query from the response
        data = None
        if request.use_adx:
            data = await execute_adx_query_from_response(agent_response)
        else:
            data = await execute_sql_query_from_response(agent_response)
        
        return QueryResponse(
            query=request.query,
            response=agent_response,
            data=data,
            source=f"{'adx' if request.use_adx else 'local'}-contextual",
            timestamp=datetime.now(),
            context_used=serialize_neo4j_data(context_data) if context_data else None  # Serialize context data
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Contextual query processing failed: {str(e)}")


async def get_schema_info(use_adx: bool) -> Dict[str, Any]:
    """Get schema information from ADX MCP or local database"""
    if use_adx:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{ADX_MCP_URL}/mcp",
                    json={"method": "tools/call", "params": {"name": "get_schema", "arguments": {}}}
                )
                if response.status_code == 200:
                    return response.json().get("result", {})
        except Exception as e:
            print(f"Failed to get ADX schema: {e}")
    
    # Fallback to local database schema
    with SessionLocal() as db:
        tables = db.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")).fetchall()
        schema = {"tables": [t[0] for t in tables], "columns": {}}
        
        for table in schema["tables"]:
            cols = db.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'")).fetchall()
            schema["columns"][table] = [c[0] for c in cols]
    
    return schema


def create_system_prompt(schema_info: Dict[str, Any], use_adx: bool) -> str:
    """Create system prompt for OpenAI agent"""
    query_language = "KQL (Kusto Query Language)" if use_adx else "SQL"
    
    prompt = f"""You are an expert industrial data analyst with access to sensor and configuration data.

Available tables and columns:
{json.dumps(schema_info, indent=2)}

You can answer questions about:
- HMI sensor data (timestamps, values, units, quality)
- Tag configurations (descriptions, scan frequencies, limits)
- Itera measurements (various LI sensor readings)

When answering queries:
1. Provide clear, insightful analysis of the industrial data
2. If a {query_language} query would be helpful, include it in your response between ```{query_language.lower()} and ``` tags
3. Explain what the data shows in business/operational terms
4. Highlight any anomalies, trends, or important insights
5. Use appropriate industrial terminology

Focus on providing actionable insights for plant operations and maintenance."""
    
    return prompt


def create_contextual_system_prompt(schema_info: Dict[str, Any], context_data: Optional[Dict[str, Any]], use_adx: bool) -> str:
    """Create contextual system prompt for scoped OpenAI agent responses"""
    query_language = "KQL (Kusto Query Language)" if use_adx else "SQL"
    
    base_prompt = f"""You are an expert industrial data analyst with access to sensor and configuration data.

Available tables and columns:
{json.dumps(schema_info, indent=2)}
"""

    # Add contextual information if available
    if context_data:
        context_prompt = f"""
🔍 CURRENT NAVIGATION CONTEXT:
You are currently focused on: {context_data.get('context_scope', 'Unknown')}
Central Node: {context_data.get('central_node', {}).get('name', 'Unknown')} ({context_data.get('central_node', {}).get('labels', [])})
"""
        
        # Add connected nodes information with relationships
        if context_data.get('connected_nodes'):
            context_prompt += f"\nConnected Entities ({len(context_data['connected_nodes'])} found):\n"
            
            # Group by relationship types and entity types with rich properties
            entity_relationships = {}
            detailed_entities = []
            
            for node in context_data['connected_nodes'][:15]:  # Show more entities for better context
                # Safely handle labels
                labels = node.get('labels', [])
                if labels and all(label is not None for label in labels):
                    node_labels = ', '.join(str(label) for label in labels)
                else:
                    node_labels = 'Unknown'
                
                # Enhanced node identification with proper names
                node_name = str(node.get('name') or 
                               node.get('properties', {}).get('equipment_name') or 
                               node.get('properties', {}).get('tag') or 
                               'Unknown')
                
                relationship_path = node.get('relationship_path', [])
                depth = node.get('depth', 'unknown')
                properties = node.get('properties', {})
                
                # Determine relationship context safely
                if relationship_path and all(r is not None for r in relationship_path):
                    rel_context = f"via {' → '.join(str(r) for r in relationship_path)}"
                else:
                    rel_context = f"at depth {str(depth)}"
                
                # Enhanced entity description with rich properties
                entity_desc = f"- {node_name} ({node_labels})"
                
                # Add sensor-specific properties
                if 'Sensor' in node_labels:
                    sensor_details = []
                    if properties.get('unit'):
                        sensor_details.append(f"Unit: {properties['unit']}")
                    if properties.get('sensor_type_code'):
                        sensor_details.append(f"Type: {properties['sensor_type_code']}")
                    if properties.get('classification'):
                        sensor_details.append(f"Class: {properties['classification']}")
                    if sensor_details:
                        entity_desc += f" [{', '.join(sensor_details)}]"
                
                # Add equipment-specific properties
                elif 'Equipment' in node_labels:
                    equip_details = []
                    if properties.get('equipment_type'):
                        equip_details.append(f"Type: {properties['equipment_type']}")
                    if properties.get('sensor_count'):
                        equip_details.append(f"Sensors: {properties['sensor_count']}")
                    if equip_details:
                        entity_desc += f" [{', '.join(equip_details)}]"
                    
                    # Add source tags if available
                    if properties.get('source_tags'):
                        source_tags = properties['source_tags'].split(',')[:3]  # Show first 3 tags
                        entity_desc += f" [Tags: {', '.join([tag.strip() for tag in source_tags])}]"
                
                entity_desc += f" - {rel_context}"
                detailed_entities.append(entity_desc)
                
                # Track relationship patterns for summary
                primary_type = node_labels.split(',')[0].strip() if node_labels and node_labels != 'Unknown' else 'Unknown'
                if primary_type not in entity_relationships:
                    entity_relationships[primary_type] = []
                entity_relationships[primary_type].append({
                    'name': node_name,
                    'properties': properties,
                    'type': primary_type
                })
            
            # Display detailed entities
            for entity_desc in detailed_entities:
                context_prompt += entity_desc + "\n"
            
            if len(context_data['connected_nodes']) > 15:
                context_prompt += f"... and {len(context_data['connected_nodes']) - 15} more entities\n"
            
            # Add enhanced relationship summary with property insights
            context_prompt += "\n📊 RELATIONSHIP SUMMARY:\n"
            for entity_type, entities in entity_relationships.items():
                entity_names = [e['name'] for e in entities]
                context_prompt += f"- {len(entities)} {entity_type}(s): {', '.join(entity_names[:3])}"
                if len(entities) > 3:
                    context_prompt += f" and {len(entities) - 3} more"
                
                # Add property summary for each type
                if entity_type == 'Sensor':
                    units = [e['properties'].get('unit') for e in entities if e['properties'].get('unit')]
                    if units:
                        unique_units = list(set(units))
                        context_prompt += f" [Units: {', '.join(unique_units)}]"
                elif entity_type == 'Equipment':
                    types = [e['properties'].get('equipment_type') for e in entities if e['properties'].get('equipment_type')]
                    if types:
                        unique_types = list(set(types))
                        context_prompt += f" [Types: {', '.join(unique_types)}]"
                    
                    total_sensor_count = sum([int(e['properties'].get('sensor_count', 0)) for e in entities if e['properties'].get('sensor_count')])
                    if total_sensor_count > 0:
                        context_prompt += f" [Total Connected Sensors: {total_sensor_count}]"
                
                context_prompt += "\n"
        
        context_prompt += f"\nTotal entities in scope: {context_data.get('total_nodes', 0)}\n"
        context_prompt += "\n⚠️  IMPORTANT: Your responses should be FOCUSED on this specific context. When the user asks about 'sensors', 'equipment', or 'data', prioritize information related to the entities listed above.\n"
        
        base_prompt += context_prompt
    
    base_prompt += f"""

📊 **AVAILABLE DATA SOURCES**:
- HMI sensor data (timestamps, values, quality) - Historical data available
- Tag configurations (descriptions, scan frequencies, limits) - Configuration data
- Itera measurements (various LI sensor readings) - Batch measurement data
- Graph relationships (plants, areas, equipment, sensors) - Real-time topology
- Sensor metadata (units like °C/%, sensor types like TI/LI, classifications)
- Equipment details (types like tank/pump, sensor counts, source tag traceability)

⚠️ **DATA LIMITATIONS** (US-019 - Be transparent about unavailable data):
- ❌ **Real-time sensor values**: Historical data only, not live streaming
- ❌ **Maintenance schedules**: Would require CMMS integration (not connected)
- ❌ **Work orders & alerts**: Would require maintenance system integration
- ❌ **Live alarms & diagnostics**: Would require SCADA/DCS integration
- ❌ **Performance KPIs**: Would require calculation from live data streams

🎯 **ENHANCED RESPONSE GUIDELINES** (US-017):

1. **USE RICH GRAPH PROPERTIES**: Always include specific details when available
   - Sensor responses: "Temperature sensor (Unit: °C, Type: TI, Class: PROCESS)"
   - Equipment responses: "Cooling tank (Type: tank, 3 connected sensors: TI-006, LIC-008, etc.)"
   - Include source tags for traceability: "Equipment monitored by tags: 7520LIC008.PIDA.OP, 7520LIC008.PIDA.SP"

2. **EXPLAIN RELATIONSHIPS WITH CONTEXT**: Use the specific connected entities
   - "This pump connects to 2 temperature sensors (°C) and 1 pressure sensor (%)"
   - "In this area, you have 3 tanks with 8 total sensors across temperature and level monitoring"

3. **PROVIDE INTELLIGENT SUGGESTIONS** (Foundation for US-018):
   - "You might also want to check the connected temperature sensors for this equipment"
   - "Related equipment in this area includes [list specific connected equipment]"
   - "Based on this equipment type (tank), you typically want to monitor level and temperature sensors"

4. **BE TRANSPARENT ABOUT LIMITATIONS** (US-019):
   - "I can see this equipment has 3 sensors, but live readings would need real-time integration"
   - "Maintenance schedules aren't available - this would come from your CMMS system"
   - "Historical data shows patterns, but current status requires live SCADA connection"

5. **LEVERAGE CONTEXTUAL SCOPE**: Focus on current navigation context
   - Reference specific entities from the relationship summary above
   - Use actual sensor units, equipment types, and counts from the context
   - Connect answers to the specific plant hierarchy location

6. **TECHNICAL ACCURACY**: 
   - If a {query_language} query would help, include it in ```{query_language.lower()} tags
   - Use proper industrial terminology based on sensor types and equipment types
   - Reference actual tag names and sensor classifications when relevant

🌟 **GOLDEN RULES** (Enhanced):
- **RICH CONTEXT**: Use specific sensor units, equipment types, and connection details
- **HONEST LIMITATIONS**: Clearly state when data isn't available vs. when integration is needed  
- **PRACTICAL FOCUS**: Connect insights to operational impact using actual connected equipment
- **INTELLIGENT SUGGESTIONS**: Recommend exploration of related entities from the graph

Provide actionable insights for plant operations within the current scope, using all available rich metadata."""
    
    return base_prompt


async def get_contextual_graph_data(context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get contextual graph data for the current navigation scope"""
    if not graph_service.is_connected():
        return None
    
    try:
        node_type = context.get('nodeType')
        node_name = context.get('nodeName') 
        scope_depth = context.get('scopeDepth', 2)
        
        if not node_type or not node_name:
            return None
        
        # Get contextual subgraph using existing graph service method
        context_data = graph_service.get_contextual_subgraph(node_name, node_type, scope_depth)
        
        return context_data
        
    except Exception as e:
        print(f"Error getting contextual graph data: {e}")
        return None


async def execute_adx_query_from_response(response: str) -> Optional[List[Dict[str, Any]]]:
    """Extract and execute KQL query from agent response"""
    try:
        # Look for KQL query in response
        import re
        kql_match = re.search(r'```kql\n(.*?)\n```', response, re.DOTALL)
        if not kql_match:
            kql_match = re.search(r'```\n(.*?)\n```', response, re.DOTALL)
        
        if kql_match:
            query = kql_match.group(1).strip()
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{ADX_MCP_URL}/mcp",
                    json={
                        "method": "tools/call",
                        "params": {"name": "execute_kql", "arguments": {"query": query}}
                    }
                )
                
                if response.status_code == 200:
                    result = response.json().get("result", {})
                    return result.get("results", [])
    
    except Exception as e:
        print(f"Failed to execute ADX query: {e}")
    
    return None


async def execute_sql_query_from_response(response: str) -> Optional[List[Dict[str, Any]]]:
    """Extract and execute SQL query from agent response"""
    try:
        # Look for SQL query in response
        import re
        sql_match = re.search(r'```sql\n(.*?)\n```', response, re.DOTALL)
        if not sql_match:
            sql_match = re.search(r'```\n(.*?)\n```', response, re.DOTALL)
        
        if sql_match:
            query = sql_match.group(1).strip()
            
            with SessionLocal() as db:
                result = db.execute(text(query)).fetchall()
                # Convert to list of dictionaries
                if result:
                    columns = result[0].keys()
                    return [dict(zip(columns, row)) for row in result]
    
    except Exception as e:
        print(f"Failed to execute SQL query: {e}")
    
    return None


@app.get("/tables")
async def list_tables():
    """List all available tables"""
    with SessionLocal() as db:
        tables = db.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")).fetchall()
        return {"tables": [t[0] for t in tables]}


@app.get("/import-status")
async def import_status():
    """Get CSV import status"""
    with SessionLocal() as db:
        imports = db.execute(text("SELECT * FROM csv_imports ORDER BY imported_at DESC")).fetchall()
        return {"imports": [dict(imp._mapping) for imp in imports]}


# Graph API Endpoints
@app.get("/api/graph/plants")
async def get_plants():
    """Get all plants in the graph"""
    try:
        if graph_service.is_connected():
            plants = graph_service.get_all_plants()
            if plants:
                return {"plants": serialize_neo4j_data(plants)}
    except Exception as e:
        print(f"Error getting plants from graph: {e}")
    
    # Fallback to mock data
    mock_plants = [
        {
            "id": "plant_001",
            "name": "Unger Plant", 
            "description": "Main industrial processing plant",
            "location": "Industrial Complex A",
            "status": "Active"
        },
        {
            "id": "plant_002", 
            "name": "Processing Unit B",
            "description": "Secondary processing facility",
            "location": "Industrial Complex B", 
            "status": "Active"
        }
    ]
    return {"plants": mock_plants}


@app.get("/api/graph/plants/{plant_name}/areas")
async def get_asset_areas_by_plant(plant_name: str):
    """Get all asset areas for a specific plant"""
    try:
        if graph_service.is_connected():
            areas = graph_service.get_asset_areas_by_plant(plant_name)
            if areas:
                return {"plant": plant_name, "asset_areas": serialize_neo4j_data(areas)}
    except Exception as e:
        print(f"Error getting areas from graph: {e}")
    
    # Fallback to mock data
    mock_areas = [
        {
            "id": "area_001",
            "name": "Production Area A", 
            "description": "Main production line area",
            "status": "Active"
        },
        {
            "id": "area_002",
            "name": "Mixing Station",
            "description": "Chemical mixing and preparation area", 
            "status": "Active"
        },
        {
            "id": "area_003",
            "name": "Quality Control",
            "description": "Testing and quality assurance area",
            "status": "Active"
        },
        {
            "id": "area_004", 
            "name": "Storage Facility",
            "description": "Raw materials and finished goods storage",
            "status": "Active"
        }
    ]
    return {"plant": plant_name, "asset_areas": mock_areas}


@app.get("/api/graph/areas/{area_name}/equipment")
async def get_equipment_by_area(area_name: str):
    """Get all equipment for a specific asset area"""
    if not graph_service.is_connected():
        raise HTTPException(status_code=503, detail="Graph service not available")
    
    try:
        equipment = graph_service.get_equipment_by_asset_area(area_name)
        return {"area": area_name, "equipment": equipment}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get equipment: {str(e)}")


@app.get("/api/graph/areas/{area_name}/sensors")
async def get_sensors_by_area(area_name: str):
    """Get all sensors for a specific asset area"""
    if not graph_service.is_connected():
        raise HTTPException(status_code=503, detail="Graph service not available")
    
    try:
        sensors = graph_service.get_sensors_by_asset_area(area_name)
        return {"area": area_name, "sensors": sensors}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sensors: {str(e)}")


@app.get("/api/graph/areas/{area_name}/sensors/categorized")
async def get_categorized_sensors_by_area(area_name: str):
    """Get sensors categorized by connection type (equipment-connected vs area-only)"""
    if not graph_service.is_connected():
        raise HTTPException(status_code=503, detail="Graph service not available")
    
    try:
        categorized_sensors = graph_service.get_categorized_sensors_by_area(area_name)
        return {"area": area_name, "categorized_sensors": categorized_sensors}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get categorized sensors: {str(e)}")


@app.get("/api/graph/equipment/{equipment_name}/sensors")
async def get_sensors_by_equipment(equipment_name: str):
    """Get all sensors for a specific equipment"""
    if not graph_service.is_connected():
        raise HTTPException(status_code=503, detail="Graph service not available")
    
    try:
        sensors = graph_service.get_sensors_by_equipment(equipment_name)
        return {"equipment": equipment_name, "sensors": sensors}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sensors: {str(e)}")


@app.get("/api/graph/nodes/{node_type}/{node_name}")
async def get_node_details(node_type: str, node_name: str):
    """Get detailed information about a specific node"""
    if not graph_service.is_connected():
        raise HTTPException(status_code=503, detail="Graph service not available")
    
    try:
        # Get node details and relationships
        node_details = graph_service.get_node_details(node_name)
        if not node_details:
            raise HTTPException(status_code=404, detail=f"Node {node_name} not found")
        
        relationships = graph_service.get_node_relationships(node_name, node_type)
        
        return {
            "node": node_details,
            "relationships": relationships,
            "node_type": node_type
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get node details: {str(e)}")


@app.get("/api/graph/context/{node_type}/{node_name}")
async def get_contextual_subgraph(node_type: str, node_name: str, max_depth: int = 2):
    """Get contextual subgraph for AI chat scoping"""
    if not graph_service.is_connected():
        raise HTTPException(status_code=503, detail="Graph service not available")
    
    try:
        context = graph_service.get_contextual_subgraph(node_name, node_type, max_depth)
        if not context.get("central_node"):
            raise HTTPException(status_code=404, detail=f"Node {node_name} not found")
        
        return serialize_neo4j_data(context)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get contextual subgraph: {str(e)}")


@app.get("/api/suggestions/{node_type}/{node_name}")
async def get_suggestions(node_type: str, node_name: str, max_suggestions: int = 6):
    """Get smart suggestions for related entities based on graph connections (US-018)"""
    if not graph_service.is_connected():
        raise HTTPException(status_code=503, detail="Graph service not available")
    
    try:
        suggestions = graph_service.get_smart_suggestions(node_name, node_type, max_suggestions)
        return {
            "node_name": node_name,
            "node_type": node_type,
            "suggestions": serialize_neo4j_data(suggestions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")


@app.get("/api/graph/search")
async def search_nodes(q: str, node_types: Optional[str] = None):
    """Search nodes by name or description"""
    if not graph_service.is_connected():
        raise HTTPException(status_code=503, detail="Graph service not available")
    
    try:
        types_list = node_types.split(',') if node_types else None
        results = graph_service.search_nodes(q, types_list)
        return {"query": q, "results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


# Data Mapping API Endpoints
@app.get("/api/mapping/area/{area_id}/sensors")
async def get_area_sensor_mapping(area_id: str):
    """Get sensor configurations mapped to an asset area"""
    try:
        sensor_configs = data_mapping_service.get_sensor_configurations_by_area(area_id)
        return {
            "area_id": area_id,
            "sensor_configurations": sensor_configs,
            "count": len(sensor_configs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sensor mapping: {str(e)}")


@app.get("/api/mapping/node/{node_type}/{node_name}")
async def get_node_sensor_mapping(node_type: str, node_name: str):
    """Get sensor data mapping for a specific graph node"""
    try:
        mapping = data_mapping_service.map_graph_node_to_sensor_data(node_name, node_type)
        return mapping
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get node mapping: {str(e)}")


@app.get("/api/mapping/enriched/{node_type}/{node_name}")
async def get_enriched_node_context(node_type: str, node_name: str):
    """Get enriched context combining graph relationships and sensor data"""
    if not graph_service.is_connected():
        raise HTTPException(status_code=503, detail="Graph service not available")
    
    try:
        enriched_context = data_mapping_service.get_enriched_context_for_node(node_name, node_type)
        return enriched_context
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get enriched context: {str(e)}")


@app.get("/api/mapping/search/sensors")
async def search_sensors(area_id: Optional[str] = None, sensor_type: Optional[str] = None, unit: Optional[str] = None):
    """Search sensors by various criteria"""
    try:
        results = data_mapping_service.search_sensors_by_criteria(area_id, sensor_type, unit)
        return {
            "criteria": {
                "area_id": area_id,
                "sensor_type": sensor_type,
                "unit": unit
            },
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sensor search failed: {str(e)}")


@app.get("/api/mapping/area/{area_id}/quality")
async def get_area_data_quality(area_id: str):
    """Get data quality summary for an asset area"""
    try:
        quality_summary = data_mapping_service.get_data_quality_summary(area_id)
        return quality_summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get node details: {str(e)}")


@app.get("/api/areas/{area_name}")
async def get_area_details(area_name: str):
    """Get detailed information about a specific area"""
    try:
        if graph_service.is_connected():
            # Try to get real area data from Neo4j
            query = """
            MATCH (a:AssetArea {name: $area_name})
            RETURN a.id as id, a.name as name, a.description as description,
                   labels(a) as labels, properties(a) as properties
            """
            results = graph_service.execute_query(query, {"area_name": area_name})
            
            if results:
                area_data = results[0]
                # Format the response to match expected structure
                serialized_response = {
                    "id": area_data.get("id"),
                    "name": area_data.get("name"),
                    "description": area_data.get("description"),
                    "type": "AssetArea",
                    "labels": area_data.get("labels", []),
                    "properties": area_data.get("properties", {})
                }
                return serialize_neo4j_data(serialized_response)
                
    except Exception as e:
        print(f"Error getting area details from graph for {area_name}: {e}")
    
    # Fallback to mock data
    area_data = {
        "id": f"area_{area_name.lower().replace(' ', '_')}",
        "name": area_name,
        "description": f"Industrial processing area containing various equipment and monitoring systems for {area_name} operations.",
        "type": "Area",
        "properties": {
            "location": "Plant Floor 2",
            "status": "Active", 
            "lastMaintenance": "2024-01-15"
        }
    }
    return area_data


@app.get("/api/areas/{area_name}/entities")
async def get_area_entities(area_name: str):
    """Get all connected entities for a specific area"""
    entities = {}
    
    try:
        if graph_service.is_connected():
            # Get real data from Neo4j graph
            equipment = graph_service.get_equipment_by_asset_area(area_name)
            sensors = graph_service.get_sensors_by_asset_area(area_name)
            
            # Get other connected entities (ProcessStep, Tank, etc.)
            all_connected_query = """
            MATCH (a:AssetArea {name: $area_name})-[*1..3]->(n)
            WHERE NOT n:Equipment AND NOT n:Sensor AND NOT n:AssetArea
            RETURN DISTINCT n.id as id, n.name as name, n.description as description,
                   labels(n) as labels, properties(n) as properties
            ORDER BY labels(n), n.name
            """
            other_entities = graph_service.execute_query(all_connected_query, {"area_name": area_name})
            
            # Format equipment data
            if equipment:
                entities["Equipment"] = equipment
            
            # Format sensor data  
            if sensors:
                entities["Sensor"] = sensors
            
            # Group other entities by their labels
            entity_groups = {}
            for entity in other_entities:
                # Get primary label (skip generic ones like 'Node')
                primary_label = None
                for label in entity.get('labels', []):
                    if label not in ['Node']:  # Skip generic labels
                        primary_label = label
                        break
                
                if primary_label:
                    if primary_label not in entity_groups:
                        entity_groups[primary_label] = []
                    entity_groups[primary_label].append(entity)
            
            # Add other entity groups to response
            entities.update(entity_groups)
            
            # If we got real data, return it
            if entities:
                return serialize_neo4j_data(entities)
                
    except Exception as e:
        print(f"Error getting entities from graph for area {area_name}: {e}")
    
    # Fallback to mock data
    mock_entities = {
        "Equipment": [
            {
                "id": "eq_001",
                "name": f"{area_name} Primary Pump",
                "description": "Main circulation pump for processing operations",
                "properties": {"status": "Running", "power": "85%"}
            },
            {
                "id": "eq_002", 
                "name": f"{area_name} Heat Exchanger",
                "description": "Primary heat exchange unit",
                "properties": {"status": "Active", "efficiency": "92%"}
            }
        ],
        "Sensor": [
            {
                "id": "sens_001",
                "name": f"{area_name} Temperature Sensor",
                "description": "Monitors process temperature",
                "properties": {"value": "85.2°C", "status": "Normal"}
            },
            {
                "id": "sens_002",
                "name": f"{area_name} Pressure Sensor", 
                "description": "Monitors system pressure",
                "properties": {"value": "2.4 bar", "status": "Normal"}
            },
            {
                "id": "sens_003",
                "name": f"{area_name} Flow Sensor",
                "description": "Measures fluid flow rate",
                "properties": {"value": "150 L/min", "status": "Normal"}
            }
        ],
        "ProcessStep": [
            {
                "id": "ps_001",
                "name": f"{area_name} Mixing Process",
                "description": "Primary mixing operation",
                "properties": {"status": "Running", "progress": "65%"}
            }
        ]
    }
    return mock_entities


@app.get("/api/entities/{entity_type}/{entity_id}")
async def get_entity_details(entity_type: str, entity_id: str):
    """Get detailed information about a specific entity"""
    try:
        if graph_service.is_connected():
            # Map UI entity types to Neo4j labels
            neo4j_label = map_entity_type_to_neo4j_label(entity_type)
            
            # Try to get real entity data from Neo4j
            # First try by ID, then by name if ID doesn't work
            query = f"""
            MATCH (e:{neo4j_label})
            WHERE e.id = $entity_id OR e.name = $entity_id OR e.equipment_id = $entity_id OR e.tag = $entity_id
            RETURN e.id as id, e.name as name, e.description as description,
                   labels(e) as labels, properties(e) as properties
            LIMIT 1
            """
            results = graph_service.execute_query(query, {"entity_id": entity_id})
            
            if results:
                entity_data = results[0]
                return serialize_neo4j_data({
                    "id": entity_data.get("id"),
                    "name": entity_data.get("name"),
                    "description": entity_data.get("description"),
                    "type": entity_type,
                    "labels": entity_data.get("labels", []),
                    "properties": entity_data.get("properties", {})
                })
                
    except Exception as e:
        print(f"Error getting entity details from graph for {entity_type}/{entity_id}: {e}")
    
    # Fallback to mock data
    mock_entity = {
        "id": entity_id,
        "name": f"Mock {entity_type}",
        "description": f"This is a mock {entity_type.lower()} entity for development",
        "type": entity_type,
        "labels": [entity_type],
        "properties": {
            "status": "Active",
            "mock": "true"
        }
    }
    return mock_entity


@app.get("/api/entities/{entity_type}/{entity_id}/connected")
async def get_entity_connected_entities(entity_type: str, entity_id: str):
    """Get all entities connected to a specific entity"""
    connected_entities = {}
    
    try:
        if graph_service.is_connected():
            # Map UI entity types to Neo4j labels
            neo4j_label = map_entity_type_to_neo4j_label(entity_type)
            
            # Get connected entities from Neo4j
            query = f"""
            MATCH (e:{neo4j_label})-[r]-(connected)
            WHERE e.id = $entity_id OR e.name = $entity_id OR e.equipment_id = $entity_id OR e.tag = $entity_id
            WITH connected, type(r) as rel_type, labels(connected) as connected_labels
            RETURN connected.id as id, connected.name as name, connected.description as description,
                   connected_labels as labels, properties(connected) as properties,
                   rel_type
            ORDER BY connected_labels, connected.name
            """
            results = graph_service.execute_query(query, {"entity_id": entity_id})
            
            # Group entities by their labels
            entity_groups = {}
            for result in results:
                # Get primary label (skip generic ones)
                primary_label = None
                for label in result.get('labels', []):
                    if label not in ['Node']:  # Skip generic labels
                        primary_label = label
                        break
                
                if primary_label:
                    if primary_label not in entity_groups:
                        entity_groups[primary_label] = []
                    
                    entity_groups[primary_label].append({
                        "id": result.get("id"),
                        "name": result.get("name"),
                        "description": result.get("description"),
                        "labels": result.get("labels", []),
                        "properties": result.get("properties", {}),
                        "relationship_type": result.get("rel_type")
                    })
            
            # Return the entity groups (empty if no connections exist)
            return serialize_neo4j_data(entity_groups)
                
    except Exception as e:
        print(f"Error getting connected entities from graph for {entity_type}/{entity_id}: {e}")
    
    # If graph service fails, return empty result instead of mock data
    return {}


# Work Orders API Endpoints
@app.get("/api/sensors/{sensor_name}/work-orders")
async def get_sensor_work_orders(sensor_name: str):
    """Get work orders for a specific sensor"""
    if not maintenance_service:
        raise HTTPException(status_code=503, detail="Maintenance API service not available")
    
    try:
        work_orders = maintenance_service.get_work_orders_by_sensor(sensor_name)
        return {
            "sensor": sensor_name,
            "work_orders": [{
                "id": wo.id,
                "nr": wo.nr,
                "asset_id": wo.asset_id,
                "short_description": wo.short_description,
                "description": wo.description,
                "comment": wo.comment,
                "status": wo.status,
                "from_date": wo.from_date,
                "to_date": wo.to_date,
                "created_at": wo.created_at,
                "finished_date": wo.finished_date,
                "priority": wo.priority,
                "url": wo.url,
                "is_reactive_maintenance": wo.is_reactive_maintenance
            } for wo in work_orders],
            "count": len(work_orders)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get work orders: {str(e)}")


@app.get("/api/areas/{area_name}/work-orders")
async def get_area_work_orders(area_name: str):
    """Get all work orders for sensors within a specific area"""
    if not maintenance_service:
        raise HTTPException(status_code=503, detail="Maintenance API service not available")
    
    if not graph_service.is_connected():
        raise HTTPException(status_code=503, detail="Graph service not available")
    
    try:
        # Get all sensors in the area
        sensors = graph_service.get_sensors_by_asset_area(area_name)
        if not sensors:
            return {
                "area": area_name,
                "work_orders": [],
                "count": 0,
                "message": "No sensors found in area"
            }
        
        # Get sensor names from the graph results
        sensor_names = []
        for sensor in sensors:
            # Try different possible fields for sensor name/tag
            sensor_name = (sensor.get('name') or 
                          sensor.get('tag') or 
                          sensor.get('properties', {}).get('tag') or
                          sensor.get('properties', {}).get('name'))
            if sensor_name:
                sensor_names.append(sensor_name)
        
        if not sensor_names:
            return {
                "area": area_name,
                "work_orders": [],
                "count": 0,
                "message": "No valid sensor names found in area"
            }
        
        # Get work orders for all sensors in the area
        all_work_orders_by_sensor = maintenance_service.get_work_orders_for_sensors(sensor_names)
        
        # Flatten all work orders with sensor information, deduplicating by work order ID
        work_orders_dict = {}  # Use dict to deduplicate by work order ID
        sensor_mapping = {}  # Track which sensors are associated with each work order
        
        for sensor_name, work_orders in all_work_orders_by_sensor.items():
            for wo in work_orders:
                wo_id = wo.id
                if wo_id not in work_orders_dict:
                    work_orders_dict[wo_id] = {
                        "sensor_name": sensor_name,  # Use first sensor found
                        "id": wo.id,
                        "nr": wo.nr,
                        "asset_id": wo.asset_id,
                        "short_description": wo.short_description,
                        "description": wo.description,
                        "comment": wo.comment,
                        "status": wo.status,
                        "from_date": wo.from_date,
                        "to_date": wo.to_date,
                        "created_at": wo.created_at,
                        "finished_date": wo.finished_date,
                        "priority": wo.priority,
                        "url": wo.url,
                        "is_reactive_maintenance": wo.is_reactive_maintenance
                    }
                    sensor_mapping[wo_id] = [sensor_name]
                else:
                    # Add additional sensors to the mapping for this work order
                    if sensor_name not in sensor_mapping[wo_id]:
                        sensor_mapping[wo_id].append(sensor_name)
        
        # Convert dict back to list and add related sensors
        all_work_orders = list(work_orders_dict.values())
        for wo in all_work_orders:
            wo["related_sensors"] = sensor_mapping[wo["id"]]
        
        # Sort by created_at date, handling empty dates
        all_work_orders.sort(key=lambda x: x['created_at'] if x['created_at'] else '', reverse=True)
        
        return {
            "area": area_name,
            "sensors_checked": sensor_names,
            "work_orders": all_work_orders,
            "count": len(all_work_orders)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get area work orders: {str(e)}")


@app.get("/api/equipment/{equipment_name}/work-orders")
async def get_equipment_work_orders(equipment_name: str):
    """Get all work orders for sensors connected to a specific equipment"""
    if not maintenance_service:
        raise HTTPException(status_code=503, detail="Maintenance API service not available")
    
    if not graph_service.is_connected():
        raise HTTPException(status_code=503, detail="Graph service not available")
    
    try:
        # Get all sensors connected to this equipment using the same logic as connected entities
        neo4j_label = map_entity_type_to_neo4j_label('Equipment')
        
        # Get connected entities from Neo4j (same query as in get_entity_connected_entities)
        query = f"""
        MATCH (e:{neo4j_label})-[r]-(connected)
        WHERE e.id = $entity_id OR e.name = $entity_id OR e.equipment_id = $entity_id OR e.tag = $entity_id
        AND 'Sensor' IN labels(connected)
        WITH connected, type(r) as rel_type, labels(connected) as connected_labels
        RETURN connected.id as id, connected.name as name, connected.description as description,
               connected_labels as labels, properties(connected) as properties,
               rel_type
        ORDER BY connected_labels, connected.name
        """
        results = graph_service.execute_query(query, {"entity_id": equipment_name})
        
        sensors = []
        for result in results:
            sensors.append({
                "id": result.get("id"),
                "name": result.get("name"),
                "description": result.get("description"),
                "labels": result.get("labels", []),
                "properties": result.get("properties", {}),
                "relationship_type": result.get("rel_type")
            })
        
        if not sensors:
            return {
                "equipment": equipment_name,
                "work_orders": [],
                "count": 0,
                "message": "No sensors found connected to equipment"
            }
        
        # Get sensor names from the graph results
        sensor_names = []
        for sensor in sensors:
            # Try different possible fields for sensor name/tag
            sensor_name = (sensor.get('name') or 
                          sensor.get('tag') or 
                          sensor.get('properties', {}).get('tag') or
                          sensor.get('properties', {}).get('name'))
            if sensor_name:
                sensor_names.append(sensor_name)
        
        if not sensor_names:
            return {
                "equipment": equipment_name,
                "work_orders": [],
                "count": 0,
                "message": "No valid sensor names found connected to equipment"
            }
        
        # Get work orders for all sensors connected to the equipment
        all_work_orders_by_sensor = maintenance_service.get_work_orders_for_sensors(sensor_names)
        
        # Flatten all work orders with sensor information
        all_work_orders = []
        for sensor_name, work_orders in all_work_orders_by_sensor.items():
            for wo in work_orders:
                all_work_orders.append({
                    "sensor_name": sensor_name,
                    "id": wo.id,
                    "nr": wo.nr,
                    "asset_id": wo.asset_id,
                    "short_description": wo.short_description,
                    "description": wo.description,
                    "comment": wo.comment,
                    "status": wo.status,
                    "from_date": wo.from_date,
                    "to_date": wo.to_date,
                    "created_at": wo.created_at,
                    "finished_date": wo.finished_date,
                    "priority": wo.priority,
                    "url": wo.url,
                    "is_reactive_maintenance": wo.is_reactive_maintenance
                })
        
        # Sort by date (most recent first)
        all_work_orders.sort(key=lambda x: x['created_at'], reverse=True)
        
        return {
            "equipment": equipment_name,
            "sensors_checked": sensor_names,
            "work_orders": all_work_orders,
            "count": len(all_work_orders)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get equipment work orders: {str(e)}")


@app.get("/api/work-orders/test-transform/{sensor_name}")
async def test_sensor_transform(sensor_name: str):
    """Test endpoint to verify sensor name transformation"""
    from services.sensor_utils import transform_sensor_to_asset_name, extract_sensor_base_name
    
    base_name = extract_sensor_base_name(sensor_name)
    asset_name = transform_sensor_to_asset_name(sensor_name)
    
    return {
        "original_sensor": sensor_name,
        "base_name": base_name,
        "transformed_asset": asset_name
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
