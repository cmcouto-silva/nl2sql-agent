"""NL2SQL agent utilities."""

import pandas as pd
from langchain_core.messages import BaseMessage
from loguru import logger
from sqlalchemy import text

from nl2sql.agents.state import State
from nl2sql.database.base import SQLBaseConnector


def get_chat_history(messages: list[BaseMessage], last_n_messages: int = 10) -> str:
    """Get the chat history from the messages."""
    return "\n".join(
        [f"{msg.type.upper()}: {msg.content}" for msg in messages[-last_n_messages:]]
    )


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


def format_answer(state: State) -> str:
    """Format the answer for the user."""
    formatted_answer = f"**SQL:**\n```sql\n{state.sql_query}\n```"

    if state.sql_explanation:
        formatted_answer += f"\n\n**Explanation:**\n{state.sql_explanation}\n"

    return formatted_answer


def execute_sql_query(query: str, db_conn: SQLBaseConnector) -> dict:
    """Execute SQL query and return formatted results.

    Args:
        query (str): The SQL query to execute.
        db_conn: A SQLBaseConnector instance.

    Returns:
        dict: {
            "success": bool,
            "data": pandas.DataFrame or None,
            "row_count": int,
            "error": str or None,
            "query_executed": str
        }
    """
    result = {
        "success": False,
        "data": None,
        "row_count": 0,
        "error": None,
        "query_executed": query.strip(),
    }

    logger.debug(
        f"🔄 Executing SQL query: {query[:100]}{'...' if len(query) > 100 else ''}"
    )

    try:
        with db_conn.engine.connect() as conn:
            query_result = conn.execute(text(query))
            logger.debug(f"Returns rows: {query_result.returns_rows}")

            if query_result.returns_rows:
                result["data"] = pd.DataFrame(
                    data=query_result.fetchall(), columns=query_result.keys()
                ).to_dict("records")
                result["row_count"] = len(result["data"])
                logger.debug(
                    "✅ Query executed successfully. "
                    f"Returned {result['row_count']} rows."
                )

            result["success"] = True

    except Exception as e:
        result["error"] = str(e)
        result["success"] = False
        logger.error(f"❌ SQL execution failed: {e}")

    return result


def format_query_results_for_llm(
    execution_result: dict, max_rows: int = 5, max_cols: int | None = None
) -> str:
    """Format SQL execution results for LLM interpretation.

    Args:
        execution_result: Result dictionary from execute_sql_query
        max_rows: Maximum number of rows to include in the formatted output
        max_cols: Maximum number of columns to include in the formatted output

    Returns:
        Formatted string representation of the results
    """
    if not execution_result["success"]:
        return f"Query execution failed: {execution_result['error']}"

    if execution_result["data"] is None:
        logger.warning("Query executed successfully but returned no results.")
        return "Query executed successfully but returned no results."

    # Convert to pandas DataFrame
    df = pd.DataFrame(execution_result["data"])

    result_text = (
        "Query executed successfully. "
        f"Returned {len(df)} rows and {len(df.columns)} columns.\n"
        f"Columns: {', '.join(df.columns)}\n\n"
    )

    # Add sample data (limited to max_rows and max_cols)
    result_text += "Results:\n"
    result_text += df.iloc[:max_rows, :max_cols].to_string(index=False)

    # Add note if results were truncated
    if len(df) > max_rows:
        result_text += f"\n\n... ({len(df) - max_rows} more rows not shown)"
    if max_cols is not None and len(df.columns) > max_cols:
        result_text += f"\n\n... ({len(df.columns) - max_cols} more columns not shown)"

    return result_text
