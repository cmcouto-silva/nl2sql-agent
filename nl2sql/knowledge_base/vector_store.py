"""Vector-based document storage and retrieval for RAG workflows."""

import hashlib

from langchain.embeddings.base import Embeddings
from langchain.schema import Document
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_postgres import PGVector

from nl2sql.database.base import SQLBaseConnector
from nl2sql.knowledge_base.data_dictionary import DataDictionary
from nl2sql.knowledge_base.sql_examples import SQLExample


class VectorStore:
    """Vector store for NL2SQL knowledge base."""

    def __init__(
        self,
        db_connector: SQLBaseConnector,
        collection_name: str = "nl2sql_embeddings",
        embeddings: Embeddings | None = None,
    ) -> None:
        """Initialize vector store."""
        self.vectorstore = PGVector(
            connection=db_connector.engine,
            embeddings=embeddings or OpenAIEmbeddings(model="text-embedding-3-small"),
            collection_name=collection_name,
        )

    def add_documents(self, documents: list[Document]) -> None:
        """Add documents to vectorstore."""
        ids = [
            f"{doc.metadata['schema']}.{doc.metadata['table']}"
            if doc.metadata.get("type") == "schema"
            else hashlib.md5(doc.metadata["title"].encode("utf-8")).hexdigest()
            for doc in documents
        ]
        self.vectorstore.add_documents(documents, ids=ids)

    def get_documents_from_data_dictionary(
        self,
        data_dictionary: DataDictionary,
    ) -> list[Document]:
        """Get documents from data dictionary."""
        documents = []

        for database_name, database_info in data_dictionary.databases.items():
            for schema_name, schema_info in database_info.schemas.items():
                for table_name, table_info in schema_info.tables.items():
                    # Format table information
                    content = table_info.format_context()

                    # Create metadata
                    metadata = {
                        "type": "schema",
                        "database": database_name,
                        "schema": schema_name,
                        "table": table_name,
                        "primary_keys": ", ".join(table_info.primary_keys),
                        "foreign_keys": ", ".join(
                            col
                            for fk in table_info.foreign_keys
                            for col in fk["constrained_columns"]
                        ),
                    }

                    # Create Document object
                    doc = Document(page_content=content, metadata=metadata)
                    documents.append(doc)

        return documents

    def get_documents_from_sql_examples(
        self,
        sql_examples: dict[str, SQLExample],
    ) -> list[Document]:
        """Get documents from SQL examples."""
        documents = []

        for title, example in sql_examples.items():
            doc_content = example.format_context()
            doc_metadata = {"type": "example", "title": title}
            documents.append(Document(page_content=doc_content, metadata=doc_metadata))

        return documents
