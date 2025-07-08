"""This module contains the tools for the chat agent."""

from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate

from nl2sql.knowledge_base.data_dictionary import DataDictionary
from nl2sql.knowledge_base.vector_store import VectorStore


class ChatAgentTools:
    """Container for chat agent tools."""

    def __init__(self, vector_store: VectorStore) -> None:
        """Initialize with a vector store instance."""
        self.vector_store = vector_store
        # Load data dictionary for schema context
        try:
            self.data_dictionary = DataDictionary.load()
            self.schema_context = self.data_dictionary.format_context()
        except Exception as e:
            # Fallback to a basic schema description
            self.schema_context = """Database contains tables for ecommerce data including:
            - customers: customer information and locations
            - orders: order details and status
            - order_items: individual items in orders
            - products: product information and categories
            - sellers: seller information
            """  # noqa: E501
            print(f"Warning: Could not load data dictionary: {e}")

    def get_similar_queries(self, query: str, k: int = 3) -> str:
        """Retrieve K similar queries from a knowledge base of SQL examples.

        Args:
            query (str): The user's query to find similar examples for.
            k (int): The number of similar queries to retrieve. Defaults to 3.
        """
        try:
            limit = min(k, 5)
            # Use the retriever interface instead of direct similarity_search
            retriever = self.vector_store.as_retriever(
                search_kwargs={"k": limit, "filter": {"type": "example"}}
            )
            docs = retriever.invoke(query)

            if not docs:
                return "I couldn't find any similar queries in the knowledge base."

            # Format the response
            response_lines = []
            if k > 10:
                response_lines.append(
                    "Note: I can only retrieve a maximum of 10 examples at a time.\n"
                )

            response_lines.append(
                f"Here are the top {len(docs)} similar queries I found:"
            )

            for i, doc in enumerate(docs):
                title = doc.metadata.get("title", "SQL Example")
                sql_query = doc.page_content
                response_lines.append(
                    f"\n---\n\n**Example {i + 1}: {title}**\n\n```sql\n{sql_query}\n```"
                )

            return "\n".join(response_lines)

        except Exception as e:
            return f"Error retrieving similar queries: {e!s}"

    def explain_query(self, sql_query: str) -> str:
        """Explain a SQL query based on the database schema.

        Args:
            sql_query (str): The SQL query to be explained.
        """
        try:
            explainer_prompt = """You are a helpful SQL expert. Explain the following SQL query in simple terms,
            considering the database schema provided.

            Database Schema:
            {schema_context}

            SQL Query to explain:
            {sql_query}

            Please provide a clear, step-by-step explanation of what this query does."""  # noqa: E501

            explainer_prompt_template = ChatPromptTemplate.from_template(
                explainer_prompt
            )
            llm = init_chat_model(
                model="gpt-4.1-mini", model_provider="openai", temperature=0
            )

            explainer_chain = explainer_prompt_template | llm

            response = explainer_chain.invoke(
                {"sql_query": sql_query, "schema_context": self.schema_context}
            )

            return response.content

        except Exception as e:
            return f"Error explaining query: {e!s}"

    def get_schema_info(self, table_name: str = "") -> str:
        """Get information about database schema or specific table.

        Args:
            table_name (str): Optional table name to get specific information.
        """
        try:
            if not table_name:
                return f"Here's an overview of the database schema:\n\n{self.schema_context[:1000]}..."  # noqa: E501

            # Look for specific table in schema context
            if table_name.lower() in self.schema_context.lower():
                lines = self.schema_context.split("\n")
                table_info = []
                capturing = False

                for line in lines:
                    if (
                        f"TABLE: {table_name}" in line
                        or f"table: {table_name}" in line.lower()
                    ):
                        capturing = True
                    elif capturing and line.startswith("TABLE:"):
                        break

                    if capturing:
                        table_info.append(line)

                if table_info:
                    return f"Information about table '{table_name}':\n\n" + "\n".join(
                        table_info
                    )

            return f"Table '{table_name}' not found in the schema. Use get_schema_info() without parameters to see all available tables."  # noqa: E501

        except Exception as e:
            return f"Error retrieving schema information: {e!s}"
