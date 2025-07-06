"""Handle SQL examples for few-shot learning and context retrieval."""

from pathlib import Path

import sqlparse
import yaml
from pydantic import BaseModel, Field


class SQLExample(BaseModel):
    """A SQL example with question and SQL query."""

    question: str = Field(..., description="Natural language question")
    sql: str = Field(..., description="Corresponding SQL query")

    def format_context(self) -> str:
        """Format the example for LLM prompts (few-shot learning)."""
        formatted_sql = sqlparse.format(self.sql, reindent=True)
        return f"Question: {self.question}\n```sql\n{formatted_sql}\n```"

    @classmethod
    def from_yaml(cls, file_path: Path | str) -> dict[str, "SQLExample"]:
        """Load SQL examples from a YAML file."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"SQL examples file not found: {file_path}")

        with open(file_path) as f:
            raw_data = yaml.safe_load(f)

        examples = {}
        for key, data in raw_data.items():
            if isinstance(data, dict):
                examples[key] = cls(**data)
            else:
                # Handle simple string format as fallback
                examples[key] = cls(question=key, sql=str(data))

        return examples

    @classmethod
    def save_yaml(
        cls, examples: dict[str, "SQLExample"], output_path: Path | str
    ) -> Path:
        """Save SQL examples to a YAML file."""
        if isinstance(output_path, str):
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict format for YAML serialization
        data = {key: example.model_dump() for key, example in examples.items()}

        with open(output_path, "w") as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)

        return output_path

    @classmethod
    def format_all_for_prompt(cls, examples: dict[str, "SQLExample"]) -> str:
        """Format all examples for LLM prompts (few-shot learning)."""
        return "\n\n".join(example.format_context() for example in examples.values())
