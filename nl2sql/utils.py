"""Utility functions for the nl2sql package."""

from nl2sql.database.base import SQLBaseConnector


def print_section(title: str, separator: str = "=") -> None:
    """Print a section with a title and a separator."""
    print(f"{title}\n{separator * len(title)}")


def validate_sql_syntax(query: str, db_conn: SQLBaseConnector) -> dict:
    """Validate SQL syntax using PostgreSQL's PREPARE statement.

    Args:
        query (str): The SQL query to validate.
        db_conn: A SQLBaseConnector instance.

    Returns:
        dict: {
            "valid_syntax": bool,
            "error": str or None
        }
    """
    cur = db_conn.engine.raw_connection().cursor()
    result = {"valid_syntax": True, "error": None}

    try:
        cur.execute(f"PREPARE validate_stmt AS {query}")
        cur.execute("DEALLOCATE validate_stmt")
    except Exception as e:
        result["valid_syntax"] = False
        result["error"] = str(e)
    finally:
        cur.close()

    return result
