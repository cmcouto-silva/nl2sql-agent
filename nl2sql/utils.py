"""Utility functions for the nl2sql package."""


def print_section(title: str, separator: str = "=") -> None:
    """Print a section with a title and a separator."""
    print(f"{title}\n{separator * len(title)}")
