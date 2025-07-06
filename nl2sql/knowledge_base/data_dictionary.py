"""Database schema inspection and documentation tools.

This module extracts and documents database schema information, including
table structures, columns, and relationships using SQLAlchemy's inspector.
"""

from pathlib import Path

import yaml
from pydantic import BaseModel
from sqlalchemy.engine.reflection import Inspector


class ColumnInfo(BaseModel):
    """Information about a database column."""

    name: str
    description: str
    type: str
    is_primary_key: bool
    is_nullable: bool
    foreign_keys: list[dict]

    @staticmethod
    def _extract_type(column: dict) -> str:
        """Extract the type of a column from the database."""
        column_type = str(column["type"])
        return column_type if column_type != "NULL" else "USER-DEFINED"


class TableInfo(BaseModel):
    """Information about a database table."""

    name: str
    schema_name: str
    description: str
    primary_keys: list[str]
    foreign_keys: list[dict]
    columns: list[ColumnInfo]

    @classmethod
    def from_inspector(
        cls, inspector: Inspector, table: str, schema: str
    ) -> "TableInfo":
        """Create TableInfo from SQLAlchemy inspector."""
        # Extract column information
        columns = inspector.get_columns(table, schema=schema)

        # Extract primary key information
        primary_keys = inspector.get_pk_constraint(table, schema=schema)

        # Extract foreign key information
        foreign_keys = inspector.get_foreign_keys(table, schema=schema)

        # Extract columns' info
        column_info = [
            ColumnInfo(
                name=column["name"],
                description=column.get("comment", "") or "",
                type=ColumnInfo._extract_type(column),
                is_primary_key=column["name"]
                in primary_keys.get("constrained_columns", []),
                is_nullable=column["nullable"],
                foreign_keys=[
                    {
                        "referred_table": fk.get("referred_table"),
                        "referred_schema": fk.get("referred_schema"),
                        "referred_columns": fk.get("referred_columns"),
                        "name": fk.get("name"),
                    }
                    for fk in foreign_keys
                    if column["name"] in fk.get("constrained_columns", [])
                ],
            )
            for column in columns
        ]

        return cls(
            name=table,
            schema_name=schema,
            description=(
                inspector.get_table_comment(table, schema=schema).get("text", "") or ""
            ),
            primary_keys=primary_keys.get("constrained_columns", []),
            foreign_keys=[
                {
                    "constrained_columns": fk.get("constrained_columns", []),
                    "referred_table": fk.get("referred_table"),
                    "referred_schema": fk.get("referred_schema"),
                    "referred_columns": fk.get("referred_columns"),
                    "name": fk.get("name"),
                }
                for fk in foreign_keys
            ],
            columns=column_info,
        )

    def format_context(self) -> str:
        """Format table information as a string for context retrieval."""
        # Start with table name and description
        context = f"TABLE: {self.name}\n"
        if self.description:
            context += f"DESCRIPTION: {self.description}\n"

        # Add primary keys
        if self.primary_keys:
            context += f"PRIMARY KEYS: {', '.join(self.primary_keys)}\n"

        # Add foreign keys
        if self.foreign_keys:
            context += "FOREIGN KEYS:\n"
            for fk in self.foreign_keys:
                constrained = ", ".join(fk["constrained_columns"])
                referred = ", ".join(fk["referred_columns"])
                context += (
                    f"  - {constrained} -> "
                    f"{fk['referred_schema']}.{fk['referred_table']}.{referred}\n"
                )

        # Add columns with descriptions
        context += "COLUMNS:\n"
        for column in self.columns:
            if not column.description:
                continue
            # Format column type, nullability, and description
            is_nullable = "NULL" if column.is_nullable else "NOT NULL"
            context += (
                f"  - {column.name} ({column.type}, {is_nullable}): "
                f"{column.description}\n"
            )

        return context

    def populate_missing_pk_descriptions(self) -> None:
        """Populate missing primary key descriptions."""
        for column in self.columns:
            if not column.description and column.is_primary_key:
                column.description = "Primary Key"

    def get_columns_with_missing_descriptions(self) -> list[str]:
        """Get list of columns with missing descriptions."""
        return [col.name for col in self.columns if not col.description]


class SchemaInfo(BaseModel):
    """Information about a database schema."""

    name: str
    tables: dict[str, TableInfo]

    def format_context(self) -> str:
        """Format schema information as a string for context retrieval."""
        context = f"SCHEMA: {self.name}\n\n"
        for table_info in self.tables.values():
            context += table_info.format_context() + "\n\n"
        return context

    def get_tables_with_missing_descriptions(self) -> list[str]:
        """Get list of tables with missing descriptions."""
        return [
            table_name
            for table_name, table_info in self.tables.items()
            if not table_info.description
        ]

    def get_columns_with_missing_descriptions(self) -> dict[str, list[str]]:
        """Get columns with missing descriptions organized by table."""
        missing_columns = {}
        for table_name, table_info in self.tables.items():
            cols_missing = table_info.get_columns_with_missing_descriptions()
            if cols_missing:
                missing_columns[table_name] = cols_missing
        return missing_columns


class DatabaseInfo(BaseModel):
    """Information about a database."""

    name: str
    schemas: dict[str, SchemaInfo]

    def format_context(self) -> str:
        """Format database information as a string for context retrieval."""
        context = f"DATABASE: {self.name}\n\n"
        for schema_info in self.schemas.values():
            context += schema_info.format_context()
        return context

    def get_tables_with_missing_descriptions(self) -> dict[str, list[str]]:
        """Get tables with missing descriptions organized by schema."""
        missing_tables = {}
        for schema_name, schema_info in self.schemas.items():
            tables_missing = schema_info.get_tables_with_missing_descriptions()
            if tables_missing:
                missing_tables[schema_name] = tables_missing
        return missing_tables

    def get_columns_with_missing_descriptions(self) -> dict[str, dict[str, list[str]]]:
        """Get columns with missing descriptions organized by schema and table."""
        missing_columns = {}
        for schema_name, schema_info in self.schemas.items():
            schema_missing = schema_info.get_columns_with_missing_descriptions()
            if schema_missing:
                missing_columns[schema_name] = schema_missing
        return missing_columns


class DataDictionary(BaseModel):
    """Main data dictionary containing all database information."""

    databases: dict[str, DatabaseInfo]

    @classmethod
    def from_inspector(
        cls,
        inspector: Inspector,
        database_schema: dict,
        handle_missing_pk_descriptions: bool = True,
    ) -> "DataDictionary":
        """Create DataDictionary from SQLAlchemy inspector."""
        databases = {}

        for database_name, schemas in database_schema.items():
            schema_dict = {}

            for schema_name, tables in schemas.items():
                table_dict = {}

                for table_name in tables:
                    table_info = TableInfo.from_inspector(
                        inspector, table_name, schema_name
                    )

                    if handle_missing_pk_descriptions:
                        table_info.populate_missing_pk_descriptions()

                    table_dict[table_name] = table_info

                schema_dict[schema_name] = SchemaInfo(
                    name=schema_name, tables=table_dict
                )

            databases[database_name] = DatabaseInfo(
                name=database_name, schemas=schema_dict
            )

        return cls(databases=databases)

    def format_context(self) -> str:
        """Format all schema information as a string for context retrieval."""
        context = ""
        for database_info in self.databases.values():
            context += database_info.format_context()
        return context

    def save(self, output_path: Path | str) -> Path:
        """Save data dictionary to a YAML file."""
        if isinstance(output_path, str):
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False, sort_keys=False)

        return output_path

    @classmethod
    def load(
        cls, file_path: Path | str = "knowledge/data_dictionary.yml"
    ) -> "DataDictionary":
        """Load data dictionary from a YAML file."""
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Data dictionary file not found: {file_path}")

        with open(file_path) as f:
            raw_data = yaml.safe_load(f)

        return cls(**raw_data)

    def get_tables_with_missing_descriptions(self) -> dict[str, dict[str, list[str]]]:
        """Get tables with missing descriptions."""
        missing_tables = {}
        for db_name, db_info in self.databases.items():
            db_missing = db_info.get_tables_with_missing_descriptions()
            if db_missing:
                missing_tables[db_name] = db_missing
        return missing_tables

    def get_columns_with_missing_descriptions(
        self,
    ) -> dict[str, dict[str, dict[str, list[str]]]]:
        """Get columns with missing descriptions."""
        missing_columns = {}
        for db_name, db_info in self.databases.items():
            db_missing = db_info.get_columns_with_missing_descriptions()
            if db_missing:
                missing_columns[db_name] = db_missing
        return missing_columns
