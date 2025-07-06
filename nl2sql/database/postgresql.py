"""PostgreSQL connector."""

from pathlib import Path

from sqlalchemy import Engine, create_engine

from nl2sql.database.base import DatabaseParams, SQLBaseConnector


class PostgreSQLConnector(SQLBaseConnector):
    """PostgreSQL connector."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        database: str | None = None,
        username: str | None = None,
        password: str | None = None,
        config_path: Path | None = None,
    ) -> None:
        """Initialize the PostgreSQL connector."""
        super().__init__(host, port, database, username, password, config_path)

    def create_uri(
        self,
        params: DatabaseParams,
        dialect: str = "postgresql",
        driver: str = "psycopg",
    ) -> str:
        """Create a URI for a PostgreSQL database."""
        dialect_driver = f"{dialect}+{driver}" if driver else dialect
        return f"{dialect_driver}://{params.username}:{params.password}@{params.host}:{params.port}/{params.database}"

    def create_engine(self, params: DatabaseParams) -> Engine:
        """Create a SQLAlchemy engine."""
        return create_engine(self.create_uri(params))
