.PHONY: install install-dev lint format typecheck test test-cov clean build publish precommit

VENV = .venv
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip

install:
	python3 -m venv $(VENV)
	$(PIP) install -e ".[dev,all]"

install-dev:
	$(PIP) install -e ".[dev,all]" pre-commit

lint:
	$(VENV)/bin/ruff check src/ tests/

format:
	$(VENV)/bin/ruff format src/ tests/

typecheck:
	$(VENV)/bin/mypy src/skillforge/ --ignore-missing-imports

test:
	$(PYTHON) -m pytest tests/ -v --tb=short

test-cov:
	$(PYTHON) -m pytest tests/ --cov=src/skillforge/ --cov-report=term-missing --cov-report=html

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .ruff_cache .mypy_cache htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

build: clean
	$(PYTHON) -m build

publish: build
	$(PIP) install twine
	$(VENV)/bin/twine upload dist/*

precommit:
	$(VENV)/bin/pre-commit install
	$(VENV)/bin/pre-commit run --all-files

.PHONY: run-dashboard
run-dashboard:
	$(PYTHON) -m skillforge dashboard

.PHONY: run-registry-server
run-registry-server:
	$(PYTHON) -m uvicorn skillforge.registry.server:app --reload --port 8765
