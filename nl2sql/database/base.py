"""Base class for SQL connectors."""

import os
from abc import ABC, abstractmethod
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from sqlalchemy import Engine, inspect

from nl2sql.config import load_database_config

load_dotenv()


class DatabaseParams(BaseModel):
    """Database connection configuration using Pydantic.

    This model represents database connection parameters.
    """

    host: str
    port: int
    database: str
    username: str
    password: str = Field(repr=False)

    def __repr__(self) -> str:
        """Custom string representation to mask the password."""
        return (
            f"DatabaseParams(host={self.host}, port={self.port}, "
            f"database={self.database}, username={self.username}, "
            f"password={'*' * len(self.password)})"
        )


class SQLBaseConnector(ABC):
    """Base class for SQL connectors."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        database: str | None = None,
        username: str | None = None,
        password: str | None = None,
        config_path: Path | None = None,
    ) -> None:
        """Initialize the SQL connector."""
        self.params = self._resolve_params(
            host, port, database, username, password, config_path
        )
        self.engine = self.create_engine(self.params)
        self.inspector = inspect(self.engine)

    def _resolve_params(
        self,
        host: str | None = None,
        port: int | None = None,
        database: str | None = None,
        username: str | None = None,
        password: str | None = None,
        config_path: Path | None = None,
    ) -> DatabaseParams:
        """Resolve database parameters."""
        db_config = load_database_config(config_path) if config_path else {}

        return DatabaseParams(
            host=host or db_config.get("host") or os.getenv("DB_HOST"),
            port=port or db_config.get("port") or os.getenv("DB_PORT"),
            database=database or db_config.get("database") or os.getenv("DB_NAME"),
            username=username or db_config.get("username") or os.getenv("DB_USER"),
            password=quote_plus(
                password or db_config.get("password") or os.getenv("DB_PASSWORD")
            ),
        )

    @abstractmethod
    def create_uri(self, params: DatabaseParams, dialect: str, driver: str) -> str:
        """Create a URI for a database."""
        pass

    @abstractmethod
    def create_engine(self, params: DatabaseParams) -> Engine:
        """Create a SQLAlchemy engine."""
        pass
