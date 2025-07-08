"""Pydantic models for API requests and responses."""

from typing import Any

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    database_connected: bool
    message: str


class ChatRequest(BaseModel):
    """Chat request model."""

    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    """Chat response model."""

    message: str
    session_id: str
    metadata: dict[str, Any] | None = None
