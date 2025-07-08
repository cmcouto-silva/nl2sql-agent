"""Setup vector store for the database."""

from loguru import logger

from nl2sql.database import PostgreSQLConnector
from nl2sql.knowledge_base.data_dictionary import DataDictionary
from nl2sql.knowledge_base.sql_examples import SQLExample
from nl2sql.knowledge_base.vector_store import VectorStore

DATA_DICTIONARY_PATH = "knowledge/data_dictionary.yml"
SQL_EXAMPLES_PATH = "knowledge/sql_examples.yml"

if __name__ == "__main__":
    logger.info("Connecting to database...")
    db_connector = PostgreSQLConnector(config_path="configs/database.yml")

    logger.info("Initializing vector store...")
    vector_store = VectorStore(db_connector)

    logger.info("Loading data dictionary...")
    data_dictionary = DataDictionary.load(DATA_DICTIONARY_PATH)

    logger.info("Adding schema documents to vector store...")
    vector_store.add_documents(
        vector_store.get_documents_from_data_dictionary(data_dictionary)
    )

    logger.info("Loading SQL examples...")
    sql_examples = SQLExample.from_yaml(SQL_EXAMPLES_PATH)

    logger.info("Adding SQL example documents to vector store...")
    vector_store.add_documents(
        vector_store.get_documents_from_sql_examples(sql_examples)
    )
    logger.success("Vector store setup complete.")
