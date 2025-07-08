"""Configuration utilities."""

from pathlib import Path

import yaml
from langchain_core.prompts import ChatPromptTemplate

UNSAFE_SQL_KEYWORDS = [
    "drop",
    "delete",
    "truncate",
    "alter",
    "update",
    "insert",
    "create",
    "rename",
    "grant",
    "revoke",
    "deny",
]


def load_config(config_path: str | Path) -> dict:
    """Load configuration from YAML file."""
    try:
        with open(config_path) as f:
            return yaml.safe_load(f)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Config file not found: {config_path}") from e
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing YAML file: {config_path}") from e


def load_database_config(config_path: str | Path = "configs/database.yml") -> dict:
    """Load database configuration from YAML file."""
    return load_config(config_path)["database"]


def load_schema_config(config_path: str | Path = "configs/schema.yml") -> dict:
    """Load database schema configuration from YAML file."""
    return load_config(config_path)


def load_chat_prompt_template(
    file_path: str | Path = "configs/prompts.yml", target_prompt: str | None = None
) -> ChatPromptTemplate:
    """Set up a prompt template from a YAML file.

    Args:
        file_path: Path to the prompt YAML file
        target_prompt: Name of the prompt to load from the YAML file

    Returns:
        LangChain ChatPromptTemplate
    """
    prompts = load_config(file_path)
    if prompts.get(target_prompt) is None:
        raise ValueError(f"Prompt template {target_prompt} not found in {file_path}")

    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", prompts[target_prompt]["system_prompt"]),
            ("human", prompts[target_prompt]["user_prompt"]),
        ]
    )
    return prompt_template
