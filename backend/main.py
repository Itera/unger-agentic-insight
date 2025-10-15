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


# Pydantic models
class QueryRequest(BaseModel):
    query: str
    use_adx: bool = True


class QueryResponse(BaseModel):
    query: str
    response: str
    data: Optional[List[Dict[str, Any]]] = None
    source: str
    timestamp: datetime


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
            model="gpt-4",
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
    if not graph_service.is_connected():
        raise HTTPException(status_code=503, detail="Graph service not available")
    
    try:
        plants = graph_service.get_all_plants()
        return {"plants": plants}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get plants: {str(e)}")


@app.get("/api/graph/plants/{plant_name}/areas")
async def get_asset_areas_by_plant(plant_name: str):
    """Get all asset areas for a specific plant"""
    if not graph_service.is_connected():
        raise HTTPException(status_code=503, detail="Graph service not available")
    
    try:
        areas = graph_service.get_asset_areas_by_plant(plant_name)
        return {"plant": plant_name, "asset_areas": areas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get asset areas: {str(e)}")


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
        
        return context
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get contextual subgraph: {str(e)}")


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
        raise HTTPException(status_code=500, detail=f"Failed to get data quality summary: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)