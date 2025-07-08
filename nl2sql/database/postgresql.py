"""PostgreSQL connector."""

from pathlib import Path
from urllib.parse import unquote_plus

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
        """Create a SQLAlchemy URI for a PostgreSQL database.

        Args:
            params: Database connection parameters
            dialect: SQL dialect (default: "postgresql")
            driver: Database driver (default: "psycopg")

        Returns:
            str: SQLAlchemy URI (e.g., "postgresql+psycopg://user:pass@host:port/db")
        """
        dialect_driver = f"{dialect}+{driver}" if driver else dialect
        return f"{dialect_driver}://{params.username}:{params.password}@{params.host}:{params.port}/{params.database}"

    def create_postgresql_uri(self, params: DatabaseParams | None = None) -> str:
        """Create a standard PostgreSQL URI (compatible with psycopg Connection).

        Args:
            params: DatabaseParams to use. If None, uses self.params.

        Returns:
            str: PostgreSQL URI (e.g., "postgresql://user:pass@host:port/db")
        """
        if params is None:
            params = self.params

        password = unquote_plus(params.password)
        return f"postgresql://{params.username}:{password}@{params.host}:{params.port}/{params.database}"

    def get_psycopg_connection(
        self,
        autocommit: bool = True,
        prepare_threshold: int = 0,
        row_factory: object = None,
        **kwargs: str | int | bool,
    ) -> object:
        """Get a direct psycopg Connection object.

        Args:
            autocommit: Whether to use autocommit mode (default: True)
            prepare_threshold: Number of executions before preparing statements
            row_factory: Row factory for result formatting (commonly dict_row)
            **kwargs: Additional connection parameters for psycopg Connection

        Returns:
            psycopg.Connection: Direct psycopg connection object
        """
        from psycopg import Connection

        conn_string = self.create_postgresql_uri()
        return Connection.connect(
            conn_string,
            autocommit=autocommit,
            prepare_threshold=prepare_threshold,
            row_factory=row_factory,
            **kwargs,
        )

    def create_engine(self, params: DatabaseParams) -> Engine:
        """Create a SQLAlchemy engine."""
        return create_engine(self.create_uri(params))
