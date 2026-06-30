# ⚒ SkillForge

**Reusable Agent Skills Registry & Runtime**

Standardized, secure, versioned, and observable agent capabilities — shareable across every framework and model.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/shubhmartin107-web/skillforge/pulls)

---

## The Problem

Every AI agent developer rebuilds the same capabilities:

- Web browsing and content extraction
- File operations and data processing
- Search and information retrieval
- Code execution and analysis
- API interaction and data transformation

This duplication is **massive, costly, and fragmented**. There is no standardized way to define, share, version, discover, or securely execute these capabilities across different agent frameworks and LLM providers. Each team reinvents the wheel — with inconsistent quality, security, and observability.

## The Solution

SkillForge is to agent capabilities what npm is to JavaScript packages and PyPI is to Python libraries — a **foundational infrastructure** for reusable, discoverable, and composable agent skills.

| Feature | Description |
|---------|-------------|
| **Skill Standard** | Clean, extensible manifest format (YAML) with typed inputs/outputs, permissions, versioning, and metadata |
| **Registry & Discovery** | Local SQLite registry with search, filtering, dependency resolution, and remote registry support |
| **Secure Runtime** | Sandboxed execution with resource limits, filesystem jailing, and network controls |
| **Composition** | DAG-based workflow engine for chaining skills with conditional branching and parallel execution |
| **Pluggable LLMs** | First-class providers for DeepSeek, Gemini, Groq, and Ollama |
| **CLI + SDK + Dashboard** | Typer CLI, Python SDK with `@skill` decorator, and Gradio dashboard |
| **Observability** | Full execution tracing compatible with OpenTelemetry and FlowLens |
| **Security** | Permission system, audit logging, and capability-based access control |

## Quick Start

```bash
# Install
pip install skillforge

# Initialize
skillforge config init

# Create a skill
skillforge skill create my-analyzer

# Install it
skillforge registry install ./my-analyzer

# Run it
skillforge skill run my-analyzer -i message="hello world"

# Or use the SDK
```

```python
from skillforge import Forge

forge = Forge()

# Install a skill
forge.install("./my-analyzer")

# Run a skill
result = forge.run("my-analyzer", message="hello world")
print(result.outputs)

# Define inline skills with the @skill decorator
@forge.register_skill(name="hello", description="Greets someone")
def hello(name: str = "World") -> dict:
    return {"greeting": f"Hello, {name}!"}

# Run it
result = forge.run("hello", name="Agent")
print(result.outputs)  # {"greeting": "Hello, Agent!"}
```

## Skill Manifest Format

Every skill is defined by a `skill.yaml` manifest:

```yaml
name: web-page-fetcher
version: 1.2.0
description: "Fetches and extracts content from a web page"

author:
  name: "SkillForge Team"

inputs:
  - name: url
    type: string
    description: "The URL to fetch"
    required: true
  - name: extract_links
    type: boolean
    default: false

outputs:
  - name: content
    type: string
  - name: links
    type: list

permissions:
  network: true
  filesystem_read: []
  filesystem_write: []

execution:
  mode: direct          # direct | tool_calling | sub_agent
  entrypoint: skill.py
  function: run
  runtime: python3.12

tags: ["web", "utility"]
categories: ["data-ingestion"]
```

## CLI Reference

```bash
skillforge registry list            # List installed skills
skillforge registry search <query>  # Search skills
skillforge registry install <path>  # Install a skill
skillforge registry remove <name>   # Remove a skill
skillforge registry info <name>     # Show skill details
skillforge registry stats           # Show registry statistics

skillforge skill create <name>      # Scaffold a new skill
skillforge skill run <name>         # Run a skill
skillforge skill test <name>        # Test a skill
skillforge skill validate <path>    # Validate a manifest

skillforge workflow run <file>      # Run a workflow
skillforge workflow validate <file> # Validate a workflow

skillforge config init              # Initialize config
skillforge config show              # Show configuration

skillforge dashboard                # Launch Gradio dashboard
```

## Workflow Example

Compose multiple skills into higher-level workflows:

```yaml
name: research-assistant
version: 0.1.0
start_node: search
nodes:
  search:
    type: skill
    skill_name: web-search
    inputs:
      query: "{workflow.inputs.topic}"
    next_on_success: fetch
  fetch:
    type: skill
    skill_name: web-page-fetcher
    inputs:
      url: "{steps.search.result.top_url}"
    next_on_success: summarize
  summarize:
    type: skill
    skill_name: text-summarizer
    inputs:
      text: "{steps.fetch.result.content}"
```

```bash
skillforge workflow run research-workflow.yaml -i topic="quantum computing"
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    SkillForge                            │
│  ┌─────────┐  ┌──────────┐  ┌────────┐  ┌───────────┐  │
│  │   CLI   │  │   SDK    │  │Dashboard│  │   API     │  │
│  └────┬────┘  └────┬─────┘  └────┬───┘  └─────┬─────┘  │
│       │            │             │             │         │
│  ┌────┴────────────┴─────────────┴─────────────┴────┐   │
│  │              Registry Manager                    │   │
│  │  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │   │
│  │  │  Local   │  │  Remote  │  │  Dependency   │  │   │
│  │  │  SQLite  │  │  GitHub  │  │  Resolver     │  │   │
│  │  └──────────┘  └──────────┘  └───────────────┘  │   │
│  └──────────────────────────────────────────────────┘   │
│                           │                              │
│  ┌────────────────────────┴──────────────────────────┐  │
│  │              Execution Engine                      │  │
│  │  ┌────────┐  ┌──────────────┐  ┌───────────────┐  │  │
│  │  │Sandbox │  │  Direct Exec │  │  Tool Calling  │  │  │
│  │  └────────┘  └──────────────┘  └───────────────┘  │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │         LLM Providers                        │  │  │
│  │  │  DeepSeek │ Gemini │ Groq │ Ollama           │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────┘   │
│                           │                              │
│  ┌────────────────────────┴──────────────────────────┐  │
│  │         Composition Engine (DAG)                   │  │
│  │  Skill Chaining │ Conditions │ Map │ Merge        │  │
│  └────────────────────────────────────────────────────┘   │
│                           │                              │
│  ┌────────────────────────┴──────────────────────────┐  │
│  │  Security & Observability                         │  │
│  │  Permissions │ Audit Log │ Tracing │ FlowLens     │  │
│  └────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Integration

SkillForge complements and enhances existing agent frameworks:

- **Claude Code / Claude Agent SDK**: Skills expose tool-calling interfaces compatible with Anthropic's tool use format
- **LangChain / LlamaIndex**: Skills can be wrapped as LangChain tools or LlamaIndex query tools
- **OpenAI Assistants**: Tool definitions generated from skill manifests
- **Any MCP-compatible client**: Skills expose capabilities through standard interfaces

## Configuration

Configure via environment variables with `SKILLFORGE_` prefix or `.env` file:

```bash
export SKILLFORGE_DEEPSEEK_API_KEY="sk-..."
export SKILLFORGE_GEMINI_API_KEY="..."
export SKILLFORGE_GROQ_API_KEY="gsk_..."
export SKILLFORGE_SANDBOX_ENABLED="true"
export SKILLFORGE_EXECUTION_TIMEOUT="120"
```

## Installation

```bash
# Core
pip install skillforge

# With dashboard
pip install skillforge[dashboard]

# With LLM providers
pip install skillforge[deepseek]    # DeepSeek
pip install skillforge[gemini]      # Google Gemini
pip install skillforge[groq]        # Groq
pip install skillforge[ollama]      # Ollama (local)

# Everything
pip install skillforge[all]
```

## Docker

```bash
docker build -t skillforge .
docker run -p 7860:7860 skillforge
```

Or with Docker Compose:

```bash
docker compose up
```

## Development

```bash
git clone https://github.com/shubhmartin107-web/skillforge
cd skillforge
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,all]"

# Run tests
pytest

# Lint
ruff check src/
```

## Roadmap

- [x] Skill manifest standard and validation
- [x] Local registry with SQLite storage
- [x] Sandboxed execution engine
- [x] Direct and tool-calling execution modes
- [x] Workflow composition (DAG engine)
- [x] CLI, Python SDK, and Gradio dashboard
- [x] LLM providers (DeepSeek, Gemini, Groq, Ollama)
- [x] Permission system and audit logging
- [ ] Remote registry (package index server)
- [ ] Skill publishing workflow (build, sign, publish)
- [ ] WebAssembly-based sandbox for higher isolation
- [ ] Auto-generated OpenAPI specs from skills
- [ ] VS Code extension for skill development
- [ ] Community skill repository

## License

Apache 2.0 — see [LICENSE](LICENSE)
