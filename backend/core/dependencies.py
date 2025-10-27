"""
Service dependencies and initialization

Manages initialization of external services (OpenAI, Neo4j, Maintenance API).
"""

from typing import Optional
from openai import OpenAI
from services.graph_service import graph_service
from services.maintenance_service import MaintenanceAPIService
from core.config import settings


# Initialize OpenAI client
openai_client: Optional[OpenAI] = None
if settings.OPENAI_API_KEY:
    openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    print("✓ OpenAI client initialized successfully")
else:
    print("⚠ OpenAI API key not provided")


# Initialize Neo4j Graph service
graph_connected = graph_service.connect()
if graph_connected:
    print("✓ Neo4j graph service initialized successfully")
else:
    print("⚠ Neo4j graph service connection failed - continuing without graph features")


# Initialize Maintenance API service
maintenance_service: Optional[MaintenanceAPIService] = None
try:
    maintenance_service = MaintenanceAPIService()
    print("✓ Maintenance API service initialized successfully")
except ValueError as e:
    print(f"⚠ Maintenance API service not initialized: {e}")


def get_openai_client() -> Optional[OpenAI]:
    """
    Get the OpenAI client instance
    
    Returns:
        OpenAI client or None if not initialized
    """
    return openai_client


def get_maintenance_service() -> Optional[MaintenanceAPIService]:
    """
    Get the Maintenance API service instance
    
    Returns:
        MaintenanceAPIService or None if not initialized
    """
    return maintenance_service
