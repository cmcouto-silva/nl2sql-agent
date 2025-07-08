"""Chat API routes."""

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres import PostgresSaver
from loguru import logger
from psycopg import Connection
from psycopg.rows import dict_row

from nl2sql.agents.graph import create_graph
from nl2sql.api.models import ChatRequest, ChatResponse
from nl2sql.database.postgresql import PostgreSQLConnector
from nl2sql.knowledge_base.vector_store import VectorStore

router = APIRouter()

# Global component instances (initialized on first request)
_db_connector = None
_vector_store = None
_graph = None
_memory = None


def _initialize_components() -> None:
    """Initialize database, vector store, graph, and memory components."""
    global _db_connector, _vector_store, _graph, _memory

    if _db_connector is None:
        logger.info("🔄 Initializing database connector...")
        _db_connector = PostgreSQLConnector(config_path="configs/database.yml")

    if _vector_store is None:
        logger.info("🔄 Initializing vector store...")
        _vector_store = VectorStore(_db_connector)

    if _memory is None:
        logger.info("🔄 Initializing PostgreSQL memory...")
        # Get connection string and create psycopg connection
        conn_string = _db_connector.create_postgresql_uri()
        postgres_conn = Connection.connect(
            conn_string, autocommit=True, prepare_threshold=0, row_factory=dict_row
        )
        _memory = PostgresSaver(conn=postgres_conn)
        # Setup memory tables
        _memory.setup()

    if _graph is None:
        logger.info("🔄 Initializing agent graph...")
        workflow = create_graph(_db_connector, _vector_store)
        _graph = workflow.compile(checkpointer=_memory)


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Chat endpoint that processes user messages through the NL2SQL agent."""
    try:
        # Initialize components if needed
        _initialize_components()

        # Generate session ID if not provided
        session_id = (
            request.session_id
            or f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"  # noqa: E501
        )

        logger.info(f"🔄 Processing chat request for session: {session_id}")
        logger.debug(f"User message: {request.message}")

        # Create user message
        user_message = HumanMessage(content=request.message)

        # Configure graph execution
        config = {"configurable": {"thread_id": session_id}}

        # Check if there's an existing interrupted state to resume
        existing_state = _graph.get_state(config)
        if existing_state.next and request.message.lower() in ["yes", "no"]:
            # This is a response to an interrupt, resume the graph
            logger.debug("🔄 Resuming interrupted graph...")
            from langgraph.types import Command

            result = _graph.invoke(Command(resume=request.message), config=config)
        else:
            # Create initial state and start new conversation
            initial_state = {"messages": [user_message]}

            # Execute the agent graph
            logger.debug("🔄 Executing agent graph...")
            result = _graph.invoke(initial_state, config=config)

        # Check if the graph was interrupted (for human feedback)
        if "__interrupt__" in result:
            interrupt_data = result["__interrupt__"][0].value
            interrupt_message = interrupt_data.get("messages")
            if hasattr(interrupt_message, "content"):
                last_message = interrupt_message.content
            elif isinstance(interrupt_message, str):
                last_message = interrupt_message
            else:
                last_message = (
                    "Waiting for your confirmation. Please respond with 'yes' or 'no'."
                )
        else:
            # Extract the last AI message from the result
            last_message = None
            if result.get("messages"):
                # Get the last message that isn't the user's input
                for msg in reversed(result["messages"]):
                    if hasattr(msg, "type") and msg.type != "human":
                        last_message = msg.content
                        break

            if last_message is None:
                last_message = (
                    "I processed your message but couldn't generate a response."
                )

        logger.info(f"✅ Chat request completed for session: {session_id}")

        return ChatResponse(
            message=last_message,
            session_id=session_id,
            metadata={
                "user_intent": result.get("user_intent"),
                "sql_query": result.get("sql_query"),
                "sql_safety_status": result.get("sql_safety_status"),
                "sql_syntax_status": result.get("sql_syntax_status"),
                "sql_execution_status": result.get("sql_execution_status"),
            },
        )

    except Exception as e:
        logger.error(f"❌ Chat request failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Chat processing error: {e!s}"
        ) from e
