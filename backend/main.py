"""
Backend API for Agentic Insight Application

Main application entry point. Initializes FastAPI app and registers routers.
Integrates OpenAI agents with Azure ADX MCP for industrial data insights.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core import dependencies  # Import to trigger service initialization
from api import health, query, graph, entities, maintenance


# Initialize FastAPI application
app = FastAPI(
    title="Agentic Insight API",
    version="1.0.0",
    description="AI-powered industrial data analytics with graph navigation"
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(health.router)
app.include_router(query.router)
app.include_router(graph.router)
app.include_router(entities.router)
app.include_router(maintenance.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
