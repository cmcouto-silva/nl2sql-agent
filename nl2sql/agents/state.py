"""NL2SQL agent state."""

from typing import Annotated, Any, Literal

from langgraph.graph.message import BaseMessage, add_messages
from pydantic import BaseModel


class Session(BaseModel):
    """Session information."""

    session_id: str
    metadata: dict[str, Any]


class State(BaseModel):
    """State for the NL2SQL agent."""

    messages: Annotated[list[BaseMessage], add_messages]
    user_query: str | None = None
    user_intent: Literal["sql", "chat"] | None = None
    sql_query: str | None = None
    sql_explanation: str | None = None
    sql_execution_result: dict[str, Any] | None = None
    sql_execution_analysis: str | None = None
    sql_safety_status: Literal["safe", "unsafe"] | None = None
    sql_syntax_status: Literal["valid", "invalid"] | None = None
    user_feedback_status: Literal["approved", "rejected"] | None = None
    sql_execution_status: Literal["success", "failure"] | None = None
