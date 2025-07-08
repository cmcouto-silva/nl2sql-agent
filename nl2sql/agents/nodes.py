"""NL2SQL agent nodes."""

from typing import Literal

import pandas as pd
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import interrupt
from loguru import logger

from nl2sql.agents.state import State
from nl2sql.agents.utils import (
    execute_sql_query,
    format_answer,
    format_query_results_for_llm,
    get_chat_history,
    validate_sql_syntax,
)
from nl2sql.config import UNSAFE_SQL_KEYWORDS, load_chat_prompt_template
from nl2sql.database.postgresql import PostgreSQLConnector
from nl2sql.knowledge_base.data_dictionary import DataDictionary
from nl2sql.knowledge_base.sql_examples import SQLExample
from nl2sql.knowledge_base.vector_store import VectorStore

# ===============================
# Prompts & Knowledge Base
# ===============================

intent_classifier_prompt = load_chat_prompt_template(target_prompt="intent_classifier")
sql_generator_prompt = load_chat_prompt_template(target_prompt="sql_generator")

# Load knowledge base components
data_dictionary = DataDictionary.load()
sql_examples = SQLExample.from_yaml("knowledge/sql_examples.yml")


# ===============================
# Agent Nodes
# ===============================


def intent_classifier(state: State) -> dict:
    """Determine if user wants chat or SQL functionality."""
    logger.info("🔄 [Node] Intent Classifier")

    # Retrieve chat history
    chat_history = get_chat_history(state.messages[:-1])
    user_query = state.messages[-1].content
    logger.debug(f"Chat history:\n{chat_history}")
    logger.debug(f"Last message: {user_query}")

    # Classify user intent using LLM
    llm = init_chat_model(model="gpt-4.1-mini", model_provider="openai", temperature=0)
    router_llm_chain = intent_classifier_prompt | llm

    response = router_llm_chain.invoke(
        {"user_message": user_query, "chat_history": chat_history}
    )

    detected_user_intent = response.content.strip().lower()
    logger.debug(f"Detected user intent: {detected_user_intent}")

    # Default to chat if the intent is not chat or sql
    if detected_user_intent not in ["chat", "sql"]:
        logger.warning(
            "⚠️ LLM Router returned unexpected classification: "
            f"'{detected_user_intent}'. Defaulting to chat."
        )
        return {"user_intent": "chat"}

    return {"user_intent": detected_user_intent, "user_query": user_query}


def chat_agent(state: State, vector_store: VectorStore) -> dict:
    """Handle general chat queries using a ReAct-style agent."""
    logger.info("🔄 [Node] Chat Agent")

    # Get user message and history
    messages = state.messages
    last_user_message = messages[-1]
    chat_history = messages[:-1]

    # Define tools for the chat agent
    from langchain.agents import AgentExecutor, create_openai_tools_agent
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.tools import StructuredTool

    from nl2sql.agents.tools.chat_tools import ChatAgentTools

    chat_agent_tools = ChatAgentTools(vector_store)
    tools = [
        StructuredTool.from_function(func=chat_agent_tools.get_similar_queries),
        StructuredTool.from_function(func=chat_agent_tools.explain_query),
        StructuredTool.from_function(func=chat_agent_tools.get_schema_info),
    ]

    # Get the system prompt
    chat_system_prompt = """You are a helpful NL2SQL assistant that can help users with database queries and data analysis.

You have access to tools that can:
1. Find similar SQL query examples from the knowledge base
2. Explain SQL queries in simple terms
3. Provide database schema information

For general questions about capabilities, explain what you can do.
For questions about the database or SQL, use the appropriate tools to provide helpful information.
Be conversational and helpful, and guide users toward useful database queries."""  # noqa: E501

    # Create the prompt
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", chat_system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    # Initialize the LLM
    llm = init_chat_model(model="gpt-4.1-mini", model_provider="openai", temperature=0)

    # Create the agent
    agent = create_openai_tools_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    # Invoke the agent
    try:
        response = agent_executor.invoke(
            {"input": last_user_message.content, "chat_history": chat_history}
        )
        response_content = response["output"]
    except Exception as e:
        logger.error(f"Chat agent error: {e}")
        response_content = (
            "I'm here to help you with database queries and data analysis. "
            "What would you like to explore in your database?"
        )

    logger.debug(f"✅ Chat Agent response: {response_content[:50]}...")
    return {"messages": [AIMessage(content=response_content)]}


def sql_generator(state: State, vector_store: VectorStore) -> dict:
    """Generate SQL query from natural language using LLM and context."""
    logger.info("🔄 [Node] SQL Generator")
    logger.debug(f"User question: {state.user_query}")

    # Get chat history for context
    chat_history = get_chat_history(state.messages[:-1])
    logger.debug(f"Chat history length: {len(chat_history)}")

    # Format schema context from data dictionary
    schema_context = data_dictionary.format_context()

    # Format SQL examples for few-shot learning
    retrieved_docs = vector_store.vectorstore.similarity_search(
        state.user_query, k=4, filter={"type": "example"}
    )
    logger.debug(f"Retrieved {len(retrieved_docs)} docs")
    sql_examples_context = "\n\n".join([doc.page_content for doc in retrieved_docs])

    # Initialize LLM
    llm = init_chat_model(
        model="gpt-4.1-mini", model_provider="openai", temperature=0
    ).with_structured_output(method="json_mode")  # returns dict directly

    # Create SQL generation chain
    llm_chain = sql_generator_prompt | llm

    # Generate SQL query
    response = llm_chain.invoke(
        {
            "user_query": state.user_query,
            "chat_history": chat_history,
            "schema_context": schema_context,
            "sql_examples": sql_examples_context,
        }
    )

    # TODO: Add key validation for the response

    return response


def sql_safety_validator(state: State) -> dict:
    """Validate if the SQL query is safe."""
    import re

    logger.info("🔄 [Node] SQL Safety Validator")

    found_unsafe_keywords = []
    for keyword in UNSAFE_SQL_KEYWORDS:
        if re.search(rf"\b{keyword}\b", state.sql_query):
            found_unsafe_keywords.append(keyword.upper())

    if found_unsafe_keywords:
        logger.error(f"❌ SQL contains unsafe keywords: {found_unsafe_keywords}")
        ai_message = AIMessage(
            content=f"❌ SQL contains unsafe keywords: {found_unsafe_keywords}"
        )
        return {"messages": [ai_message], "sql_safety_status": "unsafe"}
    else:
        logger.debug("✅ SQL is safe")
        return {"sql_safety_status": "safe"}


def sql_syntax_validator(state: State, db_connector: PostgreSQLConnector) -> dict:
    """Validate SQL syntax and attempt to fix errors using LLM."""
    logger.info("🔄 [Node] SQL Syntax Validator")

    max_retries = 3
    current_query = state.sql_query

    for attempt in range(max_retries):
        # Validate current query
        validation_result = validate_sql_syntax(current_query, db_connector)

        # If the query is valid, return success
        if validation_result["valid_syntax"]:
            logger.debug("✅ Syntax Validator: SQL syntax is valid.")
            return {
                "sql_syntax_status": "valid",
                "sql_query": current_query,
            }

        # Log the error and the current query for debugging
        logger.debug(f"Invalid syntax → Entering Fix Attempt #{attempt + 1}...")
        logger.debug(f"Current query: {current_query}")
        logger.debug(f"Error: {validation_result['error']}")

        # Use LLM to fix the error
        sql_syntax_fixer_prompt = load_chat_prompt_template(
            target_prompt="sql_syntax_fixer"
        )
        llm = init_chat_model(model="gpt-4.1", model_provider="openai", temperature=0)
        llm_chain = sql_syntax_fixer_prompt | llm
        fixed_query = llm_chain.invoke(
            {
                "query": current_query,
                "error": validation_result["error"],
            }
        ).content
        current_query = fixed_query

    logger.warning(
        f"⚠️ Syntax Validator: Failed to fix SQL syntax after {max_retries} attempts."
    )
    return {
        "sql_syntax_status": False,
        "messages": [
            AIMessage(
                content=(
                    f"❌ I couldn't generate valid SQL syntax. Error: "
                    f"{validation_result['error']}"
                )
            )
        ],
    }


def human_feedback(state: State) -> dict:
    """Ask for human confirmation and pause for input."""
    logger.info("🔄 [Node] Human Feedback")

    # Format the answer for the user
    formatted_answer = format_answer(state)
    formatted_answer += "\nShould I execute this query? Answer with 'yes' or 'no'."

    # Create the AI message
    ai_message = AIMessage(content=formatted_answer)

    # Mark that we're waiting for confirmation
    human_reply = interrupt(
        {
            "messages": ai_message,
            "waiting_for_confirmation": True,
        }
    )

    # Process the human reply - it could be a string from the Command(resume=...)
    if isinstance(human_reply, str):
        human_reply_content = human_reply.strip().lower()
    elif hasattr(human_reply, "content"):
        human_reply_content = human_reply.content.strip().lower()
    else:
        human_reply_content = str(human_reply).strip().lower()

    user_feedback_status = "approved" if "y" in human_reply_content else "rejected"

    if user_feedback_status == "approved":
        logger.debug(f"✅ Human feedback: {user_feedback_status}")
    else:
        logger.debug(f"❌ Human feedback: {user_feedback_status}")

    # Create a HumanMessage for the reply
    human_message = HumanMessage(content=human_reply_content)

    return {
        "messages": [ai_message, human_message],
        "user_feedback_status": user_feedback_status,
    }


def sql_executor(state: State, db_connector: PostgreSQLConnector) -> dict:
    """Execute the SQL query."""
    logger.info("🔄 [Node] SQL Executor")

    # Execute the SQL query
    sql_execution_result = execute_sql_query(state.sql_query, db_connector)
    sql_execution_status = "success" if sql_execution_result["success"] else "failure"

    if sql_execution_status:
        logger.debug(f"✅ SQL execution status: {sql_execution_status}")
        logger.debug(f"✅ SQL result: {sql_execution_result['data'][:50]}...")
    else:
        logger.debug(f"❌ SQL execution status: {sql_execution_status}")
        logger.debug(f"❌ SQL result: {sql_execution_result['error']}")

    return {
        "sql_execution_status": sql_execution_status,
        "sql_execution_result": sql_execution_result,
    }


def sql_result_analyzer(state: State) -> dict:
    """Analyse the SQL result using LLM."""
    logger.info("🔄 [Node] SQL Result Analyser")

    # Reconstruct execution result with DataFrame for formatting
    execution_result_for_formatting = state.sql_execution_result.copy()
    if execution_result_for_formatting["data"] is not None:
        # Convert back to DataFrame for the formatting function
        execution_result_for_formatting["data"] = pd.DataFrame(
            execution_result_for_formatting["data"]
        )

    # Format results for LLM interpretation
    formatted_results = format_query_results_for_llm(execution_result_for_formatting)

    # Load the result interpretation prompt
    result_analyzer_prompt = load_chat_prompt_template(target_prompt="result_analyzer")

    # Initialize LLM
    llm = init_chat_model(model="gpt-4.1", model_provider="openai", temperature=0.1)

    # Create the interpretation chain
    llm_chain = result_analyzer_prompt | llm

    # Generate interpretation
    response = llm_chain.invoke(
        {
            "user_query": state.user_query,
            "sql_query": state.sql_query,
            "query_results": formatted_results,
        }
    )

    analyzed_result = response.content
    logger.info("✅ Results analyzed successfully")

    # Create final response message
    final_message = AIMessage(content=analyzed_result)

    return {
        "messages": [final_message],
        "sql_execution_analysis": analyzed_result,
    }


# ===============================
# Node Rounters
# ===============================


def route_intent(state: State) -> Literal["sql", "chat"]:
    """Route intent to either SQL or Chat agent."""
    logger.debug(f"→ Routing to {state.user_intent}")
    return state.user_intent


def check_sql_generation(state: State) -> Literal["success", "failure"]:
    """Check if the SQL query is valid."""
    if state.sql_query and state.sql_query.strip():
        logger.debug("→ Routing to success")
        return "success"
    else:
        logger.debug("→ Routing to failure")
        return "failure"


def check_sql_safety(state: State) -> Literal["safe", "unsafe"]:
    """Check if the SQL query is safe."""
    logger.debug(f"→ Routing to {state.sql_safety_status}")
    return "safe" if state.sql_safety_status == "safe" else "unsafe"


def check_sql_syntax(state: State) -> Literal["valid", "invalid"]:
    """Check if the SQL query is valid."""
    logger.debug(f"→ Routing to {state.sql_syntax_status}")
    return "valid" if state.sql_syntax_status == "valid" else "invalid"


def check_human_feedback(state: State) -> Literal["approved", "rejected"]:
    """Check if user approved the SQL query."""
    logger.debug(f"→ Routing to {state.user_feedback_status}")
    return "approved" if state.user_feedback_status == "approved" else "rejected"


def check_sql_execution(state: State) -> Literal["success", "failure"]:
    """Check if the SQL query was executed successfully."""
    logger.debug(f"→ Routing to {state.sql_execution_status}")
    return "success" if state.sql_execution_status == "success" else "failure"
