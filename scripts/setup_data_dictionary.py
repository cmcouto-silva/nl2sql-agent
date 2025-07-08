"""Setup data dictionary for the database."""

from loguru import logger

from nl2sql.config import load_schema_config
from nl2sql.database import PostgreSQLConnector
from nl2sql.knowledge_base.data_dictionary import DataDictionary

DATA_DICTIONARY_OUTPUT_PATH = "knowledge/data_dictionary.yml"

if __name__ == "__main__":
    logger.info("Loading schema config...")
    schema = load_schema_config()

    logger.info("Connecting to database...")
    db_connector = PostgreSQLConnector(config_path="configs/database.yml")

    logger.info("Extracting data dictionary from database...")
    data_dictionary = DataDictionary.from_inspector(
        inspector=db_connector.inspector,
        database_schema=schema,
    )

    # Check for missing descriptions
    missing_tables = data_dictionary.get_tables_with_missing_descriptions()
    missing_columns = data_dictionary.get_columns_with_missing_descriptions()

    if missing_tables:
        logger.warning(f"There are tables with missing descriptions: {missing_tables}")
    if missing_columns:
        logger.warning(
            f"There are columns with missing descriptions: {missing_columns}"
        )

    logger.info(f"Saving data dictionary to {DATA_DICTIONARY_OUTPUT_PATH}...")
    data_dictionary.save(DATA_DICTIONARY_OUTPUT_PATH)
    logger.success("Data dictionary setup complete.")
