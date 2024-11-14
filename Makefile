.PHONY: lint format

lint:
	poetry run black . --check

format:
	poetry run black .
