# Contributing to SkillForge

Thank you for your interest in contributing to SkillForge! We're building the foundational infrastructure for reusable agent capabilities, and every contribution matters.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork: `git clone https://github.com/your-username/skillforge.git`
3. **Create a virtual environment**: `python -m venv .venv && source .venv/bin/activate`
4. **Install in development mode**: `pip install -e ".[dev,all]"`
5. **Install pre-commit hooks**: `pre-commit install`
6. **Create a branch**: `git checkout -b feature/my-feature`

## Development Workflow

```bash
# Run linting
make lint

# Format code
make format

# Type check
make typecheck

# Run tests
make test

# Run tests with coverage
make test-cov
```

## Code Standards

- **Python 3.12+**: Use modern Python features (type hints, f-strings, pattern matching)
- **Type hints**: All public APIs must have complete type annotations
- **Pydantic v2**: Use Pydantic for all data models and validation
- **No circular imports**: Design modules so they import in a DAG
- **Tests**: Every feature must have tests (unit + integration)
- **Documentation**: All public APIs need docstrings

## Pre-commit Hooks

We use pre-commit to ensure code quality. After installing:

```bash
pre-commit install
pre-commit run --all-files
```

This will automatically run:
- Ruff (linter + formatter)
- MyPy (type checker)
- Trailing whitespace removal
- YAML/JSON/TOML validation
- Large file detection

## Pull Request Process

1. Ensure all tests pass: `pytest tests/ -v`
2. Ensure lint passes: `ruff check src/ tests/`
3. Update documentation if needed
4. Add a changelog entry in `CHANGELOG.md`
5. Submit your PR with a clear description of changes

## Adding a Built-in Skill

1. Create a directory under `src/skillforge/skills/builtins/<skill-name>/`
2. Add `skill.yaml` (manifest) and `skill.py` (implementation)
3. Register the skill in `src/skillforge/skills/builtins/__init__.py`
4. Add tests for the skill
5. Update the built-in skills documentation

## Adding an LLM Provider

1. Create a new file in `src/skillforge/runtime/providers/<name>.py`
2. Extend `BaseProvider` and implement `chat()` and `generate()`
3. Add optional dependency to `pyproject.toml`
4. Register in `src/skillforge/runtime/providers/__init__.py`

## Release Process

Maintainers follow:

1. Update `_version.py` (semantic versioning)
2. Update `CHANGELOG.md`
3. Create a GitHub release with tag `vX.Y.Z`
4. CI automatically publishes to PyPI

## Questions?

Open a [Discussion](https://github.com/shubhmartin107-web/skillforge/discussions) or join our community.

Thank you for building the future of agent capabilities! ⚒
