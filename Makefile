.PHONY: fix 
fix:
	uv run ruff format .
	uv run ruff check . --fix

.PHONY: check
check:
	-uv run ruff format . --check
	-uv run ruff check .

.PHONY: clean
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
