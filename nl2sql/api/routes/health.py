"""Health check routes for the NL2SQL API."""

from fastapi import APIRouter
from loguru import logger
from sqlalchemy import text

from nl2sql.api.models import HealthResponse
from nl2sql.database.postgresql import PostgreSQLConnector

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint that verifies database connectivity."""
    try:
        # Test database connection
        db_connector = PostgreSQLConnector(config_path="configs/database.yml")

        # Test basic connectivity with a simple query
        with db_connector.engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            test_value = result.fetchone()[0]

        if test_value == 1:
            logger.info("✅ Health check passed - database connected")
            return HealthResponse(
                status="healthy",
                database_connected=True,
                message="Service is healthy and database is connected",
            )
        else:
            logger.error("❌ Health check failed - unexpected database response")
            return HealthResponse(
                status="unhealthy",
                database_connected=False,
                message="Database connection test failed",
            )

    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            database_connected=False,
            message=f"Database connection error: {e!s}",
        )
