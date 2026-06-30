# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-06-30

### Added

- **Skill Standard v1.0**: YAML-based manifest format with typed inputs/outputs, semver, permissions, and execution modes
- **Local Registry**: SQLite-backed skill storage with full CRUD, search, filtering, and statistics
- **Remote Registry**: GitHub API integration and custom registry URL support
- **Dependency Resolver**: Semantic version constraint resolution with circular dependency detection
- **Skill Installer**: Install, update, and remove skills with dependency validation
- **Sandboxed Execution**: Subprocess isolation with resource limits (CPU/memory/timeout), filesystem jailing, and network controls
- **Direct Execution Mode**: In-process function calling for simple skills
- **Tool-Calling Mode**: Auto-generated LLM tool definitions from skill manifests
- **LLM Providers**: Pluggable providers for DeepSeek, Gemini (free), Groq (free), and Ollama (local)
- **Workflow Engine**: DAG-based composition with skill, condition, map, and merge node types
- **Workflow Input Resolution**: Template-based referencing of workflow inputs and step outputs
- **CLI Application**: Typer-based CLI with 15+ commands for registry, skill, workflow, and configuration management
- **Python SDK**: `Forge` class with `run()`, `install()`, `register_skill()`, `search()`, and more
- **@skill Decorator**: Register inline Python functions as installable skills
- **Gradio Dashboard**: Multi-page web UI for browsing, inspecting, and testing skills
- **Permission System**: Capability-based security with network, filesystem, env, and dangerous operation controls
- **Audit Logging**: JSON-lines audit trail with automatic sensitive data redaction
- **Observability Hooks**: Event-driven execution tracing compatible with FlowLens
- **Configuration System**: Environment variable and `.env` file based settings
- **Built-in Skills**: hello-world, web-page-fetcher, data-analyzer example skills
- **Docker Support**: Dockerfile and docker-compose.yml for containerized deployment
- **Comprehensive Documentation**: Getting started, skill standard spec, architecture, and API reference
- **Test Suite**: 30+ tests covering models, registry, runtime, composition, and security
- **CI/CD Pipeline**: GitHub Actions for lint, test, build, and PyPI publish
- **Pre-commit Hooks**: Automated code quality checks (ruff, mypy, formatting)
