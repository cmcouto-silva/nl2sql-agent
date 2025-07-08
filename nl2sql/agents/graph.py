"""NL2SQL agent graph."""

from functools import partial

from langgraph.graph import END, START, StateGraph

from nl2sql.agents import nodes
from nl2sql.agents.state import State
from nl2sql.database.postgresql import PostgreSQLConnector
from nl2sql.knowledge_base.vector_store import VectorStore

# ===============================
# Graph
# ===============================


def create_graph(
    db_connector: PostgreSQLConnector, vector_store: VectorStore
) -> StateGraph:
    """Create the NL2SQL agent graph."""
    # State Workflow
    workflow = StateGraph(State)

    # Create agent nodes with dependencies
    chat_agent_node = partial(nodes.chat_agent, vector_store=vector_store)
    sql_generator_node = partial(nodes.sql_generator, vector_store=vector_store)
    sql_syntax_validator_node = partial(
        nodes.sql_syntax_validator, db_connector=db_connector
    )
    sql_executor_node = partial(nodes.sql_executor, db_connector=db_connector)

    # Add nodes
    workflow.add_node("intent_classifier", nodes.intent_classifier)
    workflow.add_node("chat_agent", chat_agent_node)
    workflow.add_node("sql_generator", sql_generator_node)
    workflow.add_node("sql_safety_validator", nodes.sql_safety_validator)
    workflow.add_node("sql_syntax_validator", sql_syntax_validator_node)
    workflow.add_node("human_feedback", nodes.human_feedback)
    workflow.add_node("sql_executor", sql_executor_node)
    workflow.add_node("sql_result_analyzer", nodes.sql_result_analyzer)

    # Add Edges
    workflow.add_edge(START, "intent_classifier")

    workflow.add_conditional_edges(
        "intent_classifier",
        nodes.route_intent,
        {
            "sql": "sql_generator",
            "chat": "chat_agent",
        },
    )

    workflow.add_conditional_edges(
        "sql_generator",
        nodes.check_sql_generation,
        {
            "success": "sql_safety_validator",
            "failure": END,
        },
    )

    workflow.add_conditional_edges(
        "sql_safety_validator",
        nodes.check_sql_safety,
        {
            "safe": "sql_syntax_validator",
            "unsafe": END,
        },
    )

    workflow.add_conditional_edges(
        "sql_syntax_validator",
        nodes.check_sql_syntax,
        {
            "valid": "human_feedback",
            "invalid": END,
        },
    )

    workflow.add_conditional_edges(
        "human_feedback",
        nodes.check_human_feedback,
        {
            "approved": "sql_executor",
            "rejected": END,
        },
    )

    workflow.add_conditional_edges(
        "sql_executor",
        nodes.check_sql_execution,
        {
            "success": "sql_result_analyzer",
            "failure": END,
        },
    )

    workflow.add_edge("sql_result_analyzer", END)
    workflow.add_edge("chat_agent", END)

    return workflow
