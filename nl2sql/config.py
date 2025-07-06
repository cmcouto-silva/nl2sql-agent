"""Configuration utilities."""

from pathlib import Path

import yaml


def load_config(config_path: str | Path) -> dict:
    """Load configuration from YAML file."""
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_database_config(config_path: str | Path = "configs/database.yml") -> dict:
    """Load database configuration from YAML file."""
    return load_config(config_path)["database"]


def load_schema_config(config_path: str | Path = "configs/schema.yml") -> dict:
    """Load database schema configuration from YAML file."""
    return load_config(config_path)
