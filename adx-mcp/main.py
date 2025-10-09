"""
Azure Data Explorer MCP Service
Implements MCP (Model Context Protocol) for connecting to Azure ADX
"""

import os
import json
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from azure.kusto.data import KustoClient, KustoConnectionStringBuilder
from azure.kusto.data.exceptions import KustoServiceError
from azure.identity import ClientSecretCredential
import uvicorn
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Azure ADX MCP Service", version="1.0.0")

# Configuration
ADX_CLUSTER_URL = os.getenv("ADX_CLUSTER_URL", "")
ADX_DATABASE = os.getenv("ADX_DATABASE", "")
ADX_CLIENT_ID = os.getenv("ADX_CLIENT_ID", "")
ADX_CLIENT_SECRET = os.getenv("ADX_CLIENT_SECRET", "")
ADX_TENANT_ID = os.getenv("ADX_TENANT_ID", "")

# Initialize ADX client if credentials are provided
kusto_client = None
if all([ADX_CLUSTER_URL, ADX_CLIENT_ID, ADX_CLIENT_SECRET, ADX_TENANT_ID]):
    try:
        kcsb = KustoConnectionStringBuilder.with_aad_application_key_authentication(
            connection_string=ADX_CLUSTER_URL,
            aad_app_id=ADX_CLIENT_ID,
            app_key=ADX_CLIENT_SECRET,
            authority_id=ADX_TENANT_ID
        )
        kusto_client = KustoClient(kcsb)
        print("ADX client initialized successfully")
    except Exception as e:
        print(f"Failed to initialize ADX client: {e}")


class MCPRequest(BaseModel):
    method: str
    params: Optional[Dict[str, Any]] = None


class MCPResponse(BaseModel):
    result: Optional[Any] = None
    error: Optional[str] = None


class KQLQuery(BaseModel):
    query: str
    database: Optional[str] = None


class SchemaInfo(BaseModel):
    tables: List[str]
    columns: Dict[str, List[str]]


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "adx_connected": kusto_client is not None,
        "database": ADX_DATABASE
    }


@app.post("/mcp", response_model=MCPResponse)
async def handle_mcp_request(request: MCPRequest):
    """Handle MCP protocol requests"""
    try:
        if request.method == "tools/list":
            return MCPResponse(result={
                "tools": [
                    {
                        "name": "execute_kql",
                        "description": "Execute KQL (Kusto Query Language) queries against Azure Data Explorer",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "KQL query to execute"},
                                "database": {"type": "string", "description": "Database name (optional)"}
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "get_schema",
                        "description": "Get database schema information including tables and columns",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "database": {"type": "string", "description": "Database name (optional)"}
                            }
                        }
                    },
                    {
                        "name": "get_sample_data",
                        "description": "Get sample data from a specific table",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "table": {"type": "string", "description": "Table name"},
                                "limit": {"type": "number", "description": "Number of rows to return (default: 10)"}
                            },
                            "required": ["table"]
                        }
                    }
                ]
            })
        
        elif request.method == "tools/call":
            tool_name = request.params.get("name")
            arguments = request.params.get("arguments", {})
            
            if tool_name == "execute_kql":
                return await execute_kql(arguments)
            elif tool_name == "get_schema":
                return await get_schema(arguments)
            elif tool_name == "get_sample_data":
                return await get_sample_data(arguments)
            else:
                return MCPResponse(error=f"Unknown tool: {tool_name}")
        
        else:
            return MCPResponse(error=f"Unknown method: {request.method}")
    
    except Exception as e:
        return MCPResponse(error=str(e))


async def execute_kql(arguments: Dict[str, Any]) -> MCPResponse:
    """Execute a KQL query"""
    if not kusto_client:
        return MCPResponse(error="ADX client not initialized. Check configuration.")
    
    query = arguments.get("query")
    database = arguments.get("database", ADX_DATABASE)
    
    if not query:
        return MCPResponse(error="Query is required")
    
    try:
        response = kusto_client.execute(database, query)
        
        # Convert response to JSON-serializable format
        results = []
        for row in response.primary_results[0]:
            results.append(dict(row))
        
        return MCPResponse(result={
            "query": query,
            "database": database,
            "row_count": len(results),
            "results": results
        })
    
    except KustoServiceError as e:
        return MCPResponse(error=f"KQL Error: {str(e)}")
    except Exception as e:
        return MCPResponse(error=f"Execution Error: {str(e)}")


async def get_schema(arguments: Dict[str, Any]) -> MCPResponse:
    """Get database schema information"""
    if not kusto_client:
        # Return mock schema for development/testing
        return MCPResponse(result={
            "tables": ["hmi_sensor_data", "tag_configuration", "itera_measurements"],
            "columns": {
                "hmi_sensor_data": ["timestamp", "name", "value", "unit", "quality"],
                "tag_configuration": ["record_id", "name", "description", "tag_units", "asset"],
                "itera_measurements": ["timestamp", "li_329_value", "li_331_value", "li_440_value"]
            }
        })
    
    database = arguments.get("database", ADX_DATABASE)
    
    try:
        # Get all tables
        tables_query = ".show tables"
        tables_response = kusto_client.execute(database, tables_query)
        tables = [row["TableName"] for row in tables_response.primary_results[0]]
        
        # Get columns for each table
        columns = {}
        for table in tables:
            columns_query = f".show table {table} schema"
            columns_response = kusto_client.execute(database, columns_query)
            columns[table] = [row["ColumnName"] for row in columns_response.primary_results[0]]
        
        return MCPResponse(result={
            "database": database,
            "tables": tables,
            "columns": columns
        })
    
    except Exception as e:
        return MCPResponse(error=f"Schema Error: {str(e)}")


async def get_sample_data(arguments: Dict[str, Any]) -> MCPResponse:
    """Get sample data from a table"""
    if not kusto_client:
        return MCPResponse(error="ADX client not initialized. Check configuration.")
    
    table = arguments.get("table")
    limit = arguments.get("limit", 10)
    database = arguments.get("database", ADX_DATABASE)
    
    if not table:
        return MCPResponse(error="Table name is required")
    
    try:
        query = f"{table} | take {limit}"
        response = kusto_client.execute(database, query)
        
        results = []
        for row in response.primary_results[0]:
            results.append(dict(row))
        
        return MCPResponse(result={
            "table": table,
            "database": database,
            "sample_count": len(results),
            "data": results
        })
    
    except Exception as e:
        return MCPResponse(error=f"Sample Data Error: {str(e)}")


@app.get("/tables")
async def list_tables():
    """List all available tables"""
    if not kusto_client:
        return {
            "tables": ["hmi_sensor_data", "tag_configuration", "itera_measurements"],
            "note": "Mock data - ADX client not configured"
        }
    
    try:
        query = ".show tables"
        response = kusto_client.execute(ADX_DATABASE, query)
        tables = [row["TableName"] for row in response.primary_results[0]]
        return {"tables": tables}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query")
async def execute_query(query_request: KQLQuery):
    """Direct query execution endpoint"""
    if not kusto_client:
        raise HTTPException(status_code=503, detail="ADX client not initialized")
    
    try:
        database = query_request.database or ADX_DATABASE
        response = kusto_client.execute(database, query_request.query)
        
        results = []
        for row in response.primary_results[0]:
            results.append(dict(row))
        
        return {
            "query": query_request.query,
            "database": database,
            "row_count": len(results),
            "results": results
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)