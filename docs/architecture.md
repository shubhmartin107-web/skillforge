# Architecture

## System Overview

SkillForge is organized into layered modules:

```
┌─────────────────────────────────────┐
│          User Interfaces            │
│  CLI (Typer)  │  SDK (Python)      │
│  Dashboard (Gradio)                 │
├─────────────────────────────────────┤
│          Registry Layer             │
│  LocalRegistry (SQLite)             │
│  RemoteRegistry (GitHub/HTTP)       │
│  DependencyResolver                 │
│  Installer                          │
├─────────────────────────────────────┤
│          Runtime Layer              │
│  Executor (Direct/Tool/SubAgent)    │
│  Sandbox (subprocess isolation)     │
│  LLM Providers (DeepSeek/Gemini/..) │
│  ExecutionHooks (observability)     │
├─────────────────────────────────────┤
│       Composition Layer             │
│  WorkflowEngine (DAG)               │
│  Nodes (Skill/Condition/Map/Merge)  │
├─────────────────────────────────────┤
│       Security Layer                │
│  PermissionValidator                │
│  AuditLogger                        │
├─────────────────────────────────────┤
│       Storage                       │
│  SQLite (metadata)                  │
│  Filesystem (skill packages)        │
│  Audit log (JSON-lines)             │
└─────────────────────────────────────┘
```

## Data Flow

1. **User** creates or installs a skill via CLI, SDK, or Dashboard
2. **Registry** stores metadata in SQLite, skill files on disk
3. **Executor** loads skill, validates permissions, runs in sandbox
4. **Composition Engine** orchestrates multi-skill workflows (DAG)
5. **Hooks** emit events to audit log and listeners

## Key Design Decisions

- **SQLite** for metadata: fast, atomic, no external dependencies
- **Subprocess sandboxing**: practical isolation without Docker dependency
- **Pydantic v2** for models: validation, serialization, JSON Schema
- **Pluggable providers**: skills can use any LLM with the same interface
- **Event-driven observability**: hooks compatible with FlowLens tracing
