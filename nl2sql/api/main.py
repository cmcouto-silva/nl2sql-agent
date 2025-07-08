"""Main FastAPI application for NL2SQL agent."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from nl2sql.api.routes.chat import router as chat_router
from nl2sql.api.routes.health import router as health_router

# Create FastAPI application
app = FastAPI(
    title="NL2SQL Agent API",
    description="A RAG-powered AI agent that translates natural language into SQL for live database querying.",  # noqa: E501
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, tags=["Health"])
app.include_router(chat_router, prefix="/chat", tags=["Chat"])


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "message": "Welcome to NL2SQL Agent API",
        "docs": "/docs",
        "health": "/health",
        "chat": "/chat",
    }


@app.on_event("startup")
async def startup_event() -> None:
    """Startup event handler."""
    logger.info("🚀 NL2SQL Agent API starting up...")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Shutdown event handler."""
    logger.info("🛑 NL2SQL Agent API shutting down...")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "nl2sql.api.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
